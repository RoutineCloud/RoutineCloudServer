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
