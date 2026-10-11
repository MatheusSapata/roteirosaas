from __future__ import annotations

from types import SimpleNamespace

from app.api.deps import get_current_superuser
from app.main import app

BASE = "/api/v1/admin/master/image-api-keys"


def test_image_api_keys_crud_and_separation_from_flight_keys(client):
    app.dependency_overrides[get_current_superuser] = lambda: SimpleNamespace(is_superuser=True)
    try:
        first = client.post(BASE, json={"provider": "unsplash", "label": "Conta 1", "api_key": "abcd-1234-unsplash"})
        assert first.status_code == 200, first.text
        body = first.json()
        assert body["monthly_limit"] == 50 and body["status"] == "active" and body["key_masked"].endswith("lash")
        assert client.post(BASE, json={"provider": "pexels", "label": "Pexels", "api_key": "pexels-key-0001", "hourly_limit": 180}).json()["monthly_limit"] == 180
        assert client.post(BASE, json={"provider": "airlabs", "label": "Outra", "api_key": "abcdef"}).status_code == 400
        client.post("/api/v1/admin/master/flight-api-keys", json={"provider": "airlabs", "label": "Voo", "api_key": "airlabs-key-1"})

        listed = client.get(BASE).json()
        assert {item["provider"] for item in listed["items"]} == {"unsplash", "pexels"}
        assert listed["summary"]["unsplash"]["active_keys"] == 1 and listed["summary"]["photos"] == 0
        flights = client.get("/api/v1/admin/master/flight-api-keys").json()
        assert {item["provider"] for item in flights["items"]} == {"airlabs"}
        # Uma rota não mexe na chave da outra.
        assert client.post(f"/api/v1/admin/master/flight-api-keys/{body['id']}/pause").status_code == 404
        flight_id = flights["items"][0]["id"]
        assert client.delete(f"{BASE}/{flight_id}").status_code == 404

        paused = client.post(f"{BASE}/{body['id']}/pause").json()
        assert paused["status"] == "paused" and not paused["is_active"]
        edited = client.patch(f"{BASE}/{body['id']}", json={"hourly_limit": 40, "is_active": True}).json()
        assert edited["monthly_limit"] == 40 and edited["status"] == "active"
        assert client.delete(f"{BASE}/{body['id']}").status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)


def test_curated_stock_photos_crud_and_priority(client, db_session, monkeypatch):
    from app.api.v1.endpoints import stock_photos
    from app.services import stock_images

    app.dependency_overrides[get_current_superuser] = lambda: SimpleNamespace(is_superuser=True)
    from app.services import curated_photos

    monkeypatch.setattr(stock_photos, "download_photo", lambda url: url.encode())
    monkeypatch.setattr(curated_photos, "store_photo", lambda data, name="": (f"/uploads/{data.decode()[-8:]}.webp", 1600, 1000))
    base = "/api/v1/admin/master/stock-photos"
    try:
        created = client.post(base, json={
            "url": "https://turismo.sc.gov.br/fotos/beto-carrero.jpg",
            "keywords": "Beto Carrero, parque de diversões; theme park",
            "author": "Ana Souza", "source_name": "Santur", "source_url": "https://turismo.sc.gov.br",
        })
        assert created.status_code == 200, created.text
        photo = created.json()
        assert photo["keywords"] == ["beto carrero", "parque de diversoes", "theme park"] and photo["url"].startswith("/uploads/")
        assert client.post(base, json={"url": "https://turismo.sc.gov.br/fotos/beto-carrero.jpg", "keywords": "x y"}).status_code == 409
        assert client.post(base, json={"url": "https://a.com/b.jpg", "keywords": "parque", "author_url": "javascript:alert(1)"}).status_code == 400
        client.post(base, json={"url": "https://a.com/sem-credito.jpg", "keywords": "gramado"})
        assert len(client.get(base, params={"q": "beto"}).json()) == 1

        # A foto cadastrada vem antes de qualquer banco, sem chamar API, quando a palavra-chave está na busca.
        monkeypatch.setattr(stock_images, "available_image_keys", lambda db, provider: (_ for _ in ()).throw(AssertionError("não devia chamar")))
        found = stock_images.search_stock_images(db_session, None, "Beto Carrero World Santa Catarina Brazil")
        assert [image.id for image in found] == [photo["id"]]
        image = found[0]
        assert stock_images.credit_for(image, "u") == {
            "url": "u", "name": "Ana Souza", "link": "", "provider": "Santur", "providerLink": "https://turismo.sc.gov.br",
        }
        assert stock_images.materialize(db_session, None, image) == photo["url"]
        # Sem autor nem fonte: a foto entra, mas sem "©".
        [plain] = stock_images.search_stock_images(db_session, None, "Gramado street")
        assert stock_images.credit_for(plain, "u") is None
        # "parque" sozinho não casa com "parque de diversões" (precisa de todas as palavras).
        assert stock_images._curated_matches(db_session, stock_images.query_terms("parque aquatico")) == []

        edited = client.patch(f"{base}/{photo['id']}", json={"keywords": "Penha, Beto Carrero", "author": ""}).json()
        assert edited["keywords"] == ["penha", "beto carrero"] and edited["author"] is None
        assert client.delete(f"{base}/{photo['id']}").status_code == 200
        assert client.get(base).json()[0]["keywords"] == ["gramado"]
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)


def test_curated_keywords_from_file_names_and_folders(db_session, monkeypatch):
    import io
    import zipfile

    from app.services import curated_photos, stock_images
    from app.services.curated_photos import Credits, context_words, photo_keywords, strip_common_folders

    assert context_words("Atrações/Nerf/IMG_0123.jpg") == ["atracoes", "nerf"]
    assert context_words("DSC0001-castelo_final-2.JPG") == ["castelo"]
    assert photo_keywords("Beto Carrero, Penha", "Nerf_02.jpg") == "beto carrero nerf, beto carrero, penha"
    assert photo_keywords("Beto Carrero", "beto-carrero-castelo.jpg") == "beto carrero castelo, beto carrero"
    assert strip_common_folders(["Beto Carrero Imprensa/Nerf/a.jpg", "Beto Carrero Imprensa/Castelo/b.jpg"]) == ["Nerf/a.jpg", "Castelo/b.jpg"]
    assert strip_common_folders(["Kit/a.jpg"]) == ["a.jpg"]
    assert curated_photos.direct_download_url("https://www.dropbox.com/scl/fo/abc/xyz?rlkey=k&dl=0") == (
        "https://www.dropbox.com/scl/fo/abc/xyz?rlkey=k&dl=1"
    )

    # Pasta do Dropbox (vem em .zip): cada foto ganha o contexto da pasta e do nome.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("Beto Carrero Imprensa/Nerf/IMG_1.jpg", b"nerf")
        archive.writestr("Beto Carrero Imprensa/Castelo encantado.jpg", b"castelo")
        archive.writestr("Beto Carrero Imprensa/leia-me.txt", b"x")
        archive.writestr("__MACOSX/Beto Carrero Imprensa/._IMG_1.jpg", b"lixo")
    monkeypatch.setattr(curated_photos, "download", lambda url, limit: (buffer.getvalue(), "application/zip"))
    monkeypatch.setattr(curated_photos, "store_photo", lambda data, name="": (f"/uploads/{data.decode()}.webp", 1600, 1000))
    job = curated_photos.new_job()
    session_factory = lambda: db_session  # noqa: E731
    db_session.close = lambda: None
    curated_photos.run_link_import(job, session_factory, "https://www.dropbox.com/scl/fo/abc?dl=0", "Beto Carrero, Penha",
                                   Credits(source_name="Divulgação Beto Carrero World"))
    assert job.as_dict()["status"] == "done" and job.added == 2 and job.total == 2

    nerf = stock_images.search_stock_images(db_session, None, "Nerf Beto Carrero World Brazil")
    assert nerf[0].stored_url == "/uploads/nerf.webp" and nerf[0].alt == "nerf"
    castle = stock_images.search_stock_images(db_session, None, "beto carrero castelo | castle")
    assert castle[0].stored_url == "/uploads/castelo.webp"
    assert stock_images._curated_matches(db_session, stock_images.query_terms("nerf blaster")) == []
    assert stock_images.curated_catalog(db_session) == ["beto carrero castelo", "beto carrero encantado", "beto carrero nerf"]

    # A mesma pasta de novo: nada duplica.
    job2 = curated_photos.new_job()
    curated_photos.run_link_import(job2, session_factory, "https://www.dropbox.com/scl/fo/abc?dl=0", "Beto Carrero", Credits())
    assert job2.added == 0 and job2.duplicates == 2
