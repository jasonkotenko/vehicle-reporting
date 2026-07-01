# Step 9: Authentication and RBAC

**Goal:** Secure the API and UI with role-based access for operators and admins.

**Depends on:** Steps 1–3  
**Blocks:** Steps 5, 7, 10, 12

## Scale

~5 concurrent operators (guards on laptops). JWT bearer tokens in headers; no session store or Redis required for MVP.

## Roles

| Role | Capabilities |
|------|--------------|
| `OPERATOR` | View roster, events, trips, vehicles; search; correct plates (step 10) |
| `ADMIN` | All operator capabilities + camera CRUD, authorized vehicles, reports, exports, audit log |

Ingest API uses separate **API key** auth (step 4), not user sessions.

## Auth mechanism (MVP)

- Username + password login → JWT access token (short-lived, e.g. 8h)
- `POST /api/v1/auth/login` → `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`
- `GET /api/v1/auth/me` — current user
- `POST /api/v1/auth/logout` — client discards token (optional server-side denylist later)
- Password hashing: bcrypt via `passlib`
- JWT signed with `SECRET_KEY` from env

## User management (admin)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/users` | List users |
| POST | `/api/v1/admin/users` | Create user |
| PATCH | `/api/v1/admin/users/{id}` | Update role, active, display_name |
| POST | `/api/v1/admin/users/{id}/reset-password` | Set new password |

Bootstrap: `python -m app.scripts.create_admin` or seed migration creates first admin from env `BOOTSTRAP_ADMIN_PASSWORD` (one-time).

## FastAPI dependencies

```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> User: ...
def require_admin(user: User = Depends(get_current_user)) -> User: ...
def require_operator(user: User = Depends(get_current_user)) -> User: ...
```

Apply guards to route modules introduced in steps 5, 7, 8, 10.

## Frontend

- Store token in `sessionStorage` (not `localStorage` — slightly better for shared laptops)
- Axios/fetch interceptor adds `Authorization: Bearer ...`
- Redirect to `/login` on 401
- Route guards: `/admin/*` requires admin role

## CORS and cookies

- Bearer tokens in header (not cookies) simplifies LAN + cloud deployment
- `CORS_ORIGINS` must include `PUBLIC_APP_URL`

## Deliverables

- [ ] User model wired (step 3)
- [ ] Login/me endpoints
- [ ] JWT utilities and FastAPI dependencies
- [ ] Admin user CRUD
- [ ] Bootstrap script for first admin
- [ ] Tests: login, forbidden admin route as operator, ingest key unaffected

## Acceptance criteria

- Unauthenticated requests to protected routes return 401
- Operator cannot access `/api/v1/admin/cameras`
- Admin can access all routes
- Ingest endpoint still accepts `X-Ingest-Key` without user JWT
