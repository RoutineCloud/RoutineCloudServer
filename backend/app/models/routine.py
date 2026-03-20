from typing import Optional, TYPE_CHECKING, List

from sqlmodel import Relationship

from .base import BaseModel
from .routine_access import RoutineAccess
from .routine_task import RoutineTask

if TYPE_CHECKING:
    from .task import Task


class Routine(BaseModel, table=True):
    """Routine entity representing a sequence of tasks (SQLModel)."""

    __tablename__ = "routines"

    name: str
    description: Optional[str] = None

    # Relationships
    accesses: List[RoutineAccess] = Relationship(back_populates="routine", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    routine_tasks: List[RoutineTask] = Relationship(back_populates="routine", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    tasks: List["Task"] = Relationship(back_populates="routines", link_model=RoutineTask)

    def __repr__(self):
        return f"<Routine(id={self.id}, name='{self.name}')>"
