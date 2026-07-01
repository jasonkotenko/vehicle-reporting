# Step 7: Query and Reporting APIs

**Goal:** JSON APIs powering dashboards, drill-down navigation, and report filters.

**Depends on:** Steps 3–6, 9  
**Blocks:** Steps 8, 12

## Read endpoints (operator + admin)

### Vehicle profiles

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/vehicles` | Search by plate substring; paginated |
| GET | `/api/v1/vehicles/{id}` | Profile + summary stats + link to authorized record |
| GET | `/api/v1/vehicles/{id}/events` | All events, newest first |
| GET | `/api/v1/vehicles/{id}/trips` | All trips |

### Vehicle events

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/events/{id}` | Event detail + link to profile + parent trip |
| GET | `/api/v1/events` | Filter: `plate`, `camera_id`, `plate_status`, `from`, `to`, `authorization_status` |

### Trips

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/trips/{id}` | Trip + ordered events with thumbnails |
| GET | `/api/v1/trips` | Filter: `status`, `from`, `to`, `plate`, `camera_id` (passed internal) |

### Active roster

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/roster` | Current vehicles inside; includes plate, entry time, authorization status |

## Historical report queries (admin)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports/entries` | Vehicles that **entered** in time window |
| GET | `/api/v1/reports/exits` | Vehicles that **exited** in time window |
| GET | `/api/v1/reports/transits` | Vehicles passing given `camera_ids[]` in window |
| GET | `/api/v1/reports/trips` | Trips with `status` filter (`COMPLETE` / `INCOMPLETE`) |

### Common query parameters

- `from` / `to` — ISO datetimes (inclusive), interpreted in `DISPLAY_TIMEZONE` (default `Asia/Manila`) then compared in UTC
- `page` / `page_size`
- `plate` — optional filter

### Response shape (example: trip list item)

```json
{
  "id": "...",
  "status": "COMPLETE",
  "started_at": "...",
  "ended_at": "...",
  "vehicle_profile": { "id": "...", "plate": "ABC1234" },
  "authorization_status": "RESIDENT",
  "event_count": 4,
  "links": {
    "self": "/api/v1/trips/...",
    "vehicle": "/api/v1/vehicles/..."
  }
}
```

Include `links` objects consistently for frontend deep linking.

## Performance notes

- Use DB-level filtering; avoid loading full history into memory
- Consider materialized view for roster if profiling shows slow queries (defer until needed)

## Deliverables

- [ ] Route modules with Pydantic response models
- [ ] Shared filter/pagination utilities
- [ ] Integration tests with seeded events covering each report type
- [ ] OpenAPI docs with example responses

## Acceptance criteria

- Each endpoint returns correct filtered results against seed data
- Incomplete trips appear distinctly in `/reports/trips?status=INCOMPLETE`
- Event detail includes `vehicle_profile_id` and `trip_id` when applicable
