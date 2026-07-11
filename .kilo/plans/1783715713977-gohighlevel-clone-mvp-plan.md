# GoHighLevel Clone — MVP Plan (Master Document)

> Status: FINAL. This single file is the consolidated planning document.
> It replaces the multi-file `docs/gohighlevel-clone/` set (which can be
> generated during implementation). Sections below map 1:1 to those docs.

## 0. Overview
Build an **affordable, lean alternative to GoHighLevel** from scratch.
We are NOT cloning every feature. We ship a Minimum Viable Product (MVP)
with the core features most small businesses use, then extend in clear phases.

A user signs up, gets **one workspace**, and can:
- Store/manage contacts (CRM)
- Track deals in a visual pipeline
- Build lead-capture forms + simple landing pages
- Send outbound email and see conversations in one inbox
- Let clients book appointments via a calendar
- Automate repetitive steps with simple rules (triggers -> actions)
- See a basic dashboard of key numbers

## 1. Product Requirements (PRD)
### 1.1 Goal
Offer the ~20% of GHL features that deliver 80% of the value, at a fraction
of GHL's $97/mo starter price.

### 1.2 Personas
- **Owner (you / solo business):** sets up workspace, builds forms/pages,
  manages contacts and pipeline, sends emails, books/holds appointments.
- **End customer (lead/client):** fills forms, books appointments, receives emails.

### 1.3 MVP scope (IN)
1. Auth + workspace (email/password, one workspace per user)
2. Contacts/CRM (create, edit, list, tag, custom fields, notes, tasks)
3. Pipelines (kanban board, stages, drag to move, deal value)
4. Forms & Surveys (block builder, embed + hosted URL, lead -> contact)
5. Landing Pages (block builder + templates, published URL)
6. Email (outbound campaigns/automation via Resend/SES; inbox = sent + in-app)
7. Unified Inbox (view conversations: form submits, emails sent, in-app notes)
8. Calendar / Booking (public booking page, create appointments, reminders)
9. Workflows (rules engine: triggers -> actions + Wait + If/Else)
10. Dashboard (counts: contacts, pipeline value, appointments today, activity)

### 1.4 Out of scope (MVP)
SMS/Voice, AI bots, white-label/SaaS reselling, multi-tenant sub-accounts,
billing/Stripe, full drag-drop workflow canvas, inbound email parsing,
custom domains, memberships/courses, affiliate manager, documents/e-sign,
analytics reporting, native social posting.

### 1.5 Success criteria
A solo user can: sign up -> build a form -> capture a lead -> see it in CRM
-> move it through a pipeline -> email the lead -> book a call -> automate a
follow-up. All without code.

## 2. Architecture & Infra
### 2.1 Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 (async)
- **Frontend:** React 18 + Vite, TypeScript, React Router, TanStack Query,
  a UI kit (e.g., shadcn/ui or Mantine), react-hook-form
- **DB:** PostgreSQL 15+
- **Auth:** bcrypt password hash + JWT (access + refresh), python-jose
- **Email send:** Resend (or Amazon SES) SDK
- **Migrations:** Alembic
- **Validation:** Pydantic schemas for every endpoint
- **Background jobs:** APScheduler (in-process) for email sends, appointment
  reminders, and workflow `Wait` steps; polls DB, no extra infra.
- **Storage (future):** S3-compatible (Cloudflare R2) for page images/files

### 2.2 Hosting (Railway/Render)
- `api` service: FastAPI (Dockerfile, `uvicorn`)
- `web` service: static React build (served by Nginx or Render static)
- `postgres`: managed add-on
- Env vars: `DATABASE_URL`, `JWT_SECRET`, `RESEND_API_KEY`, `FRONTEND_URL`
- Free/cheap tiers to start; pay-as-you-scale.

### 2.3 Repo layout
```
/gohighlevel-clone
  /backend
    main.py, /app (routers, models, schemas, services, db)
    alembic/, requirements.txt, Dockerfile
  /frontend
    /src (pages, components, api, hooks)
    vite.config.ts, package.json
  README.md
```

### 2.4 Key design rules
- All data scoped by `workspace_id` (foreign key on every tenant table).
- API requires valid JWT; workspace isolation enforced server-side.
- Outbound email queued/retried; never block request on send.

## 3. Data Model (schema)
Tables (all include `id`, `created_at`, `workspace_id`):
- **users** (id, email UNIQUE, password_hash, created_at)
- **workspaces** (id, name, owner_user_id, created_at)
- **workspace_members** (workspace_id, user_id, role)  [future multi-user]
- **contacts** (id, workspace_id, firstname, lastname, email, phone,
  company, tags[], custom_fields JSONB, notes, created_at)
- **tags** (id, workspace_id, name, color)
- **pipelines** (id, workspace_id, name)
- **pipeline_stages** (id, pipeline_id, name, position)
- **opportunities** (id, workspace_id, contact_id, pipeline_id, stage_id,
  name, value, status, created_at)
- **forms** (id, workspace_id, name, definition JSONB, published_slug,
  created_at)
- **form_submissions** (id, form_id, contact_id, data JSONB, created_at)
- **pages** (id, workspace_id, name, definition JSONB, published_slug)
- **emails** (id, workspace_id, contact_id, subject, body, status,
  sent_at)  [outbound log]
- **conversations** (id, workspace_id, contact_id, channel, last_message)
- **messages** (id, conversation_id, direction, body, created_at)
- **appointments** (id, workspace_id, contact_id, start, end, status,
  created_at)
- **calendars** (id, workspace_id, name, public_slug, availability JSONB)
- **workflows** (id, workspace_id, name, trigger JSONB, actions JSONB,
  active bool)
- **tasks** (id, workspace_id, contact_id, title, due, done)
- **activity_log** (id, workspace_id, type, message, created_at)
- **reviews** (id, workspace_id, contact_id, platform, rating, body,
  status, requested_at, responded_at)  [Phase 1.5]

Relationships: workspace 1—* contacts/forms/pages/emails/appointments/
workflows; contact 1—* opportunities/messages/tasks; form 1—* submissions.

## 4. API Design (REST)
Base: `/api/v1`. All require `Authorization: Bearer <jwt>`.

Auth: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
Workspace: `GET /workspace/me`
Contacts: `GET/POST/PATCH/DELETE /contacts`, `POST /contacts/{id}/tags`
Tags: `GET/POST /tags`
Pipelines: `GET/POST /pipelines`, `GET/POST /pipelines/{id}/stages`
Opportunities: `GET/POST/PATCH /opportunities`, `POST /opportunities/{id}/move`
Forms: `GET/POST/PATCH/DELETE /forms`, `GET /forms/{slug}` (public),
  `POST /forms/{slug}/submit` (public)
Pages: `GET/POST/PATCH/DELETE /pages`, `GET /p/{slug}` (public render)
Email: `POST /emails/send`, `GET /emails`, `POST /emails/campaign`
Inbox: `GET /conversations`, `GET /conversations/{id}/messages`
Calendar: `GET/POST /calendars`, `GET /book/{slug}` (public),
  `POST /book/{slug}` (public), `GET/POST/PATCH /appointments`
Workflows: `GET/POST/PATCH/DELETE /workflows`, `POST /workflows/{id}/toggle`
Dashboard: `GET /dashboard/summary`
Tasks: `GET/POST/PATCH /tasks`
Reviews: `GET/POST /reviews`, `POST /reviews/request`,
  `POST /reviews/{id}/respond`  [Phase 1.5]

## 5. Feature Specs (MVP)
### 5.1 Auth & Workspace
Email+password; on register, create user + their first workspace. JWT access
(15 min) + refresh (7 days). Frontend stores tokens; refresh on 401.

### 5.2 Contacts/CRM
List with search/filter by tag; detail page shows fields, notes, tasks,
opportunities, conversation history. Tags are reusable colored labels.
Custom fields stored as JSONB. "Create task" attaches to contact.

### 5.3 Pipelines
Kanban: columns = stages, cards = opportunities (name + value). Drag card to
another column updates `stage_id`. Add/edit stages. One default pipeline.

### 5.4 Forms & Surveys
Block builder: add blocks (short text, long text, email, phone, dropdown,
checkbox, submit). Preview. Save definition as JSONB. Two ways to use:
(1) hosted URL `/forms/{slug}`, (2) embed snippet. On submit: create/update
contact, create `form_submission`, log activity, fire matching workflows.

### 5.5 Landing Pages
Same block builder + section/template library. Publish to `/p/{slug}`.
Images -> future S3. MVP: text, image URL, button, form embed.

### 5.6 Email
`POST /emails/send` (to one contact) and campaign (to a smart filter/tag).
Sent via Resend; store in `emails`; on open (future) update status. Inbox
shows sent emails + in-app messages + form submissions as a timeline.

### 5.7 Calendar / Booking
Owner sets availability (days/hours) per calendar; public `/book/{slug}`
lets a contact pick a slot -> creates `appointment` + contact, sends
confirmation email. Reminder email sent via a workflow/cron before start.

### 5.8 Workflows (rules engine)
A workflow = 1 trigger + ordered actions (+ optional Wait + If/Else).
Triggers: `form.submitted`, `contact.created`, `tag.added`,
`appointment.booked`, `appointment.no_show`.
Actions: `send_email`, `add_tag`, `remove_tag`, `create_task`,
`move_opportunity_stage`, `notify` (internal).
Engine: on event, evaluate matching workflows, execute actions in order;
`Wait` delays via APScheduler job; `If/Else` branches on a contact field.
(MVP uses APScheduler in-process; full canvas later.)

### 5.9 Dashboard
`GET /dashboard/summary` returns: total contacts, open pipeline value,
appointments today, recent activity (last 10 from `activity_log`).

### 5.10 Reputation & Reviews (Phase 1.5)
Trigger review requests after a positive event (appointment completed,
invoice paid, workflow step) via email/SMS link to Google or Facebook.
Store incoming reviews in a **review inbox** with status (new/responded),
and allow a saved response template (manual send; AI draft deferred to
Phase 3). Keep it cheap: no scraping, just link-based requests + a place
to read/paste replies. Data: `reviews` table; API: `GET/POST /reviews`,
`POST /reviews/request`, `POST /reviews/{id}/respond`.

## 6. Roadmap (phases after MVP)
- **Phase 1.5 — Reputation & Reviews:** automated review requests (Google/
  Facebook), review inbox, basic response templates. Cheap, high-value; ship
  right after MVP validation (see §5.10).
- **Phase 2 — Messaging:** two-way SMS via Twilio; connect one inbox mailbox.
- **Phase 3 — AI:** Conversation AI bot, Content AI, Voice AI (defer; costly).
- **Phase 4 — Visual canvas:** drag-drop workflow builder (GHL-style).
- **Phase 5 — Multi-tenancy:** agency sub-accounts, roles, white-label.
- **Phase 6 — SaaS:** Stripe billing, plans, rebilling, custom domains.
- **Phase 7 — Extras:** memberships/courses, affiliate manager, documents/
  e-sign, analytics reporting, social planner.

## 7. Local Dev Setup (noob-friendly)
1. Install: Python 3.11+, Node 18+, Docker (for local Postgres) or
   `pip install` + a free Postgres (Supabase local / Neon).
2. Backend: `cd backend`, `python -m venv venv`, `source venv/bin/activate`,
   `pip install -r requirements.txt`, set `.env` (DATABASE_URL, JWT_SECRET,
   RESEND_API_KEY), `alembic upgrade head`, `uvicorn main:app --reload`.
3. Frontend: `cd frontend`, `npm install`, `npm run dev`.
4. Open `http://localhost:5173`; API at `http://localhost:8000/docs` (Swagger).
5. Create `.env` from `.env.example`; never commit secrets.
6. Test flow: register -> create form -> submit (public) -> see contact ->
   move pipeline -> send email -> book appointment -> add a workflow.

## 8. Risks & Validation
- **Deliverability:** outbound email reputation needs a verified domain
  (SPF/DKIM) via Resend. Validate before launch.
- **Workspace isolation:** every query must filter by `workspace_id`; add
  tests.
- **Scope creep:** resist adding SMS/AI/white-label until MVP validated.
- **Validation:** manual end-to-end test of the Section 1.5 flow + a small
  real user trial. Track: time-to-first-lead-captured.

## 9. Open questions (answer later)
- Exact low price point (decide after MVP works).
- Resend vs SES (pick Resend for simplicity; SES if volume/cost demands).
- Public page custom domains (defer to Phase 6).

## 10. GHL Feature -> Our Phase Mapping
| GHL capability (forensic report) | Our plan | Phase |
|---|---|---|
| CRM & Contacts | Full (tags, custom fields, notes, tasks) | MVP |
| Pipelines / Opportunities | Kanban + deal value | MVP |
| Forms & Surveys | Block builder (no quiz/NPS/e-sign) | MVP |
| Funnels & Websites | Landing Pages block builder (no full funnel suite) | MVP |
| Workflow Automation | Rules engine (5 triggers / 6 actions) | MVP |
| Calendars / Booking | Public booking + reminders (no GCal 2-way) | MVP |
| Email | Outbound only (no inbound parsing) | MVP |
| Unified Inbox | Sent + in-app only (no SMS/Voice/social) | MVP |
| Dashboard | Basic counts (no attribution/reporting) | MVP |
| Reputation / Reviews | Review requests + review inbox | Phase 1.5 |
| Phone / LC SMS & MMS | Twilio two-way SMS + mailbox | Phase 2 |
| AI Suite (Voice/Conversation/Content) | AI bots | Phase 3 |
| Workflow full canvas | Drag-drop builder (GHL 30+ triggers) | Phase 4 |
| Multi-tenant sub-accounts | Agency + roles + white-label | Phase 5 |
| SaaS Mode / Billing | Stripe plans, rebilling, custom domains | Phase 6 |
| Memberships/Courses/Communities | Courses + community | Phase 7 |
| Documents & Contracts | e-sign | Phase 7 |
| Affiliate Manager | Affiliate program | Phase 7 |
| Analytics / Revenue attribution | Reporting | Phase 7 |
| Integrations (Zapier/Marketplace/API v2) | Public API + webhooks | Phase 7 |
