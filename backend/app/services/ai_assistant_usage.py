from __future__ import annotations

from datetime import datetime, timezone
from calendar import monthrange

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ai_assistant_usage import AiAssistantUsage
from app.models.user import User
from app.services.plans import effective_plan

AI_ASSISTANT_MONTHLY_LIMITS: dict[str, int | None] = {
    "free": 0,
    "teste": 5000,
    "essencial": 50,
    "growth": 100,
    "infinity": 150,
}

PLAN_ALIASES: dict[str, str] = {
    "trial": "teste",
    "professional": "essencial",
    "profissional": "essencial",
    "agency": "growth",
    "agencia": "growth",
    "scale": "infinity",
    "escala": "infinity",
    "test": "teste",
}


def normalize_ai_assistant_plan(plan: str | None) -> str:
    normalized = str(plan or "").strip().lower()
    return PLAN_ALIASES.get(normalized, normalized or "free")


def get_ai_assistant_monthly_limit(user: User) -> int | None:
    if getattr(user, "is_superuser", False):
        return None
    plan_key = normalize_ai_assistant_plan(effective_plan(user))
    return AI_ASSISTANT_MONTHLY_LIMITS.get(plan_key, AI_ASSISTANT_MONTHLY_LIMITS["free"])


def get_ai_assistant_period_key(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).strftime("%Y-%m")


def get_ai_assistant_renewal_at(period_key: str | None = None) -> datetime:
    key = period_key or get_ai_assistant_period_key()
    try:
        year_str, month_str = key.split("-", 1)
        year = int(year_str)
        month = int(month_str)
    except (ValueError, TypeError):
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month

    if month >= 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    day = 1
    return datetime(next_year, next_month, day, 0, 0, 0, tzinfo=timezone.utc)


def get_ai_assistant_usage_record(db: Session, user_id: int, period_key: str) -> AiAssistantUsage:
    record = (
        db.query(AiAssistantUsage)
        .filter(
            AiAssistantUsage.user_id == user_id,
            AiAssistantUsage.period_key == period_key,
        )
        .first()
    )
    if record:
        return record

    record = AiAssistantUsage(user_id=user_id, period_key=period_key, message_count=0)
    db.add(record)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        record = (
            db.query(AiAssistantUsage)
            .filter(
                AiAssistantUsage.user_id == user_id,
                AiAssistantUsage.period_key == period_key,
            )
            .first()
        )
        if record:
            return record
        raise
    return record


def check_ai_assistant_message_limit(db: Session, user: User) -> tuple[AiAssistantUsage, int | None]:
    period_key = get_ai_assistant_period_key()
    usage = (
        db.query(AiAssistantUsage)
        .filter(
            AiAssistantUsage.user_id == user.id,
            AiAssistantUsage.period_key == period_key,
        )
        .first()
    )
    if usage is None:
        usage = AiAssistantUsage(user_id=user.id, period_key=period_key, message_count=0)
    limit = get_ai_assistant_monthly_limit(user)
    used = int(usage.message_count or 0)

    if limit is not None and used >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Seu plano atingiu o limite mensal de {limit} mensagem(ns) na Ajuda IA. "
                "Aguarde o próximo ciclo ou faça upgrade."
            ),
            headers={
                "X-AI-Assistant-Limit": str(limit),
                "X-AI-Assistant-Usage": str(used),
                "X-AI-Assistant-Remaining": "0",
                "X-AI-Assistant-Period": period_key,
            },
        )

    return usage, limit


def increment_ai_assistant_message_usage(db: Session, usage: AiAssistantUsage) -> AiAssistantUsage:
    if usage.id is None:
        usage = get_ai_assistant_usage_record(db, usage.user_id, usage.period_key)
    usage.message_count = int(usage.message_count or 0) + 1
    db.add(usage)
    db.flush()
    return usage


def get_ai_assistant_usage_summary(db: Session, user: User) -> dict[str, int | str | None | datetime]:
    period_key = get_ai_assistant_period_key()
    usage = (
        db.query(AiAssistantUsage)
        .filter(
            AiAssistantUsage.user_id == user.id,
            AiAssistantUsage.period_key == period_key,
        )
        .first()
    )
    limit = get_ai_assistant_monthly_limit(user)
    used = int(usage.message_count or 0) if usage else 0
    remaining = None if limit is None else max(int(limit) - used, 0)
    return {
        "period_key": period_key,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "unlimited": limit is None,
        "renewal_at": get_ai_assistant_renewal_at(period_key),
    }
