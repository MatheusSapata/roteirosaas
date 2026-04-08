from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.legal import (
    LegalContractDetail,
    LegalContractListResponse,
    LegalContractVerificationDetail,
    LegalSignatureProfilePayload,
    LegalSignatureProfileResponse,
    LegalTemplateDetail,
    LegalTemplateListResponse,
    LegalTemplatePayload,
    LegalVariablesResponse,
    LegalContractAuditEventList,
)
from app.services.legal import (
    create_template,
    delete_signature_profile,
    delete_template,
    get_contract,
    get_contract_verification_detail,
    regenerate_contract_verification,
    get_signature_profile_response,
    get_template_by_id,
    list_contracts,
    list_templates,
    save_signature_profile,
    serialize_contract,
    serialize_template_detail,
    serialize_variable_categories,
    update_template,
)
from app.services.legal_audit import legal_contract_audit_service

router = APIRouter()


@router.get("/variables", response_model=LegalVariablesResponse)
def list_variables_endpoint() -> LegalVariablesResponse:
    return LegalVariablesResponse(categories=serialize_variable_categories())


@router.get("/signature-profile", response_model=LegalSignatureProfileResponse | None)
def get_signature_profile_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalSignatureProfileResponse | None:
    return get_signature_profile_response(current_user, db)


@router.put("/signature-profile", response_model=LegalSignatureProfileResponse)
def save_signature_profile_endpoint(
    payload: LegalSignatureProfilePayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalSignatureProfileResponse:
    return save_signature_profile(payload, current_user, db)


@router.delete("/signature-profile", status_code=204)
def delete_signature_profile_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_signature_profile(current_user, db)
    return Response(status_code=204)


@router.get("/templates", response_model=LegalTemplateListResponse)
def list_templates_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalTemplateListResponse:
    items = list_templates(current_user, db)
    return LegalTemplateListResponse(items=items)


@router.post("/templates", response_model=LegalTemplateDetail)
def create_template_endpoint(
    payload: LegalTemplatePayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalTemplateDetail:
    template = create_template(payload, current_user, db)
    return serialize_template_detail(template)


@router.get("/templates/{template_id}", response_model=LegalTemplateDetail)
def get_template_endpoint(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalTemplateDetail:
    template = get_template_by_id(template_id, current_user, db)
    return serialize_template_detail(template)


@router.put("/templates/{template_id}", response_model=LegalTemplateDetail)
def update_template_endpoint(
    template_id: int,
    payload: LegalTemplatePayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalTemplateDetail:
    template = get_template_by_id(template_id, current_user, db)
    template = update_template(template, payload, db)
    return serialize_template_detail(template)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template_endpoint(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    template = get_template_by_id(template_id, current_user, db)
    delete_template(template, db)
    return Response(status_code=204)


@router.get("/contracts", response_model=LegalContractListResponse)
def list_contracts_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalContractListResponse:
    items = list_contracts(current_user, db)
    return LegalContractListResponse(items=items)


@router.get("/contracts/{contract_id}", response_model=LegalContractDetail)
def get_contract_endpoint(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalContractDetail:
    contract = get_contract(contract_id, current_user, db)
    return serialize_contract(contract)


@router.get("/contracts/{contract_id}/verification", response_model=LegalContractVerificationDetail)
def get_contract_verification_endpoint(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalContractVerificationDetail:
    return get_contract_verification_detail(contract_id, current_user, db)


@router.get("/contracts/{contract_id}/audit-events", response_model=LegalContractAuditEventList)
def list_contract_audit_events_endpoint(
    contract_id: int,
    full: bool = False,
    limit: int = 8,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalContractAuditEventList:
    contract = get_contract(contract_id, current_user, db)
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


@router.post("/contracts/{contract_id}/verification/regenerate", response_model=LegalContractVerificationDetail)
def regenerate_contract_verification_endpoint(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LegalContractVerificationDetail:
    return regenerate_contract_verification(contract_id, current_user, db)
