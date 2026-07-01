# Step 3: Database Schema

**Goal:** PostgreSQL schema reflecting PRD entities with indexes for reporting queries.

**Depends on:** Steps 1–2  
**Blocks:** Steps 4–11

## Entity-relationship summary

```
cameras ─────────────┐
                     │
authorized_vehicles ─┼──▶ vehicle_profiles ◀── vehicle_events ──▶ plate_corrections (audit)
                     │           │
                     │           └──▶ trips ◀── trip_events (ordered link)
                     │
users ───────────────┘ (audit actor)
```

## Tables

### `cameras`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| camera_id | VARCHAR UNIQUE | Alphanumeric ID from CV system |
| label | VARCHAR | Human-readable location |
| zone_type | ENUM | `ENTRY`, `EXIT`, `INTERNAL` |
| active | BOOLEAN | Default true |
| created_at | TIMESTAMPTZ | |

### `vehicle_events` (immutable ingest records)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| external_id | VARCHAR NULL | Idempotency key from CV if provided |
| camera_id | UUID FK → cameras | Resolved from payload `camera_id` string |
| captured_at | TIMESTAMPTZ | From payload `timestamp` |
| raw_plate | VARCHAR NULL | OCR as received |
| normalized_plate | VARCHAR NULL | Computed |
| effective_plate | VARCHAR NULL | Starts as normalized; updated by corrections |
| plate_status | ENUM | `READ`, `OBSCURED`, `UNREADABLE` |
| image_refs | JSONB | Array of URLs/paths/keys after processing |
| raw_payload | JSONB | Full original JSON (immutable) |
| authorization_status | ENUM | `AUTHORIZED`, `VISITOR`, `UNKNOWN` — denormalized at ingest |
| ingested_at | TIMESTAMPTZ | Server receipt time |
| vehicle_profile_id | UUID FK → vehicle_profiles | Set at ingest |

**Indexes:** `(normalized_plate, captured_at)`, `(camera_id, captured_at)`, `(captured_at)`, `(vehicle_profile_id, captured_at)`, unique partial on `external_id` where not null.

### `vehicle_profiles`

One row per distinct `normalized_plate` (nullable plate bucket for entirely unreadable events linked after correction).

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| normalized_plate | VARCHAR UNIQUE NULL | |
| first_seen_at | TIMESTAMPTZ | |
| last_seen_at | TIMESTAMPTZ | |
| authorized_vehicle_id | UUID FK NULL | |

### `trips`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| vehicle_profile_id | UUID FK | |
| status | ENUM | `OPEN`, `COMPLETE`, `INCOMPLETE` |
| started_at | TIMESTAMPTZ NULL | ENTRY event time |
| ended_at | TIMESTAMPTZ NULL | EXIT event time |
| entry_event_id | UUID FK NULL | |
| exit_event_id | UUID FK NULL | |

### `trip_events`

Ordered membership of events in a trip.

| Column | Type | Notes |
|--------|------|-------|
| trip_id | UUID FK | |
| vehicle_event_id | UUID FK | |
| sequence | INT | 0-based order |
| PRIMARY KEY (trip_id, vehicle_event_id) | | |

### `authorized_vehicles`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| normalized_plate | VARCHAR UNIQUE | |
| category | ENUM | `RESIDENT`, `STAFF`, `SERVICE` |
| owner_name | VARCHAR | |
| owner_address | VARCHAR | Street / block / lot address |
| active | BOOLEAN | |
| created_at / updated_at | TIMESTAMPTZ | |

### `plate_correction_audit` (immutable)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| vehicle_event_id | UUID FK | |
| corrected_by_user_id | UUID FK → users | |
| corrected_at | TIMESTAMPTZ | |
| original_raw_plate | VARCHAR NULL | |
| original_effective_plate | VARCHAR NULL | |
| new_plate | VARCHAR | |
| original_raw_payload | JSONB | Snapshot before change |
| image_refs | JSONB | Copy at time of correction |

### `users`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| username | VARCHAR UNIQUE | |
| password_hash | VARCHAR | bcrypt |
| display_name | VARCHAR | |
| role | ENUM | `OPERATOR`, `ADMIN` |
| active | BOOLEAN | |

## Migration workflow

- Alembic autogenerate from SQLAlchemy models, always hand-review
- Initial migration: all tables above
- Seed migration (dev only): sample cameras, admin user, test authorized plates

## Deliverables

- [x] SQLAlchemy models in `backend/app/models/`
- [x] Alembic env configured with `DATABASE_URL`
- [x] Initial migration `001_initial_schema`
- [x] `make migrate` applies cleanly on fresh volume

## Acceptance criteria

- Migration runs idempotently via `alembic upgrade head`
- Foreign keys and enums match PRD semantics
- `\d vehicle_events` in psql shows expected indexes
