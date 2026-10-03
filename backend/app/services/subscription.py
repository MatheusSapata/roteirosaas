import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.checkout import find_pix_automatic_authorization_id
from app.services.viajechat_checkout_flow import tag_abandoned_checkout_sessions

logger = logging.getLogger(__name__)
settings = get_settings()

PLAN_PRICING = {
    "essencial": {"monthly": {"price": 49.90, "asaas_cycle": "MONTHLY"}, "annual": {"price": 479.88, "asaas_cycle": "YEARLY"}},
    "growth": {"monthly": {"price": 89.99, "asaas_cycle": "MONTHLY"}, "annual": {"price": 839.88, "asaas_cycle": "YEARLY"}},
    "infinity": {"monthly": {"price": 129.90, "asaas_cycle": "MONTHLY"}, "annual": {"price": 1199.88, "asaas_cycle": "YEARLY"}},
}


def _advance_pix_due_date(base: date, cycle: str) -> date:
    if str(cycle).strip().lower() == "annual":
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


# Pix Automático (Asaas, modo MANUAL): a autorização é criada no checkout e, a
# cada ciclo, a aplicação cria a cobrança com POST /v3/payments informando
# pixAutomaticAuthorizationId. O Asaas exige que a cobrança seja criada entre 2 e
# 10 dias úteis antes do vencimento.
PIX_AUTOMATIC_MIN_LEAD_BUSINESS_DAYS = 3
PIX_AUTOMATIC_MAX_LEAD_BUSINESS_DAYS = 8
# Ciclo perdido há mais tempo que isso não é cobrado sozinho: fica marcado para
# revisão manual, para não surpreender quem já estava sem acesso.
PIX_AUTOMATIC_CATCH_UP_DAYS = 7
_CANCELLED_SUBSCRIPTION_STATUSES = {"cancelled", "cancelled_admin", "cancel_at_period_end", "canceled"}


def _business_days_between(start: date, end: date) -> int:
    """Dias úteis (seg-sex) depois de start até end, inclusive. Negativo se end < start."""
    if end == start:
        return 0
    step = 1 if end > start else -1
    count = 0
    current = start
    while current != end:
        current += timedelta(days=step)
        if current.weekday() < 5:
            count += step
    return count


def _add_business_days(base: date, days: int) -> date:
    current = base
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def _checkout_token_from_reference(reference: str | None) -> str | None:
    raw = str(reference or "").strip()
    for prefix in ("checkout_upgrade:", "checkout:", "co:"):
        if raw.startswith(prefix):
            return raw.split(prefix, 1)[1].strip() or None
    return None


def _pix_renewal_skip_reason(db, checkout_session: CheckoutSession) -> str | None:
    """Motivo para não cobrar esta sessão, ou None se pode cobrar."""
    if not checkout_session.user_id:
        return "sessão sem usuário"
    user = db.query(User).filter(User.id == checkout_session.user_id).first()
    subscription = user.subscription if user else None
    if not subscription:
        return "usuário sem assinatura"
    if str(subscription.status or "").strip().lower() in _CANCELLED_SUBSCRIPTION_STATUSES:
        return "assinatura cancelada"
    if str(subscription.payment_method_type or "").strip().lower() != "pix":
        return "assinatura atual não é Pix"
    reference = str(subscription.external_reference or "").strip()
    if reference.startswith("scheduled_downgrade:"):
        # O valor da cobrança muda com o downgrade; não cobrar o plano antigo.
        return "downgrade agendado: revisar o valor antes de cobrar"
    current_token = _checkout_token_from_reference(reference)
    if current_token and current_token != checkout_session.token:
        return "assinatura atual veio de outro checkout"
    return None


def _find_existing_renewal_payment(client: AsaasClient, checkout_session: CheckoutSession, due: date, original_due: date) -> dict | None:
    """Evita cobrança dupla: procura no Asaas uma cobrança deste checkout para o mesmo ciclo."""
    try:
        response = client.list_payments(externalReference=f"co:{checkout_session.token}"[:120], limit=100)
    except AsaasAPIError:
        logger.exception("Não foi possível consultar cobranças existentes da sessão %s", checkout_session.id)
        raise
    window_start = min(due, original_due) - timedelta(days=3)
    window_end = max(due, original_due) + timedelta(days=3)
    for item in (response or {}).get("data") or []:
        if item.get("deleted") or str(item.get("status") or "").upper() in {"DELETED", "REFUNDED"}:
            continue
        try:
            item_due = date.fromisoformat(str(item.get("dueDate") or "")[:10])
        except ValueError:
            continue
        if window_start <= item_due <= window_end:
            return item
    return None


def _create_pix_automatic_payment(client: AsaasClient, payload: dict) -> dict:
    """Cria a cobrança com a divisão de valor padrão; se o Asaas recusar a divisão
    nesse tipo de cobrança, cria sem ela para o cliente não ficar sem cobrança."""
    try:
        return client.create_payment({**payload, "split": build_default_split_payload()})
    except AsaasAPIError as exc:
        if "split" not in str(exc).lower():
            raise
        logger.warning("Asaas recusou o split na cobrança Pix Automático; criando sem split: %s", exc)
        return client.create_payment(payload)


def create_due_pix_automatic_charges(today: date | None = None) -> int:
    if not settings.asaas_api_key:
        return 0
    today = today or date.today()
    db = SessionLocal()
    created = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        candidate_ids = [
            row_id
            for (row_id,) in db.query(CheckoutSession.id)
            .filter(
                CheckoutSession.payment_method == "pix",
                CheckoutSession.status == "paid",
                CheckoutSession.metadata_json.isnot(None),
            )
            .all()
        ]
        for session_id in candidate_ids:
            # Trava a linha: com mais de um processo rodando o job, só um cobra.
            checkout_session = (
                db.query(CheckoutSession)
                .filter(CheckoutSession.id == session_id)
                .with_for_update(skip_locked=True)
                .first()
            )
            if not checkout_session or checkout_session.status != "paid":
                db.rollback()
                continue
            metadata = dict(checkout_session.metadata_json or {})
            authorization_id = str(metadata.get("asaas_pix_automatic_authorization_id") or "").strip()
            authorization_status = str(metadata.get("asaas_pix_automatic_authorization_status") or "").upper()
            raw_due_date = str(metadata.get("asaas_pix_automatic_next_due_date") or "").strip()
            if (
                str(metadata.get("pix_mode") or "").strip().lower() != "automatic"
                or not authorization_id
                or authorization_status != "ACTIVE"
                or not raw_due_date
            ):
                db.rollback()
                continue
            try:
                original_due = date.fromisoformat(raw_due_date)
            except ValueError:
                logger.warning("Data de renovação PIX Automático inválida na sessão %s", checkout_session.id)
                db.rollback()
                continue

            lead = _business_days_between(today, original_due)
            if lead > PIX_AUTOMATIC_MAX_LEAD_BUSINESS_DAYS:
                db.rollback()
                continue
            due = original_due
            if lead < PIX_AUTOMATIC_MIN_LEAD_BUSINESS_DAYS:
                if original_due < today - timedelta(days=PIX_AUTOMATIC_CATCH_UP_DAYS):
                    if metadata.get("asaas_pix_automatic_renewal_needs_review") != raw_due_date:
                        metadata["asaas_pix_automatic_renewal_needs_review"] = raw_due_date
                        checkout_session.metadata_json = metadata
                        db.add(checkout_session)
                        db.commit()
                        logger.warning(
                            "Pix Automático: ciclo de %s da sessão %s passou há mais de %s dias; não cobrado automaticamente.",
                            raw_due_date,
                            checkout_session.id,
                            PIX_AUTOMATIC_CATCH_UP_DAYS,
                        )
                    else:
                        db.rollback()
                    continue
                due = _add_business_days(today, PIX_AUTOMATIC_MIN_LEAD_BUSINESS_DAYS)

            skip_reason = _pix_renewal_skip_reason(db, checkout_session)
            if skip_reason:
                if metadata.get("asaas_pix_automatic_renewal_skipped") != skip_reason:
                    metadata["asaas_pix_automatic_renewal_skipped"] = skip_reason
                    checkout_session.metadata_json = metadata
                    db.add(checkout_session)
                    db.commit()
                    logger.info("Pix Automático: sessão %s não cobrada (%s)", checkout_session.id, skip_reason)
                else:
                    db.rollback()
                continue

            customer_id = checkout_session.asaas_customer_id
            if not customer_id and checkout_session.user_id:
                owner = db.query(User).filter(User.id == checkout_session.user_id).first()
                customer_id = owner.subscription.asaas_customer_id if owner and owner.subscription else None
            if not customer_id:
                logger.error("Pix Automático: sessão %s sem cliente no Asaas", checkout_session.id)
                db.rollback()
                continue

            try:
                payment = _find_existing_renewal_payment(client, checkout_session, due, original_due)
                if not payment:
                    payment = _create_pix_automatic_payment(
                        client,
                        {
                            "customer": customer_id,
                            "billingType": "PIX",
                            "value": float(checkout_session.amount),
                            "dueDate": due.isoformat(),
                            "description": f"Renovação {checkout_session.product_name or 'Roteiro Online'}"[:100],
                            "externalReference": f"co:{checkout_session.token}"[:120],
                            "pixAutomaticAuthorizationId": authorization_id,
                        },
                    )
            except AsaasAPIError as exc:
                db.rollback()
                metadata["asaas_pix_automatic_last_error"] = str(exc)[:500]
                metadata["asaas_pix_automatic_last_error_at"] = datetime.utcnow().isoformat()
                checkout_session.metadata_json = metadata
                db.add(checkout_session)
                db.commit()
                logger.error(
                    "Erro ao criar cobrança Pix Automático para checkout_session_id=%s: %s",
                    checkout_session.id,
                    exc,
                )
                continue

            payment_id = str((payment or {}).get("id") or "").strip()
            if not payment_id:
                logger.error("Asaas não retornou o ID da cobrança Pix Automático da sessão %s", checkout_session.id)
                db.rollback()
                continue
            renewal_ids = list(metadata.get("asaas_pix_automatic_renewal_payment_ids") or [])
            if payment_id not in renewal_ids:
                renewal_ids.append(payment_id)
            metadata["asaas_pix_automatic_renewal_payment_ids"] = renewal_ids[-24:]
            metadata["asaas_pix_automatic_last_charge_id"] = payment_id
            metadata["asaas_pix_automatic_last_charge_due_date"] = due.isoformat()
            metadata["asaas_pix_automatic_last_instruction_due_date"] = original_due.isoformat()
            metadata["asaas_pix_automatic_next_due_date"] = _advance_pix_due_date(
                original_due, checkout_session.billing_cycle
            ).isoformat()
            metadata.pop("asaas_pix_automatic_last_error", None)
            metadata.pop("asaas_pix_automatic_last_error_at", None)
            metadata.pop("asaas_pix_automatic_renewal_needs_review", None)
            metadata.pop("asaas_pix_automatic_renewal_skipped", None)
            checkout_session.metadata_json = metadata
            checkout_session.updated_at = datetime.utcnow()
            db.add(checkout_session)
            db.commit()
            created += 1
    except Exception:
        db.rollback()
        logger.exception("Erro ao criar cobranças de renovação do PIX Automático")
    finally:
        db.close()
    return created


# Nome antigo, mantido para quem ainda chama a função.
create_due_pix_automatic_instructions = create_due_pix_automatic_charges


def _parse_scheduled_downgrade(ref: str | None) -> str | None:
    raw = str(ref or "")
    if not raw.startswith("scheduled_downgrade:"):
        return None
    target = raw.split("scheduled_downgrade:", 1)[1].strip().lower()
    return target or None


def _build_external_reference(user_id: int, plan_key: str, cycle: str) -> str:
    return f"{user_id}:{plan_key}:{cycle}"


def _apply_scheduled_downgrades(now: datetime) -> int:
    if not settings.asaas_api_key:
        return 0
    db = SessionLocal()
    updated = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        subs = (
            db.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.valid_until.isnot(None),
                Subscription.external_reference.isnot(None),
            )
            .all()
        )
        for sub in subs:
            target_plan = _parse_scheduled_downgrade(sub.external_reference)
            if not target_plan:
                continue
            if not sub.asaas_subscription_id or sub.provider != "asaas":
                continue
            if not sub.valid_until:
                continue
            # Apply at D-1 (or later if the job was unavailable), before expiration.
            if sub.valid_until > (now + timedelta(days=1)):
                continue

            cycle = (sub.billing_cycle or "monthly").lower()
            plan_info = PLAN_PRICING.get(target_plan, {}).get(cycle)
            if not plan_info:
                continue

            try:
                client.update_subscription(
                    sub.asaas_subscription_id,
                    {
                        "value": plan_info["price"],
                        "cycle": plan_info["asaas_cycle"],
                        "externalReference": _build_external_reference(sub.user_id, target_plan, cycle),
                        "split": build_default_split_payload(),
                    },
                )
                updated += 1
            except AsaasAPIError:
                logger.exception("Erro ao aplicar downgrade agendado para subscription_id=%s", sub.id)

        if updated:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao aplicar downgrades agendados")
    finally:
        db.close()
    return updated


def _apply_scheduled_cancellations(now: datetime) -> int:
    if not settings.asaas_api_key:
        return 0
    db = SessionLocal()
    processed = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        subs = (
            db.query(Subscription)
            .filter(
                Subscription.provider == "asaas",
                Subscription.status == "cancel_at_period_end",
                Subscription.valid_until.isnot(None),
            )
            .all()
        )
        for sub in subs:
            if not sub.valid_until:
                continue
            # Execute at D-1 (or later if delayed) before next charge window.
            if sub.valid_until > (now + timedelta(days=1)):
                continue
            try:
                checkout_token = None
                external_reference = str(sub.external_reference or "").strip()
                if external_reference.startswith("checkout:"):
                    checkout_token = external_reference.split("checkout:", 1)[1].strip() or None
                authorization_id = None
                if str(sub.payment_method_type or "").strip().lower() == "pix":
                    authorization_id = find_pix_automatic_authorization_id(
                        db,
                        user_id=sub.user_id,
                        checkout_token=checkout_token,
                    )
                if authorization_id:
                    client.cancel_pix_automatic_authorization(
                        authorization_id,
                        reason="Cancelamento ao final do período contratado",
                    )
                elif sub.asaas_subscription_id:
                    client.cancel_subscription(sub.asaas_subscription_id)
                else:
                    logger.warning("Assinatura %s sem identificador remoto para cancelamento", sub.id)
                    continue
                sub.status = "cancelled"
                db.add(sub)
                processed += 1
            except AsaasAPIError:
                logger.exception("Erro ao aplicar cancelamento agendado para subscription_id=%s", sub.id)
        if processed:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao aplicar cancelamentos agendados")
    finally:
        db.close()
    return processed


def expire_subscriptions(now: Optional[datetime] = None) -> int:
    """
    Marca assinaturas vencidas como inativas sem despublicar páginas.
    Retorna quantidade processada.
    """
    now = now or datetime.utcnow()
    db = SessionLocal()
    processed = 0
    try:
        expired = (
            db.query(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .filter(
                Subscription.valid_until.isnot(None),
                Subscription.valid_until < now,
                Subscription.status.in_(("active", "cancelled", "cancel_at_period_end")),
            )
            .all()
        )
        for sub, user in expired:
            sub.status = "inactive"
            sub.valid_until = None
            sub.failed_attempts = 3
            db.add(user)
            processed += 1
        if processed:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao expirar assinaturas")
    finally:
        db.close()
    return processed


def schedule_expiration_job(interval_minutes: int = 60) -> None:
    """
    Inicia uma tarefa assincrona que roda a cada interval_minutes.
    """

    async def _loop() -> None:
        while True:
            try:
                _apply_scheduled_downgrades(datetime.utcnow())
                _apply_scheduled_cancellations(datetime.utcnow())
                tag_abandoned_checkout_sessions(cutoff_minutes=30)
                create_due_pix_automatic_charges()
                expire_subscriptions()
            except Exception:
                logger.exception("Erro no job de expiracao de assinaturas")
            await asyncio.sleep(interval_minutes * 60)

    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        # fallback para caso nao haja loop configurado
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(_loop())
