from __future__ import annotations

from .blimboo_mock import SimulatedBlimbooProvider, provider

__all__ = ["provider", "get_payment_provider", "SimulatedBlimbooProvider"]


def get_payment_provider() -> SimulatedBlimbooProvider:
    return provider
