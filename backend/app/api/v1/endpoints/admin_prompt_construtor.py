from __future__ import annotations

import anyio
from functools import partial
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.models.user import User
from app.schemas.prompt_construtor import (
    PromptConstructorConfigOut,
    PromptConstructorSaveIn,
    PromptConstructorTestIn,
    PromptConstructorTestOut,
    PromptConstructorUsageOut,
    PromptConstructorVersionOut,
)
from app.services.ai_assistant import (
    ChatMessage,
    _validate_ai_reply_format,
    generate_ai_assistant_reply_with_usage,
    load_system_prompt,
)
from app.services.construtor_prompt import (
    DEFAULT_GPT_MODEL,
    get_active_gpt_model,
    get_active_prompt_text,
    get_default_prompt_text,
    get_prompt_config,
    list_prompt_versions,
    restore_default_prompt as restore_default_prompt_in_db,
    restore_version as restore_prompt_version_in_db,
    save_prompt_text,
)

router = APIRouter()


def _build_version_out(version) -> PromptConstructorVersionOut:
    created_by_name = version.created_by.name if getattr(version, "created_by", None) else None
    return PromptConstructorVersionOut(
        id=version.id,
        prompt_text=version.prompt_text,
        source=version.source,
        created_at=version.created_at,
        created_by_user_id=version.created_by_user_id,
        created_by_name=created_by_name,
    )


def _build_config_out(db: Session) -> PromptConstructorConfigOut:
    config = get_prompt_config(db, create_if_missing=True)
    if not config:
        raise HTTPException(status_code=500, detail="Não foi possível carregar a configuração do prompt.")

    updated_by_name = config.updated_by.name if getattr(config, "updated_by", None) else None
    versions = [_build_version_out(version) for version in list_prompt_versions(db, limit=20)]
    return PromptConstructorConfigOut(
        id=config.id,
        key=config.key,
        active_prompt=get_active_prompt_text(db, create_if_missing=True),
        default_prompt=config.default_prompt or get_default_prompt_text(),
        gpt_model=(getattr(config, "gpt_model", "") or DEFAULT_GPT_MODEL),
        updated_at=config.updated_at,
        updated_by_user_id=config.updated_by_user_id,
        updated_by_name=updated_by_name,
        versions=versions,
    )


@router.get("/prompt-construtor", response_model=PromptConstructorConfigOut)
def get_prompt_construtor_config(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PromptConstructorConfigOut:
    return _build_config_out(db)


@router.put("/prompt-construtor", response_model=PromptConstructorConfigOut)
def save_prompt_construtor_config(
    payload: PromptConstructorSaveIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> PromptConstructorConfigOut:
    prompt_text = (payload.prompt_text or "").strip()
    if not prompt_text:
        raise HTTPException(status_code=400, detail="O prompt não pode ficar vazio.")

    save_prompt_text(db, prompt_text, user_id=current_user.id, gpt_model=payload.gpt_model)
    if hasattr(load_system_prompt, "cache_clear"):
        load_system_prompt.cache_clear()
    return _build_config_out(db)


@router.post("/prompt-construtor/restore-default", response_model=PromptConstructorConfigOut)
def restore_default_prompt_construtor_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> PromptConstructorConfigOut:
    restore_default_prompt_in_db(db, user_id=current_user.id)
    if hasattr(load_system_prompt, "cache_clear"):
        load_system_prompt.cache_clear()
    return _build_config_out(db)


@router.post("/prompt-construtor/versions/{version_id}/restore", response_model=PromptConstructorConfigOut)
def restore_prompt_construtor_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> PromptConstructorConfigOut:
    try:
        restore_prompt_version_in_db(db, version_id=version_id, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Versão não encontrada.") from exc
    if hasattr(load_system_prompt, "cache_clear"):
        load_system_prompt.cache_clear()
    return _build_config_out(db)


@router.post("/prompt-construtor/test", response_model=PromptConstructorTestOut)
async def test_prompt_construtor_config(
    payload: PromptConstructorTestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> PromptConstructorTestOut:
    travel_input = (payload.travel_input or "").strip()
    if not travel_input:
        raise HTTPException(status_code=400, detail="Informe os dados da viagem para testar o prompt.")

    active_prompt = get_active_prompt_text(db, create_if_missing=True)
    config = get_prompt_config(db, create_if_missing=True)
    raw_active_prompt = (config.active_prompt if config else "") or ""
    prompt_source = "database" if raw_active_prompt.strip() else "fallback"
    selected_model = (payload.model or "").strip() or None
    reply, used_model, usage, estimated_cost_usd = await anyio.to_thread.run_sync(
        partial(
            generate_ai_assistant_reply_with_usage,
            [ChatMessage(role="user", content=travel_input)],
            [],
            validate_output=False,
            model_override=selected_model,
        )
    )
    is_valid, validation_error = _validate_ai_reply_format(reply)
    return PromptConstructorTestOut(
        reply=reply,
        validation_error="" if is_valid else validation_error,
        prompt_source=prompt_source,
        model=used_model,
        prompt_length=len(active_prompt or ""),
        prompt_preview=(active_prompt or "")[:600],
        usage=PromptConstructorUsageOut(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cached_input_tokens=usage.get("cached_input_tokens", 0),
            estimated_cost_usd=estimated_cost_usd,
        ),
    )
