from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    username: str | None = None


class DeviceInfo(BaseModel):
    id: int
    uuid: str
    name: str
    type: str


class DeviceCodeResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int
    message: str


class AuthJsonResponse(BaseModel):
    redirect_to: str


class DeviceVerificationResponse(BaseModel):
    status: str  # "authorized" or "denied"
    device_id: Optional[int] = None
    device: Optional[DeviceInfo] = None
    client_id: Optional[str] = None
    scope: Optional[str] = None
