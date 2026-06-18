from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ai_prompt_config import AiPromptConfig, AiPromptConfigVersion

PROMPT_CONFIG_KEY = "construtor_roteiro_online"
PROMPT_FILE_PATH = Path(__file__).resolve().parents[3] / "docs" / "construtor-prompt.md"
DEFAULT_GPT_MODEL = "gpt-4.1"


@lru_cache
def _read_default_prompt_from_disk() -> str:
    try:
        text = PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()
        if text:
            return text
    except FileNotFoundError:
        pass
    return ""


def get_default_prompt_text() -> str:
    return _read_default_prompt_from_disk().strip()


def _ensure_config_row(db: Session) -> AiPromptConfig:
    config = db.query(AiPromptConfig).filter(AiPromptConfig.key == PROMPT_CONFIG_KEY).first()
    if config:
        return config

    default_prompt = get_default_prompt_text()
    config = AiPromptConfig(
        key=PROMPT_CONFIG_KEY,
        active_prompt=default_prompt,
        default_prompt=default_prompt,
        gpt_model=DEFAULT_GPT_MODEL,
    )
    db.add(config)
    db.flush()
    db.add(
        AiPromptConfigVersion(
            config_id=config.id,
            prompt_text=default_prompt,
            source="seed",
        )
    )
    db.commit()
    db.refresh(config)
    return config


def get_prompt_config(db: Session, create_if_missing: bool = True) -> AiPromptConfig | None:
    config = db.query(AiPromptConfig).filter(AiPromptConfig.key == PROMPT_CONFIG_KEY).first()
    if config or not create_if_missing:
        return config
    return _ensure_config_row(db)


def get_active_prompt_text(db: Session | None = None, create_if_missing: bool = True) -> str:
    default_prompt = get_default_prompt_text()
    own_session = False
    session = db
    if session is None:
        session = SessionLocal()
        own_session = True
    try:
        config = get_prompt_config(session, create_if_missing=create_if_missing)
        if not config:
            return default_prompt
        active_prompt = (config.active_prompt or "").strip()
        if active_prompt:
            return active_prompt
        fallback = (config.default_prompt or "").strip()
        return fallback or default_prompt
    except Exception:
        return default_prompt
    finally:
        if own_session and session is not None:
            session.close()


def get_active_gpt_model(db: Session | None = None, create_if_missing: bool = True) -> str:
    own_session = False
    session = db
    if session is None:
        session = SessionLocal()
        own_session = True
    try:
        config = get_prompt_config(session, create_if_missing=create_if_missing)
        if not config:
            return DEFAULT_GPT_MODEL
        model = (getattr(config, "gpt_model", "") or "").strip()
        return model or DEFAULT_GPT_MODEL
    except Exception:
        return DEFAULT_GPT_MODEL
    finally:
        if own_session and session is not None:
            session.close()


def save_prompt_text(
    db: Session,
    prompt_text: str,
    user_id: int | None = None,
    gpt_model: str | None = None,
) -> AiPromptConfig:
    prompt = (prompt_text or "").strip()
    if not prompt:
        raise ValueError("Prompt vazio.")

    config = get_prompt_config(db, create_if_missing=True)
    if config is None:
        raise ValueError("Não foi possível inicializar a configuração do prompt.")

    config.active_prompt = prompt
    if gpt_model is not None:
        config.gpt_model = (gpt_model or "").strip() or DEFAULT_GPT_MODEL
    config.updated_by_user_id = user_id
    db.add(config)
    db.flush()
    db.add(
        AiPromptConfigVersion(
            config_id=config.id,
            prompt_text=prompt,
            source="manual",
            created_by_user_id=user_id,
        )
    )
    db.commit()
    db.refresh(config)
    return config


def restore_default_prompt(db: Session, user_id: int | None = None) -> AiPromptConfig:
    default_prompt = get_default_prompt_text()
    config = get_prompt_config(db, create_if_missing=True)
    if config is None:
        raise ValueError("Não foi possível restaurar o prompt padrão.")

    config.active_prompt = default_prompt
    config.updated_by_user_id = user_id
    db.add(config)
    db.flush()
    db.add(
        AiPromptConfigVersion(
            config_id=config.id,
            prompt_text=default_prompt,
            source="restore-default",
            created_by_user_id=user_id,
        )
    )
    db.commit()
    db.refresh(config)
    return config


def restore_version(db: Session, version_id: int, user_id: int | None = None) -> AiPromptConfig:
    version = db.query(AiPromptConfigVersion).filter(AiPromptConfigVersion.id == version_id).first()
    if not version:
        raise ValueError("Versão não encontrada.")
    config = get_prompt_config(db, create_if_missing=True)
    if config is None:
        raise ValueError("Não foi possível restaurar o prompt.")

    config.active_prompt = version.prompt_text
    config.updated_by_user_id = user_id
    db.add(config)
    db.flush()
    db.add(
        AiPromptConfigVersion(
            config_id=config.id,
            prompt_text=version.prompt_text,
            source=f"restore-version:{version.id}",
            created_by_user_id=user_id,
        )
    )
    db.commit()
    db.refresh(config)
    return config


def list_prompt_versions(db: Session, limit: int = 20) -> list[AiPromptConfigVersion]:
    config = get_prompt_config(db, create_if_missing=True)
    if not config:
        return []
    return (
        db.query(AiPromptConfigVersion)
        .filter(AiPromptConfigVersion.config_id == config.id)
        .order_by(AiPromptConfigVersion.id.desc())
        .limit(limit)
        .all()
    )


def clear_prompt_cache() -> None:
    _read_default_prompt_from_disk.cache_clear()
