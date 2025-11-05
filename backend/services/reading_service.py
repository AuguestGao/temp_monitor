"""Reading service for handling temperature reading business logic."""
import logging
from typing import List, Optional
from datetime import datetime
from models.reading import Reading
from storage.reading_storage import ReadingStorage
from utils.timezone_utils import convert_toronto_to_utc
from exceptions import ValidationError

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
        start_datetime_toronto: Optional[str] = None,
        end_datetime_toronto: Optional[str] = None
    ) -> List[Reading]:
        """
        Get temperature readings filtered by date range.
        
        Args:
            start_datetime_toronto: Start datetime string in Toronto timezone (ISO format).
                                  If None, no start filter.
            end_datetime_toronto: End datetime string in Toronto timezone (ISO format).
                                 If None, no end filter.
        
        Returns:
            List of Reading objects within the date range.
            
        Raises:
            ValidationError: If datetime strings are invalid.
        """
        start_datetime_utc: Optional[datetime] = None
        end_datetime_utc: Optional[datetime] = None
        
        # Convert Toronto time to UTC if provided
        if start_datetime_toronto:
            try:
                start_datetime_utc = convert_toronto_to_utc(start_datetime_toronto)
                logger.debug(f"Converted start datetime from Toronto to UTC: {start_datetime_toronto} -> {start_datetime_utc}")
            except ValueError as e:
                logger.error(f"Invalid startDateTime format: {start_datetime_toronto}")
                raise ValidationError(f'Invalid startDateTime format: {e}', field='startDateTime') from e
        
        if end_datetime_toronto:
            try:
                end_datetime_utc = convert_toronto_to_utc(end_datetime_toronto)
                logger.debug(f"Converted end datetime from Toronto to UTC: {end_datetime_toronto} -> {end_datetime_utc}")
            except ValueError as e:
                logger.error(f"Invalid endDateTime format: {end_datetime_toronto}")
                raise ValidationError(f'Invalid endDateTime format: {e}', field='endDateTime') from e
        
        # Validate date range
        if start_datetime_utc and end_datetime_utc and start_datetime_utc > end_datetime_utc:
            logger.warning(f"Start datetime is after end datetime: {start_datetime_utc} > {end_datetime_utc}")
            raise ValidationError('startDateTime must be before or equal to endDateTime', field='startDateTime')
        
        # Read and filter readings from storage
        try:
            readings = self.storage.read_readings(start_datetime_utc, end_datetime_utc)
            logger.info(f"Retrieved {len(readings)} readings")
            return readings
        except IOError as e:
            logger.error(f"Storage error while retrieving readings: {e}")
            # Return empty list on storage errors rather than failing the request
            return []

