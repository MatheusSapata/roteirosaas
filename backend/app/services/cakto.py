from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
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
from app.services.trial import end_trial

logger = logging.getLogger(__name__)
settings = get_settings()


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
            base_for_token = self.api_base_url
            if base_for_token.endswith("/v1"):
                base_for_token = base_for_token[:-3]
            self._token_url = f"{base_for_token}/oauth/token/"

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
        order_id = self._normalize_str(order.get("id"))
        order_ref = self._normalize_str(order.get("refId"))

        user, _created = self._upsert_user_and_subscription(
            customer=customer,
            address=order.get("address"),
            plan_key=plan.plan_key,
            cycle=plan.cycle,
            offer_id=offer_id,
            order_id=order_id,
            order_ref=order_ref,
            subscription_code=subscription_code,
        )

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

        subscription.status = status
        subscription.updated_at = datetime.utcnow()
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

    def _extract_offer_id(self, order: Dict[str, Any], payload: Dict[str, Any]) -> str | None:
        offer = order.get("offer") or self._get_nested(payload, "data", "offer")
        if isinstance(offer, dict):
            return self._normalize_str(offer.get("id") or offer.get("code"))
        return self._normalize_str(
            order.get("offer_id")
            or order.get("offerId")
            or self._get_nested(order, "offer", "id")
        )

    def _extract_product_id(self, order: Dict[str, Any], payload: Dict[str, Any]) -> str | None:
        product = order.get("product") or self._get_nested(payload, "data", "product")
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
            "grant_type": "client_credentials",
        }
        response = httpx.post(
            self._token_url,
            data=payload,
            timeout=30,
            follow_redirects=True,
            auth=(self.api_client_id, self.api_client_secret),
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
    ) -> tuple[User, bool]:
        email = self._normalize_str(customer.get("email"))
        if not email:
            raise ValueError("Pedido sem e-mail do cliente.")
        user = self.db.query(User).filter(User.email == email).first()
        created = False
        if not user:
            random_password = auth_service.get_password_hash(secrets.token_urlsafe(32))
            user = User(
                email=email.lower(),
                name=customer.get("name") or "Cliente",
                hashed_password=random_password,
                cpf=self._normalize_str(customer.get("docNumber")),
                whatsapp=self._normalize_str(customer.get("phone")),
                plan=plan_key,
                is_active=True,
            )
            self.db.add(user)
            self.db.flush()
            created = True

        user.name = customer.get("name") or user.name
        user.whatsapp = self._normalize_str(customer.get("phone")) or user.whatsapp
        doc_number = self._normalize_str(customer.get("docNumber"))
        if doc_number and not user.cpf:
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
        if not subscription_code and not order_id:
            return None
        query = self.db.query(Subscription)
        if subscription_code:
            query = query.filter(Subscription.cakto_subscription_code == subscription_code)
        if order_id:
            query = query.filter(Subscription.cakto_order_id == order_id)
        return query.first()

    def _finalize_checkout_session(
        self,
        session_token: str | None,
        *,
        order_id: str | None,
        order_ref: str | None,
        onboarding_token: CaktoOnboardingToken,
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
        session.onboarding_token_id = onboarding_token.id
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
            if isinstance(current, list):
                current = current[0] if current else None
            elif isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if current is None:
                return None
        return current
