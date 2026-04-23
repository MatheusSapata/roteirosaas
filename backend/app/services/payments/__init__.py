from __future__ import annotations

from app.core.config import get_settings

from .blimboo_api import BlimbooAPIClient
from .blimboo_provider import BlimbooPaymentProvider

settings = get_settings()


def _build_api_client(api_token: str | None) -> BlimbooAPIClient | None:
    base_url = settings.blimboo_api_base_url
    token = api_token or settings.blimboo_api_token
    if not base_url or not token:
        return None
    try:
        return BlimbooAPIClient(base_url, token)
    except ValueError:
        return None


def get_payment_provider(api_token: str | None = None) -> BlimbooPaymentProvider:
    client = _build_api_client(api_token)
    return BlimbooPaymentProvider(client=client)


provider = get_payment_provider()

__all__ = ["provider", "get_payment_provider", "BlimbooPaymentProvider", "BlimbooAPIClient"]
