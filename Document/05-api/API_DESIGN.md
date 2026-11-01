# 5. API Design and Endpoint Catalogue

**Status:** Proposed API contract. These routes are design examples, not deployed endpoints.

## 5.1 Standards

- Base path: `/api/v1/`
- Transport: HTTPS in staging/production.
- Format: JSON.
- Authentication: bearer JWT or secure cookie strategy as finalized.
- Pagination: page-number or cursor pagination; choose one consistently.
- Filtering and sorting: allowlisted query parameters only.
- Dates: ISO 8601 with timezone.
- Money: decimal strings in JSON to avoid binary floating-point ambiguity.
- IDs: UUID strings.
- API schema: OpenAPI generated from serializers/views.
- Never return password hashes, secrets or internal storage credentials.

## 5.2 Example success response

```json
{
  "data": {
    "id": "uuid",
    "name": "Example"
  },
  "meta": {
    "request_id": "request-id"
  }
}
```

## 5.3 Example paginated response

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 0,
    "total_pages": 0
  }
}
```

## 5.4 Example error response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "fields": {
      "email": ["Enter a valid email address."]
    },
    "request_id": "request-id"
  }
}
```

## 5.5 Endpoint catalogue

### Authentication
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/refresh/`
- `POST /api/v1/auth/logout/`
- `POST /api/v1/auth/password-reset/`
- `GET /api/v1/auth/me/`

### Dashboard
- `GET /api/v1/dashboard/summary/`
- `GET /api/v1/dashboard/activity/`

### CRM
- `GET /api/v1/leads/`
- `POST /api/v1/leads/`
- `GET /api/v1/leads/{id}/`
- `PATCH /api/v1/leads/{id}/`
- `POST /api/v1/leads/{id}/activities/`
- `POST /api/v1/leads/{id}/convert/`

### Clients
- `GET /api/v1/clients/`
- `POST /api/v1/clients/`
- `GET /api/v1/clients/{id}/`
- `PATCH /api/v1/clients/{id}/`
- `GET /api/v1/clients/{id}/contacts/`
- `POST /api/v1/clients/{id}/contacts/`

### Projects and tasks
- `GET /api/v1/projects/`
- `POST /api/v1/projects/`
- `GET /api/v1/projects/{id}/`
- `PATCH /api/v1/projects/{id}/`
- `GET /api/v1/projects/{id}/milestones/`
- `POST /api/v1/projects/{id}/milestones/`
- `GET /api/v1/tasks/`
- `POST /api/v1/tasks/`
- `PATCH /api/v1/tasks/{id}/`
- `POST /api/v1/projects/{id}/updates/`

### Proposals
- `GET /api/v1/proposals/`
- `POST /api/v1/proposals/`
- `GET /api/v1/proposals/{id}/`
- `POST /api/v1/proposals/{id}/send/`
- `POST /api/v1/proposals/{id}/accept/`
- `POST /api/v1/proposals/{id}/reject/`
- `GET /api/v1/proposals/{id}/pdf/`

### Billing and payments
- `GET /api/v1/invoices/`
- `POST /api/v1/invoices/`
- `GET /api/v1/invoices/{id}/`
- `POST /api/v1/invoices/{id}/issue/`
- `GET /api/v1/invoices/{id}/pdf/`
- `GET /api/v1/payments/`
- `POST /api/v1/payments/`
- `POST /api/v1/payments/{id}/allocations/`

### Finance
- `GET /api/v1/expenses/`
- `POST /api/v1/expenses/`
- `PATCH /api/v1/expenses/{id}/`
- `GET /api/v1/finance/summary/`

### Documents
- `POST /api/v1/documents/`
- `GET /api/v1/documents/{id}/`
- `POST /api/v1/documents/{id}/download-link/`
- `DELETE /api/v1/documents/{id}/`

### Client portal
- `GET /api/v1/portal/summary/`
- `GET /api/v1/portal/projects/`
- `GET /api/v1/portal/invoices/`
- `GET /api/v1/portal/proposals/`
- `POST /api/v1/portal/feedback/`

### Reports and administration
- `GET /api/v1/reports/leads/`
- `GET /api/v1/reports/projects/`
- `GET /api/v1/reports/finance/`
- `GET /api/v1/admin/users/`
- `POST /api/v1/admin/users/invite/`
- `PATCH /api/v1/admin/users/{id}/roles/`

## 5.6 API security requirements

- Validate authentication and permission for every endpoint.
- Scope client querysets before object retrieval.
- Use serializers for input validation.
- Apply rate limits to authentication and sensitive actions.
- Prevent mass assignment by allowlisting writable fields.
- Use transactions for invoice/payment allocation operations.
- Do not trust totals sent by the browser; calculate totals on the server.
- Return safe errors without stack traces or secrets.
- Log request IDs and security-relevant events.
