from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.legal import (
    LegalContractSignaturePublic,
    LegalContractSignatureSubmitPayload,
    LegalContractSignatureSubmitResponse,
    LegalContractVerificationDetail,
)
from app.services.legal import (
    get_contract_for_signature,
    get_contract_verification_by_token,
    submit_contract_signature,
)

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
