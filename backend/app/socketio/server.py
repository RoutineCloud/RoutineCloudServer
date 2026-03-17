from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import ValidationError
from pydantic_socketio import FastAPISocketIO
from sqlmodel import Session, select

from app.db.session import engine
from app.models.device import Device, DeviceStatus
from app.schemas.socketio import (
    ClientCommandPayload,
    CommandRejectedPayload,
    HeartbeatPayload,
    SocketAuthPayload,
    SocketErrorPayload,
    SocketSnapshotPayload,
)
from app.services.routine_command_service import CommandValidationError, routine_command_service
from app.socketio.auth import SocketAuthError, authenticate_socket_client
from app.socketio.bus import socketio_bus
from app.socketio.state import build_state_payload

NAMESPACE = "/device"
HEARTBEAT_TIMEOUT_SECONDS = 90
HEARTBEAT_CHECK_INTERVAL_SECONDS = 15

logger = logging.getLogger(__name__)


sio = FastAPISocketIO()
socketio_bus.configure(sio, NAMESPACE)

# Keep explicit validation for the most important server events.
sio.register_emit("server.state.snapshot", payload_type=SocketSnapshotPayload)
sio.register_emit("server.command.rejected", payload_type=CommandRejectedPayload)
sio.register_emit("server.error", payload_type=SocketErrorPayload)


@dataclass
class SessionContext:
    user_id: int
    device_id: str
    last_heartbeat: datetime


_sid_context: dict[str, SessionContext] = {}
_heartbeat_task: asyncio.Task | None = None


def _utc_now() -> datetime:
    return datetime.utcnow()


def _parse_auth_payload(auth: SocketAuthPayload | dict[str, Any] | None) -> SocketAuthPayload:
    if auth is None:
        raise ConnectionRefusedError("unauthorized")

    try:
        return auth if isinstance(auth, SocketAuthPayload) else SocketAuthPayload.model_validate(auth)
    except ValidationError as exc:
        raise ConnectionRefusedError("invalid_payload") from exc


def _room_for_user(user_id: int) -> str:
    return f"user:{user_id}"


def _room_for_device(device_id: str) -> str:
    return f"device:{device_id}"


def _get_context(sid: str) -> SessionContext | None:
    return _sid_context.get(sid)


async def _emit_server_error(sid: str, code: str, message: str) -> None:
    await sio.emit(
        "server.error",
        SocketErrorPayload(code=code, message=message),
        to=sid,
        namespace=NAMESPACE,
    )


async def _emit_unknown_sid(sid: str) -> None:
    await _emit_server_error(sid, code="unknown_sid", message="Session not registered")


def _has_other_active_session(user_id: int, device_id: str, exclude_sid: str) -> bool:
    for session_sid, ctx in _sid_context.items():
        if session_sid == exclude_sid:
            continue
        if ctx.user_id == user_id and ctx.device_id == device_id:
            return True
    return False


async def _heartbeat_watchdog() -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_CHECK_INTERVAL_SECONDS)
        now = _utc_now()
        expired_sids = [
            sid
            for sid, ctx in _sid_context.items()
            if (now - ctx.last_heartbeat).total_seconds() > HEARTBEAT_TIMEOUT_SECONDS
        ]
        for sid in expired_sids:
            await sio.disconnect(sid, namespace=NAMESPACE)


def _ensure_watchdog() -> None:
    global _heartbeat_task
    if _heartbeat_task is None or _heartbeat_task.done():
        _heartbeat_task = sio.start_background_task(_heartbeat_watchdog)


@sio.event(namespace=NAMESPACE)
async def connect(
    sid: str,
    environ: dict[str, Any],
    auth: SocketAuthPayload | dict[str, Any] | None,
) -> bool:
    del environ
    auth_payload = _parse_auth_payload(auth)

    with Session(engine) as db:
        try:
            identity = authenticate_socket_client(
                db,
                auth_payload.access_token,
                auth_payload.device_id,
                id_token=auth_payload.id_token,
            )
        except SocketAuthError as exc:
            raise ConnectionRefusedError(exc.code) from exc

        identity.device.status = DeviceStatus.ONLINE
        db.add(identity.device)
        db.commit()

        _sid_context[sid] = SessionContext(
            user_id=identity.user.id,
            device_id=identity.device.device_id,
            last_heartbeat=_utc_now(),
        )

        await sio.enter_room(sid, _room_for_user(identity.user.id), namespace=NAMESPACE)
        await sio.enter_room(sid, _room_for_device(identity.device.device_id), namespace=NAMESPACE)

        snapshot = build_state_payload(db, identity.user.id)

    await sio.emit("server.state.snapshot", snapshot, to=sid, namespace=NAMESPACE)
    _ensure_watchdog()
    return True


@sio.event(namespace=NAMESPACE)
async def disconnect(sid: str) -> None:
    ctx = _sid_context.pop(sid, None)
    if not ctx:
        return

    if _has_other_active_session(ctx.user_id, ctx.device_id, sid):
        return

    with Session(engine) as db:
        device = db.exec(
            select(Device).where(
                Device.device_id == ctx.device_id,
                Device.owner_id == ctx.user_id,
            )
        ).first()
        if device:
            device.status = DeviceStatus.OFFLINE
            db.add(device)
            db.commit()


@sio.on("client.status.heartbeat", namespace=NAMESPACE)
async def handle_heartbeat(sid: str, data: HeartbeatPayload) -> None:
    del data
    ctx = _get_context(sid)
    if not ctx:
        return

    ctx.last_heartbeat = _utc_now()


@sio.on("client.state.request", namespace=NAMESPACE)
async def handle_state_request(sid: str, data: dict[str, Any] | None) -> None:
    del data
    ctx = _get_context(sid)
    if not ctx:
        await _emit_unknown_sid(sid)
        return

    with Session(engine) as db:
        snapshot = build_state_payload(db, ctx.user_id)

    await sio.emit("server.state.snapshot", snapshot, to=sid, namespace=NAMESPACE)


@sio.on("client.command", namespace=NAMESPACE)
async def handle_client_command(sid: str, data: ClientCommandPayload) -> None:
    ctx = _get_context(sid)
    if not ctx:
        await _emit_unknown_sid(sid)
        return

    with Session(engine) as db:
        try:
            await routine_command_service.execute(db, ctx.user_id, data, {"type": "device", "id": ctx.device_id})
        except CommandValidationError as exc:
            await sio.emit(
                "server.command.rejected",
                CommandRejectedPayload(command_id=data.command_id, reason=exc.reason),
                to=sid,
                namespace=NAMESPACE,
            )
        except Exception:
            logger.exception("Socket command execution failed", extra={"sid": sid, "user_id": ctx.user_id})
            await _emit_server_error(sid, code="command_failed", message="Command execution failed")


