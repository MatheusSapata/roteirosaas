"""Admin Master: painel da plataforma e controle das pessoas (usuários). As ações sobre
usuários (deslogar, excluir) usam as rotas já existentes em admin.py; a senha temporária fica aqui."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_superuser, get_db
from app.models.agency_user import AgencyUser
from app.services import auth as auth_service
from app.models.user import User
from app.models.user_session import UserSession
from app.services.admin_dashboard import build_dashboard, period_days
from app.services.company_status import agencies_with_owner, company_status

router = APIRouter(prefix="/master")
ONLINE_WINDOW_MINUTES = 10


@router.get("/dashboard")
def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, Any]:
    if bool(start_date) != bool(end_date):
        raise HTTPException(status_code=400, detail="Informe data inicial e final para o período personalizado.")
    if start_date and end_date:
        if end_date < start_date:
            start_date, end_date = end_date, start_date
        if (end_date - start_date).days + 1 > 366:
            raise HTTPException(status_code=400, detail="O período personalizado deve ter no máximo 1 ano.")
    now = datetime.now(timezone.utc)
    first, last = period_days(days, start_date, end_date, now)
    return build_dashboard(db, first, last, now)


class UserCompanyOut(BaseModel):
    id: int
    name: str
    slug: str
    role: str
    is_owner: bool
    status: str
    status_label: str
    plan: Optional[str] = None


class MasterUserOut(BaseModel):
    id: int
    name: str
    email: str
    whatsapp: Optional[str] = None
    is_superuser: bool = False
    global_admin: bool = False
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    last_access_at: Optional[datetime] = None
    active_sessions: int = 0
    online: bool = False
    temporary_password: bool = False
    companies: list[UserCompanyOut] = []


@router.get("/users", response_model=list[MasterUserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)) -> list[MasterUserOut]:
    """Pessoas com acesso: em quais empresas estão, com que papel e quando entraram por último.
    Os vínculos escondidos da equipe (admins globais) não aparecem como empresa."""
    now = datetime.now(timezone.utc)
    companies: dict[int, tuple[Any, Any]] = {}
    for agency, owner in agencies_with_owner(db):
        companies[agency.id] = (owner, company_status(owner, now))
    open_session = and_(UserSession.revoked_at.is_(None), UserSession.expires_at > now)
    sessions = {
        user_id: (last_seen, int(active or 0))
        for user_id, last_seen, active in db.query(
            UserSession.user_id,
            func.max(UserSession.last_seen_at),
            func.count(UserSession.id).filter(open_session),
        ).group_by(UserSession.user_id)
    }
    online_since = now - timedelta(minutes=ONLINE_WINDOW_MINUTES)
    online_users = {
        user_id
        for (user_id,) in db.query(UserSession.user_id)
        .filter(open_session, UserSession.last_seen_at >= online_since)
        .distinct()
    }
    users = db.query(User).options(selectinload(User.agencies).selectinload(AgencyUser.agency)).all()
    result: list[MasterUserOut] = []
    for user in users:
        links: list[UserCompanyOut] = []
        global_admin = False
        for rel in user.agencies or []:
            if rel.hidden_from_team:
                global_admin = True
                continue
            if rel.agency is None:
                continue
            owner, status = companies.get(rel.agency_id, (None, None))
            links.append(UserCompanyOut(
                id=rel.agency.id,
                name=rel.agency.name,
                slug=rel.agency.slug,
                role=(rel.role or "").lower(),
                is_owner=bool(owner and owner.id == user.id),
                status=status.key if status else "no_owner",
                status_label=status.label if status else "Sem dono",
                plan=owner.plan if owner else None,
            ))
        links.sort(key=lambda link: (not link.is_owner, link.name.lower()))
        last_seen, active = sessions.get(user.id, (None, 0))
        result.append(MasterUserOut(
            id=user.id,
            name=user.name,
            email=user.email,
            whatsapp=user.whatsapp,
            is_superuser=bool(user.is_superuser),
            global_admin=global_admin,
            source=user.source,
            created_at=user.created_at,
            last_access_at=last_seen,
            active_sessions=active,
            online=user.id in online_users,
            temporary_password=bool(user.temporary_password),
            companies=links,
        ))
    # Cadastrados por último primeiro.
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    result.sort(key=lambda item: (_aware(item.created_at) or oldest, item.id), reverse=True)
    return result


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class TemporaryPasswordIn(BaseModel):
    password: str


@router.post("/users/{user_id}/temporary-password")
def set_temporary_password(
    user_id: int,
    payload: TemporaryPasswordIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser),
) -> dict[str, Any]:
    """Define uma senha temporária: a pessoa entra com ela e precisa criar uma senha própria na
    hora. As sessões abertas são encerradas para ninguém continuar logado com a senha antiga."""
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Para trocar a sua própria senha, use o Perfil.")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    try:
        auth_service.validate_password_strength(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    now = datetime.now(timezone.utc)
    user.hashed_password = auth_service.get_password_hash(payload.password)
    user.temporary_password = True
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.revoked_at.is_(None)).all()
    for session in sessions:
        session.revoked_at = now
        session.revoked_by_user_id = admin.id
    db.commit()
    return {"detail": "Senha temporária definida.", "sessions_closed": len(sessions)}
