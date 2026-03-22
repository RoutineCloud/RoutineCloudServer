from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.friendship import Friendship, FriendshipStatus
from app.models.routine import Routine
from app.models.routine_access import AccessLevel, RoutineAccess
from app.models.routine_runtime_state import RuntimeStatus
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.models.user import User
from app.schemas.routine import (
    RoutineCreate,
    RoutineRead,
    RoutineShareCreate,
    RoutineShareRead,
    RoutineShareUpdate,
    RoutineTaskAdd,
    RoutineUpdate,
    TaskInRoutineRead,
)
from app.schemas.routine_control import ActiveRoutineStatusRead
from app.schemas.socketio import CommandType
from app.services.routine_command_service import CommandValidationError, routine_command_service
from app.services.routine_payloads import load_routine_tasks as _load_routine_tasks
from app.services.routine_payloads import routine_to_read as _routine_to_read
from app.socketio.state import build_runtime_payload, get_runtime_state_for_user

router = APIRouter(
    prefix="/api/routines",
    tags=["routines"],
)

def _runtime_status(db: Session, user_id: int) -> ActiveRoutineStatusRead:
    runtime = get_runtime_state_for_user(db, user_id)
    if not runtime:
        return ActiveRoutineStatusRead(status="idle")
    if runtime.recalculate():
        db.add(runtime)
        db.commit()
        db.refresh(runtime)

    routine_name: Optional[str] = None
    if runtime.active_routine_id is not None:
        routine = db.exec(
            select(Routine)
            .join(RoutineAccess)
            .where(Routine.id == runtime.active_routine_id, RoutineAccess.user_id == user_id)
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
        paused_at=runtime_payload.paused_at,
        pause_duration=runtime_payload.pause_duration,
    )


def _server_command_id(user_id: int, suffix: str) -> str:
    return f"server-{user_id}-{suffix}-{int(datetime.utcnow().timestamp())}"


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
        "requested_at": datetime.utcnow().isoformat(),
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
    r = Routine(name=payload.name, description=payload.description)
    db.add(r)
    db.flush()
    
    access = RoutineAccess(user_id=current_user.id, routine_id=r.id, access_level=AccessLevel.OWNER)
    db.add(access)
    
    db.commit()
    db.refresh(r)
    return _routine_to_read(r, [], access=access)


@router.get("/", response_model=List[RoutineRead], operation_id="routines_list")
async def list_routines(
    include_tasks: bool = Query(False, description="Include tasks for each routine"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get all routines where the user has any access
    rows = db.exec(
        select(Routine, RoutineAccess)
        .join(RoutineAccess)
        .where(RoutineAccess.user_id == current_user.id)
    ).all()
    if include_tasks:
        return [
            _routine_to_read(
                r,
                _load_routine_tasks(db, r.id),
                access=acc
            )
            for r, acc in rows
        ]
    return [
        _routine_to_read(
            r,
            None,
            access=acc
        )
        for r, acc in rows
    ]


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
    row = db.exec(
        select(Routine, RoutineAccess)
        .join(RoutineAccess)
        .where(Routine.id == routine_id, RoutineAccess.user_id == current_user.id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Routine not found")
    
    r, acc = row
    tasks = _load_routine_tasks(db, r.id)
    return _routine_to_read(
        r,
        tasks,
        access=acc
    )


@router.patch("/{routine_id}", response_model=RoutineRead, operation_id="routines_update")
async def update_routine(
    routine_id: int,
    payload: RoutineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.exec(
        select(Routine, RoutineAccess)
        .join(RoutineAccess)
        .where(
            Routine.id == routine_id,
            RoutineAccess.user_id == current_user.id
        )
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Routine not found or insufficient permissions")

    r, acc = row

    # If updating core fields (name, description), must be OWNER
    if payload.name is not None or payload.description is not None:
        if acc.access_level != AccessLevel.OWNER:
            raise HTTPException(status_code=403, detail="Only the owner can update routine name or description")
        
        if payload.name is not None:
            r.name = payload.name
        if payload.description is not None:
            r.description = payload.description
        db.add(r)

    # Anyone with access can update their own preferences
    if payload.start_mode is not None:
        acc.start_mode = payload.start_mode
    if payload.notify_mask is not None:
        # Validate notify_mask (max 31 for flags 1, 2, 4, 8, 16)
        if not (0 <= payload.notify_mask <= 31):
             raise HTTPException(status_code=400, detail="Invalid notify_mask (must be 0-31)")
        acc.notify_mask = payload.notify_mask
    
    db.add(acc)
    db.commit()
    db.refresh(r)
    db.refresh(acc)

    tasks = _load_routine_tasks(db, r.id)
    return _routine_to_read(
        r,
        tasks,
        access=acc
    )


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="routines_delete")
async def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r: Optional[Routine] = db.exec(
        select(Routine)
        .join(RoutineAccess)
        .where(
            Routine.id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found or insufficient permissions")

    runtime = get_runtime_state_for_user(db, current_user.id)
    if runtime and runtime.active_routine_id == r.id:
        runtime.active_routine_id = None
        runtime.status = RuntimeStatus.IDLE
        runtime.current_task_position = None
        runtime.task_started_at = None
        runtime.routine_started_at = None
        runtime.paused_at = None
        runtime.pause_duration = 0
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
        select(Routine)
        .join(RoutineAccess)
        .where(Routine.id == routine_id, RoutineAccess.user_id == current_user.id)
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
        select(Routine)
        .join(RoutineAccess)
        .where(
            Routine.id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found or insufficient permissions")

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
        select(Routine)
        .join(RoutineAccess)
        .where(
            Routine.id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Routine not found or insufficient permissions")

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
        select(Routine)
        .join(RoutineAccess)
        .where(Routine.id == routine_id, RoutineAccess.user_id == current_user.id)
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


@router.post("/{routine_id}/shares", response_model=RoutineShareRead, status_code=status.HTTP_201_CREATED, operation_id="routines_shares_create")
async def create_routine_share(
    routine_id: int,
    payload: RoutineShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only owner can manage shares
    owner_access = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not owner_access:
        raise HTTPException(status_code=403, detail="Only the owner can manage shares")

    # Target user must be a confirmed friend
    friendship = db.exec(
        select(Friendship).where(
            ((Friendship.user_id == current_user.id) & (Friendship.friend_id == payload.user_id)) |
            ((Friendship.user_id == payload.user_id) & (Friendship.friend_id == current_user.id)),
            Friendship.status == FriendshipStatus.ACCEPTED
        )
    ).first()
    if not friendship:
        raise HTTPException(status_code=400, detail="Target user must be a confirmed friend")

    # Check existing share
    existing_share = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == payload.user_id
        )
    ).first()
    if existing_share:
        raise HTTPException(status_code=400, detail="Routine is already shared with this user")

    share = RoutineAccess(
        routine_id=routine_id,
        user_id=payload.user_id,
        access_level=payload.access_level
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    target_user = db.get(User, payload.user_id)
    return RoutineShareRead(
        user_id=share.user_id,
        access_level=share.access_level,
        username=target_user.username,
        profile_picture=target_user.profile_picture
    )


@router.get("/{routine_id}/shares", response_model=List[RoutineShareRead], operation_id="routines_shares_list")
async def list_routine_shares(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_access = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not owner_access:
        raise HTTPException(status_code=403, detail="Only the owner can list shares")

    shares = db.exec(
        select(RoutineAccess, User)
        .join(User, RoutineAccess.user_id == User.id)
        .where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.access_level != AccessLevel.OWNER
        )
    ).all()

    return [
        RoutineShareRead(
            user_id=s.user_id,
            access_level=s.access_level,
            username=u.username,
            profile_picture=u.profile_picture
        )
        for s, u in shares
    ]


@router.get("/{routine_id}/shares/{user_id}", response_model=RoutineShareRead, operation_id="routines_shares_get")
async def get_routine_share(
    routine_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_access = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not owner_access:
        raise HTTPException(status_code=403, detail="Only the owner can view shares")

    share_data = db.exec(
        select(RoutineAccess, User)
        .join(User, RoutineAccess.user_id == User.id)
        .where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == user_id
        )
    ).first()
    if not share_data:
        raise HTTPException(status_code=404, detail="Share not found")

    s, u = share_data
    return RoutineShareRead(
        user_id=s.user_id,
        access_level=s.access_level,
        username=u.username,
        profile_picture=u.profile_picture
    )


@router.patch("/{routine_id}/shares/{user_id}", response_model=RoutineShareRead, operation_id="routines_shares_update")
async def update_routine_share(
    routine_id: int,
    user_id: int,
    payload: RoutineShareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_access = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not owner_access:
        raise HTTPException(status_code=403, detail="Only the owner can update shares")

    share_data = db.exec(
        select(RoutineAccess, User)
        .join(User, RoutineAccess.user_id == User.id)
        .where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == user_id
        )
    ).first()
    if not share_data:
        raise HTTPException(status_code=404, detail="Share not found")

    s, u = share_data
    if payload.access_level is not None:
        s.access_level = payload.access_level

    db.add(s)
    db.commit()
    db.refresh(s)

    return RoutineShareRead(
        user_id=s.user_id,
        access_level=s.access_level,
        username=u.username,
        profile_picture=u.profile_picture
    )


@router.delete("/{routine_id}/shares/{user_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="routines_shares_delete")
async def delete_routine_share(
    routine_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_access = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == current_user.id,
            RoutineAccess.access_level == AccessLevel.OWNER
        )
    ).first()
    if not owner_access:
        raise HTTPException(status_code=403, detail="Only the owner can delete shares")

    share = db.exec(
        select(RoutineAccess).where(
            RoutineAccess.routine_id == routine_id,
            RoutineAccess.user_id == user_id,
            RoutineAccess.access_level != AccessLevel.OWNER
        )
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found or cannot delete owner")

    db.delete(share)
    db.commit()
    return None




