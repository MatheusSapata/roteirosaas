"""A IA escolhe a foto de cada seção olhando as candidatas.

O banco de fotos devolve várias opções por busca, e a descrição delas (tags do Pixabay, texto do
Pexels) quase nunca diz se a foto é mesmo do lugar. Aqui a IA recebe a miniatura e a descrição de
cada candidata e escolhe, para cada vaga, as que mostram o que a seção pede. Sem chave da IA,
sem tempo ou com erro, quem decide é a ordem do ranking (rank_images), como antes.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.stock_image import StockImage

logger = logging.getLogger(__name__)

THUMB_TIMEOUT = 4.0
# Miniatura maior que isso não vai para a IA (vai só a descrição).
THUMB_MAX_BYTES = 450_000
# Teto de miniaturas por pedido (no modo "low" cada uma custa ~85 tokens).
MAX_THUMBS = 48
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

INSTRUCTIONS = """Você escolhe fotos para as seções de uma página de venda de viagem.
Para cada VAGA vêm fotos candidatas: código, descrição do banco de fotos e a miniatura.
Escolha, em ordem de preferência, as fotos que melhor mostram o que a vaga pede:
1. o lugar exato citado (cidade, praia, parque, atração) e o tema da seção;
2. se nenhuma mostrar o lugar, a que combina com o tema ou a sensação pedida.
Descarte: foto de outro lugar ou país quando o lugar foi citado, foto com texto, logotipo, marca
d'água ou moldura, colagem, ilustração ou desenho, print de tela, foto escura, borrada ou em pé
com o assunto cortado, close de pessoa posando. A foto vai num espaço largo: prefira fotos deitadas.
Não repita a mesma foto em duas vagas. Devolva lista vazia para a vaga só se todas forem inadequadas.
Responda só com JSON, sem texto antes ou depois, no formato {"V1": ["V1-3", "V1-1"], "V2": ["V2-2"]}."""


@dataclass
class PhotoSlot:
    """Uma vaga de foto: a seção (ou card) e quantas fotos ela leva."""

    key: str
    context: str
    count: int = 1
    candidates: list[StockImage] = field(default_factory=list)


def describe(image: StockImage) -> str:
    parts = [part for part in (image.alt, image.tags, image.location) if part]
    text = " · ".join(dict.fromkeys(parts))[:220] or "sem descrição"
    shape = ""
    if image.width and image.height:
        shape = " (em pé)" if image.height > image.width else ""
    source = "escolhida pela equipe" if image.provider == "manual" else image.provider.title()
    return f"{text}{shape} [{source}]"


def thumb_url(image: StockImage) -> str | None:
    """Endereço pequeno da foto: a miniatura do banco, a cópia já guardada ou a original."""
    for url in (image.preview_url, image.stored_url, image.download_url):
        if url and url.startswith(("http://", "https://")) and "/download" not in url:
            # Link do Unsplash guardado em 2000 px: a versão de 400 px basta para olhar.
            return url.replace("&w=2000", "&w=400") if "images.unsplash.com" in url else url
    return None


def _fetch(client: httpx.Client, url: str) -> str | None:
    try:
        response = client.get(url, timeout=THUMB_TIMEOUT)
        response.raise_for_status()
    except Exception:  # noqa: BLE001 - miniatura que não abre: a IA vê só a descrição
        return None
    kind = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
    if kind not in IMAGE_TYPES or len(response.content) > THUMB_MAX_BYTES:
        return None
    return f"data:{kind};base64,{base64.b64encode(response.content).decode()}"


def _thumbnails(client: httpx.Client, images: list[StockImage]) -> dict[int, str]:
    targets = [(image.id, thumb_url(image)) for image in images[:MAX_THUMBS]]
    targets = [(image_id, url) for image_id, url in targets if url]
    if not targets:
        return {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda item: (item[0], _fetch(client, item[1])), targets))
    return {image_id: data for image_id, data in results if data}


def _parse_choice(text: str, slots: list[PhotoSlot], codes: dict[str, StockImage]) -> dict[str, list[StockImage]] | None:
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    chosen: dict[str, list[StockImage]] = {}
    for slot in slots:
        picks = payload.get(slot.key)
        if not isinstance(picks, list):
            continue
        images = [codes[str(code).strip().upper()] for code in picks if str(code).strip().upper() in codes]
        # Só vale código da própria vaga.
        chosen[slot.key] = [image for image in images if image in slot.candidates]
    return chosen


def choose_photos(
    db: Session, client: httpx.Client, slots: list[PhotoSlot], *, timeout: float
) -> dict[str, list[StockImage]] | None:
    """Escolha da IA por vaga (fotos em ordem de preferência), ou None se não deu para perguntar."""
    settings = get_settings()
    slots = [slot for slot in slots if slot.candidates]
    if not settings.gpt_key or not slots or timeout < 3:
        return None
    try:
        from openai import OpenAI

        from app.services.ai_assistant import _model_kwargs
        from app.services.construtor_prompt import get_active_gpt_model
    except ImportError:  # pragma: no cover - dependência ausente
        return None
    everything = list(dict.fromkeys(image for slot in slots for image in slot.candidates))
    thumbs = _thumbnails(client, everything)
    content: list[dict[str, Any]] = []
    codes: dict[str, StockImage] = {}
    for slot in slots:
        how_many = "1 foto" if slot.count == 1 else f"até {slot.count} fotos diferentes"
        content.append({"type": "input_text", "text": f"VAGA {slot.key}: {slot.context}. Escolha {how_many}."})
        for number, image in enumerate(slot.candidates, 1):
            code = f"{slot.key}-{number}"
            codes[code] = image
            content.append({"type": "input_text", "text": f"{code}: {describe(image)}"})
            if image.id in thumbs:
                content.append({"type": "input_image", "image_url": thumbs[image.id], "detail": "low"})
    model = get_active_gpt_model(db, create_if_missing=False)
    try:
        response = OpenAI(api_key=settings.gpt_key, timeout=timeout, max_retries=0).responses.create(
            model=model,
            instructions=INSTRUCTIONS,
            input=[{"role": "user", "content": content}],
            **_model_kwargs(model),
        )
    except Exception as exc:  # noqa: BLE001 - sem a IA, vale o ranking
        logger.warning("photo_choice_failed error=%s", exc)
        return None
    chosen = _parse_choice(getattr(response, "output_text", "") or "", slots, codes)
    if chosen is None:
        logger.warning("photo_choice_unreadable reply=%r", (getattr(response, "output_text", "") or "")[:300])
    else:
        logger.info("photo_choice slots=%s thumbs=%s", {key: len(value) for key, value in chosen.items()}, len(thumbs))
    return chosen
