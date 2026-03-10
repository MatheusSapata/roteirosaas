from typing import Literal

from pydantic import BaseModel, EmailStr


class OnboardingSessionResponse(BaseModel):
    email: str
    name: str | None = None
    plan: str
    cycle: str


class OnboardingPasswordPayload(BaseModel):
    password: str


class ManualPasswordPayload(BaseModel):
    email: EmailStr
    password: str


class ManualPasswordEmailPayload(BaseModel):
    email: EmailStr


class ManualPasswordValidationResponse(BaseModel):
    email: EmailStr
    name: str | None = None


class CheckoutSessionRequest(BaseModel):
    plan: str
    cycle: Literal["monthly", "annual"] | None = None


class CheckoutSessionResponse(BaseModel):
    token: str
    checkout_url: str
    plan: str
    cycle: str


class CheckoutSessionStatusResponse(BaseModel):
    status: Literal["pending", "ready"]
    order_id: str | None = None
    ref_id: str | None = None
    redirect_token: str | None = None
