# Mahi-Tech Platform - GitHub Copilot Instructions

## 1. Project Identity

Product Name: Mahi-Tech Platform

Business: Mahi-Tech Consultant & Services

Product Type: Business Management System

Purpose: Manage all internal agency operations from one platform.

Tagline: Your Vision. Our Technology.

Brand Colors:
- Primary Blue: #1457D9
- Midnight Black: #111827
- White: #FFFFFF

## 2. Project Objective

Build a complete, secure, scalable and maintainable business management platform for Mahi-Tech Consultant & Services.

The first release is for internal agency use.

A client portal is included in the approved scope, but it must only be enabled after authorization and client data isolation tests pass.

This is a completely new implementation. Do not copy source code from the old project.

## 3. Approved Technology Stack

Frontend:
- React
- TypeScript
- Vite

Backend:
- Python
- Django
- Django REST Framework

Database:
- Supabase PostgreSQL
- Django ORM
- Django migrations

Other:
- REST APIs
- Private document storage
- PDF generation
- Automated testing
- Git and GitHub
- Cloud deployment

Do not change the approved architecture without asking for permission.

## 4. Required Software Modules

Build these modules:

1. Dashboard and business analytics.
2. CRM and lead management.
3. Client and contact management.
4. Project management.
5. Tasks and milestones.
6. Proposals and quotations.
7. Invoices and payment tracking.
8. Finance and expense management.
9. Document management.
10. Client portal.
11. Team and role management.
12. Notifications and reminders.
13. Reports and exports.
14. Audit logs.
15. Security and administration.

## 5. Explicitly Excluded Features

Do not implement:
- AI Development Studio.
- AI code generation.
- AI website builder.
- Online code editor.
- Generated-code execution.
- Public SaaS self-service registration.
- Native mobile applications.
- Full statutory accounting replacement.

AI Development Studio is a separate project handled by another team.

## 6. Engineering Standards

- Use modular and maintainable architecture.
- Write reusable React components.
- Use TypeScript types.
- Follow Django application conventions.
- Use serializers for API validation.
- Keep business logic separate from views where practical.
- Use environment variables for configuration.
- Never expose secrets in frontend code.
- Never expose Supabase service-role keys in the browser.
- Enforce server-side authentication and authorization.
- Validate all user inputs.
- Use secure password handling.
- Protect client data from unauthorized access.
- Use decimal-safe financial calculations.
- Maintain audit logs for important business actions.

## 7. Loop Engineering Workflow

For every feature, follow this loop:

1. PLAN: Understand requirements and define acceptance criteria.
2. INSPECT: Review existing files and dependencies.
3. DESIGN: Plan database, API and frontend changes.
4. IMPLEMENT: Write the required code.
5. TEST: Run automated tests and builds.
6. DEBUG: Investigate and fix errors.
7. REVIEW: Check security and code quality.
8. DOCUMENT: Update documentation and progress.
9. APPROVE: Present results for human approval.

Repeat the loop until the feature passes all acceptance criteria.

## 8. Development Rules

- Work on one small feature at a time.
- Do not generate the entire application in one operation.
- Do not delete existing files without permission.
- Do not execute destructive database commands without approval.
- Do not modify unrelated modules.
- Do not install unnecessary dependencies.
- Explain important changes before implementation.
- Never claim a test passed unless it actually ran successfully.
- Never mark a feature complete without evidence.
- Ask for approval before major architectural changes.

## 9. Testing Requirements

Test:
- Authentication.
- Role-based permissions.
- API validation.
- Client data isolation.
- Business workflows.
- Financial calculations.
- Document access.
- Error handling.
- Frontend builds.
- Backend integration.

Fix failed tests before marking a feature complete.

## 10. Database Requirements

- Use Django ORM and migrations.
- Use Supabase PostgreSQL for the approved database architecture.
- Keep development, staging and production environments separate.
- Protect production data.
- Never reset or delete database data without approval.
- Use backups and verify restoration procedures.

## 11. Security Requirements

- Keep credentials outside source code.
- Use secure environment variables.
- Use HTTPS in production.
- Apply least-privilege permissions.
- Restrict private document access.
- Prevent cross-client data exposure.
- Validate authorization on every protected API.
- Review authentication and financial workflows carefully.

## 12. Deployment Requirements

Prepare:
- Production configuration.
- Secure environment variables.
- Database backups.
- Logging and monitoring.
- Deployment documentation.
- Rollback instructions.
- Testing and security checklists.

## 13. Project Completion Rules

The platform is complete only when:
- All approved modules are implemented.
- Frontend and backend integrations work.
- Database migrations are correct.
- Authentication and authorization work.
- Client data isolation is verified.
- Financial calculations pass tests.
- Automated tests pass.
- Security checks are completed.
- Backups and restoration are verified.
- Production deployment succeeds.
- Documentation is updated.

Always report honestly:
- Completed work.
- Pending work.
- Failed tests.
- Known issues.
- Security concerns.

Never silently change the approved project scope.