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

- Use a custom Django user model from the first migration.
- Use a maintained JWT implementation if bearer tokens are selected.
- Define access-token lifetime and refresh rotation/revocation.
- Consider secure HttpOnly cookies with CSRF protection for browser auth.
- Do not store long-lived tokens casually in localStorage.
- Rate-limit login and password reset.
- Provide account deactivation and session/token revocation.
- Consider MFA for owner/admin accounts.

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
