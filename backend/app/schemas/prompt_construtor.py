from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptConstructorVersionOut(BaseModel):
    id: int
    prompt_text: str
    source: str
    created_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None
    created_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PromptConstructorConfigOut(BaseModel):
    id: int
    key: str
    active_prompt: str
    default_prompt: str
    gpt_model: str = "gpt-4.1"
    updated_at: Optional[datetime] = None
    updated_by_user_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    versions: List[PromptConstructorVersionOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PromptConstructorSaveIn(BaseModel):
    prompt_text: str
    gpt_model: Optional[str] = None


class PromptConstructorTestIn(BaseModel):
    travel_input: str
    model: Optional[str] = None


class PromptConstructorUsageOut(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_input_tokens: int = 0
    estimated_cost_usd: float = 0.0


class PromptConstructorTestOut(BaseModel):
    reply: str
    validation_error: Optional[str] = None
    prompt_source: str = "active"
    model: str = "gpt-5.4"
    prompt_length: int = 0
    prompt_preview: str = ""
    usage: Optional[PromptConstructorUsageOut] = None
