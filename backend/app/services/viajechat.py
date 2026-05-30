from __future__ import annotations

from typing import Any

import httpx
import logging


class ViajeChatClientError(Exception):
    """Raised when ViajeChat returns an error or cannot be reached."""


logger = logging.getLogger(__name__)


class ViajeChatClient:
    def __init__(self, api_key: str, base_url: str = "https://painel.viajechat.com.br/api/v1") -> None:
        if not api_key:
            raise ValueError("ViajeChat API key is required")
        self.api_key = api_key
        normalized_base = (base_url or "").rstrip("/")
        if normalized_base.endswith("/api/v1"):
            self.base_url = normalized_base
        else:
            self.base_url = f"{normalized_base}/api/v1"
        self._default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers = {**self._default_headers, **headers}
        logger.info("VIAJECHAT_HTTP_REQUEST method=%s path=%s", method, path)
        try:
            response = httpx.request(method, url, headers=headers, timeout=30, **kwargs)
        except httpx.HTTPError as exc:
            logger.exception("VIAJECHAT_HTTP_ERROR method=%s path=%s", method, path)
            raise ViajeChatClientError("Erro ao acessar ViajeChat") from exc
        logger.info("VIAJECHAT_HTTP_RESPONSE method=%s path=%s status=%s", method, path, response.status_code)
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = {"status_code": response.status_code, "body": response.text}
            logger.error("VIAJECHAT_HTTP_FAIL method=%s path=%s payload=%s", method, path, payload)
            raise ViajeChatClientError(payload)
        if not response.content:
            return None
        return response.json()

    def get_contact_by_email(self, email: str) -> dict[str, Any] | None:
        if not email:
            return None
        params = {"search": email, "limit": 1}
        data = self._request("GET", "/contacts", params=params)
        if not data:
            return None
        contacts = data.get("data") or []
        return contacts[0] if contacts else None

    def get_contact_by_phone(self, phone: str) -> dict[str, Any] | None:
        if not phone:
            return None
        params = {"search": phone, "limit": 1}
        data = self._request("GET", "/contacts", params=params)
        if not data:
            return None
        contacts = data.get("data") or []
        return contacts[0] if contacts else None

    def create_contact(self, *, name: str, email: str | None = None, phone: str | None = None) -> dict[str, Any]:
        payload = {
            "name": name or "",
            "email": email or None,
            "phone": phone or None,
        }
        # Remove nulos para evitar validação de payload em alguns painéis.
        payload = {key: value for key, value in payload.items() if value}
        return self._request("POST", "/contacts", json=payload) or {}

    def create_deal_card(
        self,
        *,
        phone: str,
        name: str | None = None,
        email: str | None = None,
        sector_id: str | None = None,
        sector_name: str | None = None,
        column_id: str | None = None,
        column_name: str | None = None,
        lead_source: str | None = None,
        value: float | None = None,
        notes: list[str] | None = None,
    ) -> dict[str, Any]:
        contact_payload: dict[str, Any] = {"phone": phone}
        if name:
            contact_payload["name"] = name
        if email:
            contact_payload["email"] = email

        kanban_payload: dict[str, Any] = {}
        if sector_id:
            kanban_payload["sector_id"] = sector_id
        elif sector_name:
            kanban_payload["sector_name"] = sector_name
        if column_id:
            kanban_payload["column_id"] = column_id
        elif column_name:
            kanban_payload["column_name"] = column_name

        payload: dict[str, Any] = {
            "contact": contact_payload,
            "kanban": kanban_payload,
        }
        deal_payload: dict[str, Any] = {}
        if lead_source:
            deal_payload["lead_source"] = lead_source
        if value is not None:
            deal_payload["value"] = value
        if deal_payload:
            payload["deal"] = deal_payload
        if notes:
            payload["notes"] = [str(item) for item in notes if str(item).strip()]
        masked_payload = self._mask_deal_payload(payload)
        logger.info("VIAJECHAT_DEAL_CREATE_PAYLOAD payload=%s", masked_payload)
        return self._request("POST", "/deals/create", json=payload) or {}

    @staticmethod
    def _mask_deal_payload(payload: dict[str, Any]) -> dict[str, Any]:
        copy_payload = dict(payload or {})
        contact = dict(copy_payload.get("contact") or {})
        email = str(contact.get("email") or "").strip()
        phone = "".join(ch for ch in str(contact.get("phone") or "") if ch.isdigit())
        if email and "@" in email:
            local, domain = email.split("@", 1)
            contact["email"] = f"{local[:2]}***@{domain}"
        elif email:
            contact["email"] = "***"
        if phone:
            contact["phone"] = f"***{phone[-4:]}"
        copy_payload["contact"] = contact
        return copy_payload

    def find_or_create_contact(
        self,
        *,
        name: str,
        email: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any] | None:
        contact = None
        if email:
            contact = self.get_contact_by_email(email)
        if not contact and phone:
            contact = self.get_contact_by_phone(phone)
        if contact:
            return contact
        if not (email or phone):
            return None
        created = self.create_contact(name=name, email=email, phone=phone)
        if isinstance(created, dict) and created.get("id"):
            return created
        if email:
            return self.get_contact_by_email(email)
        if phone:
            return self.get_contact_by_phone(phone)
        return None

    def add_tags_to_contact(self, contact_id: str, tag_ids: list[str]) -> None:
        if not contact_id or not tag_ids:
            return
        payload = {"contact_id": contact_id, "tag_ids": tag_ids}
        self._request("POST", "/contacts/tags", json=payload)

    def remove_tags_from_contact(self, contact_id: str, tag_ids: list[str]) -> None:
        if not contact_id or not tag_ids:
            return
        for tag_id in tag_ids:
            if not tag_id:
                continue
            payload = {"contact_id": contact_id, "tag_id": tag_id}
            self._request("POST", "/contacts/tags/remove", json=payload)

    def add_tags_to_contact_by_email(self, email: str, tag_ids: list[str]) -> bool:
        if not email or not tag_ids:
            return False
        contact = self.get_contact_by_email(email)
        contact_id = (contact or {}).get("id")
        if not contact_id:
            return False
        self.add_tags_to_contact(contact_id, tag_ids)
        return True

    def add_tags_to_contact_by_email_or_phone(
        self,
        *,
        name: str,
        email: str | None,
        phone: str | None,
        tag_ids: list[str],
    ) -> bool:
        if not tag_ids:
            return False
        contact = self.find_or_create_contact(name=name, email=email, phone=phone)
        contact_id = (contact or {}).get("id")
        if not contact_id:
            return False
        self.add_tags_to_contact(str(contact_id), tag_ids)
        return True

    def remove_tags_from_contact_by_email(self, email: str, tag_ids: list[str]) -> bool:
        if not email or not tag_ids:
            return False
        contact = self.get_contact_by_email(email)
        contact_id = (contact or {}).get("id")
        if not contact_id:
            return False
        self.remove_tags_from_contact(str(contact_id), tag_ids)
        return True

    def add_tags_to_contact_by_id(self, contact_id: str, tag_ids: list[str]) -> bool:
        if not contact_id or not tag_ids:
            return False
        self.add_tags_to_contact(str(contact_id), tag_ids)
        return True

    def remove_tags_from_contact_by_id(self, contact_id: str, tag_ids: list[str]) -> bool:
        if not contact_id or not tag_ids:
            return False
        self.remove_tags_from_contact(str(contact_id), tag_ids)
        return True
