from datetime import date
from time import monotonic
from unittest.mock import Mock

import pytest

from app.services.asaas import AsaasAPIError, AsaasClient
from app.services.billing_reconciliation import collect_pages, fetch_remote, reconcile

TODAY = date(2026, 9, 25)


def source(data=(), complete=True):
    return {"data": list(data), "complete": complete, "error": None if complete else "Failed"}


def snapshot(payments=(), subscriptions=(), authorizations=(), instructions=()):
    return {"payments": source(payments), "subscriptions": source(subscriptions),
            "authorizations": source(authorizations), "instructions": source(instructions)}


def payment(id="pay_1", **overrides):
    return {"id": id, "subscription": "sub_1", "customer": "cus_1", "status": "OVERDUE",
            "billingType": "PIX", "dueDate": "2026-09-20", "value": 99.90, "netValue": 98.0, **overrides}


def local(**overrides):
    return {"id": 1, "user_id": 2, "name": "Cliente Teste", "email": "test@example.com", "plan": "growth",
            "provider": "asaas", "status": "active", "method": "pix", "valid_until": "2026-09-19",
            "asaas_subscription_id": "sub_1", "asaas_customer_id": "cus_1", **overrides}


def report(remote, locals=(), sessions=(), start=None, end=TODAY):
    return reconcile(remote, list(locals), list(sessions), today=TODAY, start=start, end=end)


@pytest.mark.parametrize("status,classification", [
    ("OVERDUE", "overdue"), ("PENDING", "overdue"), ("CREDIT_CARD_CAPTURE_REFUSED", "overdue"),
    ("RECEIVED", "paid"), ("CONFIRMED", "paid"), ("RECEIVED_IN_CASH", "paid"),
    ("REFUNDED", "other"), ("CHARGEBACK_REQUESTED", "other"), ("AWAITING_RISK_ANALYSIS", "other"),
])
def test_financial_statuses_are_not_inferred_from_subscription(status, classification):
    rows = report(snapshot([payment(status=status)]))["rows"]
    assert rows[0]["classification"] == classification
    assert rows[0]["days_overdue"] == (5 if classification == "overdue" else 0)


def test_due_today_future_deleted_and_outside_period_are_not_overdue():
    data = [payment("today", dueDate="2026-09-25"), payment("future", dueDate="2026-09-26"),
            payment("deleted", deleted=True), payment("old", dueDate="2026-08-01")]
    result = report(snapshot(data), start=date(2026, 9, 1))
    assert len(result["rows"]) == 1
    assert result["rows"][0]["classification"] == "other"


def test_all_installments_remain_separate_and_one_local_subscription_is_linked():
    result = report(snapshot([payment(), payment("pay_2", dueDate="2026-08-20")]), [local()])
    assert len(result["rows"]) == 2
    assert {r["local_subscription_id"] for r in result["rows"]} == {1}
    assert {r["subscription_key"] for r in result["rows"]} == {"sub_1"}


def test_pix_authorized_is_not_the_same_as_automatic_payment_generation():
    data = snapshot([payment(pixAutomaticAuthorizationId="auth_1")], authorizations=[
        {"id": "auth_1", "status": "ACTIVE", "paymentCreationMode": "MANUAL"}])
    row = report(data)["rows"][0]
    assert row["pix_kind"] == "automatic"
    assert row["authorization_status"] == "ACTIVE"
    assert row["creation_mode"] == "MANUAL"
    assert row["classification"] == "overdue"


def test_pix_instruction_done_does_not_mark_payment_paid():
    data = snapshot([payment()], authorizations=[{"id": "a", "status": "ACTIVE", "paymentCreationMode": "SUBSCRIPTION"}],
                    instructions=[{"id": "i", "paymentId": "pay_1", "authorization": {"id": "a"}, "status": "DONE"}])
    row = report(data)["rows"][0]
    assert row["classification"] == "overdue"
    assert row["creation_mode"] == "SUBSCRIPTION"
    assert row["pix_kind"] == "automatic"


def test_local_authorization_never_proves_remote_payment_linkage():
    checkout = {"token": "token", "user_id": 2, "name": "Test", "email": "t@example.com", "plan": "growth",
                "asaas_payment_id": "pay_1", "metadata": {"asaas_pix_automatic_authorization_id": "a", "asaas_pix_automatic_authorization_status": "ACTIVE"}}
    row = report(snapshot([payment()], authorizations=[{"id": "a", "status": "CANCELLED"}]), sessions=[checkout])["rows"][0]
    assert row["pix_kind"] == "unverified"
    assert row["authorization_status"] == "CANCELLED"
    assert "Autorização diverge do cadastro local" in row["findings"]


def test_missing_pix_read_permission_is_unknown_not_missing():
    data = snapshot([payment()])
    data["authorizations"] = source(complete=False)
    result = report(data)
    assert not result["complete"]
    assert result["rows"][0]["authorization_status"] == "UNKNOWN"
    assert result["rows"][0]["pix_kind"] == "unknown"


def test_other_gateway_and_missing_charge_are_review_items_without_estimated_debt():
    result = report(snapshot(), [local(), local(id=3, user_id=4, provider="cakto", asaas_subscription_id=None)])
    assert len(result["rows"]) == 2
    assert {r["gateway"] for r in result["rows"]} == {"asaas", "cakto"}
    assert all(r["classification"] == "review" and r["amount"] is None for r in result["rows"])


def test_cancelled_contract_does_not_generate_renewal_expectation_but_keeps_existing_debt():
    assert report(snapshot(), [local(status="cancelled")])["rows"] == []
    assert report(snapshot(), [local(status="cancel_at_period_end")])["rows"] == []
    assert report(snapshot([payment()]), [local(status="cancelled")])["rows"][0]["classification"] == "overdue"


def test_paid_renewal_prevents_false_missing_charge():
    result = report(snapshot([payment(status="RECEIVED")]), [local()])
    assert [r["classification"] for r in result["rows"]] == ["paid"]


def test_remote_only_subscription_is_reported_and_unrelated_payment_is_separate():
    data = snapshot([payment(subscription=None)], subscriptions=[{"id": "remote", "status": "ACTIVE", "customer": "cus_2", "nextDueDate": "2026-09-10"}])
    result = report(data)
    assert {r["scope"] for r in result["rows"]} == {"unmatched", "subscription"}
    assert any(r["id"] == "remote:remote" and r["amount"] is None for r in result["rows"])


def test_pagination_collects_all_results_deduplicates_and_preserves_partial_errors():
    fetch = Mock(side_effect=[{"data": [{"id": "a"}], "hasMore": True}, {"data": [{"id": "b"}], "hasMore": False}])
    result = collect_pages(fetch, {"status": "OVERDUE"}, monotonic() + 10)
    assert result["complete"] and len(result["data"]) == 2
    assert fetch.call_args_list[1].kwargs["offset"] == 1
    fetch = Mock(side_effect=[{"data": [{"id": "a"}], "hasMore": True}, AsaasAPIError("secret server response")])
    result = collect_pages(fetch, {}, monotonic() + 10)
    assert not result["complete"] and len(result["data"]) == 1
    assert "secret" not in result["error"]


def test_repeated_page_and_deadline_never_claim_complete():
    fetch = Mock(return_value={"data": [{"id": "a"}], "hasMore": True})
    assert not collect_pages(fetch, {}, monotonic() + 10)["complete"]
    assert fetch.call_count == 2
    assert not collect_pages(fetch, {}, monotonic() - 1)["complete"]


def test_reconciliation_client_only_uses_read_requests():
    client = AsaasClient("test", "https://api-sandbox.asaas.com/v3")
    client._request = Mock(return_value={"data": [], "hasMore": False})
    fetch_remote(client, date(2026, 9, 1), TODAY)
    assert client._request.call_count == 4
    assert all(call.args[0] == "GET" for call in client._request.call_args_list)
    payment_call = next(c for c in client._request.call_args_list if c.args[1] == "/payments")
    assert payment_call.kwargs["params"]["dueDate[ge]"] == "2026-09-01"


def test_customer_authorization_alone_does_not_prove_automatic_charge():
    data = snapshot([payment()], authorizations=[{"id": "a", "customerId": "cus_1", "status": "ACTIVE"}])
    row = report(data)["rows"][0]
    assert row["authorization_status"] == "UNKNOWN"
    assert row["pix_kind"] == "unverified"
    assert row["customer_authorizations"][0]["status"] == "ACTIVE"


def test_other_gateway_pix_is_not_claimed_to_have_missing_asaas_authorization():
    row = report(snapshot(), [local(provider="cakto", asaas_subscription_id=None)])["rows"][0]
    assert row["authorization_status"] == "UNKNOWN"
    assert row["pix_kind"] == "unknown"


def test_latest_unpaid_checkout_does_not_replace_current_paid_mandate():
    sessions = [{"token": token, "user_id": 2, "status": status, "asaas_payment_id": None,
                 "metadata": {"asaas_pix_automatic_authorization_id": aid}}
                for token, status, aid in [("abandoned", "pending", "wrong"), ("current", "paid", "right")]]
    row = report(snapshot([payment()], authorizations=[{"id": "right", "status": "ACTIVE"}]), [local()], sessions)["rows"][0]
    assert row["authorization_id"] == "right"
    assert row["authorization_status"] == "ACTIVE"
    assert row["pix_kind"] == "unverified"


def test_invalid_access_token_exposes_actionable_message_without_response_body():
    fetch = Mock(side_effect=AsaasAPIError({"errors": [{"code": "invalid_access_token", "description": "sensitive data"}]}))
    result = collect_pages(fetch, {}, monotonic() + 5)
    assert "ASAAS_API_KEY" in result["error"]
    assert "sensitive" not in result["error"]


def test_local_inventory_uses_real_models_in_an_isolated_database():
    from sqlalchemy import create_engine
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.orm import Session
    from app.db.base import Base
    from app.models.user import User
    from app.models.subscription import Subscription
    from app.services.billing_reconciliation import load_local

    @compiles(JSONB, "sqlite")
    def compile_jsonb(_type, _compiler, **_kwargs):
        return "JSON"

    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            user = User(name="Test", email="reconciliation@example.com", hashed_password="test-only")
            db.add(user)
            db.flush()
            db.add(Subscription(user_id=user.id, plan="growth", provider="asaas", payment_method_type="card"))
            db.commit()
            locals, sessions = load_local(db)
            assert len(locals) == 1 and locals[0]["method"] == "card"
            assert sessions == []
    finally:
        engine.dispose()
