"""Anexos de imagem fora da lista aceita pela OpenAI (AVIF etc.) são convertidos; o que não
converte fica de fora em vez de ir como arquivo e derrubar a geração."""
from __future__ import annotations

import io

from PIL import Image

from app.services.ai_assistant import ChatAttachment, ChatMessage, _build_ai_conversation_input, normalize_chat_attachment


def _image(fmt: str, mode: str = "RGB") -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, (40, 30), (10, 120, 200) if mode == "RGB" else (10, 120, 200, 128)).save(buffer, fmt)
    return buffer.getvalue()


def test_avif_vira_jpeg():
    result = normalize_chat_attachment(ChatAttachment("foto.avif", "image/avif", _image("AVIF")))
    assert result is not None
    assert result.content_type == "image/jpeg"
    assert result.filename == "foto.jpg"
    assert Image.open(io.BytesIO(result.data)).format == "JPEG"


def test_imagem_com_transparencia_vira_png():
    result = normalize_chat_attachment(ChatAttachment("logo.tiff", "image/tiff", _image("TIFF", "RGBA")))
    assert result is not None and result.content_type == "image/png"


def test_formatos_aceitos_e_pdf_ficam_como_estao():
    jpeg = ChatAttachment("a.jpg", "image/jpeg", _image("JPEG"))
    pdf = ChatAttachment("a.pdf", "application/pdf", b"%PDF-1.4")
    assert normalize_chat_attachment(jpeg) is jpeg
    assert normalize_chat_attachment(pdf) is pdf


def test_imagem_que_nao_converte_e_ignorada():
    assert normalize_chat_attachment(ChatAttachment("x.heic", "image/heic", b"nao e imagem")) is None


def test_conversa_nunca_manda_imagem_como_arquivo():
    items = _build_ai_conversation_input(
        [ChatMessage(role="user", content="Monte o roteiro")],
        [
            ChatAttachment("foto.avif", "image/avif", _image("AVIF")),
            ChatAttachment("quebrada.heic", "image/heic", b"lixo"),
        ],
    )
    content = items[-1]["content"]
    assert [part["type"] for part in content] == ["input_text", "input_image"]
    assert content[1]["image_url"].startswith("data:image/jpeg;base64,")
