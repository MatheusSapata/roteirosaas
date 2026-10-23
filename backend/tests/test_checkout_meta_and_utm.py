"""Pixel da Meta e origem (UTMs) do checkout próprio.

Os eventos padrão saem uma vez por compra, com o mesmo event_id do navegador
("<token>|<evento>"), para o Meta juntar Pixel e API de Conversões. As UTMs guardadas desde a LP
chegam à sessão, ao Hub e ao cadastro do dono da empresa; o resto do que o navegador manda não entra
nos metadados da sessão."""
from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from app.models.checkout import CheckoutSession, CheckoutSettings
from app.models.user_tracking import UserTracking
from app.schemas.checkout import CheckoutOfferOut
from app.services import checkout

MONTHLY = {
    "key": "roteiro-online-mensal",
    "title": "Roteiro Online mensal",
    "footer_product_label": "Roteiro Online",
    "plan_key": "scale",
    "billing_cycle": "monthly",
    "amount": "137.00",
    "active": True,
    "checkout_key": "default",
    "first_payment_amount": "67.00",
}
NO_PROMO = {**MONTHLY, "key": "roteiro-online-sem-promo", "first_payment_amount": None}
PIXEL = {"name": "Vendas", "pixel_id": "111", "access_token": "tok-capi", "active": True, "offer_keys": [MONTHLY["key"], NO_PROMO["key"]]}
UTM = {"utm_source": "facebook", "utm_medium": "cpc", "utm_campaign": "lancamento", "utm_content": "video-1", "referrer": "https://l.facebook.com/"}
BUYER = {
    "customer_name": "Ana Paula Souza",
    "customer_email": "ana@example.com",
    "customer_document": "12345678901",
    "customer_phone": "(47) 99999-9999",
    "customer_zipcode": "89000-000",
}


@pytest.fixture
def meta(monkeypatch, db_session):
    db_session.add(
        CheckoutSettings(
            theme_mode="dark", is_active=True, offers_json=[MONTHLY, NO_PROMO], coupons_json=[],
            checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[PIXEL],
        )
    )
    db_session.commit()
    sent: list[dict] = []
    hub: list[dict] = []

    def fake_post(url, params=None, json=None, timeout=None):
        sent.append({"url": url, "access_token": params["access_token"], **json["data"][0]})
        return SimpleNamespace(status_code=200, text="{}")

    monkeypatch.setattr(checkout, "META_CAPI_IN_BACKGROUND", False)
    monkeypatch.setattr(checkout.httpx, "post", fake_post)
    monkeypatch.setattr(checkout, "ensure_checkout_contact_at_payment_step", lambda **_kwargs: None)
    monkeypatch.setattr(checkout, "send_hub_event", lambda event, **kwargs: hub.append({"event": event, **kwargs}))
    return SimpleNamespace(sent=sent, hub=hub)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _create(client, offer: dict, **extra) -> dict:
    response = client.post("/api/v1/checkout/public/session", json={"offer_key": offer["key"], **BUYER, **extra})
    assert response.status_code == 201, response.text
    return response.json()


def _track(client, token: str, event_name: str, **extra) -> None:
    response = client.post(f"/api/v1/checkout/public/session/{token}/track", json={"event_name": event_name, **extra})
    assert response.status_code == 200, response.text


def test_browser_metadata_is_ignored_and_utms_reach_session_and_hub(client, db_session, meta):
    # Alguém tentando mexer no valor da 1ª cobrança e na assinatura de outro cliente pelo checkout público.
    body = _create(
        client,
        NO_PROMO,
        metadata={"first_payment_amount": "1.00", "upgrade_mode": True, "target_user_id": 99, "replaced_asaas_subscription_id": "sub_x"},
        utm=UTM,
    )
    session = db_session.query(CheckoutSession).filter_by(token=body["token"]).one()
    metadata = session.metadata_json
    for key in ("first_payment_amount", "upgrade_mode", "target_user_id", "replaced_asaas_subscription_id"):
        assert key not in metadata
    assert checkout.session_first_payment_amount(session) is None and body["first_payment_amount"] is None
    assert metadata["utm"] == UTM
    started = next(item for item in meta.hub if item["event"] == "checkout_started")
    assert started["utm"]["utm_source"] == "facebook" and started["utm"]["utm_campaign"] == "lancamento"


def test_each_standard_event_goes_once_with_the_browser_event_id(client, db_session, meta):
    token = _create(client, MONTHLY, utm=UTM)["token"]
    browser = {"fbp": "fb.1.1700000000000.123", "fbc": "fb.1.1700000000000.AbCd", "page_url": "https://app.roteiroonline.com/checkout/roteiro-online-mensal"}
    _track(client, token, "details_submit_success", step="details", metadata=browser)
    _track(client, token, "step_method_view", step="method")
    _track(client, token, "step_method_view", step="method")  # recarregou a página
    _track(client, token, "payment_method_click", step="method", payment_method="pix")
    _track(client, token, "pix_started", step="pix", payment_method="pix")
    # Passos depois do pagamento chegam com status "paid" e não são outra compra.
    _track(client, token, "password_step_view", step="password", status="paid")
    _track(client, token, "signup_redirect_started", step="success", status="paid")
    _track(client, token, "payment_success", step="success", status="paid", payment_method="pix")
    _track(client, token, "payment_success", step="success", status="paid", payment_method="pix")

    assert [event["event_name"] for event in meta.sent] == ["Lead", "InitiateCheckout", "AddPaymentInfo", "Purchase"]
    by_name = {event["event_name"]: event for event in meta.sent}
    assert by_name["InitiateCheckout"]["event_id"] == f"{token}|initiatecheckout"
    assert by_name["Purchase"]["event_id"] == f"{token}|purchase"
    purchase = by_name["Purchase"]
    assert purchase["url"].endswith("/111/events") and purchase["access_token"] == "tok-capi"
    assert purchase["event_source_url"] == browser["page_url"]
    assert purchase["custom_data"]["value"] == 67.0  # a 1ª mensalidade promocional, a cobrança de agora
    assert purchase["custom_data"]["order_id"] == token and purchase["custom_data"]["currency"] == "BRL"
    user = purchase["user_data"]
    assert user["fbp"] == browser["fbp"] and user["fbc"] == browser["fbc"]
    assert user["ph"] == [_sha("5547999999999")] and user["em"] == [_sha("ana@example.com")]
    assert user["fn"] == [_sha("ana")] and user["ln"] == [_sha("souza")]

    # O webhook do Asaas confirmando o mesmo pagamento depois não manda outro Purchase.
    session = db_session.query(CheckoutSession).filter_by(token=token).one()
    checkout._dispatch_meta_checkout_events(
        db_session, session=session, event_name="payment_success", step="success", status="paid",
        payment_method="pix", metadata={}, ip_address_value=None, user_agent=None,
    )
    assert [event["event_name"] for event in meta.sent].count("Purchase") == 1


def test_purchase_from_webhook_uses_what_the_browser_left(client, db_session, meta):
    token = _create(client, MONTHLY)["token"]
    _track(client, token, "details_submit_success", step="details", metadata={"fbp": "fb.1.1.999", "page_url": "https://app.roteiroonline.com/checkout/x"})
    session = db_session.query(CheckoutSession).filter_by(token=token).one()
    db_session.refresh(session)
    # Pix pago com a página fechada: o webhook não tem o navegador, mas a sessão guardou.
    checkout._dispatch_meta_checkout_events(
        db_session, session=session, event_name="payment_success", step="success", status="paid",
        payment_method="pix", metadata={}, ip_address_value=None, user_agent=None,
    )
    purchase = meta.sent[-1]
    assert purchase["event_name"] == "Purchase" and purchase["user_data"]["fbp"] == "fb.1.1.999"
    assert purchase["user_data"].get("client_user_agent")  # o do navegador que mandou os passos


def test_account_created_by_the_purchase_keeps_the_origin(db_session, meta):
    session = checkout.create_checkout_session(
        db_session,
        offer=CheckoutOfferOut.model_validate(MONTHLY),
        customer_name="Bia",
        customer_email="bia@example.com",
        customer_document="98765432100",
        customer_phone="47988887777",
        customer_zipcode="89000000",
        coupon_code=None,
        metadata={"utm": UTM},
    )
    user = checkout._upsert_paid_user_and_subscription(db_session, session)
    db_session.commit()
    tracking = db_session.query(UserTracking).filter_by(user_id=user.id).all()
    assert [(row.utm_source, row.utm_campaign, row.utm_content, row.referrer) for row in tracking] == [
        ("facebook", "lancamento", "video-1", "https://l.facebook.com/")
    ]
    # Definir a senha depois (passa de novo pela conta) não duplica a origem.
    checkout._upsert_paid_user_and_subscription(db_session, session)
    db_session.commit()
    assert db_session.query(UserTracking).filter_by(user_id=user.id).count() == 1


def test_seller_code_reaches_session_hub_and_paid_event(client, db_session, meta, monkeypatch):
    """Link da vendedora (?vendedor=): o código vai na origem da compra, no checkout_started e no
    subscription_paid, mesmo quando o pagamento chega sem a sessão (Cakto, Asaas)."""
    from app.services import subscription_notifications as notes

    body = _create(client, NO_PROMO, utm={**UTM, "seller_code": "02"})
    bad = _create(client, NO_PROMO, utm={**UTM, "seller_code": "não vale!"})
    session = db_session.query(CheckoutSession).filter_by(token=body["token"]).one()
    assert session.metadata_json["utm"]["seller_code"] == "02"
    assert "seller_code" not in db_session.query(CheckoutSession).filter_by(token=bad["token"]).one().metadata_json["utm"]
    started = next(item for item in meta.hub if item["event"] == "checkout_started" and item["payload"]["checkout_session_id"] == body["token"])
    assert started["payload"]["seller_code"] == "02" and "seller_code" not in started["utm"]

    session.status = "paid"
    db_session.commit()
    paid: list[dict] = []
    monkeypatch.setattr(notes, "send_hub_event", lambda event, **kwargs: paid.append({"event": event, **kwargs}))
    monkeypatch.setattr(notes, "notify_safely", lambda **_kwargs: None)
    notes.publish_subscription_notification(
        scenario=notes.SubscriptionPushScenario.NEW, user_name="Ana", payment_method="pix", amount=137,
        plan_name="Roteiro Online", customer_email="ANA@example.com",
    )
    assert paid[-1]["event"] == "subscription_paid"
    assert paid[-1]["payload"]["seller_code"] == "02" and paid[-1]["payload"]["checkout_session_id"] == body["token"]

    notes.publish_subscription_notification(
        scenario=notes.SubscriptionPushScenario.CANCELLED, user_name="Ana", payment_method=None, amount=None,
        cancelled_item="Assinatura cancelada", customer_email="ana@example.com",
    )
    assert paid[-1]["event"] == "subscription_cancelled"
    assert paid[-1]["payload"] == {"checkout_session_id": body["token"], "reason": "Assinatura cancelada"}

    # Renovação não vira venda nova no Hub.
    notes.publish_subscription_notification(
        scenario=notes.SubscriptionPushScenario.RENEWED, user_name="Ana", payment_method="pix", amount=137,
        customer_email="ana@example.com",
    )
    assert paid[-1]["event"] == "subscription_cancelled"
