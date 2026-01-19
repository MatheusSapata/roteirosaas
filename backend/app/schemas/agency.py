from typing import Optional

from pydantic import BaseModel, ConfigDict


class AgencyBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    default_page_id: Optional[int] = None


class AgencyOut(AgencyBase):
    id: int
    default_page_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
