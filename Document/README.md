# Mahi-Tech Platform — Complete Software Documentation

**Version:** 1.0  
**Date:** 31 October 2026  
**Owner:** Mahi-Tech Consultant & Services  
**Project:** Scratch-built Business Management System

## Purpose

This repository contains the master documentation for designing, building, testing, securing, deploying and operating the Mahi-Tech Platform.

## Confirmed product decisions

- Build a new implementation from scratch. Do not copy/reuse the old project's source code.
- Frontend: React + TypeScript.
- Backend: Python + Django + Django REST Framework.
- Database: Supabase-managed PostgreSQL.
- Cloud deployment.
- First release: internal agency use.
- Client portal is in scope, gated by authorization and isolation tests.
- AI Development Studio is excluded and handled separately by the user's team.

## Documentation map

| Folder | Contents |
|---|---|
| `01-project-overview` | Product overview, glossary, scope |
| `02-requirements` | Product requirements, functional and non-functional requirements, acceptance criteria |
| `03-architecture` | System architecture, components, deployment topology, decisions |
| `04-database` | ER model, data dictionary, constraints and indexes |
| `05-api` | API standards, endpoint catalogue, response and error formats |
| `06-ui-ux` | Sitemap, screen catalogue, design system and user journeys |
| `07-security` | Threat model, security controls, privacy and access model |
| `08-testing` | Test strategy, test cases and release acceptance |
| `09-development` | Roadmap, workflow, branch strategy and progress tracking |
| `10-deployment` | Environment strategy, CI/CD and deployment runbook |
| `11-operations` | Monitoring, backup, restore, incident and maintenance |
| `12-appendices` | Decision log, change log, open questions and templates |

## Status conventions

- **Confirmed:** explicitly selected by the product owner.
- **Proposed:** recommended technical design requiring review.
- **Open:** decision required before the relevant implementation stage.
- **Out of scope:** intentionally excluded from this project.

## Important implementation note

This is a design and requirements baseline, not evidence that the software has been implemented. API routes, database fields, cloud provider details and operational settings must be finalized during implementation and verified in a running environment. Do not treat illustrative API paths as deployed endpoints.

## Recommended review order

1. Product overview and requirements.
2. Architecture and security model.
3. Database ER model and data dictionary.
4. UI/UX screen catalogue and user journeys.
5. API standards and endpoint catalogue.
6. Testing, development, deployment and operations.
7. Product owner approves the baseline before Stage 1 coding.
