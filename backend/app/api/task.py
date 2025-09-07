from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.task import Task as SATask
from app.models.routine import Routine as SARoutine
from app.models.routine_task import RoutineTask as SARoutineTask
from app.models.user import User as SAUser
from app.schemas.task import TaskCreate, TaskRead


router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
)


@router.get("/", response_model=List[TaskRead])
async def list_my_tasks(
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    """
    List all tasks used in any routine owned by the current user.
    Minimal-change approach without altering Task schema.
    """
    stmt = (
        select(SATask)
        .join(SARoutineTask, SARoutineTask.task_id == SATask.id)
        .join(SARoutine, SARoutineTask.routine_id == SARoutine.id)
        .where(SARoutine.user_id == current_user.id)
        .distinct()
    )
    tasks = db.exec(stmt).all()
    return [TaskRead(id=t.id, name=t.name, icon_name=t.icon_name, sound=t.sound, duration=t.duration) for t in tasks]


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    """
    Create a new task (global scope due to existing schema). Returns the created task.
    """
    task = SATask(
        name=payload.name,
        icon_name=payload.icon_name,
        sound=payload.sound,
        duration=payload.duration,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskRead(id=task.id, name=task.name, icon_name=task.icon_name, sound=task.sound, duration=task.duration)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: SAUser = Depends(get_current_user),
):
    """
    Delete a task only if it is not used in routines owned by other users.
    If the task is only used (or unused) within the current user's scope, allow deletion.
    """
    task: Optional[SATask] = db.get(SATask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if referenced by routines of other users
    other_ref = db.exec(
        select(SARoutineTask)
        .join(SARoutine, SARoutine.id == SARoutineTask.routine_id)
        .where(SARoutineTask.task_id == task_id, SARoutine.user_id != current_user.id)
    ).first()
    if other_ref:
        raise HTTPException(status_code=403, detail="Task is used by another user's routine and cannot be deleted")

    # Deleting task will cascade delete routine_tasks via model config
    db.delete(task)
    db.commit()
    return None
