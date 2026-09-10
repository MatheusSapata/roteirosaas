from app.services.viajechat import ViajeChatClient


def test_create_contact_sends_all_supported_lead_fields(monkeypatch):
    captured = {}
    client = ViajeChatClient("test-token")

    def fake_request(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return {"data": {"id": "contact-1"}}

    monkeypatch.setattr(client, "_request", fake_request)

    client.create_contact(
        name="Joao Silva",
        phone="5511999999999",
        email="joao@example.com",
        cpf_cnpj="12345678901",
        city="Sao Paulo",
        birth_date="1990-05-20",
        idempotency_key="contact-key",
    )

    assert captured == {
        "method": "POST",
        "path": "/contacts",
        "json": {
            "name": "Joao Silva",
            "phone": "5511999999999",
            "email": "joao@example.com",
            "cpf_cnpj": "12345678901",
            "city": "Sao Paulo",
            "birth_date": "1990-05-20",
        },
        "headers": {"Idempotency-Key": "contact-key"},
    }


def test_update_contact_is_partial_and_omits_empty_fields(monkeypatch):
    captured = {}
    client = ViajeChatClient("test-token")

    def fake_request(method, path, **kwargs):
        captured.update(method=method, path=path, **kwargs)
        return {"data": {"id": "contact-1"}}

    monkeypatch.setattr(client, "_request", fake_request)

    client.update_contact(
        "contact-1",
        name="Joao Silva",
        email="",
        cpf_cnpj="12345678901",
        city="Recife",
        birth_date=None,
        idempotency_key="update-key",
    )

    assert captured == {
        "method": "PUT",
        "path": "/contacts/contact-1",
        "json": {
            "name": "Joao Silva",
            "cpf_cnpj": "12345678901",
            "city": "Recife",
        },
        "headers": {"Idempotency-Key": "update-key"},
    }
