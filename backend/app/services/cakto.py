from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cakto import CaktoEventLog, CaktoOnboardingToken, CaktoCheckoutSession
from app.models.subscription import Subscription
from app.models.user import User
from app.services import auth as auth_service
from app.services.email import send_cakto_onboarding_email
from app.services.trial import end_trial

logger = logging.getLogger(__name__)
settings = get_settings()
ZERO_DECIMAL = Decimal("0.00")


class CaktoAPIError(Exception):
    """Raised when a request to the Cakto API fails."""


@dataclass
class PlanMapping:
    plan_key: str
    cycle: str
    offer_id: str | None
    product_id: str | None


PLAN_ENV_SPECS = [
    ("essencial", "monthly", "cakto_offer_essencial_monthly", "cakto_product_essencial_monthly"),
    ("essencial", "annual", "cakto_offer_essencial_annual", "cakto_product_essencial_annual"),
    ("growth", "monthly", "cakto_offer_growth_monthly", "cakto_product_growth_monthly"),
    ("growth", "annual", "cakto_offer_growth_annual", "cakto_product_growth_annual"),
    ("infinity", "monthly", "cakto_offer_infinity_monthly", "cakto_product_infinity_monthly"),
    ("infinity", "annual", "cakto_offer_infinity_annual", "cakto_product_infinity_annual"),
    ("teste", "monthly", "cakto_offer_teste_monthly", "cakto_product_teste_monthly"),
    ("teste", "annual", "cakto_offer_teste_annual", "cakto_product_teste_annual"),
]


class CaktoIntegrationService:
    """
    Responsável por processar eventos do Cakto e administrar o onboarding dos clientes.
    """

    def __init__(self, db: Session):
        self.db = db
        self.plan_mappings = self._load_plan_mappings()
        raw_base = getattr(settings, "cakto_api_base_url", None)
        self.api_base_url = raw_base.rstrip("/") if isinstance(raw_base, str) else None
        self.api_client_id = getattr(settings, "cakto_client_id", None)
        self.api_client_secret = getattr(settings, "cakto_client_secret", None)
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_url = None
        if self.api_base_url:
            base_for_token = self.api_base_url.rstrip("/")
            if base_for_token.endswith("/v1"):
                base_for_token = base_for_token[:-3]
            self._token_url = f"{base_for_token}/public_api/token/"

    def _load_plan_mappings(self) -> list[PlanMapping]:
        mappings: list[PlanMapping] = []
        for plan_key, cycle, offer_attr, product_attr in PLAN_ENV_SPECS:
            raw_offer_id = getattr(settings, offer_attr, None)
            raw_product_id = getattr(settings, product_attr, None)
            offer_id = raw_offer_id.strip().lower() if isinstance(raw_offer_id, str) else raw_offer_id
            product_id = raw_product_id.strip().lower() if isinstance(raw_product_id, str) else raw_product_id
            if offer_id or product_id:
                mappings.append(PlanMapping(plan_key, cycle, offer_id, product_id))
        return mappings

    def _mapping_for_plan(self, plan_key: str, cycle: str) -> PlanMapping | None:
        target_cycle = (cycle or "monthly").lower()
        target_plan = plan_key.lower()
        for mapping in self.plan_mappings:
            if mapping.plan_key == target_plan and mapping.cycle == target_cycle:
                return mapping
        return None

    def create_checkout_session(self, plan_key: str, cycle: str | None = None) -> tuple[CaktoCheckoutSession, str]:
        cycle_value = (cycle or "monthly").lower()
        mapping = self._mapping_for_plan(plan_key, cycle_value)
        if not mapping or not mapping.offer_id:
            raise ValueError("Plano indisponível no checkout Cakto.")
        base_url = f"https://pay.cakto.com.br/{mapping.offer_id}"
        token = uuid4().hex
        session = CaktoCheckoutSession(
            token=token,
            plan_key=mapping.plan_key,
            cycle=mapping.cycle,
            checkout_url=base_url,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        separator = "&" if "?" in base_url else "?"
        checkout_with_sck = f"{base_url}{separator}sck={token}"
        return session, checkout_with_sck

    def get_checkout_session(self, token: str) -> Optional[CaktoCheckoutSession]:
        return (
            self.db.query(CaktoCheckoutSession)
            .filter(CaktoCheckoutSession.token == token)
            .first()
        )

    # ------------------------------------------------------------------ #
    # Webhook dispatcher
    # ------------------------------------------------------------------ #
    def process_event(self, payload: Dict[str, Any]) -> str:
        event_type = self._extract_event_type(payload)
        if not event_type:
            raise ValueError("Evento do Cakto sem 'event' ou 'event_id'.")
        event_id = self._extract_event_id(payload)

        if event_id:
            exists = self.db.query(CaktoEventLog).filter(CaktoEventLog.event_id == event_id).first()
            if exists:
                logger.info("Evento Cakto %s ignorado (já processado).", event_id)
                return "Evento duplicado ignorado."

        log = CaktoEventLog(event_id=event_id, event_type=event_type, payload=payload)
        self.db.add(log)
        self.db.flush()

        try:
            normalized = event_type.lower()
            if normalized in {"purchase_approved", "subscription_created"}:
                result = self._handle_purchase(payload, normalized)
            elif normalized == "subscription_renewed":
                result = self._handle_subscription_status(payload, status="active")
            elif normalized == "subscription_canceled":
                result = self._handle_subscription_status(payload, status="cancelled", downgrade_plan=True)
            elif normalized == "subscription_renewal_refused":
                result = self._handle_subscription_status(payload, status="past_due", downgrade_plan=True)
            else:
                result = f"Evento {event_type} registrado sem ação específica."

            log.status = "processed"
            log.processed_at = datetime.utcnow()
            self.db.commit()
            return result
        except Exception as exc:  # pylint: disable=broad-except
            self.db.rollback()
            log.status = "error"
            log.error_message = str(exc)
            self.db.add(log)
            self.db.commit()
            logger.exception("Erro ao processar evento do Cakto: %s", event_type)
            raise

    # ------------------------------------------------------------------ #
    # Onboarding session helpers
    # ------------------------------------------------------------------ #
    def get_onboarding_record(
        self,
        *,
        token: str | None = None,
        order_id: str | None = None,
        ref_id: str | None = None,
        subscription_code: str | None = None,
    ) -> Optional[CaktoOnboardingToken]:
        """
        Retorna o registro de onboarding válido a partir de token ou identificadores do pedido.
        """
        if not any([token, order_id, ref_id, subscription_code]):
            return None

        query = self.db.query(CaktoOnboardingToken).filter(CaktoOnboardingToken.consumed_at.is_(None))
        if token:
            query = query.filter(CaktoOnboardingToken.token == token)
        if order_id:
            query = query.filter(
                or_(
                    CaktoOnboardingToken.order_id == order_id,
                    CaktoOnboardingToken.subscription_code == order_id,
                )
            )
        if ref_id:
            query = query.filter(CaktoOnboardingToken.order_ref == ref_id)
        if subscription_code:
            query = query.filter(CaktoOnboardingToken.subscription_code == subscription_code)

        record = query.first()
        if not record:
            return None
        if record.expires_at and datetime.utcnow() > record.expires_at:
            return None
        return record

    def _normalize_email(self, email: str) -> str:
        if not email:
            raise ValueError("Informe o email utilizado na compra.")
        normalized = email.strip().lower()
        if not normalized:
            raise ValueError("Informe um email válido.")
        return normalized

    def _get_user_by_email(self, email: str) -> User:
        normalized = self._normalize_email(email)
        user = (
            self.db.query(User)
            .filter(func.lower(User.email) == normalized)
            .first()
        )
        if not user:
            raise LookupError("Não encontramos nenhum cadastro com este email.")
        return user

    def set_password_for_onboarding(
        self,
        *,
        password: str,
        token: str | None = None,
        order_id: str | None = None,
        ref_id: str | None = None,
        subscription_code: str | None = None,
    ) -> None:
        record = self.get_onboarding_record(
            token=token,
            order_id=order_id,
            ref_id=ref_id,
            subscription_code=subscription_code,
        )
        if not record:
            raise ValueError("Sessão expirada ou inválida. Solicite um novo link.")

        user = record.user
        auth_service.validate_password_strength(password)
        user.hashed_password = auth_service.get_password_hash(password)
        user.is_active = True
        user.plan = record.plan_key
        record.consumed_at = datetime.utcnow()
        end_trial(user, self.db, keep_plan=record.plan_key)
        self.db.add_all([user, record])
        self.db.commit()

    def lookup_manual_user(self, email: str) -> User:
        return self._get_user_by_email(email)

    def set_password_by_email(self, *, email: str, password: str) -> User:
        user = self._get_user_by_email(email)

        auth_service.validate_password_strength(password)
        user.hashed_password = auth_service.get_password_hash(password)
        user.is_active = True
        keep_plan = user.plan
        if not keep_plan and getattr(user, "subscription", None):
            keep_plan = user.subscription.plan
        end_trial(user, self.db, keep_plan=keep_plan)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def _handle_purchase(self, payload: Dict[str, Any], event_type: str) -> str:
        order = self._extract_order(payload)
        if not order:
            raise ValueError("Payload do Cakto não contém dados de pedido.")
        customer = self._extract_customer(order, payload)
        if not customer or not customer.get("email"):
            raise ValueError("Pedido sem email do cliente.")

        offer_id = self._extract_offer_id(order, payload)
        product_id = self._extract_product_id(order, payload)
        plan = self._resolve_plan(offer_id, product_id)
        if not plan:
            raise ValueError("Não foi possível associar o pedido a um plano configurado.")

        subscription_code = self._extract_subscription_code(payload, order)
        next_due_date = self._extract_next_due_date(payload, order)
        valid_until = self._calculate_valid_until(plan.cycle, next_due_date)
        order_id = self._normalize_str(order.get("id"))
        order_ref = self._normalize_str(order.get("refId"))
        order_amount = self._extract_order_amount(order, payload)
        monthly_amount = self._calculate_mrr_amount(order_amount, plan.cycle)

        user, created = self._upsert_user_and_subscription(
            customer=customer,
            address=order.get("address"),
            plan_key=plan.plan_key,
            cycle=plan.cycle,
            offer_id=offer_id,
            order_id=order_id,
            order_ref=order_ref,
            subscription_code=subscription_code,
            valid_until=valid_until,
        )
        if monthly_amount is not None and user.subscription:
            user.subscription.mrr_amount = monthly_amount
            self.db.add(user.subscription)

        onboarding_token = None
        if created:
            onboarding_token = self._create_onboarding_token(
                user=user,
                plan_key=plan.plan_key,
                cycle=plan.cycle,
                order_id=order_id,
                order_ref=order_ref,
                subscription_code=subscription_code,
                offer_id=offer_id,
            )
        session_token = self._extract_session_token(payload)
        if session_token:
            self._finalize_checkout_session(
                session_token,
                order_id=order_id,
                order_ref=order_ref,
                onboarding_token=onboarding_token,
            )
        self.db.commit()
        if onboarding_token:
            try:
                send_cakto_onboarding_email(
                    user=user,
                    onboarding_token=onboarding_token,
                    plan_key=plan.plan_key,
                    cycle=plan.cycle,
                )
            except Exception:  # pragma: no cover - envio de email nao deve quebrar o webhook
                logger.exception("Erro ao enviar e-mail de onboarding para %s", user.email)
        return f"Pedido {order_ref or order_id} processado via {event_type}."

    def _handle_subscription_status(
        self,
        payload: Dict[str, Any],
        *,
        status: str,
        downgrade_plan: bool = False,
    ) -> str:
        subscription_code = self._extract_subscription_code(payload, None)
        order_id = self._extract_order_id(payload)
        subscription = self._find_subscription(subscription_code=subscription_code, order_id=order_id)
        if not subscription:
            raise ValueError("Assinatura não encontrada para atualização.")

        order = self._extract_order(payload)
        offer_id = self._extract_offer_id(order, payload)
        product_id = self._extract_product_id(order, payload)
        incoming_amount = self._extract_order_amount(order, payload)
        new_amount = self._calculate_mrr_amount(incoming_amount, subscription.billing_cycle)

        if status.lower() == "cancelled":
            incoming_plan = None
            if offer_id or product_id:
                mapping = self._resolve_plan(offer_id, product_id)
                if mapping:
                    incoming_plan = mapping.plan_key
            current_plan = subscription.plan.lower() if subscription.plan else None
            should_ignore = False
            if incoming_plan and current_plan and incoming_plan != current_plan:
                should_ignore = True
            elif not incoming_plan and offer_id and subscription.cakto_offer_id and offer_id != subscription.cakto_offer_id:
                should_ignore = True
            if should_ignore:
                user_identifier = None
                if subscription.user and subscription.user.email:
                    user_identifier = subscription.user.email
                elif subscription.user_id:
                    user_identifier = f"id={subscription.user_id}"
                logger.info(
                    "Cliente já com upgrade (%s). Cancelamento ignorado para assinatura %s. Evento pertence à oferta %s (plano %s), assinatura está no plano %s.",
                    user_identifier or "cliente desconhecido",
                    subscription_code or order_id,
                    offer_id,
                    incoming_plan or "desconhecido",
                    subscription.plan,
                )
                return (
                    f"Cliente já com upgrade. Assinatura {subscription_code or order_id} já migrada para outro plano; cancelamento ignorado."
                )

        subscription.status = status
        subscription.updated_at = datetime.utcnow()
        if status.lower() == "active":
            mapping = None
            if offer_id or product_id:
                mapping = self._resolve_plan(offer_id, product_id)
            next_due_date = self._extract_next_due_date(payload, order)
            target_cycle = None
            if mapping:
                subscription.plan = mapping.plan_key
                subscription.billing_cycle = mapping.cycle
                target_cycle = mapping.cycle
                if subscription.user:
                    subscription.user.plan = mapping.plan_key
                    self.db.add(subscription.user)
            else:
                target_cycle = subscription.billing_cycle
            if next_due_date or target_cycle:
                subscription.valid_until = self._calculate_valid_until(target_cycle or subscription.billing_cycle, next_due_date)
            if new_amount is not None:
                subscription.mrr_amount = new_amount
            if offer_id:
                subscription.cakto_offer_id = offer_id
            if order_id:
                subscription.cakto_order_id = order_id
            if subscription_code:
                subscription.cakto_subscription_code = subscription_code
        else:
            subscription.mrr_amount = ZERO_DECIMAL
        if downgrade_plan and subscription.user:
            subscription.user.plan = "free"
            subscription.user.subscription = subscription
        self.db.add(subscription)
        self.db.commit()
        return f"Assinatura {subscription_code or order_id} marcada como {status}."

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _extract_event_type(self, payload: Dict[str, Any]) -> str | None:
        return self._normalize_str(
            payload.get("event")
            or payload.get("event_id")
            or payload.get("eventId")
            or payload.get("type")
        )

    def _extract_event_id(self, payload: Dict[str, Any]) -> str | None:
        return self._normalize_str(payload.get("id") or payload.get("event_id") or payload.get("eventId"))

    def _to_decimal(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        normalized = "".join(ch for ch in text.replace(",", ".") if ch.isdigit() or ch in {".", "-"})
        if not normalized:
            return None
        try:
            return Decimal(normalized)
        except (InvalidOperation, ValueError):
            return None

    def _extract_order(self, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        primary = self._primary_data(payload)
        if isinstance(primary, dict):
            # Alguns eventos retornam o pedido diretamente dentro de data[]
            if primary.get("id") and primary.get("status"):
                return primary
            nested = primary.get("order")
            if isinstance(nested, dict):
                return nested
        return (
            self._get_nested(payload, "data", "order")
            or self._get_nested(payload, "order")
            or self._get_nested(payload, "payload", "order")
        )

    def _extract_customer(self, order: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any] | None:
        return order.get("customer") or self._get_nested(payload, "data", "customer")

    def _extract_order_amount(self, order: Dict[str, Any] | None, payload: Dict[str, Any]) -> Decimal | None:
        candidates: list[Any] = []

        def push(value: Any) -> None:
            if value is not None:
                candidates.append(value)

        if isinstance(order, dict):
            push(order.get("amount"))
            push(order.get("amount_paid"))
            push(order.get("netAmount"))
            push(order.get("net_amount"))
            push(order.get("price"))
            push(order.get("baseAmount"))
            push(order.get("base_amount"))

        primary = self._primary_data(payload)
        if isinstance(primary, dict):
            push(primary.get("amount"))
            push(primary.get("netAmount"))
            push(primary.get("net_amount"))

        subscription_info = self._get_nested(payload, "data", "subscription")
        if isinstance(subscription_info, dict):
            push(subscription_info.get("amount"))
            current_period = subscription_info.get("currentPeriod") or subscription_info.get("current_period")
            if isinstance(current_period, dict):
                push(current_period.get("amount"))

        for candidate in candidates:
            decimal_value = self._to_decimal(candidate)
            if decimal_value is not None:
                return decimal_value
        return None

    def _extract_offer_id(self, order: Dict[str, Any] | None, payload: Dict[str, Any]) -> str | None:
        order_data = order or {}
        offer = order_data.get("offer") or self._get_nested(payload, "data", "offer")
        if isinstance(offer, dict):
            return self._normalize_str(offer.get("id") or offer.get("code"))
        return self._normalize_str(
            order_data.get("offer_id")
            or order_data.get("offerId")
            or self._get_nested(order_data, "offer", "id")
        )

    def _extract_product_id(self, order: Dict[str, Any] | None, payload: Dict[str, Any]) -> str | None:
        order_data = order or {}
        product = order_data.get("product") or self._get_nested(payload, "data", "product")
        if isinstance(product, dict):
            return self._normalize_str(product.get("id"))
        return None

    def _extract_session_token(self, payload: Dict[str, Any]) -> str | None:
        primary = self._primary_data(payload)
        if isinstance(primary, dict):
            token = primary.get("sck")
            if token:
                return self._normalize_str(token)
        return self._normalize_str(payload.get("sck"))

    def _extract_subscription_code(self, payload: Dict[str, Any], order: Optional[Dict[str, Any]]) -> str | None:
        subscription = self._get_nested(payload, "data", "subscription") or (order or {}).get("subscription")
        if isinstance(subscription, dict):
            return self._normalize_str(subscription.get("code") or subscription.get("id"))
        if isinstance(subscription, str):
            return self._normalize_str(subscription)
        return None

    def _extract_next_due_date(self, payload: Dict[str, Any], order: Optional[Dict[str, Any]]) -> str | None:
        candidates = [
            self._get_nested(payload, "data", "subscription", "nextDueDate"),
            self._get_nested(payload, "data", "subscription", "next_due_date"),
            self._get_nested(payload, "subscription", "nextDueDate"),
            self._get_nested(payload, "subscription", "next_due_date"),
            self._get_nested(payload, "data", "subscription", "currentPeriod", "end"),
            self._get_nested(payload, "data", "subscription", "current_period", "end"),
            self._get_nested(payload, "data", "order", "nextDueDate"),
            self._get_nested(payload, "data", "order", "next_due_date"),
        ]
        if order:
            candidates.extend(
                [
                    order.get("nextDueDate"),
                    order.get("next_due_date"),
                    order.get("dueDate"),
                    order.get("due_date"),
                ]
            )
        for candidate in candidates:
            normalized = self._normalize_str(candidate)
            if normalized:
                return normalized
        return None

    def _extract_order_id(self, payload: Dict[str, Any]) -> str | None:
        order = self._extract_order(payload)
        if not order:
            return None
        return self._normalize_str(order.get("id"))

    def _normalize_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _normalize_document(self, value: Any) -> str | None:
        normalized = self._normalize_str(value)
        if not normalized:
            return None
        digits = "".join(ch for ch in normalized if ch.isdigit())
        return digits or normalized

    def _document_column_digits(self, column):
        expression = func.coalesce(column, "")
        for char in (".", "-", "/", " ", "_"):
            expression = func.replace(expression, char, "")
        return expression

    def _get_user_by_document(self, document: str) -> Optional[User]:
        target = "".join(ch for ch in document if ch.isdigit()) or document.strip()
        if not target:
            return None
        sanitized_cpf = self._document_column_digits(User.cpf)
        sanitized_cnpj = self._document_column_digits(User.cnpj)
        return (
            self.db.query(User)
            .filter(
                or_(
                    sanitized_cpf == target,
                    sanitized_cnpj == target,
                )
            )
            .first()
        )

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    def _calculate_valid_until(self, cycle: str, due_date: str | None) -> datetime:
        normalized_cycle = (cycle or "monthly").lower()
        period = timedelta(days=32 if normalized_cycle == "monthly" else 370)
        parsed_due = self._parse_datetime(due_date)
        now = datetime.utcnow()
        if parsed_due:
            if parsed_due <= now:
                return now + period
            return parsed_due + timedelta(days=1)
        return now + period

    def _calculate_mrr_amount(self, amount: Decimal | None, cycle: str | None) -> Decimal | None:
        if amount is None:
            return None
        normalized_cycle = (cycle or "monthly").lower()
        monthly_value = amount
        if normalized_cycle == "annual":
            monthly_value = amount / Decimal("12")
        monthly_value = monthly_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if monthly_value < ZERO_DECIMAL:
            return ZERO_DECIMAL
        return monthly_value

    def _resolve_plan(self, offer_id: str | None, product_id: str | None) -> Optional[PlanMapping]:
        if not self.plan_mappings:
            return None
        normalized_offer = offer_id.strip().lower() if isinstance(offer_id, str) else None
        normalized_product = product_id.strip().lower() if isinstance(product_id, str) else None
        if normalized_offer:
            for mapping in self.plan_mappings:
                if mapping.offer_id and mapping.offer_id == normalized_offer:
                    return mapping
        if normalized_product:
            for mapping in self.plan_mappings:
                if mapping.product_id and mapping.product_id == normalized_product:
                    return mapping
        return None

    def _obtain_access_token(self) -> str:
        if self._access_token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._access_token
        if not self._token_url or not self.api_client_id or not self.api_client_secret:
            raise CaktoAPIError("Credenciais da API Cakto não configuradas.")
        payload = {
            "client_id": self.api_client_id,
            "client_secret": self.api_client_secret,
        }
        response = httpx.post(
            self._token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
            follow_redirects=True,
        )
        if response.status_code >= 400:
            raise CaktoAPIError(response.json() if response.content else {"detail": response.text})
        data = response.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        if not token:
            raise CaktoAPIError("Resposta do token Cakto sem access_token.")
        self._access_token = token
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=max(int(expires_in) - 30, 60))
        return token

    def cancel_remote_subscription(self, *, subscription_code: str | None, order_id: str | None) -> None:
        """
        Cancela a assinatura diretamente na API da Cakto.
        """
        if not self.api_base_url:
            logger.info("Cakto API não configurada. Cancelamento remoto ignorado.")
            return
        if not subscription_code and not order_id:
            raise CaktoAPIError("Nenhum identificador da assinatura Cakto foi informado.")

        payload: dict[str, str] = {}
        if subscription_code:
            payload["subscription_code"] = subscription_code
        if order_id:
            payload["order_id"] = order_id

        access_token = self._obtain_access_token()
        url = f"{self.api_base_url}/subscriptions/cancel"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = httpx.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code >= 400:
            try:
                data = response.json()
            except ValueError:
                data = {"detail": response.text}
            raise CaktoAPIError(data)

    def request_order_refund(self, *, order_id: str, reason: str | None = None) -> None:
        """
        Solicita o reembolso de um pedido na API da Cakto.
        """
        if not self.api_base_url:
            raise CaktoAPIError("Cakto API não configurada.")
        if not order_id:
            raise CaktoAPIError("order_id obrigatório para reembolso.")

        payload: dict[str, str] = {}
        if reason:
            payload["reason"] = reason

        access_token = self._obtain_access_token()
        url = f"{self.api_base_url}/orders/{order_id}/refund/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = httpx.post(url, json=payload or {}, headers=headers, timeout=30)
        if response.status_code >= 400:
            try:
                data = response.json()
            except ValueError:
                data = {"detail": response.text}
            raise CaktoAPIError(data)

    def _upsert_user_and_subscription(
        self,
        *,
        customer: Dict[str, Any],
        address: Dict[str, Any] | None,
        plan_key: str,
        cycle: str,
        offer_id: str | None,
        order_id: str | None,
        order_ref: str | None,
        subscription_code: str | None,
        valid_until: datetime | None,
    ) -> tuple[User, bool]:
        email = self._normalize_email(customer.get("email"))
        doc_number = self._normalize_document(customer.get("docNumber"))
        doc_type = (self._normalize_str(customer.get("docType")) or "cpf").lower()

        user: Optional[User] = None
        if doc_number:
            user = self._get_user_by_document(doc_number)
        if not user:
            user = (
                self.db.query(User)
                .filter(func.lower(User.email) == email)
                .first()
            )

        created = False
        if not user:
            random_password = auth_service.get_password_hash(secrets.token_urlsafe(32))
            user = User(
                email=email,
                name=customer.get("name") or "Cliente",
                hashed_password=random_password,
                cpf=doc_number if doc_number and doc_type != "cnpj" else None,
                cnpj=doc_number if doc_number and doc_type == "cnpj" else None,
                whatsapp=self._normalize_str(customer.get("phone")),
                plan=plan_key,
                is_active=True,
            )
            self.db.add(user)
            self.db.flush()
            created = True
        else:
            if user.email.lower() != email:
                conflict = (
                    self.db.query(User.id)
                    .filter(func.lower(User.email) == email)
                    .filter(User.id != user.id)
                    .first()
                )
                if not conflict:
                    user.email = email

        user.name = customer.get("name") or user.name
        phone = self._normalize_str(customer.get("phone"))
        user.whatsapp = phone or user.whatsapp
        if doc_number:
            if doc_type == "cnpj":
                if not user.cnpj or self._normalize_document(user.cnpj) != doc_number:
                    user.cnpj = doc_number
            else:
                if not user.cpf or self._normalize_document(user.cpf) != doc_number:
                    user.cpf = doc_number
        if address:
            user.address_street = address.get("street") or user.address_street
            user.address_number = address.get("number") or user.address_number
            user.address_complement = address.get("complement") or user.address_complement
            user.address_neighborhood = address.get("neighborhood") or user.address_neighborhood
            user.address_city = address.get("city") or user.address_city
            user.address_state = address.get("state") or user.address_state
            user.address_zipcode = address.get("zipcode") or user.address_zipcode

        subscription = user.subscription
        if not subscription:
            subscription = Subscription(user_id=user.id)
            self.db.add(subscription)
            self.db.flush()
            user.subscription_id = subscription.id

        subscription.plan = plan_key
        subscription.billing_cycle = cycle
        subscription.provider = "cakto"
        subscription.status = "active"
        subscription.cakto_offer_id = offer_id
        subscription.cakto_order_id = order_id
        subscription.cakto_subscription_code = subscription_code
        subscription.external_reference = order_ref or subscription_code or subscription.external_reference
        if valid_until:
            subscription.valid_until = valid_until

        user.plan = plan_key
        end_trial(user, self.db, keep_plan=plan_key)
        self.db.add_all([user, subscription])
        return user, created

    def _create_onboarding_token(
        self,
        *,
        user: User,
        plan_key: str,
        cycle: str,
        order_id: str | None,
        order_ref: str | None,
        subscription_code: str | None,
        offer_id: str | None,
    ) -> CaktoOnboardingToken:
        expiration_minutes = max(10, settings.cakto_password_token_minutes or 240)
        expires_at = datetime.utcnow() + timedelta(minutes=expiration_minutes)

        self.db.query(CaktoOnboardingToken).filter(
            CaktoOnboardingToken.user_id == user.id,
            CaktoOnboardingToken.consumed_at.is_(None),
        ).delete(synchronize_session=False)

        token = CaktoOnboardingToken(
            user_id=user.id,
            token=uuid4().hex,
            order_id=order_id,
            order_ref=order_ref,
            subscription_code=subscription_code,
            offer_id=offer_id,
            plan_key=plan_key,
            billing_cycle=cycle,
            expires_at=expires_at,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def _find_subscription(self, *, subscription_code: str | None, order_id: str | None) -> Optional[Subscription]:
        masked_sub_code = f"{subscription_code[:6]}..." if subscription_code else None
        masked_order_id = f"{order_id[:6]}..." if order_id else None
        logger.info(
            "Buscando assinatura (subscription_code=%s, order_id=%s).",
            masked_sub_code,
            masked_order_id,
        )
        if not subscription_code and not order_id:
            logger.warning("Busca abortada: nenhum identificador fornecido.")
            return None

        if subscription_code:
            logger.debug("Tentando localizar assinatura pelo subscription_code %s.", masked_sub_code)
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.cakto_subscription_code == subscription_code)
                .first()
            )
            if subscription:
                logger.info("Assinatura %s encontrada pelo subscription_code %s.", subscription.id, masked_sub_code)
                return subscription
            logger.info("Nenhuma assinatura encontrada com subscription_code %s.", masked_sub_code)

        if order_id:
            logger.debug("Tentando localizar assinatura pelo order_id %s.", masked_order_id)
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.cakto_order_id == order_id)
                .first()
            )
            if subscription:
                logger.info("Assinatura %s encontrada pelo order_id %s.", subscription.id, masked_order_id)
                return subscription
            logger.info("Nenhuma assinatura encontrada com order_id %s.", masked_order_id)

        logger.error(
            "Falha ao localizar assinatura (subscription_code=%s, order_id=%s).",
            masked_sub_code,
            masked_order_id,
        )
        return None

    def _finalize_checkout_session(
        self,
        session_token: str | None,
        *,
        order_id: str | None,
        order_ref: str | None,
        onboarding_token: CaktoOnboardingToken | None,
    ) -> None:
        if not session_token:
            return
        session = (
            self.db.query(CaktoCheckoutSession)
            .filter(CaktoCheckoutSession.token == session_token)
            .first()
        )
        if not session:
            return
        session.status = "ready"
        session.order_id = order_id
        session.order_ref = order_ref
        session.onboarding_token_id = onboarding_token.id if onboarding_token else None
        session.completed_at = datetime.utcnow()
        self.db.add(session)

    def _primary_data(self, payload: Dict[str, Any]) -> Any:
        data = payload.get("data")
        if isinstance(data, list):
            return data[0] if data else None
        return data

    def _get_nested(self, data: Dict[str, Any], *keys: str) -> Any:
        current = data
        for key in keys:
            if current is None:
                return None
            if isinstance(current, list):
                current = current[0] if current else None
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current
