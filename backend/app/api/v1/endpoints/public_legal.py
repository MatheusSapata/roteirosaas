from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.legal import (
    LegalContractSignaturePublic,
    LegalContractSignatureSubmitPayload,
    LegalContractSignatureSubmitResponse,
    LegalContractVerificationDetail,
    LegalContractAuditEventList,
)
from app.services.legal import (
    get_contract_for_signature,
    get_contract_verification_by_token,
    submit_contract_signature,
    get_contract_by_verification_token,
)
from app.services.legal_audit import legal_contract_audit_service

router = APIRouter()


@router.get("/signatures/{token}", response_model=LegalContractSignaturePublic)
def get_signature_contract_endpoint(
    token: str,
    db: Session = Depends(get_db),
) -> LegalContractSignaturePublic:
    return get_contract_for_signature(token, db)


@router.post("/signatures/{token}", response_model=LegalContractSignatureSubmitResponse)
def submit_signature_contract_endpoint(
    token: str,
    payload: LegalContractSignatureSubmitPayload,
    request: Request,
    db: Session = Depends(get_db),
) -> LegalContractSignatureSubmitResponse:
    return submit_contract_signature(token, payload, request, db)


@router.get("/verification/{token}", response_model=LegalContractVerificationDetail)
def get_contract_verification_public_endpoint(
    token: str,
    db: Session = Depends(get_db),
) -> LegalContractVerificationDetail:
    return get_contract_verification_by_token(token, db)


@router.get("/verification/{token}/audit-events", response_model=LegalContractAuditEventList)
def get_contract_audit_events_public_endpoint(
    token: str,
    full: bool = False,
    limit: int = 8,
    db: Session = Depends(get_db),
) -> LegalContractAuditEventList:
    contract = get_contract_by_verification_token(token, db)
    normalized_limit = legal_contract_audit_service.normalize_limit(limit, full=full)
    created = legal_contract_audit_service.ensure_backfilled_events(contract, db)
    if created:
        db.commit()
    events, has_more = legal_contract_audit_service.list_events_for_contract(
        contract.id,
        db,
        limit=normalized_limit,
    )
    return LegalContractAuditEventList(
        items=[legal_contract_audit_service.serialize_event(event) for event in events],
        has_more=has_more and not full,
    )
