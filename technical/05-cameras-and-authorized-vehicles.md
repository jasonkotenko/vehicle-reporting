# Step 5: Cameras and Authorized Vehicles

**Goal:** Admin APIs to register cameras with zone types and maintain the authorized vehicle directory.

**Depends on:** Steps 1–3, 9 (auth) for production; stub auth OK during development  
**Blocks:** Step 4 (cameras must exist before ingest), step 6

## Camera management (admin only)

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/cameras` | List all cameras |
| POST | `/api/v1/admin/cameras` | Create camera |
| GET | `/api/v1/admin/cameras/{id}` | Detail |
| PATCH | `/api/v1/admin/cameras/{id}` | Update label, zone_type, active |
| DELETE | `/api/v1/admin/cameras/{id}` | Soft-delete (set `active=false`) |

### Create payload

```json
{
  "camera_id": "CAM-MAIN-ENTRY",
  "label": "Main Gate - Entry",
  "zone_type": "ENTRY"
}
```

**Business rules**

- `camera_id` is immutable after create (matches CV hardware config)
- Deactivating a camera rejects new ingest events for that ID
- Changing `zone_type` does not retroactively recompute trips in MVP (document as limitation; optional backfill script later)

## Authorized vehicles (admin only)

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/authorized-vehicles` | Paginated list; filter by `active`, `category`, search plate |
| POST | `/api/v1/admin/authorized-vehicles` | Create |
| GET | `/api/v1/admin/authorized-vehicles/{id}` | Detail + link to vehicle profile if seen |
| PATCH | `/api/v1/admin/authorized-vehicles/{id}` | Update |

### Create payload

```json
{
  "plate": "ABC 1234",
  "category": "RESIDENT",
  "owner_name": "Juan Dela Cruz",
  "owner_address": "Block 12 Lot 5, Maple Street"
}
```

Server normalizes plate on write. Manual admin entry only for MVP; CSV bulk import deferred.

**On create/update:** Re-link matching `vehicle_profiles` and refresh `authorization_status` on future ingests only (MVP). Optional: background job to update historical events.

## Deliverables

- [ ] CRUD routes and services for cameras and authorized vehicles
- [ ] Admin role guard (or temporary dev bypass flagged in env)
- [ ] OpenAPI documentation
- [ ] Tests for CRUD and plate normalization on create

## Acceptance criteria

- Admin can register cameras before first ingest event
- Ingest rejects events for unregistered `camera_id`
- Authorized plate lookup tags new events as `AUTHORIZED`
- Unknown plates tagged `VISITOR`
