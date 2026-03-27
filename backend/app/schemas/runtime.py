from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.routine_runtime_state import RuntimeStatus
from app.schemas.routine import TaskInRoutineRead


class RuntimeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RuntimeCommandType(str, Enum):
    ROUTINE_START = "routine.start"
    ROUTINE_PAUSE = "routine.pause"
    ROUTINE_RESUME = "routine.resume"
    ROUTINE_SKIP = "routine.skip"
    ROUTINE_STOP = "routine.stop"
    ROUTINE_COMPLETE = "routine.complete"


class RuntimeEventType(str, Enum):
    RUNTIME_STARTED = "runtime.started"
    RUNTIME_PAUSED = "runtime.paused"
    RUNTIME_RESUMED = "runtime.resumed"
    RUNTIME_SKIPPED = "runtime.skipped"
    RUNTIME_STOPPED = "runtime.stopped"
    RUNTIME_COMPLETED = "runtime.completed"


class RuntimeActorRead(RuntimeModel):
    type: str
    id: str


class RuntimeRoutineRead(RuntimeModel):
    id: int
    name: str
    description: Optional[str] = None
    tasks: list[TaskInRoutineRead]


class RuntimeStateRead(RuntimeModel):
    status: RuntimeStatus
    routine_id: Optional[int] = None
    participant_user_ids: list[int] = Field(default_factory=list)
    current_task_id: Optional[int] = None
    current_task_position: Optional[int] = None
    task_started_at: Optional[datetime] = None
    routine_started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    pause_duration: int = 0
    updated_at: Optional[datetime] = None


class RuntimeActiveRead(RuntimeModel):
    server_time: datetime
    runtime: RuntimeStateRead
    routine: Optional[RuntimeRoutineRead] = None


class RuntimeSyncRead(RuntimeModel):
    server_time: datetime
    runtime: RuntimeStateRead


class RuntimeCommandRequest(RuntimeModel):
    command_id: str
    type: RuntimeCommandType
    routine_id: Optional[int] = None
    requested_at: Optional[datetime] = None
    source_device_id: Optional[str] = None


class RuntimeCommandAccepted(RuntimeModel):
    command_id: str
    accepted: bool = True
    server_time: datetime
    sync: RuntimeSyncRead
    active: Optional[RuntimeActiveRead] = None


class RuntimeEventEnvelope(RuntimeModel):
    event_id: str
    event_type: RuntimeEventType
    server_time: datetime
    actor: Optional[RuntimeActorRead] = None
    sync: Optional[RuntimeSyncRead] = None
    active: Optional[RuntimeActiveRead] = None
