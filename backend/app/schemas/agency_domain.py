from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.domain_verification import DomainVerificationService, DomainDnsInstructions


_domain_validator = DomainVerificationService()


class DnsRecordInstructionOut(BaseModel):
    type: str
    host: str
    value: str
    description: Optional[str] = None
    fqdn: Optional[str] = None


class DomainInstructionsOut(BaseModel):
    is_apex: bool
    verification: DnsRecordInstructionOut
    target: DnsRecordInstructionOut

    @classmethod
    def from_service(cls, data: DomainDnsInstructions) -> "DomainInstructionsOut":
        return cls(
            is_apex=data.is_apex,
            verification=DnsRecordInstructionOut(
                type=data.txt_record.type,
                host=data.txt_record.host,
                value=data.txt_record.value,
                description=data.txt_record.description,
                fqdn=data.txt_record.fqdn,
            ),
            target=DnsRecordInstructionOut(
                type=data.target_record.type,
                host=data.target_record.host,
                value=data.target_record.value,
                description=data.target_record.description,
                fqdn=data.target_record.fqdn,
            ),
        )


class AgencyDomainBase(BaseModel):
    host: str
    is_primary: bool = False

    @field_validator("host")
    @classmethod
    def normalize_host(cls, value: str) -> str:
        return _domain_validator.ensure_allowed_host(value)


class AgencyDomainCreate(AgencyDomainBase):
    agency_id: int


class AgencyDomainOut(BaseModel):
    id: int
    agency_id: int
    host: str
    is_primary: bool
    is_verified: bool
    verification_token: str
    dns_target_type: Optional[str] = None
    dns_target_value: Optional[str] = None
    ssl_status: str
    ssl_last_error: Optional[str] = None
    is_active: bool
    verified_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    instructions: Optional[DomainInstructionsOut] = None
    model_config = ConfigDict(from_attributes=True)


class DomainVerificationResponse(BaseModel):
    success: bool
    txt_verified: bool
    target_verified: bool
    txt_error: Optional[str] = None
    target_error: Optional[str] = None
    observed_target: Optional[str] = None


class DomainActivationResponse(BaseModel):
    is_active: bool
    activated_at: Optional[datetime]
    ssl_status: str
