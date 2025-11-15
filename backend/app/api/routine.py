from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.routine import Routine
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.models.user import User
from app.schemas.routine import RoutineCreate, RoutineRead, TaskInRoutineRead, RoutineTaskAdd, RoutineUpdate

router = APIRouter(
    prefix="/api/routines",
    tags=["routines"],
)


def _routine_to_read(r: Routine, tasks: Optional[List[TaskInRoutineRead]] = None) -> RoutineRead:
    return RoutineRead(id=r.id, name=r.name, description=r.description, tasks=tasks)


def _load_routine_tasks(db: Session, routine_id: int) -> List[TaskInRoutineRead]:
    stmt = (
        select(Task, RoutineTask.position)
        .join(RoutineTask, RoutineTask.task_id == Task.id)
        .where(RoutineTask.routine_id == routine_id)
        .order_by(RoutineTask.position.asc())
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


@router.post("/", response_model=RoutineRead, status_code=status.HTTP_201_CREATED, operation_id="routines_create")
async def create_routine(
    payload: RoutineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = Routine(name=payload.name, description=payload.description, user_id=current_user.id)
    db.add(r)
    db.commit()
    db.refresh(r)
    return _routine_to_read(r, [])


@router.get("/", response_model=List[RoutineRead], operation_id="routines_list")
async def list_routines(
    include_tasks: bool = Query(False, description="Include tasks for each routine"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    routines = db.exec(select(Routine).where(Routine.user_id == current_user.id)).all()
    if include_tasks:
        return [_routine_to_read(r, _load_routine_tasks(db, r.id)) for r in routines]
    else:
        return [_routine_to_read(r, None) for r in routines]


@router.get("/{routine_id}", response_model=RoutineRead, operation_id="routines_get")
async def get_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    tasks = _load_routine_tasks(db, r.id)
    return _routine_to_read(r, tasks)


@router.patch("/{routine_id}", response_model=RoutineRead, operation_id="routines_update")
async def update_routine(
    routine_id: int,
    payload: RoutineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    if payload.name is not None:
        r.name = payload.name
    if payload.description is not None:
        r.description = payload.description

    db.add(r)
    db.commit()
    db.refresh(r)

    tasks = _load_routine_tasks(db, r.id)
    return _routine_to_read(r, tasks)


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="routines_delete")
async def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    db.delete(r)
    db.commit()
    return None


@router.get("/{routine_id}/tasks", response_model=List[TaskInRoutineRead], operation_id="routines_tasks_list")
async def list_routine_tasks(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    return _load_routine_tasks(db, routine_id)


@router.post("/{routine_id}/tasks", response_model=List[TaskInRoutineRead], status_code=status.HTTP_201_CREATED, operation_id="routines_tasks_add")
async def add_task_to_routine(
    routine_id: int,
    payload: RoutineTaskAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    t: Optional[Task] = db.get(Task, payload.task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    # Ownership check: only allow adding a task owned by the current user
    if t.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this task")


    # Determine position
    if payload.position is None:
        last = db.exec(
            select(RoutineTask)
            .where(RoutineTask.routine_id == r.id)
            .order_by(RoutineTask.position.desc())
        ).first()
        position = (last.position + 1) if last else 1
    else:
        position = max(1, payload.position)
        # Shift tasks at or after this position
        to_shift = db.exec(
            select(RoutineTask).where(
                RoutineTask.routine_id == r.id,
                RoutineTask.position >= position,
            ).order_by(RoutineTask.position.desc())
        ).all()
        for rt in to_shift:
            rt.position += 1
        db.commit()

    link = RoutineTask(routine_id=r.id, task_id=payload.task_id, position=position)
    db.add(link)
    db.commit()

    return _load_routine_tasks(db, r.id)


@router.delete("/{routine_id}/tasks/{position}", response_model=List[TaskInRoutineRead], operation_id="routines_tasks_remove")
async def remove_task_from_routine(
    routine_id: int,
    position: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    link: Optional[RoutineTask] = db.exec(
        select(RoutineTask).where(RoutineTask.routine_id == r.id, RoutineTask.position == position)
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="No task found at this position")

    removed_pos = link.position
    db.delete(link)
    db.commit()

    # Shift positions down for tasks after the removed one
    db.query(RoutineTask).filter(
        RoutineTask.routine_id == r.id, RoutineTask.position > removed_pos
    ).update({RoutineTask.position: RoutineTask.position - 1})
    db.commit()

    return _load_routine_tasks(db, r.id)


# --- WebSocket-triggered routine control endpoints ---
from app.websocket.manager import ws_manager  # type: ignore

@router.post("/{routine_id}/start", status_code=status.HTTP_202_ACCEPTED, operation_id="routines_start")
async def start_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    # Push event to all of this user's connections
    await ws_manager.push_routine_event(current_user.id, routine_id, "start_routine")
    return {"status": "started"}


@router.post("/{routine_id}/end", status_code=status.HTTP_202_ACCEPTED, operation_id="routines_end")
async def end_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")
    await ws_manager.push_routine_event(current_user.id, routine_id, "stop_routine")
    return {"status": "ended"}
