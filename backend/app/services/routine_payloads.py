from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.models.routine import Routine
from app.models.routine_access import AccessLevel, RoutineAccess
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.routine import RoutineRead, TaskInRoutineRead


def routine_to_read(
    routine: Routine,
    tasks: Optional[list[TaskInRoutineRead]] = None,
    access_level: Optional[AccessLevel] = None,
) -> RoutineRead:
    return RoutineRead(
        id=routine.id,
        name=routine.name,
        description=routine.description,
        tasks=tasks,
        access_level=access_level,
    )


def task_in_routine_to_read(task: Task, position: int) -> TaskInRoutineRead:
    return TaskInRoutineRead(
        id=task.id,
        name=task.name,
        icon_name=task.icon_name,
        sound=task.sound,
        duration=task.duration,
        position=position,
    )


def load_routine_tasks(db: Session, routine_id: int) -> list[TaskInRoutineRead]:
    stmt = (
        select(Task, RoutineTask.position)
        .join(RoutineTask, RoutineTask.task_id == Task.id)
        .where(RoutineTask.routine_id == routine_id)
        .order_by(RoutineTask.position.asc())
    )
    rows = db.exec(stmt).all()
    return [task_in_routine_to_read(task, position) for task, position in rows]


def load_user_routine_with_tasks(db: Session, user_id: int, routine_id: int) -> Optional[RoutineRead]:
    row = db.exec(
        select(Routine, RoutineAccess.access_level)
        .join(RoutineAccess)
        .where(RoutineAccess.user_id == user_id, Routine.id == routine_id)
    ).first()
    if not row:
        return None

    routine, access_level = row
    return routine_to_read(routine, load_routine_tasks(db, routine.id), access_level=access_level)


def load_user_routines_with_tasks(db: Session, user_id: int) -> list[RoutineRead]:
    rows = db.exec(
        select(Routine, RoutineAccess.access_level)
        .join(RoutineAccess)
        .where(RoutineAccess.user_id == user_id)
    ).all()
    return [
        routine_to_read(routine, load_routine_tasks(db, routine.id), access_level=access_level)
        for routine, access_level in rows
    ]
