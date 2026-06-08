from __future__ import annotations

from app.services.checkout import _extract_checkout_session_token


def test_extract_checkout_session_token_supports_asaas_checkout_prefixes():
    assert _extract_checkout_session_token("checkout:abc123") == "abc123"
    assert _extract_checkout_session_token("checkout_upgrade:def456") == "def456"
    assert _extract_checkout_session_token("co:ghi789") == "ghi789"
    assert _extract_checkout_session_token("unknown:zzz") is None
