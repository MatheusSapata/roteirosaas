from pydantic import BaseModel, ConfigDict


class AgencyUserBase(BaseModel):
    agency_id: int
    user_id: int
    role: str = "editor"


class AgencyUserOut(AgencyUserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
