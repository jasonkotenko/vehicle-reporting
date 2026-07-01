# Step 12: Frontend

**Goal:** React UI with bi-directional drill-down, galleries, dashboards, and exports per PRD §5.4.

**Depends on:** Steps 7–11, 9  
**Blocks:** None (final feature layer)

## Tech choices

- React 18 + TypeScript + Vite
- React Router v6 — URL-driven state for deep linking
- TanStack Query — server state, caching, pagination
- Tailwind CSS — layout and components
- Headless UI or Radix — accessible modals/dropdowns

`VITE_API_BASE_URL` set at build time from `PUBLIC_API_URL` (Compose build arg). On desktop, this is the host machine's LAN IP (e.g. `http://192.168.1.50:8000`).

Display timezone fetched from `GET /api/v1/config` (`display_timezone` field) and used for all timestamp formatting and date-range pickers.

## Page map

| Route | Role | Purpose |
|-------|------|---------|
| `/login` | public | Login form |
| `/roster` | operator | Active village inventory |
| `/vehicles` | operator | Search profiles |
| `/vehicles/:id` | operator | Profile detail → trips, events, authorized link |
| `/events/:id` | operator | Event detail, gallery, correct plate, link to profile/trip |
| `/trips/:id` | operator | Timeline with entry/internal/exit thumbnails |
| `/reports` | admin | Report filters + results tables |
| `/admin/cameras` | admin | Camera CRUD |
| `/admin/authorized` | admin | Authorized vehicle CRUD |
| `/admin/users` | admin | User management |
| `/admin/audit` | admin | Correction audit log |

## Core UX patterns

### Relational drilling

Every entity card shows clickable links to related entities (profile ↔ trip ↔ event ↔ authorized record). Breadcrumb optional.

### Trip timeline

Vertical timeline component:

- ENTRY / INTERNAL / EXIT badges colored by zone type
- Thumbnail per event (click → lightbox gallery)
- Timestamps in configured display timezone (default Manila)
- Incomplete trips show warning banner

### Multi-frame gallery (OBSCURED / UNREADABLE)

- Horizontal filmstrip or grid of all frames
- Plate correction form inline below gallery
- Highlight `plate_status` badge

### Reports

- Date range picker labeled with display timezone from config
- Camera multi-select for transit report
- Trip status toggle (complete / incomplete)
- Export CSV / PDF buttons → `window.open` or download blob from API

## API client

`frontend/src/api/client.ts`:

- Typed functions per endpoint
- Attach JWT from auth context
- Centralized error handling

## Component structure

```
src/
  components/
    layout/       AppShell, Nav, ProtectedRoute
    vehicles/     VehicleCard, VehicleSearch
    events/       EventDetail, ImageGallery, PlateCorrectionForm
    trips/        TripTimeline, TripCard
    reports/      ReportFilters, ExportButtons
    admin/        CameraForm, AuthorizedVehicleTable, AuditTable
  pages/          one file per route
  hooks/          useAuth, usePagination
```

## Deliverables

- [ ] Auth context + protected routes
- [ ] All pages in route map wired to APIs
- [ ] Responsive layout (laptop screens primary target)
- [ ] Loading/error/empty states
- [ ] Manual smoke test checklist

## Acceptance criteria

- Navigate Vehicle → Trip → Event → Profile without dead ends
- Correct plate from event page; roster updates after refresh
- Admin can add camera and authorized vehicle from UI
- CSV export downloads from reports page
- App works when accessed via `PUBLIC_APP_URL` from another laptop on LAN
