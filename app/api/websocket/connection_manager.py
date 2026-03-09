"""
Canal Educação v3.0 — WebSocket Connection Manager.
Gerencia conexões ativas, broadcast de atualizações de grade,
e slot-locking para prevenir edições simultâneas.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Gerencia conexões WebSocket e estado de slots bloqueados."""

    def __init__(self):
        # Conexões ativas: {user_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Slots bloqueados: {slot_key: {"user_id": str, "user_name": str, "locked_at": str}}
        self.locked_slots: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str, user_name: str):
        """Aceita conexão e registra o utilizador."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # Envia estado atual dos slots bloqueados ao novo utilizador
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "locked_slots": self.locked_slots,
            "connected_users": len(self.active_connections),
        })

        # Notifica todos que um novo utilizador conectou
        await self.broadcast({
            "type": "USER_CONNECTED",
            "user_id": user_id,
            "user_name": user_name,
            "connected_users": len(self.active_connections),
        })

    def disconnect(self, user_id: str):
        """Remove conexão e libera slots bloqueados pelo utilizador."""
        self.active_connections.pop(user_id, None)

        # Libera todos os slots que estavam bloqueados por este utilizador
        slots_to_release = [
            key for key, val in self.locked_slots.items()
            if val.get("user_id") == user_id
        ]
        for slot_key in slots_to_release:
            del self.locked_slots[slot_key]

        return slots_to_release

    async def broadcast(self, message: dict, exclude_user: Optional[str] = None):
        """Envia mensagem para todos os utilizadores conectados."""
        disconnected = []
        for uid, ws in self.active_connections.items():
            if uid == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(uid)

        # Limpa conexões mortas
        for uid in disconnected:
            self.disconnect(uid)

    def lock_slot(self, slot_key: str, user_id: str, user_name: str) -> bool:
        """
        Tenta bloquear um slot (Estúdio + Horário + Data).
        Retorna True se conseguiu, False se já está bloqueado por outro utilizador.
        """
        existing = self.locked_slots.get(slot_key)
        if existing and existing["user_id"] != user_id:
            return False  # Slot já bloqueado por outro utilizador

        self.locked_slots[slot_key] = {
            "user_id": user_id,
            "user_name": user_name,
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }
        return True

    def release_slot(self, slot_key: str, user_id: str) -> bool:
        """Libera um slot. Retorna True se liberou, False se não era owner."""
        existing = self.locked_slots.get(slot_key)
        if not existing:
            return True
        if existing["user_id"] != user_id:
            return False

        del self.locked_slots[slot_key]
        return True

    def get_slot_key(self, estudio: str, horario: str, data: str) -> str:
        """Gera a chave única do slot: estudio:horario:data."""
        return f"{estudio}:{horario}:{data}"


# Singleton global
manager = ConnectionManager()
