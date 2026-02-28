import secrets
from pathlib import Path
from typing import List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    # API settings
    API_V1_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    ALLOWED_HOSTS: List[str] = []

    # CORS settings
    ALLOW_ORIGINS: List[str] = []

    @field_validator("ALLOW_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DATABASE_URL: Optional[str] = None
    
    # Alexa integration settings
    # TODO Why do I need this?
    ALEXA_SKILL_ID: Optional[str] = None
    SECRETE_ALEXA_KEY: Optional[str] = None

    # OIDC configuration
    OIDC_ISSUER: str = "https://issuer.zitadel.ch"
    OIDC_CLIENT_ID: Optional[str] = None
    OIDC_CLIENT_SECRET: Optional[str] = None
    OIDC_JWKS_URL: Optional[str] = None
    
    # Load environment from backend/.env and backend/.env.local (local takes precedence)
    # Use absolute paths so loading works regardless of current working directory
    #TODO make the loading with path better
    _BASE_DIR = Path(__file__).resolve().parents[2]
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=(
            _BASE_DIR / ".env",        # example/defaults
            _BASE_DIR / ".env.local",  # developer/local overrides
        ),
        env_file_encoding="utf-8",
    )


# Global settings object
settings = Settings()