### Temperature Monitoring System — Project Document

#### Overview
A system to capture room temperature readings via an Arduino temperature sensor, transmit them to a Python/Flask server over UART (USB serial), persist the data to CSV files, and visualize it in a React + TypeScript web app with date range and room filters.

#### Goals
- Collect temperature in Celsius from Arduino-connected sensors.
- Send readings to backend over USB serial (UART).
- Persist readings reliably in CSV with timestamps and room identification.
- Provide APIs to ingest and retrieve readings.
- Visualize and filter readings by date range and room in a web UI.

---

### Architecture
- **Hardware**: Arduino + temperature sensor (e.g., DS18B20, DHT22, TMP36)
- **Transport**: USB (UART Serial)
- **Backend**: Python 3 + Flask
- **Storage**: CSV files (rotated by day)
- **Frontend**: React + TypeScript (Vite or CRA)

```
Sensor → Arduino → (UART over USB) → Serial Ingest → CSV Storage → Flask API → React App
```

---

### Data Model
- **TemperatureReading**
  - `id`: string/UUID
  - `room`: string (e.g., "101", "Lab-A")
  - `valueC`: number (Celsius)
  - `recordedAt`: ISO 8601 timestamp (device time or server-ingest time)
  - `source`: string (e.g., "arduino-01")

CSV storage (header + sample row):
```
id,room,valueC,recordedAt,source
6d0c...,101,23.6,2025-10-30T10:15:00Z,arduino-01
```
Rotation policy: one CSV file per day per environment, e.g., `storage/2025-10-30_readings.csv`.

---

### Communication from Arduino
Mode: **USB Serial (UART)**
- Arduino prints newline-delimited rows. Recommended format is CSV to match storage. Fields: `room,valueC,recordedAt,source`.
- Example CSV line: `101,23.6,2025-10-30T10:15:00Z,arduino-01`
- A Python serial-ingest process (`serial_ingest.py`) reads UART and writes to the daily CSV, assigning a UUID per record.

Serial framing recommendation (robust): one record per line; optional checksum field if needed.

---

### Backend (Flask) API

Base URL: `/api`

1) Ingest readings
- **POST** `/api/reading`
- Body (JSON) — optional for non-UART clients (Arduino uses UART ingestion):
```json
{
  "room": "101",
  "valueC": 23.6,
  "recordedAt": "2025-10-30T10:15:00Z",
  "source": "arduino-01"
}
```
- Responses:
  - 201 Created `{ "id": "<uuid>", "status": "stored" }`
  - 400 on validation errors; 415 on non-JSON; 500 on server error

2) Retrieve readings (filtered)
- **GET** `/api/readings`
- Query params:
  - `from` ISO 8601 (inclusive)
  - `to` ISO 8601 (exclusive or inclusive; choose inclusive for simplicity)
  - `room` string (optional; repeatable or comma-separated)
  - `limit` integer (optional, default 1000, max 10000)
- Example: `/api/readings?from=2025-10-30T00:00:00Z&to=2025-10-31T00:00:00Z&room=101`
- Response (200):
```json
{
  "items": [
    {
      "id": "6d0c...",
      "room": "101",
      "valueC": 23.6,
      "recordedAt": "2025-10-30T10:15:00Z",
      "source": "arduino-01"
    }
  ],
  "count": 1
}
```

Validation rules:
- `room`: non-empty string
- `valueC`: finite number between -55 and 125 (depends on sensor)
- `recordedAt`: valid ISO 8601; if omitted, server sets now (UTC)

Security considerations:
- For LAN deployments, consider an API key header (e.g., `X-API-Key`) or mutual TLS.
- Rate-limit ingest endpoint to mitigate floods.

---

### Frontend (React + TypeScript)
Features:
- Date range selector (start/end) and room selector (single or multi-select)
- Table and chart (line chart) of temperature over time
- Auto-refresh toggle (e.g., 10s interval)

Core UI elements:
- Controls: `DateRangePicker`, `RoomSelect`, `RefreshButton`
- Views: `TemperatureChart`, `ReadingsTable`

API integration:
- Fetch from `/api/readings` with query params derived from UI controls
- Display loading/errors; debounce filter changes

Type definitions:
```ts
export type TemperatureReading = {
  id: string;
  room: string;
  valueC: number;
  recordedAt: string; // ISO
  source?: string;
};
```

---

### Directory Structure (proposed)
```
temp_monitor/
  arduino/
    firmware/                 # Arduino sketches
  backend/
    app.py                    # Flask entry
    schemas.py                # Pydantic/validation
    serial_ingest.py          # optional USB serial reader
    requirements.txt
  storage/
    .gitkeep                  # CSV files stored here, rotated per day
  frontend/
    src/
      components/
      pages/
      types/
      api/
    package.json
    tsconfig.json
    vite.config.ts
  README.md
```

---

### Deployment & Ops
- Dev: CSV files; run Flask with `flask run`; Vite dev server for frontend
- Prod: CSV files on durable disk; systemd or Docker for backend; Nginx reverse proxy (serve frontend, proxy `/api`)
- Time & TZ: store and serve in UTC; convert in UI if needed

---

### Testing Strategy
- Backend: unit tests for validation; integration tests for endpoints; seed data
- Frontend: component tests for filters; e2e happy path (load, filter, render)
- Hardware loop: simulate sensor payloads for CI

---

### Open Questions
- Which sensor model exactly? (affects calibration and range)
- Will Arduino keep accurate time or should server timestamp on ingest?
- Authentication needs beyond LAN? (tokens, TLS)
- Expected data volume and retention policy?

---

### Quick Start (placeholder)
Backend
```bash
uv sync
cd backend
uv run main.py
```


