"""Temperature reading data model."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Reading:
    """Temperature reading model."""
    tempC: float
    recordedAt: str
    
    def to_dict(self) -> dict:
        """Convert reading to dictionary."""
        return {
            'tempC': self.tempC,
            'recordedAt': self.recordedAt
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['Reading']:
        """Create Reading from dictionary."""
        if not data or 'tempC' not in data or 'recordedAt' not in data:
            return None
        return cls(
            tempC=data['tempC'],
            recordedAt=data['recordedAt']
        )
    
    @classmethod
    def create_now(cls, tempC: float) -> 'Reading':
        """Create a reading with current timestamp."""
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        return cls(
            tempC=tempC,
            recordedAt=timestamp
        )

