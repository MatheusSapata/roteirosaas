"""Ciclo de vida dos arquivos guardados (Azure Blob): arquivar o material de empresas que saíram
do ar e limpar arquivos que ninguém usa mais.

Como saber se um arquivo está em uso: todo arquivo enviado tem um identificador único (UUID) no
nome ("<uuid>.jpg", "<uuid>_1600.webp"...). A análise procura esses identificadores em todas as
colunas de texto de todas as tabelas (páginas, modelos, logos, documentos de clientes, CRM,
aulas, banners, banco de fotos...). Arquivo cujo identificador aparece em algum lugar está em
uso. Arquivo sem identificador no nome nunca é mexido.

Empresas que saíram do ar (contando de subscriptions.deactivated_at):
  - 7 dias: arquivos exclusivos dela vão para a camada Cool (~45% mais barata, ainda disponível);
  - 30 dias: vão para Archive (~90% mais barata, indisponível; restaurar leva algumas horas);
  - excluir é só manual. Se a empresa voltar, os arquivos são restaurados.
Arquivos usados também por outra empresa, por modelos ou pelo banco de fotos ficam como estão.

Arquivos sem uso: só podem ser excluídos depois de 30 dias seguidos sem uso em todas as análises
(margem para quem está editando: tirou a foto e vai desfazer) e enviados há mais de 30 dias.
"""
from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import JSON, String, Text, cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.media import MediaAsset
from app.models.media_archive import AgencyMediaArchive, MediaOrphan
from app.services.company_status import agencies_with_owner, company_status, stamp_deactivations
from app.services.media_storage import StoredFile, media_storage

logger = logging.getLogger(__name__)

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
COOL_AFTER_DAYS = 7
ARCHIVE_AFTER_DAYS = 30
ORPHAN_GRACE_DAYS = 30
# Tabelas que não guardam arquivos nossos (e a de mensagens do WhatsApp tem registros corrompidos
# que travam leituras completas; ver CLAUDE.md, seção de backup).
SKIPPED_TABLE_PREFIXES = ("whatsapp",)
# As tabelas de controle deste ciclo guardam nomes de arquivos: não contam como "em uso".
SKIPPED_TABLES = frozenset({"media_orphans", "agency_media_archives"})
LIBRARY_TABLE = "media_assets"


def automation_enabled() -> bool:
    return os.getenv("MEDIA_LIFECYCLE_AUTOMATION", "").strip().lower() in {"1", "true", "yes", "sim"}


def file_key(name: str) -> str | None:
    match = UUID_RE.search(name or "")
    return match.group(0).lower() if match else None


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass
class References:
    """Identificadores de arquivos em uso: os de cada empresa e os de fora de qualquer empresa."""

    by_agency: dict[int, set[str]] = field(default_factory=dict)
    shared: set[str] = field(default_factory=set)
    # Os que só aparecem na biblioteca de mídia (enviados, mas fora de qualquer página).
    library_only: dict[int, set[str]] = field(default_factory=dict)

    def used_outside(self, agency_id: int) -> set[str]:
        used = set(self.shared)
        for other, keys in self.by_agency.items():
            if other != agency_id:
                used |= keys
        return used

    def all_used(self) -> set[str]:
        used = set(self.shared)
        for keys in self.by_agency.values():
            used |= keys
        return used


def collect_references(db: Session) -> References:
    refs = References()
    for table in Base.metadata.sorted_tables:
        if table.name.startswith(SKIPPED_TABLE_PREFIXES) or table.name in SKIPPED_TABLES:
            continue
        text_columns = [
            column for column in table.columns if isinstance(column.type, (String, Text, JSON, JSONB)) and column.name != "id"
        ]
        if not text_columns:
            continue
        owner_column = table.c.id if table.name == "agencies" else table.c.get("agency_id")
        selected = [cast(column, Text) if isinstance(column.type, (JSON, JSONB)) else column for column in text_columns]
        statement = select(owner_column, *selected) if owner_column is not None else select(*selected)
        result = db.execute(statement.execution_options(yield_per=1000))
        for row in result:
            values = row[1:] if owner_column is not None else row
            keys = {match.lower() for value in values if value for match in UUID_RE.findall(str(value))}
            if not keys:
                continue
            agency_id = row[0] if owner_column is not None else None
            if table.name == LIBRARY_TABLE:
                refs.library_only.setdefault(agency_id, set()).update(keys)
            elif agency_id is None:
                refs.shared |= keys
            else:
                refs.by_agency.setdefault(agency_id, set()).update(keys)
    # Biblioteca: o que também está numa página/registro não é "só da biblioteca".
    used = refs.all_used()
    for agency_id, keys in list(refs.library_only.items()):
        refs.library_only[agency_id] = keys - used
    return refs


def files_by_key() -> dict[str, list[StoredFile]]:
    grouped: dict[str, list[StoredFile]] = {}
    for stored in media_storage.list_files():
        key = file_key(stored.name)
        if key:
            grouped.setdefault(key, []).append(stored)
    return grouped


def exclusive_keys(refs: References, agency_id: int) -> tuple[set[str], int]:
    """Arquivos só desta empresa (páginas, biblioteca, logo...) e quantos ficaram de fora por
    serem usados em outro lugar."""
    mine = refs.by_agency.get(agency_id, set()) | refs.library_only.get(agency_id, set())
    shared = mine & refs.used_outside(agency_id)
    return mine - shared, len(shared)


# --- Análise (em segundo plano; um processo por contêiner) ---


@dataclass
class Analysis:
    status: str = "idle"  # idle | running | done | error
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)


analysis = Analysis()
_lock = threading.Lock()


def _bytes(files: list[StoredFile]) -> int:
    return sum(item.size for item in files)


def run_analysis(session_factory, now: datetime | None = None) -> Analysis:
    """Mede o armazenamento, o material de cada empresa fora do ar e os arquivos sem uso."""
    if not _lock.acquire(blocking=False):
        return analysis
    analysis.status, analysis.started_at, analysis.error = "running", datetime.now(timezone.utc), None
    db: Session = session_factory()
    try:
        now = now or datetime.now(timezone.utc)
        stamp_deactivations(db, now)
        refs = collect_references(db)
        grouped = files_by_key()
        tiers: dict[str, dict[str, int]] = {}
        for files in grouped.values():
            for item in files:
                bucket = tiers.setdefault(item.tier, {"files": 0, "bytes": 0})
                bucket["files"] += 1
                bucket["bytes"] += item.size

        # Empresas fora do ar: o que é só delas.
        inactive_total = {"companies": 0, "files": 0, "bytes": 0}
        for agency, owner in agencies_with_owner(db):
            status = company_status(owner, now)
            record = db.query(AgencyMediaArchive).filter(AgencyMediaArchive.agency_id == agency.id).first()
            if status.online and record is None:
                continue
            keys, shared = exclusive_keys(refs, agency.id)
            files = [item for key in keys for item in grouped.get(key, [])]
            if record is None:
                record = AgencyMediaArchive(agency_id=agency.id, stage="hot", blobs=[])
                db.add(record)
            if record.stage in ("hot", "restoring"):
                # Restaurando: vira "hot" quando nenhum arquivo está mais reidratando no Azure.
                if record.stage == "restoring" and not any(item.rehydrating or item.tier == "Archive" for item in files):
                    record.stage = "hot"
            record.files_count = len(files)
            record.total_bytes = _bytes(files)
            record.shared_skipped = shared
            record.measured_at = now
            if not status.online:
                inactive_total["companies"] += 1
                inactive_total["files"] += len(files)
                inactive_total["bytes"] += record.total_bytes

        # Arquivos sem uso (fora da biblioteca, nenhuma página ou registro).
        used = refs.all_used()
        orphan_keys = {key for key in grouped if key not in used}
        existing = {orphan.file_key: orphan for orphan in db.query(MediaOrphan).all()}
        for key, orphan in existing.items():
            if key not in orphan_keys:
                db.delete(orphan)  # voltou a ser usado (ou já foi excluído)
        for key in orphan_keys:
            files = grouped[key]
            orphan = existing.get(key)
            if orphan is None:
                orphan = MediaOrphan(file_key=key, first_seen_at=now)
                db.add(orphan)
            orphan.names = [item.name for item in files]
            orphan.total_bytes = _bytes(files)
            orphan.uploaded_at = max((_aware(item.last_modified) for item in files if item.last_modified), default=None)
            orphan.last_seen_at = now
        db.commit()
        ready = [orphan for orphan in db.query(MediaOrphan).all() if orphan_ready(orphan, now)]
        analysis.summary = {
            "total_files": sum(len(files) for files in grouped.values()),
            "total_bytes": sum(_bytes(files) for files in grouped.values()),
            "tiers": tiers,
            "inactive": inactive_total,
            "orphans": {
                "files": sum(len(grouped[key]) for key in orphan_keys),
                "groups": len(orphan_keys),
                "bytes": sum(_bytes(grouped[key]) for key in orphan_keys),
            },
            "orphans_ready": {"groups": len(ready), "bytes": sum(o.total_bytes or 0 for o in ready)},
        }
        analysis.status = "done"
    except Exception as exc:  # noqa: BLE001 - o painel mostra o erro
        db.rollback()
        logger.exception("media_analysis_failed")
        analysis.status, analysis.error = "error", str(exc)
    finally:
        analysis.finished_at = datetime.now(timezone.utc)
        db.close()
        _lock.release()
    return analysis


def orphan_ready(orphan: MediaOrphan, now: datetime | None = None) -> bool:
    """Pronto para excluir: 30 dias seguidos sem uso e enviado há mais de 30 dias."""
    now = now or datetime.now(timezone.utc)
    limit = now - timedelta(days=ORPHAN_GRACE_DAYS)
    first_seen = _aware(orphan.first_seen_at)
    uploaded = _aware(orphan.uploaded_at)
    return bool(first_seen and first_seen <= limit and uploaded and uploaded <= limit)


# --- Ações ---


class LifecycleError(ValueError):
    pass


def _record(db: Session, agency_id: int) -> AgencyMediaArchive:
    record = db.query(AgencyMediaArchive).filter(AgencyMediaArchive.agency_id == agency_id).first()
    if record is None:
        record = AgencyMediaArchive(agency_id=agency_id, stage="hot", blobs=[])
        db.add(record)
    return record


def _current_files(db: Session, agency_id: int) -> tuple[list[StoredFile], int]:
    """Confere de novo, na hora da ação, o que é só da empresa (nada de usar análise velha)."""
    refs = collect_references(db)
    keys, shared = exclusive_keys(refs, agency_id)
    grouped = files_by_key()
    return [item for key in keys for item in grouped.get(key, [])], shared


def _require_inactive(db: Session, agency_id: int, min_days: int) -> None:
    for agency, owner in agencies_with_owner(db):
        if agency.id != agency_id:
            continue
        status = company_status(owner)
        if status.online:
            raise LifecycleError("A empresa está no ar. Só dá para arquivar material de empresa desativada.")
        if (status.days or 0) < min_days:
            raise LifecycleError(f"A empresa está desativada há {status.days or 0} dia(s); o mínimo para esta ação é {min_days}.")
        return
    raise LifecycleError("Empresa não encontrada.")


def move_agency_media(db: Session, agency_id: int, tier: str, *, min_days: int = 0) -> AgencyMediaArchive:
    """Move os arquivos exclusivos da empresa para Cool ou Archive."""
    assert tier in ("Cool", "Archive")
    _require_inactive(db, agency_id, min_days)
    files, shared = _current_files(db, agency_id)
    record = _record(db, agency_id)
    errors: list[str] = []
    moved: list[str] = []
    for item in files:
        if item.tier == tier:
            moved.append(item.name)
            continue
        try:
            media_storage.set_tier(item.name, tier)
            moved.append(item.name)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{item.name}: {exc}")
    now = datetime.now(timezone.utc)
    record.blobs = sorted(set(record.blobs or []) | set(moved))
    record.files_count, record.total_bytes, record.shared_skipped = len(files), _bytes(files), shared
    record.stage = "cool" if tier == "Cool" else "archive"
    if tier == "Cool":
        record.cool_at = now
    else:
        record.archived_at = now
    record.last_error = "; ".join(errors[:5]) or None
    db.commit()
    return record


def restore_agency_media(db: Session, agency_id: int) -> AgencyMediaArchive:
    """Volta os arquivos para Hot. Do Archive, o Azure leva algumas horas (fica "restaurando")."""
    record = _record(db, agency_id)
    if record.stage == "deleted":
        raise LifecycleError("Os arquivos desta empresa já foram excluídos.")
    names = set(record.blobs or [])
    errors: list[str] = []
    archived = False
    for item in media_storage.list_files():
        if item.name not in names or item.tier == "Hot":
            continue
        try:
            archived = archived or item.tier == "Archive"
            media_storage.set_tier(item.name, "Hot")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{item.name}: {exc}")
    record.stage = "restoring" if archived else "hot"
    record.restored_at = datetime.now(timezone.utc)
    record.last_error = "; ".join(errors[:5]) or None
    db.commit()
    return record


def delete_agency_media(db: Session, agency_id: int, *, min_days: int = ARCHIVE_AFTER_DAYS) -> AgencyMediaArchive:
    """Exclui de vez os arquivos exclusivos da empresa (só manual, com confirmação no painel)."""
    _require_inactive(db, agency_id, min_days)
    files, shared = _current_files(db, agency_id)
    record = _record(db, agency_id)
    errors: list[str] = []
    deleted_keys: set[str] = set()
    for item in files:
        try:
            media_storage.delete_file(item.name)
            deleted_keys.add(file_key(item.name) or "")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{item.name}: {exc}")
    _drop_library_entries(db, deleted_keys, agency_id)
    record.stage, record.deleted_at = "deleted", datetime.now(timezone.utc)
    record.files_count, record.total_bytes, record.shared_skipped = 0, 0, shared
    record.last_error = "; ".join(errors[:5]) or None
    db.commit()
    return record


def _drop_library_entries(db: Session, keys: set[str], agency_id: int | None = None) -> None:
    """Tira da biblioteca de mídia as entradas dos arquivos excluídos (não fica foto quebrada)."""
    keys.discard("")
    if not keys:
        return
    query = db.query(MediaAsset)
    if agency_id is not None:
        query = query.filter(MediaAsset.agency_id == agency_id)
    for asset in query.all():
        if file_key(asset.url or "") in keys:
            db.delete(asset)


def delete_ready_orphans(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Exclui os arquivos sem uso que passaram da margem de segurança, conferindo de novo que
    continuam sem uso agora."""
    now = now or datetime.now(timezone.utc)
    ready = [orphan for orphan in db.query(MediaOrphan).all() if orphan_ready(orphan, now)]
    if not ready:
        return {"deleted_files": 0, "deleted_bytes": 0, "kept": 0}
    used = collect_references(db).all_used()
    deleted_files = deleted_bytes = kept = 0
    deleted_keys: set[str] = set()
    for orphan in ready:
        if orphan.file_key in used:
            db.delete(orphan)  # voltou a ser usado desde a última análise
            kept += 1
            continue
        for name in orphan.names or []:
            try:
                media_storage.delete_file(name)
                deleted_files += 1
            except Exception:  # noqa: BLE001 - segue com os outros
                logger.exception("orphan_delete_failed name=%s", name)
        deleted_bytes += orphan.total_bytes or 0
        deleted_keys.add(orphan.file_key)
        db.delete(orphan)
    _drop_library_entries(db, deleted_keys)
    db.commit()
    return {"deleted_files": deleted_files, "deleted_bytes": deleted_bytes, "kept": kept}


def run_automation(session_factory, now: datetime | None = None) -> None:
    """Uma vez por dia (com MEDIA_LIFECYCLE_AUTOMATION ligado): analisa, move para Cool/Archive
    quem passou dos prazos e restaura quem voltou. Arquivos sem uso nunca são excluídos sozinhos."""
    now = now or datetime.now(timezone.utc)
    run_analysis(session_factory, now)
    if analysis.status != "done":
        return
    db: Session = session_factory()
    try:
        records = {record.agency_id: record for record in db.query(AgencyMediaArchive).all()}
        for agency, owner in agencies_with_owner(db):
            record = records.get(agency.id)
            if record is None or record.stage == "deleted":
                continue
            status = company_status(owner, now)
            try:
                if status.online and record.stage in ("cool", "archive"):
                    restore_agency_media(db, agency.id)
                elif not status.online and record.stage == "hot" and record.files_count and (status.days or 0) >= COOL_AFTER_DAYS:
                    move_agency_media(db, agency.id, "Cool", min_days=COOL_AFTER_DAYS)
                elif not status.online and record.stage == "cool" and (status.days or 0) >= ARCHIVE_AFTER_DAYS:
                    move_agency_media(db, agency.id, "Archive", min_days=ARCHIVE_AFTER_DAYS)
            except LifecycleError as exc:
                logger.info("media_lifecycle_skip agency=%s reason=%s", agency.id, exc)
    finally:
        db.close()


_last_automation_day: str | None = None


def hourly_tick(session_factory, now: datetime | None = None) -> None:
    """Chamado pelo job horário das assinaturas: registra quem saiu do ar e, com a automação
    ligada, roda o ciclo uma vez por dia (madrugada de Brasília), numa thread à parte."""
    global _last_automation_day
    now = now or datetime.now(timezone.utc)
    db: Session = session_factory()
    try:
        stamp_deactivations(db, now)
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("stamp_deactivations_failed")
    finally:
        db.close()
    day = now.strftime("%Y-%m-%d")
    if automation_enabled() and now.hour >= 6 and _last_automation_day != day:  # 6h UTC = 3h em Brasília
        _last_automation_day = day
        threading.Thread(target=run_automation, args=(session_factory, now), daemon=True).start()
