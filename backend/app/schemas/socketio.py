from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.routine_runtime_state import RuntimeStatus
from app.schemas.routine import RoutineRead


class SocketModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SocketAuthPayload(SocketModel):
    access_token: str
    device_id: str
    id_token: Optional[str] = None


class HeartbeatPayload(SocketModel):
    ts: datetime


class CommandType(str, Enum):
    ROUTINE_START = "routine.start"
    ROUTINE_END = "routine.end"
    ROUTINE_PAUSE = "routine.pause"
    ROUTINE_RESUME = "routine.resume"
    TASK_SKIP = "task.skip"


class ClientCommandPayload(SocketModel):
    command_id: str
    type: CommandType
    routine_id: Optional[int] = None
    source_device_id: Optional[str] = None
    requested_at: datetime


class SocketRuntimePayload(SocketModel):
    active_routine_id: Optional[int] = None
    status: RuntimeStatus
    current_task_position: Optional[int] = None
    task_started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SocketDevicePayload(SocketModel):
    id: int
    device_id: str
    name: str
    type: str
    status: str
    is_active: bool


class SocketSnapshotPayload(SocketModel):
    runtime: SocketRuntimePayload
    routines: list[RoutineRead]
    devices: list[SocketDevicePayload]
    server_time: datetime


class CommandRejectedPayload(SocketModel):
    command_id: Optional[str] = None
    reason: str


class SocketErrorPayload(SocketModel):
    code: str
    message: str
