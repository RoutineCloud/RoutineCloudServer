from __future__ import annotations

import time
from typing import TYPE_CHECKING

from authlib.integrations.sqla_oauth2 import (
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
    OAuth2ClientMixin,
)
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
)

from app.models.base import Base

if TYPE_CHECKING:
    pass


class OAuth2Client(Base, OAuth2ClientMixin):
    __tablename__ = "oauth2_clients"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class OAuth2AuthorizationCode(Base, OAuth2AuthorizationCodeMixin):
    __tablename__ = "oauth2_authorization_codes"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class OAuth2Token(Base, OAuth2TokenMixin):
    __tablename__ = "oauth2_tokens"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    access_token = Column(String(1000), unique=True, nullable=False)
    refresh_token = Column(String(1000), index=True)


class OAuth2DeviceCodes(Base):
    """
    Device Authorization Flow credential storage.

    Stores device_code/user_code pairs and verification status.
    """

    __tablename__ = "oauth2_device_codes"

    id = Column(Integer, primary_key=True)

    client_id = Column(String(48), nullable=True)
    scope = Column(Text, nullable=False, default="")
    device_code = Column(String(255), unique=True, nullable=False)
    user_code = Column(String(255), unique=True, nullable=False)
    # optional UUID coming from the device during device_authorization
    device_uuid = Column(String(255), nullable=True)
    # unix timestamp seconds
    expires_at = Column(Integer, nullable=False)
    interval = Column(Integer, nullable=False, default=5)
    # pending | granted | denied | expired
    status = Column(String(20), nullable=False, default="pending")

    # user will be attached when approved at verification step
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # record last poll timestamp to support slow_down decision
    last_poll = Column(Integer, nullable=False, default=0)

    # Helper methods used by Authlib grants
    def get_client_id(self):
        return self.client_id

    def get_scope(self):
        return self.scope or ""

    def get_user_code(self):
        return self.user_code

    def is_expired(self):
        return self.expires_at <= int(time.time())
