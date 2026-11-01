# 6. UI/UX Specification

## 6.1 Design direction

- Professional corporate interface.
- Primary blue: `#1457D9`.
- Midnight black: `#111827`.
- White: `#FFFFFF`.
- Neutral grays for surfaces, borders and secondary text.
- Clear typography, consistent spacing and accessible contrast.
- Responsive desktop-first admin workspace with tablet/mobile adaptation.

## 6.2 Application areas

### Admin workspace
1. Login and password recovery.
2. Main dashboard.
3. CRM / leads.
4. Lead details and follow-up timeline.
5. Client list and client profile.
6. Projects list and project workspace.
7. Milestones and tasks.
8. Proposals and quotations.
9. Invoice list and invoice details.
10. Payments and receipts.
11. Expenses and finance.
12. Documents.
13. Team and roles.
14. Reports.
15. Notifications.
16. Settings and audit history.

### Client workspace
1. Client login.
2. Client dashboard.
3. My projects.
4. Project detail and approved updates.
5. Shared documents.
6. Proposals and decisions.
7. Invoices and payment history.
8. Feedback and requirements.
9. Profile and contact settings.

## 6.3 Navigation proposal

Admin sidebar:
- Overview
- CRM
- Clients
- Projects
- Proposals
- Invoices
- Payments
- Finance
- Documents
- Team
- Reports
- Notifications
- Settings

Client navigation:
- Overview
- Projects
- Documents
- Proposals
- Invoices
- Feedback
- Profile

## 6.4 Screen behavior standards

Every data screen should define:
- Loading state.
- Empty state with a useful next action.
- Error state and retry behavior.
- Form validation and field-level messages.
- Search, filters and pagination where appropriate.
- Confirmation for destructive/sensitive actions.
- Permission-aware controls.
- Responsive behavior.
- Accessible labels and keyboard navigation.

## 6.5 Key user journeys

### Lead to client
Capture lead → assign owner → follow up → qualify → send proposal → mark won → convert to client → create project.

### Project delivery
Create project → define scope → create milestones → assign tasks → update progress → share approved client update → complete project.

### Proposal to payment
Create proposal → validate line items → generate PDF → send → record acceptance → create invoice → record payment → allocate payment → reconcile balance.

### Expense recording
Create expense → select category → enter amount/date/vendor → attach receipt → save → include in finance summary.

### Client portal
Client signs in → server scopes records to client → client views approved project information → downloads authorized document → submits feedback.

## 6.6 UI component inventory

- App shell, sidebar, top navigation and breadcrumbs.
- KPI cards and charts.
- Data table with filters and pagination.
- Status badges and priority labels.
- Search and filter controls.
- Modal/drawer forms.
- Date and currency inputs.
- File upload component.
- Activity timeline.
- Confirmation dialog.
- Toast/notification system.
- Empty/loading/error states.
