from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .routine import Routine
    from .task import Task


class RoutineTask(BaseModel, table=True):
    """
    RoutineTask entity representing a task instance in a specific routine.
    Each RoutineTask belongs to exactly one Routine and one Task.
    """

    __tablename__ = "routine_tasks"

    routine_id: int = Field(foreign_key="routines.id")
    task_id: int = Field(foreign_key="tasks.id")
    position: int

    # Relationships
    routine: "Routine | None" = Relationship(back_populates="routine_tasks")
    task: "Task | None" = Relationship(back_populates="routine_tasks")

    def __repr__(self):
        return f"<RoutineTask(routine_id={self.routine_id}, task_id={self.task_id}, position={self.position})>"