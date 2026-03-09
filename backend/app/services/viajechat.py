from __future__ import annotations

from typing import Any

import httpx


class ViajeChatClientError(Exception):
    """Raised when ViajeChat returns an error or cannot be reached."""


class ViajeChatClient:
    def __init__(self, api_key: str, base_url: str = "https://painel.viajechat.com.br/api/v1") -> None:
        if not api_key:
            raise ValueError("ViajeChat API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers = {**self._default_headers, **headers}
        try:
            response = httpx.request(method, url, headers=headers, timeout=30, **kwargs)
        except httpx.HTTPError as exc:
            raise ViajeChatClientError("Erro ao acessar ViajeChat") from exc
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = {"status_code": response.status_code, "body": response.text}
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

    def add_tags_to_contact(self, contact_id: str, tag_ids: list[str]) -> None:
        if not contact_id or not tag_ids:
            return
        payload = {"contact_id": contact_id, "tag_ids": tag_ids}
        self._request("POST", "/contacts/tags", json=payload)

    def add_tags_to_contact_by_email(self, email: str, tag_ids: list[str]) -> bool:
        if not email or not tag_ids:
            return False
        contact = self.get_contact_by_email(email)
        contact_id = (contact or {}).get("id")
        if not contact_id:
            return False
        self.add_tags_to_contact(contact_id, tag_ids)
        return True
