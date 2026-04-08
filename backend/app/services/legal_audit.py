from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.legal import (
    LegalContract,
    LegalContractAuditActorType,
    LegalContractAuditEvent,
    LegalContractAuditEventType,
)


@dataclass(frozen=True)
class AuditEventDefinition:
    title: str
    description: str | None
    actor_type: LegalContractAuditActorType
    allow_duplicates: bool = False


class LegalContractAuditService:
    DEFAULT_LIMIT = 8
    MAX_LIMIT = 100

    _definitions: dict[LegalContractAuditEventType, AuditEventDefinition] = {
        LegalContractAuditEventType.contract_created: AuditEventDefinition(
            title="Contrato gerado",
            description="Registro criado com base nos dados enviados pela agência.",
            actor_type=LegalContractAuditActorType.system,
        ),
        LegalContractAuditEventType.agency_signature_applied: AuditEventDefinition(
            title="Assinatura institucional aplicada",
            description="A agência associou sua assinatura oficial ao documento.",
            actor_type=LegalContractAuditActorType.agency,
        ),
        LegalContractAuditEventType.signature_link_created: AuditEventDefinition(
            title="Link de assinatura criado",
            description="Token único e link seguro liberados para o cliente.",
            actor_type=LegalContractAuditActorType.system,
        ),
        LegalContractAuditEventType.signer_opened: AuditEventDefinition(
            title="Cliente acessou o documento",
            description="O link de assinatura foi aberto pelo cliente.",
            actor_type=LegalContractAuditActorType.customer,
        ),
        LegalContractAuditEventType.customer_signed: AuditEventDefinition(
            title="Cliente assinou o contrato",
            description="Assinatura eletrônica registrada com sucesso.",
            actor_type=LegalContractAuditActorType.customer,
            allow_duplicates=True,
        ),
        LegalContractAuditEventType.signed_pdf_generated: AuditEventDefinition(
            title="PDF final gerado",
            description="Versão assinada consolidada e salva para consulta.",
            actor_type=LegalContractAuditActorType.system,
            allow_duplicates=True,
        ),
        LegalContractAuditEventType.document_hashed: AuditEventDefinition(
            title="Hash de integridade calculado",
            description="Resumo criptográfico calculado para garantir autenticidade.",
            actor_type=LegalContractAuditActorType.system,
            allow_duplicates=True,
        ),
        LegalContractAuditEventType.verification_published: AuditEventDefinition(
            title="Verificação publicada",
            description="Link público de verificação liberado na plataforma.",
            actor_type=LegalContractAuditActorType.system,
        ),
        LegalContractAuditEventType.qr_generated: AuditEventDefinition(
            title="QR code gerado",
            description="Código visual criado para validar o documento em segundos.",
            actor_type=LegalContractAuditActorType.system,
        ),
        LegalContractAuditEventType.verification_regenerated: AuditEventDefinition(
            title="Verificação regenerada",
            description="Processo de verificação atualizado manualmente pela agência.",
            actor_type=LegalContractAuditActorType.agency,
            allow_duplicates=True,
        ),
    }

    def record_event(
        self,
        contract: LegalContract | int,
        event_type: LegalContractAuditEventType,
        db: Session,
        *,
        title: str | None = None,
        description: str | None = None,
        actor_type: LegalContractAuditActorType | None = None,
        metadata: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        allow_duplicates: bool | None = None,
        is_reconstructed: bool = False,
        force_unique: bool = False,
    ) -> LegalContractAuditEvent | None:
        contract_id = contract if isinstance(contract, int) else contract.id
        if not contract_id:
            return None

        definition = self._definitions.get(event_type)
        if not definition:
            return None

        effective_allow_duplicates = allow_duplicates
        if effective_allow_duplicates is None:
            effective_allow_duplicates = definition.allow_duplicates
        should_dedupe = not effective_allow_duplicates or force_unique

        if should_dedupe and self._event_exists(contract_id, event_type, db):
            return None

        event = LegalContractAuditEvent(
            contract_id=contract_id,
            event_type=event_type.value,
            title=title or definition.title,
            description=description or definition.description,
            actor_type=(actor_type or definition.actor_type).value,
            occurred_at=occurred_at or datetime.utcnow(),
            metadata_json=metadata,
            is_reconstructed=is_reconstructed,
        )
        db.add(event)
        return event

    def list_events_for_contract(
        self,
        contract_id: int,
        db: Session,
        limit: int | None = None,
    ) -> tuple[list[LegalContractAuditEvent], bool]:
        if not contract_id:
            return [], False

        if limit and limit > 0:
            query = (
                db.query(LegalContractAuditEvent)
                .filter(LegalContractAuditEvent.contract_id == contract_id)
                .order_by(
                    LegalContractAuditEvent.occurred_at.desc(),
                    LegalContractAuditEvent.id.desc(),
                )
            )
            rows = query.limit(limit + 1).all()
            has_more = len(rows) > limit
            events = list(reversed(rows[:limit]))
            return events, has_more

        events = (
            db.query(LegalContractAuditEvent)
            .filter(LegalContractAuditEvent.contract_id == contract_id)
            .order_by(
                LegalContractAuditEvent.occurred_at.asc(),
                LegalContractAuditEvent.id.asc(),
            )
            .all()
        )
        return events, False

    def serialize_event(self, event: LegalContractAuditEvent) -> dict[str, Any]:
        return {
            "id": event.id,
            "contract_id": event.contract_id,
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description,
            "actor_type": event.actor_type,
            "occurred_at": event.occurred_at,
            "is_reconstructed": event.is_reconstructed,
            "metadata": event.metadata_json or None,
        }

    def ensure_backfilled_events(self, contract: LegalContract, db: Session) -> bool:
        created_any = False
        if contract.created_at:
            created_any |= self._ensure_backfill_event(
                contract,
                LegalContractAuditEventType.contract_created,
                contract.created_at,
                db,
            )
        if contract.signature_signed_at:
            created_any |= self._ensure_backfill_event(
                contract,
                LegalContractAuditEventType.customer_signed,
                contract.signature_signed_at,
                db,
            )
        if contract.signed_pdf_url and contract.signed_pdf_generated_at:
            created_any |= self._ensure_backfill_event(
                contract,
                LegalContractAuditEventType.signed_pdf_generated,
                contract.signed_pdf_generated_at,
                db,
            )
        if contract.document_hash:
            created_any |= self._ensure_backfill_event(
                contract,
                LegalContractAuditEventType.document_hashed,
                contract.verification_generated_at or contract.signed_pdf_generated_at or contract.updated_at,
                db,
            )
        if contract.verification_url and contract.verification_generated_at:
            created_any |= self._ensure_backfill_event(
                contract,
                LegalContractAuditEventType.verification_published,
                contract.verification_generated_at,
                db,
            )
        return created_any

    def normalize_limit(self, limit: int | None, full: bool = False) -> int | None:
        if full or not limit:
            return None
        sanitized = max(1, min(limit, self.MAX_LIMIT))
        return sanitized

    def _ensure_backfill_event(
        self,
        contract: LegalContract,
        event_type: LegalContractAuditEventType,
        occurred_at: datetime | None,
        db: Session,
    ) -> bool:
        if not occurred_at:
            return False
        created = self.record_event(
            contract,
            event_type,
            db,
            occurred_at=occurred_at,
            is_reconstructed=True,
            allow_duplicates=False,
            force_unique=True,
        )
        return created is not None

    def _event_exists(
        self,
        contract_id: int,
        event_type: LegalContractAuditEventType,
        db: Session,
    ) -> bool:
        return (
            db.query(LegalContractAuditEvent.id)
            .filter(
                LegalContractAuditEvent.contract_id == contract_id,
                LegalContractAuditEvent.event_type == event_type.value,
            )
            .limit(1)
            .first()
            is not None
        )


legal_contract_audit_service = LegalContractAuditService()
