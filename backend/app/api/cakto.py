from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.webhook_auth import require_webhook_token
from app.schemas.cakto import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CheckoutSessionStatusResponse,
    OnboardingPasswordPayload,
    OnboardingSessionResponse,
)
from app.services.cakto import CaktoIntegrationService

router = APIRouter(prefix="/api/cakto", tags=["cakto"])
settings = get_settings()


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(payload: CheckoutSessionRequest, db: Session = Depends(get_db)) -> CheckoutSessionResponse:
    service = CaktoIntegrationService(db)
    try:
        session, checkout_url = service.create_checkout_session(payload.plan, payload.cycle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CheckoutSessionResponse(
        token=session.token,
        checkout_url=checkout_url,
        plan=session.plan_key,
        cycle=session.cycle,
    )


@router.get("/checkout-session/{token}", response_model=CheckoutSessionStatusResponse)
def get_checkout_session_status(token: str, db: Session = Depends(get_db)) -> CheckoutSessionStatusResponse:
    service = CaktoIntegrationService(db)
    session = service.get_checkout_session(token)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    redirect_token = session.onboarding_token.token if session.onboarding_token else None
    status = "ready" if session.status == "ready" else "pending"
    return CheckoutSessionStatusResponse(
        status=status,
        order_id=session.order_id,
        ref_id=session.order_ref,
        redirect_token=redirect_token,
    )


@router.post("/webhook")
async def receive_cakto_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    require_webhook_token(
        request.query_params.get("token") or request.headers.get("x-cakto-token"),
        settings.cakto_webhook_secret,
        env=settings.env,
        setting_name="CAKTO_WEBHOOK_SECRET",
    )
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Payload inválido") from exc

    service = CaktoIntegrationService(db)
    try:
        message = service.process_event(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"detail": message}


@router.get("/onboarding/session", response_model=OnboardingSessionResponse)
def get_onboarding_session(
    token: str | None = None,
    order_id: str | None = None,
    ref_id: str | None = None,
    subscription_code: str | None = None,
    db: Session = Depends(get_db),
) -> OnboardingSessionResponse:
    service = CaktoIntegrationService(db)
    record = service.get_onboarding_record(token=token, order_id=order_id, ref_id=ref_id, subscription_code=subscription_code)
    if not record:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada.")
    user = record.user
    return OnboardingSessionResponse(
        email=user.email,
        name=user.name,
        plan=record.plan_key,
        cycle=record.billing_cycle,
    )


@router.post("/onboarding/session/password")
def finish_onboarding_session(
    payload: OnboardingPasswordPayload,
    token: str | None = None,
    order_id: str | None = None,
    ref_id: str | None = None,
    subscription_code: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    service = CaktoIntegrationService(db)
    try:
        service.set_password_for_onboarding(
            password=payload.password,
            token=token,
            order_id=order_id,
            ref_id=ref_id,
            subscription_code=subscription_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"detail": "Senha definida com sucesso. Faça login para acessar o painel."}
