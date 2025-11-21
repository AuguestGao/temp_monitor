"""
Service for controlling Arduino via serial communication.
Uses a command queue system to coordinate with serial_ingest.py.
"""
import logging
from typing import Tuple
from services.serial_manager import get_serial_manager

logger = logging.getLogger(__name__)


class ArduinoService:
    """Service for sending commands to Arduino via serial port."""
    
    def __init__(self):
        self._serial_manager = get_serial_manager()
    
    def send_command(self, command: str) -> Tuple[bool, str]:
        """
        Queue a command to be sent to Arduino.
        The serial_ingest.py process will pick it up and send it.
        
        Args:
            command: Command to send (e.g., "START", "STOP", "TOGGLE")
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        return self._serial_manager.queue_command(command)
    
    def start(self) -> Tuple[bool, str]:
        """Send START command to Arduino."""
        return self.send_command("START")
    
    def stop(self) -> Tuple[bool, str]:
        """Send STOP command to Arduino."""
        return self.send_command("STOP")
    
    def toggle(self) -> Tuple[bool, str]:
        """Send TOGGLE command to Arduino."""
        return self.send_command("TOGGLE")
    

