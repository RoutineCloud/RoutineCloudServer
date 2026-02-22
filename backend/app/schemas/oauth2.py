from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class OAuth2ClientBase(BaseModel):
    client_id: str
    client_id_issued_at: int = 0
    client_secret_expires_at: int = 0
    client_metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[int] = None

class OAuth2ClientCreate(OAuth2ClientBase):
    client_secret: Optional[str] = None

class OAuth2ClientUpdate(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    client_id_issued_at: Optional[int] = None
    client_secret_expires_at: Optional[int] = None
    client_metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None

class OAuth2ClientRead(OAuth2ClientBase):
    id: int

    class Config:
        from_attributes = True
