from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from .device import Device
    from .routine import Routine


class User(BaseModel, table=True):
    """User model for authentication and user management (SQLModel)."""
    __tablename__ = "users"

    email: str = Field(index=True)
    username: str = Field(index=True)
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None

    # Relationships
    devices: List["Device"] = Relationship(back_populates="owner")
    routines: List["Routine"] = Relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"<User {self.username}>"