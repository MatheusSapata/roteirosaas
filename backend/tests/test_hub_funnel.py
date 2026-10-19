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
