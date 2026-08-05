from __future__ import annotations

import io
from functools import lru_cache
from threading import Lock

import numpy as np
from PIL import Image, ImageStat, UnidentifiedImageError
from scipy.ndimage import binary_propagation


MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class InvalidBackgroundRemovalImage(ValueError):
    """Raised when the uploaded payload is not a supported image."""


class BackgroundRemovalUnavailable(RuntimeError):
    """Raised when the segmentation engine is unavailable."""


_session_lock = Lock()


def _connected_solid_background_alpha(image: Image.Image) -> Image.Image | None:
    """Create an alpha mask when a logo has a uniform background at its edges."""
    rgba = image.convert("RGBA")
    rgb = rgba.convert("RGB")
    width, height = rgb.size
    if width < 2 or height < 2:
        return None

    patch_size = max(1, min(width, height, 24) // 4)
    boxes = (
        (0, 0, patch_size, patch_size),
        (width - patch_size, 0, width, patch_size),
        (0, height - patch_size, patch_size, height),
        (width - patch_size, height - patch_size, width, height),
    )
    colors = [tuple(round(value) for value in ImageStat.Stat(rgb.crop(box)).median) for box in boxes]
    background = tuple(round(sum(color[channel] for color in colors) / 4) for channel in range(3))
    if any(max(abs(color[channel] - background[channel]) for channel in range(3)) > 28 for color in colors):
        return None

    border = list(rgb.crop((0, 0, width, 1)).getdata())
    border += list(rgb.crop((0, height - 1, width, height)).getdata())
    border += list(rgb.crop((0, 1, 1, height - 1)).getdata())
    border += list(rgb.crop((width - 1, 1, width, height - 1)).getdata())
    matches = sum(
        max(abs(pixel[channel] - background[channel]) for channel in range(3)) <= 28 for pixel in border
    )
    if matches / max(1, len(border)) < 0.6:
        return None

    color_distance = np.max(
        np.abs(np.asarray(rgb, dtype=np.int16) - np.asarray(background, dtype=np.int16)),
        axis=2,
    )
    alpha = np.full((height, width), 255, dtype=np.uint8)
    seeds = np.zeros((height, width), dtype=bool)
    seeds[0, 0] = seeds[0, width - 1] = True
    seeds[height - 1, 0] = seeds[height - 1, width - 1] = True
    for tolerance, alpha_value in ((56, 176), (36, 80), (20, 0)):
        candidates = color_distance <= tolerance
        connected = binary_propagation(seeds & candidates, mask=candidates)
        alpha[connected] = np.minimum(alpha[connected], alpha_value)
    return Image.fromarray(alpha, mode="L")


def _refine_logo_background(source: bytes, segmented: bytes) -> bytes:
    with Image.open(io.BytesIO(source)) as source_image:
        solid_alpha = _connected_solid_background_alpha(source_image)
    if solid_alpha is None:
        return segmented

    with Image.open(io.BytesIO(segmented)) as result_image:
        result = result_image.convert("RGBA")
    if result.size != solid_alpha.size:
        solid_alpha = solid_alpha.resize(result.size, Image.Resampling.LANCZOS)
    current = result.getchannel("A").tobytes()
    refined = solid_alpha.tobytes()
    result.putalpha(Image.frombytes("L", result.size, bytes(map(min, current, refined))))
    output = io.BytesIO()
    result.save(output, format="PNG")
    return output.getvalue()


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
    return _refine_logo_background(content, result)
