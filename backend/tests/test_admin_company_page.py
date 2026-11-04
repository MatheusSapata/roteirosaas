"""Página da empresa no Admin Master: dados da empresa, faturas e pagamentos, avisos de cobrança,
mensagens enviadas e logs (inclusive as ações do próprio Admin Master)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.api.deps import get_current_superuser
from app.main import app
from app.models.activity_log import AdminActionLog, EmailLog
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.asaas import AsaasEventLog
from app.models.billing_notice import BillingNoticeSend
from app.models.cakto import CaktoEventLog
from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services.email import EmailClient


@pytest.fixture
def admin(db_session):
    user = User(name="Admin Master", email="admin@x.com", hashed_password="x", plan="infinity", is_superuser=True)
    db_session.add(user)
    db_session.commit()
    app.dependency_overrides[get_current_superuser] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_superuser, None)


@pytest.fixture
def company(db_session):
    db = db_session
    owner = User(name="Ana Souza", email="ana@x.com", hashed_password="x", plan="essencial")
    db.add(owner)
    db.flush()
    sub = Subscription(
        user_id=owner.id,
        plan="essencial",
        provider="cakto",
        status="active",
        mrr_amount=Decimal("49.90"),
        cakto_order_id="ord_1",
        valid_until=datetime.now(timezone.utc) + timedelta(days=20),
    )
    db.add(sub)
    db.flush()
    owner.subscription_id = sub.id
    agency = Agency(name="Agência Ana", slug="ana")
    db.add(agency)
    db.flush()
    db.add(AgencyUser(agency_id=agency.id, user_id=owner.id, role="owner"))
    other = User(name="Bruno", email="bruno@x.com", hashed_password="x", plan="free")
    db.add(other)
    db.flush()
    db.add(Subscription(user_id=other.id, plan="free", provider="asaas", status="active", mrr_amount=0))
    db.commit()
    return agency, owner


def test_detail_includes_the_company_row(client, admin, company):
    agency, owner = company
    data = client.get(f"/api/v1/admin/master/companies/{agency.id}").json()
    assert data["company"]["id"] == agency.id
    assert data["company"]["owner_email"] == "ana@x.com"
    assert data["company"]["mrr_amount"] == pytest.approx(49.9)


def test_billing_lists_cakto_payments_and_checkouts_of_the_owner_only(client, admin, company, db_session):
    agency, owner = company
    db_session.add_all([
        CaktoEventLog(
            event_id="c1",
            event_type="purchase_approved",
            status="processed",
            payload={"event": "purchase_approved", "data": {"id": "ord_1", "amount": 49.9, "customer": {"email": "ana@x.com"}}},
        ),
        CaktoEventLog(
            event_id="c2",
            event_type="purchase_approved",
            status="processed",
            payload={"event": "purchase_approved", "data": {"id": "ord_9", "amount": 89, "customer": {"email": "bruno@x.com"}}},
        ),
        CaktoEventLog(
            event_id="c3",
            event_type="subscription_canceled",
            status="processed",
            payload={"event": "subscription_canceled", "data": {"id": "ord_1", "customer": {"email": "ana@x.com"}}},
        ),
        CheckoutSession(
            token="tok1", offer_key="o", product_name="Roteiro Online", amount=Decimal("49.90"), status="paid",
            customer_name="Ana", customer_email="ANA@x.com", customer_document="1", customer_phone="1", customer_zipcode="1",
        ),
    ])
    db_session.commit()
    data = client.get(f"/api/v1/admin/master/companies/{agency.id}/billing").json()
    assert data["provider"] == "cakto"
    assert data["asaas"] is None
    assert [item["event_type"] for item in data["cakto_payments"]] == ["purchase_approved"]
    assert [item["token"] for item in data["checkouts"]] == ["tok1"]


def test_notices_and_messages_show_what_was_sent(client, admin, company, db_session, monkeypatch):
    agency, owner = company
    db_session.add_all([
        BillingNoticeSend(user_id=owner.id, payment_id="pay_1", step="vencimento", channel="whatsapp", status="sent",
                          recipient="5511999999999", due_date=date(2026, 11, 1), sent_at=datetime.now(timezone.utc)),
        BillingNoticeSend(user_id=owner.id, payment_id="pay_1", step="vencimento", channel="email", status="failed",
                          recipient="ana@x.com", error="SMTP fora"),
    ])
    db_session.commit()
    # E-mail do sistema: fica registrado (SMTP não configurado nos testes).
    EmailClient().send_email(to_email="ana@x.com", subject="Redefina sua senha", html_body="<p>x</p>", kind="redefinir_senha")
    EmailClient().send_email(to_email="bruno@x.com", subject="Outro", html_body="<p>x</p>")

    notices = client.get(f"/api/v1/admin/master/companies/{agency.id}/notices").json()
    assert notices["counts"] == {"sent": 1, "failed": 1}
    assert {item["channel"] for item in notices["items"]} == {"whatsapp", "email"}

    messages = client.get(f"/api/v1/admin/master/companies/{agency.id}/messages").json()["items"]
    sources = sorted(item["source"] for item in messages)
    assert sources == ["billing_notice", "billing_notice", "system_email"]
    email = next(item for item in messages if item["source"] == "system_email")
    assert email["status"] == "not_configured"
    assert email["kind_label"] == "Redefinir senha"


def test_admin_actions_are_logged_and_shown(client, admin, company, db_session):
    agency, owner = company
    response = client.patch(f"/api/v1/admin/users/{owner.id}/subscription", json={"plan": "growth"})
    assert response.status_code == 200, response.text
    response = client.post(f"/api/v1/admin/users/{owner.id}/asaas-cancel-at-period-end", json={})
    assert response.status_code == 200, response.text

    rows = db_session.query(AdminActionLog).order_by(AdminActionLog.id).all()
    assert [row.action for row in rows] == ["subscription_update", "schedule_cancel"]
    assert rows[0].actor_name == "Admin Master"
    assert "essencial → growth" in rows[0].summary

    db_session.add(AsaasEventLog(
        event_id="a1", event_type="PAYMENT_RECEIVED", status="processed",
        payload={"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_2", "customer": "cus_ana", "value": 49.9}},
    ))
    db_session.add(AsaasEventLog(
        event_id="a2", event_type="PAYMENT_RECEIVED", status="processed",
        payload={"event": "PAYMENT_RECEIVED", "payment": {"id": "pay_3", "customer": "cus_outro", "value": 10}},
    ))
    owner.subscription.asaas_customer_id = "cus_ana"
    db_session.commit()

    logs = client.get(f"/api/v1/admin/master/companies/{agency.id}/logs").json()
    assert logs["counts"]["admin"] == 2
    assert logs["counts"]["asaas"] == 1
    assert any(item["source"] == "asaas" and "pay_2" in item["detail"] for item in logs["items"])


def test_records_need_superuser(client, company):
    agency, _owner = company
    assert client.get(f"/api/v1/admin/master/companies/{agency.id}/logs").status_code in {401, 403}


def test_unknown_company_is_404(client, admin):
    assert client.get("/api/v1/admin/master/companies/999/billing").status_code == 404


def test_email_log_does_not_mark_failed_as_sent(db_session, monkeypatch):
    client = EmailClient()
    client.settings = client.settings.model_copy(
        update={"smtp_host": "smtp.x", "smtp_username": "u", "smtp_password": "p", "smtp_from_email": "no-reply@x.com"}
    )

    class Boom:
        def __init__(self, *args, **kwargs):
            raise OSError("sem rede")

    monkeypatch.setattr("app.services.email.smtplib.SMTP", Boom)
    monkeypatch.setattr("app.services.email.smtplib.SMTP_SSL", Boom)
    client.send_email(to_email="ana@x.com", subject="Oi", html_body="<p>x</p>")
    rows = db_session.query(EmailLog).all()
    assert [row.status for row in rows] == ["failed"]
