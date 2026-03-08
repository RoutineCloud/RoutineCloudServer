from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.models.device import Device
from app.models.routine import Routine
from app.models.routine_runtime_state import RoutineRuntimeState
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.routine import RoutineRead, TaskInRoutineRead
from app.schemas.socketio import SocketDevicePayload, SocketRuntimePayload, SocketSnapshotPayload
from sqlmodel import Session, select


def get_or_create_runtime_state(db: Session, user_id: int) -> RoutineRuntimeState:
    runtime = db.exec(select(RoutineRuntimeState).where(RoutineRuntimeState.user_id == user_id)).first()
    if runtime:
        return runtime

    runtime = RoutineRuntimeState(user_id=user_id)
    db.add(runtime)
    db.commit()
    db.refresh(runtime)
    return runtime


def build_runtime_payload(runtime: RoutineRuntimeState) -> SocketRuntimePayload:
    return SocketRuntimePayload.model_validate(runtime, from_attributes=True)


def _load_routine_tasks(db: Session, routine_id: int) -> list[TaskInRoutineRead]:
    rows = (
        db.exec(
            select(Task, RoutineTask.position)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(RoutineTask.routine_id == routine_id)
            .order_by(RoutineTask.position.asc())
        ).all()
    )
    tasks: list[TaskInRoutineRead] = []
    for task, position in rows:
        task_payload = TaskInRoutineRead.model_validate(task, from_attributes=True)
        tasks.append(task_payload.model_copy(update={"position": position}))
    return tasks


def routine_read_with_tasks(db: Session, user_id: int, routine_id: int) -> Optional[RoutineRead]:
    routine = db.exec(select(Routine).where(Routine.user_id == user_id, Routine.id == routine_id)).first()
    if not routine:
        return None

    routine_payload = RoutineRead.model_validate(routine, from_attributes=True)
    return routine_payload.model_copy(update={"tasks": _load_routine_tasks(db, routine.id)})


def build_state_payload(
    db: Session,
    user_id: int,
    runtime: Optional[RoutineRuntimeState] = None,
) -> SocketSnapshotPayload:
    current_runtime = runtime or get_or_create_runtime_state(db, user_id)

    routines = db.exec(select(Routine).where(Routine.user_id == user_id)).all()
    routine_payloads: list[RoutineRead] = []
    for routine in routines:
        payload = RoutineRead.model_validate(routine, from_attributes=True)
        routine_payloads.append(payload.model_copy(update={"tasks": _load_routine_tasks(db, routine.id)}))

    devices = db.exec(select(Device).where(Device.owner_id == user_id)).all()
    device_payloads = [SocketDevicePayload.model_validate(device, from_attributes=True) for device in devices]

    return SocketSnapshotPayload(
        runtime=build_runtime_payload(current_runtime),
        routines=routine_payloads,
        devices=device_payloads,
        server_time=datetime.now(timezone.utc),
    )
