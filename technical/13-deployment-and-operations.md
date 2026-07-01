# Step 13: Deployment and Operations

**Goal:** Run reliably on Bazzite desktop today; migrate to cloud without architectural changes.

**Depends on:** All prior steps

## Desktop deployment (Bazzite)

### Prerequisites

- Docker Engine + Compose plugin (already available)
- Desktop LAN IP address (operators access via IP, e.g. `http://192.168.1.50:3000`)
- Firewall: allow TCP on API + frontend ports from LAN only
- API container network access to CV image URLs on the LAN

### Checklist

1. Copy `.env.example` → `.env`; set `PUBLIC_APP_URL`, `PUBLIC_API_URL`, secrets
2. `make up && make migrate`
3. Run bootstrap admin script
4. Register cameras and authorized vehicles
5. Configure CV system to POST to `http://<desktop-ip>:8000/api/v1/ingest/events` with ingest key
6. Confirm API container can HTTP GET CV `image_urls` from inside the network
7. Verify ingest from CV or `curl` test payload

### Backups

| Data | Method |
|------|--------|
| PostgreSQL | `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql` |
| Images | Archive `image_data` Docker volume periodically |

Cron on host or manual before OS updates.

### Updates

```bash
git pull
make down          # optional; can also rolling rebuild
make up            # rebuilds images
make migrate       # apply new migrations
```

## Cloud migration path

Same `docker-compose.yml` (or Compose → k8s/ECS later) with env changes only:

| Setting | Desktop | Cloud |
|---------|---------|-------|
| `PUBLIC_APP_URL` | `http://192.168.x.x:3000` | `https://vvt.example.com` |
| `PUBLIC_API_URL` | `http://192.168.x.x:8000` | `https://vvt.example.com/api` or subdomain |
| `DISPLAY_TIMEZONE` | `Asia/Manila` | same or per-deployment |
| TLS | Optional (LAN HTTP) | Caddy automatic HTTPS |
| `IMAGE_STORAGE_BACKEND` | `local` | `s3` (S3/MinIO/R2) |
| Database volume | Docker `pgdata` | Managed PostgreSQL |

### Caddy production config (sketch)

```
{$PUBLIC_APP_DOMAIN} {
    reverse_proxy /api/* api:8000
    reverse_proxy frontend:80
}
```

Use DNS A record to cloud VM; no code changes.

## Observability (MVP)

- Structured JSON logging from API (`LOG_LEVEL` env)
- Docker `json-file` log driver with rotation
- `/health` endpoint for uptime checks
- Optional: Prometheus metrics endpoint (defer)

## Security hardening for cloud

- [ ] TLS everywhere
- [ ] Strong `SECRET_KEY`, `INGEST_API_KEY`, DB password
- [ ] Restrict ingest endpoint by network ACL or VPN if possible
- [ ] Rate limit ingest (`slowapi` or reverse proxy)
- [ ] Regular Postgres and image backups off-site

## Optional: remote access without port forwarding

If kids are not always on the same LAN:

- **Tailscale** or **Cloudflare Tunnel** on desktop — still no hardcoded IPs in app; update `PUBLIC_*` URLs to tunnel hostname

## Deliverables

- [ ] `deploy/caddy/Caddyfile` templated from env
- [ ] Backup/restore documented in this file
- [ ] `docker-compose.prod.yml` override (proxy enabled, ports not exposed publicly)
- [ ] Runbook section in README (root or technical)

## Acceptance criteria

- Documented path from fresh clone → running system in < 30 minutes
- Backup + restore tested on dev volume
- Switching `PUBLIC_APP_URL` and rebuilding frontend is sufficient to change access URL
