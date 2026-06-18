from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

import anyio
from functools import partial
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.api.deps import get_db
from app.api.v1.endpoints.pages import (
    derive_cover_image_from_config,
    ensure_agency_member,
    ensure_pages_editor_permission,
    normalize_config,
    resolve_agency_plan,
    enforce_page_limits,
)
from app.models.page import Page
from app.models.user import User
from app.schemas.page import PageOut
from app.services.ai_assistant import (
    ChatAttachment,
    ChatMessage,
    build_page_base_config_from_reply,
    generate_ai_assistant_reply,
)
from app.services.ai_assistant_usage import (
    check_ai_assistant_message_limit,
    get_ai_assistant_usage_summary,
    increment_ai_assistant_message_usage,
)
from app.services.construtor_prompt import get_active_gpt_model

router = APIRouter()


class AiAssistantChatResponse(BaseModel):
    reply: str


class AiAssistantConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AiAssistantCreatePageBaseRequest(BaseModel):
    page_id: int
    reply: str


class AiAssistantCreatePageBaseResponse(BaseModel):
    page: PageOut


class AiAssistantUsageResponse(BaseModel):
    period_key: str
    used: int
    limit: int | None = None
    remaining: int | None = None
    unlimited: bool = False
    renewal_at: datetime | None = None


@router.post("/chat", response_model=AiAssistantChatResponse)
async def chat_with_assistant(
    conversation: str = Form("[]"),
    attachments: list[UploadFile] | None = File(default=None),
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAssistantChatResponse:
    try:
        conversation_payload = json.loads(conversation or "[]")
        if not isinstance(conversation_payload, list):
            raise ValueError("conversation must be a list")
        parsed_conversation = [AiAssistantConversationMessage.model_validate(item) for item in conversation_payload]
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail="Conversa inválida.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Conversa inválida.") from exc

    if not parsed_conversation:
        raise HTTPException(status_code=400, detail="Nenhuma mensagem enviada.")

    usage_record, usage_limit = check_ai_assistant_message_limit(db, current_user)

    attachment_payload: list[ChatAttachment] = []
    for upload in attachments or []:
        data = await upload.read()
        attachment_payload.append(
            ChatAttachment(
                filename=upload.filename or "arquivo",
                content_type=upload.content_type,
                data=data,
            )
        )

    reply = await anyio.to_thread.run_sync(
        partial(
            generate_ai_assistant_reply,
            [ChatMessage(role=item.role, content=item.content) for item in parsed_conversation],
            attachment_payload,
            model_override=get_active_gpt_model(db, create_if_missing=True),
        )
    )
    usage_record = increment_ai_assistant_message_usage(db, usage_record)
    db.commit()

    response.headers["X-AI-Assistant-Period"] = usage_record.period_key
    response.headers["X-AI-Assistant-Usage"] = str(int(usage_record.message_count or 0))
    if usage_limit is not None:
        response.headers["X-AI-Assistant-Limit"] = str(usage_limit)
        response.headers["X-AI-Assistant-Remaining"] = str(max(int(usage_limit) - int(usage_record.message_count or 0), 0))
    else:
        response.headers["X-AI-Assistant-Limit"] = "unlimited"
        response.headers["X-AI-Assistant-Remaining"] = "unlimited"

    return AiAssistantChatResponse(reply=reply)


@router.get("/usage", response_model=AiAssistantUsageResponse)
def get_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AiAssistantUsageResponse:
    summary = get_ai_assistant_usage_summary(db, current_user)
    return AiAssistantUsageResponse(
        period_key=str(summary["period_key"]),
        used=int(summary["used"] or 0),
        limit=None if summary["limit"] is None else int(summary["limit"]),
        remaining=None if summary["remaining"] is None else int(summary["remaining"]),
        unlimited=bool(summary["unlimited"]),
        renewal_at=summary["renewal_at"],
    )


@router.post("/create-page-base", response_model=AiAssistantCreatePageBaseResponse)
def create_page_base(
    payload: AiAssistantCreatePageBaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AiAssistantCreatePageBaseResponse:
    page = db.query(Page).filter(Page.id == payload.page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")

    ensure_agency_member(db, page.agency_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)

    current_config = normalize_config(page.config_json)
    new_config, suggested_title = build_page_base_config_from_reply(payload.reply, current_config)
    plan = resolve_agency_plan(db, page.agency_id)
    page.config_json = enforce_page_limits(db, page, publish=False, config=new_config, plan=plan)
    page.cover_image_url = derive_cover_image_from_config(page.config_json)
    if suggested_title and suggested_title.strip():
        page.title = suggested_title.strip()

    db.add(page)
    db.commit()
    db.refresh(page)
    setattr(page, "is_default", bool(page.agency and page.agency.default_page_id == page.id))
    return AiAssistantCreatePageBaseResponse(page=page)
