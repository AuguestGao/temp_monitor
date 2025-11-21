### Temperature Monitoring System — Project Document

#### Overview
A system to capture temperature readings via an Arduino temperature sensor, transmit them to a Python/Flask server over UART (USB serial), persist the data to CSV files, and visualize it in a React + TypeScript web app with date range filters. Includes JWT-based authentication, rate limiting, and comprehensive test coverage.

#### Goals
- Collect temperature in Celsius from Arduino-connected sensors.
- Send readings to backend over USB serial (UART).
- Control Arduino remotely via web interface (start/stop/toggle temperature reading).
- Persist readings reliably in CSV with timestamps.
- Provide APIs to ingest and retrieve readings.
- Visualize and filter readings by date range in a web UI.
- Secure API with JWT authentication and rate limiting.

---

### Architecture
- **Hardware**: Arduino + temperature sensor (e.g., DS18B20, DHT22, TMP36)
- **Transport**: USB (UART Serial)
- **Backend**: Python 3.9+ + Flask + JWT Authentication
- **Storage**: CSV files (rotated by day) + JSON (user data)
- **Frontend**: React + TypeScript (Vite or CRA)
- **Authentication**: JWT with access/refresh tokens
- **Security**: Rate limiting, password hashing (bcrypt), token blacklisting

```
Sensor → Arduino ↔ (UART over USB) ↔ Serial Ingest ↔ CSV Storage ↔ Flask API (JWT Auth) ↔ React App
                                                                    ↕
                                                              Arduino Control
```

---

### Data Model
- **TemperatureReading**
  - `recordedAt`: ISO 8601 timestamp (device time or server-ingest time; used as identifier)
  - `tempC`: number (Celsius)

CSV storage (header + sample row):
```
recordedAt,tempC
2025-10-30T10:15:00Z,23.6
```
Rotation policy: one CSV file per day per environment, e.g., `storage/2025-10-30_readings.csv`.

---

### Communication with Arduino
Mode: **USB Serial (UART) - Bidirectional**

**Arduino → Backend (Temperature Readings):**
- Arduino prints newline-delimited rows. Recommended format is CSV to match storage. Fields: `recordedAt,tempC`.
- Example CSV line: `2025-10-30T10:15:00Z,23.6`
- A Python serial-ingest process (`serial_ingest.py`) reads UART and writes to the daily CSV, using `recordedAt` as the identifier.

**Backend → Arduino (Control Commands):**
- Backend sends commands via serial: `START`, `STOP`, `TOGGLE`
- Arduino firmware listens for these commands and controls temperature reading state
- Commands can be sent via web UI or API endpoints

Serial framing recommendation (robust): one record per line; optional checksum field if needed.

---

### Backend (Flask) API

Base URL: `/api`

#### Health Endpoints
- **GET** `/` - Root health check with API version
- **GET** `/api/health` - Health status endpoint

#### Authentication Endpoints

1) **Sign Up**
- **POST** `/api/signup`
- Body (JSON):
```json
{
  "username": "user123",
  "password": "securepass123"
}
```
- Responses:
  - 201 Created: `{ "message": "User signed up", "access_token": "...", "refresh_token": "..." }`
  - 400 Bad Request: Validation errors (username 3-50 chars alphanumeric+underscore, password 6-128 chars)
  - 429 Too Many Requests: Rate limit exceeded

2) **Login**
- **POST** `/api/login`
- Body (JSON):
```json
{
  "username": "user123",
  "password": "securepass123"
}
```
- Responses:
  - 200 OK: `{ "message": "Login successful", "access_token": "...", "refresh_token": "..." }`
  - 401 Unauthorized: Invalid credentials
  - 404 Not Found: User doesn't exist
  - 429 Too Many Requests: Rate limit exceeded (5 attempts per 5 minutes, 15 min lockout)

3) **Refresh Token**
- **POST** `/api/refresh-token`
- Headers: `Authorization: Bearer <refresh_token>`
- Responses:
  - 200 OK: `{ "message": "Token refreshed", "access_token": "...", "refresh_token": "..." }`
  - 401 Unauthorized: Invalid/expired/revoked token

4) **Logout**
- **POST** `/api/logout`
- Headers: `Authorization: Bearer <access_token>` (optional, idempotent)
- Body (optional JSON):
```json
{
  "revoke_all": true  // Logout from all devices
}
```
- Responses:
  - 200 OK: `{ "message": "Logged out successfully" }` or `{ "message": "Logged out from all devices", "revoked_tokens": 2 }`

5) **Reset Rate Limit**
- **POST** `/api/rate-limit/reset`
- Body (optional JSON):
```json
{
  "reset_key": "clear",  // Required for reset all
  "username": "user123"  // Optional, to reset specific username
}
```

#### Temperature Reading Endpoints

1) **Ingest readings**
- **POST** `/api/reading`
- Headers: `Authorization: Bearer <access_token>` (if auth required)
- Body (JSON):
```json
{
  "valueC": 23.6,
  "recordedAt": "2025-10-30T10:15:00Z"  // Optional, defaults to now (UTC)
}
```
- Responses:
  - 201 Created: `{ "message": "Reading created", "reading": { "tempC": 23.6, "recordedAt": "2025-10-30T10:15:00Z" } }`
  - 400 Bad Request: Validation errors
  - 422 Unprocessable Entity: Temperature out of range

2) **Retrieve readings (filtered)**
- **GET** `/api/readings`
- Headers: `Authorization: Bearer <access_token>` (if auth required)
- Query params:
  - `startDateTime`: ISO 8601 (required)
  - `endDateTime`: ISO 8601 (required)
- Example: `/api/readings?startDateTime=2025-10-30T00:00:00Z&endDateTime=2025-10-31T00:00:00Z`
- Response (200):
```json
{
  "message": "Readings retrieved",
  "count": 100,
  "readings": [...]
}
```

#### Arduino Control Endpoints

All endpoints require authentication via `Authorization: Bearer <access_token>` header.

1) **Start Arduino**
- **POST** `/api/arduino/start`
- Headers: `Authorization: Bearer <access_token>`
- Responses:
  - 200 OK: `{ "message": "Command 'START' sent successfully", "status": "success" }`
  - 500 Internal Server Error: `{ "message": "Failed to connect to Arduino: ...", "status": "error" }`

2) **Stop Arduino**
- **POST** `/api/arduino/stop`
- Headers: `Authorization: Bearer <access_token>`
- Responses:
  - 200 OK: `{ "message": "Command 'STOP' sent successfully", "status": "success" }`
  - 500 Internal Server Error: `{ "message": "Failed to connect to Arduino: ...", "status": "error" }`

3) **Toggle Arduino**
- **POST** `/api/arduino/toggle`
- Headers: `Authorization: Bearer <access_token>`
- Responses:
  - 200 OK: `{ "message": "Command 'TOGGLE' sent successfully", "status": "success" }`
  - 500 Internal Server Error: `{ "message": "Failed to connect to Arduino: ...", "status": "error" }`

**Note:** The Arduino service auto-detects the Arduino serial port by vendor ID or common port names. If multiple Arduinos are connected, it will use the first one found.

**Validation rules:**
- `recordedAt`: valid ISO 8601; if omitted, server sets now (UTC)
- `valueC` (tempC): finite number between -55 and 125 (Celsius)
- `username`: 3-50 alphanumeric characters + underscore
- `password`: 6-128 characters

**JWT Token Details:**
- Access tokens: 15 minutes expiry
- Refresh tokens: 7 days expiry
- Token rotation on refresh (old refresh token revoked, new one issued)
- Token blacklisting on logout

---

### Frontend (React + TypeScript)
Features:
- Date range selector (start/end)
- Line chart of temperature over time
- **Arduino control buttons** (Start, Stop, Toggle) with real-time status feedback
- Loading states and error handling

Core UI elements:
- Controls: `DateRangePicker`, `ArduinoControlButtons`
- Views: `TemperatureChart`

API integration:
- Fetch from `/api/readings` with query params derived from UI controls
- Send commands to `/api/arduino/start`, `/api/arduino/stop`, `/api/arduino/toggle`
- Display loading/errors; real-time status updates

Type definitions:
```ts
export type TemperatureReading = {
  recordedAt: string; // DateTime UTC (used as identifier)
  tempC: number;
};

export type ArduinoResponse = {
  message: string;
  status: 'success' | 'error';
};
```

---

### Directory Structure
```
temp_monitor/
  firmware/
    read_temp_c/              # Arduino sketches
      read_temp_c.ino
  backend/
    main.py                    # Flask entry point
    config.py                  # Configuration management
    constants.py               # HTTP status codes and constants
    exceptions.py              # Custom exception classes
    errors.py                  # Error handlers
    pyproject.toml            # Project dependencies (uv)
    models/                    # Data models
      reading.py               # Reading dataclass
      user.py                  # User model
    routes/                    # API route blueprints
      auth.py                  # Authentication routes
      health.py                # Health check routes
      readings.py              # Temperature reading routes
      arduino.py               # Arduino control routes
    services/                  # Business logic services
      user_service.py          # User management
      jwt_service.py           # JWT token operations
      token_storage.py         # Token storage (in-memory)
      arduino_service.py       # Arduino serial communication service
      reading_service.py       # Temperature reading service
    storage/                   # File storage
      file_storage.py          # File storage abstraction
      users.json               # User data (JSON)
      temp_data.csv            # Temperature readings (CSV)
    utils/                     # Utilities
      auth_middleware.py       # JWT authentication decorators
      rate_limiter.py          # Rate limiting
      validators.py            # Input validation
      logging_config.py        # Logging setup
      middleware.py            # Request/response logging
    backgroundJob/
      serial_ingest.py         # USB serial reader for Arduino
    tests/                     # Test suite
      conftest.py              # Pytest fixtures
      test_auth.py             # Authentication tests (21 tests)
      test_health.py           # Health endpoint tests (4 tests)
  README.md
```

---

### Deployment & Ops
- Dev: CSV files; run Flask with `flask run`; Vite dev server for frontend
- Prod: CSV files on durable disk; systemd or Docker for backend; Nginx reverse proxy (serve frontend, proxy `/api`)
- Time & TZ: store and serve in UTC; convert in UI if needed

---

### Testing Strategy

**Backend Testing:**
- **Framework**: pytest + pytest-flask
- **Coverage**: 25 tests total
  - Health endpoints: 4 tests
  - Authentication endpoints: 21 tests (signup, login, refresh, logout, rate limiting)
- **Test Isolation**: Each test uses isolated temporary storage, no production data modification
- **Run tests**: `cd backend && uv run pytest tests/ -v`
- **Run specific tests**: `uv run pytest tests/test_auth.py::TestLogin -v`
- **Run excluding slow tests**: `uv run pytest -m "not slow"`

**Test Features:**
- Automatic cleanup of test users after each test
- Isolated storage directories per test
- In-memory token storage and rate limiter reset between tests
- Module reloading ensures test config is used

**Frontend Testing (planned):**
- Component tests for filters
- E2E happy path (load, filter, render)
- Hardware loop: simulate sensor payloads for CI

---

### Security Features
- **JWT Authentication**: Access and refresh token pattern with token rotation
- **Password Hashing**: bcrypt with automatic salt generation
- **Rate Limiting**: In-memory rate limiting for signup/login (5 attempts per 5 minutes, 15 min lockout)
- **Token Blacklisting**: Revoked tokens are blacklisted until expiry
- **Input Validation**: Comprehensive validation for all inputs
- **Error Handling**: Standardized error responses with proper HTTP status codes
- **Request Logging**: All requests and responses are logged

### Technology Stack
- **Backend**: Python 3.9+, Flask 3.1.2, PyJWT 2.8.0, bcrypt 5.0.0
- **Package Management**: uv (modern Python package manager)
- **Testing**: pytest 7.4.0, pytest-flask 1.3.0
- **Serial Communication**: pyserial 3.5
- **CORS**: flask-cors 4.0.0

### Open Questions
- Which sensor model exactly? (affects calibration and range)
- Will Arduino keep accurate time or should server timestamp on ingest? (Currently: server timestamps on ingest)
- Expected data volume and retention policy?

---

### Quick Start

#### Prerequisites
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- Arduino IDE (for firmware)

#### Backend Setup
```bash
# Install dependencies
cd backend
uv sync

# Run the Flask server
uv run python main.py
# Server runs on http://0.0.0.0:5000 by default

# Run tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_auth.py -v
```

#### Environment Variables
All configuration can be overridden via environment variables:
```bash
# Flask
export SECRET_KEY="your-secret-key"
export FLASK_DEBUG="True"
export HOST="0.0.0.0"
export PORT="5000"

# JWT
export JWT_SECRET_KEY="jwt-secret-key"
export JWT_ACCESS_TOKEN_EXPIRES_IN="900"  # 15 minutes
export JWT_REFRESH_TOKEN_EXPIRES_IN="604800"  # 7 days

# Rate Limiting
export RATE_LIMIT_MAX_ATTEMPTS="5"
export RATE_LIMIT_WINDOW_SECONDS="300"  # 5 minutes
export RATE_LIMIT_LOCKOUT_DURATION="900"  # 15 minutes
export RATE_LIMIT_RESET_KEY="clear"

# Temperature Validation
export TEMP_MIN_CELSIUS="-55.0"
export TEMP_MAX_CELSIUS="125.0"

# API Configuration
export API_READINGS_DEFAULT_LIMIT="1000"
export API_READINGS_MAX_LIMIT="10000"
```

#### Serial Ingest (Arduino)
```bash
# Run serial ingest script to read from Arduino
cd backend

# Auto-detect Arduino port
uv run python backgroundJob/serial_ingest.py

# Or specify serial port explicitly
uv run python backgroundJob/serial_ingest.py COM3        # Windows
uv run python backgroundJob/serial_ingest.py /dev/ttyUSB0 # Linux/Raspberry Pi
uv run python backgroundJob/serial_ingest.py /dev/tty.usbserial* # macOS

# The script will:
# - Auto-detect Arduino by vendor ID or common port names
# - Write temperature readings to storage/temp_data.csv
# - Validate temperature range (-55°C to 125°C)
# - Generate UTC timestamps for each reading
```

#### Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev
# Frontend runs on http://localhost:5173 by default (Vite)

# Build for production
npm run build
```

**Frontend Features:**
- Login/Signup pages with JWT authentication
- Dashboard with temperature readings chart
- Date range filtering
- Arduino control buttons (Start/Stop/Toggle) with status feedback
- Real-time error handling and loading states

#### Example API Usage
```bash
# Sign up
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Create reading (with auth token)
curl -X POST http://localhost:5000/api/reading \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"valueC": 23.6}'

# Get readings
curl http://localhost:5000/api/readings?startDateTime=2025-10-30T00:00:00Z&endDateTime=2025-10-31T00:00:00Z \
  -H "Authorization: Bearer <access_token>"

# Control Arduino - Start
curl -X POST http://localhost:5000/api/arduino/start \
  -H "Authorization: Bearer <access_token>"

# Control Arduino - Stop
curl -X POST http://localhost:5000/api/arduino/stop \
  -H "Authorization: Bearer <access_token>"

# Control Arduino - Toggle
curl -X POST http://localhost:5000/api/arduino/toggle \
  -H "Authorization: Bearer <access_token>"
```


