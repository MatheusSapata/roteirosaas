from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
import socket
import logging
import time
import base64

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    ok: bool
    detail: str


class EvolutionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.evolution_api_url.rstrip("/")
        self.api_key = (self.settings.evolution_api_key or "").strip()
        self.timeout = httpx.Timeout(30.0)

    @property
    def test_instance_name(self) -> str:
        # Fase 1: nome fixo e controlado no backend. No multi-tenant final sera por agencia.
        return self.settings.evolution_test_instance_name.strip() or "test-instance"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["apikey"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        statuses = expected_statuses or {200, 201}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self._headers(),
                json=json,
            )
        if response.status_code not in statuses:
            raise RuntimeError(
                f"Evolution request failed [{method} {path}] "
                f"status={response.status_code} body={response.text[:400]}"
            )
        if not response.text:
            return {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        except Exception as exc:  # pragma: no cover - fallback defensivo
            raise RuntimeError(f"Evolution returned invalid JSON for [{method} {path}]") from exc

    def _request_with_fallbacks(
        self,
        candidates: list[tuple[str, str]],
        *,
        json: dict[str, Any] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        errors: list[str] = []
        for method, path in candidates:
            try:
                return self._request(method, path, json=json, expected_statuses=expected_statuses)
            except Exception as exc:
                errors.append(f"{method} {path}: {exc}")
                continue
        detail = " | ".join(errors) if errors else "unknown error"
        raise RuntimeError(f"Evolution request failed for all candidates: {detail}")

    def create_instance(self, instance_name: str | None = None) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        webhook_url = (self.settings.evolution_webhook_url or "").strip()
        events = [
            "CONNECTION_UPDATE",
            "QRCODE_UPDATED",
            "MESSAGES_UPSERT",
            "MESSAGES_SET",
            "MESSAGES_UPDATE",
            "SEND_MESSAGE",
            "CHATS_UPDATE",
            "CONTACTS_UPDATE",
            "CONTACTS_UPSERT",
        ]
        payload: dict[str, Any] = {
            "instanceName": name,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
        }
        if webhook_url:
            # Compatibilidade com versões diferentes da Evolution (v1/v2).
            payload.update(
                {
                    "webhook_by_events": False,
                    "webhook_base64": True,
                    "events": events,
                    "webhookUrl": webhook_url,
                    "webhookByEvents": False,
                    "webhookBase64": True,
                    "webhookEvents": events,
                    "webhook": {
                        "url": webhook_url,
                        "byEvents": False,
                        "base64": True,
                        "events": events,
                    },
                }
            )
        try:
            created = self._request_with_fallbacks(
                [("POST", "/instance/create"), ("POST", "/instance/create/")],
                json=payload,
            )
            if webhook_url:
                self._configure_instance_webhook(name=name, webhook_url=webhook_url, events=events)
            return created
        except Exception as exc:
            lowered = str(exc).lower()
            if "already in use" in lowered:
                if self._instance_exists(name):
                    if webhook_url:
                        self._configure_instance_webhook(name=name, webhook_url=webhook_url, events=events)
                    # Fluxo idempotente: se já existe, tratamos como sucesso operacional.
                    status = self.get_connection_status(name)
                    return {
                        "instance": {"instanceName": name, "status": "already_exists"},
                        "idempotent": True,
                        "connection": status,
                    }
            raise

    def default_webhook_events(self) -> list[str]:
        return [
            "CONNECTION_UPDATE",
            "QRCODE_UPDATED",
            "MESSAGES_UPSERT",
            "MESSAGES_SET",
            "MESSAGES_UPDATE",
            "SEND_MESSAGE",
            "CHATS_UPDATE",
            "CONTACTS_UPDATE",
            "CONTACTS_UPSERT",
        ]

    def reapply_instance_webhook_events(self, *, instance_name: str) -> dict[str, Any]:
        webhook_url = (self.settings.evolution_webhook_url or "").strip()
        if not webhook_url:
            raise RuntimeError("EVOLUTION_WEBHOOK_URL não configurada.")
        events = self.default_webhook_events()
        self._configure_instance_webhook(name=instance_name, webhook_url=webhook_url, events=events)
        return {
            "instance_name": instance_name,
            "webhook_url": webhook_url,
            "events": events,
            "status": "reapplied",
        }

    def get_qr_code(self, instance_name: str | None = None) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        attempts: list[dict[str, Any]] = []
        candidates: list[tuple[str, str]] = [
            ("GET", f"/instance/connect/{name}"),
            ("GET", f"/instance/connect/{name}/"),
            ("GET", f"/instance/qrcode/{name}"),
            ("GET", f"/instance/qrCode/{name}"),
        ]
        pairing_number = "".join(ch for ch in (self.settings.evolution_pairing_number or "") if ch.isdigit())
        if pairing_number:
            candidates.append(("GET", f"/instance/connect/{name}?number={pairing_number}"))

        last_exc: Exception | None = None
        for method, path in candidates:
            try:
                result = self._request(method, path)
                qr = self._extract_qr_payload(result)
                attempts.append({"endpoint": path, "ok": True, "result": result, "extracted": qr})
                if qr.get("qr_code_base64") or qr.get("pairing_code") or qr.get("code"):
                    return {
                        "instance": name,
                        "qr_code_base64": qr.get("qr_code_base64"),
                        "pairing_code": qr.get("pairing_code"),
                        "code": qr.get("code"),
                        "count": qr.get("count"),
                        "raw": result,
                        "attempts": attempts,
                    }
            except Exception as exc:
                last_exc = exc
                attempts.append({"endpoint": path, "ok": False, "error": str(exc)})

        diagnostics = self._collect_qr_diagnostics(name)
        logger.warning(
            "Evolution returned empty QR payload for instance=%s attempts=%s diagnostics=%s",
            name,
            attempts,
            diagnostics,
        )
        if last_exc and not attempts:
            raise RuntimeError(f"Falha ao buscar QR code: {last_exc}") from last_exc
        return {
            "instance": name,
            "qr_code_base64": None,
            "pairing_code": None,
            "code": None,
            "count": 0,
            "raw": attempts[-1]["result"] if attempts and attempts[-1].get("result") else {},
            "attempts": attempts,
            "diagnostics": diagnostics,
            "diagnosis": (
                "Evolution respondeu sem QR (count=0). "
                "Na v2.2.3 isso pode ocorrer por limitação/bug do endpoint REST; "
                "valide no /manager e eventos de QRCODE_UPDATED."
            ),
        }

    def get_connection_status(self, instance_name: str | None = None) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        result = self._request_with_fallbacks(
            [
                ("GET", f"/instance/connectionState/{name}"),
                ("GET", f"/instance/status/{name}"),
                ("GET", f"/instance/fetchInstances"),
            ]
        )
        state = self._extract_state(result, name)
        mapped = self._map_status(state)
        phone = self._extract_phone_from_payload(result)
        if not phone:
            instances = self._best_effort_request("GET", "/instance/fetchInstances")
            payload = instances.get("payload")
            if isinstance(payload, list):
                for row in payload:
                    if not isinstance(row, dict):
                        continue
                    row_name = row.get("name") or row.get("instanceName")
                    if row_name != name:
                        continue
                    phone = self._extract_phone_from_payload(row)
                    if phone:
                        break
        return {"instance": name, "status": mapped, "raw_state": state, "raw": result, "phone": phone}

    def send_text(self, number: str, text: str, instance_name: str | None = None) -> dict[str, Any]:
        return self.send_text_target(target=number, text=text, instance_name=instance_name)

    def send_text_target(self, target: str, text: str, instance_name: str | None = None) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        raw_target = (target or "").strip()
        if not raw_target:
            raise RuntimeError("Destino de mensagem vazio.")

        if "@" in raw_target:
            number_or_jid = raw_target
        else:
            digits = "".join(ch for ch in raw_target if ch.isdigit())
            if len(digits) < 10:
                raise RuntimeError("Numero invalido para envio.")
            number_or_jid = digits

        payload = {"number": number_or_jid, "text": text}
        return self._request_with_fallbacks(
            [
                ("POST", f"/message/sendText/{name}"),
                ("POST", f"/message/sendText/{name}/"),
            ],
            json=payload,
        )

    def send_media_target(
        self,
        *,
        target: str,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
        media_type: str,
        caption: str | None = None,
        ptt: bool = False,
        instance_name: str | None = None,
    ) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        raw_target = (target or "").strip()
        if not raw_target:
            raise RuntimeError("Destino de mídia vazio.")
        if "@" in raw_target:
            number_or_jid = raw_target
        else:
            digits = "".join(ch for ch in raw_target if ch.isdigit())
            if len(digits) < 10:
                raise RuntimeError("Numero invalido para envio de mídia.")
            number_or_jid = digits
        encoded = base64.b64encode(file_bytes).decode("ascii")
        media_data_url = f"data:{mime_type};base64,{encoded}"
        normalized_media_type = (media_type or "").strip().lower()
        if normalized_media_type not in {"image", "video", "audio", "document"}:
            raise RuntimeError("Tipo de mídia inválido para Evolution.")

        payload_variants: list[dict[str, Any]] = [
            {
                "number": number_or_jid,
                "mediatype": normalized_media_type,
                "mimetype": mime_type,
                "media": encoded,  # Evolution v2.3.6: "url or base64"
                "fileName": file_name,
                "caption": (caption or "").strip(),
                "ptt": bool(ptt),
            },
            {
                "number": number_or_jid,
                "mediatype": normalized_media_type,
                "mimetype": mime_type,
                "media": media_data_url,  # fallback para versões que aceitam data URL
                "fileName": file_name,
                "caption": (caption or "").strip(),
                "ptt": bool(ptt),
            },
        ]
        candidates = [
            ("POST", f"/message/sendMedia/{name}"),
            ("POST", f"/message/sendMedia/{name}/"),
        ]
        errors: list[str] = []
        for payload in payload_variants:
            for method, path in candidates:
                try:
                    return self._request(method, path, json=payload)
                except Exception as exc:
                    errors.append(f"{method} {path}: {exc}")
        raise RuntimeError(f"Evolution request failed for all candidates: {' | '.join(errors)}")

    def find_group_info(self, *, instance_name: str, group_jid: str) -> dict[str, Any]:
        name = (instance_name or "").strip()
        jid = (group_jid or "").strip()
        if not name or not jid:
            return {}
        return self._request_with_fallbacks(
            [
                ("GET", f"/group/findGroupInfos/{name}?groupJid={jid}"),
                ("GET", f"/group/findGroupInfos/{name}/?groupJid={jid}"),
            ],
            expected_statuses={200, 201, 204},
        )

    def fetch_profile_picture_url(self, *, instance_name: str, remote: str) -> str | None:
        name = (instance_name or "").strip()
        target = (remote or "").strip()
        if not name or not target:
            return None
        candidates: list[dict[str, Any]] = []
        if "@" in target:
            candidates.append({"number": target})
            candidates.append({"jid": target})
            digits = "".join(ch for ch in target if ch.isdigit())
            if digits:
                candidates.append({"number": digits})
        else:
            digits = "".join(ch for ch in target if ch.isdigit())
            if digits:
                candidates.append({"number": digits})
                candidates.append({"jid": f"{digits}@s.whatsapp.net"})
        paths = [
            f"/chat/fetchProfilePictureUrl/{name}",
            f"/chat/fetchProfilePictureUrl/{name}/",
            f"/chat/profilePictureUrl/{name}",
            f"/chat/profilePictureUrl/{name}/",
        ]
        for body in candidates:
            for path in paths:
                try:
                    response = self._request("POST", path, json=body, expected_statuses={200, 201})
                    pic = self._extract_profile_picture_from_payload(response)
                    if pic:
                        return pic
                except Exception:
                    continue
        return None

    def disconnect_instance(self, instance_name: str | None = None) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        return self._request_with_fallbacks(
            [
                ("DELETE", f"/instance/logout/{name}"),
                ("DELETE", f"/instance/delete/{name}"),
                ("POST", f"/instance/logout/{name}"),
            ],
            expected_statuses={200, 201, 204},
        )

    def get_media_base64_from_message(
        self,
        *,
        instance_name: str,
        message_payload: dict[str, Any],
        convert_to_mp4: bool = False,
    ) -> str | None:
        name = (instance_name or "").strip()
        if not name or not isinstance(message_payload, dict):
            return None
        candidates = [
            {"message": message_payload, "convertToMp4": bool(convert_to_mp4)},
            {**message_payload, "convertToMp4": bool(convert_to_mp4)},
        ]
        paths = [
            f"/chat/getBase64FromMediaMessage/{name}",
            f"/chat/getBase64FromMediaMessage/{name}/",
        ]
        errors: list[str] = []
        for body in candidates:
            for path in paths:
                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        response = client.request(
                            method="POST",
                            url=f"{self.base_url}{path}",
                            headers=self._headers(),
                            json=body,
                        )
                    if response.status_code not in {200, 201, 204}:
                        errors.append(f"POST {path}: status={response.status_code}")
                        continue
                    raw_text = (response.text or "").strip()
                    if raw_text:
                        try:
                            parsed = response.json()
                            b64 = self._extract_base64_from_unknown(parsed)
                            if b64:
                                return b64
                        except Exception:
                            if self._looks_like_base64(raw_text):
                                return raw_text
                    content_b64 = response.headers.get("x-base64") or response.headers.get("base64")
                    if isinstance(content_b64, str) and self._looks_like_base64(content_b64):
                        return content_b64
                except Exception as exc:
                    errors.append(f"POST {path}: {exc}")
                    continue
        if errors:
            logger.warning(
                "Could not resolve media base64 from Evolution instance=%s errors=%s",
                name,
                errors,
            )
        return None

    def reset_instance(self, instance_name: str | None = None) -> dict[str, Any]:
        name = (instance_name or self.test_instance_name).strip()
        steps: list[dict[str, Any]] = []
        steps.append({"step": "logout", "result": self._best_effort_request("DELETE", f"/instance/logout/{name}")})
        steps.append({"step": "delete", "result": self._best_effort_request("DELETE", f"/instance/delete/{name}")})
        created: dict[str, Any] | None = None
        last_error: Exception | None = None
        for attempt in range(1, 5):
            time.sleep(1.0)
            try:
                created = self.create_instance(name)
                # Se retornou idempotente, só aceitamos quando a instância realmente existir.
                if created.get("idempotent") and not self._instance_exists(name):
                    continue
                steps.append({"step": "create", "attempt": attempt, "result": created})
                break
            except Exception as exc:
                last_error = exc
                steps.append({"step": "create", "attempt": attempt, "error": str(exc)})
        if created is None:
            raise RuntimeError(f"Falha ao recriar instância após reset: {last_error}")
        status = self.get_connection_status(name)
        return {"instance": name, "steps": steps, "created": created, "status": status}

    def check_evolution_health(self) -> ServiceHealth:
        try:
            self._request_with_fallbacks(
                [
                    ("GET", "/"),
                    ("GET", "/manager/instance"),
                    ("GET", "/instance/fetchInstances"),
                ],
                expected_statuses={200, 201, 204},
            )
            return ServiceHealth(ok=True, detail="reachable")
        except Exception as exc:
            return ServiceHealth(ok=False, detail=str(exc))

    def check_redis_health(self) -> ServiceHealth:
        raw_url = (self.settings.redis_url or "").strip()
        if not raw_url:
            return ServiceHealth(ok=False, detail="REDIS_URL is empty")
        parsed = urlparse(raw_url)
        host = parsed.hostname or "redis"
        port = parsed.port or 6379
        try:
            with socket.create_connection((host, port), timeout=2.5):
                return ServiceHealth(ok=True, detail="reachable")
        except OSError as exc:
            return ServiceHealth(ok=False, detail=str(exc))

    def _extract_state(self, payload: dict[str, Any], instance_name: str) -> str:
        direct = payload.get("instance") if isinstance(payload.get("instance"), dict) else None
        if direct and isinstance(direct.get("state"), str):
            return direct["state"]
        if isinstance(payload.get("state"), str):
            return str(payload["state"])
        if isinstance(payload.get("status"), str):
            return str(payload["status"])
        if isinstance(payload.get("instance"), str):
            return str(payload["instance"])
        if isinstance(payload.get("data"), list):
            for row in payload["data"]:
                if not isinstance(row, dict):
                    continue
                name = row.get("name") or row.get("instanceName")
                if name == instance_name:
                    candidate = row.get("connectionStatus") or row.get("status") or row.get("state")
                    if isinstance(candidate, str):
                        return candidate
        if isinstance(payload, list):
            for row in payload:
                if not isinstance(row, dict):
                    continue
                name = row.get("name") or row.get("instanceName")
                if name == instance_name:
                    candidate = row.get("connectionStatus") or row.get("status") or row.get("state")
                    if isinstance(candidate, str):
                        return candidate
        return "unknown"

    def _map_status(self, raw_state: str) -> str:
        state = (raw_state or "").strip().lower()
        if state in {"open", "connected"}:
            return "connected"
        if state in {"connecting", "pairing", "initializing"}:
            return "connecting"
        if state in {"qrcode", "qr", "scan", "scanqr"}:
            return "qr_needed"
        if state in {"close", "closed", "disconnected", "logout"}:
            return "disconnected"
        if "qr" in state:
            return "qr_needed"
        return "disconnected"

    def _best_effort_request(self, method: str, path: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self._headers(),
            )
        payload: Any
        try:
            payload = response.json() if response.text else {}
        except Exception:
            payload = response.text[:300]
        return {"status_code": response.status_code, "payload": payload}

    def _extract_qr_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        qr_base64 = self._find_first_string(payload, ["base64", "qrcodeBase64", "qrBase64", "qr"])
        code = self._find_first_string(payload, ["code", "qrCode"])
        pairing_code = self._find_first_string(payload, ["pairingCode", "pairing_code"])
        count = self._find_first_int(payload, ["count"])
        return {
            "qr_code_base64": qr_base64,
            "code": code,
            "pairing_code": pairing_code,
            "count": count,
        }

    def _collect_qr_diagnostics(self, instance_name: str) -> dict[str, Any]:
        info = self.get_server_info()
        state = self._best_effort_request("GET", f"/instance/connectionState/{instance_name}")
        instances = self._best_effort_request("GET", "/instance/fetchInstances")
        return {
            "server_info": info,
            "connection_state": state,
            "instances": instances,
        }

    def get_server_info(self) -> dict[str, Any]:
        return self._best_effort_request("GET", "/")

    def _find_first_string(self, obj: Any, keys: list[str]) -> str | None:
        values = self._find_values(obj, set(keys))
        for value in values:
            if isinstance(value, str) and value.strip():
                return value
        return None

    def _find_first_int(self, obj: Any, keys: list[str]) -> int | None:
        values = self._find_values(obj, set(keys))
        for value in values:
            if isinstance(value, int):
                return value
        return None

    def _find_values(self, obj: Any, keys: set[str]) -> list[Any]:
        found: list[Any] = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in keys:
                    found.append(value)
                found.extend(self._find_values(value, keys))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(self._find_values(item, keys))
        return found

    def _configure_instance_webhook(self, *, name: str, webhook_url: str, events: list[str]) -> None:
        payloads = [
            {
                "enabled": True,
                "url": webhook_url,
                "webhookUrl": webhook_url,
                "events": events,
                "webhook_by_events": False,
                "webhook_base64": True,
            },
            {
                "webhook": {
                    "enabled": True,
                    "url": webhook_url,
                    "byEvents": False,
                    "base64": True,
                    "events": events,
                }
            },
        ]
        candidates = [
            ("POST", f"/webhook/set/{name}"),
            ("POST", f"/webhook/set/{name}/"),
            ("POST", f"/instance/webhook/{name}"),
            ("POST", f"/instance/webhook/{name}/"),
        ]
        last_error: Exception | None = None
        for body in payloads:
            for method, path in candidates:
                try:
                    self._request(method, path, json=body, expected_statuses={200, 201, 204})
                    logger.info("Evolution webhook configured for instance=%s endpoint=%s", name, path)
                    return
                except Exception as exc:
                    last_error = exc
                    continue
        if last_error:
            logger.warning(
                "Could not configure Evolution webhook for instance=%s url=%s error=%s",
                name,
                webhook_url,
                last_error,
            )

    def _extract_phone_from_payload(self, payload: Any) -> str | None:
        if not payload:
            return None
        keys = {"phone", "phoneNumber", "number", "ownerJid", "wid", "user"}
        values = self._find_values(payload, keys)
        for value in values:
            digits = self._digits_from_phone_like(value)
            if digits:
                return digits
        return None

    def _digits_from_phone_like(self, value: Any) -> str | None:
        if value is None:
            return None
        raw = str(value).replace("@s.whatsapp.net", "")
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) < 10:
            return None
        return digits

    def _instance_exists(self, instance_name: str) -> bool:
        rows = self._best_effort_request("GET", "/instance/fetchInstances")
        payload = rows.get("payload")
        if not isinstance(payload, list):
            return False
        for row in payload:
            if not isinstance(row, dict):
                continue
            if (row.get("name") or row.get("instanceName")) == instance_name:
                return True
        return False

    def _extract_base64_from_unknown(self, payload: Any) -> str | None:
        if isinstance(payload, str):
            return payload if self._looks_like_base64(payload) else None
        if isinstance(payload, dict):
            for key in ("base64", "data", "media", "file", "buffer"):
                value = payload.get(key)
                if isinstance(value, str) and self._looks_like_base64(value):
                    return value
            for value in payload.values():
                nested = self._extract_base64_from_unknown(value)
                if nested:
                    return nested
        if isinstance(payload, list):
            for item in payload:
                nested = self._extract_base64_from_unknown(item)
                if nested:
                    return nested
        return None

    def _looks_like_base64(self, value: str) -> bool:
        raw = (value or "").strip()
        if raw.startswith("data:"):
            return True
        if len(raw) < 40:
            return False
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r")
        return all(ch in allowed for ch in raw[:512])

    def _extract_profile_picture_from_payload(self, payload: Any) -> str | None:
        if isinstance(payload, str):
            cleaned = payload.strip()
            if cleaned.startswith(("http://", "https://")):
                return cleaned
            return None
        if isinstance(payload, dict):
            for key in ("profilePictureUrl", "profilePicUrl", "imgUrl", "url", "picture"):
                value = payload.get(key)
                if isinstance(value, str):
                    cleaned = value.strip()
                    if cleaned.startswith(("http://", "https://")):
                        return cleaned
            for value in payload.values():
                nested = self._extract_profile_picture_from_payload(value)
                if nested:
                    return nested
        if isinstance(payload, list):
            for item in payload:
                nested = self._extract_profile_picture_from_payload(item)
                if nested:
                    return nested
        return None
