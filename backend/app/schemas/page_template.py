from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)
