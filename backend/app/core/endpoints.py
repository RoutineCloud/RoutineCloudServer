import time

from authlib.oauth2.rfc8628 import DeviceAuthorizationEndpoint as _DeviceAuthorizationEndpoint

from app.core.config import settings
from app.db.session import get_db
from app.models.oauth2 import OAuth2DeviceCodes


class DeviceAuthorizationEndpoint(_DeviceAuthorizationEndpoint):
    CLIENT_AUTH_METHODS = ["client_secret_basic", "client_secret_post", "none"]

    def get_verification_uri(self) -> str:
        # End-user verification page served by our frontend
        return str(settings.OAUTH_DEVICE_VERIFICATION_URI)

    def save_device_credential(self, client_id, scope, data):
        # data includes: device_code, user_code, expires_in, interval
        session = next(get_db())
        expires_at = int(time.time()) + int(data.get("expires_in", 1800))
        item = OAuth2DeviceCodes(
            client_id=client_id,
            scope=scope or "",
            device_code=data["device_code"],
            user_code=data["user_code"],
            device_uuid=data.get("device_uuid"),
            expires_at=expires_at,
            interval=int(data.get("interval", 5)),
            status="pending",
        )
        session.add(item)
        session.commit()