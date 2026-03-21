from __future__ import annotations

import base64
import json
import re
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.ai import AiAttachmentIn
from app.services.ai_prompts import BRIEFING_EXTRACTION_PROMPT, PAGE_PLANNER_PROMPT


class GeminiClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.gemini_api_key
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY não configurado.")
        self.fast_model = self.settings.gemini_fast_model or self.settings.gemini_text_model

    async def generate_page_plan(self, prompt: str, attachments: List[AiAttachmentIn]) -> str:
        contents: list[dict[str, Any]] = [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
        if attachments:
            parts: list[dict[str, Any]] = []
            for attachment in attachments:
                mime = attachment.mime_type or "application/octet-stream"
                parts.append(
                    {
                        "inlineData": {
                            "mimeType": mime,
                            "data": attachment.data,
                        }
                    }
                )
            contents.append({"role": "user", "parts": parts})

        payload = {
            "system_instruction": {"parts": [{"text": PAGE_PLANNER_PROMPT.strip()}]},
            "contents": contents,
        }
        response = await self._post(self.settings.gemini_text_model, payload)
        return self._extract_text(response)

    async def interpret_briefing(self, briefing: str, attachments: List[AiAttachmentIn]) -> dict[str, Any]:
        contents: list[dict[str, Any]] = [
            {
                "role": "user",
                "parts": [{"text": briefing}],
            }
        ]
        if attachments:
            parts: list[dict[str, Any]] = []
            for attachment in attachments:
                mime = attachment.mime_type or "application/octet-stream"
                parts.append(
                    {
                        "inlineData": {
                            "mimeType": mime,
                            "data": attachment.data,
                        }
                    }
                )
            contents.append({"role": "user", "parts": parts})

        payload = {
            "system_instruction": {"parts": [{"text": BRIEFING_EXTRACTION_PROMPT.strip()}]},
            "contents": contents,
        }
        response = await self._post(self.fast_model, payload)
        text = self._strip_code_fence(self._extract_text(response))
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail=f"Retorno inválido do Gemini: {text[:400]}") from exc

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ]
        }
        response = await self._post(self.settings.gemini_image_model, payload)
        data = self._extract_inline_data(response)
        if not data:
            return None
        try:
            return base64.b64decode(data)
        except Exception:
            return None

    async def _post(self, model: str, payload: dict[str, Any]) -> dict[str, Any]:
        base_url = self.settings.gemini_api_base_url.rstrip("/")
        endpoint = f"{base_url}/v1beta/{model}:generateContent"
        headers = {"x-goog-api-key": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
        except httpx.ReadTimeout as exc:
            raise HTTPException(status_code=504, detail="Tempo excedido ao acessar o Gemini.") from exc
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise HTTPException(status_code=502, detail=f"Erro ao acessar o Gemini: {detail}")
        return resp.json()

    def _extract_text(self, response: dict[str, Any]) -> str:
        candidates = response.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            texts = [part.get("text", "") for part in parts if part.get("text")]
            combined = "\n".join(texts).strip()
            if combined:
                return combined
        raise HTTPException(status_code=502, detail="Gemini não retornou conteúdo textual.")

    def _extract_inline_data(self, response: dict[str, Any]) -> Optional[str]:
        candidates = response.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            for part in parts:
                data = part.get("inlineData") or part.get("inline_data")
                if data and data.get("data"):
                    return data.get("data")
        return None

    def _strip_code_fence(self, text: str) -> str:
        cleaned = text.strip()
        match = re.match(r"^```(?:json)?\s*([\s\S]+?)\s*```$", cleaned)
        if match:
            return match.group(1).strip()
        return cleaned
