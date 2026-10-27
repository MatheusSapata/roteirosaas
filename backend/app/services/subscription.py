import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.checkout import CheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services.asaas import AsaasAPIError, AsaasClient, build_default_split_payload
from app.services.billing_cycles import next_due_date
from app.services.checkout import (
    apply_pending_subscription_values,
    find_pix_automatic_authorization_id,
    renew_due_installment_subscriptions,
)
from app.services.company_status import BILLING_PROVIDERS, PAYMENT_RETRY_DAYS
from app.services.viajechat_checkout_flow import tag_abandoned_checkout_sessions

logger = logging.getLogger(__name__)
settings = get_settings()

PLAN_PRICING = {
    "essencial": {"monthly": {"price": 49.90, "asaas_cycle": "MONTHLY"}, "annual": {"price": 479.88, "asaas_cycle": "YEARLY"}},
    "growth": {"monthly": {"price": 89.99, "asaas_cycle": "MONTHLY"}, "annual": {"price": 839.88, "asaas_cycle": "YEARLY"}},
    "infinity": {"monthly": {"price": 129.90, "asaas_cycle": "MONTHLY"}, "annual": {"price": 1199.88, "asaas_cycle": "YEARLY"}},
}


def _advance_pix_due_date(base: date, cycle: str) -> date:
    return next_due_date(base, cycle)


def create_due_pix_automatic_instructions(today: date | None = None) -> int:
    if not settings.asaas_api_key:
        return 0
    today = today or date.today()
    horizon = today + timedelta(days=5)
    db = SessionLocal()
    created = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        sessions = (
            db.query(CheckoutSession)
            .filter(
                CheckoutSession.payment_method == "pix",
                CheckoutSession.status == "paid",
                CheckoutSession.metadata_json.isnot(None),
            )
            .all()
        )
        for checkout_session in sessions:
            metadata = dict(checkout_session.metadata_json or {})
            authorization_id = str(metadata.get("asaas_pix_automatic_authorization_id") or "").strip()
            authorization_status = str(metadata.get("asaas_pix_automatic_authorization_status") or "").upper()
            raw_due_date = str(metadata.get("asaas_pix_automatic_next_due_date") or "").strip()
            if not authorization_id or authorization_status != "ACTIVE" or not raw_due_date:
                continue
            try:
                due_date = date.fromisoformat(raw_due_date)
            except ValueError:
                logger.warning("Data de renovação PIX Automático inválida na sessão %s", checkout_session.id)
                continue
            if due_date > horizon:
                continue
            if str(metadata.get("asaas_pix_automatic_last_instruction_due_date") or "") == due_date.isoformat():
                continue

            try:
                instruction = client.create_pix_automatic_payment_instruction(
                    {
                        "pixAutomaticAuthorizationId": authorization_id,
                        "value": float(checkout_session.amount),
                        "dueDate": due_date.isoformat(),
                        "description": "Renovação assinatura - Roteiro Online"[:35],
                        "externalReference": f"co:{checkout_session.token}"[:120],
                    }
                )
            except AsaasAPIError:
                db.rollback()
                logger.exception(
                    "Erro ao criar instrução Pix Automático para checkout_session_id=%s",
                    checkout_session.id,
                )
                continue
            instruction_id = str((instruction or {}).get("id") or "").strip()
            if not instruction_id:
                logger.error("Asaas não retornou ID da instrução PIX Automático para a sessão %s", checkout_session.id)
                continue
            metadata["asaas_pix_automatic_last_instruction_id"] = instruction_id
            metadata["asaas_pix_automatic_last_instruction_status"] = str(
                (instruction or {}).get("status") or "AWAITING_REQUEST"
            ).upper()
            metadata["asaas_pix_automatic_last_instruction_due_date"] = due_date.isoformat()
            metadata["asaas_pix_automatic_next_due_date"] = _advance_pix_due_date(
                due_date, checkout_session.billing_cycle
            ).isoformat()
            checkout_session.metadata_json = metadata
            checkout_session.updated_at = datetime.utcnow()
            db.add(checkout_session)
            db.commit()
            created += 1
    except Exception:
        db.rollback()
        logger.exception("Erro ao criar instruções de renovação do PIX Automático")
    finally:
        db.close()
    return created


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


def _charged_by_gateway(sub: Subscription) -> bool:
    """Assinatura paga com cobrança recorrente na Asaas ou na Cakto (que pode ser tentada de novo)."""
    return (sub.provider or "").strip().lower() in BILLING_PROVIDERS and Decimal(str(sub.mrr_amount or 0)) > 0


def expire_subscriptions(now: Optional[datetime] = None) -> int:
    """
    Marca assinaturas vencidas como inativas sem despublicar páginas.
    Assinatura ativa cobrada pela Asaas/Cakto que venceu sem renovação confirmada não é encerrada:
    vira inadimplente (no ar por 3 dias, cobrança segue por 30; ver end_unpaid_subscriptions).
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
            if (sub.status or "").lower() == "active" and _charged_by_gateway(sub):
                sub.status = "past_due"
                processed += 1
                continue
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


def _asaas_paid_after(client: AsaasClient, sub: Subscription, due: date) -> bool:
    """Confere na Asaas (só consulta) se entrou pagamento depois do vencimento que o webhook não trouxe."""
    if not sub.asaas_subscription_id:
        return False
    for status in ("RECEIVED", "CONFIRMED"):
        data = client.list_payments(subscription=sub.asaas_subscription_id, status=status, limit=20) or {}
        for item in data.get("data") or []:
            raw = item.get("paymentDate") or item.get("confirmedDate") or item.get("clientPaymentDate")
            if raw and str(raw)[:10] >= due.isoformat():
                return True
    return False


def end_unpaid_subscriptions(now: Optional[datetime] = None) -> int:
    """Encerra a cobrança de quem ficou 30 dias sem pagar depois do vencimento (cancela na Asaas ou
    na Cakto e marca a assinatura como inativa). Se pagar antes disso, o webhook reativa."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=PAYMENT_RETRY_DAYS)
    db = SessionLocal()
    ended = 0
    try:
        subs = (
            db.query(Subscription)
            .filter(
                Subscription.status == "past_due",
                Subscription.valid_until.isnot(None),
                Subscription.valid_until < cutoff,
            )
            .all()
        )
        asaas_client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url) if settings.asaas_api_key else None
        for sub in subs:
            provider = (sub.provider or "").strip().lower()
            if provider not in BILLING_PROVIDERS:
                continue
            try:
                if provider == "asaas":
                    if asaas_client is None:
                        continue
                    due = sub.valid_until.date()
                    if _asaas_paid_after(asaas_client, sub, due):
                        logger.warning("Assinatura %s tem pagamento na Asaas depois do vencimento; não encerrada.", sub.id)
                        continue
                    checkout_token = None
                    reference = str(sub.external_reference or "").strip()
                    if reference.startswith("checkout:"):
                        checkout_token = reference.split("checkout:", 1)[1].strip() or None
                    authorization_id = None
                    if str(sub.payment_method_type or "").strip().lower() == "pix":
                        authorization_id = find_pix_automatic_authorization_id(db, user_id=sub.user_id, checkout_token=checkout_token)
                    if authorization_id:
                        asaas_client.cancel_pix_automatic_authorization(authorization_id, reason="Pagamento não realizado em 30 dias")
                    elif sub.asaas_subscription_id:
                        asaas_client.cancel_subscription(sub.asaas_subscription_id)
                    # Sem os ids, o webhook de assinatura removida não reabre o período.
                    sub.asaas_subscription_id = None
                    sub.asaas_payment_link_id = None
                    sub.external_reference = None
                    sub.valid_until = None
                else:
                    from app.services.cakto import CaktoIntegrationService

                    CaktoIntegrationService(db).cancel_remote_subscription(
                        subscription_code=sub.cakto_subscription_code, order_id=sub.cakto_order_id
                    )
                    # A data de vencimento (já passada) fica: o webhook de cancelamento da Cakto só
                    # recalcula a validade quando ela está vazia.
            except Exception:
                logger.exception("Erro ao encerrar assinatura inadimplente subscription_id=%s", sub.id)
                continue
            sub.status = "inactive"
            sub.failed_attempts = max(int(sub.failed_attempts or 0), 3)
            sub.mrr_amount = 0
            db.add(sub)
            ended += 1
        if ended:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Erro ao encerrar assinaturas inadimplentes")
    finally:
        db.close()
    return ended


def charge_card_renewals() -> int:
    """Cobranças no cartão que o sistema faz (e não o Asaas): renovação do anual parcelado e a
    troca para o valor cheio depois da 1ª mensalidade promocional. Roda antes da expiração, para a
    renovação paga não virar inadimplência."""
    if not settings.asaas_api_key:
        return 0
    db = SessionLocal()
    done = 0
    try:
        client = AsaasClient(settings.asaas_api_key, settings.asaas_base_url)
        done += apply_pending_subscription_values(db, client)
        done += renew_due_installment_subscriptions(db, client)
    except Exception:
        db.rollback()
        logger.exception("Erro nas cobranças de renovação no cartão")
    finally:
        db.close()
    return done


def schedule_payment_watch_job(interval_minutes: int = 5) -> None:
    """Confere de poucos em poucos minutos se algum pagamento recebido deixou a conta sem acesso."""

    async def _loop() -> None:
        while True:
            db = SessionLocal()
            try:
                from app.services.billing_operations import alert_paid_but_blocked

                alert_paid_but_blocked(db)
            except Exception:
                logger.exception("Erro no alerta de pagamento recebido com conta bloqueada")
            finally:
                db.close()
            await asyncio.sleep(interval_minutes * 60)

    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(_loop())


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
                create_due_pix_automatic_instructions()
                charge_card_renewals()
                expire_subscriptions()
                end_unpaid_subscriptions()
            except Exception:
                logger.exception("Erro no job de expiracao de assinaturas")
            try:
                # Depois de expirar: registra quem saiu do ar (e o ciclo dos arquivos, se ligado).
                from app.services.media_lifecycle import hourly_tick

                hourly_tick(SessionLocal)
            except Exception:
                logger.exception("Erro no ciclo de arquivos das empresas")
            await asyncio.sleep(interval_minutes * 60)

    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        # fallback para caso nao haja loop configurado
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(_loop())
