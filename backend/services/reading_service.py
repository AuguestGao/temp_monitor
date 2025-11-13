"""Reading service for handling temperature reading business logic."""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
from models.reading import Reading
from storage.reading_storage import ReadingStorage
from exceptions import ValidationError

UTC_TZ = ZoneInfo('UTC')

logger = logging.getLogger(__name__)


class ReadingService:
    """Service for temperature reading operations."""
    
    def __init__(self, storage: Optional[ReadingStorage] = None):
        """
        Initialize reading service with storage.
        
        Args:
            storage: ReadingStorage instance. If None, creates a new one.
        """
        self.storage = storage or ReadingStorage()
    
    def get_readings(
        self,
        start_datetime_utc_str: str,
        end_datetime_utc_str: str
    ) -> List[Reading]:
        """
        Get temperature readings filtered by date range.
        
        Args:
            start_datetime_utc_str: Start datetime string in UTC (ISO format). Required.
            end_datetime_utc_str: End datetime string in UTC (ISO format). Required.
        
        Returns:
            List of Reading objects within the date range.
            
        Raises:
            ValidationError: If datetime strings are invalid or missing.
        """
        # Both parameters are required
        if not start_datetime_utc_str:
            raise ValidationError('startDateTime is required', field='startDateTime')
        if not end_datetime_utc_str:
            raise ValidationError('endDateTime is required', field='endDateTime')
        
        start_datetime_utc: Optional[datetime] = None
        end_datetime_utc: Optional[datetime] = None
        
        # Parse UTC datetime strings
        try:
            # Handle 'Z' suffix or +00:00
            start_str = start_datetime_utc_str.replace('Z', '+00:00')
            start_datetime_utc = datetime.fromisoformat(start_str)
            if start_datetime_utc.tzinfo is None:
                start_datetime_utc = start_datetime_utc.replace(tzinfo=UTC_TZ)
            logger.debug(f"Parsed start datetime UTC: {start_datetime_utc}")
        except ValueError as e:
            logger.error(f"Invalid startDateTime format: {start_datetime_utc_str}")
            raise ValidationError(f'Invalid startDateTime format: {e}', field='startDateTime') from e
        
        try:
            # Handle 'Z' suffix or +00:00
            end_str = end_datetime_utc_str.replace('Z', '+00:00')
            end_datetime_utc = datetime.fromisoformat(end_str)
            if end_datetime_utc.tzinfo is None:
                end_datetime_utc = end_datetime_utc.replace(tzinfo=UTC_TZ)
            logger.debug(f"Parsed end datetime UTC: {end_datetime_utc}")
        except ValueError as e:
            logger.error(f"Invalid endDateTime format: {end_datetime_utc_str}")
            raise ValidationError(f'Invalid endDateTime format: {e}', field='endDateTime') from e
        
        # Validate date range
        if start_datetime_utc > end_datetime_utc:
            logger.warning(f"Start datetime is after end datetime: {start_datetime_utc} > {end_datetime_utc}")
            raise ValidationError('startDateTime must be before or equal to endDateTime', field='startDateTime')
        
        # Get filtered readings from in-memory storage
        raw_readings = self.storage.read_readings(start_datetime_utc, end_datetime_utc)
        logger.info(f"Retrieved {len(raw_readings)} raw readings")
        
        # Group readings by minute and calculate averages
        averaged_readings = self._average_by_minute(raw_readings)
        logger.info(f"Averaged to {len(averaged_readings)} readings (one per minute)")
        
        return averaged_readings
    
    def _average_by_minute(self, readings: List[Reading]) -> List[Reading]:
        """
        Group readings by minute and calculate average temperature for each minute.
        
        Args:
            readings: List of Reading objects
            
        Returns:
            List of Reading objects with averaged temperatures, one per minute
        """
        if not readings:
            return []
        
        # Group readings by minute (truncate seconds and microseconds)
        minute_groups: Dict[datetime, List[float]] = defaultdict(list)
        
        for reading in readings:
            # Parse the UTC datetime from the reading
            recorded_at_str = reading.recordedAt.replace('Z', '+00:00')
            recorded_at_utc = datetime.fromisoformat(recorded_at_str)
            
            # Ensure timezone is set to UTC
            if recorded_at_utc.tzinfo is None:
                recorded_at_utc = recorded_at_utc.replace(tzinfo=UTC_TZ)
            
            # Truncate to minute (remove seconds and microseconds)
            minute_key = recorded_at_utc.replace(second=0, microsecond=0)
            
            # Add temperature to the group for this minute
            minute_groups[minute_key].append(reading.tempC)
        
        # Calculate average for each minute and create Reading objects
        averaged_readings: List[Reading] = []
        for minute_dt, temperatures in sorted(minute_groups.items()):
            # Calculate average temperature
            avg_temp = sum(temperatures) / len(temperatures)
            
            # Create ISO format timestamp for this minute (UTC)
            minute_iso = minute_dt.isoformat().replace('+00:00', 'Z')
            
            # Create Reading object with averaged temperature
            averaged_reading = Reading(
                tempC=round(avg_temp, 2),  # Round to 2 decimal places
                recordedAt=minute_iso
            )
            averaged_readings.append(averaged_reading)
        
        return averaged_readings

