def register_payload(email: str, password: str = "SenhaNova123"):
    return {
        "name": "Tester",
        "email": email,
        "password": password,
        "cpf": "12345678909",
        "whatsapp": "5511999999999",
    }


def test_register_login_and_reset_password(client):
    email = "test@example.com"
    password = "SenhaForte123"
    new_password = "NovaSenha123"

    # Register user
    res = client.post("/api/v1/auth/register", json=register_payload(email, password))
    assert res.status_code == 200
    user_id = res.json()["id"]
    assert user_id > 0

    # Login with original password
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Request password reset (in dev/test we receive the token directly)
    forgot_res = client.post("/api/v1/auth/password/forgot", json={"email": email})
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json().get("reset_token")
    assert reset_token, "Reset token should be returned in non-prod environments"

    # Reset password
    reset_res = client.post("/api/v1/auth/password/reset", json={"token": reset_token, "password": new_password})
    assert reset_res.status_code == 200

    # Old password must fail now
    old_login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert old_login.status_code == 401

    # New password works
    new_login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": new_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()
