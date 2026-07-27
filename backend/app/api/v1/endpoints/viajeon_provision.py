from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Literal

import bcrypt
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.subscription import Subscription
from app.models.user import User
from app.models.viajeon_webhook_event import ViajeonWebhookEvent
from app.services.team import AGENCY_SLUG_MAX_LENGTH, _slugify


router = APIRouter()
settings = get_settings()

PLAN_MAP = {
    "profissional": "essencial",
    "agencia": "growth",
    "escala": "infinity",
}


class ViajeonAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: EmailStr
    password: str = Field(min_length=8, max_length=512)
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=40)
    document: str | None = Field(default=None, pattern=r"^\d{11}$|^\d{14}$")
    company_name: str = Field(min_length=1, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: Any) -> Any:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("name", "company_name")
    @classmethod
    def strip_nonempty(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("must not be blank")
        return clean

    @field_validator("password")
    @classmethod
    def validate_bcrypt_length(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("must be at most 72 bytes")
        return value


class ViajeonOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=120)
    amount: float = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    paid_at: datetime


class ViajeonProvisionPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event: Literal["subscription.paid"]
    event_id: str = Field(min_length=1, max_length=255)
    sent_at: datetime
    environment: Literal["production", "sandbox"]
    plan: Literal["profissional", "agencia", "escala"]
    billing_cycle: Literal["monthly", "annual"]
    account: ViajeonAccount
    order: ViajeonOrder


def _error(status_code: int, error: str, **extra: Any) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error, **extra})


def _validation_details(exc: ValidationError) -> list[dict[str, str]]:
    return [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": str(error["msg"]),
        }
        for error in exc.errors()
    ]


def _verify_signature(
    raw_body: bytes,
    token: str | None,
    timestamp: str | None,
    signature: str | None,
) -> JSONResponse | None:
    configured_token = settings.viajeon_provision_token
    configured_secret = settings.viajeon_provision_secret
    if not configured_token or not configured_secret:
        return _error(500, "internal")
    if not token or not hmac.compare_digest(token.encode(), configured_token.encode()):
        return _error(401, "invalid-signature")
    try:
        timestamp_number = int(timestamp or "")
    except ValueError:
        return _error(401, "invalid-signature")
    if abs(int(time.time()) - timestamp_number) > 300:
        return _error(401, "expired-timestamp")
    if not signature or not signature.startswith("sha256="):
        return _error(401, "invalid-signature")
    supplied_hex = signature.removeprefix("sha256=")
    expected_hex = hmac.new(
        configured_secret.encode(),
        (f"{timestamp_number}.".encode() + raw_body),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_hex, expected_hex):
        return _error(401, "invalid-signature")
    return None


def _password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def _agency_for_user(db: Session, user: User, company_name: str) -> Agency:
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.user_id == user.id)
        .order_by(AgencyUser.id.asc())
        .first()
    )
    if membership:
        agency = db.query(Agency).filter(Agency.id == membership.agency_id).first()
        if agency:
            if not user.primary_agency_id:
                user.primary_agency_id = agency.id
            return agency

    base_slug = _slugify(company_name or user.name or email_local_part(user.email))
    slug = base_slug
    suffix_number = 1
    while db.query(Agency).filter(Agency.slug == slug).first():
        suffix_number += 1
        suffix = f"-{suffix_number}"
        slug = f"{base_slug[:AGENCY_SLUG_MAX_LENGTH - len(suffix)]}{suffix}"
    agency = Agency(name=company_name, slug=slug)
    db.add(agency)
    db.flush()
    db.add(AgencyUser(agency_id=agency.id, user_id=user.id, role="owner"))
    user.primary_agency_id = agency.id
    return agency


def email_local_part(email: str) -> str:
    return email.split("@", 1)[0]


@router.post("/provision", response_model=None)
async def provision_viajeon_account(
    request: Request,
    x_viajeon_token: str | None = Header(default=None, alias="X-Viajeon-Token"),
    x_viajeon_timestamp: str | None = Header(default=None, alias="X-Viajeon-Timestamp"),
    x_viajeon_signature: str | None = Header(default=None, alias="X-Viajeon-Signature"),
    db: Session = Depends(get_db),
) -> Any:
    raw_body = await request.body()
    signature_error = _verify_signature(
        raw_body,
        x_viajeon_token,
        x_viajeon_timestamp,
        x_viajeon_signature,
    )
    if signature_error:
        return signature_error

    try:
        raw_payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(422, "invalid-payload", details=[{"field": "body", "message": "invalid JSON"}])
    if not isinstance(raw_payload, dict):
        return _error(422, "invalid-payload", details=[{"field": "body", "message": "must be an object"}])
    if raw_payload.get("event") != "subscription.paid":
        return {"status": "ignored"}
    try:
        payload = ViajeonProvisionPayload.model_validate(raw_payload)
    except ValidationError as exc:
        return _error(422, "invalid-payload", details=_validation_details(exc))

    event = ViajeonWebhookEvent(
        event_id=payload.event_id,
        event_type=payload.event,
        environment=payload.environment,
        status="processing",
        order_id=payload.order.id,
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate"}

    email = str(payload.account.email).strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).with_for_update().first()
    status = "updated"
    internal_plan = PLAN_MAP[payload.plan]
    if user is None:
        document = payload.account.document
        if document:
            document_column = User.cpf if len(document) == 11 else User.cnpj
            if db.query(User).filter(document_column == document).first():
                db.rollback()
                return _error(409, "email-conflict", message="CPF/CNPJ já pertence a outra conta.")
        user = User(
            email=email,
            name=payload.account.name,
            hashed_password=_password_hash(payload.account.password),
            cpf=document if document and len(document) == 11 else None,
            cnpj=document if document and len(document) == 14 else None,
            whatsapp=payload.account.phone,
            plan=internal_plan,
            is_active=True,
            is_owner=True,
            role="admin",
            status="active",
            source="viajeon",
            must_change_password=True,
            permissions=[],
        )
        db.add(user)
        db.flush()
        agency = _agency_for_user(db, user, payload.account.company_name)
        agency.name = payload.account.company_name
        agency.contact_email = email
        agency.cta_whatsapp = payload.account.phone
        status = "created"
    else:
        agency = _agency_for_user(db, user, payload.account.company_name)

    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
        db.flush()
        user.subscription_id = subscription.id
    user.plan = internal_plan
    user.is_active = True
    user.status = "active"
    if not user.source:
        user.source = "viajeon"
    subscription.plan = internal_plan
    subscription.provider = "viajeon"
    subscription.billing_cycle = payload.billing_cycle
    subscription.status = "active"
    subscription.external_reference = payload.order.id
    subscription.mrr_amount = payload.order.amount
    subscription.updated_at = datetime.now(timezone.utc)
    event.status = "processed"
    event.user_id = user.id
    event.agency_id = agency.id
    event.processed_at = datetime.now(timezone.utc)
    db.add_all([user, agency, subscription, event])
    db.commit()

    login_base = (settings.webapp_base_url or "https://app.roteiroonline.com").rstrip("/")
    return {
        "status": status,
        "user_id": str(user.id),
        "agency_id": str(agency.id),
        "plan": payload.plan,
        "login_url": f"{login_base}/login",
    }
