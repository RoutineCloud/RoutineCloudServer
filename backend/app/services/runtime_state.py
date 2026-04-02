from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.routine import Routine
from app.models.routine_runtime_state import RoutineRuntimeState, RoutineRuntimeStateParticipant
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.routine import TaskInRoutineRead
from app.schemas.runtime import (
    RuntimeActiveRead,
    RuntimeRoutineRead,
    RuntimeStateRead,
    RuntimeSyncRead,
)


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

    db.add(RoutineRuntimeStateParticipant(runtime_state_id=runtime.id, user_id=user_id))
    db.commit()
    db.refresh(runtime)
    return runtime


def refresh_runtime_state(db: Session, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
    if runtime.recalculate():
        db.add(runtime)
        db.commit()
        db.refresh(runtime)
    return runtime


def _task_to_read(task: Task, position: int) -> TaskInRoutineRead:
    return TaskInRoutineRead(
        id=task.id,
        name=task.name,
        icon_name=task.icon_name,
        sound=task.sound,
        duration=task.duration,
        position=position,
    )


def load_runtime_routine(db: Session, routine_id: int) -> Optional[RuntimeRoutineRead]:
    routine = db.get(Routine, routine_id)
    if not routine:
        return None

    rows = db.exec(
        select(Task, RoutineTask.position)
        .join(RoutineTask, RoutineTask.task_id == Task.id)
        .where(RoutineTask.routine_id == routine_id)
        .order_by(RoutineTask.position.asc())
    ).all()
    tasks = [_task_to_read(task, position) for task, position in rows]
    return RuntimeRoutineRead(
        id=routine.id,
        name=routine.name,
        description=routine.description,
        tasks=tasks,
    )


def _current_task_id(db: Session, runtime: RoutineRuntimeState) -> Optional[int]:
    if runtime.active_routine_id is None or runtime.current_task_position is None:
        return None

    return db.exec(
        select(Task.id)
        .join(RoutineTask, RoutineTask.task_id == Task.id)
        .where(
            RoutineTask.routine_id == runtime.active_routine_id,
            RoutineTask.position == runtime.current_task_position,
        )
    ).first()


def build_runtime_state_read(db: Session, runtime: RoutineRuntimeState) -> RuntimeStateRead:
    participant_user_ids = [participant.user_id for participant in (runtime.participants or [])]
    return RuntimeStateRead(
        status=runtime.status,
        routine_id=runtime.active_routine_id,
        participant_user_ids=participant_user_ids,
        current_task_id=_current_task_id(db, runtime),
        current_task_position=runtime.current_task_position,
        task_started_at=runtime.task_started_at,
        routine_started_at=runtime.routine_started_at,
        paused_at=runtime.paused_at,
        pause_duration=runtime.pause_duration,
    )


def build_runtime_sync_read(
    db: Session,
    runtime: RoutineRuntimeState,
    *,
    server_time: Optional[datetime] = None,
) -> RuntimeSyncRead:
    return RuntimeSyncRead(
        server_time=server_time or datetime.now(timezone.utc),
        runtime=build_runtime_state_read(db, runtime),
    )


def build_runtime_active_read(
    db: Session,
    runtime: RoutineRuntimeState,
    *,
    server_time: Optional[datetime] = None,
) -> RuntimeActiveRead:
    state = build_runtime_state_read(db, runtime)
    routine = load_runtime_routine(db, state.routine_id) if state.routine_id is not None else None
    return RuntimeActiveRead(
        server_time=server_time or datetime.now(timezone.utc),
        runtime=state,
        routine=routine,
    )
