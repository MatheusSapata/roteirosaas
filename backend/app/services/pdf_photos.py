"""Fotos de dentro de um PDF enviado ao assistente de IA (folheto, roteiro de operadora...).

As fotos vão só para a biblioteca de mídia da agência que enviou o PDF. Nunca entram no banco
comum de fotos (stock_images), que é usado na busca de todos os clientes.

Ficam de fora: ícones, logos e selos (pequenos), a mesma foto repetida em várias páginas e a
página "achatada" (escaneada ou exportada como uma imagem só), em que a "foto" seria a página
inteira com o texto por cima.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from PIL import Image
from pypdf import PdfReader
from pypdf.generic import DictionaryObject, StreamObject

logger = logging.getLogger(__name__)

MAX_PDF_PHOTOS = 12  # por mensagem (somando os PDFs)
MAX_PDF_PAGES = 60
MAX_PDF_BYTES = 30 * 1024 * 1024
MAX_IMAGES_CHECKED = 120  # imagens olhadas por PDF (folheto com centenas de ícones)
MIN_SIDE = 400  # menor lado, em pixels
MIN_AREA = 400 * 600
MAX_PIXELS = 40_000_000  # imagem maior que isso nem é aberta (memória do servidor)
FLAT_PAGE_TEXT = 30  # página com menos letras que isso e uma imagem do tamanho dela = achatada

PDF_TYPES = frozenset({"application/pdf", "application/x-pdf"})
# media_assets.source das fotos tiradas de PDF.
PDF_SOURCE = "pdf"


@dataclass
class PdfPhoto:
    page: int
    data: bytes
    content_type: str
    width: int
    height: int
    # Texto da página do PDF de onde a foto saiu (vira palavras-chave e ajuda a IA a encaixar).
    page_text: str = ""

    @property
    def orientation(self) -> str:
        if self.width > self.height * 1.15:
            return "horizontal"
        if self.height > self.width * 1.15:
            return "vertical"
        return "quadrada"


def is_pdf(content_type: str | None, filename: str | None) -> bool:
    return (content_type or "").lower() in PDF_TYPES or (filename or "").lower().endswith(".pdf")


def _xobject(page, key) -> StreamObject | None:
    """Objeto da imagem a partir do nome que a pypdf dá ("/Im0", ou ["/Fm0", "/Im0"] dentro de um
    formulário). Imagem embutida no texto da página (inline) não tem objeto: fica de fora."""
    obj = page
    for name in key if isinstance(key, list) else [key]:
        resources = obj.get("/Resources") if isinstance(obj, DictionaryObject) else None
        resources = resources.get_object() if resources is not None else None
        if not isinstance(resources, DictionaryObject):
            return None
        xobjects = resources.get("/XObject")
        xobjects = xobjects.get_object() if xobjects is not None else None
        if not isinstance(xobjects, DictionaryObject) or name not in xobjects:
            return None
        obj = xobjects[name].get_object()
    return obj if isinstance(obj, StreamObject) else None


def _size(xobject: StreamObject) -> tuple[int, int]:
    try:
        return int(xobject.get("/Width", 0)), int(xobject.get("/Height", 0))
    except (TypeError, ValueError):
        return 0, 0


def _page_text(page, limit: int = 600) -> str:
    try:
        text = page.extract_text() or ""
    except Exception:  # noqa: BLE001 - página sem texto legível
        return ""
    return " ".join(text.split())[:limit]


def _flat_page(page, width: int, height: int, text: str) -> bool:
    """Página escaneada ou exportada como imagem: a imagem tem o formato da página e quase não há
    texto de verdade (o texto está desenhado dentro da imagem)."""
    try:
        box = page.mediabox
        page_ratio = float(box.width) / float(box.height)
    except Exception:  # noqa: BLE001 - página sem tamanho: não dá para comparar
        return False
    if not page_ratio or abs(width / height - page_ratio) / page_ratio > 0.04:
        return False
    return len(text.replace(" ", "")) < FLAT_PAGE_TEXT


def _encode(image: Image.Image) -> tuple[bytes, str]:
    """PNG quando há transparência; o resto em JPEG (CMYK de gráfica vira RGB)."""
    has_alpha = image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info)
    buffer = io.BytesIO()
    if has_alpha:
        image.convert("RGBA").save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "image/png"
    image.convert("RGB").save(buffer, format="JPEG", quality=92)
    return buffer.getvalue(), "image/jpeg"


def extract_pdf_photos(data: bytes, *, limit: int = MAX_PDF_PHOTOS) -> list[PdfPhoto]:
    """As fotos do PDF, na ordem das páginas. Passando do limite, ficam as maiores."""
    if not data or len(data) > MAX_PDF_BYTES or limit <= 0:
        return []
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            reader.decrypt("")  # PDF só com senha de edição abre; com senha de leitura, não
        pages = list(reader.pages[:MAX_PDF_PAGES])
    except Exception as exc:  # noqa: BLE001 - PDF quebrado ou protegido: segue sem as fotos
        logger.info("pdf_photos_unreadable: %s", exc)
        return []

    found: list[tuple[int, int, PdfPhoto]] = []  # (área, ordem, foto)
    seen: set[object] = set()
    checked = 0
    for number, page in enumerate(pages, start=1):
        try:
            keys = list(page.images.keys())
        except Exception as exc:  # noqa: BLE001
            logger.info("pdf_photos_page_failed page=%s: %s", number, exc)
            continue
        text: str | None = None  # lido só se a página tiver foto
        for key in keys:
            if checked >= MAX_IMAGES_CHECKED:
                break
            xobject = _xobject(page, key)
            if xobject is None:
                continue
            width, height = _size(xobject)
            if min(width, height) < MIN_SIDE or width * height < MIN_AREA or width * height > MAX_PIXELS:
                continue
            # A mesma foto em várias páginas (fundo, capa repetida) é o mesmo objeto no PDF.
            reference = xobject.indirect_reference
            identity = (reference.idnum, reference.generation) if reference is not None else id(xobject)
            if identity in seen:
                continue
            seen.add(identity)
            checked += 1
            if text is None:
                text = _page_text(page)
            if len(keys) == 1 and _flat_page(page, width, height, text):
                continue
            try:
                image = page.images[key].image
                if image is None:
                    continue
                encoded, content_type = _encode(image)
            except Exception as exc:  # noqa: BLE001 - formato que a pypdf não abre: pula a imagem
                logger.info("pdf_photos_image_failed page=%s key=%s: %s", number, key, exc)
                continue
            photo = PdfPhoto(
                page=number, data=encoded, content_type=content_type, width=image.width, height=image.height, page_text=text
            )
            found.append((image.width * image.height, len(found), photo))

    biggest = sorted(found, key=lambda item: item[0], reverse=True)[:limit]
    return [photo for _, _, photo in sorted(biggest, key=lambda item: item[1])]
