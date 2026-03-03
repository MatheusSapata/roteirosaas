from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AgencyBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    cta_whatsapp: Optional[str] = None

    @field_validator("cta_whatsapp")
    @classmethod
    def sanitize_whatsapp(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(filter(str.isdigit, value))
        return digits or None


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    default_page_id: Optional[int] = None
    cta_whatsapp: Optional[str] = None

    @field_validator("cta_whatsapp")
    @classmethod
    def sanitize_whatsapp(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(filter(str.isdigit, value))
        return digits or None


class AgencyOut(AgencyBase):
    id: int
    default_page_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
