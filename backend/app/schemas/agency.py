from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator


AgencySocialNetwork = Literal["instagram", "facebook", "youtube", "tiktok"]


class AgencySocialLinkBase(BaseModel):
    network: AgencySocialNetwork
    url: str

    @field_validator("network")
    @classmethod
    def normalize_network(cls, value: str) -> str:
        return value.lower()

    @field_validator("url")
    @classmethod
    def sanitize_url(cls, value: str) -> str:
        if value is None:
            raise ValueError("URL obrigatoria.")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("URL obrigatoria.")
        return cleaned


class AgencySocialLinkCreate(AgencySocialLinkBase):
    pass


class AgencySocialLinkOut(AgencySocialLinkBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


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
    social_links: Optional[list[AgencySocialLinkCreate]] = None


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    default_page_id: Optional[int] = None
    cta_whatsapp: Optional[str] = None
    social_links: Optional[list[AgencySocialLinkCreate]] = None

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
    social_links: list[AgencySocialLinkOut] = []
    model_config = ConfigDict(from_attributes=True)
