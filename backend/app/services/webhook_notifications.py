from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.webhook_notification import WebhookNotificationRule
from app.schemas.webhook_notification import WebhookNotificationMetaIcon


AVAILABLE_ICON_OPTIONS: list[WebhookNotificationMetaIcon] = [
    WebhookNotificationMetaIcon(tag="rocket", label="Foguete", emoji="🚀"),
    WebhookNotificationMetaIcon(tag="arrow_up", label="Seta para cima", emoji="⬆️"),
    WebhookNotificationMetaIcon(tag="heavy_check_mark", label="Confirmado", emoji="✔️"),
    WebhookNotificationMetaIcon(tag="loudspeaker", label="Aviso", emoji="📢"),
    WebhookNotificationMetaIcon(tag="warning", label="Alerta", emoji="⚠️"),
    WebhookNotificationMetaIcon(tag="rotating_light", label="Urgente", emoji="🚨"),
    WebhookNotificationMetaIcon(tag="skull", label="Cancelamento", emoji="💀"),
    WebhookNotificationMetaIcon(tag="moneybag", label="Financeiro", emoji="💰"),
    WebhookNotificationMetaIcon(tag="tada", label="Celebração", emoji="🎉"),
    WebhookNotificationMetaIcon(tag="partying_face", label="Comemoração", emoji="🥳"),
]


DEFAULT_AVAILABLE_FIELDS = [
    "event_label",
    "user_name",
    "amount",
    "payment_method",
    "plan_name",
    "offer_name",
    "previous_plan_name",
    "upgraded_plan_name",
    "cancelled_item",
    "occurred_at",
]


DEFAULT_WEBHOOK_RULES: list[dict[str, Any]] = [
    {
        "event_key": "subscription_created",
        "display_name": "Nova assinatura",
        "description": "Dispara quando a assinatura é criada.",
        "enabled": True,
        "title_template": "Assinatura criada - {{plan_name}}",
        "body_template": "{{amount}} | {{user_name}} | {{payment_method}}",
        "icon_tag": "rocket",
        "priority": 3,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 10,
        "is_builtin": True,
    },
    {
        "event_key": "subscription_renewed",
        "display_name": "Assinatura renovada",
        "description": "Dispara quando a renovação é confirmada.",
        "enabled": True,
        "title_template": "Assinatura renovada - {{plan_name}}",
        "body_template": "{{amount}} | {{user_name}} | {{payment_method}}",
        "icon_tag": "heavy_check_mark",
        "priority": 3,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 20,
        "is_builtin": True,
    },
    {
        "event_key": "subscription_cancelled",
        "display_name": "Assinatura cancelada",
        "description": "Dispara quando a assinatura é cancelada.",
        "enabled": True,
        "title_template": "Assinatura cancelada - {{plan_name}}",
        "body_template": "{{amount}} | {{user_name}}",
        "icon_tag": "skull",
        "priority": 3,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 30,
        "is_builtin": True,
    },
    {
        "event_key": "upgrade_realizado",
        "display_name": "Upgrade realizado",
        "description": "Dispara quando uma assinatura faz upgrade.",
        "enabled": True,
        "title_template": "Upgrade realizado - {{previous_plan_name}} para {{upgraded_plan_name}}",
        "body_template": "{{amount}} | {{user_name}}",
        "icon_tag": "arrow_up",
        "priority": 3,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 40,
        "is_builtin": True,
    },
]


def _render_template(template: str, context: dict[str, Any]) -> str:
    pattern = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")

    def resolve(key: str) -> str:
        current: Any = context
        for part in key.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
            if current is None:
                return ""
        return str(current)

    return pattern.sub(lambda match: resolve(match.group(1)), template or "").strip()


def _default_context(value: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(value or {})
    payload.setdefault("event_label", payload.get("event_key") or "Evento")
    payload.setdefault("user_name", "Não informado")
    payload.setdefault("amount", "R$ 0,00")
    payload.setdefault("payment_method", "Não informado")
    payload.setdefault("plan_name", "Plano")
    payload.setdefault("offer_name", "")
    payload.setdefault("previous_plan_name", "Plano anterior")
    payload.setdefault("upgraded_plan_name", "Novo plano")
    payload.setdefault("cancelled_item", "")
    payload.setdefault("occurred_at", "")
    return payload


@contextmanager
def _session_scope(db: Session | None = None):
    if db is not None:
        yield db
        return
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_default_rules(db: Session) -> None:
    existing = {row.event_key for row in db.query(WebhookNotificationRule.event_key).all()}
    created = False
    for row in DEFAULT_WEBHOOK_RULES:
        if row["event_key"] in existing:
            continue
        db.add(WebhookNotificationRule(**row))
        created = True
    if created:
        db.commit()


def list_rules(db: Session) -> list[WebhookNotificationRule]:
    ensure_default_rules(db)
    return (
        db.query(WebhookNotificationRule)
        .order_by(WebhookNotificationRule.sort_order.asc(), WebhookNotificationRule.id.asc())
        .all()
    )


def get_rule(db: Session, rule_id: int) -> WebhookNotificationRule | None:
    ensure_default_rules(db)
    return db.query(WebhookNotificationRule).filter(WebhookNotificationRule.id == rule_id).first()


def get_rule_by_event_key(db: Session, event_key: str) -> WebhookNotificationRule | None:
    ensure_default_rules(db)
    normalized = str(event_key or "").strip()
    if not normalized:
        return None
    return db.query(WebhookNotificationRule).filter(WebhookNotificationRule.event_key == normalized).first()


def upsert_rule(db: Session, *, payload: dict[str, Any], rule_id: int | None = None) -> WebhookNotificationRule:
    ensure_default_rules(db)
    if rule_id is not None:
        rule = get_rule(db, rule_id)
        if not rule:
            raise ValueError("Regra não encontrada.")
        for key, value in payload.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    rule = WebhookNotificationRule(**payload)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int) -> None:
    rule = get_rule(db, rule_id)
    if not rule:
        return
    db.delete(rule)
    db.commit()


def build_rendered_notification(rule: WebhookNotificationRule, context: dict[str, Any] | None = None) -> tuple[str, str, list[str]]:
    payload = _default_context(context)
    payload["event_key"] = rule.event_key
    title = _render_template(rule.title_template, payload)
    body = _render_template(rule.body_template, payload)
    tags = [rule.icon_tag] if rule.icon_tag else []
    return title, body, tags


def send_notification(
    *,
    event_key: str,
    context: dict[str, Any] | None = None,
    db: Session | None = None,
) -> bool:
    payload = _default_context(context)
    payload["event_key"] = event_key
    with _session_scope(db) as session:
        rule = get_rule_by_event_key(session, event_key)
        if not rule or not rule.enabled:
            return False
        title, body, tags = build_rendered_notification(rule, payload)
        from app.services.ntfy import NtfyService  # local import avoids circular dependency

        client = NtfyService(default_topic=rule.topic or None)
        client.publish(
            topic=rule.topic or client.default_topic,
            title=title,
            message=body,
            priority=rule.priority,
            tags=tags,
        )
        return True


def test_notification(
    *,
    rule_id: int,
    context: dict[str, Any] | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    with _session_scope(db) as session:
        rule = get_rule(session, rule_id)
        if not rule:
            raise ValueError("Regra não encontrada.")
        payload = _default_context(context)
        payload["event_key"] = rule.event_key
        title, body, tags = build_rendered_notification(rule, payload)
        from app.services.ntfy import NtfyService  # local import avoids circular dependency

        client = NtfyService(default_topic=rule.topic or None)
        client.publish(
            topic=rule.topic or client.default_topic,
            title=title,
            message=body,
            priority=rule.priority,
            tags=tags,
        )
        return {"title": title, "body": body, "tags": tags}
