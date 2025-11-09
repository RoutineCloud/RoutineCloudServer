from typing import Optional

from sqlmodel import SQLModel

from app.models.device import DeviceStatus


class DeviceBase(SQLModel):
    name: str
    type: str
    is_active: bool = True


class DeviceCreate(DeviceBase):
    pass


class DeviceRead(DeviceBase):
    id: int
    status: DeviceStatus = DeviceStatus.OFFLINE

    model_config = {"title": "Device"}


class DeviceUpdate(SQLModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[DeviceStatus] = None
