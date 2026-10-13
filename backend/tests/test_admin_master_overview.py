from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.api.deps import get_current_superuser
from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.asaas import AsaasEventLog
from app.models.cakto import CaktoEventLog
from app.models.page import Page, PageStatus
from app.models.stats import PageVisitStats
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_session import UserSession
from app.services.admin_dashboard import build_dashboard

NOW = datetime(2026, 10, 12, 15, tzinfo=timezone.utc)
FIRST, LAST = date(2026, 9, 13), date(2026, 10, 12)


def _company(db, email, *, plan, created, status="active", mrr=0, superuser=False, sub_created=None, **sub):
    user = User(name=email.split("@")[0].title(), email=email, hashed_password="x", plan=plan, is_superuser=superuser,
                created_at=sub_created or created)
    db.add(user)
    db.flush()
    subscription = Subscription(user_id=user.id, plan=plan, status=status, mrr_amount=Decimal(str(mrr)),
                                created_at=sub_created or created, **sub)
    db.add(subscription)
    db.flush()
    user.subscription_id = subscription.id
    agency = Agency(name=f"Agência {user.name}", slug=email.split("@")[0], created_at=created)
    db.add(agency)
    db.flush()
    db.add(AgencyUser(agency_id=agency.id, user_id=user.id, role="owner"))
    return user, agency


@pytest.fixture
def data(db_session):
    db = db_session
    _company(db, "a@x.com", plan="growth", mrr=199, provider="asaas", asaas_customer_id="cus_a",
             created=datetime(2026, 10, 1, tzinfo=timezone.utc))
    _company(db, "b@x.com", plan="essencial", mrr=99, provider="cakto", created=datetime(2026, 10, 5, 14, tzinfo=timezone.utc))
    # Gratuita cadastrada há mais de 7 dias: vencida.
    _company(db, "c@x.com", plan="free", created=datetime(2026, 9, 20, tzinfo=timezone.utc))
    trial, _ = _company(db, "d@x.com", plan="free", created=datetime(2026, 10, 7, tzinfo=timezone.utc))
    trial.trial_plan, trial.trial_started_at, trial.trial_ends_at = "growth", NOW - timedelta(days=5), NOW + timedelta(days=2)
    # Cliente que saiu do ar dentro do período.
    _company(db, "e@x.com", plan="growth", status="inactive", created=datetime(2026, 1, 1, tzinfo=timezone.utc),
             deactivated_at=datetime(2026, 10, 3, tzinfo=timezone.utc))
    _company(db, "f@x.com", plan="infinity", superuser=True, created=datetime(2026, 10, 2, tzinfo=timezone.utc))

    def asaas(event_id, event, payment):
        db.add(AsaasEventLog(event_id=event_id, event_type=event, payload={"event": event, "payment": payment}, status="processed"))

    # A já pagava antes do período: a cobrança de outubro é renovação, não cliente novo.
    asaas("e1", "PAYMENT_CONFIRMED", {"id": "pay_1", "customer": "cus_a", "value": 199, "confirmedDate": "2026-08-01"})
    asaas("e2", "PAYMENT_CONFIRMED", {"id": "pay_2", "customer": "cus_a", "value": 199, "confirmedDate": "2026-10-01"})
    asaas("e3", "PAYMENT_RECEIVED", {"id": "pay_2", "customer": "cus_a", "value": 199, "paymentDate": "2026-10-02"})
    asaas("e4", "PAYMENT_REFUNDED", {"id": "pay_3", "customer": "cus_a", "value": 50, "refundedDate": "2026-10-07"})
    # Outro produto na mesma conta da Asaas: não é receita do Roteiro Online.
    asaas("e5", "PAYMENT_CONFIRMED", {"id": "pay_4", "customer": "cus_a", "value": 1997, "externalReference": "viajeon:9", "confirmedDate": "2026-10-03"})
    # B pagou pela primeira vez no período (Cakto, pelo e-mail).
    db.add(CaktoEventLog(event_id="c1", event_type="purchase_approved", status="processed",
                         payload={"data": {"order": {"amount": 99}, "customer": {"email": "B@x.com"}}},
                         processed_at=datetime(2026, 10, 5, 14, tzinfo=timezone.utc)))
    db.commit()
    return db


def test_dashboard_numbers_match_their_sources(data):
    result = build_dashboard(data, FIRST, LAST, NOW)
    # MRR só das assinaturas pagas que renovam (a interna e a desativada ficam fora).
    assert (result["mrr"], result["paying_customers"], result["arpa"]) == (298.0, 2, 149.0)
    # Recebido no período: 199 (Asaas, contado uma vez) + 99 (Cakto); estorno à parte.
    assert (result["received"], result["payments"], result["refunded"]) == (298.0, 2, 50.0)
    assert result["received_others"] == 1997.0
    assert (result["new_paying"], result["new_paying_previous"]) == (1, 0)
    # Cadastros do período (sem a conta interna): A, B, C e D; destes, A e B pagam.
    assert (result["signups"], result["signups_paying"]) == (4, 2)
    assert (result["left"], result["trials_ending"]) == (1, 1)
    assert result["companies"] == {"active": 2, "free_expired": 1, "trial": 1, "inactive": 1, "internal": 1}
    assert len(result["series"]) == 30 and not result["period"]["weekly"]
    day = next(item for item in result["series"] if item["start"] == "2026-10-05")
    assert (day["received"], day["new_paying"], day["signups"], day["signups_paying"]) == (99.0, 1, 1, 1)


def test_long_periods_are_grouped_by_week(data):
    result = build_dashboard(data, date(2026, 7, 15), LAST, NOW)
    assert result["period"]["weekly"]
    # A primeira semana começa no primeiro dia do período, não na segunda-feira anterior.
    assert result["series"][0]["start"] == "2026-07-15" and result["series"][-1]["end"] == "2026-10-12"
    assert sum(item["received"] for item in result["series"]) == result["received"] == 497.0


def _as_admin(client):
    client.app.dependency_overrides[get_current_superuser] = lambda: User(id=999, is_superuser=True)


def test_users_list_people_with_companies(client, data):
    owner = data.query(User).filter(User.email == "a@x.com").one()
    agency = data.query(Agency).filter(Agency.slug == "a").one()
    member = User(name="Membro", email="m@x.com", hashed_password="x", plan="free")
    data.add(member)
    data.flush()
    data.add(AgencyUser(agency_id=agency.id, user_id=member.id, role="editor"))
    # Admin global entra escondido na empresa: não aparece como da equipe.
    global_admin = data.query(User).filter(User.email == "f@x.com").one()
    data.add(AgencyUser(agency_id=agency.id, user_id=global_admin.id, role="admin", hidden_from_team=True))
    data.add(UserSession(user_id=member.id, last_seen_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
    data.commit()
    _as_admin(client)
    try:
        response = client.get("/api/v1/admin/master/users")
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)
    assert response.status_code == 200, response.text
    people = {item["email"]: item for item in response.json()}
    assert people["m@x.com"]["online"] and people["m@x.com"]["active_sessions"] == 1
    assert [(c["slug"], c["role"], c["is_owner"], c["status"]) for c in people["m@x.com"]["companies"]] == [("a", "editor", False, "active")]
    assert people["a@x.com"]["companies"][0]["is_owner"] and owner.id == people["a@x.com"]["id"]
    assert people["f@x.com"]["global_admin"] and [c["slug"] for c in people["f@x.com"]["companies"]] == ["f"]


def test_companies_newest_first_and_detail(client, data):
    agency = data.query(Agency).filter(Agency.slug == "a").one()
    page = Page(agency_id=agency.id, title="Roteiro", slug="roteiro", status=PageStatus.published)
    data.add(page)
    data.flush()
    data.add(PageVisitStats(page_id=page.id, date=date(2026, 10, 1), visits=10, clicks_cta=2, clicks_whatsapp=1))
    data.commit()
    _as_admin(client)
    try:
        listing = client.get("/api/v1/admin/master/companies")
        detail = client.get(f"/api/v1/admin/master/companies/{agency.id}")
        storage = client.get("/api/v1/admin/master/companies/storage")
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)
    assert listing.status_code == 200, listing.text
    items = listing.json()["items"]
    assert [item["slug"] for item in items] == ["d", "b", "f", "a", "c", "e"]
    first = next(item for item in items if item["slug"] == "a")
    assert (first["owner_email"], first["subscription_provider"], first["mrr_amount"], first["members_count"]) == ("a@x.com", "asaas", 199.0, 1)
    gratuita = next(item for item in items if item["slug"] == "c")
    assert gratuita["status"] == "free_expired" and gratuita["access_until"].startswith("2026-09-27")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert [(p["slug"], p["visits"], p["clicks"]) for p in body["pages"]] == [("roteiro", 10, 3)]
    assert body["members"][0]["is_owner"]
    assert storage.status_code == 200


def test_temporary_password_forces_a_new_one(client, data):
    from app.services.auth import get_password_hash

    person = data.query(User).filter(User.email == "b@x.com").one()
    person.hashed_password = get_password_hash("Antiga123")
    data.add(UserSession(user_id=person.id, last_seen_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
    data.commit()
    _as_admin(client)
    try:
        weak = client.post(f"/api/v1/admin/master/users/{person.id}/temporary-password", json={"password": "fraca"})
        own = client.post("/api/v1/admin/master/users/999/temporary-password", json={"password": "Temporaria1"})
        done = client.post(f"/api/v1/admin/master/users/{person.id}/temporary-password", json={"password": "Temporaria1"})
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)
    assert weak.status_code == 400 and own.status_code == 400
    assert done.status_code == 200, done.text
    assert done.json()["sessions_closed"] == 1
    data.expire_all()
    assert data.query(UserSession).filter(UserSession.user_id == person.id, UserSession.revoked_at.is_(None)).count() == 0

    # A senha antiga deixa de valer; com a temporária a pessoa entra e vê que precisa trocar.
    assert client.post("/api/v1/auth/login", data={"username": "b@x.com", "password": "Antiga123"}).status_code == 401
    login = client.post("/api/v1/auth/login", data={"username": "b@x.com", "password": "Temporaria1"})
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).json()["temporary_password"] is True

    # Criou a própria senha: some o aviso.
    changed = client.post("/api/v1/auth/me/password", headers=headers, json={"current_password": "Temporaria1", "new_password": "MinhaSenha9"})
    assert changed.status_code == 200, changed.text
    assert client.get("/api/v1/auth/me", headers=headers).json()["temporary_password"] is False


def test_companies_ordered_by_account_creation_not_payment(client, data):
    # Conta antiga cuja agência só foi criada agora (no pagamento): continua na posição da conta.
    agency = data.query(Agency).filter(Agency.slug == "c").one()
    agency.created_at = datetime(2026, 10, 12, tzinfo=timezone.utc)
    data.commit()
    _as_admin(client)
    try:
        items = client.get("/api/v1/admin/master/companies").json()["items"]
    finally:
        client.app.dependency_overrides.pop(get_current_superuser, None)
    assert [item["slug"] for item in items] == ["d", "b", "f", "a", "c", "e"]
    assert next(item for item in items if item["slug"] == "c")["created_at"].startswith("2026-09-20")
