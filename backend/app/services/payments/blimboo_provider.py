from __future__ import annotations

import logging
from dataclasses import asdict, replace
from typing import Any

from app.models.sale import SalePaymentStatus

from .base import PaymentCharge, PaymentChargeRequest, PaymentProvider, PaymentQuote, PaymentQuoteRequest
from .blimboo_api import BlimbooAPIClient, BlimbooAPIError
from .blimboo_mock import SimulatedBlimbooProvider

logger = logging.getLogger(__name__)


class BlimbooPaymentProvider(PaymentProvider):
    """Hybrid provider that prefers the official Blimboo API and falls back to the simulator."""

    name = "blimboo"

    def __init__(self, client: BlimbooAPIClient | None = None) -> None:
        self.client = client
        self._fallback = SimulatedBlimbooProvider()

    # region helpers
    @staticmethod
    def _normalize_payload(payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            if isinstance(payload.get("data"), dict):
                return payload["data"]
            return payload
        return {}

    def _quote_from_api(self, response: Any, request: PaymentQuoteRequest) -> PaymentQuote:
        payload = self._normalize_payload(response)
        quote_payload = payload.get("quote") if isinstance(payload.get("quote"), dict) else payload

        def _int(key: str, default: int) -> int:
            value = quote_payload.get(key)
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        currency = quote_payload.get("currency") or request.currency or "BRL"
        payment_method = quote_payload.get("payment_method") or request.payment_method
        return PaymentQuote(
            base_amount=_int("base_amount", request.base_amount),
            gross_amount=_int("gross_amount", request.base_amount),
            platform_fee_amount=_int("platform_fee_amount", 0),
            gateway_fee_estimated=_int("gateway_fee_estimated", 0),
            agency_net_amount=_int("agency_net_amount", request.base_amount),
            spread_percentage_bps=_int("spread_percentage_bps", 0),
            installment_amount=_int("installment_amount", request.base_amount // max(1, request.installments)),
            installments=_int("installments", request.installments or 1),
            payment_method=payment_method,
            currency=currency.lower(),
        )

    @staticmethod
    def _resolve_charge_metadata(payload: dict[str, Any], fallback: dict[str, Any] | None) -> dict[str, Any]:
        meta = payload.get("metadata") or payload.get("meta") or fallback or {}
        return meta if isinstance(meta, dict) else {}

    @staticmethod
    def _resolve_charge_id(payload: dict[str, Any]) -> str:
        for key in ("id", "charge_id", "reference", "provider_charge_id", "transaction_id"):
            value = payload.get(key)
            if value:
                return str(value)
        return ""

    @staticmethod
    def _resolve_status(value: Any, fallback: SalePaymentStatus = SalePaymentStatus.pending) -> SalePaymentStatus:
        if isinstance(value, SalePaymentStatus):
            return value
        if isinstance(value, str):
            normalized = value.lower()
            for candidate in SalePaymentStatus:
                if candidate.value == normalized:
                    return candidate
        return fallback

    def _api_available(self) -> bool:
        return self.client is not None

    # endregion

    def quote(self, request: PaymentQuoteRequest) -> PaymentQuote:
        if not self._api_available():
            return self._fallback.quote(request)
        payload = {
            "amount": request.base_amount,
            "currency": (request.currency or "BRL").upper(),
            "installments": request.installments,
            "payment_method": request.payment_method,
        }
        try:
            response = self.client.quote_payment(payload)
            return self._quote_from_api(response, request)
        except (BlimbooAPIError, Exception) as exc:  # pragma: no cover - depends on external API
            logger.warning("Blimboo quote via API falhou, usando simulador: %s", exc)
            return self._fallback.quote(request)

    def initialize_charge(self, request: PaymentChargeRequest) -> PaymentCharge:
        if not self._api_available():
            return self._fallback.initialize_charge(request)
        payload = {
            "amount": request.base_amount,
            "currency": (request.currency or "BRL").upper(),
            "installments": request.installments,
            "payment_method": request.payment_method,
            "metadata": request.metadata or {},
        }
        try:
            response = self.client.create_charge(payload)
            payload = self._normalize_payload(response)
            quote = self._quote_from_api(payload, request)
            provider_charge_id = self._resolve_charge_id(payload) or quote.payment_method
            provider_status = self._resolve_status(payload.get("status") or payload.get("provider_status"))
            metadata = self._resolve_charge_metadata(payload, request.metadata)
            return PaymentCharge(
                **asdict(quote),
                provider=self.name,
                provider_charge_id=provider_charge_id,
                provider_status=provider_status,
                metadata=metadata,
            )
        except (BlimbooAPIError, Exception) as exc:  # pragma: no cover - depends on external API
            logger.warning("Falha ao criar cobranca na Blimboo, usando simulador: %s", exc)
            return self._fallback.initialize_charge(request)

    def update_status(self, charge: PaymentCharge, status: SalePaymentStatus) -> PaymentCharge:
        if not self._api_available() or not charge.provider_charge_id:
            return self._fallback.update_status(charge, status)
        try:
            response = self.client.update_charge_status(charge.provider_charge_id, status.value)
            payload = self._normalize_payload(response) if response else {}
            provider_status = self._resolve_status(payload.get("status") or payload.get("provider_status") or status, status)
            metadata = self._resolve_charge_metadata(payload, charge.metadata)
            return replace(charge, provider_status=provider_status, metadata=metadata)
        except (BlimbooAPIError, Exception) as exc:  # pragma: no cover
            logger.warning("Falha ao atualizar status na Blimboo, usando simulador: %s", exc)
            return self._fallback.update_status(charge, status)
