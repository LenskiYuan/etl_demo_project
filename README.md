# Medical AI Workflow Observability Demo

This repository is a synthetic ETL and platform demo inspired by the same class of observability problems found in medical AI workflow systems. It does **not** reuse private code, schemas, data, or internal workflows. Everything is rebuilt from scratch with fake entities and deterministic synthetic events.

## What This Repository Demonstrates

- synthetic ETL for medical imaging workflow telemetry
- live PostgreSQL-backed analytics queries
- a React frontend for operational monitoring
- a FastAPI backend for authenticated data access and job control
- a Celery worker for asynchronous ETL runs
- Keycloak-based authentication and role-driven access
- multi-user persistent app state through saved dashboard views

## Stack

- `frontend/`: React + Vite + Keycloak login
- `backend/`: FastAPI API + Celery worker
- `src/medical_ai_demo/`: shared ETL pipeline logic
- `postgres`: raw, analytics, and app-state data
- `redis`: background job broker/result backend
- `keycloak`: authentication, users, and roles

## Service Architecture

1. Users sign in through Keycloak.
2. The React frontend calls the FastAPI backend with bearer tokens.
3. The backend validates tokens, queries PostgreSQL, and exposes dashboard APIs.
4. Admin users can trigger ETL runs from the UI.
5. The backend enqueues work in Redis.
6. The Celery worker runs the shared ETL pipeline and refreshes raw/analytics tables in PostgreSQL.
7. User-specific saved views are stored in PostgreSQL and loaded back into the UI.

## Default Demo Accounts

- `demo-admin` / `demo-admin-pass`
- `demo-analyst` / `demo-analyst-pass`

`demo-admin` can trigger ETL jobs. `demo-analyst` can sign in and review data but cannot launch jobs.

## Run The Full Stack

Copy environment values if needed:

```bash
cp .env.example .env
```

Then start everything:

```bash
make up
```

Services:

- frontend: `http://localhost:5173`
- backend API: `http://localhost:8000`
- keycloak: `http://host.docker.internal:8080`
- postgres: `localhost:5432`
- redis: `localhost:6379`

Stop the stack:

```bash
make down
```

## Local ETL Commands

The original standalone ETL pipeline is still available:

```bash
make demo
make test
```

Or directly:

```bash
PYTHONPATH=src python3 -m medical_ai_demo.pipeline generate --seed 7 --requests 120
PYTHONPATH=src python3 -m medical_ai_demo.pipeline etl
PYTHONPATH=src python3 -m medical_ai_demo.pipeline report
```

## Frontend Commands

```bash
make frontend-install
make frontend-build
```

## Repository Layout

- `backend/` API and worker services
- `frontend/` React application
- `keycloak/` realm import seed
- `sql/schema/` raw and analytics DDL
- `sql/postgres-init/` postgres bootstrap scripts
- `src/medical_ai_demo/` shared ETL package
- `tests/` ETL tests
- `docs/` architecture notes

## Current Scope

The analytics tables currently behave as the latest snapshot produced by the most recent ETL run, while run history and user state persist in app tables. That keeps the demo operationally realistic without turning the warehouse layer into a full historical event store.
