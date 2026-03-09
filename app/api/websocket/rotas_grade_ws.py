"""
Canal Educação v3.0 — WebSocket Routes para Grade Horária.
Canal de tempo real para atualização da grade e slot-locking.
"""

import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.websocket.connection_manager import manager
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

router = APIRouter()


@router.websocket("/ws/grade")
async def websocket_grade(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Canal WebSocket para atualizações em tempo real da grade horária.
    O frontend conecta com: ws://host/ws/grade?token=JWT_TOKEN

    Mensagens suportadas (client → server):
      - LOCK_SLOT: {"action": "LOCK_SLOT", "estudio": "...", "horario": "...", "data": "..."}
      - RELEASE_SLOT: {"action": "RELEASE_SLOT", "estudio": "...", "horario": "...", "data": "..."}
      - GRADE_UPDATE: {"action": "GRADE_UPDATE", "data": {...}}

    Mensagens emitidas (server → clients):
      - INITIAL_STATE, USER_CONNECTED, USER_DISCONNECTED
      - SLOT_LOCKED, SLOT_RELEASED, SLOT_LOCK_DENIED
      - GRADE_UPDATED
    """
    # Autenticação via token na query string
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Token inválido ou expirado")
        return

    user_email = payload.get("sub")
    user_id = payload.get("user_id", user_email)
    user_name = user_email  # Simplificado; poderia buscar full_name do DB

    await manager.connect(websocket, user_id, user_name)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "JSON inválido.",
                })
                continue

            action = data.get("action")

            if action == "LOCK_SLOT":
                slot_key = manager.get_slot_key(
                    data.get("estudio", ""),
                    data.get("horario", ""),
                    data.get("data", ""),
                )
                success = manager.lock_slot(slot_key, user_id, user_name)

                if success:
                    await manager.broadcast({
                        "type": "SLOT_LOCKED",
                        "slot_key": slot_key,
                        "user_id": user_id,
                        "user_name": user_name,
                        "estudio": data.get("estudio"),
                        "horario": data.get("horario"),
                        "data": data.get("data"),
                    })
                else:
                    locker = manager.locked_slots.get(slot_key, {})
                    await websocket.send_json({
                        "type": "SLOT_LOCK_DENIED",
                        "slot_key": slot_key,
                        "locked_by": locker.get("user_name", "desconhecido"),
                        "message": f"Slot bloqueado por {locker.get('user_name', '?')}.",
                    })

            elif action == "RELEASE_SLOT":
                slot_key = manager.get_slot_key(
                    data.get("estudio", ""),
                    data.get("horario", ""),
                    data.get("data", ""),
                )
                manager.release_slot(slot_key, user_id)
                await manager.broadcast({
                    "type": "SLOT_RELEASED",
                    "slot_key": slot_key,
                    "user_id": user_id,
                })

            elif action == "GRADE_UPDATE":
                # Broadcast de atualização da grade para todos
                await manager.broadcast(
                    {
                        "type": "GRADE_UPDATED",
                        "updated_by": user_name,
                        "payload": data.get("payload", {}),
                    },
                    exclude_user=user_id,
                )

            else:
                await websocket.send_json({
                    "type": "ERROR",
                    "message": f"Ação desconhecida: {action}",
                })

    except WebSocketDisconnect:
        released_slots = manager.disconnect(user_id)
        await manager.broadcast({
            "type": "USER_DISCONNECTED",
            "user_id": user_id,
            "user_name": user_name,
            "released_slots": released_slots,
            "connected_users": len(manager.active_connections),
        })
