"""Temperature reading routes."""
import logging
from typing import Tuple, Optional, Dict, Any
from flask import Blueprint, jsonify, request, Response
from services.reading_service import ReadingService
from utils.auth_middleware import require_auth
from utils.timezone_utils import convert_utc_to_toronto
from constants import HTTP_OK

logger = logging.getLogger(__name__)

# Create a Blueprint for readings routes
readings_bp = Blueprint('readings', __name__)

# Initialize reading service
reading_service = ReadingService()


@readings_bp.route('/api/readings', methods=['GET'])
@require_auth
def get_readings() -> Tuple[Response, int]:
    """
    Get temperature readings filtered by date range, averaged by minute.
    
    Query parameters:
        startDateTime: Start datetime in UTC (ISO format, required)
                      Example: "2025-11-04T10:00:00Z"
        endDateTime: End datetime in UTC (ISO format, required)
                    Example: "2025-11-04T11:00:00Z"
    
    Returns:
        JSON response with filtered readings (averaged per minute):
        {
            "message": "Readings retrieved",
            "count": <number>,
            "readings": [<Reading objects with averaged temperatures, one per minute>]
        }
        
    Raises:
        ValidationError: If datetime strings are missing, invalid, or startDateTime > endDateTime
    """
    start_datetime_str: Optional[str] = request.args.get('startDateTime')
    end_datetime_str: Optional[str] = request.args.get('endDateTime')
    
    logger.info(
        f"Retrieving readings - startDateTime: {start_datetime_str}, endDateTime: {end_datetime_str}"
    )
    
    # Get readings from service (handles timezone conversion and filtering)
    # Both startDateTime and endDateTime are required
    readings = reading_service.get_readings(start_datetime_str or '', end_datetime_str or '')
    
    # Convert to dictionary format and convert UTC timestamps to Toronto time
    readings_data: list[Dict[str, Any]] = []
    for reading in readings:
        reading_dict = reading.to_dict()
        # Convert recordedAt from UTC to Toronto time
        try:
            reading_dict['recordedAt'] = convert_utc_to_toronto(reading_dict['recordedAt'])
        except ValueError as e:
            logger.warning(f"Failed to convert timestamp to Toronto time: {e}, keeping original")
            # Keep original timestamp if conversion fails
        
        readings_data.append(reading_dict)
    
    logger.info(f"Returning {len(readings_data)} readings")
    
    return jsonify({
        'message': 'Readings retrieved',
        'count': len(readings_data),
        'readings': readings_data
    }), HTTP_OK

