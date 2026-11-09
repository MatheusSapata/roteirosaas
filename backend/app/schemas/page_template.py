from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PageTemplateBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    is_default: bool = False
    config_json: Any


class PageTemplateCreate(PageTemplateBase):
    pass


class PageTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    is_default: Optional[bool] = None
    config_json: Optional[str] = None


class PageTemplateOut(PageTemplateBase):
    id: int
    agency_id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PageTemplateFromPage(BaseModel):
    page_id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_default: bool = False


class AgencyTemplateCreate(BaseModel):
    """Modelo próprio do cliente, salvo a partir do editor."""

    agency_id: int
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    config_json: Any


class AgencyTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
