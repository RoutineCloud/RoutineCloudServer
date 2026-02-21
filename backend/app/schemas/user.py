from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel


class UserBase(SQLModel):
    """Base schema for user data (SQLModel)."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    email: EmailStr
    username: str
    password: str


class UserUpdate(UserBase):
    """Schema for updating a user."""
    password: Optional[str] = None


class UserPasswordUpdate(SQLModel):
    """Schema for updating a user's password."""
    current_password: str
    new_password: str


class UserRead(UserBase):
    """Schema for returning user data."""
    pass
