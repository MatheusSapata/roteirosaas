import io

from PIL import Image

from app.api.v1.endpoints import media as media_endpoint
from app.services.background_removal import _connected_solid_background_alpha


def _register_payload(email: str) -> dict[str, str]:
    return {
        "name": "Tester",
        "email": email,
        "password": "SenhaForte123",
        "cpf": "52998224725" if "outsider" in email else "12345678909",
        "whatsapp": "5511999999999",
    }


def _authenticated_agency(client, email: str) -> tuple[dict[str, str], int]:
    assert client.post("/api/v1/auth/register", json=_register_payload(email)).status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SenhaForte123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    agency = client.post(
        "/api/v1/agencies",
        json={"name": "Agência de teste", "slug": email.split("@", 1)[0]},
        headers=headers,
    )
    assert agency.status_code == 200
    return headers, agency.json()["id"]


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_solid_logo_background_is_removed_without_erasing_foreground() -> None:
    image = Image.new("RGB", (80, 40), "black")
    for x in range(20, 60):
        for y in range(12, 28):
            image.putpixel((x, y), (255, 255, 255))

    alpha = _connected_solid_background_alpha(image)

    assert alpha is not None
    assert alpha.getpixel((0, 0)) == 0
    assert alpha.getpixel((40, 20)) == 255


def test_photo_like_edges_do_not_trigger_solid_background_removal() -> None:
    image = Image.new("RGB", (40, 40))
    for x in range(40):
        for y in range(40):
            image.putpixel((x, y), ((x * 7) % 256, (y * 9) % 256, ((x + y) * 5) % 256))

    assert _connected_solid_background_alpha(image) is None


def test_partially_transparent_logo_still_loses_opaque_solid_background() -> None:
    image = Image.new("RGBA", (80, 40), (0, 0, 0, 255))
    image.putpixel((0, 0), (0, 0, 0, 120))
    for x in range(20, 60):
        for y in range(12, 28):
            image.putpixel((x, y), (255, 255, 255, 255))

    alpha = _connected_solid_background_alpha(image)

    assert alpha is not None
    assert alpha.getpixel((10, 10)) == 0
    assert alpha.getpixel((40, 20)) == 255


def test_remove_background_returns_transparent_png(client, monkeypatch) -> None:
    headers, agency_id = _authenticated_agency(client, "remove-bg@example.com")
    output = io.BytesIO()
    Image.new("RGBA", (8, 8), (255, 0, 0, 0)).save(output, format="PNG")
    monkeypatch.setattr(media_endpoint, "remove_image_background", lambda _: output.getvalue())

    response = client.post(
        "/api/v1/media/remove-background",
        params={"agency_id": agency_id},
        files={"file": ("source.png", _png_bytes(), "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    with Image.open(io.BytesIO(response.content)) as image:
        assert image.mode == "RGBA"
        assert image.getpixel((0, 0))[3] == 0


def test_remove_background_rejects_non_image(client, monkeypatch) -> None:
    headers, agency_id = _authenticated_agency(client, "remove-bg-invalid@example.com")
    called = False

    def fake_remove(_: bytes) -> bytes:
        nonlocal called
        called = True
        return b""

    monkeypatch.setattr(media_endpoint, "remove_image_background", fake_remove)
    response = client.post(
        "/api/v1/media/remove-background",
        params={"agency_id": agency_id},
        files={"file": ("source.txt", b"not an image", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 415
    assert called is False


def test_remove_background_requires_agency_membership(client, monkeypatch) -> None:
    owner_headers, agency_id = _authenticated_agency(client, "remove-bg-owner@example.com")
    assert owner_headers
    outsider_headers, _ = _authenticated_agency(client, "remove-bg-outsider@example.com")
    monkeypatch.setattr(media_endpoint, "remove_image_background", lambda _: _png_bytes())

    response = client.post(
        "/api/v1/media/remove-background",
        params={"agency_id": agency_id},
        files={"file": ("source.png", _png_bytes(), "image/png")},
        headers=outsider_headers,
    )

    assert response.status_code == 403
