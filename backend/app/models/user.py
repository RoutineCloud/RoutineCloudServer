#DO NOT use from future import annotations as this will break SQLModel with SQLAlchemy!!!

from datetime import datetime
from typing import Optional, List
from typing import TYPE_CHECKING

from app.models.base import BaseModel
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from .device import Device
    from .routine import Routine
    from .task import Task


class User(BaseModel, table=True):
    """User model for authentication and user management (SQLModel)."""
    __tablename__ = "users"

    email: Optional[str] = Field(default=None, index=True)
    username: Optional[str] = Field(default=None, index=True)
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    oidc_sub: str = Field(index=True, unique=True)

    # Relationships
    devices: List["Device"] = Relationship(back_populates="owner")
    routines: List["Routine"] = Relationship(back_populates="owner")
    tasks: List["Task"] = Relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"<User {self.username}>"
