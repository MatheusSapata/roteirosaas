from __future__ import annotations

import base64
import binascii
import logging
import re
from datetime import date, datetime
from html import escape
from io import BytesIO
from secrets import token_urlsafe
from typing import Iterable

from fastapi import HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload
from xhtml2pdf import pisa



from app.models import (
    AgencyUser,
    LegalContract,
    LegalContractSignatureStatus,
    LegalContractSignatureType,
    LegalContractStatus,
    LegalContractTemplate,
    LegalSignatureProfile,
    Product,
    Sale,
    SalePassenger,
    SalePassengerStatus,
    SalePaymentStatus,
    User,
)

from app.schemas.legal import (
    LegalContractOut,
    LegalContractSignaturePublic,
    LegalContractSignatureSubmitPayload,
    LegalContractSignatureSubmitResponse,
    LegalContractVerificationDetail,
    LegalContractVerificationStatus,
    LegalSignatureProfilePayload,
    LegalSignatureProfileResponse,
    LegalTemplateDetail,
    LegalTemplatePayload,
    LegalTemplateSummary,
    LegalVariableCategory,
    LegalVariableDefinition,
)

from app.core.config import get_settings
from app.services.media_storage import media_storage
from app.services.legal_verification import legal_verification_service



logger = logging.getLogger(__name__)



LocalizedTextDict = dict[str, str]

_SANITIZE_RE = re.compile(r"<(script|style).*?>.*?</\1>", flags=re.IGNORECASE | re.DOTALL)
_SANITIZE_RE = re.compile(r"<(script|style).*?>.*?</\1>", flags=re.IGNORECASE | re.DOTALL)
PASSENGERS_PLACEHOLDER = "[[PASSAGEIROS]]"
SIGNATURE_PLACEHOLDER = "[[ASSINATURAS]]"
_SIGNATURE_MARKER = "__contract_signature__"
_BLOCK_RE = re.compile(r"(<(p|ol|ul)(?:\s[^>]*)?>.*?</\2>)", flags=re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+", flags=re.UNICODE)
_DATA_URL_PREFIX = "data:"
_MAX_SIGNATURE_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB
_TYPED_SIGNATURE_STYLES = {"classic", "cursive", "elegant"}
_DEFAULT_TYPED_STYLE = "classic"


def _build_signature_link(token: str) -> str:
    settings = get_settings()
    base = settings.resolved_signature_base_url.rstrip("/")
    return f"{base}/assinatura/{token}"


def _ensure_signature_metadata(contract: LegalContract) -> bool:
    changed = False

    if not contract.signature_status:
        contract.signature_status = LegalContractSignatureStatus.pending.value
        changed = True

    if contract.status != LegalContractStatus.generated.value or not contract.pdf_url:
        return changed

    if not contract.signature_token:
        contract.signature_token = token_urlsafe(32)
        changed = True

    if contract.signature_token:
        expected_link = _build_signature_link(contract.signature_token)
        if contract.signature_link != expected_link:
            contract.signature_link = expected_link
            changed = True

    return changed


def _decode_signature_image(data_url: str) -> tuple[bytes, str]:
    if not data_url or not data_url.startswith(_DATA_URL_PREFIX):
        raise HTTPException(status_code=400, detail="Imagem de assinatura inválida.")

    try:
        metadata, encoded = data_url.split(",", 1)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail="Imagem de assinatura inválida.") from exc

    if ";base64" not in metadata:
        raise HTTPException(status_code=400, detail="Imagem de assinatura inválida.")

    mime = metadata[len(_DATA_URL_PREFIX) : metadata.index(";")].strip().lower()
    if mime not in {"image/png", "image/jpeg"}:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")

    try:
        binary = base64.b64decode(encoded.strip(), validate=True)
    except (binascii.Error, ValueError) as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail="Imagem de assinatura inválida.") from exc

    if len(binary) > _MAX_SIGNATURE_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Imagem de assinatura muito grande.")

    return binary, mime


def _save_signature_image(data: bytes, mime: str, contract: LegalContract) -> str:
    extension = ".png" if mime == "image/png" else ".jpg"
    timestamp = int(datetime.utcnow().timestamp())
    filename = f"signature-contract-{contract.id}-{timestamp}{extension}"
    return media_storage.save(data, filename, mime)


def _extract_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else None


def _store_signature_image_payload(image_payload: str, prefix: str = "agency-signature") -> tuple[str, str]:
    image_bytes, mime = _decode_signature_image(image_payload)
    filename = f"{prefix}-{token_urlsafe(8)}.png" if mime == "image/png" else f"{prefix}-{token_urlsafe(8)}.jpg"
    image_url = media_storage.save(image_bytes, filename, mime)
    inline_data = _to_data_uri(image_bytes, mime)
    return image_url, inline_data


def _get_signature_profile(user: User, db: Session) -> LegalSignatureProfile | None:
    return (
        db.query(LegalSignatureProfile)
        .filter(LegalSignatureProfile.user_id == user.id)
        .first()
    )


def _get_signature_profile_by_user_id(user_id: int, db: Session) -> LegalSignatureProfile | None:
    return (
        db.query(LegalSignatureProfile)
        .filter(LegalSignatureProfile.user_id == user_id)
        .first()
    )


def _serialize_signature_profile(profile: LegalSignatureProfile) -> LegalSignatureProfileResponse:
    return LegalSignatureProfileResponse(
        signature_type=profile.signature_type,
        signature_drawn_image_url=profile.drawn_image_url,
        signature_drawn_image_data=profile.drawn_image_data,
        signature_typed_value=profile.typed_value,
        signature_font_style=profile.font_style,
        signature_display_name=profile.display_name,
        signature_role=profile.role,
        signature_company_name=profile.company_name,
        signature_city=profile.city,
        updated_at=profile.updated_at,
    )


def get_signature_profile_response(user: User, db: Session) -> LegalSignatureProfileResponse | None:
    profile = _get_signature_profile(user, db)
    if not profile:
        return None
    return _serialize_signature_profile(profile)


def save_signature_profile(payload: LegalSignatureProfilePayload, user: User, db: Session) -> LegalSignatureProfileResponse:
    profile = _get_signature_profile(user, db)
    if not profile:
        profile = LegalSignatureProfile(user_id=user.id)
    profile.agency_id = _resolve_template_agency(user, db)
    signature_type = payload.signature_type
    if signature_type == LegalContractSignatureType.drawn.value:
        if not payload.signature_drawn_image:
            raise HTTPException(status_code=400, detail="Envie a assinatura desenhada.")
        image_url, inline_data = _store_signature_image_payload(payload.signature_drawn_image, "agency-signature")
        profile.drawn_image_url = image_url
        profile.drawn_image_data = inline_data
        profile.typed_value = None
        profile.font_style = None
    else:
        typed_value = (payload.signature_typed_value or "").strip()
        if len(typed_value) < 2:
            raise HTTPException(status_code=400, detail="Informe o texto da assinatura digitada.")
        font_style = payload.signature_font_style or _DEFAULT_TYPED_STYLE
        if font_style not in _TYPED_SIGNATURE_STYLES:
            raise HTTPException(status_code=400, detail="Estilo de assinatura inválido.")
        profile.typed_value = typed_value
        profile.font_style = font_style
        profile.drawn_image_url = None
        profile.drawn_image_data = None
    display_name = payload.signature_display_name.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="Informe o nome do responsável.")
    profile.signature_type = signature_type
    profile.display_name = display_name
    profile.role = payload.signature_role.strip() if payload.signature_role else None
    profile.company_name = payload.signature_company_name.strip() if payload.signature_company_name else None
    profile.city = payload.signature_city.strip() if payload.signature_city else None
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _serialize_signature_profile(profile)


def delete_signature_profile(user: User, db: Session) -> None:
    profile = _get_signature_profile(user, db)
    if not profile:
        return
    db.delete(profile)
    db.commit()





def _localized_text(pt: str, es: str) -> LocalizedTextDict:

    return {"pt": pt, "es": es}





VARIABLE_CATEGORIES: list[dict] = [

    {

        "key": "comprador",

        "label": _localized_text("Comprador", "Comprador"),

        "variables": [

            (

                "nome_comprador",

                "Nome do comprador",

                "Nome completo informado no checkout.",

                "João da Silva",

            ),

            (

                "email_comprador",

                "Email do comprador",

                "E-mail usado na compra.",

                "joao@email.com",

            ),

            (

                "telefone_comprador",

                "Telefone do comprador",

                "Telefone principal informado.",

                "+55 11 99999-9999",

            ),

            ("cpf_comprador", "CPF do comprador", "Documento CPF informado.", "123.456.789-00"),

        ],

    },

    {

        "key": "venda",

        "label": _localized_text("Venda", "Venta"),

        "variables": [

            ("id_venda", "ID da venda", "Identificador interno da venda.", "#1024"),

            (

                "data_venda",

                "Data da venda",

                "Data em que o pagamento foi aprovado.",

                "12/04/2026",

            ),

            ("valor_total", "Valor total", "Total pago pelo cliente.", "R$ 5.500,00"),

            (

                "status_venda",

                "Status da venda",

                "Status de pagamento da venda.",

                "Pago",

            ),

        ],

    },

    {

        "key": "produto",

        "label": _localized_text("Produto", "Producto"),

        "variables": [

            ("nome_produto", "Nome do produto", "Nome da viagem/produto.", "Expedição Amazônia"),

            (

                "descricao_produto",

                "Descrição do produto",

                "Descrição cadastrada no produto.",

                "Pacote completo com traslados...",

            ),

        ],

    },

    {

        "key": "agencia",

        "label": _localized_text("Agência", "Agencia"),

        "variables": [

            ("nome_agencia", "Nome da Agência", "Nome comercial da Agência.", "LuaTur"),

            ("email_agencia", "Email da Agência", "Email usado no painel.", "contato@luatur.com"),

            ("telefone_agencia", "Telefone da Agência", "Telefone configurado.", "+55 11 98888-0000"),

            ("cnpj_agencia", "CNPJ da Agência", "CNPJ configurado para a Agência.", "12.345.678/0001-00"),

            (

                "endereco_agencia",

                "Endereço da Agência",

                "Endere~ço completo configurado no painel.",

                "Av. Paulista, 1000 - Bela Vista, São Paulo/SP",

            ),

        ],

    },

    {

        "key": "passageiros",

        "label": _localized_text("Passageiros", "Pasajeros"),

        "variables": [

            (

                "lista_passageiros",

                "Lista de passageiros",

                "Lista formatada com nome e CPF de cada passageiro.",

                "- Nome: João Silva | CPF: 123.456.789-00",

            ),

            (

                "quantidade_passageiros",

                "Quantidade de passageiros",

                "Número total de passageiros preenchidos.",

                "4",

            ),

        ],

    },

    {

        "key": "viagem",

        "label": _localized_text("Viagem", "Viaje"),

        "variables": [

            ("data_embarque", "Data de embarque", "Data de inÃƒÆ’Ã‚Â­cio da viagem.", "15/07/2026"),

            ("data_retorno", "Data de retorno", "Data estimada de retorno.", "22/07/2026"),

            (

                "cidade_embarque",

                "Cidade de embarque",

                "Local de embarque (primeiro passageiro ou metadata do produto).",

                "São Paulo",

            ),

        ],

    },

]





ALLOWED_VARIABLES = {var_key for category in VARIABLE_CATEGORIES for (var_key, *_rest) in category["variables"]}

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")





def serialize_variable_categories() -> list[LegalVariableCategory]:

    categories: list[LegalVariableCategory] = []

    for category in VARIABLE_CATEGORIES:

        variables: list[LegalVariableDefinition] = []

        for var_key, title, description, sample in category["variables"]:

            variables.append(

                LegalVariableDefinition(

                    key=var_key,

                    placeholder=f"{{{{{var_key}}}}}",

                    label=_localized_text(title, title),

                    description=_localized_text(description, description),

                    sample_value=sample,

                )

            )

        categories.append(

            LegalVariableCategory(

                key=category["key"],

                label=category["label"],

                variables=variables,

            )

        )

    return categories





def _extract_variables(content: str) -> set[str]:

    return {match.group(1).strip() for match in VARIABLE_PATTERN.finditer(content or "")}





def _validate_content_variables(content: str) -> None:

    used = _extract_variables(content)

    invalid = sorted(var for var in used if var not in ALLOWED_VARIABLES)

    if invalid:

        raise HTTPException(

            status_code=400,

            detail=f"VariÃƒÆ’Ã‚Â¡veis desconhecidas: {', '.join(invalid)}",

        )





def _clean_text(value: str | None) -> str | None:

    if value is None:

        return None

    text = value.strip()

    return text or None





def _resolve_template_agency(user: User, db: Session) -> int | None:

    membership = db.query(AgencyUser).filter(AgencyUser.user_id == user.id).order_by(AgencyUser.role.asc()).first()

    return membership.agency_id if membership else None





def serialize_template(template: LegalContractTemplate) -> LegalTemplateSummary:

    return LegalTemplateSummary(

        id=template.id,

        name=template.name,

        description=template.description,

        is_active=template.is_active,

        created_at=template.created_at,

        updated_at=template.updated_at,

    )





def serialize_template_detail(template: LegalContractTemplate) -> LegalTemplateDetail:

    summary = serialize_template(template)

    return LegalTemplateDetail(**summary.model_dump(), content=template.content)





def serialize_contract(contract: LegalContract) -> LegalContractOut:

    return LegalContractOut(

        id=contract.id,

        sale_id=contract.sale_id,

        template_id=contract.template_id,

        buyer_name=contract.buyer_name,

        product_name=contract.product_name,

        total_amount=contract.total_amount,

        currency=contract.currency,

        status=contract.status,

        pdf_url=contract.pdf_url,

        created_at=contract.created_at,

        generated_at=contract.generated_at,

        last_error=contract.last_error,
        signature_status=contract.signature_status,
        signature_token=contract.signature_token,
        signature_link=contract.signature_link,
        signature_signed_at=contract.signature_signed_at,
        signature_name=contract.signature_name,
        signature_type=contract.signature_type,
        signature_image_url=contract.signature_image_url,
        signature_ip=contract.signature_ip,
        signature_user_agent=contract.signature_user_agent,
        signed_pdf_url=contract.signed_pdf_url,
        signed_pdf_generated_at=contract.signed_pdf_generated_at,
        signed_pdf_size_bytes=contract.signed_pdf_size_bytes,
        document_hash=contract.document_hash,
        document_hash_algorithm=contract.document_hash_algorithm,
        verification_token=contract.verification_token,
        verification_url=contract.verification_url,
        verification_qr_image_data=contract.verification_qr_image_data,
        verification_generated_at=contract.verification_generated_at,
        agency_signature_status=contract.agency_signature_status,
        agency_signature_signed_at=contract.agency_signature_signed_at,
        agency_signature_type=contract.agency_signature_type,
        agency_signature_name=contract.agency_signature_name,
        agency_signature_role=contract.agency_signature_role,
        agency_signature_company=contract.agency_signature_company,
        agency_signature_city=contract.agency_signature_city,
        agency_signature_font_style=contract.agency_signature_font_style,
        agency_signature_typed_value=contract.agency_signature_typed_value,
        agency_signature_image_url=contract.agency_signature_image_url,

    )


def serialize_signature_contract(contract: LegalContract) -> LegalContractSignaturePublic:

    agency_name = contract.agency.name if contract.agency else None

    agency_logo_url = contract.agency.logo_url if contract.agency else None

    return LegalContractSignaturePublic(

        contract_id=contract.id,

        sale_id=contract.sale_id,

        token=contract.signature_token or "",

        buyer_name=contract.buyer_name,

        product_name=contract.product_name,

        currency=contract.currency,

        total_amount=contract.total_amount,

        status=contract.status,

        pdf_url=contract.pdf_url,

        signature_status=contract.signature_status,

        signature_signed_at=contract.signature_signed_at,

        signature_name=contract.signature_name,

        signature_type=contract.signature_type,

        signature_image_url=contract.signature_image_url,

        agency_name=agency_name,

        agency_logo_url=agency_logo_url,

        created_at=contract.created_at,

        generated_at=contract.generated_at,

        signed_pdf_url=contract.signed_pdf_url,

        signed_pdf_generated_at=contract.signed_pdf_generated_at,

        signed_pdf_size_bytes=contract.signed_pdf_size_bytes,

        document_hash=contract.document_hash,

        document_hash_algorithm=contract.document_hash_algorithm,

        verification_token=contract.verification_token,

        verification_url=contract.verification_url,

        verification_qr_image_data=contract.verification_qr_image_data,

        verification_generated_at=contract.verification_generated_at,
        agency_signature_status=contract.agency_signature_status,
        agency_signature_signed_at=contract.agency_signature_signed_at,
        agency_signature_type=contract.agency_signature_type,
        agency_signature_name=contract.agency_signature_name,
        agency_signature_role=contract.agency_signature_role,
        agency_signature_company=contract.agency_signature_company,
        agency_signature_city=contract.agency_signature_city,
        agency_signature_font_style=contract.agency_signature_font_style,
        agency_signature_typed_value=contract.agency_signature_typed_value,
        agency_signature_image_url=contract.agency_signature_image_url,

    )


def _determine_verification_status(contract: LegalContract) -> LegalContractVerificationStatus:

    if contract.signature_status != LegalContractSignatureStatus.signed.value:

        return LegalContractVerificationStatus.pending

    if not contract.signed_pdf_url or not contract.document_hash:

        return LegalContractVerificationStatus.incomplete

    return LegalContractVerificationStatus.valid


def _verification_status_message(status: LegalContractVerificationStatus) -> str:

    mapping = {

        LegalContractVerificationStatus.valid: "Documento válido e íntegro.",

        LegalContractVerificationStatus.pending: "Aguardando assinatura do cliente.",

        LegalContractVerificationStatus.incomplete: "Documento assinado, mas aguardando finalização de verificação.",

        LegalContractVerificationStatus.invalid: "Documento inválido ou divergente.",

        LegalContractVerificationStatus.not_found: "Documento não encontrado.",

    }

    return mapping.get(status, "Status indisponível.")


def serialize_verification_detail(contract: LegalContract) -> LegalContractVerificationDetail:

    status = _determine_verification_status(contract)

    agency_name = contract.agency.name if contract.agency else None

    agency_logo_url = contract.agency.logo_url if contract.agency else None

    return LegalContractVerificationDetail(

        status=status,

        contract_id=contract.id,

        sale_id=contract.sale_id,

        buyer_name=contract.buyer_name,

        product_name=contract.product_name,

        agency_name=agency_name,

        agency_logo_url=agency_logo_url,

        created_at=contract.created_at,

        generated_at=contract.generated_at,

        signature_signed_at=contract.signature_signed_at,

        signature_status=contract.signature_status,

        signature_type=contract.signature_type,

        agency_signature_status=contract.agency_signature_status,

        agency_signature_signed_at=contract.agency_signature_signed_at,

        document_hash=contract.document_hash,

        document_hash_algorithm=contract.document_hash_algorithm,

        signed_pdf_url=contract.signed_pdf_url,

        signed_pdf_generated_at=contract.signed_pdf_generated_at,

        signed_pdf_size_bytes=contract.signed_pdf_size_bytes,

        pdf_url=contract.pdf_url,

        verification_token=contract.verification_token,

        verification_url=contract.verification_url,

        verification_qr_image_data=contract.verification_qr_image_data,

        verification_generated_at=contract.verification_generated_at,

        message=_verification_status_message(status),

    )




def list_templates(user: User, db: Session) -> list[LegalTemplateSummary]:

    templates = (

        db.query(LegalContractTemplate)

        .filter(LegalContractTemplate.user_id == user.id)

        .order_by(LegalContractTemplate.updated_at.desc().nullslast(), LegalContractTemplate.created_at.desc())

        .all()

    )

    return [serialize_template(template) for template in templates]





def get_template_by_id(template_id: int, user: User, db: Session) -> LegalContractTemplate:

    template = (

        db.query(LegalContractTemplate)

        .filter(LegalContractTemplate.id == template_id, LegalContractTemplate.user_id == user.id)

        .first()

    )

    if not template:

        raise HTTPException(status_code=404, detail="Template não encontrado.")

    return template





def create_template(payload: LegalTemplatePayload, user: User, db: Session) -> LegalContractTemplate:

    _validate_content_variables(payload.content)

    template = LegalContractTemplate(

        user_id=user.id,

        agency_id=_resolve_template_agency(user, db),

        name=payload.name.strip(),

        description=_clean_text(payload.description),

        content=payload.content.strip(),

        is_active=payload.is_active,

    )

    db.add(template)

    db.commit()

    db.refresh(template)

    return template





def update_template(template: LegalContractTemplate, payload: LegalTemplatePayload, db: Session) -> LegalContractTemplate:

    _validate_content_variables(payload.content)

    template.name = payload.name.strip()

    template.description = _clean_text(payload.description)

    template.content = payload.content.strip()

    template.is_active = payload.is_active

    db.add(template)

    db.commit()

    db.refresh(template)

    return template





def delete_template(template: LegalContractTemplate, db: Session) -> None:

    db.delete(template)

    db.commit()





def list_contracts(user: User, db: Session) -> list[LegalContractOut]:

    contracts = (

        db.query(LegalContract)

        .filter(LegalContract.user_id == user.id)

        .order_by(LegalContract.created_at.desc())

        .all()

    )

    metadata_updated = False
    signed_generated = False

    for contract in contracts:

        if _ensure_signature_metadata(contract):

            metadata_updated = True

            db.add(contract)

        if _ensure_signed_pdf(contract, db):

            signed_generated = True

        if legal_verification_service.ensure_contract_metadata(contract):
            metadata_updated = True
            db.add(contract)

    if metadata_updated or signed_generated:

        db.commit()


    return [serialize_contract(contract) for contract in contracts]





def get_contract(contract_id: int, user: User, db: Session) -> LegalContract:

    contract = (

        db.query(LegalContract)

        .filter(LegalContract.id == contract_id, LegalContract.user_id == user.id)

        .first()

    )

    if not contract:

        raise HTTPException(status_code=404, detail="Contrato não encontrado.")

    updated = False

    if _ensure_signature_metadata(contract):

        db.add(contract)

        updated = True

    if _ensure_signed_pdf(contract, db):

        updated = True

    if legal_verification_service.ensure_contract_metadata(contract):
        db.add(contract)
        updated = True

    if updated:

        db.commit()

        db.refresh(contract)

    return contract


def get_contract_verification_detail(contract_id: int, user: User, db: Session) -> LegalContractVerificationDetail:

    contract = (

        db.query(LegalContract)

        .options(joinedload(LegalContract.agency))

        .filter(LegalContract.id == contract_id, LegalContract.user_id == user.id)

        .first()

    )

    if not contract:

        raise HTTPException(status_code=404, detail="Contrato não encontrado.")

    updated = False

    if _ensure_signature_metadata(contract):

        db.add(contract)

        updated = True

    if _ensure_signed_pdf(contract, db):

        updated = True

    if legal_verification_service.ensure_contract_metadata(contract):

        db.add(contract)

        updated = True

    if updated:

        db.commit()

        db.refresh(contract)

    return serialize_verification_detail(contract)


def regenerate_contract_verification(contract_id: int, user: User, db: Session) -> LegalContractVerificationDetail:

    contract = (

        db.query(LegalContract)

        .options(joinedload(LegalContract.agency))

        .filter(LegalContract.id == contract_id, LegalContract.user_id == user.id)

        .with_for_update(of=LegalContract)

        .first()

    )

    if not contract:

        raise HTTPException(status_code=404, detail="Contrato não encontrado.")

    if contract.signature_status != LegalContractSignatureStatus.signed.value:

        raise HTTPException(status_code=400, detail="Contrato ainda não foi assinado.")

    _generate_signed_contract_pdf(contract, db)

    db.commit()

    db.refresh(contract)

    return serialize_verification_detail(contract)


def get_contract_verification_by_token(token: str, db: Session) -> LegalContractVerificationDetail:

    normalized = token.strip()

    if not normalized:

        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    contract = (

        db.query(LegalContract)

        .options(joinedload(LegalContract.agency))

        .filter(
            or_(
                LegalContract.verification_token == normalized,
                LegalContract.signature_token == normalized,
            )
        )

        .first()

    )

    if not contract:

        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    updated = False

    if _ensure_signature_metadata(contract):

        db.add(contract)

        updated = True

    if _ensure_signed_pdf(contract, db):

        updated = True

    if legal_verification_service.ensure_contract_metadata(contract):

        db.add(contract)

        updated = True

    if updated:

        db.commit()

        db.refresh(contract)

    return serialize_verification_detail(contract)





def _load_sale_for_contract(sale_id: int, db: Session) -> Sale:

    sale = (

        db.query(Sale)

        .options(

            joinedload(Sale.product).joinedload(Product.agency),

            joinedload(Sale.user),

            selectinload(Sale.passengers),

        )

        .filter(Sale.id == sale_id)

        .first()

    )

    if not sale:

        raise HTTPException(status_code=404, detail="Venda não encontrada.")

    return sale





def _format_currency(amount_cents: int, currency: str) -> str:

    symbol = "R$" if currency.upper() == "BRL" else currency.upper()

    formatted = f"{amount_cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return f"{symbol} {formatted}"





def _format_date(value: datetime | date | str | None) -> str:

    if not value:

        return ""

    if isinstance(value, str):

        try:

            parsed = datetime.fromisoformat(value)

            return parsed.strftime("%d/%m/%Y")

        except ValueError:

            return value

    return value.strftime("%d/%m/%Y")





def _format_agency_address(user: User | None) -> str:

    if not user:

        return ""

    segments: list[str] = []

    street_parts = [user.address_street, user.address_number]

    street_line = " ".join(part.strip() for part in street_parts if part and part.strip())

    if user.address_complement and user.address_complement.strip():

        street_line = f"{street_line}, {user.address_complement.strip()}" if street_line else user.address_complement.strip()

    if street_line:

        segments.append(street_line)

    neighborhood_city = ", ".join(

        part.strip()

        for part in [user.address_neighborhood, user.address_city]

        if part and part.strip()

    )

    if neighborhood_city:

        segments.append(neighborhood_city)

    state_zip = " ".join(

        part.strip()

        for part in [user.address_state, user.address_zipcode]

        if part and part.strip()

    )

    if state_zip:

        segments.append(state_zip)

    return " - ".join(segments)







def _replace_variables(content: str, data: dict[str, str]) -> str:
    def _replacer(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return data.get(key, '' )

    return VARIABLE_PATTERN.sub(_replacer, content)

def _sanitize_editor_content(content: str) -> str:

    if not content:

        return ""

    cleaned = _SANITIZE_RE.sub("", content)

    cleaned = cleaned.replace("<p><br></p>", "<p>&nbsp;</p>")

    return cleaned





def _render_passenger_list(passengers: Iterable) -> str:

    lines = []

    for passenger in passengers:

        cpf = passenger.cpf or "N/A"

        line = f"- Nome: {passenger.name} | CPF: {cpf}"

        if passenger.whatsapp:

            line += f" | WhatsApp: {passenger.whatsapp}"

        lines.append(line)

    return "\n".join(lines)


def _build_contract_context(sale: Sale, product: Product | None) -> dict[str, str]:
    agency = product.agency if product else None
    passengers = sale.passengers or []
    passenger_list = _render_passenger_list(passengers)
    first_boarding = next((p.boarding_location for p in passengers if p.boarding_location), None)
    metadata = sale.metadata_json or {}
    user = sale.user

    return {
        "nome_comprador": sale.customer_name or "",
        "email_comprador": sale.customer_email or "",
        "telefone_comprador": sale.customer_phone or "",
        "cpf_comprador": metadata.get("customer_cpf", ""),
        "id_venda": f"#{sale.id}",
        "data_venda": _format_date(sale.paid_at or sale.created_at),
        "valor_total": _format_currency(sale.gross_amount, sale.currency),
        "status_venda": sale.payment_status.capitalize(),
        "nome_produto": sale.product_title or (product.name if product else ""),
        "descricao_produto": sale.product_description or (product.description if product else ""),
        "nome_agencia": agency.name if agency else "",
        "email_agencia": user.email if user else "",
        "telefone_agencia": user.whatsapp if user else "",
        "cnpj_agencia": user.cnpj or "",
        "endereco_agencia": _format_agency_address(user),
        "lista_passageiros": passenger_list,
        "quantidade_passageiros": str(len(passengers)),
        "data_embarque": _format_date(product.trip_date if product and product.trip_date else None),
        "data_retorno": _format_date(metadata.get("trip_return_date")),
        "cidade_embarque": first_boarding or metadata.get("boarding_city", ""),
    }







def _render_passenger_table_html(passengers: list[SalePassenger]) -> str:
    if not passengers:
        return "<p class='muted'>Não há passageiros cadastrados até o momento.</p>"
    items: list[str] = []
    for passenger in passengers:
        name = passenger.name or "Passageiro sem nome"
        cpf = passenger.cpf or "não informado"
        phone = passenger.phone or passenger.whatsapp or ""
        phone_text = f" | Telefone: {escape(phone)}" if phone else ""
        items.append(f"<li>Nome: {escape(name)} | CPF: {escape(cpf)}{phone_text}</li>")
    return f"<ul class='passenger-list'>{''.join(items)}</ul>"


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def _strip_tags(value: str | None) -> str:
    if not value:
        return ""
    return _TAG_RE.sub("", value)


def _normalize_whitespace(value: str) -> str:
    if not value:
        return ""
    return _WHITESPACE_RE.sub(" ", value).strip()


def _looks_like_clause_title(value: str) -> bool:
    normalized = _normalize_whitespace(value)
    if not normalized:
        return False
    letters = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ0-9 ]", "", normalized)
    if not letters:
        return False
    return letters == letters.upper() and len(letters) <= 120


def _split_blocks(html: str) -> list[str]:
    blocks = [match.group(0) for match in _BLOCK_RE.finditer(html)]
    if blocks:
        return blocks
    return [html] if html.strip() else []


def _extract_clause_sections(html: str) -> list[tuple[str, list[str]]]:
    blocks = _split_blocks(html)
    clauses: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_blocks: list[str] = []

    for block in blocks:
        text = _normalize_whitespace(_strip_tags(block))
        if text and _looks_like_clause_title(text):
            if current_blocks:
                clauses.append((current_title or "CLÁUSULA", current_blocks))
                current_blocks = []
            current_title = text
        else:
            if current_title is None and not clauses:
                current_title = "CLÁUSULA"
            if block.strip():
                current_blocks.append(block)

    if current_blocks:
        clauses.append((current_title or "CLÁUSULA", current_blocks))

    if not clauses and html.strip():
        clauses.append(("CLÁUSULAS GERAIS", [html]))

    return clauses


def _wrap_clause(number: int, title: str, blocks: list[str]) -> str:
    body = "".join(blocks).strip()
    if not body:
        return ""
    heading = f"<h2><span class='clause-number'>{number}.</span> {escape(title)}</h2>"
    return f"<section class='clause'>{heading}{body}</section>"


def _render_agency_signature_block(agency_name: str, signature: dict | None) -> str:
    if not signature:
        return f"""
        <div class="signature-block signature-block--agency">
          <div class="signature-line"></div>
          <p><strong>{escape(agency_name)}</strong></p>
          <p class="signature-label">Contratada</p>
        </div>
        """
    visual_html = ""
    if signature.get("image"):
        visual_html = f'<img src="{signature["image"]}" alt="Assinatura institucional" class="agency-signature__image" />'
    elif signature.get("typed_value"):
        style = signature.get("font_style") or _DEFAULT_TYPED_STYLE
        css_class = (
            f"agency-signature__typed agency-signature__typed--{style}"
            if style in _TYPED_SIGNATURE_STYLES
            else "agency-signature__typed agency-signature__typed--classic"
        )
        visual_html = f'<p class="{css_class}">{escape(signature["typed_value"] or signature.get("name") or "")}</p>'
    else:
        visual_html = '<div class="signature-line"></div>'
    role_line = ""
    if signature.get("role"):
        role_line = f'<p class="agency-signature__role">{escape(signature["role"])}</p>'
    badge_text = "Assinatura institucional da contratada"
    details = ""
    company = signature.get("company")
    city = signature.get("city")
    if company or city:
        parts = [part for part in [company, city] if part]
        details = f'<p class="signature-label">{" · ".join(escape(part) for part in parts)}</p>'
    return f"""
        <div class="signature-block signature-block--agency">
          {visual_html}
          <p class="agency-signature__name">{escape(signature.get("name") or agency_name)}</p>
          {role_line}
          {details}
          <p class="agency-signature__badge">{badge_text}</p>
        </div>
    """


def _render_signature_block(agency_name: str, buyer_name: str, agency_signature: dict | None) -> str:
    agency_block = _render_agency_signature_block(agency_name, agency_signature)
    return f"""
    <section class="signature-area">
      {agency_block}
      <div class="signature-block">
        <div class="signature-line"></div>
        <p><strong>{escape(buyer_name)}</strong></p>
        <p class="signature-label">Contratante</p>
      </div>
    </section>
    """


def _format_signature_type_label(signature_type: str | None) -> str:
    if signature_type == LegalContractSignatureType.drawn.value:
        return "Assinatura desenhada"
    return "Assinatura digitada"


def _summarize_user_agent(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    ua = user_agent.lower()
    browser = None
    if "chrome" in ua and "edge" not in ua:
        browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edge" in ua:
        browser = "Edge"
    os = None
    if "windows" in ua:
        os = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os = "macOS"
    elif "android" in ua:
        os = "Android"
    elif "iphone" in ua or "ios" in ua:
        os = "iOS"
    elif "linux" in ua:
        os = "Linux"
    if browser and os:
        return f"{browser} / {os}"
    cleaned = user_agent.strip()
    if len(cleaned) > 80:
        return f"{cleaned[:77]}..."
    return cleaned or None


def _to_data_uri(data: bytes, mime: str) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _mask_signature_token(token: str | None) -> str | None:
    if not token:
        return None
    if len(token) <= 6:
        return token
    return f"...{token[-8:]}"


def _render_signature_summary_block(
    contract: LegalContract,
    inline_signature_image: str | None = None,
    verification: dict | None = None,
) -> str:
    signer_name = contract.signature_name or contract.buyer_name or "Assinante"
    signed_at = contract.signature_signed_at or datetime.utcnow()
    signed_label = signed_at.strftime("%d/%m/%Y %H:%M")
    signature_type_label = _format_signature_type_label(contract.signature_type)
    masked_token = _mask_signature_token(contract.signature_token)
    evidence_parts: list[str] = []
    if contract.signature_ip:
        evidence_parts.append(contract.signature_ip)
    summarized_agent = _summarize_user_agent(contract.signature_user_agent)
    if summarized_agent:
        evidence_parts.append(summarized_agent)
    evidence_text = " · ".join(evidence_parts)

    if inline_signature_image:
        visual_html = f'<img src="{inline_signature_image}" alt="Assinatura eletrônica" class="signature-panel__image" />'
    else:
        visual_html = f'<p class="signature-panel__handwrite">{escape(signer_name)}</p>'

    hash_label = None
    hash_algorithm = None
    verification_url = None
    verification_qr = None
    if verification:
        hash_label = verification.get("document_hash_preview") or verification.get("document_hash")
        verification_url = verification.get("verification_url")
        verification_qr = verification.get("verification_qr_image_data")
        hash_algorithm = verification.get("document_hash_algorithm")

    verification_block = ""
    if verification_qr or verification_url:
        verification_block = f"""
        <div class="signature-panel__verification">
          <div class="signature-panel__verification-qr">
            {'<img src="' + verification_qr + '" alt="QR Code de verificação" />' if verification_qr else ''}
          </div>
          <div class="signature-panel__verification-meta">
            <p class="signature-panel__verification-title">Validação pública</p>
            <p class="signature-panel__verification-hint">Escaneie para verificar</p>
            {f'<p class="signature-panel__verification-url">{escape(verification_url)}</p>' if verification_url else ''}
            {f'<p class="signature-panel__verification-hash"><strong>Hash:</strong> {escape(hash_label)}</p>' if hash_label else ''}
            {f'<p class="signature-panel__verification-algorithm">{escape((hash_algorithm or "SHA-256").upper())}</p>' if hash_label else ''}
          </div>
        </div>
        """

    return f"""
    <section class="signature-summary">
      <div class="signature-panel">
        <div class="signature-panel__header">
          <p class="signature-panel__title">DOCUMENTO ASSINADO ELETRONICAMENTE</p>
          <span class="signature-panel__badge">✔ Verificação eletrônica</span>
        </div>
        <div class="signature-panel__visual">
          {visual_html}
        </div>
        <p class="signature-panel__name">{escape(signer_name)}</p>
        <p class="signature-panel__role">Contratante</p>
        <div class="signature-panel__audit">
          <span class="signature-panel__audit-item"><strong>Assinado por:</strong> {escape(signer_name)}</span>
          <span class="signature-panel__audit-item"><strong>Data e hora:</strong> {escape(signed_label)}</span>
          <span class="signature-panel__audit-item"><strong>Tipo:</strong> {escape(signature_type_label)}</span>
          {f'<span class="signature-panel__audit-item"><strong>Evidência:</strong> {escape(evidence_text)}</span>' if evidence_text else ''}
          {f'<span class="signature-panel__audit-item"><strong>Token:</strong> {escape(masked_token)}</span>' if masked_token else ''}
          {f'<span class="signature-panel__audit-item"><strong>Hash resumido:</strong> {escape(hash_label)}</span>' if hash_label else ''}
        </div>
        {verification_block}
      </div>
    </section>
    """


def build_contract_pdf_html(
    *,
    contract: LegalContract,
    sale: Sale,
    template: LegalContractTemplate,
    context: dict[str, str],
    agency_signature: dict | None = None,
    signature_summary_html: str | None = None,
) -> str:
    generated_label = (contract.generated_at or datetime.utcnow()).strftime("%d/%m/%Y %H:%M")
    passenger_list = list(sale.passengers)
    passenger_html = _render_passenger_table_html(passenger_list)
    agency_name = _clean_text(context.get("nome_agencia")) or "Contratada"
    buyer_name = (
        _clean_text(context.get("nome_comprador")) or sale.customer_name or sale.customer_email or "Contratante"
    )
    agency_doc = _clean_text(context.get("cnpj_agencia")) or "não informado"
    agency_address = _clean_text(context.get("endereco_agencia"))
    buyer_doc = _clean_text(context.get("cpf_comprador")) or "não informado"

    agency_sentence = f"{escape(agency_name)}, inscrita no CNPJ sob nº {escape(agency_doc)}"
    if agency_address:
        agency_sentence += f", com sede em {escape(agency_address)}"
    buyer_sentence = f"{escape(buyer_name)}, inscrito no CPF sob nº {escape(buyer_doc)}"
    preamble_text = (
        f"Pelo presente instrumento particular, de um lado {agency_sentence}, doravante denominada CONTRATADA, "
        f"e, de outro lado, {buyer_sentence}, doravante denominado CONTRATANTE, têm entre si justo e contratado o seguinte."
    )
    preamble_html = f"<p class='preamble'>{preamble_text}</p>"

    rendered_content = _sanitize_editor_content(_replace_variables(template.content or "", context))
    content_with_passengers = rendered_content.replace(PASSENGERS_PLACEHOLDER, passenger_html)
    signature_requested = SIGNATURE_PLACEHOLDER in content_with_passengers
    content_with_markers = content_with_passengers.replace(SIGNATURE_PLACEHOLDER, _SIGNATURE_MARKER)

    clauses = _extract_clause_sections(content_with_markers)
    clause_sections: list[str] = []
    signature_rendered = False

    for index, (title, block_list) in enumerate(clauses, start=1):
        body_html = "".join(block_list).strip()
        if not body_html:
            continue
        if _SIGNATURE_MARKER in body_html:
            body_html = body_html.replace(
                _SIGNATURE_MARKER, _render_signature_block(agency_name, buyer_name, agency_signature)
            )
            signature_rendered = True
        clause_sections.append(_wrap_clause(index, title, [body_html]))

    if not clause_sections and content_with_markers.strip():
        clause_sections.append(
            _wrap_clause(1, "CLÁUSULAS GERAIS", [content_with_markers])
        )

    if not clause_sections:
        clause_sections.append(
            _wrap_clause(1, "CLÁUSULAS GERAIS", ["<p>O conteúdo do contrato será definido entre as partes.</p>"])
        )

    if not signature_rendered and signature_requested:
        clause_sections.append(_render_signature_block(agency_name, buyer_name, agency_signature))
    if not signature_requested and not signature_rendered:
        clause_sections.append(_render_signature_block(agency_name, buyer_name, agency_signature))

    if signature_summary_html:
        clause_sections.append(signature_summary_html)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <style>
      @page {{
        size: A4;
        margin: 2.8cm 2.4cm;
      }}
      body {{
        font-family: Arial, Helvetica, sans-serif;
        color: #111827;
        font-size: 11.5px;
        line-height: 1.7;
        background: #ffffff;
      }}
      h1 {{
        font-size: 22px;
        text-align: center;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }}
      .subtitle {{
        text-align: center;
        font-size: 11px;
        color: #6b7280;
        margin-bottom: 26px;
      }}
      p {{
        margin: 0 0 12px 0;
        text-align: justify;
      }}
      .preamble {{
        margin-top: 18px;
        font-size: 11.5px;
      }}
      .clause {{
        margin-top: 20px;
        page-break-inside: avoid;
      }}
      .clause h2 {{
        font-size: 12.5px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 10px 0;
        color: #1f2937;
      }}
      .clause-number {{
        margin-right: 6px;
      }}
      .passenger-list {{
        list-style: none;
        margin: 8px 0 0 0;
        padding: 0;
      }}
      .passenger-list li {{
        margin-bottom: 6px;
      }}
      .passenger-list li::before {{
        content: "- ";
      }}
      .muted {{
        color: #6b7280;
      }}
      .signature-area {{
        margin-top: 40px;
      }}
      .signature-location {{
        text-align: center;
        margin-bottom: 36px;
      }}
      .signature-block {{
        width: 100%;
        text-align: center;
        margin-bottom: 32px;
      }}
      .signature-block--agency {{
        margin-bottom: 40px;
      }}
      .signature-line {{
        border-bottom: 1px solid #111827;
        margin: 0 auto 6px auto;
        width: 70%;
        height: 0;
      }}
      .signature-label {{
        font-size: 11px;
        text-transform: uppercase;
        color: #6b7280;
        margin: 0;
      }}
      .agency-signature__image {{
        max-height: 70px;
        max-width: 260px;
        width: auto;
        height: auto;
        margin-bottom: 8px;
      }}
      .agency-signature__typed {{
        font-size: 20px;
        margin: 0 0 8px 0;
      }}
      .agency-signature__typed--classic {{
        font-family: "Times New Roman", serif;
        font-style: italic;
      }}
      .agency-signature__typed--cursive {{
        font-family: "Georgia", serif;
        font-style: italic;
        letter-spacing: 0.03em;
      }}
      .agency-signature__typed--elegant {{
        font-family: "Arial", sans-serif;
        font-weight: 600;
        letter-spacing: 0.15em;
      }}
      .agency-signature__name {{
        font-size: 12px;
        font-weight: 600;
        margin: 4px 0 2px 0;
      }}
      .agency-signature__role {{
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        color: #6b7280;
        margin-bottom: 6px;
      }}
      .agency-signature__badge {{
        font-size: 9px;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-top: 6px;
      }}
      .signature-summary {{
        margin-top: 32px;
        display: flex;
        justify-content: center;
        page-break-inside: avoid;
      }}
      .signature-panel {{
        width: 360px;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        background: #f9fafb;
        padding: 14px;
      }}
      .signature-panel__header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
      }}
      .signature-panel__title {{
        font-size: 9px;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        color: #6b7280;
        font-weight: 600;
      }}
      .signature-panel__badge {{
        font-size: 9px;
        color: #047857;
        border: 1px solid #6ee7b7;
        border-radius: 999px;
        padding: 2px 8px;
      }}
      .signature-panel__visual {{
        text-align: center;
        margin-bottom: 8px;
      }}
      .signature-panel__image {{
        max-width: 220px;
        max-height: 70px;
        width: auto;
        height: auto;
        display: inline-block;
      }}
      .signature-panel__handwrite {{
        font-size: 20px;
        font-style: italic;
        color: #0f172a;
        margin: 0;
      }}
      .signature-panel__name {{
        text-align: center;
        font-size: 12px;
        font-weight: 600;
        color: #111827;
        margin: 4px 0 0 0;
      }}
      .signature-panel__role {{
        text-align: center;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        color: #9ca3af;
        margin: 0 0 10px 0;
      }}
      .signature-panel__audit {{
        font-size: 9px;
        color: #374151;
        line-height: 1.4;
        border-top: 1px solid #e5e7eb;
        padding-top: 8px;
      }}
      .signature-panel__audit dt {{
        font-weight: 600;
        display: inline;
      }}
      .signature-panel__audit dd {{
        display: inline;
        margin: 0 0 6px 0;
      }}
      .signature-panel__audit-item {{
        display: block;
        margin-bottom: 4px;
      }}
      .signature-panel__verification {{
        display: flex;
        gap: 10px;
        align-items: center;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed #d1d5db;
      }}
      .signature-panel__verification-qr img {{
        width: 72px;
        height: 72px;
        display: block;
      }}
      .signature-panel__verification-meta {{
        font-size: 9px;
        color: #1f2937;
      }}
      .signature-panel__verification-title {{
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0 0 2px 0;
        color: #047857;
      }}
      .signature-panel__verification-hint {{
        margin: 0 0 4px 0;
        color: #6b7280;
      }}
      .signature-panel__verification-url {{
        margin: 0;
        word-break: break-all;
      }}
      .signature-panel__verification-hash,
      .signature-panel__verification-algorithm {{
        margin: 2px 0 0 0;
      }}
    </style>
  </head>
  <body>
    <h1>{escape(template.name)}</h1>
    <p class="subtitle">Documento gerado em {generated_label}</p>
    {preamble_html}
    {''.join(clause_sections)}
  </body>
</html>
"""
def _render_pdf_bytes(html: str) -> bytes:

    buffer = BytesIO()

    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8")

    if result.err:

        raise RuntimeError("Falha ao gerar PDF do contrato.")

    return buffer.getvalue()





def maybe_generate_contract_for_sale(sale: Sale, db: Session) -> LegalContract | None:

    if sale.payment_status != SalePaymentStatus.paid.value:

        return None

    if sale.passenger_status != SalePassengerStatus.completed.value:

        return None

    if not sale.product_id:

        return None



    sale_with_details = _load_sale_for_contract(sale.id, db)

    product = sale_with_details.product

    if not product or not product.template_contract_id:

        return None



    template = (

        db.query(LegalContractTemplate)

        .filter(

            LegalContractTemplate.id == product.template_contract_id,

            LegalContractTemplate.user_id == sale_with_details.user_id,

            LegalContractTemplate.is_active.is_(True),

        )

        .first()

    )

    if not template:

        return None



    contract = (

        db.query(LegalContract)

        .filter(LegalContract.sale_id == sale_with_details.id)

        .with_for_update(of=LegalContract)

        .first()

    )

    if contract and contract.status == LegalContractStatus.generated.value and contract.pdf_url:

        return contract



    if not contract:

        contract = LegalContract(

            sale_id=sale_with_details.id,

            user_id=sale_with_details.user_id,

            agency_id=sale_with_details.agency_id or (product.agency_id if product else None),

            template_id=template.id,

            buyer_name=sale_with_details.customer_name or sale_with_details.customer_email or "",

            product_name=sale_with_details.product_title or (product.name if product else ""),

            currency=sale_with_details.currency,

            total_amount=sale_with_details.gross_amount,

            status=LegalContractStatus.pending.value,

        )

        db.add(contract)

        db.flush()

    else:

        contract.template_id = template.id

        contract.user_id = sale_with_details.user_id

        contract.agency_id = sale_with_details.agency_id or (product.agency_id if product else None)

        contract.buyer_name = sale_with_details.customer_name or sale_with_details.customer_email or ""

        contract.product_name = sale_with_details.product_title or (product.name if product else "")

        contract.total_amount = sale_with_details.gross_amount

        contract.currency = sale_with_details.currency



    agency_profile = _get_signature_profile_by_user_id(contract.user_id, db)
    if agency_profile and agency_profile.agency_id and not contract.agency_id:
        contract.agency_id = agency_profile.agency_id
    _apply_agency_signature_profile(contract, agency_profile)

    try:

        context = _build_contract_context(sale_with_details, product)

        agency_signature_block = _build_agency_signature_payload(contract)

        html = build_contract_pdf_html(

            contract=contract,

            sale=sale_with_details,

            template=template,

            context=context,

            agency_signature=agency_signature_block,

        )

        pdf_bytes = _render_pdf_bytes(html)

        pdf_url = media_storage.save(pdf_bytes, f"contrato-venda-{sale_with_details.id}.pdf", "application/pdf")



        contract.pdf_url = pdf_url

        contract.status = LegalContractStatus.generated.value

        contract.generated_at = datetime.utcnow()

        contract.last_error = None

        _ensure_signature_metadata(contract)

        db.add(contract)

        db.commit()

        db.refresh(contract)

        return contract

    except Exception as exc:  # pragma: no cover - defensive logging

        logger.exception("Erro ao gerar contrato da venda %s: %s", sale_with_details.id, exc)

        contract.status = LegalContractStatus.failed.value

        contract.last_error = str(exc)

        db.add(contract)

        db.commit()

        return None


def _generate_signed_contract_pdf(
    contract: LegalContract,
    db: Session,
    inline_signature_image: str | None = None,
) -> None:
    if contract.signature_status != LegalContractSignatureStatus.signed.value:
        return
    if not contract.signature_signed_at:
        return
    if not contract.template_id:
        return

    sale = _load_sale_for_contract(contract.sale_id, db)
    product = sale.product
    template = (
        db.query(LegalContractTemplate)
        .filter(LegalContractTemplate.id == contract.template_id, LegalContractTemplate.user_id == contract.user_id)
        .first()
    )
    if not template:
        return

    context = _build_contract_context(sale, product)
    if legal_verification_service.ensure_contract_metadata(contract):
        db.add(contract)
    verification_payload = legal_verification_service.serialize_contract(contract)
    summary_block = _render_signature_summary_block(
        contract,
        inline_signature_image or contract.signature_image_data,
        verification_payload,
    )
    agency_signature_block = _build_agency_signature_payload(contract)
    html = build_contract_pdf_html(
        contract=contract,
        sale=sale,
        template=template,
        context=context,
        agency_signature=agency_signature_block,
        signature_summary_html=summary_block,
    )
    pdf_bytes = _render_pdf_bytes(html)
    legal_verification_service.attach_pdf_metadata(contract, pdf_bytes)
    if contract.document_hash != verification_payload.get("document_hash"):
        verification_payload = legal_verification_service.serialize_contract(contract)
        summary_block = _render_signature_summary_block(
            contract,
            inline_signature_image or contract.signature_image_data,
            verification_payload,
        )
        html = build_contract_pdf_html(
            contract=contract,
            sale=sale,
            template=template,
            context=context,
            agency_signature=agency_signature_block,
            signature_summary_html=summary_block,
        )
        pdf_bytes = _render_pdf_bytes(html)
        legal_verification_service.attach_pdf_metadata(contract, pdf_bytes)
    signed_pdf_url = media_storage.save(pdf_bytes, f"contrato-venda-{sale.id}-assinado.pdf", "application/pdf")
    contract.signed_pdf_url = signed_pdf_url
    contract.signed_pdf_generated_at = datetime.utcnow()
    db.add(contract)


def _ensure_signed_pdf(contract: LegalContract, db: Session) -> bool:
    if contract.signature_status != LegalContractSignatureStatus.signed.value:
        return False
    if contract.signed_pdf_url:
        return False
    try:
        _generate_signed_contract_pdf(contract, db)
        return True
    except Exception:  # pragma: no cover - defensive
        logger.exception("Falha ao gerar PDF assinado do contrato %s", contract.id)
        return False


def _apply_agency_signature_profile(contract: LegalContract, profile: LegalSignatureProfile | None) -> None:
    if not profile:
        contract.agency_signature_status = LegalContractSignatureStatus.pending.value
        contract.agency_signature_signed_at = None
        contract.agency_signature_type = None
        contract.agency_signature_name = None
        contract.agency_signature_role = None
        contract.agency_signature_company = None
        contract.agency_signature_city = None
        contract.agency_signature_font_style = None
        contract.agency_signature_typed_value = None
        contract.agency_signature_image_url = None
        contract.agency_signature_image_data = None
        return
    now = datetime.utcnow()
    contract.agency_signature_status = LegalContractSignatureStatus.signed.value
    contract.agency_signature_signed_at = now
    contract.agency_signature_type = profile.signature_type
    contract.agency_signature_name = profile.display_name
    contract.agency_signature_role = profile.role
    contract.agency_signature_company = profile.company_name
    contract.agency_signature_city = profile.city
    if profile.signature_type == LegalContractSignatureType.drawn.value:
        contract.agency_signature_image_url = profile.drawn_image_url
        contract.agency_signature_image_data = profile.drawn_image_data
        contract.agency_signature_typed_value = None
        contract.agency_signature_font_style = None
    else:
        contract.agency_signature_typed_value = profile.typed_value
        contract.agency_signature_font_style = profile.font_style or _DEFAULT_TYPED_STYLE
        contract.agency_signature_image_url = None
        contract.agency_signature_image_data = None


def _build_agency_signature_payload(contract: LegalContract) -> dict | None:
    if contract.agency_signature_status != LegalContractSignatureStatus.signed.value:
        return None
    payload: dict[str, str | None] = {
        "name": contract.agency_signature_name,
        "role": contract.agency_signature_role,
        "company": contract.agency_signature_company,
        "city": contract.agency_signature_city,
        "type": contract.agency_signature_type,
        "typed_value": contract.agency_signature_typed_value,
        "font_style": contract.agency_signature_font_style or _DEFAULT_TYPED_STYLE,
    }
    if contract.agency_signature_image_data:
        payload["image"] = contract.agency_signature_image_data
    elif contract.agency_signature_image_url:
        payload["image"] = contract.agency_signature_image_url
    else:
        payload["image"] = None
    return payload

def get_contract_for_signature(token: str, db: Session) -> LegalContractSignaturePublic:
    normalized = token.strip()
    if not normalized:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")

    contract = (
        db.query(LegalContract)
        .options(joinedload(LegalContract.agency))
        .filter(LegalContract.signature_token == normalized)
        .first()
    )

    if not contract:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")

    if _ensure_signature_metadata(contract):
        db.add(contract)
        db.commit()
        db.refresh(contract)

    if _ensure_signed_pdf(contract, db):
        db.commit()
        db.refresh(contract)

    if legal_verification_service.ensure_contract_metadata(contract):
        db.add(contract)
        db.commit()
        db.refresh(contract)

    return serialize_signature_contract(contract)


def submit_contract_signature(
    token: str,
    payload: LegalContractSignatureSubmitPayload,
    request: Request,
    db: Session,
) -> LegalContractSignatureSubmitResponse:
    normalized = token.strip()
    if not normalized:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")

    contract = (
        db.query(LegalContract)
        .options(joinedload(LegalContract.agency))
        .filter(LegalContract.signature_token == normalized)
        .with_for_update(of=LegalContract)
        .first()
    )

    if not contract:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")

    if _ensure_signature_metadata(contract):
        db.add(contract)
        db.flush()

    if contract.status != LegalContractStatus.generated.value or not contract.pdf_url:
        raise HTTPException(status_code=400, detail="Contrato ainda não está disponível para assinatura.")

    if contract.signature_status == LegalContractSignatureStatus.signed.value:
        raise HTTPException(status_code=400, detail="Contrato já assinado.")

    if not payload.accepted_terms:
        raise HTTPException(status_code=400, detail="É necessário aceitar os termos do contrato.")

    signature_type = payload.signature_type
    if signature_type not in (
        LegalContractSignatureType.typed.value,
        LegalContractSignatureType.drawn.value,
    ):
        raise HTTPException(status_code=400, detail="Tipo de assinatura inválido.")

    inline_signature_image: str | None = None

    if signature_type == LegalContractSignatureType.typed.value:
        full_name = (payload.full_name or "").strip()
        if len(full_name) < 3:
            raise HTTPException(status_code=400, detail="Informe o nome completo para assinar.")
        contract.signature_name = full_name
        contract.signature_image_url = None
        contract.signature_image_data = None
    else:
        image_payload = (payload.signature_image or "").strip()
        if not image_payload:
            raise HTTPException(status_code=400, detail="Desenhe a assinatura para continuar.")
        image_bytes, mime = _decode_signature_image(image_payload)
        image_url = _save_signature_image(image_bytes, mime, contract)
        contract.signature_image_url = image_url
        inline_signature_image = _to_data_uri(image_bytes, mime)
        contract.signature_image_data = inline_signature_image
        fallback_name = (payload.full_name or contract.buyer_name or "").strip() or None
        contract.signature_name = fallback_name

    contract.signature_type = signature_type
    contract.signature_status = LegalContractSignatureStatus.signed.value
    contract.signature_signed_at = datetime.utcnow()
    contract.signature_ip = _extract_client_ip(request)
    contract.signature_user_agent = request.headers.get("user-agent")

    db.add(contract)
    db.flush()

    try:
        _generate_signed_contract_pdf(contract, db, inline_signature_image=inline_signature_image)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Falha ao gerar PDF final assinado do contrato %s", contract.id)

    db.commit()
    db.refresh(contract)

    return LegalContractSignatureSubmitResponse(detail=serialize_signature_contract(contract))








