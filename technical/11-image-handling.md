# Step 11: Image Handling

**Goal:** Fetch CV capture frames from HTTP URLs at ingest and serve them to the UI reliably across desktop and cloud deployments.

**Depends on:** Steps 2–4  
**Blocks:** Steps 10, 12

## Input assumption

CV payloads provide `image_urls` — HTTP(S) URLs pointing at the CV system or a CDN on the local network. The API container fetches these at ingest time; operators' laptops never contact the CV host directly.

Multi-frame events (`OBSCURED`, `UNREADABLE`) may include several URLs for the same capture event.

## Approach: ingest-time fetch + local/object storage

Background task (enqueued from step 4) after event commit:

1. For each URL in `image_urls`, HTTP GET the bytes (with timeout and size limit)
2. Store under `IMAGE_STORAGE_PATH` with a UUID-based key
3. Update `image_refs` in `vehicle_events` from pending URLs to stored keys

App-relative serve path:

```
GET /api/v1/images/{image_key}
```

Requires operator auth (JWT). Use signed short-lived URLs for `<img src>` tags (no `Authorization` header on image requests).

### Storage layout (local backend)

```
/data/images/
  ab/
    abc123....jpg
```

Env `IMAGE_STORAGE_BACKEND=local` uses filesystem; future `s3` uses MinIO/S3-compatible API with same key scheme.

At ~5,000 events/day, estimate image storage separately from Postgres (e.g. 5–15 GB/month depending on frame count and resolution). Plan volume sizing in step 13.

## Serving images

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/images/{key}` | signed token query param | Stream image with correct `Content-Type` |
| GET | `/api/v1/events/{id}/images/{index}` | signed token | Convenience redirect to keyed image |

### Security

- Validate `key` against path traversal (`..`, absolute paths)
- Do not proxy arbitrary user-supplied URLs at request time (SSRF) — only serve pre-stored keys
- Fetch only URLs present in the ingest payload; optional `CV_IMAGE_URL_ALLOWLIST` prefix env for defense in depth
- If fetch fails at ingest, event is still stored; `image_refs` entry marked `fetch_failed`; operator UI shows placeholder

## Network note (desktop phase)

The API container must reach CV image URLs (typically same LAN). This is an infrastructure/Docker networking concern, not an application hardcode. Operators only talk to `PUBLIC_API_URL`.

## Thumbnails (optional MVP+)

Generate 200px-wide thumbnails on ingest for faster gallery loading; store alongside originals with `_thumb` suffix.

## Deliverables

- [ ] `ImageStorage` interface with `local` implementation
- [ ] Background fetch task wired from ingest pipeline
- [ ] Signed URL generation for image serve endpoint
- [ ] Tests with mocked HTTP fetch and fixture image files
- [ ] Fetch timeout and max file size enforced

## Acceptance criteria

- Event with `image_urls` shows viewable thumbnails in UI after background fetch completes
- Image endpoint returns 404 for unknown keys
- No unauthenticated access to images
- Switching `PUBLIC_API_URL` does not require re-storing images
