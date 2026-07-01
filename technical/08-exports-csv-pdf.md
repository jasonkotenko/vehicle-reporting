# Step 8: Exports (CSV and PDF)

**Goal:** Downloadable exports for all tabular report views per PRD §5.3.

**Depends on:** Step 7  
**Blocks:** Step 12 (export buttons)

## Endpoints

Mirror report filters from step 7 with `Accept` or `?format=` negotiation:

```
GET /api/v1/reports/entries?from=...&to=...&format=csv
GET /api/v1/reports/entries?from=...&to=...&format=pdf
```

Same pattern for `exits`, `transits`, `trips`, and `roster`.

### Response headers

```
Content-Disposition: attachment; filename="entries-2026-07-01.csv"
Content-Type: text/csv | application/pdf
```

## CSV implementation

- Python `csv` module writing to `StreamingResponse`
- Column sets per report type (documented in OpenAPI)
- Timestamps formatted in `DISPLAY_TIMEZONE` (default `Asia/Manila`) for human readability
- UTF-8 with BOM optional for Excel compatibility

### Example columns (entries report)

`plate`, `entry_time`, `camera_label`, `authorization_status`, `trip_id`, `trip_status`

## PDF implementation

- Jinja2 HTML templates in `backend/app/templates/reports/`
- WeasyPrint renders HTML → PDF
- Include: report title, filter summary (date range), generated-at timestamp, row table
- Logo/branding from env `REPORT_LOGO_URL` or static asset path (optional)

## Shared export service

`backend/app/services/exports.py`:

- `export_csv(report_type, filters) -> Iterator[str]`
- `export_pdf(report_type, filters) -> bytes`

Reuse query logic from step 7 — do not duplicate SQL.

## Docker note

WeasyPrint requires system fonts/libs; add to `backend/Dockerfile`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

## Deliverables

- [ ] CSV streaming for all report types
- [ ] PDF templates for all report types
- [ ] Tests: CSV row count matches API JSON total; PDF returns valid content-type
- [ ] Frontend download triggers (step 12)

## Acceptance criteria

- CSV opens correctly in LibreOffice / Excel
- PDF is readable and includes filter metadata
- Large result sets stream without OOM (cursor-based or chunked queries)
