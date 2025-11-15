import os
import secrets
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    # API settings
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days


    ALLOWED_HOSTS: List[str] = []
    CORS_ORIGINS: List[str] = []

    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DATABASE_URL: str = os.getenv("DATABASE_URL", None)

    # OAuth client configuration
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "AlexaRoutinCloud")
    OAUTH_CLIENT_SECRET: Optional[str] = os.getenv("OAUTH_CLIENT_SECRET", None)
    OAUTH_ALLOWED_REDIRECT_URIS: List[AnyHttpUrl] = []
    # Device Authorization Flow verification page (frontend)
    OAUTH_DEVICE_VERIFICATION_URI: AnyHttpUrl = "http://localhost:3000/device"

    # Alexa integration settings
    # TODO Why do I need this?
    ALEXA_SKILL_ID: Optional[str] = os.getenv("ALEXA_SKILL_ID")
    SECRETE_ALEXA_KEY: Optional[str] = os.getenv("SECRETE_ALEXA_KEY")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings object
settings = Settings()