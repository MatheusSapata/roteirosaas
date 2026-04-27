from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_agency_membership
from app.models.document import Document
from app.models.user import User

router = APIRouter()


@router.delete("/{document_id}", status_code=204, response_class=Response)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.deleted_at.is_(None))
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado.")

    require_agency_membership(db=db, agency_id=document.agency_id, user_id=current_user.id)
    document.deleted_at = datetime.utcnow()
    db.add(document)
    db.commit()
    return Response(status_code=204)
