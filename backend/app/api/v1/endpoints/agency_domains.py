from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.agency import Agency
from app.models.agency_domain import AgencyDomain
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.schemas.agency_domain import (
    AgencyDomainCreate,
    AgencyDomainOut,
    DomainActivationResponse,
    DomainInstructionsOut,
    DomainVerificationResponse,
)
from app.services.domain_ssl import DomainSslService
from app.services.domain_verification import DomainVerificationService

router = APIRouter()

verification_service = DomainVerificationService()
ssl_service = DomainSslService()


def ensure_agency_member(db: Session, agency_id: int, user_id: int) -> Agency:
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agencia nao encontrada.")
    membership = (
        db.query(AgencyUser)
        .filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao faz parte desta agencia.")
    return agency


def load_domain(db: Session, domain_id: int, user_id: int) -> AgencyDomain:
    domain = db.query(AgencyDomain).filter(AgencyDomain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dominio nao encontrado.")
    ensure_agency_member(db, domain.agency_id, user_id)
    return domain


def serialize_domain(domain: AgencyDomain) -> AgencyDomainOut:
    payload = AgencyDomainOut.model_validate(domain)
    payload.instructions = DomainInstructionsOut.from_service(
        verification_service.build_instructions(domain.host, domain.verification_token)
    )
    return payload


def unset_other_primary(db: Session, agency_id: int, domain_id: int) -> None:
    db.query(AgencyDomain).filter(
        AgencyDomain.agency_id == agency_id,
        AgencyDomain.id != domain_id,
        AgencyDomain.is_primary.is_(True),
    ).update({AgencyDomain.is_primary: False}, synchronize_session=False)


@router.get("", response_model=list[AgencyDomainOut])
def list_domains(
    agency_id: int = Query(..., description="ID da agencia atual"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[AgencyDomainOut]:
    ensure_agency_member(db, agency_id, current_user.id)
    domains = (
        db.query(AgencyDomain)
        .filter(AgencyDomain.agency_id == agency_id)
        .order_by(AgencyDomain.created_at.desc())
        .all()
    )
    return [serialize_domain(domain) for domain in domains]


@router.post("", response_model=AgencyDomainOut, status_code=status.HTTP_201_CREATED)
def create_domain(
    payload: AgencyDomainCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgencyDomainOut:
    ensure_agency_member(db, payload.agency_id, current_user.id)
    normalized_host = payload.host.lower()
    existing = (
        db.query(AgencyDomain)
        .filter(func.lower(AgencyDomain.host) == normalized_host)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este host ja esta em uso por outra agencia.")

    token = verification_service.generate_token()
    instructions = verification_service.build_instructions(payload.host, token)
    domain = AgencyDomain(
        agency_id=payload.agency_id,
        host=payload.host,
        is_primary=payload.is_primary,
        verification_token=token,
        dns_target_type=instructions.target_record.type,
        dns_target_value=instructions.target_record.value,
    )
    if domain.is_primary:
        unset_other_primary(db, domain.agency_id, domain.id or 0)

    db.add(domain)
    db.commit()
    db.refresh(domain)
    if domain.is_primary:
        unset_other_primary(db, domain.agency_id, domain.id)
        db.commit()
        db.refresh(domain)
    return serialize_domain(domain)


@router.get("/{domain_id}", response_model=AgencyDomainOut)
def get_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgencyDomainOut:
    domain = load_domain(db, domain_id, current_user.id)
    return serialize_domain(domain)


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    domain = load_domain(db, domain_id, current_user.id)
    if domain.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Desative o dominio antes de removelo.")
    db.delete(domain)
    db.commit()


@router.post("/{domain_id}/verify", response_model=DomainVerificationResponse)
def verify_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DomainVerificationResponse:
    domain = load_domain(db, domain_id, current_user.id)
    result = verification_service.verify(domain.host, domain.verification_token)

    if result.success:
        domain.is_verified = True
        domain.verified_at = datetime.now(tz=timezone.utc)
        domain.ssl_last_error = None
        ssl_service.queue_certificate_request(domain)
    else:
        domain.is_verified = False
        domain.ssl_last_error = result.target_error or result.txt_error
    db.add(domain)
    db.commit()
    db.refresh(domain)

    return DomainVerificationResponse(
        success=result.success,
        txt_verified=result.txt_verified,
        target_verified=result.target_verified,
        txt_error=result.txt_error,
        target_error=result.target_error,
        observed_target=result.observed_target,
    )


@router.post("/{domain_id}/activate", response_model=DomainActivationResponse)
def activate_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DomainActivationResponse:
    domain = load_domain(db, domain_id, current_user.id)
    if not domain.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voce nao pode ativar um dominio sem verificacao DNS.",
        )
    if not ssl_service.can_activate(domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O certificado SSL ainda nao esta pronto para este dominio.",
        )
    domain.is_active = True
    domain.activated_at = datetime.now(tz=timezone.utc)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return DomainActivationResponse(is_active=domain.is_active, activated_at=domain.activated_at, ssl_status=domain.ssl_status)


@router.post("/{domain_id}/deactivate", response_model=DomainActivationResponse)
def deactivate_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DomainActivationResponse:
    domain = load_domain(db, domain_id, current_user.id)
    domain.is_active = False
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return DomainActivationResponse(is_active=domain.is_active, activated_at=domain.activated_at, ssl_status=domain.ssl_status)


@router.post("/{domain_id}/set-primary", response_model=AgencyDomainOut)
def set_primary_domain(
    domain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AgencyDomainOut:
    domain = load_domain(db, domain_id, current_user.id)
    domain.is_primary = True
    unset_other_primary(db, domain.agency_id, domain.id)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return serialize_domain(domain)
