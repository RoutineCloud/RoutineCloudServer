#!/bin/bash

set -e

# Use python to wait for DB
uv run python << END
import sys
import time
from sqlmodel import create_engine, Session, select
from app.core.config import settings

def wait_for_db():
    # Mask password in logs
    masked_url = settings.DATABASE_URL
    if "@" in masked_url:
        auth, rest = masked_url.split("@", 1)
        if ":" in auth:
            scheme_user, _ = auth.rsplit(":", 1)
            masked_url = f"{scheme_user}:****@{rest}"
    
    print(f"Waiting for database at {masked_url}...")
    engine = create_engine(settings.DATABASE_URL)
    start_time = time.time()
    timeout = 60
    while True:
        try:
            with Session(engine) as session:
                # Try a simple query
                session.exec(select(1))
            print("Database is ready!")
            break
        except Exception as e:
            if time.time() - start_time > timeout:
                print(f"Timeout waiting for database: {e}")
                sys.exit(1)
            print(f"Database not ready yet, retrying in 1s...")
            time.sleep(1)

if __name__ == "__main__":
    wait_for_db()
END

# Run migrations
echo "Running migrations..."
uv run alembic upgrade head

echo "Startup script finished successfully."

# Run the passed command
exec "$@"
