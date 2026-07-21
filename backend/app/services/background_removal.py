from __future__ import annotations

import io
from functools import lru_cache
from threading import Lock

from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class InvalidBackgroundRemovalImage(ValueError):
    """Raised when the uploaded payload is not a supported image."""


class BackgroundRemovalUnavailable(RuntimeError):
    """Raised when the segmentation engine is unavailable."""


_session_lock = Lock()


def validate_background_removal_image(content: bytes) -> None:
    if not content:
        raise InvalidBackgroundRemovalImage("A imagem está vazia.")
    if len(content) > MAX_IMAGE_BYTES:
        raise InvalidBackgroundRemovalImage("A imagem deve ter no máximo 15 MB.")

    try:
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                raise InvalidBackgroundRemovalImage("A resolução da imagem é muito alta.")
            image.verify()
    except InvalidBackgroundRemovalImage:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidBackgroundRemovalImage("Envie uma imagem PNG, JPG ou WEBP válida.") from exc


@lru_cache(maxsize=1)
def _background_removal_session():
    try:
        from rembg import new_session
    except ImportError as exc:  # pragma: no cover - depends on deployment extras
        raise BackgroundRemovalUnavailable("O motor de remoção de fundo não está instalado.") from exc

    # u2netp é um modelo compacto apropriado para a interação dentro do editor.
    with _session_lock:
        try:
            return new_session("u2netp")
        except Exception as exc:  # pragma: no cover - model download/runtime failure
            raise BackgroundRemovalUnavailable("O motor de remoção de fundo não pôde ser iniciado.") from exc


def remove_image_background(content: bytes) -> bytes:
    validate_background_removal_image(content)
    try:
        from rembg import remove
    except ImportError as exc:  # pragma: no cover - depends on deployment extras
        raise BackgroundRemovalUnavailable("O motor de remoção de fundo não está instalado.") from exc

    try:
        result = remove(
            content,
            session=_background_removal_session(),
            force_return_bytes=True,
        )
    except BackgroundRemovalUnavailable:
        raise
    except Exception as exc:
        raise RuntimeError("Não foi possível segmentar a imagem.") from exc

    if not isinstance(result, bytes) or not result:
        raise RuntimeError("O motor não retornou uma imagem válida.")
    return result
