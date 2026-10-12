"""Admin Master: receita (MRR, ARR, recebido, a receber, renovações). Somente leitura: nenhuma
rota daqui cria, altera ou cancela cobrança (ver services/revenue)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.core.config import get_settings
from app.models.user import User
from app.services.asaas import AsaasAPIError
from app.services.revenue import asaas_open_charges, revenue_overview

router = APIRouter(prefix="/master/revenue")


@router.get("")
def get_revenue(
    month: str | None = Query(None, description="AAAA-MM; padrão: mês atual"),
    horizon: int = Query(60, ge=7, le=120),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, Any]:
    chosen = None
    if month:
        try:
            chosen = date.fromisoformat(f"{month}-01")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Mês inválido (use AAAA-MM).") from exc
    return revenue_overview(db, chosen, horizon)


@router.get("/asaas-open")
def get_asaas_open(_: User = Depends(get_current_superuser)) -> dict[str, Any]:
    """Confere na Asaas as cobranças já emitidas e não pagas (só consulta)."""
    settings = get_settings()
    if not settings.asaas_api_key:
        raise HTTPException(status_code=400, detail="A chave da Asaas não está configurada no servidor.")
    today = date.today()
    month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    try:
        return {"until": month_end.isoformat(), **asaas_open_charges(settings.asaas_api_key, settings.asaas_base_url, month_end)}
    except AsaasAPIError as exc:
        raise HTTPException(status_code=502, detail="A Asaas não respondeu à consulta.") from exc
