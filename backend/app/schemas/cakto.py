from pydantic import BaseModel


class OnboardingSessionResponse(BaseModel):
    email: str
    name: str | None = None
    plan: str
    cycle: str


class OnboardingPasswordPayload(BaseModel):
    password: str
