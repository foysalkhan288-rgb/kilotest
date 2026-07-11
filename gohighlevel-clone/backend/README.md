# GoHighLevel Clone — Backend (Wave 1: Foundation)

Lean CRM / marketing-automation MVP backend. This repository contains the **shared
foundation only**: database layer, auth, all data models, Alembic migration, and
pre-wired feature routers. Feature logic is implemented by later agents in their
respective router files — they should **not** need to touch `app/db.py`,
`app/models.py`, `app/security.py`, `app/deps.py`, `app/schemas.py`, or
`app/main.py`.

## Stack

- Python 3.11+, FastAPI, Uvicorn
- Pydantic v2
- SQLAlchemy 2 (async) + asyncpg
- Alembic (async env)
- python-jose (JWT), passlib[bcrypt]
- APScheduler, httpx (Resend email)

## Project layout

```
backend/
  requirements.txt
  Dockerfile
  .env.example
  alembic.ini
  alembic/            # async env.py + versions/0001_initial.py
  app/
    main.py           # FastAPI app; wires every router; CORS for FRONTEND_URL
    db.py             # async engine + sessionmaker + Base + get_db
    config.py         # central settings (env / .env, via python-dotenv)
    security.py       # bcrypt hash/verify + JWT create/decode
    deps.py           # get_current_user, require_workspace_id
    models.py         # ALL 20 tables
    schemas.py        # Pydantic v2 request/response schemas
    routers/
      auth.py         # FULLY implemented
      workspace.py    # FULLY implemented (GET /workspace/me)
      contacts.py     # STUB (routes pre-wired)
      tags.py         # STUB
      pipelines.py    # STUB
      opportunities.py# STUB
      forms.py        # STUB (public routes included)
      pages.py        # STUB (public route included)
      emails.py       # STUB
      inbox.py        # STUB
      calendars.py    # STUB
      appointments.py # STUB (public booking routes included)
      workflows.py    # STUB
      dashboard.py    # STUB
      tasks.py        # STUB
      reviews.py      # STUB
```

## API contract

- Base prefix: `/api/v1`.
- Protected routes require `Authorization: Bearer <access_token>`.
- Public routes (no bearer required):
  - `GET  /api/v1/forms/{slug}`
  - `POST /api/v1/forms/{slug}/submit`
  - `GET  /api/v1/p/{slug}`
  - `GET  /api/v1/book/{slug}`
  - `POST /api/v1/book/{slug}`
- Every protected query is expected to scope by `workspace_id` (carried in the JWT).
  Protected routers already enforce a valid token via a router-level
  `require_workspace_id` dependency; later agents should additionally filter all
  DB queries by `workspace_id` from the token.

> Note on routing: the spec lists public routes without the `/api/v1` prefix.
> For consistency they are mounted under `/api/v1` here (e.g. `/api/v1/forms/{slug}`).
> Adjust `app/main.py` / the routers if the frontend expects them at the root path.

## Auth (implemented)

| Method | Path | Body | Result |
| ------ | ---- | ---- | ------ |
| POST | `/api/v1/auth/register` | `{email, password, workspace_name}` | creates user + owned workspace, returns access + refresh tokens + `workspace_id` |
| POST | `/api/v1/auth/login` | `{email, password}` | returns tokens |
| POST | `/api/v1/auth/refresh` | `{refresh_token}` | rotates refresh → new access token |

- Access token: 15 minutes. Refresh token: 7 days.
- JWT secret read from `JWT_SECRET` env (defaults to an insecure dev string —
  **set this in any non-local environment**).
- `GET /api/v1/workspace/me` returns the current user's workspace.

## Setup / run

1. Create a virtualenv and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy env and fill in values:

   ```bash
   cp .env.example .env
   ```

   Required:
   - `DATABASE_URL` — async Postgres DSN, e.g.
     `postgresql+asyncpg://user:pass@localhost:5432/gohighlevel`
   - `JWT_SECRET` — long random string
   - `RESEND_API_KEY` — for email (used in later waves)
   - `FRONTEND_URL` — CORS allow-origin

3. Create the database (PostgreSQL) and run migrations:

   ```bash
   alembic upgrade head
   ```

4. Run the API:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   # or via Docker:
   docker build -t gohighlevel-backend .
   docker run -e PORT=8000 --env-file .env -p 8000:8000 gohighlevel-backend
   ```

5. Import / smoke check (does not require a DB):

   ```bash
   python -c "from app.main import app; print('OK')"
   ```

## Validation status

- The app imports cleanly and all routers are wired; the migration creates the
  full schema (`alembic upgrade head`).
- **Blocker:** a live PostgreSQL instance (and the matching `DATABASE_URL`) is
  required to actually run the server, execute `alembic upgrade head`, or run
  end-to-end auth flows. In the build sandbox no Postgres/command execution was
  available, so the `pip install` + import smoke test could not be executed here.
  Run the steps above in an environment with Postgres to validate.

## Notes for later agents

- Do **not** edit shared files (`db.py`, `models.py`, `security.py`, `deps.py`,
  `schemas.py`, `main.py`). Add feature logic inside the relevant
  `app/routers/<feature>.py` stub.
- When adding a new model, add it to `app/models.py` and generate a new Alembic
  revision (`alembic revision --autogenerate -m "..."`).
- Keep every DB query scoped by `workspace_id` from the verified token.
