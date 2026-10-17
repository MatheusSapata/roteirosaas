from __future__ import annotations

import logging
import re
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import session as db_session
from app.models.pushover_account import PushoverAccount
from app.models.webhook_notification import WebhookNotificationRule
from app.schemas.webhook_notification import WebhookNotificationMetaIcon
from app.services.api_key_crypto import decrypt_api_key, encrypt_api_key, extract_api_key_last4
from app.services import pushover

logger = logging.getLogger(__name__)


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
    "purchase_kind",
    "customer_email",
    "customer_phone",
    "due_date",
]

# Eventos novos chegam pelo Pushover; no ntfy (tópico das assinaturas) começam desligados.
SALES_EVENT_KEYS = ("purchase_approved", "checkout_started", "payment_overdue")

# Som de receita nova no Pushover: o som personalizado "viajeonvenda", cadastrado na conta dona do
# aplicativo (a do token), que toca para todas as contas. Evento sem som escolhido na tela usa este
# padrão; os outros eventos tocam o som padrão do app.
REVENUE_SOUND = "viajeonvenda"
REVENUE_EVENT_KEYS = ("purchase_approved", "subscription_created", "subscription_renewed", "upgrade_realizado")


def default_pushover_sound(event_key: str) -> str | None:
    return REVENUE_SOUND if event_key in REVENUE_EVENT_KEYS else None


def pushover_sound_for(rule: WebhookNotificationRule) -> str | None:
    """O som escolhido na tela; sem escolha, o padrão do evento."""
    return (rule.pushover_sound or "").strip() or default_pushover_sound(rule.event_key)


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
    {
        "event_key": "gateway_modified_cakto_asaas",
        "display_name": "Gateway modificado Cakto -> Asaas",
        "description": "Dispara quando a assinatura antiga em Cakto passa a operar no fluxo Asaas.",
        "enabled": True,
        "title_template": "GATEWAY MODIFICADO CAKTO -> ASAAS",
        "body_template": "{{user_name}}",
        "icon_tag": "arrow_up",
        "priority": 3,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 50,
        "is_builtin": True,
    },
    {
        "event_key": "purchase_approved",
        "display_name": "Compra aprovada",
        "description": "Pagamento aprovado: assinatura nova, renovação ou upgrade (qualquer forma de pagamento).",
        "enabled": True,
        "ntfy_enabled": False,
        "title_template": "Compra aprovada - {{plan_name}}",
        "body_template": "{{amount}} | {{user_name}} | {{payment_method}} | {{purchase_kind}}",
        "icon_tag": "moneybag",
        "priority": 4,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 60,
        "is_builtin": True,
    },
    {
        "event_key": "checkout_started",
        "display_name": "Checkout iniciado",
        "description": "A pessoa preencheu os dados no checkout (ainda sem pagar). Uma vez por pessoa e oferta a cada 3 horas.",
        "enabled": True,
        "ntfy_enabled": False,
        "title_template": "Checkout iniciado - {{plan_name}}",
        "body_template": "{{user_name}} | {{customer_phone}} | {{amount}}",
        "icon_tag": "loudspeaker",
        "priority": 3,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 70,
        "is_builtin": True,
    },
    {
        "event_key": "payment_overdue",
        "display_name": "Cobrança vencida não paga",
        "description": "Cobrança passou do vencimento sem pagamento: renovação de quem já assina ou a primeira cobrança de uma compra não concluída.",
        "enabled": True,
        "ntfy_enabled": False,
        "title_template": "Cobrança vencida - {{plan_name}}",
        "body_template": "{{amount}} | {{user_name}} | venceu {{due_date}} | {{purchase_kind}}",
        "icon_tag": "warning",
        "priority": 4,
        "topic": "roteiro_online_assinaturas",
        "sort_order": 80,
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
    payload.setdefault("purchase_kind", "")
    payload.setdefault("customer_email", "")
    payload.setdefault("customer_phone", "")
    payload.setdefault("due_date", "")
    return payload


@contextmanager
def _session_scope(db: Session | None = None):
    if db is not None:
        yield db
        return
    session = db_session.SessionLocal()  # lida na hora (os testes trocam o banco)
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
    missing = [row for row in DEFAULT_WEBHOOK_RULES if row["event_key"] not in existing]
    if not missing:
        return
    for row in missing:
        try:
            with db.begin_nested():
                db.add(WebhookNotificationRule(**row))
        except IntegrityError:
            pass  # outra requisição criou o mesmo evento ao mesmo tempo
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


def contact_context(email: str | None, phone: str | None) -> dict[str, str]:
    """E-mail e telefone do cliente para o aviso, com o link do WhatsApp (o Pushover abre a conversa)."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) in (10, 11):
        digits = f"55{digits}"
    shown = ""
    if len(digits) in (12, 13) and digits.startswith("55"):
        local = digits[2:]
        shown = f"({local[:2]}) {local[2:-4]}-{local[-4:]}"
    elif digits:
        shown = f"+{digits}"
    return {
        "customer_email": (email or "").strip(),
        "customer_phone": shown,
        "whatsapp_url": f"https://wa.me/{digits}" if len(digits) >= 12 else "",
    }


def _date_br(value: Any) -> str:
    text = str(value or "").strip()[:10]
    try:
        return datetime.fromisoformat(text).strftime("%d/%m/%Y") if text else ""
    except ValueError:
        return text


def notify_payment_overdue(
    *,
    user_name: str | None,
    plan_name: str | None,
    amount: Any,
    due_date: Any,
    payment_method: str | None,
    kind: str,
    email: str | None = None,
    phone: str | None = None,
    dedupe_key: str | None = None,
) -> None:
    """Cobrança vencida sem pagamento (o gateway pode reenviar o aviso: sai uma vez por cobrança)."""
    from app.services.ntfy import format_brl  # local import avoids circular dependency

    notify_safely(
        event_key="payment_overdue",
        context={
            "event_label": "Cobrança vencida",
            "user_name": user_name or "Não informado",
            "plan_name": plan_name or "Plano",
            "amount": format_brl(amount),
            "payment_method": payment_method or "Não informado",
            "due_date": _date_br(due_date),
            "purchase_kind": kind,
            **contact_context(email, phone),
        },
        dedupe_key=dedupe_key,
    )


def _icon_emoji(tag: str | None) -> str:
    return next((icon.emoji for icon in AVAILABLE_ICON_OPTIONS if icon.tag == tag), "")


def _accounts_for(session: Session, event_key: str, *, only: int | None = None) -> list[PushoverAccount]:
    query = session.query(PushoverAccount).filter(PushoverAccount.enabled.is_(True))
    if only is not None:
        query = query.filter(PushoverAccount.id == only)
    return [account for account in query.order_by(PushoverAccount.id.asc()).all() if event_key in (account.event_keys or [])]


def send_to_pushover_account(
    account: PushoverAccount,
    *,
    title: str,
    body: str,
    priority: int,
    context: dict[str, Any] | None = None,
    sound: str | None = None,
) -> str | None:
    """Manda para uma conta e guarda na conta quando foi o último envio (ou o último erro). Devolve
    um aviso quando o som escolhido não existe e o aviso saiu com o som padrão."""
    context = context or {}
    message = {
        "app_token": decrypt_api_key(account.app_token_encrypted),
        "user_key": decrypt_api_key(account.user_key_encrypted),
        "title": title,
        "message": body,
        "priority": priority,
        "device": account.device or None,
        # Checkout iniciado e cobrança vencida: o aviso abre a conversa com o cliente.
        "url": context.get("whatsapp_url") or None,
        "url_title": "Chamar no WhatsApp" if context.get("whatsapp_url") else None,
    }
    note = None
    try:
        try:
            pushover.send_message(**message, sound=sound or None)
        except pushover.PushoverError as exc:
            if not sound or "sound" not in str(exc).lower():
                raise
            # Som personalizado que o Pushover não achou: o aviso sai com o som padrão do app.
            pushover.send_message(**message)
            note = f'O som "{sound}" não está no Pushover da conta dona do aplicativo; o aviso tocou o som padrão.'
    except Exception as exc:
        account.last_error = str(exc)[:500]
        raise
    account.last_error = note
    account.last_sent_at = datetime.now(timezone.utc)
    return note


def _deliver(session: Session, rule: WebhookNotificationRule, context: dict[str, Any]) -> list[dict[str, Any]]:
    """Manda pelo ntfy (se ligado na regra) e para cada conta do Pushover que escolheu o evento.
    Um canal com erro não impede os outros. Devolve o resultado de cada envio."""
    title, body, tags = build_rendered_notification(rule, context)
    results: list[dict[str, Any]] = []
    if rule.ntfy_enabled:
        from app.services.ntfy import NtfyService  # local import avoids circular dependency

        client = NtfyService(default_topic=rule.topic or None)
        target = rule.topic or client.default_topic
        try:
            client.publish(topic=target, title=title, message=body, priority=rule.priority, tags=tags)
            results.append({"channel": "ntfy", "target": target, "ok": True})
        except Exception as exc:  # noqa: BLE001 - um canal com erro não derruba os outros
            logger.warning("notification_ntfy_failed event=%s error=%s", rule.event_key, exc)
            results.append({"channel": "ntfy", "target": target, "ok": False, "error": str(exc)[:300]})
    emoji = _icon_emoji(rule.icon_tag)
    push_title = f"{emoji} {title}".strip() if emoji else title
    for account in _accounts_for(session, rule.event_key):
        try:
            note = send_to_pushover_account(
                account, title=push_title, body=body, priority=rule.priority, context=context, sound=pushover_sound_for(rule)
            )
            results.append({"channel": "pushover", "target": account.name, "ok": True, "error": note})
        except Exception as exc:  # noqa: BLE001
            logger.warning("notification_pushover_failed event=%s account=%s error=%s", rule.event_key, account.id, exc)
            results.append({"channel": "pushover", "target": account.name, "ok": False, "error": str(exc)[:300]})
    return results


# Mesmo aviso repetido (o gateway reenvia o webhook, a pessoa volta ao checkout): só o primeiro sai.
_RECENT: dict[str, float] = {}
_RECENT_LOCK = threading.Lock()


def _seen_recently(key: str, ttl_seconds: int) -> bool:
    now = time.monotonic()
    with _RECENT_LOCK:
        for old_key, expires in list(_RECENT.items()):
            if expires < now:
                _RECENT.pop(old_key, None)
        if key in _RECENT:
            return True
        _RECENT[key] = now + ttl_seconds
        return False


def send_notification(
    *,
    event_key: str,
    context: dict[str, Any] | None = None,
    db: Session | None = None,
    dedupe_key: str | None = None,
    dedupe_seconds: int = 48 * 3600,
) -> bool:
    payload = _default_context(context)
    payload["event_key"] = event_key
    if dedupe_key and _seen_recently(f"{event_key}:{dedupe_key}", dedupe_seconds):
        return False
    with _session_scope(db) as session:
        rule = get_rule_by_event_key(session, event_key)
        if not rule or not rule.enabled:
            return False
        results = _deliver(session, rule, payload)
        return any(item["ok"] for item in results)


# Os avisos saem em segundo plano: o checkout e os webhooks não esperam o ntfy nem o Pushover.
# Os testes desligam para conferir o envio na hora.
RUN_IN_BACKGROUND = True


def notify_safely(**kwargs: Any) -> None:
    """Aviso que não pode atrapalhar o pagamento: sai em segundo plano e erro só vai para o log."""

    def run() -> None:
        try:
            send_notification(**kwargs)
        except Exception:  # noqa: BLE001
            logger.exception("notification_failed event=%s", kwargs.get("event_key"))

    if RUN_IN_BACKGROUND:
        threading.Thread(target=run, name="notification", daemon=True).start()
    else:
        run()


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
        results = _deliver(session, rule, payload)
        session.commit()
        return {"title": title, "body": body, "tags": tags, "deliveries": results}


# Contas do Pushover (Admin Master)


def list_pushover_accounts(db: Session) -> list[PushoverAccount]:
    return db.query(PushoverAccount).order_by(PushoverAccount.id.asc()).all()


def _clean_event_keys(db: Session, event_keys: list[str] | None) -> list[str]:
    known = {rule.event_key for rule in list_rules(db)}
    return [key for key in dict.fromkeys(event_keys or []) if key in known]


def save_pushover_account(db: Session, payload: dict[str, Any], account: PushoverAccount | None = None) -> PushoverAccount:
    """Cria ou altera uma conta. Chave e token em branco na alteração: ficam os atuais. Na conta
    nova, token em branco usa o do aplicativo já cadastrado (um aplicativo serve para todas).
    A chave é conferida com o Pushover antes de salvar."""
    user_key = "".join(str(payload.get("user_key") or "").split())
    app_token = "".join(str(payload.get("app_token") or "").split())
    device = str(payload.get("device") or "").strip() or None
    if account is None:
        if not user_key:
            raise ValueError("Informe a chave do usuário (User Key) do Pushover.")
        if not app_token:
            previous = db.query(PushoverAccount).order_by(PushoverAccount.id.desc()).first()
            if previous is None:
                raise ValueError("Informe o token do aplicativo (API Token) do Pushover.")
            app_token = decrypt_api_key(previous.app_token_encrypted)
        account = PushoverAccount(event_keys=list(SALES_EVENT_KEYS))
    plain_user = user_key or decrypt_api_key(account.user_key_encrypted)
    plain_token = app_token or decrypt_api_key(account.app_token_encrypted)
    if user_key or app_token or device != account.device:
        try:
            pushover.validate_user(app_token=plain_token, user_key=plain_user, device=device)
        except pushover.PushoverError as exc:
            raise ValueError(f"O Pushover não aceitou a conta: {exc}") from exc
    if user_key:
        account.user_key_encrypted = encrypt_api_key(user_key)
        account.user_key_last4 = extract_api_key_last4(user_key)
    if app_token:
        account.app_token_encrypted = encrypt_api_key(app_token)
        account.app_token_last4 = extract_api_key_last4(app_token)
    account.name = str(payload.get("name") or account.name or "Pushover").strip()[:120]
    account.device = device
    if payload.get("enabled") is not None:
        account.enabled = bool(payload["enabled"])
    if payload.get("event_keys") is not None:
        account.event_keys = _clean_event_keys(db, payload["event_keys"])
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def pushover_sounds(db: Session) -> list[dict[str, str]]:
    """Sons que tocam para todas as contas ligadas: os do Pushover e os personalizados da conta dona
    do aplicativo. Contas com tokens diferentes: só os sons que existem em todos. Sem conta ou sem
    resposta: lista vazia (a tela usa a lista fixa)."""
    accounts = db.query(PushoverAccount).filter(PushoverAccount.enabled.is_(True)).order_by(PushoverAccount.id).all()
    tokens = list(dict.fromkeys(decrypt_api_key(account.app_token_encrypted) for account in accounts))
    common: dict[str, str] | None = None
    for token in tokens:
        try:
            sounds = pushover.list_sounds(app_token=token)
        except Exception as exc:  # noqa: BLE001 - só uma ajuda para a tela
            logger.info("pushover_sounds_unavailable error=%s", exc)
            return []
        common = sounds if common is None else {key: label for key, label in common.items() if key in sounds}
    return [{"value": key, "label": label} for key, label in (common or {}).items()]


def test_pushover_account(db: Session, account: PushoverAccount) -> None:
    try:
        send_to_pushover_account(
            account,
            title="🔔 Teste do Roteiro Online",
            body=f"Avisos chegando para {account.name}.",
            priority=3,
        )
    finally:
        db.add(account)
        db.commit()
