# 10. Deployment and Environment Guide

## 10.1 Environment model

### Local development
- Developer-owned local frontend and backend.
- Fresh local SQLite database at `backend/dev.sqlite3`, or a dedicated Supabase development project.
- Test/sample data only.
- `.env` files excluded from Git.
- The pre-existing `backend/db.sqlite3` is not selected by settings and must not be used for custom-user migrations.

### Staging
- Cloud deployment mirroring production architecture.
- Separate non-production database and storage.
- Synthetic or anonymized test data.
- Used for QA, acceptance and release rehearsal.

### Production
- Cloud-hosted frontend and Django backend.
- Production Supabase PostgreSQL and private storage.
- HTTPS, restricted secrets, backups, monitoring and access controls.
- No debug mode.

## 10.2 Environment variables

Frontend public variable:
- `VITE_API_BASE_URL`

Backend server-side variables:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DB_ENGINE` (`sqlite` for local development or `postgresql` for Supabase)
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT` (defaults to `5432`)
- `DB_SSLMODE` (defaults to `require` for PostgreSQL)
- `DB_CONN_MAX_AGE` (defaults to `60` seconds)
- `FRONTEND_ORIGIN` (comma-separated explicit CORS and CSRF trusted origins)
- `SESSION_COOKIE_SAMESITE` (`Lax` by default; `None` requires production HTTPS)
- `CACHE_URL` (required Redis URL for production shared login throttling; use `rediss://`)
- `LOGIN_RATE_LIMIT_MAX_ATTEMPTS` (defaults to `5`)
- `LOGIN_RATE_LIMIT_WINDOW_SECONDS` (defaults to `900`)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (server-side only, if required)
- Email provider credentials
- Error monitoring DSN

Never put database credentials or Supabase service-role keys in `VITE_*` variables or browser bundles.
Session authentication is cookie-based and does not use JWT. Keep the frontend and API on the same site where possible; use HTTPS and `SESSION_COOKIE_SAMESITE=None` only when a cross-site deployment requires it.
Local debug mode without `CACHE_URL` uses process-local memory for development and tests only. Production refuses to start without `CACHE_URL` and requires Redis TLS. Set edge/gateway limits as an additional control; configure trusted proxy handling before relying on client IP rate limits behind a load balancer.

### Local database setup

Copy `backend/.env.example` to `backend/.env`. The example selects `DB_ENGINE=sqlite`; with `DJANGO_DEBUG=True`, Django uses the separate `backend/dev.sqlite3` file. No command in this setup should target `backend/db.sqlite3`.

Run commands from `backend/` with its virtual environment active:

```powershell
python manage.py check
python manage.py showmigrations
python manage.py migrate --plan
python manage.py migrate
python manage.py test
```

`migrate` creates or updates only the database selected by the active environment. Review the engine and database name before applying it.

### Supabase PostgreSQL setup

Create or select a non-production Supabase project, then retrieve its PostgreSQL connection details from the Supabase dashboard. Set `DB_ENGINE=postgresql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in the backend environment. Set `DB_SSLMODE=require`; use the connection host and port provided for the selected direct or session-pooler connection. `DB_CONN_MAX_AGE` is optional.

Store actual values only in the ignored backend `.env` for local development or in the hosting provider's secret manager. The `.env.example` values are placeholders. Never put these variables in the frontend or expose them through `VITE_*`.

To verify connectivity without printing credentials, run from `backend/` after configuring a valid connection:

```powershell
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
```

No connection is attempted until PostgreSQL settings are explicitly configured.

### Production database safeguards

Set `DJANGO_DEBUG=False`, a generated `DJANGO_SECRET_KEY` of at least 50 characters, explicit non-wildcard `DJANGO_ALLOWED_HOSTS`, and complete PostgreSQL settings. Production rejects SQLite, placeholder database values, invalid ports, and PostgreSQL SSL modes that do not require TLS. Missing configuration raises an error rather than falling back to a local database.

The initial `accounts.User` model is the Django identity authority, uses a UUID key and normalized unique email, and must be present in the first project migration. Do not enable Supabase Auth as a second user store.

## 10.3 CI/CD pipeline

1. Pull request created.
2. Install locked dependencies.
3. Lint and type-check frontend/backend.
4. Run unit and API tests.
5. Build frontend.
6. Validate OpenAPI schema and migrations.
7. Merge after review.
8. Deploy to staging.
9. Run migrations and smoke tests.
10. Product owner approves production release.
11. Deploy production.
12. Verify health and monitor logs.

## 10.4 Database migration procedure

- Review migration files in code review.
- Back up production before risky migrations.
- Test migrations against a staging copy.
- Use backward-compatible expand/migrate/contract changes where possible.
- Run migration once as a controlled deployment step.
- Verify application health after migration.
- Document rollback or forward-fix plan.

## 10.5 Production checklist

- [ ] Domain and DNS configured.
- [ ] HTTPS certificate active.
- [ ] `DEBUG=False`.
- [ ] Allowed hosts and CORS/CSRF origins restricted.
- [ ] Secrets stored in host secret manager.
- [ ] Database credentials least privilege.
- [ ] Private storage and file authorization tested.
- [ ] Migrations applied.
- [ ] Static assets served correctly.
- [ ] Health and readiness checks pass.
- [ ] Error monitoring and logs configured.
- [ ] Backups enabled and restore tested.
- [ ] Admin accounts protected.
- [ ] Rollback plan documented.
- [ ] Owner approves release.

## 10.6 Cloud provider selection

Provider remains open. Evaluate:
- Django/Python runtime support.
- React static hosting support.
- Region and latency.
- Cost and scaling.
- Managed secrets and logs.
- Deployment rollback.
- PostgreSQL connection and pooling compatibility.
- Backup and restore options.
- Support and operational complexity.

Do not select a provider solely because it is popular; compare current pricing and requirements before committing.
