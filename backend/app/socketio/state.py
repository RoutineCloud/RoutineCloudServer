from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models.device import Device
from app.models.routine_runtime_state import RoutineRuntimeState, RoutineRuntimeStateParticipant
from app.schemas.routine import RoutineRead
from app.schemas.socketio import SocketDevicePayload, SocketRuntimePayload, SocketSnapshotPayload
from app.services.routine_payloads import load_user_routine_with_tasks, load_user_routines_with_tasks


def get_runtime_state_for_user(db: Session, user_id: int) -> Optional[RoutineRuntimeState]:
    participant = db.exec(
        select(RoutineRuntimeStateParticipant).where(RoutineRuntimeStateParticipant.user_id == user_id)
    ).first()
    return participant.runtime_state if participant else None


def get_or_create_runtime_state(db: Session, user_id: int) -> RoutineRuntimeState:
    runtime = get_runtime_state_for_user(db, user_id)
    if runtime:
        return runtime

    runtime = RoutineRuntimeState()
    db.add(runtime)
    db.commit()
    db.refresh(runtime)

    participant = RoutineRuntimeStateParticipant(runtime_state_id=runtime.id, user_id=user_id)
    db.add(participant)
    db.commit()
    db.refresh(runtime)
    return runtime


def build_runtime_payload(runtime: RoutineRuntimeState) -> SocketRuntimePayload:
    user_ids = [p.user_id for p in (runtime.participants or [])]
    return SocketRuntimePayload(
        user_ids=user_ids,
        active_routine_id=runtime.active_routine_id,
        status=runtime.status,
        current_task_position=runtime.current_task_position,
        task_started_at=runtime.task_started_at,
        routine_started_at=runtime.routine_started_at,
        paused_at=runtime.paused_at,
        pause_duration=runtime.pause_duration,
        updated_at=runtime.updated_at,
    )


def _device_to_payload(device: Device) -> SocketDevicePayload:
    return SocketDevicePayload(
        id=device.id,
        device_id=device.device_id,
        name=device.name,
        type=device.type,
        status=device.status.value,
        is_active=device.is_active,
    )


def routine_read_with_tasks(db: Session, user_id: int, routine_id: int) -> Optional[RoutineRead]:
    return load_user_routine_with_tasks(db, user_id, routine_id)


def build_state_payload(
    db: Session,
    user_id: int,
    runtime: Optional[RoutineRuntimeState] = None,
) -> SocketSnapshotPayload:
    current_runtime = runtime or get_or_create_runtime_state(db, user_id)
    if current_runtime.recalculate():
        db.add(current_runtime)
        db.commit()
        db.refresh(current_runtime)
    routine_payloads = load_user_routines_with_tasks(db, user_id)

    devices = db.exec(select(Device).where(Device.owner_id == user_id)).all()
    device_payloads = [_device_to_payload(device) for device in devices]

    return SocketSnapshotPayload(
        runtime=build_runtime_payload(current_runtime),
        routines=routine_payloads,
        devices=device_payloads,
        server_time=datetime.utcnow(),
    )
