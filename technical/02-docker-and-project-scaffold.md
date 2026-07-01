# Step 2: Docker and Project Scaffold

**Goal:** Runnable multi-container stack on Bazzite (desktop) that mirrors future cloud deployment.

**Depends on:** Step 1  
**Blocks:** Steps 3–13

## Compose services

| Service | Image / build | Purpose |
|---------|---------------|---------|
| `db` | `postgres:16-alpine` | Primary datastore |
| `api` | Build `backend/Dockerfile` | FastAPI application |
| `frontend` | Build `frontend/Dockerfile` | nginx serving Vite production build |
| `proxy` | `caddy:2-alpine` | Optional in dev; recommended for prod-like single entrypoint |

Development may expose `api` and `frontend` ports directly; production routes everything through `proxy`.

## docker-compose.yml sketch

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      retries: 5

  api:
    build: ./backend
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - image_data:/data/images   # configurable image store
    ports:
      - "${API_PORT:-8000}:8000"

  frontend:
    build: ./frontend
    environment:
      VITE_API_BASE_URL: ${PUBLIC_API_URL}
    ports:
      - "${FRONTEND_PORT:-3000}:80"

volumes:
  pgdata:
  image_data:
```

## Environment variables (.env.example)

```bash
# Public URLs — desktop phase: use the host machine's LAN IP; cloud: use your domain
# Never hardcode these in application code
PUBLIC_APP_URL=http://192.168.1.50:3000
PUBLIC_API_URL=http://192.168.1.50:8000

# Database
POSTGRES_USER=vvt
POSTGRES_PASSWORD=change-me
POSTGRES_DB=vvt
DATABASE_URL=postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# API
API_PORT=8000
SECRET_KEY=change-me-long-random
INGEST_API_KEY=change-me-ingest-key
CORS_ORIGINS=${PUBLIC_APP_URL}

# Images
IMAGE_STORAGE_PATH=/data/images
IMAGE_STORAGE_BACKEND=local   # local | s3 (future)

# App
DISPLAY_TIMEZONE=Asia/Manila
LOG_LEVEL=INFO
```

`PUBLIC_*` URLs are what browsers and the CV system use. Inside Compose, services talk via Docker DNS (`db`, `api`).

## Makefile targets

```makefile
up:          docker compose up -d --build
down:        docker compose down
logs:        docker compose logs -f
migrate:     docker compose exec api alembic upgrade head
shell-api:   docker compose exec api bash
test:        docker compose exec api pytest
seed:        docker compose exec api python -m app.scripts.seed  # dev fixtures
```

## Backend Dockerfile

- Multi-stage optional; single stage is fine for MVP
- Base: `python:3.12-slim`
- Install deps from `requirements.txt` or `pyproject.toml`
- Run with `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Non-root user in container

## Frontend Dockerfile

- Stage 1: `node:22-alpine` — `npm ci && npm run build`
- Stage 2: `nginx:alpine` — copy `dist/` to `/usr/share/nginx/html`
- nginx `try_files` fallback for client-side routing

## LAN access from operators' laptops (desktop phase)

1. Find the desktop's LAN IP (`ip addr` or router DHCP table).
2. Set `PUBLIC_APP_URL` and `PUBLIC_API_URL` to `http://<desktop-ip>:<port>` (e.g. `http://192.168.1.50:3000`).
3. Ensure Bazzite firewall allows inbound on those ports from the LAN.
4. Rebuild the frontend container after changing `PUBLIC_*` URLs (API base URL is baked in at build time).
5. No application code changes when moving to cloud — only env vars and TLS via Caddy.

## Deliverables

- [ ] `docker-compose.yml` + `.env.example`
- [ ] `Makefile` with targets above
- [ ] Backend and frontend Dockerfiles
- [ ] `.gitignore` (`.env`, `node_modules`, `__pycache__`, volumes)
- [ ] `docker-compose.override.yml.example` for local dev hot-reload (optional)

## Acceptance criteria

- `make up` brings up db + api + frontend
- All containers healthy; API `/health` OK
- Frontend loads in browser at `PUBLIC_APP_URL`
- `make down` cleans up without data loss (`pgdata` volume persists)
