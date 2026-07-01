# Step 4: Ingest API

**Goal:** Accept CV/ALPR JSON payloads, persist immutable `vehicle_events`, and trigger downstream processing.

**Depends on:** Steps 1–3  
**Blocks:** Steps 6–7, 11

## Scale assumptions

~5,000 events/day (~3.5/min average, higher peaks at gate rush hours). A single API instance with synchronous event persistence and inline trip recompute is sufficient. Image fetching (step 11) runs as a **background task** after the event row is committed so ingest latency stays low.

## Endpoint

```
POST /api/v1/ingest/events
Authorization: X-Ingest-Key: <INGEST_API_KEY>
Content-Type: application/json
```

CV system POSTs directly to this endpoint.

### Request body

```json
{
  "external_id": "optional-cv-event-id",
  "camera_id": "CAM-MAIN-ENTRY",
  "timestamp": "2026-07-01T08:15:32+08:00",
  "license_plate": "ABC1234",
  "plate_status": "READ",
  "image_urls": ["http://cv-host/snapshots/abc1.jpg", "http://cv-host/snapshots/abc2.jpg"]
}
```

`image_urls` is required (min length 1). Each URL must be HTTP or HTTPS. The API container must be able to reach these URLs at fetch time (same LAN or routed network).

### Validation rules

- `camera_id` must match a registered, active camera (else 422 with clear message)
- `timestamp` required, parsed to UTC for storage
- `plate_status` required enum
- `license_plate` may be null when `UNREADABLE`
- `image_urls` required — at least one HTTP(S) URL

### Processing pipeline

1. Validate API key and payload (Pydantic schema)
2. Resolve camera row; reject unknown `camera_id`
3. Idempotency: if `external_id` exists, return `200` with existing event ID (fallback dedupe on `(camera_id, captured_at, normalized_plate)` if CV sends no `external_id` — see [decisions.md](decisions.md))
4. Normalize plate; lookup `authorized_vehicles` → set `authorization_status`
5. Upsert `vehicle_profile` for plate (or unattributed bucket if null plate)
6. Persist `vehicle_event` with full `raw_payload` and original `image_urls` in `image_refs` (pending fetch)
7. Inline trip recomputation for this profile (step 6)
8. Enqueue background task to fetch `image_urls` and update `image_refs` with stored keys (step 11)
9. Return `201` with `{ "event_id": "...", "vehicle_profile_id": "..." }`

## Error responses

| Status | Condition |
|--------|-----------|
| 401 | Invalid/missing ingest key |
| 422 | Validation failure, unknown camera, missing/invalid image URLs |
| 409 | Duplicate `external_id` with conflicting payload (optional strict mode) |

## Service module

`backend/app/services/ingest.py`:

- `IngestService.process_event(payload) -> IngestResult`
- Unit-tested independently of HTTP layer

## Deliverables

- [ ] Pydantic schemas `IngestEventRequest`, `IngestEventResponse`
- [ ] Route `POST /api/v1/ingest/events`
- [ ] Ingest service with idempotency
- [ ] Background task hook for image fetch (stub OK until step 11)
- [ ] Tests: happy path, unknown camera, duplicate external_id, unreadable plate, multi-frame `image_urls`

## Acceptance criteria

- `curl` with valid key and payload creates a row in `vehicle_events`
- Unknown camera returns 422
- Same `external_id` twice does not duplicate rows
- `raw_payload` matches submitted JSON exactly
- Ingest returns quickly even when image URLs are slow to fetch
