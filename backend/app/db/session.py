from typing import Generator

from sqlmodel import create_engine, Session

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

# FastAPI-Dependency
def get_db() -> Generator[Session, None, None]:
    """Gibt eine SQLModel-Session als Dependency zurück."""
    with Session(engine) as session:
        yield session
