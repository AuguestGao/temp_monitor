from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator


class TemperatureReadingIn(BaseModel):
    room: str = Field(min_length=1)
    valueC: float = Field(ge=-55.0, le=125.0)
    recordedAt: Optional[str] = None  # ISO 8601 string; server may set if omitted
    source: Optional[str] = None

    @field_validator("recordedAt")
    @classmethod
    def validate_iso8601(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if v is None or v == "":
            return None
        # Accept ISO 8601 with optional trailing 'Z'
        try:
            if v.endswith("Z"):
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            else:
                datetime.fromisoformat(v)
        except Exception as exc:  # noqa: BLE001 - surface clean error to client
            raise ValueError("recordedAt must be ISO 8601 timestamp") from exc
        return v


class TemperatureReadingOut(BaseModel):
    id: str
    room: str
    valueC: float
    recordedAt: str  # ISO 8601 string (UTC)
    source: Optional[str] = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


