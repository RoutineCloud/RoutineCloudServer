import difflib
from datetime import datetime

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.routine import Routine
from app.models.user import User
from app.schemas.routine_control import RoutineStartPayload
from app.websocket.manager import ws_manager
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

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
    # Fetch all routines for this user
    routines = db.exec(
        select(Routine).where(Routine.user_id == current_user.id)
    ).all()

    if not routines:
        raise HTTPException(status_code=404, detail="No routines found for this user")

    # Find the best match for the routine name
    routine_names = [r.name for r in routines]
    matches = difflib.get_close_matches(payload.name, routine_names, n=1, cutoff=0.3)

    if not matches:
        raise HTTPException(status_code=404, detail=f"No routine found matching '{payload.name}'")

    best_match_name = matches[0]
    routine = next(r for r in routines if r.name == best_match_name)

    current_user.active_routine_id = routine.id
    current_user.active_routine_started_at = datetime.utcnow()
    db.add(current_user)
    db.commit()

    # Trigger the routine start via WebSocket
    await ws_manager.push_routine_event(current_user.id, routine.id, "start_routine")

    return {"status": "started", "routine_name": routine.name, "routine_id": routine.id}


@router.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_current_routine(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    active_routine_id = current_user.active_routine_id
    if active_routine_id is None:
        raise HTTPException(status_code=404, detail="No active routine")

    await ws_manager.push_routine_event(current_user.id, active_routine_id, "stop_routine")

    current_user.active_routine_id = None
    current_user.active_routine_started_at = None
    db.add(current_user)
    db.commit()

    return {"status": "stopped", "routine_id": active_routine_id}
