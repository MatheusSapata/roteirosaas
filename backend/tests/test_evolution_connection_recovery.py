from app.services.evolution import EvolutionService

OTHER_AGENCY_ROW = {
    "name": "agency-2-whatsapp",
    "connectionStatus": "open",
    "ownerJid": "5511988887777@s.whatsapp.net",
    "number": "5511988887777",
    "token": "segredo-outra-agencia",
}


def _service() -> EvolutionService:
    return EvolutionService.__new__(EvolutionService)


def test_status_fallback_ignores_other_agencies_instances(monkeypatch):
    service = _service()
    # connectionState falhou; o fallback devolveu a lista de todas as instâncias.
    monkeypatch.setattr(service, "_request_with_fallbacks", lambda *a, **k: {"data": [OTHER_AGENCY_ROW]})
    monkeypatch.setattr(
        service, "_best_effort_request", lambda *a, **k: {"status_code": 200, "payload": [OTHER_AGENCY_ROW]}
    )

    result = service.get_connection_status("agency-1-whatsapp")

    assert result["phone"] is None
    assert result["status"] == "disconnected"
    assert result["raw"] == {"data": []}


def test_status_reads_phone_from_own_instance_owner_jid(monkeypatch):
    service = _service()
    own = {"name": "agency-1-whatsapp", "connectionStatus": "open", "ownerJid": "5553991411379:7@s.whatsapp.net",
           "number": "5500000000000"}
    monkeypatch.setattr(service, "_request_with_fallbacks", lambda *a, **k: {"data": [OTHER_AGENCY_ROW, own]})

    result = service.get_connection_status("agency-1-whatsapp")

    assert result["status"] == "connected"
    assert result["phone"] == "5553991411379"


def test_qr_recreates_deleted_instance_and_retries(monkeypatch):
    service = _service()
    service.settings = type("S", (), {"evolution_pairing_number": "5551999999999", "evolution_test_instance_name": "test-instance"})()
    calls: list[str] = []
    created: list[str] = []

    def fake_request(method, path, **kwargs):
        calls.append(path)
        if not created:
            raise RuntimeError("status=404 instance does not exist")
        return {"base64": "data:image/png;base64,AAAA", "count": 1}

    monkeypatch.setattr(service, "_request", fake_request)
    monkeypatch.setattr(
        service, "_best_effort_request", lambda *a, **k: {"status_code": 200, "payload": [OTHER_AGENCY_ROW]}
    )
    monkeypatch.setattr(service, "create_instance", lambda name: created.append(name) or {})

    result = service.get_qr_code("agency-1-whatsapp")

    assert created == ["agency-1-whatsapp"]
    assert result["recovered"] == "recreated"
    assert result["qr_code_base64"].startswith("data:image")
    # O número fixo de pareamento do ambiente nunca é usado na conexão de uma agência.
    assert not any("number=" in path for path in calls)


def test_qr_never_touches_connected_instance(monkeypatch):
    service = _service()
    service.settings = type("S", (), {"evolution_pairing_number": None, "evolution_test_instance_name": "test-instance"})()
    own = {"name": "agency-1-whatsapp", "connectionStatus": "open"}
    monkeypatch.setattr(service, "_request", lambda *a, **k: {"count": 0})
    best_effort: list[tuple] = []

    def fake_best_effort(method, path):
        best_effort.append((method, path))
        return {"status_code": 200, "payload": [own]}

    monkeypatch.setattr(service, "_best_effort_request", fake_best_effort)
    monkeypatch.setattr(service, "create_instance", lambda name: (_ for _ in ()).throw(AssertionError("no create")))

    result = service.get_qr_code("agency-1-whatsapp")

    assert result["qr_code_base64"] is None
    assert "recovered" not in result
    assert not any(method == "DELETE" for method, _ in best_effort)
    assert "token" not in str(result["diagnostics"])


def test_disconnect_does_not_delete_instance(monkeypatch):
    service = _service()
    paths: list[tuple[str, str]] = []

    def fake_request(method, path, **kwargs):
        paths.append((method, path))
        raise RuntimeError("status=400 instance is not connected")

    monkeypatch.setattr(service, "_request", fake_request)

    result = service.disconnect_instance("agency-1-whatsapp")

    assert result["status"] == "logout_failed"
    assert all("/delete/" not in path for _, path in paths)
