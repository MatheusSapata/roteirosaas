from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.external_api_key import ExternalApiKey
from app.services.api_key_crypto import decrypt_api_key


@dataclass(slots=True)
class ProviderKey:
    record: ExternalApiKey
    plain_key: str


class FlightProviderKeyManager:
    ACTIVE_STATUSES = {"active"}

    def __init__(self, db: Session) -> None:
        self.db = db

    def has_available_key(self, provider: str = "airlabs") -> bool:
        # A key is only "available" if it can actually be decrypted and used.
        # This avoids showing lookup as enabled when stored keys are unusable.
        return bool(self.list_available_keys(provider))

    def list_available_keys(self, provider: str = "airlabs") -> list[ProviderKey]:
        rows = self._query_available(provider).all()
        keys: list[ProviderKey] = []
        dirty_rows: list[ExternalApiKey] = []
        now = datetime.now(timezone.utc)
        for row in rows:
            if self._should_auto_reset_monthly_usage(row, now):
                row.monthly_usage_estimated = 0
                row.status = "active"
                row.last_error = None
                dirty_rows.append(row)
            try:
                keys.append(ProviderKey(record=row, plain_key=decrypt_api_key(row.api_key_encrypted)))
            except Exception as exc:  # noqa: BLE001
                row.status = "error"
                row.last_error = f"Falha ao descriptografar chave: {exc}"
                dirty_rows.append(row)
        if dirty_rows:
            self.db.add_all(dirty_rows)
            self.db.commit()
        return keys

    def mark_key_success(self, record: ExternalApiKey) -> None:
        record.monthly_usage_estimated = int(record.monthly_usage_estimated or 0) + 1
        record.total_usage_estimated = int(record.total_usage_estimated or 0) + 1
        record.last_used_at = datetime.now(timezone.utc)
        record.status = "active"
        record.last_error = None
        self.db.add(record)
        self.db.commit()

    def mark_key_error(self, record: ExternalApiKey, message: str, *, quota_exceeded: bool = False) -> None:
        record.last_error = (message or "").strip()[:1000] or "Erro não especificado."
        record.status = "exhausted" if quota_exceeded else "error"
        self.db.add(record)
        self.db.commit()

    def reset_monthly_usage(self, record: ExternalApiKey) -> None:
        record.monthly_usage_estimated = 0
        if record.status in {"exhausted", "error"}:
            record.status = "active"
            record.last_error = None
        self.db.add(record)
        self.db.commit()

    def _query_available(self, provider: str):
        return (
            self.db.query(ExternalApiKey)
            .filter(
                and_(
                    ExternalApiKey.provider == provider,
                    ExternalApiKey.is_active.is_(True),
                    ExternalApiKey.status.in_(self.ACTIVE_STATUSES),
                    ExternalApiKey.monthly_usage_estimated < ExternalApiKey.monthly_limit,
                )
            )
            .order_by(ExternalApiKey.priority.asc(), ExternalApiKey.id.asc())
        )

    @staticmethod
    def _should_auto_reset_monthly_usage(record: ExternalApiKey, now: datetime) -> bool:
        if not record.reset_day:
            return False
        if not record.last_used_at:
            return False
        try:
            reset_day = max(1, min(31, int(record.reset_day)))
        except (TypeError, ValueError):
            return False

        def with_day(base: datetime) -> datetime:
            last_day = calendar.monthrange(base.year, base.month)[1]
            target_day = min(reset_day, last_day)
            return base.replace(day=target_day, hour=0, minute=0, second=0, microsecond=0)

        cycle_start = with_day(now)
        if now < cycle_start:
            previous_month_anchor = (now.replace(day=1) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            cycle_start = with_day(previous_month_anchor)
        return record.last_used_at < cycle_start and int(record.monthly_usage_estimated or 0) > 0
