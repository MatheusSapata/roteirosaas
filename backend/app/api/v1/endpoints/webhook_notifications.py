from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.user import User
from app.schemas.webhook_notification import (
    WebhookNotificationMetaOut,
    WebhookNotificationRuleCreate,
    WebhookNotificationRuleOut,
    WebhookNotificationRuleUpdate,
    WebhookNotificationTestRequest,
    WebhookNotificationTestResponse,
)
from app.services.webhook_notifications import (
    AVAILABLE_ICON_OPTIONS,
    DEFAULT_AVAILABLE_FIELDS,
    delete_rule,
    get_rule,
    list_rules,
    send_notification,
    test_notification,
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
        test_notification(rule_id=rule_id, context=payload.context, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WebhookNotificationTestResponse(success=True)


@router.post("/dispatch")
def dispatch_webhook_notification(
    payload: WebhookNotificationTestRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    delivered = send_notification(event_key=payload.event_key, context=payload.context, db=db)
    return {"success": delivered}
