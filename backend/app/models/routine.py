from typing import Optional, TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from .base import BaseModel
from .routine_task import RoutineTask

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class Routine(BaseModel, table=True):
    """Routine entity representing a sequence of tasks (SQLModel)."""

    __tablename__ = "routines"

    name: str
    description: Optional[str] = None
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    owner: "User" = Relationship(back_populates="routines", sa_relationship_kwargs={"foreign_keys": "Routine.user_id"})

    routine_tasks: List[RoutineTask] = Relationship(back_populates="routine", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    tasks: List["Task"] = Relationship(back_populates="routines", link_model=RoutineTask)

    def __repr__(self):
        return f"<Routine(id={self.id}, name='{self.name}')>"
