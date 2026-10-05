from types import SimpleNamespace

import pytest

from app.core.config import get_settings
from app.services.page_design import design_v2_enabled_for_agency


def _agency(*superuser_flags: bool):
    return SimpleNamespace(users=[SimpleNamespace(user=SimpleNamespace(is_superuser=flag)) for flag in superuser_flags])


@pytest.fixture
def rollout(monkeypatch):
    def _set(value: str) -> None:
        monkeypatch.setattr(get_settings(), "page_design_v2_rollout", value)

    return _set


def test_superusers_rollout_only_enables_agencies_with_a_superuser(rollout):
    rollout("superusers")
    assert design_v2_enabled_for_agency(_agency(False, True)) is True
    assert design_v2_enabled_for_agency(_agency(False, False)) is False
    assert design_v2_enabled_for_agency(None) is False


def test_all_and_off_rollouts(rollout):
    rollout("all")
    assert design_v2_enabled_for_agency(_agency(False)) is True
    rollout("off")
    assert design_v2_enabled_for_agency(_agency(True)) is False
