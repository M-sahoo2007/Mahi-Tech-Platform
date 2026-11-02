# Loop 012: CRM and Lead Management Design

**Status:** Part A design only; awaiting owner review and approval before implementation.  
**Date:** 2026-11-02

## Scope and work completed

This report defines the proposed CRM/Lead Management foundation and its implementation sequence. Part B has not started. No Python/TypeScript source, models, serializers, routes, migrations, databases, Redis settings, or frontend files were changed in this loop. No migration command or database query was run.

## Files inspected

- `.github/copilot-instructions.md`
- `Document/02-requirements/PRODUCT_REQUIREMENTS.md`
- `Document/03-architecture/SOFTWARE_ARCHITECTURE.md`
- `Document/04-database/DATABASE_ERD.md`
- `Document/05-api/API_DESIGN.md`
- `Document/06-ui-ux/UI_UX_SPECIFICATION.md`
- `Document/07-security/SECURITY_AND_PRIVACY.md`
- `Document/09-development/DEVELOPMENT_PROCESS_AND_ROADMAP.md`
- `Document/11-operations/LOOP_009_POSTGRES_REDIS_INVESTIGATION.md`
- `Document/11-operations/LOOP_010_REDIS_IMPLEMENTATION.md`
- `Document/12-development/LOOP_011_APPLICATION_SHELL_DASHBOARD.md`
- Backend settings, custom user/audit models and migrations, account views/URLs, API views/URLs/serializers/tests
- Frontend `App.tsx`, `authApi.ts`, styles, package manifest and environment example
- Current Git status and backend app/migration directory structure

The worktree already contains uncommitted changes from earlier loops. Part A made no source changes beyond creating this report; those existing changes are not attributed to Loop 012.

## Existing architecture findings

- Django and DRF are a modular monolith; `accounts.User` is the identity authority and uses a UUID key plus normalized unique email.
- Browser authentication uses Django sessions, HttpOnly cookies, CSRF, explicit origins, and Redis-backed login throttling when configured. No Supabase Auth, JWT, or public registration is present.
- Admin access is determined by Django superuser status or `accounts.manage_users`. The existing `Team` Django group is used for team membership and dashboard counts.
- `AuditEvent` currently records account management events. It has actor, optional target user, action, safe JSON metadata, and timestamp, but no generic object reference.
- The API currently exposes account/auth, health, and dashboard summary routes under `/api/`. No CRM, clients, leads, sources, or lead-activity apps/models/endpoints exist.
- The React app currently implements login, the authenticated shell/dashboard, and admin team account management. Business-module navigation is disabled and labeled planned. No router dependency is present.
- The database ERD proposes `Client`, `LeadSource`, `Lead`, and `LeadActivity`, but labels the ERD a logical proposal requiring approval before migrations. No migration was generated or applied for CRM in this loop.

## CRM requirements

Implement leads with create, list/detail, update, archive, assigned owner, contact details, source, service interest, status, priority, estimated value/currency, follow-up date, notes, activity history, filtering, search, allowlisted sorting, and pagination.

Statuses are `New`, `Contacted`, `Qualified`, `Proposal Sent`, `Negotiation`, `Won`, and `Lost`. Priorities are proposed as `Low`, `Normal`, `High`, and `Urgent`.

Conversion must link a lead to either an explicitly selected existing client or a newly created client, preserve the lead and its history, and prevent a second conversion. No automatic duplicate merge is proposed.

## Proposed database design

All business records use UUID primary keys and timezone-aware timestamps. Monetary values use `DecimalField`; no floating-point money values. Fields marked nullable remain optional until a business rule requires them.

### `clients.Client` (conversion prerequisite only)

| Field | Proposed type / rule |
|---|---|
| `id` | UUID primary key |
| `display_name` | CharField, required |
| `legal_name` | CharField, optional |
| `primary_email` | EmailField, optional; normalized on write |
| `primary_phone` | CharField, optional |
| `status` | Active/archived choice; defaults active |
| `created_at`, `updated_at` | DateTimeField |
| `created_by` | FK to `accounts.User`, SET_NULL, optional |

This is only the smallest client identity needed for lead conversion and links. It does not imply a client-management UI or the rest of the clients module. **Owner approval is required to include this prerequisite model in the CRM migration sequence.**

### `crm.LeadSource`

| Field | Proposed type / rule |
|---|---|
| `id` | UUID primary key |
| `name` | CharField, required |
| `slug` | SlugField, unique |
| `is_active` | BooleanField, defaults true |
| `created_at` | DateTimeField |

Leads reference a source with `SET_NULL`; sources are deactivated rather than deleted after use. Initial source values and whether admins can manage them in the CRM UI require approval.

### `crm.Lead`

| Field | Proposed type / rule |
|---|---|
| `id` | UUID primary key |
| `contact_name` | CharField, required |
| `email` | EmailField, optional, normalized; indexed for candidate duplicate search, not unique |
| `phone` | CharField, optional, normalized for duplicate search |
| `company_name` | CharField, optional, indexed for search |
| `source` | FK to `LeadSource`, nullable, SET_NULL |
| `interested_service` | CharField (bounded length), optional; no service catalogue in this loop |
| `status` | Choice field; defaults `new` |
| `priority` | Choice field; defaults `normal` |
| `assigned_to` | FK to `accounts.User`, nullable, SET_NULL |
| `estimated_value` | DecimalField(12,2), nullable; must be non-negative |
| `currency` | CharField(3), nullable; required when `estimated_value` is set |
| `follow_up_date` | DateField, nullable |
| `notes` | TextField, blank |
| `created_by`, `updated_by` | FK to `accounts.User`, nullable, SET_NULL |
| `converted_client` | OneToOneField to `clients.Client`, nullable, PROTECT; unique conversion target |
| `converted_at`, `converted_by` | DateTimeField / FK to User, nullable |
| `archived_at` | DateTimeField, nullable; archive is soft, not deletion |
| `created_at`, `updated_at` | DateTimeField |

Proposed constraints: estimated value is null or non-negative; currency is non-null whenever value is set; converted client and converted timestamp are either both null or both set. Database uniqueness on the one-to-one converted-client reference and atomic row locking protect against duplicate conversion. Status and priority choices are validated by model/serializer and, where practical, database check constraints.

Proposed indexes:
- `(status, follow_up_date)` for pipeline/follow-up views.
- `(assigned_to, status, follow_up_date)` for owner work queues.
- `(priority, follow_up_date)` for prioritization.
- `created_at` and `updated_at` for sorting.
- Case-insensitive email and company search indexes only if query-plan tests justify them.

Email and phone are intentionally not unique: a prospect may be entered more than once and duplicate handling needs an explicit workflow.

### `crm.LeadActivity`

| Field | Proposed type / rule |
|---|---|
| `id` | UUID primary key |
| `lead` | FK to Lead, CASCADE; parent lead is archived, not hard-deleted |
| `actor` | FK to `accounts.User`, nullable, SET_NULL |
| `kind` | Choice: note, call, email, status change, assignment, follow-up, conversion |
| `summary` | Short required description |
| `details` | TextField, optional |
| `metadata` | JSONField, safe allowlisted fields only |
| `created_at` | DateTimeField, indexed |

Activity rows are append-only through the API. Passwords, session identifiers, tokens, full request bodies, and credentials are never stored. Status/owner/follow-up changes and conversion create activity records in the same transaction as the lead update.

### Central audit integration

The existing `AuditEvent` cannot strongly reference a Lead. Proposed option: add nullable `target_object_type` and UUID `target_object_id` fields plus an index, extend action choices for lead created/updated/archived/converted, and write those events transactionally. `LeadActivity` remains the user-facing CRM timeline. This is a schema change and needs approval as part of the migration plan. Do not silently overload unrelated `target_user` fields.

## Proposed API specification

Use current `/api/` routing conventions; do not introduce a new API version in this loop without approval.

| Method and route | Purpose |
|---|---|
| `GET /api/crm/leads/` | Paginated list; filters: status, priority, source, assigned user, follow-up range, archived; search across name/email/phone/company; allowlisted `ordering` |
| `POST /api/crm/leads/` | Create lead; server assigns creator and enforces owner assignment policy |
| `GET /api/crm/leads/{uuid}/` | Scoped lead detail |
| `PATCH /api/crm/leads/{uuid}/` | Allowlisted field update; records activity/audit |
| `POST /api/crm/leads/{uuid}/archive/` | Soft archive; records activity/audit |
| `GET /api/crm/leads/{uuid}/activities/` | Paginated, read-only activity history |
| `POST /api/crm/leads/{uuid}/activities/` | Add a validated note/call/email activity |
| `POST /api/crm/leads/{uuid}/convert/` | Convert once to an existing client ID or create the approved minimal client and link it atomically |
| `GET /api/crm/lead-sources/` | List active sources for form controls |

Responses should use the existing safe JSON conventions, expose only fields required by the interface, and never return user password/hash fields or audit secrets. Apply fixed maximum page sizes and allowlisted sort fields. Reject malformed UUIDs, unknown filter values, negative estimates, invalid email, unsupported state transitions, and unexpected writable fields.

## Permissions proposal

The current account model exposes Admin via superuser/`accounts.manage_users` and Team via the `Team` group. Recommended least-privilege policy, pending owner approval:

| Action | Admin | Team |
|---|---|---|
| List/search leads | All active and archived leads | Leads assigned to the current user |
| Create lead | Yes; may assign any active Team member | Yes; automatically assigned to self |
| Read/update lead | Any lead | Assigned leads only; owner cannot be changed by Team |
| Archive lead | Any lead | Assigned leads only |
| Manage lead sources | Yes | No |
| Convert a Won lead | Any lead | Assigned lead only |
| View activity | Same scope as lead | Same scope as lead |

Every queryset is scoped server-side before object lookup. A guessed UUID outside the user's scope returns 404. Frontend navigation/visibility is not an authorization control.

**Owner decision required:** confirm whether Team may see only assigned leads (recommended) or all leads. Confirm whether Team may archive/convert their assigned leads and whether only Admin can manage sources.

## Frontend plan

- Enable the existing `CRM & Leads` navigation item only after the backend endpoints are ready.
- Add a CRM landing with server-derived counts/pipeline only; never hard-code statistics.
- Add a paginated lead table with search, status/priority/source/owner/follow-up filters and allowlisted sort controls.
- Add lead detail/activity timeline and add/edit forms using serializer validation errors.
- Provide loading, empty, retry/error, archived, and permission-denied states.
- Add explicit conversion confirmation with existing-client selection or approved new-client fields; show duplicate candidates but do not merge records automatically.
- Keep session-cookie `credentials: include`, CSRF bootstrap/token header, and expired-session handling through existing `authApi.ts`.
- Use existing MCS colors and responsive shell; no new dependencies are currently justified.

## Migration plan (not executed)

No CRM migration exists today. Proposed dependency sequence, subject to owner approval:

1. `clients.0001_initial`: create only the minimal Client identity table required for Lead conversion; dependency on `accounts.0003_auditevent` if creator FK is included.
2. `accounts.0004_audit_object_target` (or equivalent): add generic target fields/index and CRM action choices to the existing audit model.
3. `crm.0001_initial`: create `LeadSource`, `Lead`, and `LeadActivity`; depend on `accounts.0003/0004` and `clients.0001`.
4. Review the generated migration graph/SQL; test apply/rollback on a disposable SQLite test DB and a non-production PostgreSQL project only after separate authorization.
5. Never run these migrations against Supabase or `test_postgres` during Part A.

The exact number/order of migrations can be adjusted when models are implemented. The original `backend/db.sqlite3` is not a target. Existing PostgreSQL test DB findings remain documented in Loop 009; no connection was made in this loop.

## Planned tests

- Anonymous list/detail/create/update/archive/activity/conversion denied.
- Admin can create, view, assign, update, archive, and manage sources.
- Team can create and access assigned leads only; cross-owner UUID lookup/update returns 404.
- Invalid email, status, priority, assignment, value/currency combination, unknown fields, and oversized pagination rejected.
- Search/filter/sort allowlists work; pagination bounds and stable ordering verified.
- Activity rows are recorded transactionally and do not contain password/session/token data.
- Conversion to existing/new client creates one link atomically; duplicate concurrent/repeated conversion is rejected; source history remains intact.
- Duplicate candidate detection is advisory and does not silently merge or block legitimate leads.
- Audit events contain actor/action/object reference and safe metadata.
- Existing login, CSRF, Redis throttle, dashboard, account permissions, and audit tests remain passing.
- Frontend tests cover loading/empty/error/permission states and form validation; browser tests cover lead CRUD and conversion after the APIs are approved and built.

## Risks and unresolved owner decisions

1. **Client conversion dependency:** there is no `clients.Client` model. Full conversion requires approval for a minimal Client schema/migration before or alongside CRM. Without it, only a conversion interface—not the requested conversion behavior—can be designed.
2. **Team visibility:** assigned-only access is recommended; the owner must approve the rule before implementing querysets.
3. **Currency:** choose whether estimated value must include a per-lead ISO currency code or use an owner-approved default. No default is assumed.
4. **Lead source values:** approve initial sources and whether source maintenance is Admin-only.
5. **Duplicate detection:** approve candidate matching thresholds/fields and whether warnings suffice. Automatic merges are excluded.
6. **Conversion rules:** confirm whether only `Won` leads convert and what client fields are required for an individual vs business lead.
7. **Audit design:** approve generic object references on `AuditEvent` versus relying only on `LeadActivity` for object history.
8. **Status transitions/archival:** define whether transitions are unrestricted or workflow-constrained and who can restore archived leads.
9. **Concurrency:** conversion and duplicate creation require transactional locking and database constraints; behavior must be validated on PostgreSQL after separate approval.

## Part A completion

- Requirements, existing architecture, API surface, frontend surface, database relationships, permissions proposal, API plan, frontend plan, migration graph, and test plan are documented.
- Only this Loop 012 design report is created in Part A.
- No source code, environment values, models, serializers, endpoints, migrations, databases, or Supabase resources were changed.
- **Part B is blocked pending owner approval** of the client conversion prerequisite, Team visibility/authorization policy, currency rule, lead-source policy, and central audit extension.
