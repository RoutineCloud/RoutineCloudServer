from typing import Optional

from sqlmodel import SQLModel


class TaskBase(SQLModel):
    name: str
    icon_name: str
    sound: str
    duration: int


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: int

    model_config = {"title": "Task"}


class TaskUpdate(SQLModel):
    name: Optional[str] = None
    icon_name: Optional[str] = None
    sound: Optional[str] = None
    duration: Optional[int] = None
