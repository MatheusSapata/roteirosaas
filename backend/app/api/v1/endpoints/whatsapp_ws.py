from __future__ import annotations

from datetime import datetime, timezone
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.agency_user import AgencyUser
from app.models.user import User
from app.models.user_session import UserSession
from app.services.whatsapp_access import has_whatsapp_inbox_access
from app.services.whatsapp_realtime import whatsapp_realtime

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def _parse_agency_id(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        value = int(raw)
        return value if value > 0 else None
    except Exception:
        return None


@router.websocket("/ws")
async def whatsapp_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    token = websocket.query_params.get("token")
    agency_id = _parse_agency_id(websocket.query_params.get("agencyId"))
    user: User | None = None

    async def close_ws(code: int, reason: str) -> None:
        await websocket.close(code=code, reason=reason)

    if not token or not agency_id:
        await close_ws(1008, "token e agencyId obrigatorios")
        return

    db = SessionLocal()
    try:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except JWTError:
            await close_ws(1008, "token invalido")
            return

        email = payload.get("sub")
        session_id = payload.get("sid")
        if not email:
            await close_ws(1008, "token invalido")
            return

        if session_id:
            session = db.query(UserSession).filter(UserSession.id == session_id).first()
            if not session or session.revoked_at or not session.user_id:
                await close_ws(1008, "sessao invalida")
                return

            user = db.query(User).filter(User.id == session.user_id).first()
            if not user or not user.is_active:
                await close_ws(1008, "usuario invalido")
                return

            if user.email != email:
                await close_ws(1008, "token invalido")
                return

            if session.expires_at and session.expires_at < datetime.now(timezone.utc):
                await close_ws(1008, "sessao expirada")
                return
        else:
            # Compatibilidade com tokens antigos sem "sid".
            user = db.query(User).filter(User.email == email).first()
            if not user or not user.is_active:
                await close_ws(1008, "usuario invalido")
                return

        membership = db.query(AgencyUser).filter(AgencyUser.agency_id == agency_id, AgencyUser.user_id == user.id).first()
        if not membership:
            await close_ws(1008, "sem acesso a agencia")
            return

        has_access = has_whatsapp_inbox_access(db, user=user, agency_id=agency_id)
        if not has_access:
            await close_ws(1008, "sem permissao de inbox")
            return

        await whatsapp_realtime.register(websocket, user_id=user.id, agency_id=agency_id)
        await websocket.send_json({"type": "ws.ready", "agency_id": agency_id, "user_id": user.id})

        while True:
            # Mantem sessao viva e permite ping/pong futuro.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("whatsapp_ws erro inesperado agency=%s user=%s: %s", agency_id, getattr(user, "id", None), exc)
        try:
            await close_ws(1011, "erro interno websocket")
        except Exception:
            pass
    finally:
        try:
            if agency_id:
                await whatsapp_realtime.unregister(websocket, agency_id=agency_id)
        except Exception:
            pass
        db.close()
