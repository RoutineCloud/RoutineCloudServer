# Routine Cloud Server Scripts

This directory contains scripts for managing and running the Routine Cloud Server application.

## Available Scripts

### run.py

This script starts the FastAPI application using uvicorn.

**Usage:**
```bash
# Using pixi
pixi run start

# Or directly
python -m scripts.run
```

### init_db.py

This script initializes the database by creating all tables and setting up an admin user.

**Environment Variables:**
- `ADMIN_USERNAME`: Username for the admin user (default: admin)
- `ADMIN_EMAIL`: Email for the admin user (default: admin@example.com)
- `INIT_ADMIN_PASSWORD`: Password for the admin user (required, no default)

**Usage:**
```bash
# Using pixi
pixi run init_db

# Or directly
python -m scripts.init_db
```

## User Groups

The application now supports user groups to identify users as normal or admin:

- `admin`: Users with administrative privileges
- `user`: Regular users with standard permissions

The user model has been updated with a `group` field that can be set to one of these values. The `is_superuser` field is maintained for backward compatibility.

## Database Schema Changes

The following changes have been made to the database schema:

1. Added `group` field to the `User` model with possible values:
   - `admin`: Administrative users
   - `user`: Regular users (default)

To apply these changes to an existing database, you need to run database migrations:

```bash
pixi run alembic revision --autogenerate -m "Add user groups"
pixi run alembic upgrade head
```