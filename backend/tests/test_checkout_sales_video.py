"""Vídeo da capa da página de vendas: envio em partes pelo Admin Master, configuração salva junto
com Ofertas e checkout e o endereço público que a página consulta."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.deps import get_current_active_user, get_current_user
from app.main import app
from app.models.checkout import CheckoutSettings
from app.models.user import User
from app.schemas.checkout import CheckoutSalesVideo, CheckoutSettingsUpdate
from app.services import checkout, sales_video
from app.services.media_storage import media_storage

VIDEO = {"url": "https://agenciafiles.blob.core.windows.net/media/2f1c7c52-6a63-4f7e-9f0e-3c4f5a6b7c8d.mp4", "width": 1080, "height": 1080}


@pytest.fixture
def local_media(tmp_path, monkeypatch):
    monkeypatch.setattr(media_storage, "_local_dir", tmp_path)
    monkeypatch.setattr(media_storage, "_blob_service", None)
    return tmp_path


@pytest.fixture
def as_user():
    def _as(user: User) -> None:
        app.dependency_overrides[get_current_active_user] = lambda: user
        app.dependency_overrides[get_current_user] = lambda: user

    yield _as
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


def _admin() -> User:
    return User(id=999, email="admin@x.com", is_superuser=True, is_active=True)


def _update(db, **extra):
    payload = CheckoutSettingsUpdate.model_validate({"is_active": True, "offers": checkout.DEFAULT_OFFERS, "checkouts": checkout.DEFAULT_CHECKOUTS, **extra})
    return checkout.update_checkout_settings(db, payload)


def test_video_is_saved_kept_when_absent_and_removed_with_null(db_session):
    _update(db_session, sales_video={**VIDEO, "color": "#1de9a0"})
    record = db_session.query(CheckoutSettings).first()
    assert checkout.get_sales_video(record) == {**VIDEO, "poster_url": None, "color": "#1DE9A0"}

    # Salvar a tela sem o campo (ex.: aba aberta antes da atualização) não tira o vídeo.
    _update(db_session)
    assert checkout.get_sales_video(record)["url"] == VIDEO["url"]

    _update(db_session, sales_video=None)
    assert checkout.get_sales_video(record) is None


def test_video_only_accepts_media_urls_and_hex_color():
    with pytest.raises(ValidationError):
        CheckoutSalesVideo.model_validate({"url": "javascript:alert(1)"})
    with pytest.raises(ValidationError):
        CheckoutSalesVideo.model_validate({**VIDEO, "color": "verde"})
    assert CheckoutSalesVideo.model_validate({"url": "/uploads/x.mp4", "poster_url": "  "}).poster_url is None


def test_public_endpoint_returns_null_then_the_video(client, db_session):
    assert client.get("/api/v1/checkout/public/sales-video").json() is None
    _update(db_session, sales_video=VIDEO)
    body = client.get("/api/v1/checkout/public/sales-video").json()
    assert body["url"] == VIDEO["url"] and body["width"] == 1080


def test_upload_in_chunks_joins_the_parts(client, local_media, as_user):
    as_user(_admin())
    start = client.post("/api/v1/admin/checkout-settings/sales-video/uploads", json={"content_type": "video/mp4", "size": 10})
    assert start.status_code == 200
    name = start.json()["name"]
    assert name.endswith(".mp4") and start.json()["chunk_size"] == sales_video.SALES_VIDEO_CHUNK_BYTES

    base = f"/api/v1/admin/checkout-settings/sales-video/uploads/{name}"
    # As partes podem chegar fora de ordem; o fim junta pela posição.
    assert client.put(f"{base}/chunks/1", content=b"world").status_code == 204
    assert client.put(f"{base}/chunks/0", content=b"hello ").status_code == 204
    done = client.post(f"{base}/finish", json={"chunks": 2})
    assert done.status_code == 200
    assert done.json()["url"] == f"/uploads/{name}"
    assert (local_media / name).read_bytes() == b"hello world"
    assert not (local_media / ".chunks" / name).exists()


def test_upload_with_a_missing_part_fails(client, local_media, as_user):
    as_user(_admin())
    name = client.post("/api/v1/admin/checkout-settings/sales-video/uploads", json={"content_type": "video/mp4", "size": 10}).json()["name"]
    base = f"/api/v1/admin/checkout-settings/sales-video/uploads/{name}"
    client.put(f"{base}/chunks/0", content=b"hello")
    done = client.post(f"{base}/finish", json={"chunks": 2})
    assert done.status_code == 400
    assert not (local_media / name).exists()


def test_upload_refuses_other_types_big_files_and_odd_names(client, local_media, as_user):
    as_user(_admin())
    url = "/api/v1/admin/checkout-settings/sales-video/uploads"
    assert client.post(url, json={"content_type": "video/quicktime", "size": 10}).status_code == 415
    assert client.post(url, json={"content_type": "video/mp4", "size": sales_video.SALES_VIDEO_MAX_BYTES + 1}).status_code == 413
    assert client.put(f"{url}/..%2Fsegredo.mp4/chunks/0", content=b"x").status_code in {400, 404}
    assert client.put(f"{url}/nao-e-uuid.mp4/chunks/0", content=b"x").status_code == 400


def test_only_superuser_uploads(client, local_media, as_user):
    as_user(User(id=998, email="cliente@x.com", is_superuser=False, is_active=True, role="owner"))
    response = client.post("/api/v1/admin/checkout-settings/sales-video/uploads", json={"content_type": "video/mp4", "size": 10})
    assert response.status_code == 403


def test_azure_stages_blocks_and_commits_in_order(monkeypatch):
    calls: list[tuple] = []

    class FakeBlob:
        def stage_block(self, block_id, data, length):
            calls.append(("stage", block_id, data, length))

        def commit_block_list(self, blocks, content_settings):
            calls.append(("commit", [block.id for block in blocks], content_settings.content_type, content_settings.cache_control))

    monkeypatch.setattr(media_storage, "_blob_service", object())
    monkeypatch.setattr(media_storage, "_container_name", "media")
    monkeypatch.setattr(media_storage, "_base_url", "https://conta.blob.core.windows.net/media")
    monkeypatch.setattr(media_storage, "_build_blob_client", lambda name: FakeBlob())
    name = "2f1c7c52-6a63-4f7e-9f0e-3c4f5a6b7c8d.mp4"
    sales_video.save_chunk(name, 1, b"bb")
    url = sales_video.finish_upload(name, 2)
    assert url == f"https://conta.blob.core.windows.net/media/{name}"
    assert calls == [
        ("stage", "000001", b"bb", 2),
        ("commit", ["000000", "000001"], "video/mp4", "public, max-age=31536000, immutable"),
    ]
