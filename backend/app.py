from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from dateutil import parser as dtparser
from flask import Flask, jsonify, request

from .schemas import TemperatureReadingIn, TemperatureReadingOut, utc_now_iso


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def iso_to_dt(value: str) -> datetime:
    # Accept ISO with trailing Z
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return dtparser.isoparse(value)


def dt_to_iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def csv_filename_for_date(day: datetime) -> Path:
    return STORAGE_DIR / f"{day.date().isoformat()}_readings.csv"


def ensure_csv_with_header(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "room", "valueC", "recordedAt", "source"])  # header


def write_reading(reading: TemperatureReadingOut) -> None:
    recorded_dt = iso_to_dt(reading.recordedAt)
    path = csv_filename_for_date(recorded_dt)
    ensure_csv_with_header(path)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            reading.id,
            reading.room,
            f"{reading.valueC:.6f}",
            reading.recordedAt,
            reading.source or "",
        ])


def daterange_inclusive(start: datetime, end: datetime) -> Iterable[datetime]:
    cur = start.date()
    last = end.date()
    while cur <= last:
        yield datetime.combine(cur, datetime.min.time(), tzinfo=timezone.utc)
        cur = cur + timedelta(days=1)


def read_readings(from_dt: datetime, to_dt: datetime, rooms: Optional[List[str]], limit: int) -> List[TemperatureReadingOut]:
    results: List[TemperatureReadingOut] = []
    for day in daterange_inclusive(from_dt, to_dt):
        path = csv_filename_for_date(day)
        if not path.exists():
            continue
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    recorded_at = row["recordedAt"]
                    dt_val = iso_to_dt(recorded_at)
                except Exception:
                    continue
                if dt_val < from_dt or dt_val > to_dt:
                    continue
                if rooms and row["room"] not in rooms:
                    continue
                item = TemperatureReadingOut(
                    id=row["id"],
                    room=row["room"],
                    valueC=float(row["valueC"]),
                    recordedAt=dt_to_iso_utc(dt_val),
                    source=row.get("source") or None,
                )
                results.append(item)
                if len(results) >= limit:
                    return results
    return results


def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/api/reading")
    def ingest_reading():
        if not request.is_json:
            return jsonify({"error": "Expected application/json"}), 415
        try:
            payload = TemperatureReadingIn(**request.get_json())
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": "Validation failed", "detail": str(exc)}), 400

        recorded_at = payload.recordedAt or utc_now_iso()
        out = TemperatureReadingOut(
            id=str(uuid.uuid4()),
            room=payload.room,
            valueC=float(payload.valueC),
            recordedAt=recorded_at,
            source=payload.source,
        )
        try:
            write_reading(out)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": "Failed to store reading"}), 500
        return jsonify({"id": out.id, "status": "stored"}), 201

    @app.get("/api/readings")
    def get_readings():
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        if not from_str or not to_str:
            return jsonify({"error": "Query params 'from' and 'to' are required (ISO 8601)"}), 400
        try:
            from_dt = iso_to_dt(from_str)
            to_dt = iso_to_dt(to_str)
        except Exception:  # noqa: BLE001
            return jsonify({"error": "Invalid ISO 8601 in 'from' or 'to'"}), 400
        if to_dt < from_dt:
            return jsonify({"error": "'to' must be >= 'from'"}), 400

        rooms_param = request.args.get("room")
        rooms: Optional[List[str]] = None
        if rooms_param:
            rooms = [r for r in (s.strip() for s in rooms_param.split(",")) if r]

        try:
            limit = int(request.args.get("limit", "1000"))
        except Exception:
            return jsonify({"error": "'limit' must be an integer"}), 400
        limit = max(1, min(limit, 10000))

        items = read_readings(from_dt, to_dt, rooms, limit)
        return jsonify({
            "items": [item.model_dump() for item in items],
            "count": len(items),
        })

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)


