# Step 1: Architecture and Conventions

**Goal:** Establish repository layout, cross-cutting rules, and API contracts before writing feature code.

**Depends on:** Nothing  
**Blocks:** All other steps

## Repository layout

```
vehicle-reporting/
├── product/                 # PRD (existing)
├── technical/               # This plan
├── backend/
│   ├── app/
│   │   ├── api/             # Route modules (v1)
│   │   ├── core/            # Config, security, dependencies
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic (trips, reports, ingest)
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── components/
│   │   ├── pages/
│   │   └── routes/          # React Router paths = deep links
│   ├── Dockerfile
│   └── package.json
├── deploy/
│   ├── caddy/               # Reverse proxy config (templated)
│   └── compose/             # Optional override files
├── docker-compose.yml
├── docker-compose.override.yml.example
├── Makefile
├── .env.example
└── AGENTS.md
```

## API conventions

- **Base path:** `/api/v1`
- **Format:** JSON request/response; `Content-Type: application/json`
- **Timestamps:** ISO 8601 in UTC in the API and database; UI and exports format using `DISPLAY_TIMEZONE` (env, default `Asia/Manila`). Per-user timezone preference is out of scope for MVP.
- **IDs:** UUID v4 for all primary keys exposed to clients
- **Pagination:** `?page=1&page_size=50` with response envelope `{ "items": [], "total": N, "page": 1, "page_size": 50 }`
- **Errors:** RFC 7807–style `{ "detail": "...", "code": "..." }` with appropriate HTTP status
- **Versioning:** URL prefix (`/api/v1`); breaking changes require `/api/v2`

## Entity URL map (frontend deep links)

| Entity | Path |
|--------|------|
| Vehicle profile | `/vehicles/:id` |
| Vehicle event | `/events/:id` |
| Trip | `/trips/:id` |
| Authorized record | `/authorized/:id` |
| Camera | `/admin/cameras/:id` |
| Audit log entry | `/admin/audit/:id` |
| Active roster | `/roster` |
| Reports | `/reports` |

## Naming conventions

- **Python:** `snake_case` modules/functions; `PascalCase` classes; type hints everywhere
- **TypeScript:** `camelCase` variables; `PascalCase` components; API types mirror backend schemas
- **Database:** `snake_case` tables and columns; plural table names (`vehicle_events`, `trips`)
- **Environment variables:** `SCREAMING_SNAKE_CASE`; prefix service-specific vars (`DATABASE_URL`, `API_BASE_URL`, `IMAGE_STORAGE_PATH`, `DISPLAY_TIMEZONE`)

## Plate normalization

Implement a single shared function used by ingest, authorization lookup, and search:

```python
def normalize_plate(raw: str | None) -> str | None:
    if not raw:
        return None
    return "".join(c for c in raw.upper() if c.isalnum())
```

Store both `raw_plate` (OCR as received) and `normalized_plate` (for matching).

## Timezone handling

- `DISPLAY_TIMEZONE` env var (IANA name, default `Asia/Manila`) — used by export formatters and exposed via `GET /api/v1/config` for the frontend
- Report date-range filters (`from` / `to`) are interpreted in `DISPLAY_TIMEZONE`, then converted to UTC for queries
- `backend/app/core/timezone.py` provides shared `to_display(dt)` / `parse_display_datetime(s)` helpers

## Expected scale (MVP)

~5,000 ingest events per day (~3.5/min average). No message queue or horizontal scaling required; synchronous ingest with inline trip recompute is acceptable. Image fetching may run as a background task after the event row is committed.

## Security baseline (all environments)

- No secrets in git; `.env` is gitignored; `.env.example` documents required vars
- CORS origins from env (`CORS_ORIGINS`)
- Ingest endpoint authenticated via API key header (`X-Ingest-Key`), separate from user session auth
- User passwords hashed with bcrypt (step 9)

## Deliverables

- [x] This directory structure created (empty placeholders OK)
- [x] `backend/app/core/config.py` reading env via `pydantic-settings`
- [x] `backend/app/main.py` with `/health` returning `{ "status": "ok" }`
- [x] `GET /api/v1/config` returning `{ "display_timezone": "..." }` from env
- [x] Documented API conventions (this file + inline OpenAPI from FastAPI)

## Acceptance criteria

- `make up` starts API container; `curl http://localhost:${API_PORT}/health` returns 200
- OpenAPI docs available at `/docs`
- Config fails fast with a clear error if required env vars are missing
