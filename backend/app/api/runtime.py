from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.runtime import (
    RuntimeActiveRead,
    RuntimeCommandAccepted,
    RuntimeCommandRequest,
    RuntimeCommandType,
    RuntimeEventEnvelope,
    RuntimeSyncRead,
)
from app.services.routine_command_service import CommandValidationError, routine_command_service
from app.services.runtime_event_bus import runtime_event_bus
from app.services.runtime_state import (
    build_runtime_active_read,
    build_runtime_sync_read,
    get_or_create_runtime_state,
    refresh_runtime_state,
)

router = APIRouter(prefix="/runtime", tags=["runtime"])


def _server_command_id(user_id: int, command_type: RuntimeCommandType) -> str:
    return f"server-{user_id}-{command_type.value}-{int(datetime.utcnow().timestamp())}"


def _normalize_command(
    payload: RuntimeCommandRequest,
    expected_type: RuntimeCommandType,
    user_id: int,
) -> RuntimeCommandRequest:
    if payload.type != expected_type:
        raise HTTPException(status_code=400, detail="invalid_command_type")
    if not payload.command_id:
        payload.command_id = _server_command_id(user_id, expected_type)
    if payload.requested_at is None:
        payload.requested_at = datetime.utcnow()
    return payload


@router.get("/active", response_model=RuntimeActiveRead, operation_id="runtime_active")
async def active_runtime(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runtime = refresh_runtime_state(db, get_or_create_runtime_state(db, current_user.id))
    return build_runtime_active_read(db, runtime)


@router.get("/sync", response_model=RuntimeSyncRead, operation_id="runtime_sync")
async def sync_runtime(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runtime = refresh_runtime_state(db, get_or_create_runtime_state(db, current_user.id))
    return build_runtime_sync_read(db, runtime)


async def _execute_command(
    payload: RuntimeCommandRequest,
    expected_type: RuntimeCommandType,
    db: Session,
    current_user: User,
) -> RuntimeCommandAccepted:
    normalized = _normalize_command(payload, expected_type, current_user.id)
    try:
        return (
            await routine_command_service.execute(
                db=db,
                user_id=current_user.id,
                command=normalized,
                actor={"type": "server", "id": f"api:runtime/{expected_type.value}"},
            )
        ).accepted
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc


@router.post("/start", response_model=RuntimeCommandAccepted, operation_id="runtime_start")
async def start_runtime(
    payload: RuntimeCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _execute_command(payload, RuntimeCommandType.ROUTINE_START, db, current_user)


@router.post("/pause", response_model=RuntimeCommandAccepted, operation_id="runtime_pause")
async def pause_runtime(
    payload: RuntimeCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _execute_command(payload, RuntimeCommandType.ROUTINE_PAUSE, db, current_user)


@router.post("/resume", response_model=RuntimeCommandAccepted, operation_id="runtime_resume")
async def resume_runtime(
    payload: RuntimeCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _execute_command(payload, RuntimeCommandType.ROUTINE_RESUME, db, current_user)


@router.post("/skip", response_model=RuntimeCommandAccepted, operation_id="runtime_skip")
async def skip_runtime(
    payload: RuntimeCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _execute_command(payload, RuntimeCommandType.ROUTINE_SKIP, db, current_user)


@router.post("/stop", response_model=RuntimeCommandAccepted, operation_id="runtime_stop")
async def stop_runtime(
    payload: RuntimeCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _execute_command(payload, RuntimeCommandType.ROUTINE_STOP, db, current_user)


@router.post("/complete", response_model=RuntimeCommandAccepted, operation_id="runtime_complete")
async def complete_runtime(
    payload: RuntimeCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _execute_command(payload, RuntimeCommandType.ROUTINE_COMPLETE, db, current_user)


@router.get(
    "/events",
    response_model=RuntimeEventEnvelope,
    response_class=StreamingResponse,
    operation_id="runtime_events",
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def stream_runtime_events(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    async def event_stream():
        async with runtime_event_bus.subscribe(current_user.id) as queue:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue

                data = json.dumps(event.model_dump(mode="json"))
                yield f"id: {event.event_id}\n"
                yield f"event: {event.event_type.value}\n"
                yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
