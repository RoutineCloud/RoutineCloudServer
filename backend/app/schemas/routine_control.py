from sqlmodel import SQLModel

class RoutineStartPayload(SQLModel):
    name: str
