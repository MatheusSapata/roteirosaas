from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClientMeta:
    user_id: int
    agency_id: int
    connected_at: datetime


class WhatsAppRealtimeManager:
    """
    In-memory realtime manager (fase 3).
    Futuro: trocar por Redis pub/sub para múltiplas réplicas.
    """

    def __init__(self) -> None:
        self._by_agency: dict[int, dict[WebSocket, ClientMeta]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def register(self, websocket: WebSocket, *, user_id: int, agency_id: int) -> None:
        meta = ClientMeta(
            user_id=user_id,
            agency_id=agency_id,
            connected_at=datetime.now(timezone.utc),
        )
        async with self._lock:
            self._loop = asyncio.get_running_loop()
            self._by_agency[agency_id][websocket] = meta

    async def unregister(self, websocket: WebSocket, *, agency_id: int) -> None:
        async with self._lock:
            clients = self._by_agency.get(agency_id, {})
            clients.pop(websocket, None)
            if not clients and agency_id in self._by_agency:
                self._by_agency.pop(agency_id, None)

    async def broadcast_to_agency(self, *, agency_id: int, payload: dict[str, Any]) -> None:
        async with self._lock:
            clients = list(self._by_agency.get(agency_id, {}).keys())
        if not clients:
            return
        to_remove: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception as exc:
                logger.warning("Falha ao enviar evento websocket para agency=%s: %s", agency_id, exc)
                to_remove.append(ws)
        if to_remove:
            async with self._lock:
                agency_clients = self._by_agency.get(agency_id, {})
                for ws in to_remove:
                    agency_clients.pop(ws, None)
                if not agency_clients and agency_id in self._by_agency:
                    self._by_agency.pop(agency_id, None)

    def broadcast_to_agency_best_effort(self, *, agency_id: int, payload: dict[str, Any]) -> None:
        """
        Pode ser chamado de endpoints síncronos sem quebrar persistência.
        """
        try:
            loop = self._loop
            if not loop or loop.is_closed():
                return
            future = asyncio.run_coroutine_threadsafe(
                self.broadcast_to_agency(agency_id=agency_id, payload=payload),
                loop,
            )
            future.add_done_callback(lambda f: f.exception())
        except Exception as exc:
            logger.warning("Realtime best-effort falhou (agency=%s): %s", agency_id, exc)


whatsapp_realtime = WhatsAppRealtimeManager()
