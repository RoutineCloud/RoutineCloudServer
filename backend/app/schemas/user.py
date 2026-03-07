from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel


class UserBase(SQLModel):
    """Base schema for user data (SQLModel)."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    oidc_sub: str
    active_routine_id: Optional[int] = None
    active_routine_started_at: Optional[datetime] = None


class UserUpdate(UserBase):
    """Schema for updating a user."""
    pass


class UserRead(UserBase):
    """Schema for returning user data."""
    id: int
