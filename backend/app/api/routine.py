from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.routine import Routine as SARoutine
from app.models.task import Task as SATask
from app.models.routine_task import RoutineTask as SARoutineTask
from app.models.user import User as SAUser
from app.schemas.routine import RoutineCreate, RoutineRead, TaskInRoutineRead, RoutineTaskAdd


router = APIRouter(
    prefix="/api/routines",
    tags=["routines"],
)


def _routine_to_read(r: SARoutine, tasks: Optional[List[TaskInRoutineRead]] = None) -> RoutineRead:
    return RoutineRead(id=r.id, name=r.name, description=r.description, tasks=tasks)


def _load_routine_tasks(db: Session, routine_id: int) -> List[TaskInRoutineRead]:
    stmt = (
        select(SATask, SARoutineTask.position)
        .join(SARoutineTask, SARoutineTask.task_id == SATask.id)
        .where(SARoutineTask.routine_id == routine_id)
        .order_by(SARoutineTask.position.asc())
    )
    rows = db.exec(stmt).all()
    result: List[TaskInRoutineRead] = []
    for task, position in rows:
        result.append(
            TaskInRoutineRead(
                id=task.id,
                name=task.name,
                icon_name=task.icon_name,
                sound=task.sound,
                duration=task.duration,
                position=position,
            )
        )
    return result


@router.post("/", response_model=RoutineRead, status_code=status.HTTP_201_CREATED)
async def create_routine(
    payload: RoutineCreate,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    r = SARoutine(name=payload.name, description=payload.description, user_id=current_user.id)
    db.add(r)
    db.commit()
    db.refresh(r)
    return _routine_to_read(r, [])


@router.get("/", response_model=List[RoutineRead])
async def list_routines(
    include_tasks: bool = Query(False, description="Include tasks for each routine"),
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    routines = db.exec(select(SARoutine).where(SARoutine.user_id == current_user.id)).all()
    if include_tasks:
        return [_routine_to_read(r, _load_routine_tasks(db, r.id)) for r in routines]
    else:
        return [_routine_to_read(r, None) for r in routines]


@router.get("/{routine_id}", response_model=RoutineRead)
async def get_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    r: Optional[SARoutine] = db.exec(
        select(SARoutine).where(SARoutine.id == routine_id, SARoutine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    tasks = _load_routine_tasks(db, r.id)
    return _routine_to_read(r, tasks)


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    r: Optional[SARoutine] = db.exec(
        select(SARoutine).where(SARoutine.id == routine_id, SARoutine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    db.delete(r)
    db.commit()
    return None


@router.get("/{routine_id}/tasks", response_model=List[TaskInRoutineRead])
async def list_routine_tasks(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    r: Optional[SARoutine] = db.exec(
        select(SARoutine).where(SARoutine.id == routine_id, SARoutine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    return _load_routine_tasks(db, routine_id)


@router.post("/{routine_id}/tasks", response_model=List[TaskInRoutineRead], status_code=status.HTTP_201_CREATED)
async def add_task_to_routine(
    routine_id: int,
    payload: RoutineTaskAdd,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    r: Optional[SARoutine] = db.exec(
        select(SARoutine).where(SARoutine.id == routine_id, SARoutine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    t: Optional[SATask] = db.get(SATask, payload.task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    # Prevent duplicates
    exists = db.exec(
        select(SARoutineTask).where(SARoutineTask.routine_id == r.id, SARoutineTask.task_id == payload.task_id)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Task already in routine")

    # Determine position
    if payload.position is None:
        last = db.exec(
            select(SARoutineTask)
            .where(SARoutineTask.routine_id == r.id)
            .order_by(SARoutineTask.position.desc())
        ).first()
        position = (last.position + 1) if last else 1
    else:
        position = max(1, payload.position)
        # Shift tasks at or after this position
        to_shift = db.exec(
            select(SARoutineTask).where(
                SARoutineTask.routine_id == r.id,
                SARoutineTask.position >= position,
            ).order_by(SARoutineTask.position.desc())
        ).all()
        for rt in to_shift:
            rt.position += 1
        db.commit()

    link = SARoutineTask(routine_id=r.id, task_id=payload.task_id, position=position)
    db.add(link)
    db.commit()

    return _load_routine_tasks(db, r.id)


@router.delete("/{routine_id}/tasks/{task_id}", response_model=List[TaskInRoutineRead])
async def remove_task_from_routine(
    routine_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    r: Optional[SARoutine] = db.exec(
        select(SARoutine).where(SARoutine.id == routine_id, SARoutine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    link: Optional[SARoutineTask] = db.exec(
        select(SARoutineTask).where(SARoutineTask.routine_id == r.id, SARoutineTask.task_id == task_id)
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Task not in routine")

    removed_pos = link.position
    db.delete(link)
    db.commit()

    # Shift positions down for tasks after the removed one
    db.query(SARoutineTask).filter(
        SARoutineTask.routine_id == r.id, SARoutineTask.position > removed_pos
    ).update({SARoutineTask.position: SARoutineTask.position - 1})
    db.commit()

    return _load_routine_tasks(db, r.id)
