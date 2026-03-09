from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone, time
from typing import Dict

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.user import User
from app.services.viajechat import ViajeChatClient, ViajeChatClientError

logger = logging.getLogger(__name__)


def _get_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        logger.warning("Timezone %s not found. Falling back to UTC.", name)
        return ZoneInfo("UTC")


def _days_until(trial_ends_at: datetime, reference: datetime, tz: ZoneInfo) -> int:
    end_local = trial_ends_at.astimezone(tz)
    return (end_local.date() - reference.date()).days


def tag_trial_users(now: datetime | None = None) -> Dict[int, int]:
    """
    Procura usuários em trial e adiciona tags no ViajeChat quando faltarem 5, 3 ou 1 dia
    e também quando completar 1 dia de atraso após o vencimento.
    Retorna um dict com quantidade processada por faixa de dias.
    """
    settings = get_settings()
    tag_map = {
        5: settings.viajechat_tag_trial_5days,
        3: settings.viajechat_tag_trial_3days,
        1: settings.viajechat_tag_trial_1day,
        -1: settings.viajechat_tag_trial_overdue,
    }
    tag_map = {days: tag for days, tag in tag_map.items() if tag}
    if not settings.viajechat_api_key or not tag_map:
        logger.debug("Pulando job de etiquetas trial. API key ou tags não configuradas.")
        return {}

    tz = _get_timezone(settings.trial_tag_job_timezone or "UTC")
    reference = (now or datetime.now(timezone.utc)).astimezone(tz)
    min_days = min(tag_map.keys())
    max_days = max(tag_map.keys())
    window_start_local = datetime.combine(
        reference.date() + timedelta(days=min_days),
        time.min,
        tzinfo=tz,
    )
    window_end_local = datetime.combine(
        reference.date() + timedelta(days=max_days + 1),
        time.min,
        tzinfo=tz,
    )
    lower_bound = window_start_local.astimezone(timezone.utc)
    upper_bound = window_end_local.astimezone(timezone.utc)

    client = ViajeChatClient(settings.viajechat_api_key, settings.viajechat_api_base_url)
    db = SessionLocal()
    counters: Dict[int, int] = {days: 0 for days in tag_map}
    try:
        candidates = (
            db.query(User)
            .filter(
                User.trial_plan.isnot(None),
                User.trial_ends_at.isnot(None),
                User.trial_blocked.is_(False),
                User.email.isnot(None),
                User.trial_ends_at >= lower_bound,
                User.trial_ends_at < upper_bound,
            )
            .all()
        )
        for user in candidates:
            if not user.email or not user.trial_ends_at:
                continue
            days_left = _days_until(user.trial_ends_at, reference, tz)
            tag_id = tag_map.get(days_left)
            if not tag_id:
                continue
            try:
                added = client.add_tags_to_contact_by_email(user.email, [tag_id])
                if added:
                    counters[days_left] += 1
            except ViajeChatClientError:
                logger.exception(
                    "Erro ao adicionar tag trial para usuário %s (dias_restantes=%s)", user.id, days_left
                )
    finally:
        db.close()
    return counters


def schedule_trial_tag_job() -> None:
    """Agenda a rotina diária que executa no horário configurado (timezone configurável)."""
    settings = get_settings()
    hour = settings.trial_tag_job_hour
    minute = settings.trial_tag_job_minute
    timezone_name = settings.trial_tag_job_timezone

    async def _loop() -> None:
        tz = _get_timezone(timezone_name)
        while True:
            now = datetime.now(tz)
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            try:
                result = tag_trial_users()
                if result:
                    logger.info("Etiquetas trial executadas: %s", result)
            except Exception:
                logger.exception("Erro ao executar job diário de etiquetas trial.")

    try:
        asyncio.get_event_loop().create_task(_loop())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(_loop())
