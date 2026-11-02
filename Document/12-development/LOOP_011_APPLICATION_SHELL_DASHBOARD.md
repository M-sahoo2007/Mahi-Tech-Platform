# Loop 011: Application Shell and Dashboard Foundation

**Status:** Implemented and verified  
**Date:** 2026-11-02

## Architecture

No architecture changes were made. The internal React/TypeScript/Vite application continues to use Django REST Framework, `accounts.User`, Django Session Authentication, HttpOnly cookies, CSRF, and the existing Redis cache configuration. Supabase Auth, JWT, public registration, and new business-module models were not introduced.

The authenticated page now has a responsive workspace shell with a sidebar, active navigation, header/profile, sign-out, main content area, loading/error states, and a mobile navigation drawer. Existing admin Team account management remains available to administrators. Unimplemented navigation is disabled and labeled Planned; no fake module pages or data are provided.

## Dashboard API

`GET /api/dashboard/summary/` requires an authenticated Django session and is implemented as a DRF `APIView` with `IsAuthenticated` plus serializer validation.

It returns:

- The current user UUID, normalized email, and Admin/Team role.
- Total and active account counts based on Django's `Team` group.
- API status and cache status/backend label.

The endpoint does not return account lists, password data, business-module totals, or fabricated values. Cache health is checked with a unique short-lived key; a cache error is reported as unavailable without failing the dashboard response.

The dashboard shows real team counts and service state. Leads, projects, tasks, revenue, activity, and follow-ups display honest not-implemented states because their business modules and data models do not exist yet.

## Redis configuration

The existing local Compose Redis service remains the cache target. The real `backend/.env` was not modified. For local server commands, `CACHE_URL` was loaded process-locally from the ignored `.env.redis` secret file; the database was separately forced to the isolated local SQLite database. This verified Django selected `django_redis.cache.RedisCache` without exposing or persisting credentials.

## Tests and verification

- `manage.py check` passed.
- All 39 backend tests passed, including dashboard access/role/count/privacy tests and Redis integration tests.
- Existing login, logout, CSRF, throttle, account permission, and audit tests remain passing.
- Frontend `npm run build` passed.
- Redis was already running and healthy on `127.0.0.1:6379`; dashboard Redis availability was exercised through the actual Redis cache backend.
- The original `backend/db.sqlite3` SHA-256 remained unchanged. No Supabase connection or migration command was run. Django's test runner created and removed its temporary SQLite test database.
- No frontend credentials are stored in browser storage, and no Redis/database variables were added to frontend configuration.

## Known limitations

- No CRM, client, project, task, proposal, invoice, payment, finance, document, or reporting data is implemented. Dashboard panels state this explicitly.
- The dashboard API uses group membership for team counts; accounts without the `Team` group are not counted as team members.
- The real backend `.env` remains unchanged. Developers must provide `CACHE_URL` process-locally or configure it privately in their own ignored backend environment file for Redis-backed throttling during normal server startup; otherwise debug mode uses LocMem.
- Password reset/invitations, MFA, and production shared Redis provisioning remain future work.
- No production readiness claim is made.

## Recommended Loop 012

Build the first business workflow, CRM & Leads, using an owner-reviewed lead model, serializer-backed authenticated endpoints, admin/team permissions, audit events, isolated-database tests, and a small functional frontend view. Keep client records and all later business modules out of scope until their own requirements and acceptance criteria are addressed.
