from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.pushover_account import PushoverAccount
from app.models.user import User
from app.schemas.webhook_notification import (
    PushoverAccountIn,
    PushoverAccountOut,
    PushoverAccountUpdate,
    WebhookNotificationMetaOut,
    WebhookNotificationRuleCreate,
    WebhookNotificationRuleOut,
    WebhookNotificationRuleUpdate,
    WebhookNotificationTestRequest,
    WebhookNotificationTestResponse,
)
from app.services.api_key_crypto import mask_api_key
from app.services.webhook_notifications import (
    AVAILABLE_ICON_OPTIONS,
    DEFAULT_AVAILABLE_FIELDS,
    delete_rule,
    get_rule,
    list_pushover_accounts,
    list_rules,
    save_pushover_account,
    send_notification,
    test_notification,
    test_pushover_account,
    upsert_rule,
)

router = APIRouter()
admin_router = APIRouter(prefix="/admin-master/webhook-notifications")


@admin_router.get("", response_model=list[WebhookNotificationRuleOut])
def list_webhook_notification_rules(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[WebhookNotificationRuleOut]:
    return [WebhookNotificationRuleOut.model_validate(rule) for rule in list_rules(db)]


@admin_router.get("/meta", response_model=WebhookNotificationMetaOut)
def get_webhook_notification_meta(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> WebhookNotificationMetaOut:
    rules = list_rules(db)
    return WebhookNotificationMetaOut(
        icons=AVAILABLE_ICON_OPTIONS,
        available_fields=DEFAULT_AVAILABLE_FIELDS,
        builtin_events=[WebhookNotificationRuleOut.model_validate(rule) for rule in rules if rule.is_builtin],
        custom_events_count=sum(1 for rule in rules if not rule.is_builtin),
    )


@admin_router.post("", response_model=WebhookNotificationRuleOut, status_code=status.HTTP_201_CREATED)
def create_webhook_notification_rule(
    payload: WebhookNotificationRuleCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> WebhookNotificationRuleOut:
    created = upsert_rule(db, payload=payload.model_dump())
    return WebhookNotificationRuleOut.model_validate(created)


@admin_router.put("/{rule_id}", response_model=WebhookNotificationRuleOut)
def update_webhook_notification_rule(
    rule_id: int,
    payload: WebhookNotificationRuleUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> WebhookNotificationRuleOut:
    rule = get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    updated = upsert_rule(db, rule_id=rule_id, payload=payload.model_dump(exclude_unset=True))
    return WebhookNotificationRuleOut.model_validate(updated)


@admin_router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook_notification_rule(
    rule_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> None:
    rule = get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    if rule.is_builtin:
        raise HTTPException(status_code=400, detail="Regras padrão não podem ser excluídas.")
    delete_rule(db, rule_id)


@admin_router.post("/{rule_id}/test", response_model=WebhookNotificationTestResponse)
def test_webhook_notification_rule(
    rule_id: int,
    payload: WebhookNotificationTestRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> WebhookNotificationTestResponse:
    try:
        result = test_notification(rule_id=rule_id, context=payload.context, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    deliveries = result["deliveries"]
    if not deliveries:
        message = "Nenhum canal ligado: ligue o ntfy ou escolha este evento numa conta do Pushover."
    elif all(item["ok"] for item in deliveries):
        message = "Enviado."
    else:
        message = "Alguns envios falharam."
    return WebhookNotificationTestResponse(
        success=any(item["ok"] for item in deliveries), message=message, deliveries=deliveries
    )


# Contas do Pushover: cada pessoa que recebe os avisos (sem Pushover Teams).


def _account_out(account: PushoverAccount) -> PushoverAccountOut:
    return PushoverAccountOut(
        id=account.id,
        name=account.name,
        user_key_masked=mask_api_key(account.user_key_last4),
        app_token_masked=mask_api_key(account.app_token_last4),
        device=account.device,
        enabled=account.enabled,
        event_keys=list(account.event_keys or []),
        last_sent_at=account.last_sent_at,
        last_error=account.last_error,
    )


def _get_account(db: Session, account_id: int) -> PushoverAccount:
    account = db.query(PushoverAccount).filter(PushoverAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta do Pushover não encontrada.")
    return account


@admin_router.get("/pushover-accounts", response_model=list[PushoverAccountOut])
def list_pushover(
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[PushoverAccountOut]:
    return [_account_out(account) for account in list_pushover_accounts(db)]


@admin_router.post("/pushover-accounts", response_model=PushoverAccountOut, status_code=status.HTTP_201_CREATED)
def create_pushover(
    payload: PushoverAccountIn,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> PushoverAccountOut:
    try:
        account = save_pushover_account(db, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _account_out(account)


@admin_router.put("/pushover-accounts/{account_id}", response_model=PushoverAccountOut)
def update_pushover(
    account_id: int,
    payload: PushoverAccountUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> PushoverAccountOut:
    account = _get_account(db, account_id)
    try:
        account = save_pushover_account(db, payload.model_dump(exclude_unset=True), account)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _account_out(account)


@admin_router.delete("/pushover-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pushover(
    account_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> None:
    db.delete(_get_account(db, account_id))
    db.commit()


@admin_router.post("/pushover-accounts/{account_id}/test", response_model=PushoverAccountOut)
def test_pushover(
    account_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> PushoverAccountOut:
    account = _get_account(db, account_id)
    try:
        test_pushover_account(db, account)
    except Exception as exc:  # noqa: BLE001 - o erro do Pushover vai para a tela
        raise HTTPException(status_code=400, detail=f"O Pushover não entregou o teste: {exc}") from exc
    return _account_out(account)


@router.post("/dispatch")
def dispatch_webhook_notification(
    payload: WebhookNotificationTestRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    delivered = send_notification(event_key=payload.event_key, context=payload.context, db=db)
    return {"success": delivered}
