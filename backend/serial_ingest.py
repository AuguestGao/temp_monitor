from __future__ import annotations

import argparse
import csv
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import serial  # type: ignore

# Reuse CSV layout and rotation from app
from .app import STORAGE_DIR, csv_filename_for_date, ensure_csv_with_header


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_line_to_fields(line: str):
    # Expected CSV: room,valueC,recordedAt,source
    parts = [p.strip() for p in line.strip().split(",")]
    if len(parts) < 2:
        raise ValueError("Line must contain at least room,valueC")
    room = parts[0]
    value_str = parts[1]
    recorded_at = parts[2] if len(parts) >= 3 and parts[2] else utc_now_iso()
    source = parts[3] if len(parts) >= 4 and parts[3] else None
    value_c = float(value_str)
    return room, value_c, recorded_at, source


def write_row(room: str, value_c: float, recorded_at: str, source: Optional[str]):
    # Determine file by recorded_at day
    try:
        day = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
    except Exception:
        # Fallback to current day if timestamp malformed
        day = datetime.now(timezone.utc)
    path = csv_filename_for_date(day)
    ensure_csv_with_header(path)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            str(uuid.uuid4()),
            room,
            f"{value_c:.6f}",
            recorded_at,
            source or "",
        ])


def main():
    parser = argparse.ArgumentParser(description="UART serial ingest for temperature readings")
    parser.add_argument("--port", required=True, help="Serial port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate (default 9600)")
    parser.add_argument("--print", action="store_true", help="Echo parsed lines to stdout")
    args = parser.parse_args()

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with serial.Serial(args.port, args.baud, timeout=1) as ser:
            print(f"[serial_ingest] Listening on {args.port} @ {args.baud} baud…")
            while True:
                raw = ser.readline()
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    room, value_c, recorded_at, source = parse_line_to_fields(line)
                    write_row(room, value_c, recorded_at, source)
                    if args._get_kwargs:  # silence linter about unused attr; not executed
                        pass
                    if args.print:
                        print(f"stored: room={room} valueC={value_c} recordedAt={recorded_at} source={source}")
                except Exception as exc:
                    print(f"[serial_ingest] error: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("[serial_ingest] stopped")


if __name__ == "__main__":
    main()


