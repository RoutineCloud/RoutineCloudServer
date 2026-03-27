from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"


class Friendship(BaseModel, table=True):
    """Many-to-many relationship for friends."""
    __tablename__ = "friendships"

    user_id: int = Field(foreign_key="users.id", index=True)
    friend_id: int = Field(foreign_key="users.id", index=True)
    status: FriendshipStatus = Field(default=FriendshipStatus.PENDING)

    # Relationship to the user who added the friend
    user: "User" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Friendship.user_id==User.id",
            "back_populates": "friendships"
        }
    )
    # Relationship to the user who is being added as a friend
    friend: "User" = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Friendship.friend_id==User.id"
        }
    )

    def __repr__(self):
        return f"<Friendship(user_id={self.user_id}, friend_id={self.friend_id}, status={self.status})>"
