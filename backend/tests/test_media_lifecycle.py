from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.models.agency import Agency
from app.models.agency_user import AgencyUser
from app.models.media import MediaAsset
from app.models.media_archive import AgencyMediaArchive, MediaOrphan
from app.models.page import Page
from app.models.page_template import PageTemplate
from app.models.subscription import Subscription
from app.models.user import User
from app.services import company_status as status_service
from app.services import media_lifecycle as lifecycle
from app.services.media_storage import StoredFile

NOW = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
U = {name: f"{n:08d}-1111-4111-8111-{n:012d}" for n, name in enumerate(
    ["exclusive", "shared_agency", "template", "library", "orphan", "logo", "active_photo"], start=1)}


class FakeStorage:
    def __init__(self, names: list[str], uploaded: datetime) -> None:
        self.files = {name: StoredFile(name=name, size=1000, last_modified=uploaded, tier="Hot") for name in names}
        self.deleted: list[str] = []

    def list_files(self):
        return iter(list(self.files.values()))

    def set_tier(self, name: str, tier: str) -> None:
        self.files[name].tier = tier

    def delete_file(self, name: str) -> None:
        self.files.pop(name, None)
        self.deleted.append(name)


def _company(db, name: str, status: str, valid_until=None, failed=0) -> Agency:
    user = User(name=name, email=f"{name}@x.com", hashed_password="x", is_active=True)
    agency = Agency(name=name.title(), slug=name)
    db.add_all([user, agency])
    db.flush()
    db.add(AgencyUser(agency_id=agency.id, user_id=user.id, role="owner"))
    subscription = Subscription(user_id=user.id, plan="pro", status=status, valid_until=valid_until, failed_attempts=failed)
    db.add(subscription)
    db.flush()
    user.subscription_id = subscription.id
    db.flush()
    return agency


def test_public_rule_ended_subscription_only_until_paid_period():
    allows = status_service.subscription_allows_public
    future, past = NOW + timedelta(days=5), NOW - timedelta(days=1)
    assert allows(SimpleNamespace(status="cancelled", valid_until=future, failed_attempts=0), NOW)
    assert not allows(SimpleNamespace(status="cancelled", valid_until=past, failed_attempts=0), NOW)
    assert not allows(SimpleNamespace(status="cancelled", valid_until=None, failed_attempts=0), NOW)
    assert allows(SimpleNamespace(status="active", valid_until=None, failed_attempts=5), NOW)
    assert allows(SimpleNamespace(status="past_due", valid_until=None, failed_attempts=2), NOW)
    assert not allows(SimpleNamespace(status="past_due", valid_until=None, failed_attempts=3), NOW)
    assert not allows(None, NOW)


@pytest.fixture
def scenario(db_session, monkeypatch):
    db = db_session
    active = _company(db, "ativa", "active")
    gone = _company(db, "saiu", "cancelled", valid_until=NOW - timedelta(days=40))
    gone.logo_url = f"https://cdn.x/{U['logo']}.png"
    db.add(Page(agency_id=gone.id, title="P", slug="p", status="published", config_json={"sections": [
        {"image": f"https://cdn.x/{U['exclusive']}_1600.webp"},
        {"image": f"https://cdn.x/{U['shared_agency']}.jpg"},
        {"image": f"/uploads/{U['template']}.jpg"},
    ]}))
    db.add(Page(agency_id=active.id, title="A", slug="a", status="published", config_json={"sections": [
        {"image": f"https://cdn.x/{U['shared_agency']}.jpg"}, {"image": f"https://cdn.x/{U['active_photo']}.jpg"},
    ]}))
    db.add(PageTemplate(name="T", slug="t", config_json={"img": f"https://cdn.x/{U['template']}.jpg"}))
    db.add(MediaAsset(agency_id=gone.id, url=f"https://cdn.x/{U['library']}.jpg", type="image"))
    db.commit()
    names = [
        f"{U['exclusive']}_1600.webp", f"{U['exclusive']}_800.webp", f"{U['shared_agency']}.jpg",
        f"{U['template']}.jpg", f"{U['library']}.jpg", f"{U['orphan']}.jpg", f"{U['logo']}.png",
        f"{U['active_photo']}.jpg", "logo-sem-uuid.png",
    ]
    storage = FakeStorage(names, uploaded=NOW - timedelta(days=60))
    monkeypatch.setattr(lifecycle, "media_storage", storage)
    db.close = lambda: None
    return SimpleNamespace(db=db, active=active, gone=gone, storage=storage, factory=lambda: db)


def test_analysis_finds_exclusive_media_and_orphans(scenario):
    db, gone, storage = scenario.db, scenario.gone, scenario.storage
    result = lifecycle.run_analysis(scenario.factory, NOW)
    assert result.status == "done", result.error

    sub = db.query(Subscription).join(User, User.id == Subscription.user_id).filter(User.email == "saiu@x.com").one()
    assert sub.deactivated_at is not None and sub.deactivation_estimated  # estimado na 1ª vez
    record = db.query(AgencyMediaArchive).filter_by(agency_id=gone.id).one()
    # Só dela: as 2 larguras da foto exclusiva, o logo e a foto da biblioteca. A foto usada
    # também pela outra empresa e a do modelo ficam de fora.
    assert record.files_count == 4 and record.shared_skipped == 2
    orphan_keys = {orphan.file_key for orphan in db.query(MediaOrphan).all()}
    assert orphan_keys == {U["orphan"], U["library"]}  # biblioteca sem página = sem uso
    assert db.query(AgencyMediaArchive).filter_by(agency_id=scenario.active.id).first() is None


def test_cool_archive_restore_and_delete(scenario):
    db, gone, storage = scenario.db, scenario.gone, scenario.storage
    lifecycle.run_analysis(scenario.factory, NOW)
    with pytest.raises(lifecycle.LifecycleError):
        lifecycle.move_agency_media(db, scenario.active.id, "Cool")  # empresa no ar: nunca

    record = lifecycle.move_agency_media(db, gone.id, "Cool")
    assert record.stage == "cool" and storage.files[f"{U['exclusive']}_800.webp"].tier == "Cool"
    assert storage.files[f"{U['shared_agency']}.jpg"].tier == "Hot" and storage.files[f"{U['template']}.jpg"].tier == "Hot"
    record = lifecycle.move_agency_media(db, gone.id, "Archive")
    assert record.stage == "archive" and storage.files[f"{U['logo']}.png"].tier == "Archive"
    record = lifecycle.restore_agency_media(db, gone.id)
    assert record.stage == "restoring" and storage.files[f"{U['logo']}.png"].tier == "Hot"

    record = lifecycle.delete_agency_media(db, gone.id, min_days=0)
    assert record.stage == "deleted" and f"{U['exclusive']}_1600.webp" in storage.deleted
    assert f"{U['shared_agency']}.jpg" in storage.files and "logo-sem-uuid.png" in storage.files
    assert db.query(MediaAsset).filter_by(agency_id=gone.id).count() == 0


def test_orphans_need_30_days_without_use(scenario):
    db, storage = scenario.db, scenario.storage
    lifecycle.run_analysis(scenario.factory, NOW)
    # Acabou de ficar sem uso: nada é excluído ainda (quem edita pode desfazer).
    assert lifecycle.delete_ready_orphans(db, NOW)["deleted_files"] == 0

    # Na edição, a foto "sem uso" voltou para uma página: sai da lista.
    page = db.query(Page).filter_by(slug="a").one()
    page.config_json = {**page.config_json, "extra": f"https://cdn.x/{U['orphan']}.jpg"}
    db.commit()
    lifecycle.run_analysis(scenario.factory, NOW + timedelta(days=1))
    assert {o.file_key for o in db.query(MediaOrphan).all()} == {U["library"]}

    # 31 dias seguidos sem uso: a da biblioteca pode ir; a que voltou a ser usada fica.
    lifecycle.run_analysis(scenario.factory, NOW + timedelta(days=31))
    result = lifecycle.delete_ready_orphans(db, NOW + timedelta(days=31))
    assert result["deleted_files"] == 1 and f"{U['library']}.jpg" in storage.deleted
    assert f"{U['orphan']}.jpg" in storage.files
    assert db.query(MediaAsset).count() == 0  # a entrada da biblioteca também sai


def test_stamp_after_first_run_uses_real_time(db_session):
    db = db_session
    _company(db, "antiga", "inactive")
    db.commit()
    status_service.stamp_deactivations(db, NOW)
    _company(db, "nova", "cancelled", valid_until=NOW - timedelta(days=200))
    db.commit()
    status_service.stamp_deactivations(db, NOW + timedelta(hours=1))
    nova = db.query(Subscription).join(User, User.id == Subscription.user_id).filter(User.email == "nova@x.com").one()
    # Depois da primeira vez, vale a hora em que o job viu (nada de data antiga estimada).
    assert not nova.deactivation_estimated
    assert nova.deactivated_at.replace(tzinfo=timezone.utc) == NOW + timedelta(hours=1)


def _owner(plan, status="active", created_days_ago=200, valid_until=None, **extra):
    subscription = SimpleNamespace(plan=plan, status=status, valid_until=valid_until, failed_attempts=0, created_at=NOW - timedelta(days=created_days_ago), deactivated_at=None, deactivation_estimated=False)
    defaults = dict(is_superuser=False, trial_plan=None, trial_ends_at=None, trial_started_at=None, trial_blocked=False)
    defaults.update(extra)
    return SimpleNamespace(subscription=subscription, **defaults)


def test_unpaid_plans_are_not_counted_as_active():
    status = status_service.company_status
    # Plano gratuito com assinatura "active": Gratuita nos 7 dias do cadastro e continua no ar
    # (mesma regra da página pública).
    free = status(_owner("free", created_days_ago=3), NOW)
    assert (free.key, free.online) == ("free", True)
    assert free.ends == NOW + timedelta(days=4)
    # Passado o prazo: Gratuita vencida (a página pública não muda por isso).
    expired = status(_owner("free"), NOW)
    assert (expired.key, expired.online, expired.since) == ("free_expired", True, NOW - timedelta(days=193))
    # Validade definida pelo admin vale no lugar do prazo padrão.
    extended = status(_owner("free", valid_until=NOW + timedelta(days=10)), NOW)
    assert (extended.key, extended.ends) == ("free", NOW + timedelta(days=10))
    # Teste que acabou sem pagamento: Teste encerrado (não "Ativa").
    ended = status(_owner("free", trial_plan="growth", trial_blocked=True, trial_started_at=NOW - timedelta(days=220), trial_ends_at=NOW - timedelta(days=213)), NOW)
    assert ended.key == "trial_ended"
    assert status(_owner("trial"), NOW).key == "trial_ended"
    # Teste ainda valendo continua "Em teste"; plano pago continua "Ativa"; planos internos à parte.
    assert status(_owner("free", trial_plan="growth", trial_started_at=NOW - timedelta(days=2), trial_ends_at=NOW + timedelta(days=5)), NOW).key == "trial"
    assert status(_owner("growth"), NOW).key == "active"
    assert status(_owner("teste"), NOW).key == "internal"
    # Plano gratuito com assinatura encerrada e sem período pago: Desativada.
    assert status(_owner("free", status="cancelled"), NOW).key == "inactive"
