from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.asaas import AsaasEventLog
from app.models.cakto import CaktoEventLog
from app.models.subscription import Subscription
from app.models.user import User
from app.services import revenue
from app.services.asaas import AsaasClient

NOW = datetime(2026, 10, 12, 15, tzinfo=timezone.utc)


def _sub(db, email, *, mrr, status="active", cycle="monthly", valid_until=None, failed=0, plan="pro", method="card"):
    user = User(name=email.split("@")[0].title(), email=email, hashed_password="x", is_active=True, plan=plan)
    db.add(user)
    db.flush()
    db.add(Subscription(user_id=user.id, plan=plan, provider="asaas", status=status, billing_cycle=cycle,
                        mrr_amount=Decimal(str(mrr)), valid_until=valid_until, failed_attempts=failed,
                        payment_method_type=method))


def _asaas(db, event_id, event, payment):
    # Cobranças do Roteiro Online levam a referência do checkout (ou "usuário:plano:ciclo").
    payment = {"externalReference": "checkout:tok", **payment}
    db.add(AsaasEventLog(event_id=event_id, event_type=event, payload={"event": event, "payment": payment}, status="processed"))


@pytest.fixture
def data(db_session):
    db = db_session
    _sub(db, "mensal@x.com", mrr=199, valid_until=datetime(2026, 10, 20, tzinfo=timezone.utc))
    _sub(db, "anual@x.com", mrr="83.25", cycle="annual", valid_until=datetime(2026, 11, 20, tzinfo=timezone.utc))
    _sub(db, "saindo@x.com", mrr=99, status="cancel_at_period_end", valid_until=datetime(2026, 10, 25, tzinfo=timezone.utc))
    _sub(db, "atrasado@x.com", mrr=149, failed=1, valid_until=datetime(2026, 10, 5, tzinfo=timezone.utc), method="boleto")
    _sub(db, "interno@x.com", mrr=500, plan="teste", valid_until=datetime(2026, 10, 15, tzinfo=timezone.utc))
    _sub(db, "cancelado@x.com", mrr=79, status="cancelled", valid_until=datetime(2026, 10, 18, tzinfo=timezone.utc))
    # Cartão: confirmado em outubro e recebido em novembro = 1 pagamento, em outubro.
    _asaas(db, "e1", "PAYMENT_CONFIRMED", {"id": "pay_1", "value": 199, "netValue": 190.5, "billingType": "CREDIT_CARD", "confirmedDate": "2026-10-03"})
    _asaas(db, "e2", "PAYMENT_RECEIVED", {"id": "pay_1", "value": 199, "netValue": 190.5, "billingType": "CREDIT_CARD", "paymentDate": "2026-11-02"})
    _asaas(db, "e3", "PAYMENT_RECEIVED", {"id": "pay_2", "value": 99, "netValue": 97, "billingType": "PIX", "paymentDate": "2026-09-28"})
    _asaas(db, "e4", "PAYMENT_REFUNDED", {"id": "pay_3", "value": 50, "netValue": 48, "billingType": "PIX", "refundedDate": "2026-10-07"})
    _asaas(db, "e5", "PAYMENT_OVERDUE", {"id": "pay_4", "value": 149, "billingType": "BOLETO", "dueDate": "2026-10-05"})
    # Pagamento de outro produto na mesma conta da Asaas (ex.: combo vendido pela Viaje On): fora da receita.
    _asaas(db, "e6", "PAYMENT_CONFIRMED", {"id": "pay_9", "value": 1997, "externalReference": "viajeon:pedido-9", "confirmedDate": "2026-10-04"})
    db.add(CaktoEventLog(event_id="c1", event_type="subscription_renewed", status="processed",
                         payload={"data": {"order": {"amount": 297}, "customer": {"email": "cakto@x.com"}}},
                         processed_at=datetime(2026, 10, 9, tzinfo=timezone.utc)))
    db.commit()
    return db


def test_mrr_month_and_renewals(data):
    result = revenue.revenue_overview(data, None, 60, now=NOW)
    # MRR: mensal 199 + anual 83,25 + atrasado 149 (ainda ativo); fora: cancelando, teste, cancelado.
    assert result["mrr"] == 431.25 and result["arr"] == 5175.0 and result["paying_customers"] == 3
    assert result["mrr_at_risk"] == 248.0  # cancelando (99) + com falha (149)
    assert result["mrr_by_cycle"] == {"Mensal": 348.0, "Anual": 83.25}
    # Recebido em outubro: 199 (Asaas, contado 1 vez) + 297 (Cakto); estorno de 50.
    assert result["month_received_gross"] == 496.0 and result["month_payments"] == 2 and result["month_refunded"] == 50.0
    assert result["month_other_received"] == 1997.0 and result["month_other_payments"] == 1
    # A receber até o fim do mês: só a renovação do mensal no dia 20 (o anual é em novembro).
    assert result["month_to_receive"] == 199.0 and result["month_to_receive_count"] == 1
    assert result["month_expected"] == 645.0
    assert result["overdue"] == 149.0 and result["overdue_items"][0]["alerts"] == ["1 falha(s) de cobrança", "Depende do cliente pagar"]
    # Próximas renovações: o anual aparece pelo valor cheio da cobrança (12 x 83,25).
    upcoming = {item["email"]: item for item in result["upcoming"]}
    assert set(upcoming) == {"mensal@x.com", "anual@x.com"}
    assert upcoming["anual@x.com"]["amount"] == 999.0 and upcoming["anual@x.com"]["cycle"] == "Anual"


def test_viajeon_combo_is_not_revenue(data):
    # Combo da Viaje On com o valor anual gravado como se fosse mensal: não entra no MRR.
    user = User(name="Combo", email="combo@x.com", hashed_password="x", is_active=True, plan="growth")
    data.add(user)
    data.flush()
    data.add(Subscription(user_id=user.id, plan="growth", provider="viajeon", status="active", billing_cycle="annual",
                          mrr_amount=Decimal("1997"), valid_until=datetime(2026, 10, 30, tzinfo=timezone.utc)))
    data.commit()
    result = revenue.revenue_overview(data, None, 60, now=NOW)
    assert result["mrr"] == 431.25 and result["paying_customers"] == 3
    assert "combo@x.com" not in {item["email"] for item in result["upcoming"]}


def test_past_month_has_no_to_receive(data):
    result = revenue.revenue_overview(data, date(2026, 9, 1), 60, now=NOW)
    assert result["month_received_gross"] == 99.0 and result["month_to_receive"] is None


def test_revenue_never_writes_to_payment_providers(data, monkeypatch, client):
    """Garantia: o painel de receita só consulta. Qualquer escrita na Asaas é bloqueada."""
    calls = []

    def fake_request(self, method, path, **kwargs):
        calls.append((method, path))
        return {"data": [{"value": 199}], "hasMore": False}

    monkeypatch.setattr(AsaasClient, "_request", fake_request)
    totals = revenue.asaas_open_charges("k", "https://x", date(2026, 10, 31))
    assert totals == {"pending": {"count": 1, "amount": 199.0}, "overdue": {"count": 1, "amount": 199.0}}
    assert {method for method, _ in calls} == {"GET"}

    reader = revenue.ReadOnlyAsaas("k", "https://x")
    for attempt in (
        lambda: reader.create_payment({"value": 1}),
        lambda: reader.create_subscription({"value": 1}),
        lambda: reader.update_subscription("sub_1", {"value": 1}),
        lambda: reader.cancel_subscription("sub_1"),
        lambda: reader.create_pix_automatic_payment_instruction({"value": 1}),
    ):
        with pytest.raises(PermissionError):
            attempt()

    # E as rotas do painel não chamam a Asaas fora a consulta explícita.
    from app.api.deps import get_current_superuser
    from app.main import app

    calls.clear()
    app.dependency_overrides[get_current_superuser] = lambda: SimpleNamespace(is_superuser=True)
    try:
        response = client.get("/api/v1/admin/master/revenue")
        assert response.status_code == 200 and calls == []
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)
