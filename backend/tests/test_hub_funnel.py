from __future__ import annotations

from types import SimpleNamespace

from app.services import hub_funnel


def _settings(url: str | None, key: str | None):
    return SimpleNamespace(hub_funnel_url=url, hub_funnel_key=key)


def test_sem_configuracao_nao_envia(monkeypatch):
    monkeypatch.setattr(hub_funnel, "get_settings", lambda: _settings(None, None))
    assert hub_funnel.send_hub_event("signup", email="a@b.com") is False


def test_sem_email_nao_envia(monkeypatch):
    monkeypatch.setattr(hub_funnel, "get_settings", lambda: _settings("https://hub/x", "k"))
    assert hub_funnel.send_hub_event("signup", email=" ") is False


def test_monta_o_corpo_do_passo(monkeypatch):
    sent: list[tuple[str, str, dict]] = []

    class _Thread:
        def __init__(self, target, args, daemon):
            self.target, self.args = target, args

        def start(self):
            sent.append(self.args)

    monkeypatch.setattr(hub_funnel, "get_settings", lambda: _settings("https://hub/x", "chave"))
    monkeypatch.setattr(hub_funnel.threading, "Thread", _Thread)
    ok = hub_funnel.send_hub_event(
        "signup",
        email=" Pessoa@Exemplo.com ",
        name="Pessoa",
        utm={"utm_source": "facebook", "utm_term": None},
        payload={"a": 1, "b": None},
        external_id="ro-signup-1",
    )
    assert ok is True
    url, key, body = sent[0]
    assert (url, key) == ("https://hub/x", "chave")
    assert body["email"] == "pessoa@exemplo.com"
    assert body["external_id"] == "ro-signup-1"
    assert body["source"] == "roteiro_online"
    assert body["utm"] == {"utm_source": "facebook"}
    assert body["payload"] == {"a": 1}


def test_falha_de_rede_nao_propaga(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("rede fora")

    monkeypatch.setattr(hub_funnel.httpx, "post", boom)
    hub_funnel._post("https://hub/x", "k", {"event_type": "signup"})


def test_conexao_salva_no_painel_vale_antes_do_ambiente(client, monkeypatch):
    from app.api.deps import get_current_superuser
    from app.main import app
    from app.models.external_api_key import ExternalApiKey
    from tests.conftest import TestingSessionLocal

    monkeypatch.setattr(hub_funnel, "get_settings", lambda: _settings("https://env/x", "chave-env"))
    hub_funnel.clear_config_cache()
    assert hub_funnel.hub_config() == ("https://env/x", "chave-env", "ambiente")

    app.dependency_overrides[get_current_superuser] = lambda: SimpleNamespace(is_superuser=True)
    base = "/api/v1/admin/admin-master/viajehub"
    try:
        assert client.put(base, json={"url": "https://hub.viajeon.com/api/public/funil/evento"}).status_code == 400
        assert client.put(base, json={"url": "http://hub/x", "key": "abc"}).status_code == 400
        saved = client.put(
            base,
            json={"url": "POST https://hub.viajeon.com/api/public/funil/evento", "key": " chave-do-roteiro-1234 "},
        )
        assert saved.status_code == 200, saved.text
        body = saved.json()
        assert body["url"] == "https://hub.viajeon.com/api/public/funil/evento"
        assert body["key_masked"].endswith("1234") and body["source"] == "painel"
        assert "chave-do-roteiro" not in saved.text

        db = TestingSessionLocal()
        record = db.query(ExternalApiKey).filter(ExternalApiKey.provider == "viajehub").one()
        assert "chave-do-roteiro" not in record.api_key_encrypted
        db.close()
        assert hub_funnel.hub_config() == (
            "https://hub.viajeon.com/api/public/funil/evento",
            "chave-do-roteiro-1234",
            "painel",
        )

        # Trocar só o endereço mantém a chave.
        client.put(base, json={"url": "https://outro.hub/api/public/funil/evento"})
        assert hub_funnel.hub_config()[1] == "chave-do-roteiro-1234"

        calls: list[tuple[str, str]] = []

        def fake_post(url, json, headers, timeout):
            calls.append((url, headers["x-funnel-key"]))
            assert json == {}
            return SimpleNamespace(status_code=400)

        monkeypatch.setattr(hub_funnel.httpx, "post", fake_post)
        tested = client.post(f"{base}/test").json()
        assert tested["ok"] is True
        assert calls == [("https://outro.hub/api/public/funil/evento", "chave-do-roteiro-1234")]

        monkeypatch.setattr(hub_funnel.httpx, "post", lambda *a, **k: SimpleNamespace(status_code=401))
        assert client.post(f"{base}/test").json()["ok"] is False

        assert client.delete(base).json()["source"] == "ambiente"
    finally:
        app.dependency_overrides.pop(get_current_superuser, None)
        hub_funnel.clear_config_cache()
