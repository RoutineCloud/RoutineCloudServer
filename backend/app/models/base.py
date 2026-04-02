from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import declarative_base
from sqlmodel import SQLModel, Field, DateTime


class BaseModel(SQLModel):
    """Base mixin for all SQLModel tables (not a table itself)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

Base = declarative_base(metadata=SQLModel.metadata)