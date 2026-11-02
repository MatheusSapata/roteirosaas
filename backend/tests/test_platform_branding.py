"""Admin master › Marca e SEO e › E-mails do sistema. Dados fictícios."""
from __future__ import annotations

import pytest

from app.api.deps import get_current_superuser
from app.main import app
from app.services import email as email_service
from app.services import platform_branding as branding

INDEX = """<html><head>
    <!--default-meta-->
    <title>Roteiro Online</title>
    <meta name="description" content="x" />
    <!--/default-meta-->
    <link rel="icon" type="image/png" href="/assets/Favicon-abc.png" />
</head><body></body></html>"""


@pytest.fixture
def admin():
    app.dependency_overrides[get_current_superuser] = lambda: object()
    yield
    app.dependency_overrides.pop(get_current_superuser, None)


@pytest.fixture
def sent(monkeypatch):
    out = []
    monkeypatch.setattr(email_service.EmailClient, "_is_configured", lambda self: True)
    monkeypatch.setattr(email_service.EmailClient, "send_email", lambda self, **kw: out.append(kw))
    return out


def test_system_emails_keep_todays_text_by_default(sent):
    email_service.send_password_reset_email(to_email="a@example.com", name="Ana", reset_url="https://x/reset", expires_minutes=60)
    email_service.send_team_invite_email(
        to_email="b@example.com", invitee_name="Bia", inviter_name="Caio", agency_name="Viagens X", invite_url="https://x/inv"
    )
    reset, invite = sent
    assert reset["subject"] == "Redefinir a sua senha do Roteiro Online"
    assert "Olá, Ana. Vamos criar uma nova senha?" in reset["html_body"] and "1 hora" in reset["html_body"]
    assert invite["subject"] == "Convite para acessar a equipe da Viagens X"
    assert "<b>Caio</b>" in invite["html_body"] and "https://x/inv" in invite["text_body"]


def test_saved_texts_are_used_and_never_become_html(client, admin, sent):
    client.put("/api/v1/admin/platform/emails", json={"templates": {"redefinir_senha": {
        "subject": "Nova senha, {{nome}}", "title": "Oi <script>alert(1)</script>",
    }}})
    email_service.send_password_reset_email(to_email="a@example.com", name="<b>Ana</b>", reset_url="https://x/r", expires_minutes=30)
    message = sent[0]
    assert message["subject"] == "Nova senha, <b>Ana</b>"  # assunto é texto puro
    assert "<script>" not in message["html_body"] and "&lt;script&gt;" in message["html_body"]
    # Nome com HTML também é escapado quando entra no texto.
    email_service.send_team_invite_email(
        to_email="b@example.com", invitee_name="<i>Bia</i>", inviter_name="C", agency_name="X", invite_url="https://x/i"
    )
    assert "&lt;i&gt;Bia&lt;/i&gt;" in sent[1]["html_body"] and "<i>Bia</i>" not in sent[1]["html_body"]
    # Campo que não mudou segue o padrão.
    assert "Redefinir minha senha" in message["html_body"]


def test_text_equal_to_default_is_not_stored(client, admin):
    default = branding.EMAIL_BY_KEY["convite_equipe"].defaults["subject"]
    data = client.put("/api/v1/admin/platform/emails", json={"templates": {"convite_equipe": {"subject": default}}}).json()
    item = next(i for i in data["items"] if i["key"] == "convite_equipe")
    assert item["custom_fields"] == []


def test_preview_does_not_send(client, admin, sent):
    data = client.post("/api/v1/admin/platform/emails/preview", json={"key": "boas_vindas_checkout", "texts": {"title": "Olá, {{nome}}"}}).json()
    assert "Olá, Maria Souza" in data["html"] and data["subject"].startswith("Pagamento confirmado")
    assert sent == []


def test_branding_goes_to_platform_html_and_email_logo(client, admin):
    assert branding.apply_head_meta(INDEX) == INDEX  # nada configurado: igual ao build
    client.put("/api/v1/admin/platform/branding", json={
        "site_title": "Roteiro & Cia", "site_description": "Descrição nova", "theme_color": "#0A6346",
        "favicon_url": "/uploads/fav.png", "share_image_url": "/uploads/share.jpg", "email_logo_url": "https://cdn.example.com/logo.png",
    })
    html = branding.apply_head_meta(INDEX)
    assert "<title>Roteiro &amp; Cia</title>" in html and 'content="Descrição nova"' in html
    assert 'href="/uploads/fav.png"' in html and "Favicon-abc" not in html
    assert 'og:image" content="http' in html and "/uploads/share.jpg" in html
    assert email_service._logo_url() == "https://cdn.example.com/logo.png"
    public = client.get("/api/v1/public/platform-branding").json()
    assert public["site_title"] == "Roteiro & Cia" and public["favicon_url"] == "/uploads/fav.png"


def test_branding_validation(client, admin):
    assert client.put("/api/v1/admin/platform/branding", json={"theme_color": "verde"}).status_code == 422
    assert client.put("/api/v1/admin/platform/branding", json={"logo_url": "javascript:alert(1)"}).status_code == 422
    svg = client.post("/api/v1/admin/platform/branding/upload?field=logo_url",
                      files={"file": ("x.svg", b"<svg/>", "image/svg+xml")})
    assert svg.status_code == 422


def test_upload_saves_and_sets_the_field(client, admin, monkeypatch, tmp_path):
    from app.services import media_storage

    monkeypatch.setattr(media_storage.MediaStorage, "save", lambda self, data, name, ctype=None: "/uploads/novo.png")
    data = client.post("/api/v1/admin/platform/branding/upload?field=favicon_url",
                       files={"file": ("f.png", b"\x89PNG....", "image/png")}).json()
    assert data["favicon_url"] == "/uploads/novo.png"


def test_admin_routes_need_superuser(client):
    assert client.get("/api/v1/admin/platform/branding").status_code in (401, 403)
