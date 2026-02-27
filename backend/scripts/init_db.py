"""
Database Initialization Script (SQLModel-only)

Initializes the database by creating all tables and setting up an admin user.
Env vars:
- ADMIN_USERNAME (default: admin)
- ADMIN_EMAIL    (default: admin@example.com)
- INIT_ADMIN_PASSWORD (required)

Usage:
    python -m scripts.init_db
"""
import logging
import os
import sys

import pyrootutils
from sqlmodel import SQLModel, create_engine, Session, select

# Setup root directory
root = pyrootutils.setup_root(
    search_from=__file__,
    indicator=["pyproject.toml"],
    project_root_env_var=True,
    dotenv=True,
    cwd=True,
)

# Ensure app package is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models to register tables
from app.db import base as models_base  # noqa: F401
from app.core.security import get_password_hash
from app.models.oauth2 import OAuth2Client
from app.core.config import settings

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Set default database URL if not provided
if not getattr(settings, "DATABASE_URL", None):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.db")
    url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = url
    settings.DATABASE_URL = url
    logger.warning(f"DATABASE_URL not set. Using SQLite database at {db_path}")

# Create engine (SQLModel)
engine = create_engine(settings.DATABASE_URL)

def _mask_db_url(url: str) -> str:
    if not url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" not in rest:
        return url
    auth, after = rest.split("@", 1)
    if ":" in auth:
        user, _ = auth.split(":", 1)
        return f"{scheme}://{user}:****@{after}"
    return f"{scheme}://{auth}@{after}"

logger.info(f"Using database: {_mask_db_url(settings.DATABASE_URL)}")

def init_db() -> None:
    """
    Initialize the database by creating all tables and setting up an admin user.
    """
    try:
        logger.info("Creating database tables...")
        SQLModel.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")

        create_admin_user()
        seed_oauth_clients()
        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

def create_admin_user() -> None:
    """
    Create an admin user using environment variables if no admin exists.
    """
    admin_username = settings.ADMIN_USERNAME
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.INIT_ADMIN_PASSWORD

    if not admin_password:
        logger.error("INIT_ADMIN_PASSWORD environment variable is required.")
        sys.exit(1)

    with Session(engine) as session:
        try:
            # Check if any admin user exists
            existing_admin = session.exec(
                select(models_base.User).where(models_base.User.is_superuser == True)
            ).first()

            if existing_admin:
                logger.info(f"Admin user already exists: {existing_admin.username}")
                return

            # Create user
            hashed_password = get_password_hash(admin_password)
            admin_user = models_base.User(
                username=admin_username,
                email=admin_email,
                hashed_password=hashed_password,
                is_superuser=True,
                is_active=True,
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            logger.info(f"Admin user created successfully: {admin_username}")
        except Exception:
            session.rollback()
            raise

#TODO Check if client are valid
def _upsert_client(session: Session, *, client_id: str, client_secret: str | None, metadata: dict) -> None:
    # Check if client already exists
    existing = session.exec(select(OAuth2Client).where(OAuth2Client.client_id == client_id)).first()
    
    if existing:
        return

    item = OAuth2Client(client_id=client_id, client_secret=client_secret)
    item.set_client_metadata(metadata)
    session.add(item)
    session.commit()
    logger.info(f"Created OAuth2 client: {client_id}")


def seed_oauth_clients() -> None:
    with Session(engine) as session:
        try:
            web_client_id = "routine-web"
            web_client_metadata = {
                "client_name": "Routine Cloud Web",
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": "",
                "redirect_uris": ["http://localhost:3000/callback"],
            }

            device_client_id = "routine-device"
            device_client_metadata = {
                "client_name": "Routine Cloud Device",
                "grant_types": [
                    "urn:ietf:params:oauth:grant-type:device_code",
                    "refresh_token",
                ],
                "response_types": [],
                "token_endpoint_auth_method": "none",
                "scope": "",
                "redirect_uris": [],
            }

            alex_client_id = "alexa-client"
            alex_client_metadata = {
                "client_name": "Alexa Routine Cloud",
                "grant_types": [ # allowed grant types
                    "authorization_code",
                    "refresh_token",
                ],
                "response_types": ["code"], # allowed response types
                "token_endpoint_auth_method": "client_secret_basic", # allowed token endpoint auth methods
                "scope": "routinecloud",  # allowed scopes
                "redirect_uris": [], # allowed redirect URIs
            }

            _upsert_client(
                session,
                client_id=web_client_id,
                client_secret="",
                metadata=web_client_metadata,
            )
            _upsert_client(
                session,
                client_id=device_client_id,
                client_secret="",
                metadata=device_client_metadata,
            )
            assert settings.SECRETE_ALEXA_KEY, "SECRETE_ALEXA_KEY environment variable is required"
            _upsert_client(
                session,
                client_id=alex_client_id,
                client_secret=settings.SECRETE_ALEXA_KEY,
                metadata=alex_client_metadata,
            )
        except Exception:
            session.rollback()
            logger.exception("Failed seeding OAuth2 clients")
            raise

if __name__ == "__main__":
    logger.info("Starting database initialization...")
    init_db()
