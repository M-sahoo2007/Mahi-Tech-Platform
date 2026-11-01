# Architecture and Product Decision Log

| ID | Decision | Status | Notes |
|---|---|---|---|
| ADR-001 | Build from scratch; do not reuse old implementation code | Confirmed | Old project may be inspected only for business requirements if useful |
| ADR-002 | React + TypeScript frontend | Confirmed | Vite proposed |
| ADR-003 | Django + DRF backend | Proposed baseline | Confirm before Stage 1 |
| ADR-004 | Supabase PostgreSQL | Confirmed | Django ORM/migrations proposed |
| ADR-005 | Cloud deployment | Confirmed target | Provider and region open |
| ADR-006 | Internal agency use first | Confirmed | Client portal included behind test gate |
| ADR-007 | AI Development Studio excluded | Confirmed | Separate team owns it |
| ADR-008 | Django identity authority + JWT | Proposed | Avoid competing Django and Supabase Auth identities |
| ADR-009 | Modular monolith | Proposed | Avoid microservices at initial scale |
| OPEN-001 | Default currency | Open | Confirm INR or multi-currency |
| OPEN-002 | GST/tax behavior | Open | Confirm with business/accounting requirements |
| OPEN-003 | Invoice numbering | Open | Define sequence and financial-year rules |
| OPEN-004 | Multiple portal users per client | Proposed yes | ClientContact model supports multiple users |
| OPEN-005 | Cloud provider and region | Open | Compare cost, runtime, logs, backups and region |
| OPEN-006 | Email provider and sender domain | Open | Configure before email notifications |
| OPEN-007 | Refunds/credit notes | Open | Decide first-release requirement |
| OPEN-008 | Data retention policy | Open | Define before production |
