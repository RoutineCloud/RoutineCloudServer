from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlmodel import Relationship

from .base import BaseModel
from .routine_task import RoutineTask

if TYPE_CHECKING:
    from .routine import Routine


class Task(BaseModel, table=True):
    """Task entity representing a task that can be used in multiple routines (SQLModel)."""

    __tablename__ = "tasks"

    name: str
    icon_name: str
    sound: str
    duration: int  # Duration in seconds

    # Relationships
    routine_tasks: List[RoutineTask] = Relationship(back_populates="task")
    routines: List["Routine"] = Relationship(back_populates="tasks", link_model=RoutineTask)

    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}')>"