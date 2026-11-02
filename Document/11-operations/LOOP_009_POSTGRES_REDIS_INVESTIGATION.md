# Loop 009: PostgreSQL Test Database and Redis Development Plan

**Status:** Investigation complete; no infrastructure or database changes made.  
**Date:** 2026-11-01

## Executive summary

- `test_postgres` exists, is owned by `postgres`, is approximately 8.05 MiB, and contains only Django account/auth/admin/session/content-type/migration tables. No CRM, client, project, billing, or other business tables were found.
- The database has 19 Django migration records through `accounts.0001_initial`. The repository now has later account migrations, so this test database is behind the current local migration set; it was not changed.
- No active `test_postgres` sessions were visible to the configured database role during inspection. No application names or connection users were therefore reported.
- The database appears safe to retain as test infrastructure. No cleanup is proposed or performed; any deletion requires separate owner approval.
- Docker Compose is installed, but the Docker daemon is unavailable. WSL2 is present, with Ubuntu and `docker-desktop` stopped. No local Redis listener or `CACHE_URL` is configured.
- The code already supports `django-redis`; development currently uses LocMem because `CACHE_URL` is absent. Production settings require a shared `rediss://` cache.

## PostgreSQL investigation

All statements were executed in read-only transactions. Queries were limited to PostgreSQL catalogs, Django migration metadata, and approximate table statistics. No application records, passwords, connection strings, or database credentials were retrieved or printed. No schema writes, migration commands, connection termination, ownership changes, or cleanup commands were run.

### Database and connection facts

| Finding | Result |
|---|---|
| `test_postgres` exists | Yes |
| Database owner | `postgres` |
| Connection allowed | Yes |
| Size | 8,443,571 bytes (8,246 kB, approximately 8.05 MiB) |
| Active sessions visible to the configured role | None |
| Active-session application names/users | None; no session rows were visible |
| Cleanup | Not performed; owner explicitly prohibited modification/deletion |

`pg_stat_activity` visibility depends on the inspecting role. The query returned no visible sessions at inspection time; it does not prove that a more privileged role would see no hidden session metadata.

### Schemas

| Schema | Owner |
|---|---|
| `information_schema` | `supabase_admin` |
| `pg_catalog` | `supabase_admin` |
| `pg_toast` | `supabase_admin` |
| `public` | `pg_database_owner` |

### Tables and views

All listed tables are owned by `postgres`. No user views were present.

| Table | Approximate live rows |
|---|---:|
| `accounts_user` | 0 |
| `accounts_user_groups` | 0 |
| `accounts_user_user_permissions` | 0 |
| `auth_group` | 0 |
| `auth_group_permissions` | 0 |
| `auth_permission` | 24 |
| `django_admin_log` | 0 |
| `django_content_type` | 6 |
| `django_migrations` | 19 |
| `django_session` | 0 |

Counts are PostgreSQL `pg_stat_user_tables.n_live_tup` statistics, which are approximate and may be stale. No table rows were selected. The table inventory contains Django identity/authentication/test infrastructure only; no business-module tables were found. Based on that structure and the zero estimates for user/session/admin-log tables, the database appears to be safe to retain. Exact row counts and private records were intentionally not inspected.

### Applied migration records

`django_migrations` exists in `public`. The following 19 migration records were returned; timestamps are rendered in UTC.

| App | Migration | Applied (UTC) |
|---|---|---|
| `accounts` | `0001_initial` | 2026-11-01 13:37:24 |
| `admin` | `0001_initial` | 2026-11-01 13:37:25 |
| `admin` | `0002_logentry_remove_auto_add` | 2026-11-01 13:37:25 |
| `admin` | `0003_logentry_add_action_flag_choices` | 2026-11-01 13:37:26 |
| `auth` | `0001_initial` | 2026-11-01 13:37:06 |
| `auth` | `0002_alter_permission_name_max_length` | 2026-11-01 13:37:07 |
| `auth` | `0003_alter_user_email_max_length` | 2026-11-01 13:37:07 |
| `auth` | `0004_alter_user_username_opts` | 2026-11-01 13:37:09 |
| `auth` | `0005_alter_user_last_login_null` | 2026-11-01 13:37:11 |
| `auth` | `0006_require_contenttypes_0002` | 2026-11-01 13:37:13 |
| `auth` | `0007_alter_validators_add_error_messages` | 2026-11-01 13:37:13 |
| `auth` | `0008_alter_user_username_max_length` | 2026-11-01 13:37:14 |
| `auth` | `0009_alter_user_last_name_max_length` | 2026-11-01 13:37:15 |
| `auth` | `0010_alter_group_name_max_length` | 2026-11-01 13:37:16 |
| `auth` | `0011_update_proxy_permissions` | 2026-11-01 13:37:16 |
| `auth` | `0012_alter_user_first_name_max_length` | 2026-11-01 13:37:18 |
| `contenttypes` | `0001_initial` | 2026-11-01 13:36:42 |
| `contenttypes` | `0002_remove_content_type_name` | 2026-11-01 13:36:48 |
| `sessions` | `0001_initial` | 2026-11-01 13:37:28 |

The repository also has `accounts.0002_alter_user_options` and `accounts.0003_auditevent`; neither appears in this database. No migration was run against it.

### Permission limitations and retention decision

The database, schema, table-owner, migration, and approximate statistics queries succeeded. No elevated workaround was attempted. Connection visibility can be role-limited as noted above. The existing metadata is sufficient to classify this as Django test/auth infrastructure with no business tables. **Recommendation: retain `test_postgres` unchanged.** If the owner later requests cleanup, first obtain explicit approval and repeat a fresh connection/session check immediately before any destructive action.

## Development environment findings

| Component | Verified state |
|---|---|
| Windows | Windows 11 Home Single Language, build 26300 |
| Docker CLI | 29.9.2 |
| Docker daemon | Unavailable; named pipe for Docker Desktop Linux engine was absent |
| Docker Compose | v5.6.1 installed |
| WSL2 | Available; default version 2 |
| WSL distributions | `Ubuntu` and `docker-desktop` are stopped |
| Docker Desktop service | No `com.docker.service` entry was returned |
| Compose files | None found in the repository |
| Redis listener | No local listener on port 6379 |
| `redis-server` executable | Not found on PATH |
| `CACHE_URL` | Absent from process environment and `backend/.env` |
| Current Django cache | `LocMemCache`, because `DEBUG=True` and no `CACHE_URL` is configured |
| Redis dependencies | `django-redis` 6.0.0 and `redis` 8.1.0 installed; `django-redis>=5.4,<7` declared in backend requirements |
| Throttle defaults | 5 failed attempts per key per 900 seconds |

The Docker client/Compose binaries are available, but a Compose configuration cannot be started or health-checked until the Docker Desktop engine is available. Redis was not installed or started during this loop.

## Recommended local Redis architecture

Run Redis in Docker Desktop for local development only. Bind its published port to loopback, attach it to a private internal Docker network, require a locally generated password, and omit persistent storage: login-throttle keys expire, and losing development counters on restart is acceptable. Set a memory ceiling with `noeviction`; if Redis cannot accept a counter, the application already fails closed with a generic 503. Do not mount or pass the entire backend `.env` into the Redis container; pass only the Redis-specific password variable.

If Django remains a host process, it uses the loopback-published port. If Django is later containerized, attach it to the same private network, address Redis by service name, and remove the host port publication.

### Docker Compose proposal (not created or run)

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    environment:
      REDIS_DEV_PASSWORD: ${REDIS_DEV_PASSWORD:?Set a local development password}
    command:
      - sh
      - -c
      - exec redis-server --requirepass "$$REDIS_DEV_PASSWORD" --save "" --appendonly no --maxmemory 64mb --maxmemory-policy noeviction
    ports:
      - "127.0.0.1:6379:6379"
    networks:
      - redis-private
    healthcheck:
      test:
        - CMD-SHELL
        - REDISCLI_AUTH="$$REDIS_DEV_PASSWORD" redis-cli ping | grep -q PONG
      interval: 5s
      timeout: 3s
      retries: 5

networks:
  redis-private:
    internal: true
```

Before implementation, select and pin a currently supported Redis image/tag (and preferably digest), create a local ignored Redis env file, and confirm the chosen Compose network/loopback port behavior on this Docker Desktop installation. No password value belongs in this report, Git, frontend configuration, or command output.

## Django cache configuration and environment proposal

The Django configuration is already wired to `django-redis.cache.RedisCache` when `CACHE_URL` is supplied. With debug mode and no URL it uses process-local `LocMemCache`; production refuses startup without `CACHE_URL` and requires `rediss://`. The application throttle uses the standard Django cache API, hashes email/IP keys with HMAC, and fails closed on cache errors.

For a host-run backend, use backend-only ignored environment values similar to:

```dotenv
CACHE_URL=redis://:<URL-encoded-local-password>@127.0.0.1:6379/0
LOGIN_RATE_LIMIT_MAX_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=900
```

For a Django container on the Compose network, use the `redis` service name instead of `127.0.0.1`. Keep all cache URLs/passwords out of `VITE_*` settings. Use separate Redis services, credentials, and network boundaries for development, staging, and production; a Redis logical database number alone is not an environment security boundary.

## Redis validation plan

1. Start the local Redis service only after Docker Desktop is running; wait for its health check and verify authenticated `PING` without printing the secret.
2. From Django, exercise cache set/get/delete and assert the stored test value round-trips.
3. Run two separate Django processes against the same Redis and same cache namespace. Send failures to process A, then verify process B observes the same throttle and returns the expected generic `429`.
4. Verify expiry recovery using a short test window and verify successful-login reset behavior.
5. Stop Redis and confirm login fails closed with the documented generic `503`; restore Redis and verify requests recover.
6. Restart Redis and verify expected counter behavior. With the proposed non-persistent local cache, counters reset on restart; document that development behavior.
7. Verify development/staging/production use distinct cache endpoints, credentials, and key namespaces. Never run these tests against production Redis.
8. Re-run Django checks and the complete authentication suite. Keep unit tests on an isolated local cache and label Redis-dependent tests as integration tests.

## Production Redis requirements

- Shared Redis-compatible service reachable by all Django workers.
- `rediss://` with certificate verification and authenticated credentials.
- Private network access, firewall allowlisting, and no public Redis listener.
- Secret-manager delivery; credentials restricted to backend workloads and rotated.
- Memory limits, eviction policy chosen to preserve security counters, connection/pool limits, health monitoring, alerts, and documented recovery/restart behavior.
- Trusted reverse-proxy configuration so IP-based throttling uses the real client address rather than an untrusted forwarded header.
- Separate Redis deployments/credentials across environments. Do not claim production rate limiting is active until shared TLS Redis is provisioned and cross-process tests pass.

## Assumptions and unresolved decisions

- The `n_live_tup` row estimates are approximate PostgreSQL statistics, not exact table counts. No private records were read.
- The visible connection inventory may be limited by PostgreSQL role permissions; no active session rows were visible to the current role.
- No Redis service, Docker daemon, or `CACHE_URL` is currently available locally.
- Confirm the Redis image version/digest, whether Django will remain host-run, where the ignored local Redis password will live, and the shared-cache endpoint/secret-management approach for each hosted environment.
- `test_postgres` should remain untouched unless the owner explicitly approves a separate cleanup task.

## Recommended Loop 010

1. Start Docker Desktop and confirm WSL2 integration is healthy.
2. Obtain approval for the Compose file and local Redis env-file convention.
3. Add the Redis development Compose configuration and document start/stop commands without coupling it to Supabase.
4. Run cache connectivity and cross-process throttle integration tests against that local Redis instance.
5. Reassess production Redis service, TLS, credentials, networking, monitoring, and trusted-proxy settings before claiming production-grade throttling.
6. Keep `test_postgres` intact unless a new owner-approved cleanup request is made.
