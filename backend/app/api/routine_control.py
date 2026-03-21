import difflib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.routine import Routine
from app.models.routine_access import RoutineAccess
from app.models.routine_runtime_state import RoutineRuntimeState
from app.models.user import User
from app.schemas.routine_control import RoutineStartPayload
from app.services.routine_command_service import CommandValidationError, routine_command_service

router = APIRouter(
    prefix="/api/routine-control",
    tags=["routine-control"],
)


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_routine_by_name(
    payload: RoutineStartPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    routines = db.exec(
        select(Routine)
        .join(RoutineAccess)
        .where(RoutineAccess.user_id == current_user.id)
    ).all()

    if not routines:
        raise HTTPException(status_code=404, detail="No routines found for this user")

    routine_names = [r.name for r in routines]
    matches = difflib.get_close_matches(payload.name, routine_names, n=1, cutoff=0.3)

    if not matches:
        raise HTTPException(status_code=404, detail=f"No routine found matching '{payload.name}'")

    best_match_name = matches[0]
    routine = next(r for r in routines if r.name == best_match_name)

    try:
        await routine_command_service.execute(
            db=db,
            user_id=current_user.id,
            command={
                "command_id": f"server-{current_user.id}-{routine.id}-{int(datetime.utcnow().timestamp())}",
                "type": "routine.start",
                "routine_id": routine.id,
                "requested_at": datetime.utcnow().isoformat(),
            },
            actor={"type": "server", "id": "api:routine-control/start"},
        )
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc

    return {"status": "started", "routine_name": routine.name, "routine_id": routine.id}


@router.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_current_routine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runtime = db.exec(
        select(RoutineRuntimeState).where(RoutineRuntimeState.user_id == current_user.id)
    ).first()
    active_routine_id = runtime.active_routine_id if runtime else None
    if active_routine_id is None:
        raise HTTPException(status_code=404, detail="No active routine")

    try:
        await routine_command_service.execute(
            db=db,
            user_id=current_user.id,
            command={
                "command_id": f"server-{current_user.id}-{active_routine_id}-{int(datetime.utcnow().timestamp())}",
                "type": "routine.end",
                "requested_at": datetime.utcnow().isoformat(),
            },
            actor={"type": "server", "id": "api:routine-control/stop"},
        )
    except CommandValidationError as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from exc

    return {"status": "stopped", "routine_id": active_routine_id}
