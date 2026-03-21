from typing import Optional

from sqlmodel import SQLModel

from app.models.friendship import FriendshipStatus


class FriendRead(SQLModel):
    id: int
    username: str
    profile_picture: Optional[str] = None
    status: Optional[FriendshipStatus] = None


class FriendAdd(SQLModel):
    friend_code: str
