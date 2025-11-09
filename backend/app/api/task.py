from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.routine import Routine
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
)


@router.get("/", response_model=List[TaskRead], operation_id="tasks_list")
async def list_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all tasks owned by the current user.
    """
    tasks = db.exec(select(Task).where(Task.user_id == current_user.id)).all()
    return [TaskRead(id=t.id, name=t.name, icon_name=t.icon_name, sound=t.sound, duration=t.duration) for t in tasks]


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED, operation_id="tasks_create")
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new task owned by the current user. Returns the created task.
    """
    task = Task(
        name=payload.name,
        icon_name=payload.icon_name,
        sound=payload.sound,
        duration=payload.duration,
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskRead(id=task.id, name=task.name, icon_name=task.icon_name, sound=task.sound, duration=task.duration)


@router.patch("/{task_id}", response_model=TaskRead, operation_id="tasks_update")
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update mutable fields of a task. All fields are optional; only provided fields are updated.
    """
    task: Optional[Task] = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this task")

    if payload.name is not None:
        task.name = payload.name
    if payload.icon_name is not None:
        task.icon_name = payload.icon_name
    if payload.sound is not None:
        task.sound = payload.sound
    if payload.duration is not None:
        task.duration = payload.duration

    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskRead(id=task.id, name=task.name, icon_name=task.icon_name, sound=task.sound, duration=task.duration)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="tasks_delete")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a task only if you are its owner and it is not used in routines owned by other users.
    """
    task: Optional[Task] = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this task")

    # Check if referenced by routines of other users
    other_ref = db.exec(
        select(RoutineTask)
        .join(Routine, Routine.id == RoutineTask.routine_id)
        .where(RoutineTask.task_id == task_id, Routine.user_id != current_user.id)
    ).first()
    if other_ref:
        raise HTTPException(status_code=403, detail="Task is used by another user's routine and cannot be deleted")

    # Deleting task will cascade delete routine_tasks via model config
    db.delete(task)
    db.commit()
    return None
