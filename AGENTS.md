# Repository Guidelines

## Project Structure & Module Organization
`backend/app/` hosts the Flask stack: `api/` for blueprints, `core/` for settings, `models/` for SQLAlchemy entities, and `schemas/` for Pydantic validation. Alembic artifacts live in `backend/migrations/`, and developer utilities (seed/run) stay in `backend/scripts/`. The Vue 3 application is under `frontend/` with routed pages in `src/views/`, shared widgets in `src/components/`, and Pinia stores in `src/stores/`. Docker assets (`docker/`) wire the two services together.

## Build, Test, and Development Commands
- `cd backend && uv sync` installs backend dependencies from `pyproject.toml` and `uv.lock`.
- `cd backend && uv run python scripts/run.py` serves the API on `:8000`; pair it with `uv run alembic upgrade head` whenever models change.
- `cd backend && uv run pytest [-k name]` executes backend tests.
- `cd frontend && npm install` then `npm run dev` launches Vite on `:3000`; `npm run build` emits optimized assets and `npm run lint` enforces formatting.

## API Client Sync Rule
When Codex changes any REST API contract (routes, request/response schemas, OpenAPI output, or related backend model/serializer behavior), Codex must run the project skill at `.codex/skills/generate-openapi-ts-api/` to regenerate the frontend client before finishing.

Use:
- `bash .codex/skills/generate-openapi-ts-api/scripts/generate_api.sh`

Treat stale generated files in `frontend/src/api/` as a blocking issue for API-related changes.

## Coding Style & Naming Conventions
Follow PEP 8 on the backend: 4-space indents, explicit type hints, `snake_case` modules, and `PascalCase` SQLAlchemy models.
Group new Flask routes by domain (`app/api/device.py`, `app/api/task.py`) and keep shared helpers inside `app/utils/`.
Vue SFCs use `<script setup lang="ts">`, 2-space indents, and `PascalCase.vue` filenames.
Pinia stores follow the `useThingStore` convention, and cross-cutting helpers belong in `src/utils/` to avoid bloated views.

## Testing Guidelines
Create backend tests under `backend/tests/<module>/test_*.py`. 
Use pytest fixtures for database setup and mock outbound HTTP clients so `uv run pytest` completes offline.
Target =80% coverage on the modules you modify and add regression cases for every new schema or service branch. 
The frontend lacks an automated suite; if you add Vitest or Cypress, keep specs beside the component and add the script to `package.json`.

## Commit & Pull Request Guidelines
Commits mirror the current history: imperative summaries under 72 characters (example: `Add device verification flow`). Separate backend and frontend edits when practical, and note migration commands in the commit body. Pull requests should include a problem statement, the commands you ran (`uv run alembic upgrade head`, `uv run pytest`, `npm run lint`), and screenshots for UI tweaks. Never commit `.env`, SQLite snapshots, or `node_modules/`.

## Security & Configuration Tips
Store secrets in `backend/.env` or `frontend/.env.local`, not in Git. Rotate OAuth credentials under `backend/app/oauth2/` when provisioning new environments and confirm `ALLOWED_ORIGINS` in `app/core/config.py` before exposing a host. Scrub JWTs and device identifiers from shared logs.
