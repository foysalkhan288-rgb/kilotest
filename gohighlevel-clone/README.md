# GoHighLevel Clone — MVP

A lean GoHighLevel-style CRM / marketing-automation MVP. FastAPI backend
(async SQLAlchemy + PostgreSQL) with a React 18 + Vite + Mantine v7 frontend.

> **Status:** Code is **static-review complete** but **NOT runtime-verified**.
> The sandbox blocked command execution, so nothing was installed or run
> (no `npm`, `pip`, `uvicorn`, or DB migrations were executed). See the
> **STATUS** section for what is implemented, what is stubbed, and known
> runtime-only risks.

---

## What was built (feature → MVP scope)

| Area | Backend | Frontend | Notes |
|------|---------|----------|-------|
| Auth | `auth.py` register / login / refresh (`/api/v1/auth/*`) | Login / Register pages, `AuthContext`, token refresh interceptor | JWT access + refresh; workspace_id encoded in token |
| Workspaces | `workspace.py` `/workspace/me` | shown in `Layout` header | created on registration |
| Contacts | `contacts.py` CRUD + tags + per-contact tasks/opportunities | Contacts page | search/tag filters, tag add/remove |
| Tags | `tags.py` CRUD | used inside Contacts | workspace-scoped |
| Pipelines & Stages | `pipelines.py` CRUD + stages | Pipelines page (drag-to-move Kanban) | |
| Opportunities | `opportunities.py` CRUD + move | Pipelines page (deals) | |
| Forms | `forms.py` CRUD + public submit | Forms page | CREATE + public GET/POST (see Public pages) |
| Pages | `pages.py` CRUD + public render | Pages page | CREATE + public GET (see Public pages) |
| Email | `emails.py` send / campaign + log | Email page | via Resend (`send_email`) |
| Inbox | `inbox.py` conversations aggregation | Inbox page | aggregates emails + form submissions per contact |
| Calendars | `calendars.py` CRUD | Calendar page | public booking slug |
| Appointments | `appointments.py` CRUD + public booking | Calendar page | public POST creates contact + books |
| Workflows | `workflows.py` CRUD + engine `workflows_engine.py` | Workflows page | event-driven automation (never raises) |
| Dashboard | `dashboard.py` summary | Dashboard page | totals, open pipeline value, appts today, activity |
| Reviews | `reviews.py` request / respond / record | Reviews page | email review-request link |
| Tasks | `tasks.py` **stub** | — | backend returns `[]` / `501`; no UI |

**Automation engine (`app/workflows_engine.py`)** loads all active workflows
for a workspace on a given event and executes their actions
(`send_email`, `add_tag`/`remove_tag`, `create_task`,
`move_opportunity_stage`, `notify`, `wait`, `if_else`). It is invoked from
`contacts.py` (contact.created), `forms.py` (form.submitted),
`appointments.py` (appointment.booked / appointment.no_show). `wait` actions
are deferred via the APScheduler instance started in `main.py` (in-process).

### Public (unauthenticated) endpoints
These are JSON API endpoints (a rendered public frontend is a follow-up):

- Forms: `GET  /api/v1/forms/{slug}/public` and `POST /api/v1/forms/{slug}/submit`
  (submit creates/updates a contact, inserts a `form_submissions` row, and
  fires `handle_event('form.submitted', workspace_id, {contact_id, data})`).
- Pages: `GET  /api/v1/p/{slug}` (returns the page definition JSON).
- Booking: `GET  /api/v1/book/{slug}` and `POST /api/v1/book/{slug}`
  (creates a contact if needed, books an appointment, sends a confirmation,
  fires `appointment.booked`).

> Why `/forms/{slug}/public` + `/forms/{slug}/submit` rather than a bare
> `/forms/{slug}`: the protected `GET /forms/{id}` already occupies that
> path pattern, so the public routes are namespaced to avoid a collision.

---

## Prerequisites

- Python **3.11+**
- Node.js **18+**
- A running **PostgreSQL** database and a `DATABASE_URL`
  (e.g. `postgresql+asyncpg://user:pass@localhost:5432/gohighlevel`)

---

## Backend run steps

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set at least:
#   DATABASE_URL, JWT_SECRET, RESEND_API_KEY, EMAIL_FROM, FRONTEND_URL

alembic upgrade head                 # create/upgrade schema
uvicorn app.main:app --reload          # serves on :8000
```

API docs (Swagger UI): http://localhost:8000/docs

`requirements.txt` pins: fastapi, uvicorn, pydantic, sqlalchemy, alembic,
python-jose, passlib/bcrypt, APScheduler, httpx, asyncpg, python-multipart,
email-validator, python-dotenv.

---

## Frontend run steps

```bash
cd frontend
npm install
cp .env.example .env
# .env: VITE_API_URL=http://localhost:8000

npm run dev          # Vite dev server on :5173
```

Build: `npm run build` (runs `tsc && vite build`). Typecheck: `npm run typecheck`.

---

## Mantine v7 notes

The frontend targets **@mantine/core ^7.10**. All v6-only props have been
migrated to v7: `leftIcon`/`rightIcon` → `leftSection`/`rightSection`,
`Group position=` → `justify=`, `Text weight=` → `fw=`, `Stack/Group/SimpleGrid
spacing=` → `gap=`, and `Group noWrap` → `wrap={false}`. The `AppShell`
header/navbar are used via `AppShell.Header` / `AppShell.Navbar` (Layout.tsx).

---

## STATUS — incomplete / risky

**Implemented & reviewed (static):**
- All protected queries filter by `workspace_id` via `deps.require_workspace_id`.
- `forms.py` and `pages.py` are **fully implemented** (CRUD + local Pydantic
  schemas + public endpoints), not stubs.
- `workflows_engine.handle_event` is importable; guarded imports in
  `contacts.py` (try/except), `forms.py` (direct), `calendars.py` (n/a),
  `appointments.py` (lazy try/except) are correct.
- `main.py` includes all 16 routers under `/api/v1` and starts APScheduler.
- Frontend API call paths match implemented backend endpoints.
- Frontend Mantine v6→v7 breaking props fixed across all pages.

**Stubbed / not implemented:**
- `tasks.py` is a stub (returns `[]` / HTTP 501). No Tasks UI exists.
- No public *rendered* frontend for forms/pages/booking — only JSON endpoints.

**Known runtime-only risks (cannot be verified without install + a real DB):**
- **Email sending** requires a valid `RESEND_API_KEY`. Without it,
  `send_email` stores rows with `status='failed'` (does not crash), so email
  features are effectively no-op in dev.
- **Workflow `wait`** uses APScheduler **in-process**. It will not fire after
  a single-process restart and won't run across multiple workers / serverless.
- **CORS**: the backend allows only `FRONTEND_URL`. The example `.env` now
  points to `http://localhost:5173` (Vite default); if you serve the frontend
  elsewhere, update `FRONTEND_URL` or the browser will be blocked.
- **Auth response contract**: the backend returns `{access_token,
  refresh_token, workspace_id}` (no `user`/`workspace` object). The frontend
  `auth.ts`/`AuthContext.tsx` were aligned to this shape; the UI shows the
  workspace id but no workspace name (the API does not return one yet).
- **No tests** were executed (and none are wired in this MVP).
- Alembic has a single initial migration (`0001_initial.py`); confirm it
  matches `models.py` once you can run `alembic upgrade head` against Postgres.
