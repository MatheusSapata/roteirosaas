"""Fotos cadastradas à mão no Admin Master: guardar a imagem, montar as palavras-chave a partir
do nome do arquivo e das pastas, e importar lotes (pasta do Dropbox, arquivos enviados).

Ex.: lote com a palavra-chave "Beto Carrero" e o arquivo "Atrações/Nerf/IMG_0123.jpg" →
palavras-chave "beto carrero atracoes, beto carrero nerf, beto carrero". A busca "Nerf Beto
Carrero" acha essa foto antes da do castelo; "nerf" sozinho (outro lugar) não acha. A pasta
comum a todas as fotos do lote (ex.: "Beto Carrero - Imprensa") não entra.
"""
from __future__ import annotations

import hashlib
import io
import ipaddress
import logging
import re
import socket
import tempfile
import threading
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from PIL import Image
from sqlalchemy.orm import Session

from app.models.stock_image import StockImage
from app.services.image_optimizer import optimize_image
from app.services.media_storage import media_storage
from app.services.stock_images import MANUAL_PROVIDER, keyword_list, normalize_query

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 30 * 1024 * 1024
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_IMPORT_FILES = 300
IMAGE_EXTENSIONS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
USER_AGENT = "RoteiroOnline/1.0 (+https://roteiroonline.com)"
# Pedaços de nome de arquivo que não dizem nada sobre a foto.
NOISE_WORDS = frozenset(
    """img image imagem foto fotos photo photos pic dsc dscn dcim jpg jpeg png webp copy copia final
    edit editada editado hd web alta baixa res resolucao site novo nova versao v1 v2 v3 crop
    banner thumb print midia media divulgacao press kit""".split()
)


class PhotoError(ValueError):
    """Problema com uma foto (mensagem pronta para mostrar no painel)."""


def context_words(path: str) -> list[str]:
    """Palavras úteis do caminho do arquivo (pastas e nome), sem números nem códigos de câmera."""
    parts = PurePosixPath(path.replace("\\", "/")).parts
    words: list[str] = []
    for index, part in enumerate(parts):
        if index == len(parts) - 1:
            part = PurePosixPath(part).stem
        for word in normalize_query(re.sub(r"[_\-.]+", " ", part)).split():
            if len(word) < 3 or word in NOISE_WORDS or any(char.isdigit() for char in word):
                continue
            if word not in words:
                words.append(word)
    return words[:6]


def photo_keywords(batch_keywords: str, path: str = "") -> str:
    """Palavras-chave do lote + o contexto do arquivo, ligado à primeira palavra-chave do lote."""
    batch = keyword_list(batch_keywords)
    main_words = set((batch[0] if batch else "").split())
    extra = [word for word in context_words(path) if word not in main_words and not any(word == k for k in batch)]
    # Uma palavra-chave por palavra do contexto, sempre junto da principal do lote: a busca
    # precisa ter todas as palavras de uma palavra-chave, então "atracoes" não atrapalha "nerf".
    keywords = [f"{batch[0]} {word}" if batch else word for word in extra]
    keywords.extend(batch)
    if not keywords:
        raise PhotoError("Informe ao menos uma palavra-chave.")
    return ", ".join(dict.fromkeys(keywords))[:500]


def check_public_url(url: str) -> None:
    """Só baixa de endereços públicos (nada da rede interna do servidor)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise PhotoError("Informe o endereço completo (começando com http:// ou https://).")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as exc:
        raise PhotoError("Não encontramos esse site.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise PhotoError("Endereço não permitido.")


def _check_request(request: httpx.Request) -> None:
    # Vale também para os redirecionamentos (o Dropbox redireciona para outro domínio).
    check_public_url(str(request.url))


def http_client(timeout: float = 30) -> httpx.Client:
    return httpx.Client(
        timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}, event_hooks={"request": [_check_request]}
    )


def direct_download_url(url: str) -> str:
    """Link de compartilhamento do Dropbox → download direto (pasta vem em .zip)."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host == "dropbox.com" or host.endswith(".dropbox.com"):
        query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key not in ("dl", "raw")]
        query.append(("dl", "1"))
        return urlunparse(parsed._replace(query=urlencode(query)))
    return url.strip()


def store_photo(data: bytes, filename: str = "foto.jpg") -> tuple[str, int, int]:
    """Guarda a cópia otimizada (WebP em várias larguras) e devolve (endereço, largura, altura)."""
    if len(data) > MAX_IMAGE_BYTES:
        raise PhotoError("Imagem grande demais (máximo de 30 MB).")
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            kind = (image.format or "").lower()
    except Exception as exc:  # noqa: BLE001
        raise PhotoError("Não conseguimos abrir essa imagem.") from exc
    variants = optimize_image(data)
    if variants:
        return media_storage.save_image_variants(variants), width, height
    content_type = {"jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(kind)
    if not content_type:
        raise PhotoError("Use imagens JPG, PNG ou WebP.")
    return media_storage.save(data, f"foto.{'jpg' if kind == 'jpeg' else kind}", content_type), width, height


@dataclass
class Credits:
    description: str | None = None
    author: str | None = None
    author_url: str | None = None
    source_name: str | None = None
    source_url: str | None = None


def save_curated_photo(
    db: Session, data: bytes, *, keywords: str, credits: Credits, origin: str, path: str = ""
) -> StockImage | None:
    """Cadastra a foto. Devolve None se a mesma imagem já estiver no banco."""
    provider_id = hashlib.sha1(data).hexdigest()[:40]
    if db.query(StockImage.id).filter(StockImage.provider == MANUAL_PROVIDER, StockImage.provider_id == provider_id).first():
        return None
    stored_url, width, height = store_photo(data, path or "foto.jpg")
    context = " ".join(context_words(path))
    image = StockImage(
        provider=MANUAL_PROVIDER,
        provider_id=provider_id,
        download_url=origin[:1000],
        stored_url=stored_url,
        tags=photo_keywords(keywords, path),
        alt=(credits.description or context or None),
        photographer=credits.author,
        photographer_url=credits.author_url,
        source_name=credits.source_name,
        page_url=credits.source_url,
        width=width,
        height=height,
        uses=0,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def download(url: str, limit: int) -> tuple[bytes, str]:
    """Baixa um arquivo (imagem ou .zip) e devolve (bytes, tipo)."""
    with http_client(timeout=120) as client:
        with client.stream("GET", url) as response:
            if response.status_code >= 400:
                raise PhotoError(f"O site respondeu com erro {response.status_code}. O link é público?")
            content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            if content_type == "text/html":
                raise PhotoError("O link abriu uma página, não um arquivo. Confira se o link é público (qualquer pessoa com o link).")
            with tempfile.SpooledTemporaryFile(max_size=50 * 1024 * 1024) as buffer:
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > limit:
                        raise PhotoError("Arquivo grande demais para importar de uma vez (máximo de 1 GB).")
                    buffer.write(chunk)
                buffer.seek(0)
                return buffer.read(), content_type


# Importações em andamento (um processo por contêiner; o painel consulta o andamento).
@dataclass
class ImportJob:
    id: str
    status: str = "running"  # running | done | error
    total: int = 0
    added: int = 0
    duplicates: int = 0
    skipped: list[str] = field(default_factory=list)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "status": self.status, "total": self.total, "added": self.added,
            "duplicates": self.duplicates, "skipped": self.skipped[:20], "error": self.error,
        }


_jobs: dict[str, ImportJob] = {}
_jobs_lock = threading.Lock()


def new_job() -> ImportJob:
    job = ImportJob(id=uuid.uuid4().hex[:12])
    with _jobs_lock:
        _jobs[job.id] = job
        if len(_jobs) > 50:
            for old in list(_jobs)[:-50]:
                _jobs.pop(old, None)
    return job


def get_job(job_id: str) -> ImportJob | None:
    return _jobs.get(job_id)


def strip_common_folders(paths: list[str]) -> list[str]:
    """Tira as pastas que todos os arquivos têm em comum (a pasta do lote não diz nada da foto)."""
    split = [PurePosixPath(path.replace("\\", "/")).parts for path in paths]
    if not split:
        return []
    common = 0
    while all(len(parts) > common + 1 for parts in split) and len({parts[common] for parts in split}) == 1:
        common += 1
    return ["/".join(parts[common:]) for parts in split]


def archive_images(data: bytes) -> list[tuple[str, bytes]]:
    """Imagens de dentro de um .zip (sem as pastas de sistema do Mac), com o caminho a partir
    das pastas que mudam entre as fotos."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise PhotoError("Não conseguimos abrir o arquivo .zip.") from exc
    images = []
    for info in archive.infolist():
        name = info.filename
        if info.is_dir() or "__MACOSX" in name or PurePosixPath(name).name.startswith("."):
            continue
        if PurePosixPath(name).suffix.lower() not in IMAGE_EXTENSIONS or info.file_size > MAX_IMAGE_BYTES:
            continue
        images.append((name, archive.read(info)))
        if len(images) >= MAX_IMPORT_FILES:
            break
    return list(zip(strip_common_folders([name for name, _ in images]), [content for _, content in images]))


def run_link_import(job: ImportJob, session_factory, url: str, keywords: str, credits: Credits) -> None:
    """Baixa o link (foto ou pasta em .zip) e cadastra cada imagem. Roda em segundo plano."""
    db: Session = session_factory()
    try:
        data, content_type = download(direct_download_url(url), MAX_ARCHIVE_BYTES)
        if data[:4] == b"PK\x03\x04" or content_type in ("application/zip", "application/x-zip-compressed"):
            files = archive_images(data)
        else:
            name = PurePosixPath(urlparse(url).path).name or "foto.jpg"
            files = [(name, data)]
        job.total = len(files)
        if not files:
            raise PhotoError("Não encontramos imagens JPG, PNG ou WebP nesse link.")
        for path, content in files:
            try:
                saved = save_curated_photo(db, content, keywords=keywords, credits=credits, origin=f"{url}#{path}", path=path)
            except PhotoError as exc:
                db.rollback()
                job.skipped.append(f"{PurePosixPath(path).name}: {exc}")
                continue
            if saved is None:
                job.duplicates += 1
            else:
                job.added += 1
        job.status = "done"
    except PhotoError as exc:
        job.status, job.error = "error", str(exc)
    except Exception as exc:  # noqa: BLE001 - o painel precisa saber que parou
        logger.exception("curated_import_failed job=%s", job.id)
        job.status, job.error = "error", f"Falha ao importar: {exc}"
    finally:
        db.close()
