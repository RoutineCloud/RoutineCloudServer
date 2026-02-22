import time
import uuid
from typing import Generator

import pytest
from authlib.jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import get_db
from app.main import app
from app.models.user import User

# Setup in-memory SQLite for testing
sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def create_test_token(user_id: int) -> str:
    now = int(time.time())
    exp = now + 3600
    claims = {
        "iss": settings.OAUTH2_ISSUER,
        "iat": now,
        "exp": exp,
        "aud": "test-client",
        "jti": uuid.uuid4().hex,
        "sub": str(user_id),
    }
    return jwt.encode({"alg": settings.OAUTH2_JWT_ALG}, claims, settings.OAUTH2_JWT_KEY).decode()

@pytest.fixture
def superuser_token(session: Session) -> str:
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("admin"),
        is_superuser=True,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return create_test_token(user.id)

@pytest.fixture
def normal_user_token(session: Session) -> str:
    user = User(
        email="user@example.com",
        username="user",
        hashed_password=get_password_hash("user"),
        is_superuser=False,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return create_test_token(user.id)
