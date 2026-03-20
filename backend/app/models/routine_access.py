from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .routine import Routine


class AccessLevel(str, Enum):
    OWNER = "owner"
    WRITE = "write"
    READ = "read"


class RoutineAccess(BaseModel, table=True):
    """Access rights for a routine (SQLModel)."""

    __tablename__ = "routine_access"

    user_id: int = Field(foreign_key="users.id")
    routine_id: int = Field(foreign_key="routines.id")
    access_level: AccessLevel = Field(default=AccessLevel.READ)

    # Relationships
    user: "User" = Relationship(back_populates="routine_accesses")
    routine: "Routine" = Relationship(back_populates="accesses")

    def __repr__(self):
        return f"<RoutineAccess(user_id={self.user_id}, routine_id={self.routine_id}, level='{self.access_level}')>"
