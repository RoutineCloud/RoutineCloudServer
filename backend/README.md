# Routine Cloud Backend

This is the backend for the Routine Cloud application, built with FastAPI and SQLite (default) or PostgreSQL.

## Setup

### Prerequisites

- Python 3.11+
- SQLite (default) or PostgreSQL
- uv (for environment and dependency management)

### Environment Setup

1. Sync dependencies:
   ```bash
   cd backend
   uv sync
   ```

### Database Setup

The application uses SQLite by default (stored in `backend/routine_cloud.db`).

If you prefer PostgreSQL:
1. Create a PostgreSQL database:
   ```bash
   createdb routine_cloud
   ```

2. Update `.env` (or `.env.local`) with your PostgreSQL credentials, or set `DATABASE_URL` directly.

### Running Migrations

```bash
cd backend
uv run alembic upgrade head
```

### Running the Application

```bash
cd backend
uv run python scripts/run.py
```

API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Creating New Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "Description of changes"
uv run alembic upgrade head
```

### Running Tests

```bash
cd backend
uv run pytest
```
