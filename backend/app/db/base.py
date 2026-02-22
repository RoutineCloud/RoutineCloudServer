"""
Central place to import all models so that SQLModel/SQLAlchemy metadata is aware of them.
Used by app.main and scripts.init_db for side-effect registration and admin views.
"""
from sqlmodel import SQLModel  # noqa: F401

from app.models.device import Device  # noqa: F401
from app.models.oauth2 import (
    OAuth2Client,  # noqa: F401
    OAuth2AuthorizationCode,  # noqa: F401
    OAuth2Token,  # noqa: F401
    OAuth2DeviceCodes,  # noqa: F401
    OAuthConsent,  # noqa: F401
)
from app.models.routine import Routine  # noqa: F401
from app.models.routine_task import RoutineTask  # noqa: F401
from app.models.task import Task  # noqa: F401
# Import models to register tables and expose for admin usage
from app.models.user import User  # noqa: F401

__all__ = [
    "SQLModel",
    "User",
    "Device",
    "Task",
    "Routine",
    "RoutineTask",
    "OAuth2Client",
    "OAuth2AuthorizationCode",
    "OAuth2Token",
    "OAuth2DeviceCodes",
    "OAuthConsent",
]
