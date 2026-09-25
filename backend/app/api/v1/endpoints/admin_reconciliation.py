from datetime import date, timedelta
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_superuser, get_db
from app.core.config import get_settings
from app.models.user import User
from app.services.asaas import AsaasClient
from app.services.billing_reconciliation import fetch_remote, load_local, reconcile, sao_paulo_today

router = APIRouter()
_lock = Lock()
_cache: dict[tuple, tuple[float, dict]] = {}


@router.get("/billing-reconciliation")
def billing_reconciliation(
    response: Response,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
):
    """Consult Asaas using GET only; never renew, retry, cancel, or mutate subscriptions."""
    response.headers["Cache-Control"] = "no-store"
    today = sao_paulo_today()
    end = end_date or today - timedelta(days=1)
    if end > today or (start_date and start_date > end):
        raise HTTPException(422, "Informe um período válido, com data final até hoje.")
    settings = get_settings()
    if not settings.asaas_api_key:
        raise HTTPException(503, "A chave da API Asaas não está configurada no servidor.")
    key = (settings.asaas_base_url, start_date, end, today)
    if not _lock.acquire(blocking=False):
        raise HTTPException(429, "Já existe uma conciliação em andamento. Aguarde e tente novamente.", headers={"Retry-After": "15"})
    try:
        cached = _cache.get(key)
        if not refresh and cached and monotonic() - cached[0] < 300:
            return {**cached[1], "cached": True}
        local, sessions = load_local(db)
        remote = fetch_remote(AsaasClient(settings.asaas_api_key, settings.asaas_base_url), start_date, end)
        report = reconcile(remote, local, sessions, today=today, start=start_date, end=end)
        report["environment"] = "sandbox" if "sandbox" in settings.asaas_base_url.lower() else "production"
        report["cached"] = False
        if len(_cache) >= 4:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (monotonic(), report)
        return report
    finally:
        _lock.release()
