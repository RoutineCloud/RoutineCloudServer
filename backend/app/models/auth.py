from datetime import datetime
from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class BrowserSession(BaseModel, table=True):
    """
    Model for browser-based user sessions.
    
    Requested columns:
    - id
    - session_id
    - session_secret_hash
    - user_id
    - created_at
    - last_seen_at
    - expires_at
    - revoked_at
    """
    __tablename__ = "browser_sessions"

    session_id: str = Field(index=True, unique=True, nullable=False)
    session_secret_hash: str = Field(nullable=False)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(nullable=False)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships (optional but good to have)
    # user: Optional["User"] = Relationship(back_populates="browser_sessions")
