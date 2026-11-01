# 10. Deployment and Environment Guide

## 10.1 Environment model

### Local development
- Developer-owned local frontend and backend.
- Isolated development database or Supabase development project.
- Test/sample data only.
- `.env` files excluded from Git.

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
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (server-side only, if required)
- Email provider credentials
- Error monitoring DSN

Never put database credentials or Supabase service-role keys in `VITE_*` variables or browser bundles.

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
