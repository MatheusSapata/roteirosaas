def _register_payload(email: str, password: str = "SenhaForte123"):
    return {
        "name": "Tester",
        "email": email,
        "password": password,
        "cpf": "12345678909",
        "whatsapp": "5511999999999",
    }


def _auth_headers(client, email: str, password: str):
    res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_update_agency_slug_with_dot(client):
    email = "slug-dot@example.com"
    password = "SenhaForte123"

    register_res = client.post("/api/v1/auth/register", json=_register_payload(email, password))
    assert register_res.status_code == 200

    headers = _auth_headers(client, email, password)

    create_res = client.post(
        "/api/v1/agencies",
        json={"name": "Agencia com ponto", "slug": "minha.agencia"},
        headers=headers,
    )
    assert create_res.status_code == 200
    assert create_res.json()["slug"] == "minha.agencia"

    agency_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/v1/agencies/{agency_id}",
        json={"slug": "nova.marca.2026"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["slug"] == "nova.marca.2026"
