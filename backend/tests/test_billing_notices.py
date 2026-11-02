"""Avisos de cobrança aos clientes (e-mail e WhatsApp). Todos os dados são fictícios."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.api.deps import get_current_superuser
from app.main import app
from app.models.billing_notice import BillingNoticeSend
from app.models.subscription import Subscription
from app.models.user import User
from app.services import billing_notices as notices
from app.services.billing_account import mark_payment_replaced

TODAY = date(2026, 11, 2)


class FakeAsaas:
    def __init__(self, payments: list[dict]) -> None:
        self.payments = payments
        self.updated_customers: list[tuple[str, dict]] = []

    def list_payments(self, **params):
        rows = list(self.payments)
        if "status" in params:
            rows = [p for p in rows if p.get("status") == params["status"]]
        if "customer" in params:
            rows = [p for p in rows if p.get("customer") == params["customer"]]
        if "dueDate[ge]" in params:
            rows = [p for p in rows if p["dueDate"] >= params["dueDate[ge]"]]
        if "dueDate[le]" in params:
            rows = [p for p in rows if p["dueDate"] <= params["dueDate[le]"]]
        offset = int(params.get("offset") or 0)
        return {"data": rows[offset: offset + int(params.get("limit") or 100)]}

    def get_payment(self, payment_id):
        return next(p for p in self.payments if p["id"] == payment_id)

    def update_customer(self, customer_id, payload):
        self.updated_customers.append((customer_id, payload))
        return {}


@pytest.fixture
def outbox(monkeypatch):
    sent: list[tuple[str, str, str]] = []

    def fake_whatsapp(db, settings_row, number, text):
        sent.append(("whatsapp", number, text))

    def fake_email(to_email, subject, html_body, text_body):
        sent.append(("email", to_email, subject))

    monkeypatch.setattr(notices, "send_whatsapp", fake_whatsapp)
    monkeypatch.setattr(notices, "send_email", fake_email)
    return sent


def make_user(db, *, email="cliente@example.com", status="active", payment_type="pix", whatsapp="47999990000",
              created_days_ago=90) -> User:
    user = User(name="Cliente Fictício", email=email, hashed_password="x", plan="essencial", whatsapp=whatsapp,
                created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago))
    db.add(user)
    db.flush()
    sub = Subscription(user_id=user.id, plan="essencial", provider="asaas", billing_cycle="monthly", status=status,
                       mrr_amount=Decimal("97"), asaas_customer_id=f"cus_{user.id}", payment_method_type=payment_type)
    db.add(sub)
    db.flush()
    user.subscription_id = sub.id
    db.commit()
    db.refresh(user)
    return user


def payment(user, pid="pay_1", *, due: date, created: date | None = None, status="PENDING", billing="PIX", value=97.0):
    return {
        "id": pid, "customer": f"cus_{user.id}", "externalReference": f"{user.id}:essencial:monthly", "status": status,
        "billingType": billing, "value": value, "dueDate": due.isoformat(),
        "dateCreated": (created or due - timedelta(days=40)).isoformat(),
        "invoiceUrl": f"https://www.asaas.com/i/{pid}",
    }


def enable(db, **changes):
    row = notices.get_settings_row(db)
    row.enabled = True
    row.sender_instance_name = "roteiroonline-cobranca"
    row.sender_status = "connected"
    # Ligado há um mês: os testes de rotina não esbarram na trava de envio retroativo.
    row.schedule_since = TODAY - timedelta(days=30)
    for key, value in changes.items():
        setattr(row, key, value)
    db.commit()
    return row


def steps_sent(outbox):
    return [item for item in outbox]


# ---------------------------------------------------------------- quando cada etapa sai


def test_annual_renewal_created_after_payment_waits_until_10_days_before_due():
    """O caso da Play UP: a renovação anual nasce logo após o pagamento e só vence um ano depois."""
    pay = {"dueDate": "2027-09-28", "dateCreated": "2026-09-30"}
    assert notices.available_date(pay, 10) == date(2027, 9, 18)
    assert notices.steps_on(pay, date(2026, 9, 30), 10, date(2026, 9, 30)) == []
    assert notices.steps_on(pay, date(2027, 9, 18), 10, date(2027, 9, 18)) == ["fatura_disponivel"]


def test_nothing_goes_out_on_the_day_the_charge_is_created():
    """O cliente pode estar pagando no checkout naquele momento."""
    pay = {"dueDate": "2026-11-05", "dateCreated": "2026-11-02"}
    assert notices.steps_on(pay, date(2026, 11, 2), 10, date(2026, 11, 2)) == []
    assert notices.steps_on(pay, date(2026, 11, 3), 10, date(2026, 11, 3)) == ["fatura_disponivel"]


def test_reminders_do_not_go_out_with_available_on_the_same_day():
    pay = {"dueDate": "2026-11-05", "dateCreated": "2026-11-01"}
    # 3 dias antes, mas é o dia da "Fatura disponível": só ela sai.
    assert notices.steps_on(pay, date(2026, 11, 2), 10, date(2026, 11, 2)) == ["fatura_disponivel"]


def test_late_available_catches_up_once():
    pay = {"dueDate": "2026-11-05", "dateCreated": "2026-10-01"}
    # Deveria ter saído em 26/10 (rotina parada): sai no próximo dia da rotina, sem o lembrete junto.
    assert notices.steps_on(pay, date(2026, 11, 2), 10, date(2026, 11, 2)) == ["fatura_disponivel"]
    # Já saiu antes: o lembrete de 3 dias sai normalmente.
    assert notices.steps_on(pay, date(2026, 11, 2), 10, date(2026, 11, 2), available_done=True) == ["lembrete_3_dias"]


def test_overdue_steps():
    pay = {"dueDate": "2026-11-01", "dateCreated": "2026-10-01"}
    assert notices.steps_on(pay, date(2026, 11, 2), 10, date(2026, 11, 2), True) == ["atraso_1_dia"]
    assert notices.steps_on(pay, date(2026, 11, 4), 10, date(2026, 11, 4), True) == ["atraso_3_dias"]


# ---------------------------------------------------------------- rotina diária


def test_daily_run_sends_each_step_once_per_channel(db_session, outbox):
    user = make_user(db_session)
    enable(db_session)
    fake = FakeAsaas([payment(user, due=TODAY + timedelta(days=8))])

    first = notices.run_daily(db_session, today=TODAY, client=fake)
    second = notices.run_daily(db_session, today=TODAY, client=fake)

    assert first["sent"] == 2 and second.get("sent", 0) == 0
    assert sorted(item[0] for item in outbox) == ["email", "whatsapp"]
    assert outbox[0][1] == "5547999990000" if outbox[0][0] == "whatsapp" else outbox[1][1] == "5547999990000"
    rows = db_session.query(BillingNoticeSend).all()
    assert {(r.step, r.channel, r.status) for r in rows} == {
        ("fatura_disponivel", "whatsapp", "sent"), ("fatura_disponivel", "email", "sent")
    }


def test_whatsapp_text_uses_the_invoice_data(db_session, outbox):
    user = make_user(db_session)
    enable(db_session)
    notices.run_daily(db_session, today=TODAY, client=FakeAsaas([payment(user, due=date(2026, 11, 10), value=129.9)]))
    text = next(item[2] for item in outbox if item[0] == "whatsapp")
    assert "Cliente" in text and "R$ 129,90" in text and "10/11/2026" in text and "https://www.asaas.com/i/pay_1" in text


def test_nothing_goes_out_with_the_main_switch_off(db_session, outbox):
    user = make_user(db_session)
    fake = FakeAsaas([payment(user, due=TODAY + timedelta(days=5))])
    assert notices.run_daily(db_session, today=TODAY, client=fake) == {
        "sent": 0, "failed": 0, "skipped": 0, "payments": 0, "disabled": True
    }
    assert outbox == []


def test_card_and_pix_automatic_skip_reminders_but_get_overdue(db_session, outbox):
    user = make_user(db_session, payment_type="credit_card")
    enable(db_session)
    fake = FakeAsaas([
        payment(user, "pay_card_soon", due=TODAY + timedelta(days=3), billing="CREDIT_CARD"),
        payment(user, "pay_card_late", due=TODAY - timedelta(days=1), status="OVERDUE", billing="CREDIT_CARD"),
    ])
    notices.run_daily(db_session, today=TODAY, client=fake)
    rows = {(r.payment_id, r.step) for r in db_session.query(BillingNoticeSend).all()}
    assert rows == {("pay_card_late", "atraso_1_dia")}


def test_ended_account_replaced_and_already_paid_period_get_nothing(db_session, outbox):
    ended = make_user(db_session, email="ended@example.com", status="cancelled")
    active = make_user(db_session, email="active@example.com")
    enable(db_session)
    mark_payment_replaced(db_session, "pay_replaced", reason="renovação")
    fake = FakeAsaas([
        payment(ended, "pay_ended", due=TODAY + timedelta(days=5)),
        payment(active, "pay_replaced", due=TODAY + timedelta(days=5)),
        # Período de 01/11 a 01/12 já pago: a fatura em aberto de 10/11 é desse período.
        payment(active, "pay_paid", due=date(2026, 11, 1), status="RECEIVED"),
        payment(active, "pay_covered", due=date(2026, 11, 10)),
    ])
    summary = notices.run_daily(db_session, today=TODAY, client=fake)
    assert outbox == [] and summary["skipped"] == 3


def test_failed_send_is_retried_up_to_three_times(db_session, monkeypatch):
    user = make_user(db_session, whatsapp=None)
    enable(db_session)
    calls = []

    def broken_email(*args):
        calls.append(args)
        raise RuntimeError("SMTP fora do ar")

    monkeypatch.setattr(notices, "send_email", broken_email)
    fake = FakeAsaas([payment(user, due=TODAY + timedelta(days=6))])
    notices.run_daily(db_session, today=TODAY, client=fake)
    row = db_session.query(BillingNoticeSend).one()
    assert row.status == "failed" and row.attempts == 1 and "SMTP" in row.error

    later = datetime.now(timezone.utc) + timedelta(hours=1)
    for _ in range(4):
        db_session.query(BillingNoticeSend).update({BillingNoticeSend.updated_at: datetime.now(timezone.utc) - timedelta(hours=1)})
        db_session.commit()
        notices.retry_failed(db_session, client=fake, now=later)
    db_session.refresh(row)
    assert row.attempts == 3 and len(calls) == 3


def test_claim_is_atomic(db_session):
    args = dict(payment_id="pay_x", step="vence_hoje", channel="email", user_id=None, recipient="a@example.com",
                due_date=TODAY, context={})
    assert notices.claim(db_session, **args) is not None
    assert notices.claim(db_session, **args) is None


def test_retry_cancels_when_invoice_is_no_longer_open(db_session, monkeypatch):
    user = make_user(db_session)
    enable(db_session)
    monkeypatch.setattr(notices, "send_whatsapp", lambda *a: (_ for _ in ()).throw(RuntimeError("desconectado")))
    monkeypatch.setattr(notices, "send_email", lambda *a: None)
    pay = payment(user, due=TODAY + timedelta(days=6))
    fake = FakeAsaas([pay])
    notices.run_daily(db_session, today=TODAY, client=fake)
    pay["status"] = "RECEIVED"
    db_session.query(BillingNoticeSend).update({BillingNoticeSend.updated_at: datetime.now(timezone.utc) - timedelta(hours=1)})
    db_session.commit()
    notices.retry_failed(db_session, client=fake)
    row = db_session.query(BillingNoticeSend).filter_by(channel="whatsapp").one()
    assert row.status == "cancelled"


# ---------------------------------------------------------------- pagamento confirmado


def test_payment_confirmed_goes_out_once(db_session, outbox):
    user = make_user(db_session)
    enable(db_session)
    paid = payment(user, due=TODAY, status="CONFIRMED") | {"paymentDate": TODAY.isoformat()}
    now = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)
    assert notices.payment_confirmed(db_session, paid, now=now) == {"whatsapp": "sent", "email": "sent"}
    assert notices.payment_confirmed(db_session, paid | {"status": "RECEIVED"}, now=now) == {
        "whatsapp": "skipped", "email": "skipped"
    }
    assert len(outbox) == 2


def test_payment_confirmed_skips_new_accounts_and_old_payments(db_session, outbox):
    new_user = make_user(db_session, email="new@example.com", created_days_ago=0)
    old_user = make_user(db_session, email="old@example.com")
    enable(db_session)
    assert notices.payment_confirmed(db_session, payment(new_user, "pay_new", due=TODAY, status="RECEIVED")) == {}
    old = payment(old_user, "pay_old", due=TODAY, status="RECEIVED") | {"paymentDate": "2026-01-10"}
    assert notices.payment_confirmed(db_session, old) == {}
    assert outbox == []


# ---------------------------------------------------------------- próximos envios


def test_upcoming_shows_plan_and_cancel_reactivate(db_session, outbox):
    user = make_user(db_session)
    enable(db_session)
    fake = FakeAsaas([payment(user, due=TODAY + timedelta(days=12))])

    preview = notices.upcoming(db_session, days=7, client=fake, today=TODAY)
    item = preview["items"][0]
    assert item["date"] == (TODAY + timedelta(days=2)).isoformat() and item["step"] == "fatura_disponivel"
    assert {c["state"] for c in item["channels"]} == {"scheduled"}

    assert notices.cancel_planned(db_session, payment_id="pay_1", step="fatura_disponivel", channel="whatsapp",
                                  user_id=user.id, due_date=None)
    preview = notices.upcoming(db_session, days=7, client=fake, today=TODAY)
    states = {c["channel"]: c["state"] for c in preview["items"][0]["channels"]}
    assert states == {"whatsapp": "cancelled", "email": "scheduled"}
    assert outbox == []

    assert notices.reactivate_planned(db_session, payment_id="pay_1", step="fatura_disponivel", channel="whatsapp")
    preview = notices.upcoming(db_session, days=7, client=fake, today=TODAY)
    assert {c["state"] for c in preview["items"][0]["channels"]} == {"scheduled"}


# ---------------------------------------------------------------- textos e tela


def test_templates_keep_only_custom_text():
    cleaned = notices.clean_templates({
        "vence_hoje": {"whatsapp": "Oi {{nome}}", "email_subject": notices.DEFAULT_TEMPLATES["vence_hoje"]["email_subject"]},
        "inexistente": {"whatsapp": "x"},
    })
    assert cleaned == {"vence_hoje": {"whatsapp": "Oi {{nome}}"}}


def test_email_never_turns_user_text_into_html():
    subject, html_body, _text = notices.build_email(
        "vence_hoje",
        {"whatsapp": "", "email_subject": "Fatura <b>", "email_body": "Olá <script>x</script>\n\n*Valor:* {{valor}}"},
        dict(notices.SAMPLE_CONTEXT),
    )
    assert "<script>" not in html_body and "&lt;script&gt;" in html_body
    assert "<b>Valor:</b> R$ 97,00" in html_body


def test_admin_settings_endpoints(client, db_session, monkeypatch):
    app.dependency_overrides[get_current_superuser] = lambda: object()
    applied = []
    monkeypatch.setattr(notices, "apply_asaas_notifications_in_background", lambda enabled: applied.append(enabled))
    monkeypatch.setattr(notices, "asaas_client", lambda: FakeAsaas([]))
    try:
        data = client.get("/api/v1/admin/billing-notices/settings").json()
        assert data["enabled"] is False and data["asaas_notifications_enabled"] is True
        assert data["available_lead_days"] == 10 and len(data["steps"]) == 6

        saved = client.put("/api/v1/admin/billing-notices/settings", json={
            "enabled": True, "available_lead_days": 15,
            "steps": {"vence_hoje": {"whatsapp": False, "email": True}},
            "templates": {"vence_hoje": {"whatsapp": "Oi {{nome}}, vence hoje.", "email_subject": "", "email_body": ""}},
        }).json()
        assert saved["enabled"] is True and saved["available_lead_days"] == 15
        assert saved["channels"]["vence_hoje"] == {"whatsapp": False, "email": True}
        assert saved["templates"]["vence_hoje"]["whatsapp"] == "Oi {{nome}}, vence hoje."
        assert saved["custom_fields"]["vence_hoje"] == ["whatsapp"]

        off = client.post("/api/v1/admin/billing-notices/asaas-notifications", json={"enabled": False}).json()
        assert off["asaas_notifications_enabled"] is False and applied == [False]
        assert notices.asaas_notifications_disabled() is True
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)


def test_asaas_notifications_applied_to_every_customer(db_session):
    make_user(db_session, email="a@example.com")
    make_user(db_session, email="b@example.com")
    fake = FakeAsaas([])
    assert notices.apply_asaas_notifications(db_session, False, client=fake) == {"updated": 2, "failed": 0}
    assert all(payload == {"notificationDisabled": True} for _id, payload in fake.updated_customers)


def test_new_asaas_customers_follow_the_switch(db_session):
    from app.services.checkout import _build_asaas_customer_payload

    payload = _build_asaas_customer_payload(name="A", email="a@example.com", document="123", phone="47999990000", session_token="t")
    assert payload["notificationDisabled"] is False
    row = notices.get_settings_row(db_session)
    row.asaas_notifications_enabled = False
    db_session.commit()
    payload = _build_asaas_customer_payload(name="A", email="a@example.com", document="123", phone="47999990000", session_token="t")
    assert payload["notificationDisabled"] is True


# ---------------------------------------------------------------- sem envio retroativo


def test_turning_on_does_not_send_what_should_have_gone_out_before(db_session, outbox):
    """Ligar hoje: a "Fatura disponível" que deveria ter saído há dias não sai atrasada."""
    user = make_user(db_session)
    enable(db_session, schedule_since=TODAY)
    fake = FakeAsaas([
        payment(user, "pay_late", due=TODAY + timedelta(days=8)),          # deveria ter saído há 2 dias
        payment(user, "pay_today", due=TODAY + timedelta(days=10)),        # sai hoje: é o dia dela
        payment(user, "pay_overdue", due=TODAY - timedelta(days=5), status="OVERDUE"),  # atraso antigo
    ])
    notices.run_daily(db_session, today=TODAY, client=fake)
    sent = {(r.payment_id, r.step) for r in db_session.query(BillingNoticeSend).all()}
    assert sent == {("pay_today", "fatura_disponivel")}


def test_saving_settings_never_sends_and_resets_the_start_day(client, db_session, outbox, monkeypatch):
    app.dependency_overrides[get_current_superuser] = lambda: object()
    try:
        body = {"enabled": True, "available_lead_days": 10, "steps": {}, "templates": {}}
        client.put("/api/v1/admin/billing-notices/settings", json=body)
        row = notices.get_settings_row(db_session)
        db_session.refresh(row)
        assert row.schedule_since == notices.sao_paulo_today()

        # Mudar só o texto não mexe na data; mudar o prazo, sim.
        row.schedule_since = TODAY - timedelta(days=40)
        db_session.commit()
        client.put("/api/v1/admin/billing-notices/settings", json=body | {
            "templates": {"vence_hoje": {"whatsapp": "Oi", "email_subject": "", "email_body": ""}}
        })
        db_session.refresh(row)
        assert row.schedule_since == TODAY - timedelta(days=40)
        client.put("/api/v1/admin/billing-notices/settings", json=body | {"available_lead_days": 30})
        db_session.refresh(row)
        assert row.schedule_since == notices.sao_paulo_today()
        assert outbox == [] and db_session.query(BillingNoticeSend).count() == 0
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)


def test_no_payment_confirmation_for_payments_before_turning_on(db_session, outbox):
    user = make_user(db_session)
    enable(db_session, schedule_since=TODAY)
    paid = payment(user, due=TODAY, status="RECEIVED") | {"paymentDate": (TODAY - timedelta(days=1)).isoformat()}
    assert notices.payment_confirmed(db_session, paid, now=datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)) == {}
    assert outbox == []


# ---------------------------------------------------------------- WhatsApp próprio da cobrança


class FakeEvolution:
    def __init__(self, status="connected"):
        self.status = status
        self.created = []
        self.sent = []

    def create_instance(self, instance_name=None, *, with_webhook=True):
        self.created.append((instance_name, with_webhook))
        return {}

    def get_connection_status(self, instance_name=None):
        return {"status": self.status, "phone": "5547988887777"}

    def get_qr_code(self, instance_name=None):
        return {"qr_code_base64": "data:image/png;base64,AAA", "pairing_code": None}

    def send_text_target(self, target, text, instance_name=None):
        if self.status != "connected":
            raise RuntimeError("Connection Closed")
        self.sent.append((instance_name, target))

    def disconnect_instance(self, instance_name=None):
        self.status = "disconnected"
        return {}


def test_connect_creates_a_dedicated_instance_without_inbox_webhook(db_session, monkeypatch):
    fake = FakeEvolution(status="qr_needed")
    monkeypatch.setattr(notices, "_evolution", lambda: fake)
    result = notices.connect_sender(db_session)
    assert result["status"] == "qr_needed" and result["qr_code_base64"]
    assert fake.created == [("roteiroonline-cobranca", False)]
    # Ler de novo não cria outra instância.
    fake.status = "connected"
    assert notices.connect_sender(db_session)["status"] == "connected"
    assert len(fake.created) == 1
    row = notices.get_settings_row(db_session)
    assert row.sender_status == "connected" and row.sender_phone == "5547988887777"


def test_whatsapp_goes_out_through_the_billing_instance(db_session, monkeypatch):
    fake = FakeEvolution()
    monkeypatch.setattr(notices, "_evolution", lambda: fake)
    monkeypatch.setattr(notices, "send_email", lambda *a: None)
    user = make_user(db_session)
    enable(db_session)
    notices.run_daily(db_session, today=TODAY, client=FakeAsaas([payment(user, due=TODAY + timedelta(days=8))]))
    assert fake.sent == [("roteiroonline-cobranca", "5547999990000")]


def test_disconnected_sender_fails_alerts_once_and_does_not_send(db_session, monkeypatch):
    from app.services import webhook_notifications

    alerts = []
    monkeypatch.setattr(webhook_notifications, "notify_safely", lambda **kw: alerts.append(kw))
    fake = FakeEvolution(status="disconnected")
    monkeypatch.setattr(notices, "_evolution", lambda: fake)
    monkeypatch.setattr(notices, "send_email", lambda *a: None)
    user = make_user(db_session)
    enable(db_session)  # gravado como conectado; a Evolution diz que caiu
    notices.run_daily(db_session, today=TODAY, client=FakeAsaas([payment(user, due=TODAY + timedelta(days=8))]))
    row = db_session.query(BillingNoticeSend).filter_by(channel="whatsapp").one()
    assert row.status == "failed" and row.error == "Connection Closed"
    assert fake.sent == []
    settings_row = notices.get_settings_row(db_session)
    assert settings_row.sender_status == "disconnected"
    # Próximo envio nem tenta: falha na hora com o motivo claro.
    with pytest.raises(RuntimeError, match="desconectado"):
        notices.send_whatsapp(db_session, settings_row, "5547999990000", "oi")
    assert [a["event_key"] for a in alerts] == ["billing_whatsapp_disconnected"]
    # Continua caído: não avisa de novo.
    notices.refresh_sender(db_session, notices.get_settings_row(db_session))
    assert len(alerts) == 1


def test_preview_shows_when_billing_whatsapp_is_not_connected(db_session, outbox):
    user = make_user(db_session)
    enable(db_session, sender_status="disconnected")
    preview = notices.upcoming(db_session, days=7, client=FakeAsaas([payment(user, due=TODAY + timedelta(days=12))]), today=TODAY)
    states = {c["channel"]: (c["state"], c["reason"]) for c in preview["items"][0]["channels"]}
    assert states["whatsapp"] == ("skipped", "WhatsApp da cobrança desconectado")
    assert states["email"][0] == "scheduled"
