"""Admin master › Avisos de cobrança: configuração, textos, próximos envios e histórico."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.agency import Agency
from app.models.billing_notice import BillingNoticeSend
from app.models.user import User
from app.models.whatsapp import WhatsAppConnection
from app.services import billing_notices as notices
from app.services.asaas import AsaasAPIError

router = APIRouter()

Channel = Literal["whatsapp", "email"]


class StepChannelsIn(BaseModel):
    whatsapp: bool = True
    email: bool = True


class TemplateIn(BaseModel):
    whatsapp: str = ""
    email_subject: str = ""
    email_body: str = ""


class SettingsIn(BaseModel):
    enabled: bool
    whatsapp_connection_id: int | None = None
    available_lead_days: int = Field(notices.DEFAULT_LEAD_DAYS, ge=notices.MIN_LEAD_DAYS, le=notices.MAX_LEAD_DAYS)
    steps: dict[str, StepChannelsIn] = Field(default_factory=dict)
    templates: dict[str, TemplateIn] = Field(default_factory=dict)


class AsaasNotificationsIn(BaseModel):
    enabled: bool


class TestIn(BaseModel):
    step: str
    channel: Channel
    to: str = Field(..., min_length=3, max_length=255)


class PlannedRefIn(BaseModel):
    payment_id: str = Field(..., min_length=1, max_length=80)
    step: str
    channel: Channel
    user_id: int | None = None
    due_date: date | None = None


def _connections(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(WhatsAppConnection, Agency.name)
        .outerjoin(Agency, Agency.id == WhatsAppConnection.agency_id)
        .order_by(WhatsAppConnection.status.desc(), WhatsAppConnection.id.desc())
        .limit(300)
        .all()
    )
    return [
        {
            "id": connection.id,
            "name": connection.name,
            "phone_number": connection.phone_number,
            "status": connection.status,
            "agency_name": agency_name,
        }
        for connection, agency_name in rows
    ]


def _stats(db: Session) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    rows = (
        db.query(BillingNoticeSend.status, func.count(BillingNoticeSend.id))
        .filter(BillingNoticeSend.updated_at >= since)
        .group_by(BillingNoticeSend.status)
        .all()
    )
    counts = {status: count for status, count in rows}
    return {
        "sent_7d": counts.get("sent", 0),
        "failed_7d": counts.get("failed", 0),
        "cancelled_7d": counts.get("cancelled", 0),
    }


def _settings_out(db: Session) -> dict[str, Any]:
    row = notices.get_settings_row(db)
    connection = notices.sender_connection(db, row)
    from app.core.config import get_settings
    from app.services.email import EmailClient

    return {
        "enabled": bool(row.enabled),
        "whatsapp_connection_id": row.whatsapp_connection_id,
        "whatsapp_connection": {
            "id": connection.id,
            "name": connection.name,
            "status": connection.status,
            "phone_number": connection.phone_number,
        }
        if connection
        else None,
        "available_lead_days": notices.lead_days(row),
        "asaas_notifications_enabled": bool(row.asaas_notifications_enabled),
        "steps": [
            {
                "key": step.key,
                "label": step.label,
                "description": step.description.format(dias=notices.lead_days(row)),
                "kind": step.kind,
            }
            for step in notices.STEPS
        ],
        "channels": notices.step_channels(row),
        "templates": notices.step_templates(row),
        "default_templates": notices.DEFAULT_TEMPLATES,
        "custom_fields": notices.custom_template_fields(row),
        "variables": [{"key": key, "label": label} for key, label in notices.VARIABLES],
        "sample": notices.SAMPLE_CONTEXT,
        "connections": _connections(db),
        "email_configured": EmailClient()._is_configured(),
        "asaas_configured": bool(get_settings().asaas_api_key),
        "daily_run_at": "08:07",
        "schedule_since": row.schedule_since.isoformat() if row.schedule_since else None,
        "ran_today": notices.daily_ran(db, notices.sao_paulo_today()),
        "stats": _stats(db),
    }


@router.get("/billing-notices/settings")
def get_billing_notice_settings(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    return _settings_out(db)


@router.put("/billing-notices/settings")
def update_billing_notice_settings(
    payload: SettingsIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)
):
    row = notices.get_settings_row(db)
    if payload.whatsapp_connection_id is not None and db.get(WhatsAppConnection, payload.whatsapp_connection_id) is None:
        raise HTTPException(422, "Conexão de WhatsApp não encontrada.")
    turned_on = payload.enabled and not row.enabled
    lead_changed = payload.available_lead_days != notices.lead_days(row)
    if turned_on or lead_changed or row.schedule_since is None:
        # Sem envio retroativo: o que deveria ter saído antes de hoje não sai mais.
        row.schedule_since = notices.sao_paulo_today()
    row.enabled = payload.enabled
    row.whatsapp_connection_id = payload.whatsapp_connection_id
    row.available_lead_days = payload.available_lead_days
    current = notices.step_channels(row)
    for key, value in payload.steps.items():
        if key in notices.STEP_BY_KEY:
            current[key] = {"whatsapp": value.whatsapp, "email": value.email}
    row.steps_json = current
    if payload.templates:
        row.templates_json = notices.clean_templates({key: value.model_dump() for key, value in payload.templates.items()})
    db.add(row)
    db.commit()
    return _settings_out(db)


@router.post("/billing-notices/asaas-notifications")
def set_asaas_notifications(
    payload: AsaasNotificationsIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)
):
    """Liga ou desliga os avisos do próprio Asaas: grava a escolha (vale para clientes novos) e aplica
    em segundo plano a todos os clientes que já existem."""
    if notices.asaas_client() is None:
        raise HTTPException(503, "A chave da API Asaas não está configurada no servidor.")
    row = notices.get_settings_row(db)
    row.asaas_notifications_enabled = payload.enabled
    db.add(row)
    db.commit()
    notices.apply_asaas_notifications_in_background(payload.enabled)
    return _settings_out(db)


@router.post("/billing-notices/test")
def send_test(payload: TestIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    if payload.step not in notices.STEP_BY_KEY:
        raise HTTPException(422, "Etapa inválida.")
    row = notices.get_settings_row(db)
    if payload.channel == "whatsapp":
        recipient = notices.whatsapp_number(payload.to)
        if not recipient:
            raise HTTPException(422, "Informe um WhatsApp com DDD.")
    else:
        recipient = payload.to.strip()
        if "@" not in recipient:
            raise HTTPException(422, "Informe um e-mail válido.")
    try:
        notices.deliver(db, row, payload.step, payload.channel, recipient, dict(notices.SAMPLE_CONTEXT))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"O teste não saiu: {exc}") from exc
    return {"sent": True}


@router.post("/billing-notices/run-now")
def run_now(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    """Roda a rotina do dia agora. O que já saiu hoje não sai de novo."""
    row = notices.get_settings_row(db)
    if not row.enabled:
        raise HTTPException(409, "Ligue os avisos antes de rodar a rotina.")
    try:
        summary = notices.run_daily(db)
    except (AsaasAPIError, RuntimeError) as exc:
        raise HTTPException(502, f"A rotina não rodou: {exc}") from exc
    notices.mark_event_once(
        db,
        f"billing_notices_daily:{notices.sao_paulo_today().isoformat()}",
        "BILLING_NOTICES_DAILY",
        {"started_at": notices.sao_paulo_now().isoformat(), "manual": True},
    )
    return summary


@router.get("/billing-notices/upcoming")
def get_upcoming(
    days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db), _: User = Depends(get_current_superuser)
):
    try:
        return notices.upcoming(db, days=days)
    except (AsaasAPIError, RuntimeError) as exc:
        raise HTTPException(502, f"Não foi possível consultar o Asaas: {exc}") from exc


@router.post("/billing-notices/upcoming/cancel")
def cancel_upcoming(payload: PlannedRefIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    if payload.step not in notices.STEP_BY_KEY:
        raise HTTPException(422, "Etapa inválida.")
    if not notices.cancel_planned(
        db,
        payment_id=payload.payment_id,
        step=payload.step,
        channel=payload.channel,
        user_id=payload.user_id,
        due_date=payload.due_date,
    ):
        raise HTTPException(409, "Este aviso já saiu ou está saindo.")
    return {"cancelled": True}


@router.post("/billing-notices/upcoming/reactivate")
def reactivate_upcoming(payload: PlannedRefIn, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    if not notices.reactivate_planned(db, payment_id=payload.payment_id, step=payload.step, channel=payload.channel):
        raise HTTPException(409, "Este aviso não está cancelado.")
    return {"reactivated": True}


def _send_out(row: BillingNoticeSend, user: User | None) -> dict[str, Any]:
    step = notices.STEP_BY_KEY.get(row.step)
    context = row.context_json or {}
    return {
        "id": row.id,
        "payment_id": row.payment_id,
        "step": row.step,
        "step_label": step.label if step else row.step,
        "channel": row.channel,
        "status": row.status,
        "attempts": row.attempts,
        "recipient": row.recipient,
        "error": row.error,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "value": context.get("valor"),
        "link": context.get("link"),
        "user_id": row.user_id,
        "name": user.name if user else None,
        "email": user.email if user else None,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/billing-notices/history")
def get_history(
    status: str | None = Query(None),
    step: str | None = Query(None),
    channel: str | None = Query(None),
    q: str | None = Query(None, max_length=120),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    query = db.query(BillingNoticeSend, User).outerjoin(User, User.id == BillingNoticeSend.user_id)
    if status:
        query = query.filter(BillingNoticeSend.status == status)
    if step:
        query = query.filter(BillingNoticeSend.step == step)
    if channel:
        query = query.filter(BillingNoticeSend.channel == channel)
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(User.name).like(term),
                func.lower(User.email).like(term),
                func.lower(BillingNoticeSend.recipient).like(term),
                func.lower(BillingNoticeSend.payment_id).like(term),
            )
        )
    total = query.count()
    rows = query.order_by(BillingNoticeSend.updated_at.desc(), BillingNoticeSend.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [_send_out(row, user) for row, user in rows]}


@router.post("/billing-notices/history/{send_id}/retry")
def retry_send(send_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    row = db.get(BillingNoticeSend, send_id)
    if row is None:
        raise HTTPException(404, "Envio não encontrado.")
    if row.status not in {"failed", "sending"}:
        raise HTTPException(409, "Só dá para tentar de novo um envio que falhou.")
    if not row.recipient:
        raise HTTPException(409, "Este envio não tem destinatário.")
    if not notices.resend(db, row, manual=True):
        raise HTTPException(409, "Este envio já está saindo. Aguarde alguns minutos.")
    db.refresh(row)
    user = db.get(User, row.user_id) if row.user_id else None
    return _send_out(row, user)
