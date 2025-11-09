from typing import List, Optional

from sqlmodel import SQLModel


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
    tasks: Optional[List[TaskInRoutineRead]] = None

    model_config = {"title": "Routine"}


class RoutineUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RoutineTaskAdd(SQLModel):
    task_id: int
    position: Optional[int] = None
