# Questions for Stakeholder

> **Most questions are answered.** See [decisions.md](decisions.md) for the full record. Remaining items below.

## CV / ALPR integration

1. **Does the CV system send a unique event ID we can use for idempotency, or must we dedupe on `(camera_id, timestamp, plate)`?**

## Cameras and zones

2. **How many cameras in v1?** How many are ENTRY vs EXIT vs INTERNAL?

3. **Can one physical gate have separate ENTRY and EXIT cameras, or is it always one camera per direction?**

## Reporting

4. **PDF branding requirements?** (village name, logo, header/footer)

5. **Retention:** PRD says indefinite retention for MVP — confirm disk budget is acceptable on the desktop host (~5k events/day with multi-frame images for some events).
