# Routine Cloud Backend

This is the backend for the Routine Cloud application, built with FastAPI and PostgreSQL.

## Setup

### Prerequisites

- Python 3.11
- PostgreSQL
- Pixi (for environment management)

### Environment Setup

1. Install Pixi if you haven't already:
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. Initialize the Pixi environment:
   ```bash
   cd backend
   pixi install
   ```

### Database Setup

1. Install PostgreSQL if you haven't already.

2. Create a new PostgreSQL database:
   ```bash
   createdb routine_cloud
   ```

3. Update the `.env` file with your PostgreSQL credentials:
   ```
   POSTGRES_SERVER=localhost
   POSTGRES_USER=your_postgres_user
   POSTGRES_PASSWORD=your_postgres_password
   POSTGRES_DB=routine_cloud
   POSTGRES_PORT=5432
   ```

   Alternatively, you can set the `DATABASE_URL` directly:
   ```
   DATABASE_URL=postgresql://your_postgres_user:your_postgres_password@localhost:5432/routine_cloud
   ```

### Running Migrations

1. Run the migrations to create the database tables:
   ```bash
   cd backend
   pixi run alembic upgrade head
   ```

   This will create the following tables:
   - `users`: User accounts
   - `devices`: IoT devices
   - `alexa_links`: Alexa account links

### Running the Application

1. Start the FastAPI application:
   ```bash
   cd backend
   pixi run start
   ```

2. The API will be available at http://localhost:8000

3. API documentation is available at:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development

### Creating New Migrations

If you make changes to the database models, you'll need to create a new migration:

```bash
cd backend
pixi run alembic revision --autogenerate -m "Description of changes"
```

Then apply the migration:

```bash
pixi run alembic upgrade head
```

### Running Tests

```bash
cd backend
pixi run pytest
```