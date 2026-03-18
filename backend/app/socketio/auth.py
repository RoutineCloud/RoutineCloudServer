from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session, select

from app.core.security import get_or_create_user_from_oidc
from app.models.device import Device
from app.models.user import User


class SocketAuthError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class SocketIdentity:
    user: User
    device: Device


def authenticate_socket_client(
    db: Session,
    access_token: str,
    device_id: str,
    id_token: Optional[str] = None,
) -> SocketIdentity:
    if not access_token:
        raise SocketAuthError("unauthorized", "Missing access token")
    if not device_id:
        raise SocketAuthError("invalid_payload", "Missing device_id")

    try:
        user = get_or_create_user_from_oidc(db, access_token, id_token=id_token)
    except Exception as exc:
        raise SocketAuthError("unauthorized", "Invalid token") from exc

    device = db.exec(
        select(Device).where(Device.device_id == device_id, Device.owner_id == user.id)
    ).first()
    if not device:
        raise SocketAuthError("device_not_owned", "Device does not belong to user")

    return SocketIdentity(user=user, device=device)
