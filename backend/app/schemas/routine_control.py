from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel


class RoutineStartPayload(SQLModel):
    name: str


class ActiveRoutineStatusRead(BaseModel):
    active_routine_id: Optional[int] = None
    routine_name: Optional[str] = None
    status: str
    current_task_position: Optional[int] = None
    started_at: Optional[datetime] = None
