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
    friend_code: Optional[str] = None
    profile_picture: Optional[str] = None


class UserUpdate(SQLModel):
    """Schema for updating a user."""
    profile_picture: Optional[str] = None


class UserRead(UserBase):
    """Schema for returning user data."""
    id: int
