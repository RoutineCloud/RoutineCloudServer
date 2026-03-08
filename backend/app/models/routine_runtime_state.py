from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class RuntimeStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


class RoutineRuntimeState(BaseModel, table=True):
    __tablename__ = "routine_runtime_states"

    user_id: int = Field(foreign_key="users.id", index=True, unique=True)
    active_routine_id: Optional[int] = Field(default=None, foreign_key="routines.id")
    status: RuntimeStatus = Field(default=RuntimeStatus.IDLE)
    current_task_position: Optional[int] = None
    task_started_at: Optional[datetime] = None
