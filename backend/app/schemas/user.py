from typing import Optional
from datetime import datetime
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


class UserInDBBase(UserBase):
    """Base schema for user in database."""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserRead(UserInDBBase):
    """Schema for returning user data."""
    pass


class UserInDB(UserInDBBase):
    """Schema for user in database with hashed password."""
    hashed_password: str