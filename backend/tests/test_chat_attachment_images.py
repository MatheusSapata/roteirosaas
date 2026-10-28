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


def test_sem_consentimento_so_ficam_as_fotos_enviadas():
    from app.services.ai_assistant import AI_IMAGE_PLACEHOLDER
    from app.services.hub_black import build_request_text, restrict_images_to_allowed

    enviada = "/uploads/1/cliente.jpg"
    sections = [
        {"type": "hero", "backgroundImage": enviada, "mobileBackgroundImage": "https://images.unsplash.com/x.jpg"},
        {"type": "story", "images": [enviada, "https://exemplo.com/outra.jpg"]},
        {"type": "itinerary", "days": [{"image": "https://pixabay.com/y.jpg"}, {"image": enviada}]},
        {"type": "photo", "image": AI_IMAGE_PLACEHOLDER},
    ]
    assert restrict_images_to_allowed(sections, {enviada}) == 3
    assert sections[0] == {"type": "hero", "backgroundImage": enviada, "mobileBackgroundImage": AI_IMAGE_PLACEHOLDER}
    assert sections[1]["images"] == [enviada]
    assert [day["image"] for day in sections[2]["days"]] == [AI_IMAGE_PLACEHOLDER, enviada]
    assert sections[3]["image"] == AI_IMAGE_PLACEHOLDER

    lista_toda_estranha = [{"type": "story", "images": ["https://exemplo.com/a.jpg"]}]
    restrict_images_to_allowed(lista_toda_estranha, set())
    assert lista_toda_estranha[0]["images"] == [AI_IMAGE_PLACEHOLDER]

    assert "EXPRESSAMENTE PROIBIDO" in build_request_text("t", "d", "g", False)
    assert "AUTORIZOU" in build_request_text("t", "d", "g", True)


def test_usa_o_maximo_das_fotos_do_cliente():
    from app.services.ai_assistant import AI_IMAGE_PLACEHOLDER as VAZIA
    from app.services.hub_black import build_request_text, distribute_client_photos

    fotos = [f"/uploads/1/f{n}.jpg" for n in range(1, 9)]
    sections = [
        {"type": "hero", "backgroundImage": fotos[0], "mobileBackgroundImage": fotos[0]},  # a IA já usou f1
        {"type": "photo", "image": VAZIA, "aiImageQuery": "praia"},
        {"type": "itinerary", "days": [{"image": VAZIA}, {"image": VAZIA}]},
        {"type": "story", "images": [VAZIA]},
        {"type": "faq"},
    ]
    colocadas = distribute_client_photos(sections, fotos)
    assert colocadas == 7
    assert sections[0]["backgroundImage"] == fotos[0]
    assert sections[1]["image"] == fotos[1] and "aiImageQuery" not in sections[1]
    assert [day["image"] for day in sections[2]["days"]] == [fotos[2], fotos[3]]
    assert sections[3]["images"] == fotos[4:8]  # 3 na vaga livre + 1 que sobrou
    usadas = [sections[0]["backgroundImage"], sections[1]["image"], *(d["image"] for d in sections[2]["days"]), *sections[3]["images"]]
    assert sorted(usadas) == sorted(fotos)  # todas entraram, nenhuma repetida

    # não repete foto já usada e não inventa foto quando o cliente não mandou nenhuma
    de_novo = [{"type": "photo", "image": VAZIA}]
    assert distribute_client_photos(de_novo, []) == 0 and de_novo[0]["image"] == VAZIA
    assert "MÁXIMO" in build_request_text("t", "d", "g", False)
