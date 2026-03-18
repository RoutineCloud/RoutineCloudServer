# Routine Cloud Server Scripts

This directory contains scripts for managing and running the Routine Cloud Server application.

## Available Scripts

### run.py

This script starts the FastAPI application using uvicorn.

**Usage:**
```bash
# Preferred (via uv)
uv run python scripts/run.py

# Or directly
python -m scripts.run
```

## Database Schema Changes

The application uses SQLAlchemy (via SQLModel) and Alembic for database migrations.

To apply changes to an existing database:

```bash
uv run alembic upgrade head
```
