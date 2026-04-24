from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class FlightProviderInterface(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def supports_future_lookup(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def lookup_flight_by_number(self, api_key: str, flight_number: str, flight_date: date) -> dict[str, Any]:
        raise NotImplementedError
