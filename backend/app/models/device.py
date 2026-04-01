from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from .user import User

class DeviceStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"

class Device(BaseModel, table=True):
    """
    Device model for IoT devices (SQLModel)
    """
    __tablename__ = "devices"
    name: str
    type: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    is_active: bool = True
    device_id: str = Field(index=True)

    # Foreign keys
    owner_id: int = Field(foreign_key="users.id")

    # Relationships
    owner: "User" = Relationship(back_populates="devices")

    def __repr__(self):
        return f"<Device {self.name} ({self.type})>"