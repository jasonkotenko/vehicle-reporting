# Stakeholder Decisions

Recorded answers that drive implementation. Remaining open items are listed at the bottom.

## Resolved

| Topic | Decision |
|-------|----------|
| **CV image delivery** | HTTP `image_urls` only; API fetches at ingest and stores locally |
| **CV ingest** | Direct POST to `/api/v1/ingest/events` with `X-Ingest-Key` header |
| **Event volume** | ~5,000 events/day (~3.5/min avg); modest peak at gate rush hours — no special scaling architecture needed for MVP |
| **Authorized vehicle fields** | `plate`, `category` (resident/staff/service), `owner_name`, `owner_address` |
| **Authorized vehicle maintenance** | Manual admin entry in MVP; CSV import deferred |
| **Concurrent users** | ~5 operators on laptops; local username/password accounts |
| **LAN access (desktop phase)** | Operators use desktop **IP address** in browser (e.g. `http://192.168.1.50:3000`); set via `PUBLIC_APP_URL` / `PUBLIC_API_URL` env vars — never hardcoded in code |
| **Timezone** | Configurable via `DISPLAY_TIMEZONE` env var; default `Asia/Manila`. API stores UTC; UI and exports use configured timezone |
| **Stack** | Python 3.12 + FastAPI backend; React + TypeScript frontend; PostgreSQL; Docker Compose |
| **Plate normalization** | Store raw OCR text; normalize to uppercase alphanumeric for matching |

## Still open

- **CV idempotency:** Does the CV system send a unique `external_id`, or dedupe on `(camera_id, timestamp, plate)`?
- **Camera count:** How many cameras in v1, and ENTRY / EXIT / INTERNAL split?
- **PDF branding:** Village name, logo, header/footer requirements?
- **Retention / disk:** PRD assumes indefinite retention — confirm desktop disk budget for images at ~5k events/day.
