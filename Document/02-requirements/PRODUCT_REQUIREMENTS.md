# 2. Product Requirements Document (PRD)

**Version:** 1.0 | **Status:** Draft baseline for owner approval

## 2.1 Users and roles

### Owner / Super Admin
- Configure the platform and business settings.
- Manage users, roles and permissions.
- Access business records and reports.
- Review audit events and approve sensitive changes.

### Operations Admin
- Manage leads, clients, projects, documents and routine client workflows.
- Access only finance functions granted by the owner.

### Project Manager
- Manage assigned projects, milestones, tasks, team assignments and client-visible updates.

### Team Member / Developer
- View assigned projects and tasks.
- Update task progress and add permitted work notes/files.

### Finance Manager
- Manage proposals where authorized, invoices, payment records, expenses and financial summaries.

### Client
- Access only the client organization and records explicitly assigned to their account.
- View approved project updates and shared documents.
- Review proposals and invoices.
- Submit requirements and feedback.

## 2.2 Functional requirements

### FR-001 Authentication and account lifecycle
- Secure login and logout.
- Staff invitation and activation/deactivation.
- Password reset and account recovery.
- Session/token lifecycle and revocation.
- Role and permission assignment.
- Audit sensitive access changes.

### FR-002 Dashboard
- Lead, client, project and task counts.
- Upcoming deadlines and overdue work.
- Invoice totals, collected payments and outstanding balances.
- Recent activity.
- Role-specific visibility.
- Dashboard figures reconcile to source records.

### FR-003 CRM
- Lead create, view, edit, archive and search.
- Contact and business details.
- Lead source and service interest.
- Pipeline stages: New, Contacted, Qualified, Proposal Sent, Negotiation, Won, Lost.
- Follow-up date, owner, notes and activity history.
- Convert a won lead to a client without losing history.
- Prevent duplicate conversion.

### FR-004 Client management
- Client organization/profile and multiple contacts.
- Business details and contact channels.
- Internal notes and relationship history.
- Linked projects, proposals, invoices and documents.
- Search, filter, archive and controlled export.
- Duplicate detection/merge policy.

### FR-005 Project management
- Project linked to a client.
- Service type, scope, budget, start date, due date, priority and status.
- Project manager and team members.
- Milestones and completion dates.
- Progress and project updates.
- Client visibility flag for updates.

### FR-006 Task management
- Tasks and optional subtasks.
- Project and milestone association.
- Assignee, creator, priority, status and due date.
- Comments/activity history.
- Overdue indicators.
- Permission checks on assignment and status changes.

### FR-007 Proposals and quotations
- Create proposal/quotation with line items.
- Quantity, unit, unit price, discounts and tax treatment.
- Draft, sent, accepted, rejected and expired states.
- Versioning or immutable snapshots for sent/accepted documents.
- PDF generation and download.
- Link accepted proposal to project/invoice.

### FR-008 Invoices
- Unique invoice number.
- Client and optional project association.
- Issue date, due date, currency, line items and totals.
- Draft, sent, partially paid, paid, overdue, void/cancelled statuses.
- PDF generation.
- Payment history and outstanding balance.

### FR-009 Payments
- Record payment date, amount, currency, method and reference.
- Support partial payments.
- Allocate payment amounts to invoices.
- Prevent invalid over-allocation.
- Generate receipt.
- Do not store card numbers or payment credentials.

### FR-010 Finance
- Expense categories and expense records.
- Vendor/payee, amount, currency, date, method and receipt.
- Collected income, expenses and receivables.
- Clearly distinguish invoiced revenue from cash collected.
- Date/category/client filters.
- Reconcile summaries with invoices, allocations and expenses.

### FR-011 Documents
- Private client/project document uploads.
- Generated proposal, quotation, invoice and receipt PDFs.
- File metadata and ownership.
- File size/type validation.
- Authorized download via backend-controlled access or short-lived signed URLs.
- Audit upload and deletion events.

### FR-012 Client portal
- Client-specific dashboard.
- View own profile and projects.
- View only client-visible updates.
- Access shared documents, proposals and invoices.
- Submit requirements and feedback.
- No access to other clients' records, files or identifiers.

### FR-013 Team management
- Staff profile and active status.
- Role assignment.
- Project membership and task assignments.
- Workload visibility.
- Payroll/attendance are excluded from initial release.

### FR-014 Notifications
- In-app assignment and deadline notifications.
- Proposal and payment event notifications.
- Email notifications after sender/domain and delivery workflow are configured.
- No sensitive data leakage in notifications.

### FR-015 Reports
- Lead pipeline and conversion.
- Client growth.
- Project status and overdue tasks.
- Invoice and receivables.
- Payment collections.
- Expenses and operating summary.
- CSV/PDF export with access controls.

### FR-016 Audit
- Actor, action, object type/id, timestamp and safe metadata.
- Audit role changes, login/security events, invoice/payment changes and client access.
- Never log passwords, tokens, secret keys or full sensitive file contents.

## 2.3 Non-functional requirements

- Security: HTTPS, secure configuration, CSRF, strict CORS, authorization, rate limiting and dependency updates.
- Privacy: data minimization, retention rules and least-privilege access.
- Reliability: managed backups and tested restore.
- Performance: pagination, indexes and query optimization.
- Accessibility: keyboard support, labels, focus visibility and contrast.
- Responsive design: desktop, tablet and mobile browser.
- Maintainability: typed frontend, modular backend, tests and documented APIs.
- Observability: health checks, structured logs and error monitoring.
- Portability: version-controlled source and documented deployment.

## 2.4 Acceptance criteria

- A lead can be captured, followed up and converted to a client.
- A client can have projects and contacts.
- A project manager can create milestones and assign tasks.
- A proposal can be created, versioned, sent and accepted.
- An invoice can receive multiple partial payments.
- Finance summaries reconcile to source transactions.
- Client A cannot read or download Client B's data.
- All critical workflows have automated tests.
- Production uses HTTPS, managed secrets, backups and monitoring.
- A backup restore is demonstrated in non-production.
- Owner signs the release checklist.

## 2.5 Business rules requiring approval

- Default currency and supported currencies.
- GST/tax rules, inclusive/exclusive pricing and rounding.
- Invoice numbering and financial-year convention.
- Proposal validity and approval rules.
- Refunds, credit notes and payment reversal policy.
- Client organization/contact access model.
- Data retention and deletion policy.
