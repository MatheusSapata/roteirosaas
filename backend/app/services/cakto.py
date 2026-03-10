from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cakto import CaktoEventLog, CaktoOnboardingToken
from app.models.subscription import Subscription
from app.models.user import User
from app.services import auth as auth_service
from app.services.trial import end_trial

logger = logging.getLogger(__name__)
settings = get_settings()


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

    def _load_plan_mappings(self) -> list[PlanMapping]:
        mappings: list[PlanMapping] = []
        for plan_key, cycle, offer_attr, product_attr in PLAN_ENV_SPECS:
            offer_id = getattr(settings, offer_attr, None)
            product_id = getattr(settings, product_attr, None)
            if offer_id or product_id:
                mappings.append(PlanMapping(plan_key, cycle, offer_id, product_id))
        return mappings

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

        user, created = self._upsert_user_and_subscription(
            customer=customer,
            address=order.get("address"),
            plan_key=plan.plan_key,
            cycle=plan.cycle,
            offer_id=offer_id,
            order_id=order_id,
            order_ref=order_ref,
            subscription_code=subscription_code,
        )

        if created:
            self._create_onboarding_token(
                user=user,
                plan_key=plan.plan_key,
                cycle=plan.cycle,
                order_id=order_id,
                order_ref=order_ref,
                subscription_code=subscription_code,
                offer_id=offer_id,
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
        for mapping in self.plan_mappings:
            if mapping.offer_id and offer_id and mapping.offer_id == offer_id:
                return mapping
            if mapping.product_id and product_id and mapping.product_id == product_id:
                return mapping
        return None

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
    ) -> None:
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

    def _find_subscription(self, *, subscription_code: str | None, order_id: str | None) -> Optional[Subscription]:
        if not subscription_code and not order_id:
            return None
        query = self.db.query(Subscription)
        if subscription_code:
            query = query.filter(Subscription.cakto_subscription_code == subscription_code)
        if order_id:
            query = query.filter(Subscription.cakto_order_id == order_id)
        return query.first()

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
