# 5. API Design and Endpoint Catalogue

**Status:** Proposed API contract. These routes are design examples, not deployed endpoints.

## 5.1 Standards

- Base path: `/api/v1/`
- Transport: HTTPS in staging/production.
- Format: JSON.
- Authentication: Django session authentication using HttpOnly cookies and CSRF tokens for unsafe requests. JWT is not used.
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
- `GET /api/auth/csrf/` (initialize the CSRF cookie/token)
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

Public self-registration is not available. Administrators create accounts through the protected `/api/accounts/` endpoint.

### Dashboard
- `GET /api/dashboard/summary/` (implemented; active Django session required)
- `GET /api/v1/dashboard/activity/` (planned; activity feed not implemented)

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
- `GET /api/accounts/` (implemented; admin permission required)
- `POST /api/accounts/` (implemented; admin permission required)
- `PATCH /api/accounts/{uuid}/` (implemented; admin permission required)

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

## 5.7 Implemented authentication foundation

The current foundation routes are implemented under `/api/` (the `/api/v1/` business API remains a future contract decision). The browser obtains a CSRF token from `/api/auth/csrf/`, sends it in `X-CSRFToken` for login, logout and account-management writes, and includes cookies with credentialed requests. The session and CSRF cookies are HttpOnly; production cookies require HTTPS. CORS and CSRF trust use explicit frontend origins and never wildcard origins.

`GET /api/auth/me/` requires an active authenticated session. Account list/create/update routes require a superuser or the Django `accounts.manage_users` permission. Role values are allowlisted as `admin` and `team`; API account creation never sets superuser status. There is no public registration route.
