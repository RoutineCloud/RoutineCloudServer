from __future__ import annotations

import asyncio
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select
from sqlmodel import update

from app.core.security import validate_oidc_token
from app.db.session import get_db
from app.models.device import DeviceStatus, Device
from app.models.routine import Routine
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.models.user import User
from app.websocket.manager import ws_manager

router = APIRouter()


async def _get_user_and_device_id_from_token(token: Optional[str], db: Session) -> tuple[Optional[User], Optional[str]]:
    """
    Checks if the user and device from the token are valid and if the user owns the device
    If yes returns the user and device id
    """
    if not token:
        return None, None
    try:
        payload = validate_oidc_token(token)
    except Exception:
        return None, None
    
    sub = payload.get("sub")
    if not sub:
        return None, None
    
    user = db.exec(select(User).where(User.oidc_sub == sub)).first()
    if not user:
        return None, None
        
    client_id = payload.get("client_id")
    if not client_id:
        # Fallback or alternate claim for device ID if needed
        # For now keep it as it was
        return user, None

    # Check if the user owns the device
    dev = db.exec(select(Device).where(Device.device_id == client_id)).first()
    if not dev or dev.owner_id != user.id:
        # If client_id was provided but doesn't match, we still return user but no device_id
        # or we could return None, None. The old code returned None, None.
        return None, None
        
    return user, client_id


def _task_rows_for_routine(db: Session, routine_id: int) -> List[Dict[str, Any]]:
    rows = (
        db.exec(
            select(Task, RoutineTask.position)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(RoutineTask.routine_id == routine_id)
            .order_by(RoutineTask.position.asc())
        ).all()
    )
    items: List[Dict[str, Any]] = []
    for task, position in rows:
        items.append(
            {
                "id": task.id,
                "name": task.name,
                "icon_name": task.icon_name,
                "sound": task.sound,
                "duration": task.duration,
                "position": position,
            }
        )
    return items

def _set_device_status(db: Session, device_id: int, status: DeviceStatus) -> None:
    db.exec(
        update(Device).where(Device.id == device_id).values(status=status)
    ).scalar_one()


def _routines_snapshot(db: Session, user_id: int) -> List[Dict[str, Any]]:
    routines = db.exec(select(Routine).where(Routine.user_id == user_id)).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "tasks": _task_rows_for_routine(db, r.id),
        }
        for r in routines
    ]

"""
Protocoll of a session

1) User connect with auth
2) User sends status
3) Server sends snapshot of routines
4) User repeatedly sends status
5) Server can send messages to handel routines
"""

async def _recv_json_with_timeout(ws: WebSocket, timeout: float = 75.0):
    return await asyncio.wait_for(ws.receive_json(), timeout=timeout)

def upsert_device_status(db: Session, owner_id: int, device_id: str, status: DeviceStatus) -> None:
    dev = db.exec(select(Device).where(Device.device_id == device_id)).first()
    dev.status = status
    #dev.last_seen = datetime.now(timezone.utc)
    db.commit()


async def dumps_routines(user_id: int, ws: WebSocket, db: Session):
    """
    Load all routines with tasks from the db and send them to the websocket
    """
    message = {
        "type": "command",
        "command": "routines_snapshot",
        "data": _routines_snapshot(db, user_id),
    }
    await ws.send_json(message)


@router.websocket("/ws/routines")
async def routines_websocket_endpoint(websocket: WebSocket):
    # Extract token from query (?token=...) or Authorization header: Bearer <token>
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("Authorization") or websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1]

    # Open DB session manually (can't use Depends directly in WS handler)
    db: Session = next(get_db())
    try:
        user, device_id = await _get_user_and_device_id_from_token(token, db)
        if not user:
            await websocket.accept()
            await websocket.close(code=1008)  # policy violation / unauthorized
            return

        await ws_manager.connect(user.id, websocket)
        upsert_device_status(db, user.id, device_id, DeviceStatus.ONLINE)
        await dumps_routines(user.id, websocket, db)

        try:
            while True:
                try:
                    msg = await _recv_json_with_timeout(websocket, timeout=120)
                except asyncio.TimeoutError:
                    # Kein Status → Gerät auf OFFLINE und Verbindung schließen
                    upsert_device_status(db, user.id, device_id, DeviceStatus.OFFLINE)
                    break

                if msg.get("type") == "status":
                    upsert_device_status(db, user.id, device_id, DeviceStatus.ONLINE)
        except WebSocketDisconnect:
            pass
        finally:
            upsert_device_status(db, user.id, device_id, DeviceStatus.OFFLINE)
            await ws_manager.disconnect(user.id, websocket)
    finally:
        db.close()
