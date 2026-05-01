from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TeamMemberOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    avatar_url: str | None = None
    role: str
    role_name: str | None = None
    status: str
    is_owner: bool
    permissions: list[str] = Field(default_factory=list)


class TeamInviteOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role_name: str | None = None
    permissions: list[str] = Field(default_factory=list)
    status: str
    expires_at: datetime
    created_at: datetime | None = None


class TeamSummaryOut(BaseModel):
    plan_key: str
    extra_users_limit: int | None
    extra_users_used: int
    members: list[TeamMemberOut]
    pending_invites: list[TeamInviteOut]
    plan_allowed_permissions: list[str]


class TeamInviteCreate(BaseModel):
    name: str
    email: EmailStr
    role: str = "member"
    permissions: list[str] = Field(default_factory=list)


class TeamUserPermissionsUpdate(BaseModel):
    role: str = "member"
    permissions: list[str] = Field(default_factory=list)


class InviteInfoOut(BaseModel):
    valid: bool
    reason: str | None = None
    agency_name: str | None = None
    email: EmailStr | None = None
    name: str | None = None


class AcceptInviteIn(BaseModel):
    token: str
    password: str
