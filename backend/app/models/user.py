#DO NOT use from future import annotations as this will break SQLModel with SQLAlchemy!!!

import uuid
from datetime import datetime
from typing import Optional, List
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel
from .routine_access import RoutineAccess

if TYPE_CHECKING:
    from .device import Device
    from .task import Task
    from .friendship import Friendship


def generate_friend_code() -> str:
    return str(uuid.uuid4()).split("-")[0].upper()


class User(BaseModel, table=True):
    """User model for authentication and user management (SQLModel)."""
    __tablename__ = "users"

    email: Optional[str] = Field(default=None, index=True)
    username: Optional[str] = Field(default=None, index=True)
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    oidc_sub: str = Field(index=True, unique=True)
    friend_code: str = Field(default_factory=generate_friend_code, index=True, unique=True)
    profile_picture: Optional[str] = Field(default=None, description="Base64 encoded highly compressed image")

    # Relationships
    devices: List["Device"] = Relationship(back_populates="owner")
    routine_accesses: List["RoutineAccess"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="owner")
    friendships: List["Friendship"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Friendship.user_id",
            "back_populates": "user",
        }
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
