# 9. Development Process and Roadmap

## 9.1 Development stages

| Stage | Name | Deliverables | Exit gate |
|---|---|---|---|
| 0 | Planning and architecture | Approved PRD, architecture, ERD, UI map, decisions | Owner sign-off |
| 1 | Repository and foundations | Clean repo, React shell, Django API shell, env, CI | Both apps run; CI passes |
| 2 | Database foundation | Supabase PostgreSQL connection, custom user, migrations | Clean migration and DB tests |
| 3 | Authentication and access | Login, roles, client links, object permissions | Permission tests pass |
| 4 | Design system and dashboard | App shell, navigation, dashboard base | UI review approved |
| 5 | CRM and clients | Leads, follow-ups, client profiles | Lead-to-client workflow passes |
| 6 | Projects and tasks | Projects, milestones, tasks, updates | Delivery workflow passes |
| 7 | Proposals, invoices and payments | Commercial docs, PDFs, payment allocations | Financial calculation tests pass |
| 8 | Finance and documents | Expenses, private files, summaries | Reconciliation and file tests pass |
| 9 | Client portal | Client dashboard and controlled records | Cross-client isolation passes |
| 10 | Team, notifications and reports | Team, alerts, reports and exports | Acceptance tests pass |
| 11 | Hardening and cloud launch | Security, performance, backup, deployment | Release checklist signed |

AI Development Studio is not part of this roadmap.

## 9.2 Repository layout

```text
mahi-tech-platform/
  frontend/
  backend/
  docs/
  infrastructure/
  scripts/
  .github/
  README.md
  .gitignore
```

## 9.3 Git workflow

- `main`: production-ready branch.
- `develop`: integration branch if the team chooses a GitFlow model.
- `feature/<short-name>`: feature work.
- `fix/<short-name>`: bug fixes.
- `hotfix/<short-name>`: urgent production fixes.

Require pull requests, review, automated checks and protected main branch. Choose either trunk-based development or GitFlow and document one consistent workflow.

## 9.4 Issue/task template

Every task should include:
- ID and title.
- Business purpose.
- Scope and exclusions.
- Owner.
- Priority.
- Dependencies.
- Acceptance criteria.
- Test plan.
- Status.
- Evidence/PR/commit.
- Remaining work and blockers.

## 9.5 Status definitions

- Not Started.
- In Progress.
- Blocked.
- Implemented — Not Verified.
- Testing.
- Done.
- Deferred / Out of Scope.

Never mark a feature Done merely because source code exists.

## 9.6 Suggested priority model

- P0: security, data integrity, release blocker.
- P1: required first-release capability.
- P2: important but can follow core workflows.
- P3: enhancement or later release.

## 9.7 Change control

Any scope or architecture change must include:
1. Requested change.
2. Reason/business value.
3. Impact on security, database, API, UI, schedule and cost.
4. Decision owner.
5. Updated documents and version history.
