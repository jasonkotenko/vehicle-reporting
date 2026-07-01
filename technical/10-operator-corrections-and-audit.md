# Step 10: Operator Corrections and Audit

**Goal:** Allow operators to fix misread plates with a full immutable audit trail per PRD §5.5.

**Depends on:** Steps 3–4, 6, 9  
**Blocks:** Step 12 (correction UI)

## Operator workflow

1. Search/filter events with `plate_status` in (`OBSCURED`, `UNREADABLE`) or any event by ID/time
2. View multi-frame image gallery (all `image_refs` for the event)
3. Submit corrected plate text
4. System updates `vehicle_event.effective_plate`, reassigns profile linkage, recomputes trips, writes audit row

## Endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/events/{id}/gallery` | operator | Image refs + metadata for gallery view |
| POST | `/api/v1/events/{id}/correct-plate` | operator | Submit correction |
| GET | `/api/v1/admin/audit/corrections` | admin | Paginated audit log |
| GET | `/api/v1/admin/audit/corrections/{id}` | admin | Audit detail with payload snapshot |

### Correct plate payload

```json
{
  "new_plate": "XYZ5678",
  "note": "readable on frame 3"
}
```

## Correction service logic

`backend/app/services/corrections.py`:

1. Load event; reject if unchanged plate
2. Snapshot `original_raw_payload`, `original_effective_plate`, `image_refs` into `plate_correction_audit`
3. Update `effective_plate` and `normalized_plate` on event
4. Move event to correct `vehicle_profile` (create profile if needed)
5. Recompute trips for affected profiles (old + new)
6. Refresh authorization tag on event if plate now matches authorized list

**Immutability:** `raw_payload` and `raw_plate` never change; only `effective_plate` is derived.

## Audit log display fields

- `corrected_at`, `corrector.display_name`
- Before/after plates
- `original_raw_payload` (JSON)
- `image_refs` at time of correction
- Link to `vehicle_event_id`

## Deliverables

- [ ] Correction endpoint with validation
- [ ] Audit list/detail endpoints (admin)
- [ ] Service with transactional integrity (all-or-nothing)
- [ ] Tests: correction moves trip ownership; audit row created; raw_payload unchanged

## Acceptance criteria

- Operator can correct an `UNREADABLE` event; subsequent trip/roster reflects new plate
- Admin audit view shows original JSON and images
- Re-correction creates a second audit entry (history preserved)
