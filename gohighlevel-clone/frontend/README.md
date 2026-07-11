# GoHighLevel Clone — Frontend

Lean GoHighLevel (GHL) clone MVP. This is **Wave 1: the shared application shell only**.
Feature-page logic is intentionally stubbed; later agents implement it (Wave 2+).

## Stack

- **Vite** + **React 18** + **TypeScript**
- **react-router-dom** — routing & protected routes
- **@tanstack/react-query** — server-state / data fetching
- **axios** — HTTP client
- **react-hook-form** — form state (used in Login/Register)
- **Mantine v7** (UI kit — see below)

## UI Kit Choice (LOCKED)

We use **Mantine** (`@mantine/core` + `@mantine/hooks`) with `@emotion/react` /
`@emotion/server`. Rationale: fast to build a consistent, accessible app shell
(sidebar, topbar, forms) with minimal custom CSS.

> **Do not swap the UI kit** without a deliberate decision — the Layout, Login,
> and Register pages are built on Mantine primitives. New pages should use
> Mantine components for consistency.

Required Mantine setup (already wired):
- `MantineProvider` in `src/App.tsx`
- `import "@mantine/core/styles.css";` in `src/main.tsx`

## Getting Started

```bash
cp .env.example .env   # optional; defaults to http://localhost:8000
npm install
npm run dev            # http://localhost:3000
npm run build          # tsc + vite build
npm run typecheck      # tsc --noEmit
```

Backend API is expected at `VITE_API_URL` (default `http://localhost:8000`),
serving `/api/v1`. Auth endpoints used:
`POST /api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/refresh`.

## Project Structure

```
src/
  main.tsx              # React root + Mantine styles
  App.tsx               # Router + QueryClientProvider + MantineProvider + routes
  api/
    client.ts           # axios instance (baseURL, Bearer token, 401 refresh)
    auth.ts             # register / login / refresh / logout helpers
  auth/
    AuthContext.tsx     # current user/workspace, login/logout, useAuth()
  components/
    Layout.tsx          # sidebar + topbar app shell (protected)
    Placeholder.tsx     # shared "TODO: Wave 2" stub for feature pages
  pages/
    Login.tsx, Register.tsx   # IMPLEMENTED
    Dashboard.tsx, Contacts.tsx, Pipelines.tsx, Forms.tsx, Pages.tsx,
    Email.tsx, Inbox.tsx, Calendar.tsx, Workflows.tsx, Reviews.tsx  # placeholders
```

## Auth & Routing

- `src/api/client.ts` attaches `Authorization: Bearer <token>` from
  `localStorage` and, on `401`, transparently calls `/auth/refresh` (queueing
  in-flight requests) before retrying. Token keys: `ghl.access_token`,
  `ghl.refresh_token`, `ghl.workspace`.
- `src/components/Layout.tsx` is the **protected layout**: renders the
  sidebar (Dashboard, Contacts, Pipelines, Forms, Pages, Email, Inbox,
  Calendar, Workflows, Reviews) + topbar, and redirects to `/login` when no
  token is present.
- Public routes: `/login`, `/register`. All `/dashboard … /reviews` routes are
  wrapped by the protected layout in `src/App.tsx`.

## How To Add A Page (for later agents)

1. Create `src/pages/MyFeature.tsx` exporting a default React component:

   ```tsx
   import Placeholder from "../components/Placeholder";
   export default function MyFeature() {
     return <Placeholder title="MyFeature" />; // replace body in Wave 2
   }
   ```

2. Add a nav entry in `NAV_ITEMS` in `src/components/Layout.tsx`
   (`{ label: "My Feature", to: "/my-feature" }`).

3. Register the route in `src/App.tsx` inside the protected `<Route>` group:

   ```tsx
   <Route path="/my-feature" element={<MyFeature />} />
   ```

**You only need to replace a page body (`src/pages/<Feature>.tsx`)** — do not
edit `Layout.tsx`, `App.tsx`, `api/*`, or `auth/*` unless changing the shell.

## Status

- ✅ App shell, routing, protected layout, sidebar nav
- ✅ Login / Register fully implemented
- ✅ 10 placeholder feature pages (Dashboard, Contacts, Pipelines, Forms,
  Pages, Email, Inbox, Calendar, Workflows, Reviews)
- ⏳ Feature-page logic — **Wave 2**
