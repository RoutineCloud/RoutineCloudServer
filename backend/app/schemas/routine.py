from typing import List, Optional

from sqlmodel import SQLModel

from app.models.routine_access import AccessLevel, StartMode


class RoutineBase(SQLModel):
    name: str
    description: Optional[str] = None


class RoutineCreate(RoutineBase):
    pass


class TaskInRoutineRead(SQLModel):
    id: int
    name: str
    icon_name: str
    sound: str
    duration: int
    position: int


class RoutineRead(RoutineBase):
    id: int
    access_level: Optional[AccessLevel] = None
    start_mode: StartMode = StartMode.NONE
    notify_mask: int = 0
    tasks: Optional[List[TaskInRoutineRead]] = None

    model_config = {"title": "Routine"}


class RoutineUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_mode: Optional[StartMode] = None
    notify_mask: Optional[int] = None


class RoutineTaskAdd(SQLModel):
    task_id: int
    position: Optional[int] = None


class RoutineShareBase(SQLModel):
    user_id: int
    access_level: AccessLevel = AccessLevel.READ


class RoutineShareCreate(RoutineShareBase):
    pass


class RoutineShareUpdate(SQLModel):
    access_level: Optional[AccessLevel] = None


class RoutineShareRead(RoutineShareBase):
    username: str
    profile_picture: Optional[str] = None
