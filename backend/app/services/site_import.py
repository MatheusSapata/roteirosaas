"""Importação do site inteiro de uma agência pelo assistente de IA.

Fluxo:
1. A pessoa cola o link da home de uma agência no chat. A raspagem (url_import) classifica a
   página como "central" (lista várias viagens). Em vez de chamar a IA, o chat devolve uma
   pergunta (central_question) e grava um SiteImportJob "awaiting_confirmation" com os links das
   viagens. Não gasta chamada da OpenAI nem conta no limite de mensagens.
2. A pessoa responde "completo" (ou parecido). O backend reconhece a resposta porque a última
   mensagem do assistente na conversa é a pergunta (começa por CENTRAL_QUESTION_PREFIX) e há um
   job aguardando confirmação para a mesma página e pessoa. O job passa para "running" e roda
   numa thread própria (mesmo padrão de hub_black.start_generation_thread).
   Se a home organiza as viagens em 2 ou mais categorias (url_import detecta o título da seção de
   cada card), antes de rodar vem uma segunda pergunta (categories_question, prefixo
   CATEGORIES_QUESTION_PREFIX, job "awaiting_categories"): manter as categorias ou juntar tudo.
   A resposta fica em job.preserve_categories e só então o job passa para "running".
3. A thread raspa uma viagem por vez: decide o nome (pick_unique_title), cria a página já com o
   nome e o endereço definitivos (rascunho, marcada com config_json["siteImport"]), liga a tag da
   categoria (quando preserve_categories), gera as seções com a IA e marca o item como feito ou
   com erro, sem parar os outros.
4. No fim, monta a home na página onde a conversa aconteceu, com os cards ligados às páginas
   novas (link_cards_to_pages + relink_original_urls + ensure_created_pages_linked). Com
   preserve_categories, a vitrine única vira uma seção "Links" por categoria (category_sections).

O andamento fica no próprio SiteImportJob e o painel consulta GET /ai-assistant/import-jobs/active.
"""
from __future__ import annotations

import asyncio
import logging
import re
import threading
import unicodedata
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Iterator

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.page import Page
from app.models.site_import_job import SiteImportJob
from app.services.url_import import (
    ImportedPage,
    UrlImportError,
    build_url_context_block,
    download_page_images,
    normalize_url,
    scrape_page,
)

logger = logging.getLogger(__name__)

# Teto de páginas de viagem criadas por importação completa (a home não conta).
MAX_SITE_IMPORT_PAGES = 20
# Job "running" sem nenhum passo gravado há mais que isso (container reiniciado no meio) vira erro
# e deixa de travar uma importação nova da agência. Um passo (raspar + IA de uma viagem) leva
# poucos minutos; 15 dá folga para a IA lenta.
STALE_AFTER = timedelta(minutes=15)
# Job concluído aparece no endpoint de andamento por este tempo (para o aviso do painel mostrar o fim).
RECENT_FINISHED_WINDOW = timedelta(hours=1)
# Marca na config da página criada pela importação, enquanto ela ainda não tem seções.
PAGE_MARKER = "siteImport"
MAX_TITLE_CHARS = 200

STATUS_AWAITING = "awaiting_confirmation"
STATUS_AWAITING_CATEGORIES = "awaiting_categories"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Estágios de cada item (e da home): aguardando, raspando, gerando, concluído, erro.
STAGE_WAITING = "waiting"
STAGE_SCRAPING = "scraping"
STAGE_GENERATING = "generating"
STAGE_DONE = "done"
STAGE_ERROR = "error"

CENTRAL_QUESTION_PREFIX = "Essa página parece ser a principal de um site"
CATEGORIES_QUESTION_PREFIX = "Essa página organiza as viagens em categorias"
# Pergunta das categorias só quando há separação de verdade: com uma categoria só (ex.: um único
# título "Próximas saídas" em cima de todos os cards) não há o que manter separado.
MIN_CATEGORIES_TO_ASK = 2
# Seção da home com as viagens que ficaram sem categoria (quando outras têm).
UNCATEGORIZED_TITLE = "Outras viagens"
# Quantas categorias citar de exemplo na pergunta.
CATEGORIES_EXAMPLES = 3


# ---------------------------------------------------------------------------
# Pergunta no chat e reconhecimento da resposta
# ---------------------------------------------------------------------------


def central_question(found: int) -> str:
    extra = f" Como passa de {MAX_SITE_IMPORT_PAGES}, monto as {MAX_SITE_IMPORT_PAGES} primeiras." if found > MAX_SITE_IMPORT_PAGES else ""
    return (
        f"{CENTRAL_QUESTION_PREFIX}, com várias viagens (encontrei {found} links de viagem diferentes). "
        f"Quer que eu monte o site inteiro (até {MAX_SITE_IMPORT_PAGES} páginas) ou só uma viagem específica?{extra} "
        "Responda 'completo' para montar tudo, ou cole o link da viagem que quer. "
        "Se era só esta página mesmo, cole o mesmo link de novo."
    )


def _plain_key(value: str) -> str:
    """Texto para comparar: sem acento, minúsculo, espaços simples."""
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", normalized.casefold()).strip()


_CONFIRM_NEGATIVE_RE = re.compile(r"\b(nao|so uma|apenas uma|somente uma|uma so|so essa|so esta|so esse|so este|so a viagem)\b")
_CONFIRM_POSITIVE_RE = re.compile(
    r"\b(completo|completa|tudo|todas|todos|inteiro|inteira|site todo|todo o site|site completo)\b"
)
_CONFIRM_SHORT = frozenset(
    {
        "sim", "s", "ss", "pode", "pode sim", "sim pode", "quero", "quero sim", "bora", "vai", "ok", "okay",
        "isso", "isso mesmo", "claro", "beleza", "fechado", "pode montar", "pode fazer", "monta", "monte",
        "pode ser", "manda ver", "faz", "faca", "por favor", "sim por favor", "pode ir",
    }
)


def is_full_import_confirmation(text: str) -> bool:
    """"completo", "sim", "tudo", "o site inteiro", "pode montar tudo"... Resposta curta e sem
    negação ("não", "só uma"). Só é consultada logo depois da pergunta de central/específica."""
    key = re.sub(r"[^\w\s]", " ", _plain_key(text))
    key = re.sub(r"\s+", " ", key).strip()
    if not key or len(key) > 80:
        return False
    if _CONFIRM_NEGATIVE_RE.search(key):
        return False
    if key in _CONFIRM_SHORT or _CONFIRM_POSITIVE_RE.search(key):
        return True
    return key.startswith("sim ") and len(key) <= 30


def is_central_question(message: str | None) -> bool:
    return bool(message) and message.strip().startswith(CENTRAL_QUESTION_PREFIX)


def _latest_awaiting_job(db: Session, page_id: int, user_id: int) -> SiteImportJob | None:
    return (
        db.query(SiteImportJob)
        .filter(
            SiteImportJob.page_id == page_id,
            SiteImportJob.user_id == user_id,
            SiteImportJob.status == STATUS_AWAITING,
        )
        .order_by(SiteImportJob.id.desc())
        .first()
    )


def pending_confirmation_job(
    db: Session, page_id: int, user_id: int, last_assistant_message: str | None, user_text: str
) -> SiteImportJob | None:
    """Job aguardando confirmação quando a mensagem do usuário confirma a pergunta que o
    assistente acabou de fazer. Sem a pergunta como última resposta, "sim" é só conversa."""
    if not is_central_question(last_assistant_message) or not is_full_import_confirmation(user_text):
        return None
    return _latest_awaiting_job(db, page_id, user_id)


def is_repeat_of_pending_central(
    db: Session, page_id: int, user_id: int, last_assistant_message: str | None, url: str
) -> bool:
    """Depois da pergunta, a pessoa colou o mesmo link de novo: era só aquela página mesmo."""
    if not is_central_question(last_assistant_message):
        return False
    job = _latest_awaiting_job(db, page_id, user_id)
    return bool(job) and normalize_url(job.source_url) == normalize_url(url)


# ---------------------------------------------------------------------------
# Segunda pergunta (só quando a home tem categorias): manter ou juntar
# ---------------------------------------------------------------------------


def _item_position(item: dict, fallback: int) -> int:
    value = item.get("position")
    return value if isinstance(value, int) else fallback


def job_categories(job: SiteImportJob) -> list[str]:
    """Categorias distintas das viagens do job, na ordem em que aparecem no site original."""
    first_seen: dict[str, int] = {}
    for index, item in enumerate(job.items or []):
        category = item.get("category")
        if category:
            position = _item_position(item, index)
            if category not in first_seen or position < first_seen[category]:
                first_seen[category] = position
    return sorted(first_seen, key=lambda name: first_seen[name])


def categories_question(categories: list[str]) -> str:
    examples = categories[:CATEGORIES_EXAMPLES]
    listed = ", ".join(f'"{name}"' for name in examples)
    if len(categories) > len(examples):
        rest = len(categories) - len(examples)
        listed += f" e mais {rest} {'categoria' if rest == 1 else 'categorias'}"
    return (
        f"{CATEGORIES_QUESTION_PREFIX} (ex.: {listed}). Quer manter essa separação? Cada categoria vira uma "
        "tag nas páginas das viagens, e a página principal fica com uma seção por categoria. Responda 'manter' "
        "para separar por categoria ou 'juntar' para colocar todas as viagens numa lista só."
    )


def is_categories_question(message: str | None) -> bool:
    return bool(message) and message.strip().startswith(CATEGORIES_QUESTION_PREFIX)


# Manter: "manter", "mantém", "separar", "separado", "por categoria", "cada uma na sua"...
_KEEP_RE = re.compile(
    r"\b(mant(?:er|em|enha|enho|ido|ida|idas|idos)?|separ(?:ar|a|e|ado|ada|ados|adas|ando|acao)|"
    r"por categorias?|com (?:as )?categorias|cada (?:uma|categoria) (?:na|em) (?:sua|seu)|uma secao por categoria|"
    r"dividid[oa]s?|divid(?:ir|e|a))\b"
)
# Juntar: "juntar", "tudo junto", "lista única", "uma lista só", "misturar", "sem categoria"...
_JOIN_RE = re.compile(
    r"\b(junt(?:ar|a|e|o|as|os|inho)|unir|une|uni(?:fica|ficar)|mistur(?:ar|a|e|ado|ados)|"
    r"lista (?:unica|so)|uma lista|uma (?:vitrine|secao) so|uma so lista|sem (?:as )?categorias?|todas juntas|tudo junto)\b"
)
# "não" logo antes de uma das opções inverte o sentido ("não precisa separar" = juntar).
_NEGATION_BEFORE_RE = re.compile(r"\b(?:nao|sem)\s+(?:quero\s+|precisa\s+(?:de\s+)?|vou\s+|e\s+pra\s+|e\s+para\s+)?$")
_KEEP_SHORT = frozenset(
    {
        "sim", "s", "ss", "pode", "pode sim", "sim pode", "quero", "quero sim", "isso", "isso mesmo", "claro", "ok",
        "okay", "beleza", "fechado", "bora", "pode ser", "sim por favor", "por favor",
    }
)
_JOIN_SHORT = frozenset({"nao", "n", "nao obrigado", "nao obrigada", "nao precisa", "nao quero", "melhor nao"})


def categories_answer(text: str) -> bool | None:
    """Resposta à pergunta das categorias: True = manter, False = juntar, None = não deu para saber
    (a conversa segue normal, com a IA). "sim"/"manter"/"separar" mantêm; "não"/"juntar"/"tudo junto"
    juntam; "não" logo antes de uma opção inverte ("não precisa separar" junta)."""
    key = re.sub(r"[^\w\s]", " ", _plain_key(text))
    key = re.sub(r"\s+", " ", key).strip()
    if not key or len(key) > 80:
        return None
    if key in _KEEP_SHORT:
        return True
    if key in _JOIN_SHORT:
        return False
    votes: set[bool] = set()
    for pattern, meaning in ((_KEEP_RE, True), (_JOIN_RE, False)):
        for match in pattern.finditer(key):
            negated = bool(_NEGATION_BEFORE_RE.search(key[: match.start()]))
            votes.add(meaning != negated)
    if len(votes) == 1:
        return votes.pop()
    if not votes and re.match(r"^(sim|pode|quero)\b", key) and len(key) <= 30:
        return True
    if not votes and re.match(r"^nao\b", key) and len(key) <= 30:
        return False
    return None


def pending_categories_job(
    db: Session, page_id: int, user_id: int, last_assistant_message: str | None, user_text: str
) -> tuple[SiteImportJob, bool] | None:
    """(job, manter?) quando a mensagem do usuário responde a pergunta das categorias que o
    assistente acabou de fazer. Sem a pergunta como última resposta, "manter" é só conversa."""
    if not is_categories_question(last_assistant_message):
        return None
    decision = categories_answer(user_text)
    if decision is None:
        return None
    job = (
        db.query(SiteImportJob)
        .filter(
            SiteImportJob.page_id == page_id,
            SiteImportJob.user_id == user_id,
            SiteImportJob.status == STATUS_AWAITING_CATEGORIES,
        )
        .order_by(SiteImportJob.id.desc())
        .first()
    )
    return (job, decision) if job else None


def confirm_full_import(db: Session, job: SiteImportJob, include_images: bool = True) -> str:
    """A pessoa respondeu "completo". Com categorias na home, faz a segunda pergunta (job fica
    "awaiting_categories"); sem, dispara a importação direto, como sempre."""
    categories = job_categories(job)
    if len(categories) < MIN_CATEGORIES_TO_ASK:
        return start_job(db, job, include_images)
    if running_job(db, job.agency_id):
        return ALREADY_RUNNING_MESSAGE
    job.status = STATUS_AWAITING_CATEGORIES
    db.commit()
    return categories_question(categories)


def create_pending_job(db: Session, page: Page, user_id: int, url: str, imported: ImportedPage) -> SiteImportJob:
    items = [
        {
            "url": link.url,
            "card_title": link.title,
            "price": link.price,
            "card_text": link.text,
            "category": link.category,
            "position": link.position,
            "title": None,
            "stage": STAGE_WAITING,
            "page_id": None,
            "slug": None,
            "error": None,
        }
        for link in imported.trip_links[:MAX_SITE_IMPORT_PAGES]
    ]
    job = SiteImportJob(
        agency_id=page.agency_id,
        page_id=page.id,
        user_id=user_id,
        source_url=url[:2000],
        source_title=(imported.title or "")[:255] or None,
        status=STATUS_AWAITING,
        total_found=len(imported.trip_links),
        items=items,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# Andamento e limite de um job por agência
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def expire_stale_jobs(db: Session, agency_id: int) -> None:
    """Job "running" parado (container reiniciado no meio) vira "failed" e libera a agência."""
    limit = _now() - STALE_AFTER
    changed = False
    for job in db.query(SiteImportJob).filter(SiteImportJob.agency_id == agency_id, SiteImportJob.status == STATUS_RUNNING).all():
        last = _aware(job.updated_at) or _aware(job.started_at)
        if last and last >= limit:
            continue
        items = deepcopy(job.items or [])
        for item in items:
            if item.get("stage") not in (STAGE_DONE, STAGE_ERROR):
                item["stage"] = STAGE_ERROR
                item["error"] = item.get("error") or "A importação foi interrompida."
        job.items = items
        flag_modified(job, "items")
        if job.home_stage not in (STAGE_DONE, STAGE_ERROR):
            job.home_stage = STAGE_ERROR
        job.status = STATUS_FAILED
        job.error = "A importação foi interrompida (o servidor reiniciou no meio). As páginas já criadas continuam na lista."
        job.finished_at = _now()
        changed = True
    if changed:
        db.commit()


def running_job(db: Session, agency_id: int) -> SiteImportJob | None:
    expire_stale_jobs(db, agency_id)
    return (
        db.query(SiteImportJob)
        .filter(SiteImportJob.agency_id == agency_id, SiteImportJob.status == STATUS_RUNNING)
        .first()
    )


ALREADY_RUNNING_MESSAGE = (
    "Já tem uma importação de site completo em andamento nesta empresa. Espere ela terminar para começar "
    "outra. Enquanto isso, você pode continuar usando o assistente normalmente, inclusive para importar uma "
    "página de viagem só."
)


def start_job(db: Session, job: SiteImportJob, include_images: bool = True, preserve_categories: bool | None = None) -> str:
    """Confirma o job e dispara a thread. Devolve a resposta do assistente para o chat.
    preserve_categories: resposta à pergunta das categorias (None quando não houve pergunta)."""
    if running_job(db, job.agency_id):
        return ALREADY_RUNNING_MESSAGE
    job.status = STATUS_RUNNING
    job.stage = "pages"
    job.home_stage = STAGE_WAITING
    job.include_images = bool(include_images)
    job.preserve_categories = preserve_categories
    job.started_at = _now()
    try:
        db.commit()
    except IntegrityError:
        # Outra confirmação da mesma agência ganhou a corrida (índice único de job "running").
        db.rollback()
        return ALREADY_RUNNING_MESSAGE
    start_job_thread(job.id)
    count = len(job.items or [])
    pages = "1 página de viagem" if count == 1 else f"{count} páginas de viagem"
    categories = (
        " Cada viagem ganha a tag da categoria dela, e a página principal fica com uma seção por categoria."
        if preserve_categories
        else ""
    )
    return (
        f"Combinado! Comecei a montar o site inteiro: {pages}, uma de cada vez. Cada página já aparece na "
        "lista de páginas com o nome certo assim que começa a ser montada. Por último, monto esta página como "
        f"a página principal, com os cards levando para as páginas novas.{categories} Isso leva alguns minutos e você pode "
        "fechar o editor. Até terminar, evite salvar esta página para não apagar a página principal que vou "
        "montar; quando acabar, recarregue para ver o resultado."
    )


def describe_job(job: SiteImportJob, home: Page | None = None) -> dict[str, Any]:
    items = []
    for item in job.items or []:
        items.append(
            {
                "url": item.get("url") or "",
                "title": item.get("title") or item.get("card_title") or item.get("url") or "",
                "stage": item.get("stage") or STAGE_WAITING,
                "page_id": item.get("page_id"),
                "slug": item.get("slug"),
                "error": item.get("error"),
            }
        )
    return {
        "id": job.id,
        "agency_id": job.agency_id,
        "status": job.status,
        "stage": job.stage,
        "source_url": job.source_url,
        "source_title": job.source_title,
        "total_found": int(job.total_found or 0),
        "total": len(items),
        "done": sum(1 for item in items if item["stage"] == STAGE_DONE),
        "failed": sum(1 for item in items if item["stage"] == STAGE_ERROR),
        "items": items,
        "home": {
            "page_id": job.page_id,
            "slug": home.slug if home else None,
            "title": home.title if home else None,
            "stage": job.home_stage or STAGE_WAITING,
        },
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


def get_job(db: Session, job_id: int) -> SiteImportJob | None:
    return db.query(SiteImportJob).filter(SiteImportJob.id == job_id).first()


def completed_page_ids(job: SiteImportJob) -> list[int]:
    """Páginas prontas desta importação (viagens concluídas + a principal), para publicar em
    lote. Viagem com erro fica de fora (nunca ganhou página)."""
    ids = [item["page_id"] for item in (job.items or []) if item.get("stage") == STAGE_DONE and item.get("page_id")]
    if job.page_id:
        ids.append(job.page_id)
    return ids


def active_job_for_agencies(db: Session, agency_ids: Iterable[int]) -> SiteImportJob | None:
    """Job em andamento ou concluído há pouco (RECENT_FINISHED_WINDOW) das agências informadas."""
    ids = list(dict.fromkeys(agency_ids))
    if not ids:
        return None
    for agency_id in ids:
        expire_stale_jobs(db, agency_id)
    running = (
        db.query(SiteImportJob)
        .filter(SiteImportJob.agency_id.in_(ids), SiteImportJob.status == STATUS_RUNNING)
        .order_by(SiteImportJob.started_at.desc())
        .first()
    )
    if running:
        return running
    recent = (
        db.query(SiteImportJob)
        .filter(
            SiteImportJob.agency_id.in_(ids),
            SiteImportJob.status.in_((STATUS_COMPLETED, STATUS_FAILED)),
            SiteImportJob.finished_at.isnot(None),
        )
        .order_by(SiteImportJob.finished_at.desc())
        .first()
    )
    if recent and (_aware(recent.finished_at) or _now()) >= _now() - RECENT_FINISHED_WINDOW:
        return recent
    return None


# ---------------------------------------------------------------------------
# Nome da página: título raspado, com desempate
# ---------------------------------------------------------------------------

_TITLE_SEPARATOR_RE = re.compile(r"\s+(?:\||–|—|-|::|·|•)\s+")
_MONTHS = {
    "janeiro": "jan", "fevereiro": "fev", "marco": "mar", "abril": "abr", "maio": "mai", "junho": "jun",
    "julho": "jul", "agosto": "ago", "setembro": "set", "outubro": "out", "novembro": "nov", "dezembro": "dez",
}
_MONTH_RE = (
    r"(janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|"
    r"jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.?"
)
_RANGE_SEP = r"\s*(?:a|à|-|–|até|ate)\s*"
_DATE_PATTERNS = (
    # 28 de junho a 2 de julho
    re.compile(rf"\b(\d{{1,2}})\s+de\s+{_MONTH_RE}{_RANGE_SEP}(\d{{1,2}})\s+de\s+{_MONTH_RE}(?![a-zç])", re.IGNORECASE),
    # 23 a 28 de junho
    re.compile(rf"\b(\d{{1,2}}){_RANGE_SEP}(\d{{1,2}})\s+de\s+{_MONTH_RE}(?![a-zç])", re.IGNORECASE),
    # 23/06 a 28/06 (com ou sem ano)
    re.compile(r"\b(\d{1,2}/\d{1,2})(?:/\d{2,4})?" + _RANGE_SEP + r"(\d{1,2}/\d{1,2})(?:/\d{2,4})?\b"),
    # 23 de junho
    re.compile(rf"\b(\d{{1,2}})\s+de\s+{_MONTH_RE}(?![a-zç])", re.IGNORECASE),
    # 23/06/2026
    re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b"),
)
_DESTINATION_LABEL_RE = re.compile(
    r"\b(?:destino|cidade|local|localiza[cç][aã]o|regi[aã]o)\s*[:\-–]\s*([^\n|•·,;.()]{2,40})", re.IGNORECASE
)
_NAME = r"[A-ZÀ-Ý][\wÀ-ÿ'’]+"
_DESTINATION_PHRASE_RE = re.compile(
    rf"(?i:\b(?:viagem|pacote|excurs[aã]o|roteiro|tour|passeio|bate-volta)\s+(?:para|pra|a|ao|à|em|no|na)\s+)"
    rf"({_NAME}(?:\s+(?:(?:de|do|da|dos|das|e)\s+)?{_NAME}){{0,3}})"
)
_DAYS_RE = re.compile(r"\b(\d{1,2})\s*dias\b", re.IGNORECASE)
_NIGHTS_RE = re.compile(r"\b(\d{1,2})\s*noites\b", re.IGNORECASE)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_site_name(title: str, site_title: str | None) -> str:
    """Tira o nome do site do título raspado ("Pacote Gramado | Agência X" vira "Pacote Gramado")
    quando esse pedaço também está no título da home do mesmo site."""
    title = _clean_text(title)
    if not site_title:
        return title
    site_parts = {_plain_key(part) for part in _TITLE_SEPARATOR_RE.split(_clean_text(site_title)) if part.strip()}
    site_key = _plain_key(site_title)
    parts = [part for part in _TITLE_SEPARATOR_RE.split(title) if part.strip()]
    if len(parts) < 2:
        return title
    if _plain_key(parts[-1]) in site_parts or (len(_plain_key(parts[-1])) >= 4 and _plain_key(parts[-1]) in site_key):
        parts = parts[:-1]
    elif _plain_key(parts[0]) in site_parts:
        parts = parts[1:]
    return " - ".join(parts).strip() or title


def _format_date(match: re.Match[str]) -> str:
    def month(value: str) -> str:
        key = _plain_key(value).rstrip(".")
        return _MONTHS.get(key, key[:3])

    groups = match.groups()
    if len(groups) == 4:
        return f"{int(groups[0])} de {month(groups[1])} a {int(groups[2])} de {month(groups[3])}"
    if len(groups) == 3:
        return f"{int(groups[0])} a {int(groups[1])} de {month(groups[2])}"
    if len(groups) == 2 and "/" in groups[0]:
        return f"{groups[0]} a {groups[1]}"
    if len(groups) == 2:
        return f"{int(groups[0])} de {month(groups[1])}"
    return groups[0]


def _first_destination(title: str, text: str) -> str | None:
    title_key = _plain_key(title)
    for pattern in (_DESTINATION_LABEL_RE, _DESTINATION_PHRASE_RE):
        for match in pattern.finditer(text):
            value = _clean_text(match.group(1)).strip(" -–:")
            if len(value) < 2 or _plain_key(value) in title_key:
                continue
            return value[:40]
    return None


def _first_duration(title: str, text: str) -> str | None:
    title_key = _plain_key(title)
    for pattern, word in ((_DAYS_RE, "dias"), (_NIGHTS_RE, "noites")):
        match = pattern.search(text)
        if match:
            value = f"{int(match.group(1))} {word}"
            if value not in title_key:
                return value
    return None


def _first_date(title: str, text: str) -> str | None:
    title_key = _plain_key(title)
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            value = _format_date(match)
            if _plain_key(value) not in title_key:
                return value
    return None


def _title_features(title: str, text: str) -> Iterator[str]:
    """Característica que distingue a viagem, na ordem: destino, duração, data."""
    for finder in (_first_destination, _first_duration, _first_date):
        value = finder(title, text or "")
        if value:
            yield value


def pick_unique_title(base_title: str, text: str, existing_titles: Iterable[str]) -> str:
    """Nome da página nova: o título raspado; se a agência já tem uma página com esse nome exato
    (sem diferenciar maiúsculas e acentos), completa com o destino ("— Gramado"), a duração
    ("— 3 dias") ou a data ("— 23 a 28 de jun"), nessa ordem, usando o que achar no texto raspado.
    Sufixo numérico ("(2)") só quando nada disso desempata."""
    base = _clean_text(base_title)[:MAX_TITLE_CHARS] or "Viagem"
    taken = {_plain_key(title) for title in existing_titles if title}
    if _plain_key(base) not in taken:
        return base
    for feature in _title_features(base, text):
        candidate = f"{base} — {feature}"[:MAX_TITLE_CHARS]
        if _plain_key(candidate) not in taken:
            return candidate
    number = 2
    while True:
        candidate = f"{base[: MAX_TITLE_CHARS - 6]} ({number})"
        if _plain_key(candidate) not in taken:
            return candidate
        number += 1


# ---------------------------------------------------------------------------
# Religar os links da home às páginas novas
# ---------------------------------------------------------------------------


def _card_to_page(card: dict, target: dict[str, Any]) -> None:
    card["source"] = "page"
    card["pageId"] = target["page_id"]
    card["url"] = target["url"]
    card["openInNewTab"] = False


def relink_original_urls(node: Any, url_map: dict[str, dict[str, Any]]) -> int:
    """Troca, em toda a config, qualquer link para uma URL original de viagem pelo endereço da
    página nova. url_map: normalize_url(url original) -> {"page_id", "url"}. Card de Links/Roteiros
    com o link vira card de página (source "page", pageId). Também troca href="..." dentro de texto
    rico. Devolve quantas trocas fez."""
    replaced = 0

    def target_for(value: str) -> dict[str, Any] | None:
        if not value or not value.lower().startswith(("http://", "https://", "//")):
            return None
        return url_map.get(normalize_url(value if not value.startswith("//") else f"https:{value}"))

    def replace_hrefs(value: str) -> str:
        nonlocal replaced

        def swap(match: re.Match[str]) -> str:
            nonlocal replaced
            target = target_for(match.group(2))
            if not target:
                return match.group(0)
            replaced += 1
            return f"{match.group(1)}{target['url']}{match.group(3)}"

        return re.sub(r"""(href=["'])([^"']+)(["'])""", swap, value)

    def walk(current: Any) -> None:
        nonlocal replaced
        if isinstance(current, list):
            for index, item in enumerate(current):
                if isinstance(item, str):
                    target = target_for(item)
                    if target:
                        current[index] = target["url"]
                        replaced += 1
                    elif "href=" in item:
                        current[index] = replace_hrefs(item)
                else:
                    walk(item)
            return
        if not isinstance(current, dict):
            return
        for key, value in list(current.items()):
            if isinstance(value, str):
                target = target_for(value)
                if target:
                    if key == "url" and ("source" in current or "title" in current):
                        _card_to_page(current, target)
                    else:
                        current[key] = target["url"]
                    replaced += 1
                elif "href=" in value:
                    current[key] = replace_hrefs(value)
            else:
                walk(value)

    walk(node)
    return replaced


def link_cards_to_pages(
    sections: list[dict], pages_by_slug: dict[str, dict[str, Any]], pages_by_title: dict[str, dict[str, Any]] | None = None
) -> None:
    """Card de Links/Roteiros com "Página: slug" (pageSlug) vira card ligado à página, como o editor
    faz ao aplicar a resposta da IA (prepareAiSection). Sem pageSlug, um card com o mesmo título de
    uma página criada nesta importação também é ligado a ela."""
    from app.services.ai_assistant import AI_IMAGE_PLACEHOLDER

    for section in sections:
        if not isinstance(section, dict) or section.get("type") != "links":
            continue
        for card in section.get("items") or []:
            if not isinstance(card, dict):
                continue
            slug = card.pop("pageSlug", None)
            target = pages_by_slug.get(slug) if slug else None
            if target is None and pages_by_title and not card.get("pageId"):
                title = card.get("title")
                title = title.get("pt") if isinstance(title, dict) else title
                target = pages_by_title.get(_plain_key(str(title or "")))
            if target is None:
                continue
            _card_to_page(card, target)
            if target.get("image") and (not card.get("image") or card.get("image") == AI_IMAGE_PLACEHOLDER):
                card["image"] = target["image"]


def linked_page_ids(node: Any) -> set[int]:
    found: set[int] = set()
    if isinstance(node, list):
        for item in node:
            found |= linked_page_ids(item)
    elif isinstance(node, dict):
        if node.get("source") == "page" and isinstance(node.get("pageId"), int):
            found.add(node["pageId"])
        for value in node.values():
            if isinstance(value, (dict, list)):
                found |= linked_page_ids(value)
    return found


def ensure_created_pages_linked(sections: list[dict], created: list[dict[str, Any]]) -> bool:
    """Se a IA não pôs nenhuma das páginas criadas na home, acrescenta uma vitrine com todas,
    antes do rodapé. Devolve True quando acrescentou."""
    if not created or linked_page_ids(sections) & {item["page_id"] for item in created}:
        return False
    cards = [_showcase_card(item) for item in created]
    section = {
        "type": "links",
        "enabled": True,
        "anchorId": "viagens-importadas",
        "title": "Nossas viagens",
        "subtitle": "",
        "items": cards,
        "carouselEnabled": len(cards) > 3,
    }
    sections.insert(_footer_position(sections), section)
    return True


_FOOTER_TYPES = {"agency_footer", "footer", "free_footer_brand"}


def _footer_position(sections: list[dict]) -> int:
    """Índice logo antes do rodapé (ou o fim, sem rodapé)."""
    return next(
        (index for index, item in enumerate(sections) if isinstance(item, dict) and item.get("type") in _FOOTER_TYPES),
        len(sections),
    )


def _showcase_card(item: dict[str, Any]) -> dict[str, Any]:
    """Card de vitrine ligado a uma página criada pela importação (o que a IA não montou)."""
    return {
        "id": f"site-import-{item['page_id']}",
        "source": "page",
        "pageId": item["page_id"],
        "url": item["url"],
        "image": item.get("image") or "",
        "title": item["title"],
        "description": "",
        "buttonLabel": "Ver roteiro",
        "openInNewTab": False,
        "showDates": False,
        "showPrice": bool(item.get("price")),
        "pricePrefix": "a partir de" if item.get("price") else "",
        "priceValue": item.get("price") or "",
        "priceSuffix": "",
    }


def group_created_by_category(created: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    """Páginas criadas agrupadas pela categoria do site original: categorias na ordem em que
    apareceram no site, cards na ordem do site dentro de cada uma. As viagens sem categoria (quando
    outras têm) vão para uma última seção, UNCATEGORIZED_TITLE. Lista vazia quando nenhuma página
    criada tem categoria (aí a home segue com a vitrine única de sempre)."""
    ordered = sorted(enumerate(created), key=lambda pair: (_item_position(pair[1], pair[0]), pair[0]))
    groups: dict[str, list[dict[str, Any]]] = {}
    loose: list[dict[str, Any]] = []
    for _index, item in ordered:
        if item.get("category"):
            groups.setdefault(item["category"], []).append(item)
        else:
            loose.append(item)
    if not groups:
        return []
    result = list(groups.items())
    if loose:
        result.append((UNCATEGORIZED_TITLE, loose))
    return result


def place_category_sections(sections: list[dict], groups: list[tuple[str, list[dict[str, Any]]]]) -> None:
    """Troca a vitrine de viagens da home por uma seção "Links" por categoria, no mesmo lugar.

    A vitrine é a seção Links (ou as seções) com algum card já ligado a uma página criada (depois
    de link_cards_to_pages e relink_original_urls). Card que a IA já montou para a página (com
    descrição, datas, preço) é reaproveitado; o que faltar ganha o card padrão (_showcase_card).
    Sem vitrine da IA, as seções entram antes do rodapé, como em ensure_created_pages_linked."""
    from app.services.page_tags import slugify_tag

    created_ids = {item["page_id"] for _name, items in groups for item in items}
    showcase = [
        index
        for index, section in enumerate(sections)
        if isinstance(section, dict) and section.get("type") == "links" and linked_page_ids(section) & created_ids
    ]
    ai_cards: dict[int, dict] = {}
    for index in showcase:
        for card in sections[index].get("items") or []:
            if isinstance(card, dict) and card.get("source") == "page" and card.get("pageId") in created_ids:
                ai_cards.setdefault(card["pageId"], card)
    position = showcase[0] if showcase else _footer_position(sections)
    for index in reversed(showcase):
        sections.pop(index)

    used_anchors = {section.get("anchorId") for section in sections if isinstance(section, dict)}
    new_sections = []
    for name, items in groups:
        anchor = base_anchor = slugify_tag(name) or "viagens"
        number = 2
        while anchor in used_anchors:
            anchor = f"{base_anchor}-{number}"
            number += 1
        used_anchors.add(anchor)
        cards = [deepcopy(ai_cards[item["page_id"]]) if item["page_id"] in ai_cards else _showcase_card(item) for item in items]
        new_sections.append(
            {
                "type": "links",
                "enabled": True,
                "anchorId": anchor,
                "title": name,
                "subtitle": "",
                "items": cards,
                "mode": "manual",
                "carouselEnabled": len(cards) > 3,
            }
        )
    sections[position:position] = new_sections


def _fits_section_limit(db: Session, agency_id: int, sections: list[dict]) -> bool:
    """O plano da agência comporta essa quantidade de seções? (plano free: 4; rodapé free não conta)."""
    from app.api.v1.endpoints.pages import resolve_agency_plan
    from app.services.plans import plan_limits

    _max_pages, max_sections = plan_limits(resolve_agency_plan(db, agency_id))
    regular = [section for section in sections if not (isinstance(section, dict) and section.get("type") == "free_footer_brand")]
    return max_sections is None or len(regular) <= max_sections


# ---------------------------------------------------------------------------
# Execução em segundo plano
# ---------------------------------------------------------------------------


def _error_text(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)[:500]
    if isinstance(exc, UrlImportError):
        return str(exc)[:500]
    return "Não consegui montar esta página. Tente importar o link dela sozinho pelo assistente."


def _save(db: Session, job: SiteImportJob) -> None:
    if "items" in job.__dict__:  # depois de um commit o atributo expira e não há o que marcar
        flag_modified(job, "items")
    job.updated_at = _now()
    db.add(job)
    db.commit()


def _set_item(db: Session, job: SiteImportJob, index: int, **changes: Any) -> None:
    items = deepcopy(job.items or [])
    items[index].update(changes)
    job.items = items
    _save(db, job)


def _strip_ai_keys(sections: list[dict]) -> None:
    """Mesma limpeza do create-page-base: tira as marcas internas da IA antes de gravar."""
    for section in sections:
        for key in ("aiReplaces", "aiStockPhoto", "aiPhotoOrigins", "aiSetKeys", "aiFlights"):
            section.pop(key, None)
        if section.get("type") == "header":
            section.setdefault("links", [])
        if section.get("type") == "header" and isinstance(section.get("links"), list):
            section["links"] = [
                {key: value for key, value in link.items() if key != "aiTargetLabel"}
                for link in section["links"]
                if isinstance(link, dict) and (link.get("target") or link.get("targetType") != "section")
            ]
        if section.get("type") == "links":
            for card in section.get("items") or []:
                if isinstance(card, dict):
                    card.pop("pageSlug", None)


def _page_targets(db: Session, agency_id: int) -> tuple[dict[str, dict[str, Any]], str]:
    from app.models.agency import Agency
    from app.services.page_tags import agency_page_base

    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    base = agency_page_base(db, agency) if agency else "/"
    targets = {
        page.slug: {"page_id": page.id, "slug": page.slug, "url": f"{base}{page.slug}", "image": page.cover_image_url or "", "title": page.title}
        for page in db.query(Page).filter(Page.agency_id == agency_id).all()
    }
    return targets, base


async def _ask_ai(db: Session, page: Page, request: str, attachments: list, context: str) -> str:
    from app.services.ai_assistant import ChatMessage, _reply_has_structure, generate_ai_assistant_reply
    from app.services.construtor_prompt import get_active_gpt_model

    model = get_active_gpt_model(db, create_if_missing=True)
    conversation = [ChatMessage(role="user", content=request)]
    reply = generate_ai_assistant_reply(conversation, attachments, model_override=model, context=context)
    if not _reply_has_structure(reply):
        # A IA respondeu com perguntas: pede a estrutura com o que já tem (como no hub_black).
        conversation += [
            ChatMessage(role="assistant", content=reply),
            ChatMessage(role="user", content="Não pergunte nada. Monte agora a estrutura completa da página com as informações que já tem."),
        ]
        reply = generate_ai_assistant_reply(conversation, attachments, model_override=model, context=context)
    return reply


async def _build_context(db: Session, page: Page, url: str, imported: ImportedPage, attachments: list, include_images: bool) -> tuple[str, list[str]]:
    from app.api.v1.endpoints.ai_assistant import _save_chat_photos
    from app.services.ai_assistant_context import build_agency_context

    sent_photos = await _save_chat_photos(db, page.agency_id, attachments)
    context = build_agency_context(db, page, [], include_images=include_images)
    context = f"{context}\n{build_url_context_block(url, imported)}"
    if sent_photos:
        lines = [
            "IMAGENS DA PÁGINA DO LINK (já estão na biblioteca de mídia da agência). Para usar uma numa seção, "
            'escreva "Imagem: endereço" com o endereço abaixo (sem "Busca de imagem"):'
        ]
        lines.extend(f"- {name}: {photo_url}" for name, photo_url in sent_photos)
        context = f"{context}\n" + "\n".join(lines)
    return context, [photo_url for _name, photo_url in sent_photos]


def _apply_reply(
    db: Session,
    page: Page,
    reply: str,
    photo_urls: list[str],
    include_images: bool,
    *,
    created: list[dict[str, Any]] | None = None,
    url_map: dict[str, dict[str, Any]] | None = None,
    category_groups: list[tuple[str, list[dict[str, Any]]]] | None = None,
) -> None:
    """Aplica a resposta da IA na página (mesmo caminho do create-page-base), sem trocar o título:
    o nome da página foi decidido antes e é definitivo. Com category_groups (home com as categorias
    mantidas), a vitrine vira uma seção por categoria (place_category_sections)."""
    from app.api.v1.endpoints.pages import derive_cover_image_from_config, enforce_page_limits, normalize_config, resolve_agency_plan
    from app.services.ai_assistant import build_page_base_config_from_reply
    from app.services.hub_black import distribute_client_photos
    from app.services.page_tags import apply_ai_tag_sections
    from app.services.stock_images import clear_photo_queries, fill_section_photos

    db.refresh(page)
    base = normalize_config(page.config_json)
    base = deepcopy(base) if isinstance(base, dict) else {}
    base.pop(PAGE_MARKER, None)
    config, _suggested_title = build_page_base_config_from_reply(reply, base)
    sections = config["sections"]
    apply_ai_tag_sections(db, page.agency, sections, host_page_id=page.id)
    distribute_client_photos(sections, photo_urls)
    if include_images:
        try:
            fill_section_photos(db, sections, page.agency_id, exclude_page_id=page.id)
        except Exception:  # pragma: no cover - sem foto, a seção fica com a imagem provisória
            logger.exception("site_import_stock_photos_failed page=%s", page.id)
            db.rollback()
            clear_photo_queries(sections)
    else:
        clear_photo_queries(sections)
    if created is not None:
        targets, _base = _page_targets(db, page.agency_id)
        by_title = {_plain_key(item["title"]): item for item in created}
        by_title.update({_plain_key(item["card_title"]): item for item in created if item.get("card_title")})
        link_cards_to_pages(sections, targets, by_title)
        relink_original_urls(sections, url_map or {})
        by_category = deepcopy(sections) if category_groups else None
        if by_category is not None:
            place_category_sections(by_category, category_groups)
        if by_category is not None and _fits_section_limit(db, page.agency_id, by_category):
            sections[:] = by_category
        else:
            # Sem categorias (ou o plano não comporta uma seção por categoria): vitrine única.
            ensure_created_pages_linked(sections, created)
    _strip_ai_keys(sections)
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = enforce_page_limits(db, page, publish=False, config=config, plan=plan)
    page.cover_image_url = derive_cover_image_from_config(page.config_json)
    db.add(page)
    db.commit()


def _create_trip_page(db: Session, job: SiteImportJob, title: str) -> Page:
    from app.api.v1.endpoints.pages import _ensure_unique_slug

    page = Page(
        agency_id=job.agency_id,
        title=title,
        slug=_ensure_unique_slug(db, job.agency_id, title),
        status="draft",
        # Sem seções ainda: o editor mostra o aviso de importação em andamento (PAGE_MARKER).
        config_json={"sections": [], PAGE_MARKER: {"status": "importing", "job_id": job.id}},
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def _tag_page_with_category(db: Session, page: Page, category: str) -> None:
    """Liga à página a tag com o nome da categoria do site original (exatamente como estava lá),
    criando a tag na agência se ainda não existir. Falha aqui não derruba a viagem: a página
    segue sem a tag (e entra na seção da categoria na home do mesmo jeito)."""
    from app.services.page_tags import get_or_create_tag

    try:
        tag = get_or_create_tag(db, page.agency_id, category)
        if tag is None:
            return
        db.refresh(page)
        if all(existing.id != tag.id for existing in page.tags):
            page.tags.append(tag)
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("site_import_category_tag_failed page=%s category=%s", page.id, category)


def _mark_page_error(db: Session, page_id: int, message: str) -> None:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page or not isinstance(page.config_json, dict) or PAGE_MARKER not in page.config_json:
        return
    config = deepcopy(page.config_json)
    config[PAGE_MARKER] = {"status": "error", "error": message[:500]}
    page.config_json = config
    db.add(page)
    db.commit()


async def _process_item(db: Session, job: SiteImportJob, index: int) -> None:
    item = job.items[index]
    url = item["url"]
    _set_item(db, job, index, stage=STAGE_SCRAPING)
    imported = await scrape_page(url)
    attachments = await download_page_images(imported)

    base_title = strip_site_name(imported.title, job.source_title) or item.get("card_title") or "Viagem"
    existing = [title for (title,) in db.query(Page.title).filter(Page.agency_id == job.agency_id).all()]
    nearby_text = "\n".join(part for part in (item.get("card_text"), imported.text) if part)
    title = pick_unique_title(base_title, nearby_text, existing)
    page = _create_trip_page(db, job, title)
    if job.preserve_categories and item.get("category"):
        _tag_page_with_category(db, page, item["category"])
    _set_item(db, job, index, stage=STAGE_GENERATING, title=page.title, page_id=page.id, slug=page.slug)

    try:
        context, photo_urls = await _build_context(db, page, url, imported, attachments, job.include_images)
        request = (
            "Monte agora a estrutura completa da página desta viagem, pronta para aplicar, com as informações do "
            "CONTEÚDO EXTRAÍDO DO LINK ENVIADO. Não faça perguntas: deixe de fora o que não foi informado."
        )
        reply = await _ask_ai(db, page, request, attachments, context)
        _apply_reply(db, page, reply, photo_urls, job.include_images)
    except Exception as exc:
        db.rollback()
        _mark_page_error(db, page.id, _error_text(exc))
        raise


async def _generate_home(db: Session, job: SiteImportJob) -> None:
    home = db.query(Page).filter(Page.id == job.page_id).first() if job.page_id else None
    if home is None:
        raise HTTPException(status_code=404, detail="A página onde a importação começou foi apagada.")
    targets, _base = _page_targets(db, job.agency_id)
    created: list[dict[str, Any]] = []
    url_map: dict[str, dict[str, Any]] = {}
    for item in job.items or []:
        if item.get("stage") != STAGE_DONE or not item.get("slug") or item["slug"] not in targets:
            continue
        target = targets[item["slug"]]
        entry = {
            **target,
            "title": item.get("title") or target["title"],
            "card_title": item.get("card_title"),
            "price": item.get("price"),
            "category": item.get("category"),
            "position": item.get("position"),
        }
        created.append(entry)
        url_map[normalize_url(item["url"])] = target
    # Categorias mantidas: uma seção por categoria no lugar da vitrine única (montada em código,
    # sem depender da IA escrever as seções certas). Sem nenhuma página com categoria, nada muda.
    category_groups = group_created_by_category(created) if job.preserve_categories else []

    imported = await scrape_page(job.source_url)
    attachments = await download_page_images(imported)
    context, photo_urls = await _build_context(db, home, job.source_url, imported, attachments, job.include_images)
    if created:
        lines = [
            "PÁGINAS CRIADAS NESTA IMPORTAÇÃO (cada viagem do site original já virou uma página da agência). "
            'Monte uma VITRINE DE VIAGENS com um card por página abaixo, cada card com "Página: identificador" '
            "(o identificador é o que vem antes dos dois-pontos). Não use os links originais do site:"
        ]
        lines.extend(
            f"- {item['slug']}: {item['title']}" + (f" (preço no site: {item['price']})" if item.get("price") else "")
            for item in created
        )
        context = f"{context}\n" + "\n".join(lines)
    request = (
        "Monte agora a estrutura completa da página principal deste site (a home da agência), pronta para aplicar, "
        "com as informações do CONTEÚDO EXTRAÍDO DO LINK ENVIADO. Não faça perguntas: deixe de fora o que não foi informado."
    )
    reply = await _ask_ai(db, home, request, attachments, context)
    _apply_reply(
        db, home, reply, photo_urls, job.include_images, created=created, url_map=url_map, category_groups=category_groups or None
    )


async def _run(job_id: int) -> None:
    from app.db import session as db_session

    with db_session.SessionLocal() as db:
        job = db.query(SiteImportJob).filter(SiteImportJob.id == job_id).first()
        if not job or job.status != STATUS_RUNNING:
            return
        for index in range(len(job.items or [])):
            try:
                await _process_item(db, job, index)
            except Exception as exc:
                db.rollback()
                logger.exception("site_import_item_failed job=%s url=%s", job.id, job.items[index].get("url"))
                db.refresh(job)
                _set_item(db, job, index, stage=STAGE_ERROR, error=_error_text(exc))
            else:
                _set_item(db, job, index, stage=STAGE_DONE, error=None)

        job.stage = "home"
        job.home_stage = STAGE_GENERATING
        _save(db, job)
        try:
            await _generate_home(db, job)
        except Exception as exc:
            db.rollback()
            logger.exception("site_import_home_failed job=%s", job.id)
            db.refresh(job)
            job.home_stage = STAGE_ERROR
            job.status = STATUS_FAILED
            job.error = f"As páginas das viagens foram criadas, mas a página principal falhou: {_error_text(exc)}"
        else:
            job.home_stage = STAGE_DONE
            job.status = STATUS_COMPLETED
        job.stage = None
        job.finished_at = _now()
        _save(db, job)


def _fail(job_id: int, message: str) -> None:
    from app.db import session as db_session

    with db_session.SessionLocal() as db:
        job = db.query(SiteImportJob).filter(SiteImportJob.id == job_id).first()
        if not job or job.status != STATUS_RUNNING:
            return
        job.status = STATUS_FAILED
        job.error = message[:500]
        job.finished_at = _now()
        _save(db, job)


def run_job(job_id: int) -> None:
    """Roda numa thread própria, com sessão própria do banco e event loop próprio."""
    try:
        asyncio.run(_run(job_id))
    except Exception as exc:  # pragma: no cover - guarda geral
        logger.exception("site_import_job_failed job=%s", job_id)
        _fail(job_id, f"Falha na importação do site: {exc}")


def start_job_thread(job_id: int) -> None:
    threading.Thread(target=run_job, args=(job_id,), daemon=True).start()
