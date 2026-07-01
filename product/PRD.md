# **Product Requirements Document: Village Vehicle Tracking System (v1.3)**

## **1. Executive Summary**

**Objective:** To develop a centralized vehicle tracking and monitoring system for gated residential communities in the Philippines. The system will ingest automated license plate recognition (ALPR) data from an external computer vision service to track vehicle residency, map transit trips, manage authorized vehicle lists, and provide actionable security reporting.

**Out of Scope (for MVP):** Automated alerting, visitor ID scanning/surrender workflows, hardware integration (boom barrier control), data archiving/pruning (data is assumed retained indefinitely), and the computer vision model itself.

## **2. User Personas**

- **Security Operator / Guard:** Monitors the system, looks up specific vehicles, and manually corrects misread license plates using multi-frame image galleries.
- **Village Administrator / Security Head:** Generates reports, investigates incidents, audits operator corrections, and manages the authorized vehicle database.

## **3. System Inputs**

The system will passively consume data via an API endpoint from an existing CV/ALPR system.

- **Payload Format:** JSON
- **Required Fields:**
  - `image_urls` / `file_paths`: Array of strings. Contains the location of the captured image files. Standard reads may contain a single image, while flagged captures (`OBSCURED` or `UNREADABLE`) will contain multiple frames from the video stream of the same continuous event.
  - `license_plate`: String of alphanumeric text (or null if entirely unreadable).
  - `plate_status`: Enum/Indicator (e.g., `READ`, `OBSCURED`, `UNREADABLE`).
  - `camera_id`: Unique identifier of the capturing hardware.
  - `timestamp`: Exact time of the initial capture event.

## **4. Data Architecture & Entity Relationships**

To ensure system resilience and handle edge cases, the system utilizes a decoupled data model where raw captures are stored independently and relationships are derived dynamically.

- **Vehicle Event (Base Entity):** An immutable, independent detection record (Entry, Internal, or Exit) ingested from the external CV system. It contains the array of image frames, timestamp, location, and OCR plate data.
- **Trip (Computed Entity):** A logical grouping of `Vehicle Events` representing a single stay within the village.
  - *Standard Trip:* Begins with an `ENTRY` event, includes zero or more `INTERNAL` events, and concludes with an `EXIT` event.
  - *Incomplete/Orphaned Trip:* An `EXIT` event without a preceding `ENTRY` (or vice versa). The system seamlessly stores these and flags them as incomplete during reporting.
- **Vehicle Profile:** The master record for a unique license plate. It aggregates all `Vehicle Events` and `Trips` associated with that plate over time.
- **Authorized Vehicle Record:** The administrative profile indicating if a `Vehicle Profile` belongs to a resident, staff, or registered service.

## **5. Core Feature Specifications**

### **5.1. Infrastructure Mapping (Camera Management)**

- **Camera Registration:** Admins can map an alphanumeric `camera_id` to a human-readable physical location (e.g., "Main Gate - Entry", "Intersection 1 - Northbound").
- **Zone Definition:** Each camera must be tagged with a directional context determining its impact on the vehicle's state:
  - `ENTRY`: Marks the beginning of a vehicle's residency.
  - `EXIT`: Marks the end of a vehicle's residency.
  - `INTERNAL`: Logs a transit point without changing residency status.

### **5.2. Vehicle Database & Authorization**

- **Resident/Authorized Directory:** A database module mapping known license plates to authorized entities.
- **Data Correlation:** All incoming CV data automatically cross-references this database to tag captures as `Authorized` or `Visitor`.

### **5.3. Analytics & Reporting Engine**

- **Active Roster (Current Village Inventory):** A real-time dashboard of vehicles currently inside the village, calculated by identifying all `Vehicle Profiles` that have an `ENTRY` event as their most recent chronological state, without a subsequent `EXIT` event.
- **Historical Querying:** Filterable reports allowing admins to query:
  - Vehicles that entered or exited during a specific time window.
  - Vehicles that passed a specific internal camera (or set of cameras) during a time window.
- **Trip Resolution Reporting:** Reports must explicitly distinguish between "Completed Trips" and "Incomplete/Orphaned Events."
- **Exportability:** All tabular reports and data views must be downloadable as `.csv` (Spreadsheet) and `.pdf`.

### **5.4. User Interface & Deep Linking**

The UI must support seamless, bi-directional navigation between related data points to facilitate rapid investigations.

- **Relational Drilling:** Users must be able to click through entities fluidly (e.g., Click a `Trip` -> View the `Vehicle Events` -> Click the `Vehicle Profile` -> View all historical `Trips` -> Click the `Authorized Vehicle Record`).
- **Visual Evidence:** When viewing a "Trip," the UI must display the chronological timeline, complete with thumbnail images of the `ENTRY` capture, all `INTERNAL` transit captures, and the `EXIT` capture, alongside timestamps.
- **Event Context:** When viewing any isolated `Vehicle Event`, the UI must provide a direct link to the overarching `Vehicle Profile`.

### **5.5. Data Integrity & Operator Overrides**

- **Multi-Frame Analysis:** For captures flagged as `OBSCURED` or `UNREADABLE`, the operator interface will present a gallery or sequence view of all available image frames associated with the event. This allows the operator to cross-reference multiple angles, lighting conditions, or positions of the same vehicle to deduce the correct license plate.
- **Manual Correction:** Operators can search for a specific capture and manually update the `license_plate` text value.
- **Audit Trail:** Every manual correction must generate an immutable log containing:
  - Timestamp of the correction.
  - Operator ID/Name making the change.
  - Original JSON payload data (pre-correction).
  - New plate data (post-correction).
  - Direct display of the image array for subsequent admin verification.

