"""Situação de cada empresa (agência) para o Admin Master e para a página pública.

A página pública fica no ar enquanto a assinatura do dono permite (subscription_allows_public).
Quando deixa de permitir, a data é registrada em subscriptions.deactivated_at pelo job horário,
e é a partir dela que contam os prazos do arquivamento dos arquivos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session, selectinload

from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.cakto import CaktoEventLog
from app.models.subscription import Subscription
from app.models.user import User

# Assinatura encerrada: a página só fica no ar até o fim do período pago (valid_until).
ENDED_STATUSES = frozenset({"cancelled", "canceled", "cancelled_admin", "inactive", "expired", "refunded"})
CAKTO_CANCEL_EVENTS = frozenset({"subscription_canceled", "subscription_cancelled", "subscription_renewal_refused"})

STATUS_LABELS = {
    "active": "Ativa",
    "trial": "Em teste",
    "cancelling": "Cancelando",
    "past_due": "Inadimplente",
    "inactive": "Desativada",
    "internal": "Interna",
    "no_owner": "Sem dono",
}


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def subscription_allows_public(subscription: Subscription | None, now: datetime | None = None) -> bool:
    """A página pública fica no ar? Ativa ou com menos de 3 falhas de cobrança; encerrada, só
    até o fim do período pago."""
    if subscription is None:
        return False
    now = now or datetime.now(timezone.utc)
    status = (subscription.status or "").strip().lower()
    if status in ENDED_STATUSES:
        valid_until = _aware(subscription.valid_until)
        return bool(valid_until and valid_until > now)
    return status == "active" or int(subscription.failed_attempts or 0) < 3


def agency_owner(agency: Agency) -> User | None:
    memberships = list(agency.users or [])
    owner = next((rel for rel in memberships if (rel.role or "").lower() == "owner" and rel.user), None)
    owner = owner or next((rel for rel in memberships if rel.user), None)
    return owner.user if owner else None


@dataclass
class CompanyStatus:
    key: str
    label: str
    online: bool
    since: datetime | None = None
    estimated: bool = False

    @property
    def days(self) -> int | None:
        if self.since is None:
            return None
        return max(0, (datetime.now(timezone.utc) - self.since).days)


def company_status(owner: User | None, now: datetime | None = None) -> CompanyStatus:
    now = now or datetime.now(timezone.utc)
    if owner is None:
        return CompanyStatus("no_owner", STATUS_LABELS["no_owner"], online=False)
    subscription = owner.subscription
    if owner.is_superuser or (subscription and (subscription.plan or "") == "infinity"):
        return CompanyStatus("internal", STATUS_LABELS["internal"], online=True)
    online = subscription_allows_public(subscription, now)
    trial_ends = _aware(owner.trial_ends_at)
    if owner.trial_plan and trial_ends and trial_ends > now:
        return CompanyStatus("trial", STATUS_LABELS["trial"], online=online or True, since=_aware(owner.trial_started_at))
    if not online:
        return CompanyStatus(
            "inactive",
            STATUS_LABELS["inactive"],
            online=False,
            since=_aware(subscription.deactivated_at) if subscription else None,
            estimated=bool(subscription and subscription.deactivation_estimated),
        )
    status = (subscription.status or "").strip().lower() if subscription else ""
    if status == "cancel_at_period_end" or status in ENDED_STATUSES:
        return CompanyStatus("cancelling", STATUS_LABELS["cancelling"], online=True, since=_aware(subscription.valid_until))
    if status == "past_due" or int(subscription.failed_attempts or 0) > 0:
        return CompanyStatus("past_due", STATUS_LABELS["past_due"], online=True)
    return CompanyStatus("active", STATUS_LABELS["active"], online=True, since=_aware(subscription.created_at))


def _cakto_cancellations(db: Session, emails: Iterable[str]) -> dict[str, datetime]:
    """Último cancelamento registrado pela Cakto para cada e-mail (para estimar o passado)."""
    from app.api.v1.endpoints.admin import _extract_customer_email  # evita import circular

    wanted = {email.lower() for email in emails if email}
    if not wanted:
        return {}
    found: dict[str, datetime] = {}
    rows = db.query(CaktoEventLog).filter(CaktoEventLog.event_type.in_(tuple(CAKTO_CANCEL_EVENTS))).all()
    for row in rows:
        payload = row.payload if isinstance(row.payload, dict) else {}
        email = (_extract_customer_email(payload) or "").lower()
        if email not in wanted:
            continue
        moment = _aware(row.processed_at or row.created_at)
        if moment and (email not in found or moment > found[email]):
            found[email] = moment
    return found


def stamp_deactivations(db: Session, now: datetime | None = None) -> int:
    """Registra quando cada conta saiu do ar (e limpa quando volta). Devolve quantas mudaram.

    O job roda de hora em hora, então a data registrada é a real (com até 1 hora de diferença).
    Só na primeira vez (antes não existia o registro) a data de quem já estava fora do ar é
    estimada: cancelamento na Cakto, fim do período pago ou última atualização da assinatura,
    o que vier depois; sem nenhuma pista, conta a partir de agora (o mais conservador)."""
    now = now or datetime.now(timezone.utc)
    first_run = db.query(Subscription.id).filter(Subscription.deactivated_at.isnot(None)).first() is None
    to_stamp: list[Subscription] = []
    changed = 0
    for subscription in db.query(Subscription).all():
        online = subscription_allows_public(subscription, now)
        if online and subscription.deactivated_at is not None:
            subscription.deactivated_at = None
            subscription.deactivation_estimated = False
            changed += 1
        elif not online and subscription.deactivated_at is None:
            to_stamp.append(subscription)
    if to_stamp and first_run:
        users = {user.id: user for user in db.query(User).filter(User.id.in_([s.user_id for s in to_stamp])).all()}
        cancellations = _cakto_cancellations(db, [user.email for user in users.values()])
        for subscription in to_stamp:
            user = users.get(subscription.user_id)
            candidates = [
                cancellations.get((user.email or "").lower()) if user else None,
                _aware(subscription.valid_until),
                _aware(subscription.updated_at),
            ]
            known = [moment for moment in candidates if moment and moment <= now]
            subscription.deactivated_at = max(known) if known else now
            subscription.deactivation_estimated = True
    else:
        for subscription in to_stamp:
            subscription.deactivated_at = now
            subscription.deactivation_estimated = False
    changed += len(to_stamp)
    if changed:
        db.commit()
    return changed


def agencies_with_owner(db: Session) -> list[tuple[Agency, User | None]]:
    agencies = (
        db.query(Agency)
        .options(selectinload(Agency.users).selectinload(AgencyUser.user).selectinload(User.subscription))
        .all()
    )
    return [(agency, agency_owner(agency)) for agency in agencies]
