"""Versões leves de fotos antigas (enviadas antes de existirem as versões em WebP).

A página pede `/public/img?u=<endereço da foto>&w=<largura>`. Na primeira vez a foto é lida,
reduzida e guardada como `<id>_<largura>.webp` (o mesmo padrão das fotos novas, então segue o
ciclo de vida do arquivo original); depois é só redirecionar. O arquivo original não muda.
"""

import logging
import re
import threading

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from app.services.image_optimizer import VARIANT_WIDTHS, optimize_width, variant_name
from app.services.media_storage import media_storage

logger = logging.getLogger(__name__)
router = APIRouter()

_LEGACY_NAME = re.compile(r"^([0-9a-fA-F-]{36})\.(png|jpe?g)$")
# Converter foto grande gasta processador e memória: no máximo duas ao mesmo tempo.
_slots = threading.BoundedSemaphore(2)
_not_optimizable: set[str] = set()
_REDIRECT_CACHE = {"Cache-Control": "public, max-age=3600"}


def _convert(original_name: str, cached_name: str, width: int) -> bool:
    with _slots:
        if media_storage.exists(cached_name):
            return True
        data = media_storage.read_bytes(original_name)
        optimized = optimize_width(data, width)
        if optimized is None:
            return False
        media_storage.save_as(optimized, cached_name, "image/webp")
        return True


@router.get("/img")
async def legacy_image(u: str = Query(..., max_length=600), w: int = Query(1280)) -> RedirectResponse:
    if w not in VARIANT_WIDTHS:
        raise HTTPException(status_code=400, detail="Largura inválida.")
    name = media_storage.blob_name_from_url(u.strip())
    match = _LEGACY_NAME.match(name or "")
    if not name or not match:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    original_url = media_storage.public_url(name)
    cached_name = variant_name(match.group(1).lower(), w)
    if cached_name in _not_optimizable:
        return RedirectResponse(original_url, status_code=302, headers=_REDIRECT_CACHE)
    try:
        ready = await run_in_threadpool(_convert, name, cached_name, w)
    except Exception:  # noqa: BLE001 - qualquer falha: a página usa a foto original
        logger.exception("Foto antiga sem versão leve: %s (w=%s)", name, w)
        return RedirectResponse(original_url, status_code=302)
    if not ready:
        _not_optimizable.add(cached_name)
        return RedirectResponse(original_url, status_code=302, headers=_REDIRECT_CACHE)
    return RedirectResponse(media_storage.public_url(cached_name), status_code=302, headers=_REDIRECT_CACHE)
