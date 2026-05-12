from __future__ import annotations

import threading
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.client import Client
from app.models.lead_form import LeadFormSubmission
from app.models.whatsapp import WhatsAppConnection, WhatsAppConversation
from app.services.evolution import EvolutionService
from app.services.whatsapp_domain import WhatsAppDomainService


def _digits(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def _to_e164_br(value: str | None) -> str | None:
    digits = _digits(value)
    if not digits:
        return None
    if len(digits) in {10, 11}:
        return f"55{digits}"
    return digits


def _phone_equivalent(a: str | None, b: str | None) -> bool:
    da = _digits(a)
    db = _digits(b)
    if da.startswith("55") and len(da) > 11:
        da = da[2:]
    if db.startswith("55") and len(db) > 11:
        db = db[2:]
    return bool(da) and da == db


def _resolve_greeting(now: datetime | None = None) -> str:
    current = now or datetime.now()
    if current.hour < 12:
        return "Bom dia"
    if current.hour < 18:
        return "Boa tarde"
    return "Boa noite"


def _resolve_source_name(raw_source: str | None, page_name: str) -> str:
    text = (raw_source or "").strip()
    if not text:
        return page_name or "origem"
    # Alguns fluxos enviam source como id técnico (ex.: "194").
    # Nesses casos, preferimos exibir o nome da página para o cliente final.
    if text.isdigit():
        return page_name or "origem"
    return text


def _render_message_template(
    template: str | None,
    client_name: str,
    form_name: str,
    page_name: str,
    source_name: str,
) -> str:
    base = (template or "").strip()
    if not base:
        return f"Ola {client_name}, recebemos seu interesse, e gostariamos de falar com voce!"
    return (
        base.replace("{{saudacao}}", _resolve_greeting())
        .replace("{{nome}}", client_name)
        .replace("{{template_nome}}", form_name or "formulario")
        .replace("{{pagina_nome}}", page_name or "pagina")
        .replace("{{pagina}}", source_name or page_name or "origem")
        .replace("{{origem}}", source_name or page_name or "origem")
    )


def send_opportunity_welcome_message_best_effort(*, db: Session, opportunity_id: int) -> None:
    try:
        submission = (
            db.query(LeadFormSubmission)
            .filter(LeadFormSubmission.id == opportunity_id)
            .first()
        )
        if not submission:
            return

        linked_client = None
        if submission.client_id:
            linked_client = (
                db.query(Client)
                .filter(Client.id == submission.client_id, Client.deleted_at.is_(None))
                .first()
            )

        target_phone = _to_e164_br(submission.phone or (linked_client.phone if linked_client else None))
        if not target_phone:
            return

        connection = (
            db.query(WhatsAppConnection)
            .filter(
                WhatsAppConnection.agency_id == submission.agency_id,
                WhatsAppConnection.status == "connected",
            )
            .order_by(WhatsAppConnection.is_default.desc(), WhatsAppConnection.updated_at.desc())
            .first()
        )
        if not connection:
            return

        existing_conversation = None
        candidates = (
            db.query(WhatsAppConversation)
            .filter(WhatsAppConversation.agency_id == submission.agency_id)
            .order_by(WhatsAppConversation.updated_at.desc())
            .all()
        )
        for row in candidates:
            if _phone_equivalent(row.remote_phone, target_phone):
                existing_conversation = row
                break

        domain_service = WhatsAppDomainService()
        conversation = existing_conversation or domain_service.get_or_create_conversation(
            db=db,
            agency_id=submission.agency_id,
            connection=connection,
            remote_phone=target_phone,
            remote_name=(submission.name or (linked_client.name if linked_client else None)),
        )

        if linked_client and conversation.client_id is None:
            conversation.client_id = linked_client.id
        if conversation.opportunity_id is None:
            conversation.opportunity_id = submission.id
        if not conversation.remote_name and submission.name:
            conversation.remote_name = submission.name
        db.add(conversation)
        db.flush()

        client_name = (
            (linked_client.name if linked_client and linked_client.name else None)
            or submission.name
            or "cliente"
        )
        form_name = (submission.form.name if submission.form and submission.form.name else "Formulario")
        page_name = (submission.page_title or submission.page_slug or "Pagina")
        source_name = _resolve_source_name(submission.source, page_name)
        message_text = _render_message_template(
            submission.form.auto_whatsapp_message_template if submission.form else None,
            client_name=client_name,
            form_name=form_name,
            page_name=page_name,
            source_name=source_name,
        )

        evolution_service = EvolutionService()
        evolution_raw = evolution_service.send_text_target(
            target=conversation.remote_phone,
            text=message_text,
            instance_name=connection.instance_name,
        )
        domain_service.save_outbound_message(
            db=db,
            connection=connection,
            conversation=conversation,
            text=message_text,
            evolution_response=evolution_raw,
        )
        db.commit()
    except Exception:
        db.rollback()
        return


def dispatch_opportunity_welcome_message(*, opportunity_id: int, delay_seconds: int = 0) -> None:
    safe_delay = max(0, min(int(delay_seconds or 0), 86400))

    def _run() -> None:
        if safe_delay > 0:
            time.sleep(safe_delay)
        db = SessionLocal()
        try:
            send_opportunity_welcome_message_best_effort(db=db, opportunity_id=opportunity_id)
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True).start()
