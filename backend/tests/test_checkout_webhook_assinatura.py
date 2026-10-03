from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.api.v1.endpoints import billing as billing_endpoint
from app.models.checkout import CheckoutSession
from app.models.user import User
from app.services import checkout as checkout_service

TOKEN = "A" * 32


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    monkeypatch.setattr(checkout_service, "mark_viajechat_signed", lambda **_k: None)
    monkeypatch.setattr(checkout_service, "republish_all_user_pages", lambda *_a, **_k: None)
    monkeypatch.setattr(checkout_service, "publish_subscription_notification", lambda **_k: None)
    monkeypatch.setattr(checkout_service, "_dispatch_meta_checkout_events", lambda *_a, **_k: None)
    monkeypatch.setattr(checkout_service, "send_notification", lambda **_k: None)
    monkeypatch.setattr(billing_endpoint.settings, "asaas_webhook_token", None)


def _sessao(db, *, method="pix", status="awaiting_payment", metadata=None):
    row = CheckoutSession(
        token=TOKEN,
        offer_key="escala-mensal",
        product_name="Plano Escala",
        plan_key="scale",
        billing_cycle="monthly",
        amount=Decimal("129.90"),
        status=status,
        payment_method=method,
        customer_name="Cliente Teste",
        customer_email="cliente@example.com",
        customer_document="12345678901",
        customer_phone="47999999999",
        customer_zipcode="89000000",
        metadata_json=metadata
        if metadata is not None
        else {
            "pix_mode": "automatic",
            "asaas_pix_automatic_authorization_id": "auth_1",
            "asaas_pix_automatic_authorization_status": "CREATED",
        },
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _user(db) -> User:
    db.expire_all()
    return db.query(User).filter(User.email == "cliente@example.com").first()


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def test_webhook_recusa_chamada_sem_token_quando_configurado(client, db_session, monkeypatch):
    monkeypatch.setattr(billing_endpoint.settings, "asaas_webhook_token", "segredo-do-asaas")
    _sessao(db_session)
    payload = {"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_x", "status": "RECEIVED", "externalReference": f"checkout:{TOKEN}"}}
    assert client.post("/api/v1/billing/webhook", json=payload).status_code == 401
    assert client.post("/api/v1/billing/webhook", json=payload, headers={"asaas-access-token": "errado"}).status_code == 401
    assert _user(db_session) is None
    ok = client.post("/api/v1/billing/webhook", json=payload, headers={"asaas-access-token": "segredo-do-asaas"})
    assert ok.status_code == 200
    assert _user(db_session).subscription.status == "active"


def test_webhook_sem_token_configurado_continua_funcionando(client, db_session):
    _sessao(db_session)
    payload = {"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_x", "status": "RECEIVED", "externalReference": f"checkout:{TOKEN}"}}
    assert client.post("/api/v1/billing/webhook", json=payload).status_code == 200
    assert _user(db_session).subscription.status == "active"


def test_primeiro_pagamento_nao_conta_como_renovacao(monkeypatch, db_session):
    session = _sessao(db_session)

    class FakeClient:
        def get_pix_automatic_authorization(self, _id):
            return {"id": "auth_1", "status": "ACTIVE"}

    monkeypatch.setattr(checkout_service, "_ensure_asaas_client", lambda: FakeClient())
    checkout_service.refresh_session_status(db_session, session)
    validade = _user(db_session).subscription.valid_until
    checkout_service.handle_asaas_checkout_webhook(
        db_session,
        {"event": "PAYMENT_RECEIVED", "payment": {
            "id": "pay_primeiro", "status": "RECEIVED", "pixAutomaticAuthorizationId": "auth_1",
            "dueDate": date.today().isoformat()}},
    )
    assert _user(db_session).subscription.valid_until == validade


def test_validade_inicial_cobre_ate_a_proxima_cobranca(monkeypatch, db_session):
    session = _sessao(db_session)

    class FakeClient:
        def get_pix_automatic_authorization(self, _id):
            return {"id": "auth_1", "status": "ACTIVE"}

    monkeypatch.setattr(checkout_service, "_ensure_asaas_client", lambda: FakeClient())
    checkout_service.refresh_session_status(db_session, session)
    db_session.expire_all()
    session = db_session.query(CheckoutSession).first()
    proxima = date.fromisoformat(session.metadata_json["asaas_pix_automatic_next_due_date"])
    validade = _as_utc(_user(db_session).subscription.valid_until)
    assert validade.date() >= proxima + timedelta(days=1)
    assert validade - datetime.now(timezone.utc) <= timedelta(days=34)


def test_renovacao_no_cartao_estende_validade_uma_vez(client, db_session):
    _sessao(db_session, method="card", metadata={"asaas_subscription_id": "sub_card"})
    base = {"subscription": "sub_card", "externalReference": f"checkout:{TOKEN}"}
    client.post("/api/v1/billing/webhook", json={"event": "PAYMENT_CONFIRMED", "payment": {
        **base, "id": "pay_1", "status": "CONFIRMED", "dueDate": date.today().isoformat()}})
    v1 = _as_utc(_user(db_session).subscription.valid_until)
    # o mesmo primeiro pagamento sendo recebido depois não renova
    client.post("/api/v1/billing/webhook", json={"event": "PAYMENT_RECEIVED", "payment": {
        **base, "id": "pay_1", "status": "RECEIVED", "dueDate": date.today().isoformat()}})
    assert _as_utc(_user(db_session).subscription.valid_until) == v1
    proximo = (date.today() + timedelta(days=30)).isoformat()
    for evento, status in (("PAYMENT_CONFIRMED", "CONFIRMED"), ("PAYMENT_RECEIVED", "RECEIVED")):
        client.post("/api/v1/billing/webhook", json={"event": evento, "payment": {
            **base, "id": "pay_2", "status": status, "dueDate": proximo}})
    v2 = _as_utc(_user(db_session).subscription.valid_until)
    assert v2 - v1 >= timedelta(days=28)
    assert v2 - v1 <= timedelta(days=33)


@pytest.mark.parametrize(("evento", "status_pagamento"), [("PAYMENT_CREATED", "PENDING"), ("PAYMENT_OVERDUE", "OVERDUE")])
def test_eventos_da_cobranca_de_renovacao_nao_desligam_a_venda(db_session, evento, status_pagamento):
    session = _sessao(db_session, status="paid", metadata={
        "pix_mode": "automatic",
        "asaas_pix_automatic_authorization_id": "auth_1",
        "asaas_pix_automatic_authorization_status": "ACTIVE",
        "asaas_pix_automatic_renewal_payment_ids": ["pay_renov"],
    })
    session.paid_at = datetime.now(timezone.utc)
    db_session.commit()
    checkout_service.handle_asaas_checkout_webhook(db_session, {
        "event": evento,
        "payment": {"id": "pay_renov", "status": status_pagamento, "externalReference": f"co:{TOKEN}"},
    })
    db_session.expire_all()
    session = db_session.query(CheckoutSession).first()
    assert session.status == "paid"
    assert session.metadata_json["asaas_last_renewal_payment_status"] == status_pagamento


def test_estorno_continua_marcando_a_venda(db_session):
    session = _sessao(db_session, status="paid", metadata={"pix_mode": "automatic"})
    session.paid_at = datetime.now(timezone.utc)
    db_session.commit()
    checkout_service.handle_asaas_checkout_webhook(db_session, {
        "event": "PAYMENT_REFUNDED",
        "payment": {"id": "pay_1", "status": "REFUNDED", "externalReference": f"checkout:{TOKEN}"},
    })
    db_session.expire_all()
    assert db_session.query(CheckoutSession).first().status == "refunded"


def test_cobranca_proxima_ao_upgrade_tambem_renova(db_session):
    session = _sessao(db_session, method="card", status="paid", metadata={"upgrade_mode": True})
    session.paid_at = datetime.now(timezone.utc)
    db_session.commit()
    assert checkout_service._is_new_cycle_payment(session, {}, {"id": "p", "dueDate": (date.today() + timedelta(days=5)).isoformat()})
    assert not checkout_service._is_new_cycle_payment(session, {}, {"id": "p", "dueDate": date.today().isoformat()})
