from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """Base mixin for all SQLModel tables (not a table itself)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})