# 11. Operations Runbook

## 11.1 Operational ownership

Assign named owners for:
- Application maintenance.
- Database and backup operations.
- Cloud infrastructure.
- Security and access reviews.
- Client support and data requests.
- Release approvals.

## 11.2 Monitoring

Monitor:
- Frontend and API availability.
- API error rate and latency.
- Database connection errors and capacity.
- Storage upload/download failures.
- Background notification failures.
- Backup success/failure.
- Authentication abuse and repeated failed logins.
- Disk, memory and CPU for hosted services.

## 11.3 Logging

Use structured logs with timestamp, severity, request ID, actor ID where appropriate, route and safe event metadata. Never log passwords, JWTs, cookies, database URLs, service keys or sensitive document contents.

## 11.4 Backup and restore

- Define database backup frequency and retention based on business risk.
- Confirm provider backup/PITR features and limits.
- Keep a documented restore procedure.
- Restore to a non-production environment periodically.
- Verify users, clients, projects, invoices and payment allocations after restore.
- Document recovery time and recovery point objectives after owner approval.

## 11.5 Incident response

1. Detect and classify incident.
2. Protect users and contain access.
3. Preserve logs and relevant evidence.
4. Notify project owner and assigned responders.
5. Restore service or data safely.
6. Assess privacy/security impact.
7. Communicate with affected parties as required.
8. Record root cause and corrective actions.
9. Update tests, controls and runbooks.

## 11.6 Routine maintenance

- Review dependency updates.
- Review user and admin access.
- Review failed logins and suspicious activity.
- Verify backup jobs.
- Check error and performance trends.
- Remove inactive accounts when approved.
- Review storage usage and retention.
- Test restore and deployment rollback.
- Keep documentation and changelog current.

## 11.7 Release and rollback

Each release must have:
- Version/commit reference.
- Change summary.
- Migration list.
- Test evidence.
- Backup status.
- Deployment owner.
- Rollback/forward-fix procedure.
- Post-release smoke test.

Do not assume a database migration can always be rolled back. Prefer tested forward fixes and backups for destructive schema/data changes.
