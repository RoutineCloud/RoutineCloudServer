from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from .user import User


class Device(BaseModel, table=True):
    """
    Device model for IoT devices (SQLModel)
    """
    __tablename__ = "devices"

    name: str
    type: str
    status: str = "offline"
    is_active: bool = True

    # Foreign keys
    owner_id: int = Field(foreign_key="users.id")

    # Relationships
    owner: "User" = Relationship(back_populates="devices")

    def __repr__(self):
        return f"<Device {self.name} ({self.type})>"