"""Vídeo da capa da página de vendas: o Admin Master envia o arquivo em partes (um vídeo passa do
limite de uma requisição) direto para o armazenamento de mídia, e a página toca no player próprio.

O arquivo recebe um nome "<uuid>.mp4": o ciclo de vida da mídia reconhece o identificador na
configuração do checkout e não apaga o vídeo em uso."""
from __future__ import annotations

import math
import re
from uuid import uuid4

from fastapi import HTTPException

from app.services.media_storage import media_storage

SALES_VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm"}
SALES_VIDEO_MAX_BYTES = 300 * 1024 * 1024
SALES_VIDEO_CHUNK_BYTES = 4 * 1024 * 1024
SALES_VIDEO_MAX_CHUNKS = math.ceil(SALES_VIDEO_MAX_BYTES / SALES_VIDEO_CHUNK_BYTES)
_NAME_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(mp4|webm)$")


def start_upload(content_type: str, size: int) -> dict[str, int | str]:
    extension = SALES_VIDEO_TYPES.get((content_type or "").split(";", 1)[0].strip().lower())
    if not extension:
        raise HTTPException(status_code=415, detail="Envie o vídeo em MP4 ou WebM.")
    if size > SALES_VIDEO_MAX_BYTES:
        raise HTTPException(status_code=413, detail="O vídeo passa de 300 MB. Exporte em 1080p ou 720p e envie de novo.")
    return {"name": f"{uuid4()}{extension}", "chunk_size": SALES_VIDEO_CHUNK_BYTES}


def _check_name(name: str) -> str:
    if not _NAME_RE.fullmatch(name or ""):
        raise HTTPException(status_code=400, detail="Envio de vídeo inválido. Comece de novo.")
    return name


def save_chunk(name: str, index: int, data: bytes) -> None:
    _check_name(name)
    if index < 0 or index >= SALES_VIDEO_MAX_CHUNKS:
        raise HTTPException(status_code=400, detail="Parte do vídeo fora do limite.")
    if not data:
        raise HTTPException(status_code=400, detail="Parte do vídeo vazia.")
    if len(data) > SALES_VIDEO_CHUNK_BYTES:
        raise HTTPException(status_code=413, detail="Parte do vídeo maior que o permitido.")
    media_storage.stage_chunk(name, index, data)


def finish_upload(name: str, chunks: int) -> str:
    _check_name(name)
    if chunks < 1 or chunks > SALES_VIDEO_MAX_CHUNKS:
        raise HTTPException(status_code=400, detail="Quantidade de partes do vídeo inválida.")
    content_type = "video/webm" if name.endswith(".webm") else "video/mp4"
    try:
        return media_storage.commit_chunks(name, chunks, content_type)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="O envio do vídeo ficou incompleto. Envie de novo.") from exc
