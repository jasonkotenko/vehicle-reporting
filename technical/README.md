# Technical Implementation Plan

Village Vehicle Tracking System — engineering plan derived from [product/PRD.md](../product/PRD.md).

## Recommended stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend API | **Python 3.12 + FastAPI** | Readable, strong typing via Pydantic, excellent for data/reporting; satisfies the no-JS-backend constraint |
| ORM / migrations | **SQLAlchemy 2.0 + Alembic** | Mature PostgreSQL tooling, explicit schema evolution |
| Database | **PostgreSQL 16** | Relational model fits events/trips/audit; robust querying for reports |
| Frontend | **React + TypeScript + Vite** | Component model suits drill-down navigation; TS is fine on frontend per requirements |
| Styling | **Tailwind CSS** | Fast iteration, consistent UI without heavy design system overhead |
| PDF export | **WeasyPrint** (HTML → PDF) | Reuse report templates; easier to maintain than low-level PDF libraries |
| CSV export | **stdlib `csv`** | Simple, no extra dependencies |
| Container orchestration | **Docker Compose** | Matches Bazzite workflow; identical layout for desktop and cloud |
| Reverse proxy | **Caddy** (or nginx) | TLS termination, single hostname for API + UI in production |

All hostnames, ports, and storage paths are driven by environment variables — nothing is tied to a LAN IP or `localhost` in application code. For the desktop phase, operators reach the app via the host machine's IP (configured in `PUBLIC_APP_URL`).

## Stakeholder decisions

Key choices are recorded in [decisions.md](decisions.md). Summary:

- CV sends **HTTP image URLs**; API fetches and stores them at ingest
- **~5,000 events/day**, **~5 concurrent operators** — standard single-node Compose is sufficient
- Authorized vehicles: **plate, category, owner name, owner address**
- **Local username/password** auth; two roles (operator, admin)
- **Configurable timezone** (`DISPLAY_TIMEZONE`, default `Asia/Manila`)
- Stack confirmed: **Python/FastAPI + React/PostgreSQL/Docker Compose**

## Architecture overview

```
┌─────────────────┐     POST /api/v1/ingest      ┌──────────────────┐
│  CV / ALPR      │ ────────────────────────────▶│                  │
│  (external)     │                              │   API (FastAPI)  │
└─────────────────┘                              │                  │
                                                 │  ┌────────────┐  │
┌─────────────────┐     HTTPS (browser)          │  │ Trip       │  │
│  Operators /    │ ◀───────────────────────────▶│  │ computation│  │
│  Admins (web)   │                              │  └────────────┘  │
└─────────────────┘                              └────────┬─────────┘
                                                          │
                        ┌─────────────────────────────────┼──────────────┐
                        ▼                                 ▼              ▼
                 ┌─────────────┐                  ┌─────────────┐  ┌──────────┐
                 │ PostgreSQL  │                  │ Image store │  │  Static  │
                 │             │                  │ (volume /   │  │  React   │
                 └─────────────┘                  │  S3-compat) │  │  (nginx) │
                                                  └─────────────┘  └──────────┘
```

**Core design principles**

1. **Immutable events** — CV payloads are stored as-is; corrections create audit records and update a derived `effective_plate` field without destroying the original payload.
2. **Derived trips** — Trips are computed from ordered events + camera zone tags, not written by the CV system.
3. **Configuration over convention** — Camera zones (`ENTRY` / `EXIT` / `INTERNAL`) are admin-configured, not inferred.
4. **Deep-linkable entities** — Every entity has a stable UUID and a canonical URL path (`/vehicles/{id}`, `/trips/{id}`, etc.).

## Implementation steps

Execute in order. Each step has its own doc with scope, deliverables, and acceptance criteria.

| Step | Document | Summary |
|------|----------|---------|
| 1 | [01-architecture-and-conventions.md](01-architecture-and-conventions.md) | Repo layout, naming, API versioning, timezone rules |
| 2 | [02-docker-and-project-scaffold.md](02-docker-and-project-scaffold.md) | Compose services, Makefile, env templates, health checks |
| 3 | [03-database-schema.md](03-database-schema.md) | Tables, indexes, Alembic migrations |
| 4 | [04-ingest-api.md](04-ingest-api.md) | CV webhook, event persistence, idempotency |
| 5 | [05-cameras-and-authorized-vehicles.md](05-cameras-and-authorized-vehicles.md) | Admin CRUD for cameras, zones, authorized plates |
| 6 | [06-trip-computation.md](06-trip-computation.md) | Trip builder, incomplete-trip detection, active roster |
| 7 | [07-query-and-reporting-apis.md](07-query-and-reporting-apis.md) | Filterable history, drill-down JSON APIs |
| 8 | [08-exports-csv-pdf.md](08-exports-csv-pdf.md) | Downloadable reports |
| 9 | [09-authentication-and-rbac.md](09-authentication-and-rbac.md) | Login, operator vs admin roles |
| 10 | [10-operator-corrections-and-audit.md](10-operator-corrections-and-audit.md) | Plate correction UI/API, immutable audit log |
| 11 | [11-image-handling.md](11-image-handling.md) | Serving frame images to the UI |
| 12 | [12-frontend.md](12-frontend.md) | React app: navigation, galleries, dashboards |
| 13 | [13-deployment-and-operations.md](13-deployment-and-operations.md) | Desktop LAN access, cloud migration, backups |

## Suggested MVP cut line

For a first usable release, complete steps **1–7, 9, 11 (minimal), and 12 (core views)**. Defer full PDF polish and advanced audit UI to a fast-follow.

## Open questions

See [decisions.md](decisions.md) for resolved items and remaining questions (CV idempotency key, camera count, PDF branding).
