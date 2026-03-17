from __future__ import annotations

from typing import Optional

from app.models.routine import Routine
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.routine import RoutineRead, TaskInRoutineRead
from sqlmodel import Session, select


def routine_to_read(routine: Routine, tasks: Optional[list[TaskInRoutineRead]] = None) -> RoutineRead:
    return RoutineRead(id=routine.id, name=routine.name, description=routine.description, tasks=tasks)


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
    routine = db.exec(select(Routine).where(Routine.user_id == user_id, Routine.id == routine_id)).first()
    if not routine:
        return None

    return routine_to_read(routine, load_routine_tasks(db, routine.id))


def load_user_routines_with_tasks(db: Session, user_id: int) -> list[RoutineRead]:
    routines = db.exec(select(Routine).where(Routine.user_id == user_id)).all()
    return [routine_to_read(routine, load_routine_tasks(db, routine.id)) for routine in routines]
