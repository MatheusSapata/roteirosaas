"""Versões leves das imagens enviadas para as páginas.

Foto de celular ou arte exportada chega com vários MB e, no visitante, aparece em faixas
enquanto baixa. No envio, cada imagem vira WebP em três larguras (640, 1280 e 2400 px),
com a orientação da câmera aplicada e sem metadados (GPS etc.). A página pública escolhe
a largura certa para a tela (srcset) a partir do nome `<id>_2400.webp`.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

VARIANT_WIDTHS = (640, 1280, 2400)
MAIN_WIDTH = VARIANT_WIDTHS[-1]
PHOTO_QUALITY = 80
ALPHA_QUALITY = 88
# GIF (pode ser animado), SVG e ícones ficam como foram enviados.
OPTIMIZABLE_FORMATS = {"JPEG", "MPO", "PNG", "WEBP", "BMP", "TIFF"}
MAX_SOURCE_PIXELS = 80_000_000


def variant_name(stem: str, width: int) -> str:
    return f"{stem}_{width}.webp"


def _has_alpha(image: Image.Image) -> bool:
    if image.mode in {"RGBA", "LA", "PA"} or (image.mode == "P" and "transparency" in image.info):
        alpha = image.convert("RGBA").getchannel("A")
        return alpha.getextrema()[0] < 255
    return False


def optimize_image(data: bytes) -> Optional[dict[int, bytes]]:
    """Devolve {largura: bytes WebP} ou None quando a imagem deve ficar como foi enviada."""
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in OPTIMIZABLE_FORMATS or getattr(source, "is_animated", False):
                return None
            if source.width * source.height > MAX_SOURCE_PIXELS:
                return None
            # Perfil de cor só vale para RGB; CMYK é convertido sem ele.
            icc_profile = source.info.get("icc_profile") if source.mode != "CMYK" else None
            image = ImageOps.exif_transpose(source)
            alpha = _has_alpha(image)
            image = image.convert("RGBA" if alpha else "RGB")

            variants: dict[int, bytes] = {}
            for width in VARIANT_WIDTHS:
                if image.width > width:
                    height = max(1, round(image.height * width / image.width))
                    resized = image.resize((width, height), Image.Resampling.LANCZOS)
                else:
                    resized = image
                buffer = io.BytesIO()
                options = {"quality": ALPHA_QUALITY if alpha else PHOTO_QUALITY, "method": 5}
                if icc_profile:
                    options["icc_profile"] = icc_profile
                resized.save(buffer, format="WEBP", **options)
                variants[width] = buffer.getvalue()
            return variants
    except Exception as exc:  # noqa: BLE001 - imagem estranha não pode impedir o envio
        logger.warning("Imagem enviada sem otimizar: %s", exc)
        return None
