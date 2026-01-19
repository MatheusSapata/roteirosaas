from datetime import datetime
from typing import Any, Optional
import json

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class PageBase(BaseModel):
    title: str
    slug: str
    status: str = "draft"
    cover_image_url: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    config_json: Optional[Any] = None
    template_id: Optional[int] = None


class PageCreate(PageBase):
    agency_id: int


class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    cover_image_url: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    config_json: Optional[Any] = None
    template_id: Optional[int] = None


class PageConfigUpdate(BaseModel):
    config: Any

    @model_validator(mode="before")
    @classmethod
    def include_legacy_key(cls, value: Any) -> Any:
        if isinstance(value, dict) and "config" not in value and "config_json" in value:
            return {**value, "config": value.get("config_json")}
        return value

    @field_validator("config")
    @classmethod
    def parse_config(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


class PagePublish(BaseModel):
    publish: bool = True


class PageOut(PageBase):
    id: int
    agency_id: int
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_default: bool = False
    model_config = ConfigDict(from_attributes=True)


class PublicPageOut(BaseModel):
    id: int
    title: str
    slug: str
    agency_slug: str
    cover_image_url: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    config: Any
    branding: dict[str, Any]
