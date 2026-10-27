"""Plano trimestral: cobra a cada 3 meses no Asaas (cartão e Pix Automático), sem parcelas e sem a
promoção da 1ª mensalidade, e só entra na página de vendas quando marcado. Mensal e anual seguem
exatamente como antes."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.checkout import CheckoutSettings
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.checkout import CheckoutOfferIn, CheckoutSettingsUpdate
from app.services import checkout, revenue
from app.services.billing_account import covered_period, current_contract_offer
from app.services.billing_cycles import (
    asaas_cycle,
    cycle_duration,
    cycle_from_asaas,
    monthly_amount,
    next_due_date,
    pix_automatic_frequency,
)
from tests.conftest import TestingSessionLocal
from tests.test_checkout_installments import ANNUAL, MONTHLY, FakeAsaas, _card, _new_session, quiet  # noqa: F401

QUARTERLY = {
    "key": "roteiro-online-trimestral",
    "title": "Roteiro Online trimestral",
    "footer_product_label": "Roteiro Online",
    "plan_key": "scale",
    "billing_cycle": "quarterly",
    "amount": "297.00",
    "active": True,
    "checkout_key": "default",
}


def _old_next_due_date(base: date, cycle: str) -> date:
    """Como o próximo vencimento era calculado antes do trimestral (mensal e anual)."""
    if cycle == "annual":
        try:
            return base.replace(year=base.year + 1)
        except ValueError:
            return base.replace(year=base.year + 1, day=28)
    next_month = 1 if base.month == 12 else base.month + 1
    next_year = base.year + 1 if base.month == 12 else base.year
    month_after = 1 if next_month == 12 else next_month + 1
    year_after = next_year + 1 if next_month == 12 else next_year
    last_day = (date(year_after, month_after, 1) - timedelta(days=1)).day
    return date(next_year, next_month, min(base.day, last_day))


def _settings(db, *offers: dict) -> CheckoutSettings:
    record = CheckoutSettings(theme_mode="dark", is_active=True, offers_json=list(offers), coupons_json=[], checkouts_json=checkout.DEFAULT_CHECKOUTS, pixels_json=[])
    db.add(record)
    db.commit()
    return record


# ---------------------------------------------------------------- regras do ciclo


def test_monthly_and_annual_rules_did_not_change():
    day = date(2027, 1, 1)
    while day < date(2029, 1, 1):  # dois anos, com o 29/2 de 2028
        for cycle in ("monthly", "annual"):
            assert next_due_date(day, cycle) == _old_next_due_date(day, cycle)
        day += timedelta(days=1)
    assert cycle_duration("monthly") == timedelta(days=30) and cycle_duration("annual") == timedelta(days=365)
    assert cycle_duration(None) == timedelta(days=30) and cycle_duration("semanal") == timedelta(days=30)
    assert (asaas_cycle("monthly"), asaas_cycle("annual"), asaas_cycle("")) == ("MONTHLY", "YEARLY", "MONTHLY")
    assert (pix_automatic_frequency("monthly"), pix_automatic_frequency("annual")) == ("MONTHLY", "ANNUALLY")
    assert monthly_amount(Decimal("137.00"), "monthly") == Decimal("137.00")
    assert monthly_amount(Decimal("997.00"), "annual") == Decimal("997.00") / Decimal("12")


def test_quarterly_rules():
    assert next_due_date(date(2027, 1, 31), "quarterly") == date(2027, 4, 30)
    assert next_due_date(date(2027, 11, 30), "quarterly") == date(2028, 2, 29)
    assert next_due_date(date(2027, 8, 15), "quarterly") == date(2027, 11, 15)
    assert cycle_duration("quarterly") == timedelta(days=90)
    assert asaas_cycle("quarterly") == "QUARTERLY" and pix_automatic_frequency("quarterly") == "QUARTERLY"
    assert monthly_amount(Decimal("297.00"), "quarterly") == Decimal("99")
    assert cycle_from_asaas("QUARTERLY") == "quarterly" and cycle_from_asaas("YEARLY") == "annual"
    assert cycle_from_asaas("BIWEEKLY") is None
    assert covered_period(date(2027, 1, 10), "quarterly") == (date(2027, 1, 10), date(2027, 4, 10))


def test_quarterly_offer_has_no_installments_nor_promo():
    offer = CheckoutOfferIn.model_validate(
        {**QUARTERLY, "max_installments": 3, "installment_fixed_values": {"3": "99.00"}, "first_payment_amount": "50.00"}
    )
    assert offer.max_installments == 1 and offer.installment_fixed_values == {}
    assert offer.first_payment_amount is None and offer.first_payment_ends_at is None
    # Mensal e anual com as regras de sempre.
    assert CheckoutOfferIn.model_validate(ANNUAL).max_installments == 12
    assert CheckoutOfferIn.model_validate(MONTHLY).first_payment_amount == Decimal("67.00")


# ---------------------------------------------------------------- página de vendas


def test_creating_a_quarterly_offer_does_not_change_the_sales_page():
    db = TestingSessionLocal()
    record = _settings(db, MONTHLY, ANNUAL)
    before = checkout.get_public_sales_plan(db)
    record.offers_json = [MONTHLY, ANNUAL, QUARTERLY]
    db.commit()
    after = checkout.get_public_sales_plan(db)
    assert after["monthly"] == before["monthly"] and after["annual"] == before["annual"]
    assert after["annual"]["key"] == ANNUAL["key"]
    assert after["quarterly"] is None


def test_marked_quarterly_takes_the_place_of_the_unmarked_annual():
    db = TestingSessionLocal()
    _settings(db, MONTHLY, ANNUAL, {**QUARTERLY, "sales_slot": "quarterly"})
    plan = checkout.get_public_sales_plan(db)
    assert plan["monthly"]["key"] == MONTHLY["key"]
    assert plan["quarterly"]["key"] == QUARTERLY["key"] and plan["quarterly"]["billing_cycle"] == "quarterly"
    assert plan["quarterly"]["max_installments"] == 1 and plan["quarterly"]["first_payment_amount"] is None
    assert plan["annual"] is None


def test_marked_annual_stays_next_to_the_quarterly():
    db = TestingSessionLocal()
    _settings(db, MONTHLY, {**ANNUAL, "sales_slot": "annual"}, {**QUARTERLY, "sales_slot": "quarterly"})
    plan = checkout.get_public_sales_plan(db)
    assert [plan[slot]["key"] for slot in ("monthly", "quarterly", "annual")] == [MONTHLY["key"], QUARTERLY["key"], ANNUAL["key"]]


def test_quarterly_slot_must_be_a_quarterly_offer():
    db = TestingSessionLocal()
    payload = CheckoutSettingsUpdate.model_validate(
        {"is_active": True, "offers": [{**MONTHLY, "sales_slot": "quarterly"}], "checkouts": checkout.DEFAULT_CHECKOUTS}
    )
    with pytest.raises(HTTPException) as err:
        checkout.update_checkout_settings(db, payload)
    assert err.value.status_code == 400 and "Trimestral" in err.value.detail and "ciclo mensal" in err.value.detail


# ---------------------------------------------------------------- cobrança no Asaas


def test_quarterly_card_subscription_charges_every_three_months(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session = _new_session(db, QUARTERLY)
    assert checkout.serialize_checkout_session(db, session)["installment_options"][-1]["count"] == 1

    checkout.start_card_payment(db, session, _card())

    assert fake.subscriptions[0]["cycle"] == "QUARTERLY" and fake.subscriptions[0]["value"] == 297.0
    assert fake.updates == []  # sem promoção para ajustar depois
    subscription = db.query(User).filter(User.email == "cliente@example.com").one().subscription
    assert subscription.billing_cycle == "quarterly"
    assert subscription.mrr_amount == Decimal("99")
    valid_until = subscription.valid_until if subscription.valid_until.tzinfo else subscription.valid_until.replace(tzinfo=timezone.utc)
    assert abs(valid_until - (datetime.now(timezone.utc) + timedelta(days=90))) < timedelta(minutes=5)


def test_quarterly_pix_automatic_authorization(monkeypatch, quiet):
    db = TestingSessionLocal()
    fake = FakeAsaas()
    monkeypatch.setattr(checkout, "_ensure_asaas_client", lambda: fake)
    session = _new_session(db, QUARTERLY)
    checkout.start_pix_payment(db, session)
    assert fake.pix[0]["frequency"] == "QUARTERLY" and fake.pix[0]["value"] == 297.0


def test_quarterly_contract_renewal_and_revenue_use_the_whole_quarter():
    db = TestingSessionLocal()
    user = User(email="tri@example.com", name="Tri", hashed_password="x", plan="scale", is_active=True)
    db.add(user)
    db.flush()
    subscription = Subscription(user_id=user.id, provider="asaas", plan="scale", status="active", billing_cycle="quarterly", mrr_amount=Decimal("99.00"))
    db.add(subscription)
    db.flush()
    user.subscription_id = subscription.id
    db.commit()
    contract = current_contract_offer(db, user)
    assert contract.billing_cycle == "quarterly" and contract.amount == Decimal("297.00")
    assert revenue.charge_amount(subscription) == Decimal("297.00")
