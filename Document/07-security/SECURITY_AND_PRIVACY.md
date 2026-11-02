# 7. Security and Privacy Specification

## 7.1 Security objectives

Protect customer data, project files, business financial records, user accounts and system availability. Apply least privilege and verify access on the backend.

## 7.2 Threat model

| Threat | Example | Required controls |
|---|---|---|
| Broken access control | Client changes a UUID to view another client's invoice | Server-side object scoping and negative tests |
| Credential theft | Stolen staff password/token | Strong password hashing, MFA where available, rate limits, revocation |
| Secret leakage | Database password committed to Git | Secret manager, `.env` ignored, secret scanning |
| Injection | Malicious input in search/form | ORM parameterization, validation, output encoding |
| CSRF/CORS errors | Cross-site request to authenticated API | CSRF controls, strict CORS allowlist |
| Unsafe uploads | Malicious or oversized file | Size/type checks, private storage, scanning policy |
| Financial tampering | Browser submits altered invoice total | Server recalculates totals; audit changes |
| Data loss | Accidental deletion or database failure | Backups, retention and restore drills |
| Information leakage | Stack trace or sensitive log content | Safe errors, log scrubbing, production debug off |

## 7.3 Authentication

- Django is the single identity and authorization authority; Supabase Auth is not enabled.
- The first-party browser uses Django Session Authentication with HttpOnly session cookies and CSRF protection on every state-changing request.
- CORS and CSRF trusted origins are explicit; wildcard origins are forbidden when credentials are enabled.
- Session/CSRF cookies use `SameSite=Lax` by default. Cross-site deployment may opt into `SameSite=None` only with HTTPS-secure cookies.
- Authentication state is not stored in localStorage or sessionStorage.
- Apply application login throttling through the shared Django cache; production requires a TLS Redis cache. Add edge/gateway throttles as defense in depth.
- Provide account deactivation and session/token revocation.
- Consider MFA for owner/admin accounts.
- The initial administrator is created manually with Django's `createsuperuser` command; the application does not seed a default administrator.
- Admins create and manage team accounts through permission-protected backend endpoints. Public registration is disabled.

Run `python manage.py createsuperuser` from `backend/` after applying migrations. Complete the interactive email/password prompts locally or in a secure administrative environment; do not put the password in source control, frontend configuration or shell history.

## 7.4 Authorization

- Define permissions per role, action and resource.
- Enforce authorization in DRF permission classes and queryset scoping.
- Client users are linked to one client organization/contact.
- Client APIs and file operations must scope to that organization.
- Test guessed UUIDs, changed IDs, list filters and download links.
- Frontend route guards are usability controls, not security controls.

## 7.5 Data protection

- TLS for browser, API, database and storage connections.
- Encrypt managed backups and storage according to provider capabilities.
- Store only necessary personal data.
- Define retention, archival and deletion policies.
- Restrict finance and client data to staff who need it.
- Never log passwords, tokens, service keys or complete sensitive documents.

## 7.6 Application hardening

- `DEBUG=False` in production.
- Correct `ALLOWED_HOSTS`.
- Strict CORS allowlist.
- Secure cookie settings and HSTS after HTTPS/proxy configuration is verified.
- CSRF protection for cookie-authenticated requests.
- Security headers.
- Dependency updates and vulnerability scanning.
- Rate limits on sensitive endpoints.
- Safe file upload/download.
- Database least-privilege credentials.
- Audit role changes, invoice/payment events and data access changes.
- The application login limiter keys counters by HMAC-hashed normalized email and remote address, returns a generic 429 response, and fails closed if cache operations fail. Development may use process-local memory only; production requires shared TLS Redis. Verify trusted proxy configuration so remote addresses are meaningful.

## 7.9 Future invitation and password reset workflow

This workflow is planned and is not implemented by the current account API:

1. An active administrator creates an invitation for a normalized email and an allowlisted role. Create an inactive account with no usable password; do not accept public registration.
2. Generate a cryptographically random, single-use token with a short expiry (recommended: 24 hours for invitations). Store only a keyed hash of the token and its expiry/consumed state. Send the raw token only through the configured email provider over HTTPS; never put it in logs or analytics.
3. The recipient follows a same-origin HTTPS link. The server verifies the token in constant time, checks expiry and unused state, validates the chosen password with Django validators, activates the account, consumes the token atomically, and records an audit event. Use CSRF protection for the password-setting POST.
4. A password-reset request for any email returns the same generic response and timing profile. Rate-limit by normalized email and remote address. For an eligible active account, issue a separate one-use token with a shorter expiry (recommended: 30 minutes), store only its keyed hash, and send it through email.
5. On reset, update the password hash, consume the token atomically, invalidate existing sessions by changing the authentication hash, and audit the reset without recording the token or password.

Before implementation, configure and verify the email provider, sender domain, token retention/cleanup, rate limits, delivery failure handling, and account enumeration tests. These flows must not create accounts without an administrator-issued invitation.

## 7.7 Privacy operations

Before launch, document:
- Privacy notice and contact point.
- Data collected and purpose.
- Data retention period.
- Data export and deletion request process.
- Backup retention and deletion limitations.
- Client/staff offboarding procedure.
- Incident notification procedure.

## 7.8 Security release gate

Production launch is blocked until:
- Cross-client isolation tests pass.
- Admin and finance permissions are reviewed.
- No secrets are present in repository history.
- Production deploy checks are reviewed.
- Upload/download controls pass.
- Backup restore succeeds.
- Known high-severity vulnerabilities are resolved or formally accepted.
