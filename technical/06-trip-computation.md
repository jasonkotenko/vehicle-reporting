# Step 6: Trip Computation

**Goal:** Derive `trips` from chronologically ordered `vehicle_events` and camera `zone_type` tags.

**Depends on:** Steps 3–5  
**Blocks:** Steps 7–8, 12

## State machine (per vehicle profile)

Events for a single `vehicle_profile_id` are processed in `captured_at` ascending order:

| Event zone | Action |
|------------|--------|
| `ENTRY` | If no open trip → create `OPEN` trip, attach as `entry_event`. If open trip exists → mark current trip `INCOMPLETE`, start new `OPEN` trip (orphaned exit implied). |
| `INTERNAL` | Attach to current open trip if one exists; else create `INCOMPLETE` trip (entered without recorded entry). |
| `EXIT` | If open trip → attach as exit, set `COMPLETE`, set `ended_at`. If no open trip → create `INCOMPLETE` trip with only exit. |

## Trip statuses

| Status | Meaning |
|--------|---------|
| `OPEN` | ENTRY seen, no EXIT yet — vehicle presumed inside |
| `COMPLETE` | ENTRY + EXIT (zero or more INTERNAL between) |
| `INCOMPLETE` | Orphaned ENTRY (no EXIT), orphaned EXIT (no ENTRY), or INTERNAL-only sequence |

## Active roster query

Vehicles currently inside = vehicle profiles where the **latest relevant event** implies residency:

```sql
-- Conceptual: profile whose most recent ENTRY-starting open trip has status OPEN
SELECT vp.* FROM vehicle_profiles vp
JOIN trips t ON t.vehicle_profile_id = vp.id
WHERE t.status = 'OPEN'
ORDER BY t.started_at DESC;
```

Expose via `GET /api/v1/roster` (step 7).

## Recomputation strategy

**MVP:** On each new ingest for a profile, recompute trips for that profile from scratch (simple, correct for moderate volume).

**Optimization (later):** Incremental append if performance requires it.

**On plate correction:** Reassign event to new profile, recompute both old and new profiles.

## Service module

`backend/app/services/trips.py`:

- `recompute_trips_for_profile(profile_id: UUID) -> None`
- `get_active_roster() -> list[RosterEntry]`
- `get_trip_with_events(trip_id: UUID) -> TripDetail`

## Deliverables

- [ ] Trip builder service with unit tests covering:
  - Standard entry → internal → exit
  - Entry only (open trip)
  - Exit only (incomplete)
  - Double entry without exit
  - Internal without entry
- [ ] `trip_events` ordering populated correctly
- [ ] Hook called from ingest pipeline (step 4)

## Acceptance criteria

- Ingest sequence in tests produces expected trip statuses
- Active roster returns only `OPEN` trips
- Trip detail returns events in chronological order with image refs
