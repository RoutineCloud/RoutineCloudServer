from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.routine import Routine
from app.models.routine_runtime_state import RoutineRuntimeState, RuntimeStatus
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.models.user import User
from app.schemas.routine import RoutineCreate, RoutineRead, RoutineTaskAdd, RoutineUpdate, TaskInRoutineRead
from app.schemas.routine_control import ActiveRoutineStatusRead
from app.schemas.socketio import CommandType
from app.services.routine_command_service import CommandValidationError, routine_command_service
from app.socketio.state import build_runtime_payload

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


def _runtime_status(db: Session, user_id: int) -> ActiveRoutineStatusRead:
    runtime = db.exec(select(RoutineRuntimeState).where(RoutineRuntimeState.user_id == user_id)).first()
    if not runtime:
        return ActiveRoutineStatusRead(status="idle")

    routine_name: Optional[str] = None
    if runtime.active_routine_id is not None:
        routine = db.exec(
            select(Routine).where(Routine.id == runtime.active_routine_id, Routine.user_id == user_id)
        ).first()
        if routine:
            routine_name = routine.name

    runtime_payload = build_runtime_payload(runtime)
    return ActiveRoutineStatusRead(
        active_routine_id=runtime_payload.active_routine_id,
        routine_name=routine_name,
        status=runtime_payload.status.value,
        current_task_position=runtime_payload.current_task_position,
        started_at=runtime_payload.task_started_at,
    )


def _server_command_id(user_id: int, suffix: str) -> str:
    return f"server-{user_id}-{suffix}-{int(datetime.now(timezone.utc).timestamp())}"


async def _execute_runtime_command(
    db: Session,
    user_id: int,
    command_type: CommandType,
    actor_id: str,
    routine_id: Optional[int] = None,
) -> None:
    payload = {
        "command_id": _server_command_id(user_id, command_type.value),
        "type": command_type.value,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
    if routine_id is not None:
        payload["routine_id"] = routine_id

    await routine_command_service.execute(
        db=db,
        user_id=user_id,
        command=payload,
        actor={"type": "server", "id": actor_id},
    )


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
    return [_routine_to_read(r, None) for r in routines]


@router.get("/active/status", response_model=ActiveRoutineStatusRead, operation_id="routines_active_status")
async def active_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _runtime_status(db, current_user.id)


@router.post("/active/skip", status_code=status.HTTP_202_ACCEPTED, operation_id="routines_active_skip")
async def skip_active_task(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await _execute_runtime_command(
            db=db,
            user_id=current_user.id,
            command_type=CommandType.TASK_SKIP,
            actor_id="api:routines/active/skip",
        )
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc
    return {"status": "skipped"}


@router.post("/active/pause", status_code=status.HTTP_202_ACCEPTED, operation_id="routines_active_pause")
async def pause_active_routine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await _execute_runtime_command(
            db=db,
            user_id=current_user.id,
            command_type=CommandType.ROUTINE_PAUSE,
            actor_id="api:routines/active/pause",
        )
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc
    return {"status": "paused"}


@router.post("/active/resume", status_code=status.HTTP_202_ACCEPTED, operation_id="routines_active_resume")
async def resume_active_routine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await _execute_runtime_command(
            db=db,
            user_id=current_user.id,
            command_type=CommandType.ROUTINE_RESUME,
            actor_id="api:routines/active/resume",
        )
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc
    return {"status": "running"}


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

    runtime = db.exec(select(RoutineRuntimeState).where(RoutineRuntimeState.user_id == current_user.id)).first()
    if runtime and runtime.active_routine_id == r.id:
        runtime.active_routine_id = None
        runtime.status = RuntimeStatus.IDLE
        runtime.current_task_position = None
        runtime.task_started_at = None
        db.add(runtime)

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
    if t.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this task")

    if payload.position is None:
        last = db.exec(
            select(RoutineTask)
            .where(RoutineTask.routine_id == r.id)
            .order_by(RoutineTask.position.desc())
        ).first()
        position = (last.position + 1) if last else 1
    else:
        position = max(1, payload.position)
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

    db.query(RoutineTask).filter(
        RoutineTask.routine_id == r.id, RoutineTask.position > removed_pos
    ).update({RoutineTask.position: RoutineTask.position - 1})
    db.commit()

    return _load_routine_tasks(db, r.id)


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

    try:
        await _execute_runtime_command(
            db=db,
            user_id=current_user.id,
            command_type=CommandType.ROUTINE_START,
            actor_id="api:routines/start",
            routine_id=routine_id,
        )
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc

    return {"status": "started"}




