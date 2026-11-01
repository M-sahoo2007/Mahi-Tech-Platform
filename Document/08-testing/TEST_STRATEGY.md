# 8. Testing Strategy and Acceptance Tests

## 8.1 Test pyramid

1. Unit tests: domain rules, model methods, calculations and validators.
2. API tests: authentication, validation, response format and permissions.
3. Integration tests: PostgreSQL, storage adapters, PDF generation and notifications.
4. End-to-end tests: critical owner, staff and client journeys.
5. Security tests: authorization, upload restrictions, CSRF/CORS and secrets.
6. Acceptance tests: business owner validates realistic workflows.

## 8.2 Suggested tools

- Backend: pytest, pytest-django, Django test client.
- Frontend: Vitest, React Testing Library.
- Browser E2E: Playwright.
- API contract: OpenAPI schema validation.
- Static quality: Ruff, mypy where appropriate, ESLint and TypeScript compiler.
- Dependency checks: pip audit / Dependabot or equivalent, npm audit with triage.

Tool choices are proposed and may be adjusted by the technical lead.

## 8.3 Core test cases

| ID | Scenario | Expected result |
|---|---|---|
| TC-001 | Valid staff login | User receives valid authenticated session/token |
| TC-002 | Invalid password | Safe authentication error; no sensitive details |
| TC-003 | Inactive user login | Access denied |
| TC-004 | Client requests another client's project UUID | 404/403 according to policy; no data leakage |
| TC-005 | Client requests another client's file download | Access denied |
| TC-006 | Create lead and add follow-up | Lead and activity persist |
| TC-007 | Convert won lead twice | Duplicate conversion prevented |
| TC-008 | Create project for client | Project linked to correct client |
| TC-009 | Assign task to staff member | Assignment and activity recorded |
| TC-010 | Client reads internal-only project update | Update not returned |
| TC-011 | Calculate proposal with discount/tax | Server-calculated total follows approved rounding rules |
| TC-012 | Create invoice with invalid date range | Validation error |
| TC-013 | Allocate partial payment | Invoice balance decreases correctly |
| TC-014 | Allocate more than payment amount | Transaction rejected |
| TC-015 | Allocate more than invoice balance | Rejected unless approved credit/refund workflow |
| TC-016 | Upload oversized or disallowed file | Upload rejected |
| TC-017 | Generate invoice PDF | Correct client, number, line items and totals |
| TC-018 | Expense included in finance report | Summary reconciles to expense records |
| TC-019 | User lacks finance permission | Finance endpoint denied |
| TC-020 | Clean database migration | All migrations apply successfully |
| TC-021 | Restore backup in staging | Data is recoverable and application starts |
| TC-022 | Production configuration check | No unsafe debug/host/secret configuration |

## 8.4 Financial calculation testing

Use decimal arithmetic. Define and test:
- Quantity × unit price.
- Line-level discounts.
- Document-level discounts.
- Tax inclusive/exclusive behavior.
- Rounding precision and rounding mode.
- Partial payment allocation.
- Outstanding balance.
- Refund/credit note behavior if included.

All tax and currency rules require owner/accountant approval before implementation.

## 8.5 Definition of Done

A task is Done only when:
- Requirements and acceptance criteria are met.
- Code is reviewed.
- Unit/API tests pass.
- Permission and error cases are tested.
- Frontend loading/empty/error states are handled.
- Documentation is updated.
- No unresolved release-blocking defect remains.
- Evidence is linked in the progress tracker.
