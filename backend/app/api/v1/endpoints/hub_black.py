"""Entrada do Viaje On Hub (Implementações Black): gerar a página de um roteiro e consultar o
andamento. Só servidor a servidor, com a chave do funil do Hub no cabeçalho x-funnel-key (a mesma
salva em Admin Master › ViajeHub). A prévia sem login fica em /public/pages/hub-preview/{token}.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.page import Page
from app.services import hub_black

router = APIRouter(prefix="/hub/black")


def require_hub_key(x_funnel_key: Optional[str] = Header(default=None)) -> None:
    if not hub_black.hub_key():
        raise HTTPException(status_code=503, detail="A conexão com o ViajeHub não está configurada no Roteiro Online.")
    if not hub_black.key_matches(x_funnel_key):
        raise HTTPException(status_code=401, detail="Chave inválida.")


class HubBlackFile(BaseModel):
    url: str = Field(..., max_length=2000)
    name: str = Field("arquivo", max_length=200)
    content_type: Optional[str] = Field(None, max_length=120)


class HubBlackGenerateIn(BaseModel):
    client_email: Optional[str] = Field(None, max_length=255)
    fallback_email: Optional[str] = Field(None, max_length=255)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=4000)
    general_info: str = Field(..., min_length=1, max_length=40000)
    stock_images_consent: bool = False
    files: list[HubBlackFile] = Field(default_factory=list, max_length=hub_black.MAX_FILES)
    # Página de uma geração anterior: gera de novo nela em vez de criar outra.
    page_id: Optional[int] = None


@router.post("/generate", dependencies=[Depends(require_hub_key)])
def generate_page(payload: HubBlackGenerateIn, db: Session = Depends(get_db)) -> dict:
    agency, used_fallback = hub_black.resolve_target_agency(db, payload.client_email, payload.fallback_email)
    page = hub_black.start_page(db, agency, payload.title, payload.page_id)
    hub_black.start_generation_thread(page.id, payload.model_dump())
    return {**hub_black.describe_page(page), "used_fallback": used_fallback}


@router.get("/pages/{page_id}", dependencies=[Depends(require_hub_key)])
def page_status(page_id: int, db: Session = Depends(get_db)) -> dict:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada no Roteiro Online.")
    return hub_black.describe_page(page)
