from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.agency_user import AgencyUser
from app.models.page import Page
from app.models.sale import (
    Sale,
    SaleFinancialStatus,
    SalePassenger,
    SalePassengerStatus,
    SalePaymentStatus,
    SalePayoutStatus,
)
from app.models.stripe_account import StripeAccount
from app.models.user import User
from app.schemas.finance import PassengerInput, SalePassengerOut, SaleSummary
from app.services.stripe_connect import (
    create_account_link,
    create_express_account,
    create_payment_intent,
    iter_payout_transactions,
    retrieve_account,
    retrieve_balance_transaction,
)


def calculate_platform_fee(amount_in_cents: int) -> int:
    """
    Calcula a comiss\u00e3o fixa de 1.5% sobre o valor final da transa\u00e7\u00e3o.
    """
    if amount_in_cents <= 0:
        return 0
    fee = Decimal(amount_in_cents) * Decimal("0.015")
    rounded = int(fee.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(rounded, 1)


def _localized_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("pt", "es", "en"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return text
        for _, text in value.items():
            if isinstance(text, str) and text.strip():
                return text
    return str(value)


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value)
    raise HTTPException(status_code=400, detail="Valor de preço inválido.")


def _to_cents(value: Decimal) -> int:
    cents = (value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def _find_price_item(config: dict[str, Any], product_id: str, section_hint: str | None = None) -> CheckoutPriceResolution:
    sections = config.get("sections") or []
    for idx, raw_section in enumerate(sections):
        if not isinstance(raw_section, dict) or raw_section.get("type") != "prices":
            continue
        section_id = (
            raw_section.get("id")
            or raw_section.get("section_id")
            or raw_section.get("sectionId")
            or raw_section.get("anchorId")
            or f"prices-{idx}"
        )
        if section_hint and section_hint != section_id:
            continue
        for item_idx, raw_item in enumerate(raw_section.get("items") or []):
            if not isinstance(raw_item, dict):
                continue
            checkout_config = raw_item.get("checkout") or {}
            candidate_product_id = checkout_config.get("productId") or raw_item.get("productId")
            if candidate_product_id == product_id:
                price_value = _to_decimal(raw_item.get("price"))
                passengers_required = checkout_config.get("passengersRequired") or checkout_config.get("passengers_required") or 0
                installments = checkout_config.get("installments") or 1
                interest_mode = checkout_config.get("interestMode") or checkout_config.get("interest_mode") or "merchant"
                max_no_interest = checkout_config.get("maxInstallmentsNoInterest") or checkout_config.get(
                    "max_installments_no_interest"
                )
                currency = (raw_item.get("currency") or "BRL").upper()
                return CheckoutPriceResolution(
                    section_id=str(section_id),
                    section_index=idx,
                    item_index=item_idx,
                    product_id=product_id,
                    title=_localized_value(raw_item.get("title")),
                    description=_localized_value(raw_item.get("description")),
                    price_decimal=price_value,
                    currency=currency,
                    passengers_required=int(passengers_required or 0),
                    installments=int(installments or 1),
                    interest_mode=str(interest_mode or "merchant"),
                    max_installments_no_interest=int(max_no_interest) if max_no_interest else None,
                    raw_section=raw_section,
                    raw_item=raw_item,
                    checkout_config=checkout_config,
                )
    raise HTTPException(status_code=404, detail="Produto não encontrado no configurador da página.")


def _trim(value: str | None, length: int) -> str | None:
    if value is None:
        return None
    return value[:length]


def _pick_agency_owner(db: Session, agency_id: int) -> User:
    membership = (
        db.query(AgencyUser)
        .options(joinedload(AgencyUser.user))
        .filter(AgencyUser.agency_id == agency_id)
        .order_by(AgencyUser.role.desc())
        .all()
    )
    for rel in membership:
        if rel.role == "owner" and rel.user:
            return rel.user
    for rel in membership:
        if rel.user:
            return rel.user
    raise HTTPException(status_code=400, detail="Agência sem usuário responsável.")


def ensure_stripe_account_record(user: User, db: Session) -> StripeAccount:
    record = db.query(StripeAccount).filter(StripeAccount.user_id == user.id).first()
    if record and user.stripe_account_id:
        return record
    account = create_express_account(user.email)
    record = record or StripeAccount(user_id=user.id, stripe_account_id=account.id)
    record.stripe_account_id = account.id
    record.email = account.get("email")
    record.country = account.get("country")
    record.default_currency = account.get("default_currency")
    record.charges_enabled = bool(account.get("charges_enabled"))
    record.payouts_enabled = bool(account.get("payouts_enabled"))
    record.details_submitted = bool(account.get("details_submitted"))
    record.onboarding_completed = record.details_submitted
    record.requirements = account.get("requirements")
    user.stripe_account_id = account.id
    user.stripe_charges_enabled = record.charges_enabled
    user.stripe_payouts_enabled = record.payouts_enabled
    user.stripe_onboarding_completed = record.onboarding_completed
    db.add(record)
    db.add(user)
    db.commit()
    db.refresh(record)
    return record


def sync_account_status(user: User, account_data: dict[str, Any], db: Session) -> StripeAccount:
    record = db.query(StripeAccount).filter(StripeAccount.user_id == user.id).first()
    if not record:
        record = StripeAccount(user_id=user.id, stripe_account_id=account_data["id"])
    record.stripe_account_id = account_data["id"]
    record.email = account_data.get("email")
    record.country = account_data.get("country")
    record.default_currency = account_data.get("default_currency")
    record.charges_enabled = bool(account_data.get("charges_enabled"))
    record.payouts_enabled = bool(account_data.get("payouts_enabled"))
    record.details_submitted = bool(account_data.get("details_submitted"))
    record.onboarding_completed = record.details_submitted
    record.requirements = account_data.get("requirements")

    user.stripe_account_id = record.stripe_account_id
    user.stripe_charges_enabled = record.charges_enabled
    user.stripe_payouts_enabled = record.payouts_enabled
    user.stripe_onboarding_completed = record.onboarding_completed

    db.add(record)
    db.add(user)
    db.commit()
    db.refresh(record)
    return record


def create_onboarding_link(user: User, db: Session, *, refresh_url: str, return_url: str) -> str:
    record = ensure_stripe_account_record(user, db)
    link = create_account_link(record.stripe_account_id, refresh_url=refresh_url, return_url=return_url)
    return link.url


def create_checkout_sale(
    *,
    db: Session,
    page_id: int,
    product_id: str,
    section_id: str | None,
    customer: dict[str, str],
    source_url: str | None = None,
    page_slug: str | None = None,
    agency_slug: str | None = None,
) -> tuple[Sale, str]:
    page = (
        db.query(Page)
        .options(joinedload(Page.agency).joinedload(Page.agency.users).joinedload(AgencyUser.user))
        .filter(Page.id == page_id, Page.status == "published")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    config = page.config_json or {}
    resolution = _find_price_item(config, product_id, section_id)
    if resolution.currency != "BRL":
        raise HTTPException(status_code=400, detail="Apenas valores em BRL são aceitos.")
    owner = _pick_agency_owner(db, page.agency_id)
    if not owner.stripe_account_id or not owner.stripe_charges_enabled:
        raise HTTPException(status_code=400, detail="Conta Stripe da agência não está apta a receber pagamentos.")

    amount_cents = _to_cents(resolution.price_decimal)
    if amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Valor do produto inválido.")
    commission_cents = calculate_platform_fee(amount_cents)

    passenger_token = secrets.token_urlsafe(24)
    metadata_raw = {
        "sale_passenger_token": passenger_token,
        "page_id": page.id,
        "page_slug": page.slug,
        "agency_id": page.agency_id,
        "agency_slug": agency_slug or (page.agency.slug if page.agency else None),
        "product_id": product_id,
        "section_id": resolution.section_id,
        "user_id": owner.id,
        "page_url": source_url,
    }
    metadata = {key: str(value) for key, value in metadata_raw.items() if value is not None}
    description = f"{page.title} - {resolution.title}"
    payment_intent = create_payment_intent(
        amount=amount_cents,
        currency="brl",
        stripe_account_id=owner.stripe_account_id,  # type: ignore[arg-type]
        application_fee_amount=commission_cents,
        metadata_json=metadata,
        customer_email=customer.get("email"),
        description=description[:255],
    )

    sale = Sale(
        user_id=owner.id,
        agency_id=page.agency_id,
        page_id=page.id,
        page_slug=page.slug,
        section_id=resolution.section_id,
        price_item_id=product_id,
        product_title=_trim(resolution.title, 255) or "",
        product_description=_trim(resolution.description, 500),
        currency="brl",
        amount=amount_cents,
        commission_amount=commission_cents,
        stripe_application_fee_amount=commission_cents,
        passengers_required=resolution.passengers_required,
        passenger_form_token=passenger_token,
        installments=resolution.installments,
        interest_mode=resolution.interest_mode,
        max_installments_no_interest=resolution.max_installments_no_interest,
        metadata_json={
            "checkout": resolution.checkout_config,
            "page_slug": page_slug or page.slug,
            "page_url": source_url,
        },
        customer_name=_trim(customer.get("name"), 255),
        customer_email=_trim(customer.get("email"), 255),
        customer_phone=_trim(customer.get("phone"), 50),
        stripe_payment_intent_id=payment_intent.id,
        stripe_destination_account=owner.stripe_account_id,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale, payment_intent.client_secret


def serialize_sale(sale: Sale) -> SaleSummary:
    return SaleSummary(
        id=sale.id,
        created_at=sale.created_at,
        product_title=sale.product_title,
        product_description=sale.product_description,
        amount_cents=sale.amount,
        currency=sale.currency,
        commission_cents=sale.commission_amount,
        net_amount_cents=sale.net_amount,
        stripe_fee_cents=sale.stripe_fee_amount,
        payment_method=sale.payment_method,
        installments=sale.installments,
        payment_status=sale.payment_status,
        financial_status=sale.financial_status,
        payout_status=sale.payout_status,
        passenger_status=sale.passenger_status,
        passengers_required=sale.passengers_required,
        customer_name=sale.customer_name,
        customer_email=sale.customer_email,
        customer_phone=sale.customer_phone,
    )


def serialize_passenger(passenger: SalePassenger) -> SalePassengerOut:
    return SalePassengerOut(
        id=passenger.id,
        name=passenger.name,
        cpf=passenger.cpf,
        birthdate=passenger.birthdate.isoformat() if passenger.birthdate else None,
        phone=passenger.phone,
        whatsapp=passenger.whatsapp,
        boarding_location=passenger.boarding_location,
        extras=passenger.extras,
    )


def update_passengers_from_payload(sale: Sale, passenger_payload: Iterable[PassengerInput], db: Session) -> Sale:
    sale.passengers.clear()
    db.flush()
    for payload in passenger_payload:
        birthdate_value = None
        if payload.birthdate:
            try:
                birthdate_value = date.fromisoformat(payload.birthdate)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Data de nascimento inválida.") from exc
        passenger = SalePassenger(
            sale_id=sale.id,
            name=_trim(payload.name, 255) or "",
            cpf=_trim(payload.cpf, 20),
            birthdate=birthdate_value,
            phone=_trim(payload.phone, 50),
            whatsapp=_trim(payload.whatsapp, 50),
            boarding_location=_trim(payload.boarding_location, 255),
            extras=_trim(payload.extras, 1000),
        )
        sale.passengers.append(passenger)
    sale.passenger_status = compute_passenger_status(sale)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def compute_passenger_status(sale: Sale) -> str:
    if not sale.passengers:
        return SalePassengerStatus.not_started.value
    if sale.passengers_required and len(sale.passengers) >= sale.passengers_required:
        has_missing = any(not passenger.name or not passenger.cpf for passenger in sale.passengers)
        if not has_missing:
            return SalePassengerStatus.completed.value
    return SalePassengerStatus.partial.value


def apply_payment_intent_update(
    sale: Sale,
    payment_intent: dict[str, Any],
    *,
    stripe_account: str | None,
    db: Session,
) -> Sale:
    sale.payment_status = payment_intent.get("status") or SalePaymentStatus.processing.value
    charges = payment_intent.get("charges", {}).get("data", [])
    if charges:
        charge = charges[0]
        sale.stripe_charge_id = charge.get("id")
        sale.payment_method = (charge.get("payment_method_details") or {}).get("type") or charge.get("payment_method")
        card_info = (charge.get("payment_method_details") or {}).get("card") or {}
        installments_info = (card_info.get("installments") or {}).get("plan") or {}
        if installments_info.get("count"):
            sale.installments = installments_info["count"]
        sale.stripe_balance_transaction_id = charge.get("balance_transaction")
        sale.stripe_destination_account = (
            (charge.get("transfer_data") or {}).get("destination") or sale.stripe_destination_account
        )
    if sale.stripe_balance_transaction_id:
        balance_tx = retrieve_balance_transaction(sale.stripe_balance_transaction_id, stripe_account=stripe_account)
        sale.stripe_fee_amount = abs(int(balance_tx.get("fee") or 0))
        sale.net_amount = sale.amount - sale.commission_amount - (sale.stripe_fee_amount or 0)
        availability = balance_tx.get("status")
        if availability == "available":
            sale.payout_status = SalePayoutStatus.available.value
        else:
            sale.payout_status = SalePayoutStatus.pending.value
        sale.financial_status = SaleFinancialStatus.finalized.value
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def mark_sale_payment_failed(sale: Sale, db: Session) -> Sale:
    sale.payment_status = SalePaymentStatus.canceled.value
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def handle_payout_event(*, db: Session, stripe_account: str, payout_id: str, status: str) -> None:
    transactions = iter_payout_transactions(payout_id, stripe_account=stripe_account)
    for tx in transactions:
        source = tx.get("source")
        if not source or not source.startswith("ch_"):
            continue
        sale = db.query(Sale).filter(Sale.stripe_charge_id == source).first()
        if not sale:
            continue
        if status == "paid":
            sale.payout_status = SalePayoutStatus.payout_paid.value
        else:
            sale.payout_status = SalePayoutStatus.payout_failed.value
        db.add(sale)
    db.commit()


def fetch_stripe_account_status(user: User, db: Session) -> StripeAccount | None:
    if not user.stripe_account_id:
        return None
    record = (
        db.query(StripeAccount)
        .filter(StripeAccount.user_id == user.id, StripeAccount.stripe_account_id == user.stripe_account_id)
        .first()
    )
    if not record:
        data = retrieve_account(user.stripe_account_id)
        return sync_account_status(user, data, db)
    return record
@dataclass
class CheckoutPriceResolution:
    section_id: str
    section_index: int
    item_index: int
    product_id: str
    title: str
    description: str
    price_decimal: Decimal
    currency: str
    passengers_required: int
    installments: int
    interest_mode: str
    max_installments_no_interest: int | None
    raw_section: dict[str, Any]
    raw_item: dict[str, Any]
    checkout_config: dict[str, Any]
