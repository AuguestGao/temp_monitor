"""
Shared serial port manager with command queue.
Allows multiple processes to coordinate serial port access.
"""
import logging
import json
import os
import time
from pathlib import Path
from typing import Optional, Tuple, List
from threading import Lock
from config import get_config

logger = logging.getLogger(__name__)
Config = get_config()


class SerialPortManager:
    """
    Manages serial port access and command queue.
    Commands are queued and processed by the serial_ingest.py process.
    """
    
    def __init__(self):
        self._command_queue_file = Config.STORAGE_DIR / 'arduino_commands.json'
        self._lock_file = Config.STORAGE_DIR / 'arduino_commands.lock'
        self._lock = Lock()
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        Config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _acquire_file_lock(self, timeout: float = 1.0) -> bool:
        """
        Acquire a file-based lock for cross-process coordination.
        Returns True if lock acquired, False otherwise.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to create lock file exclusively
                if not self._lock_file.exists():
                    self._lock_file.touch()
                    return True
                # Check if lock file is stale (older than 5 seconds)
                elif time.time() - self._lock_file.stat().st_mtime > 5.0:
                    # Lock file seems stale, remove it
                    try:
                        self._lock_file.unlink()
                        self._lock_file.touch()
                        return True
                    except OSError:
                        pass
            except OSError:
                pass
            time.sleep(0.1)
        return False
    
    def _release_file_lock(self):
        """Release the file-based lock."""
        try:
            if self._lock_file.exists():
                self._lock_file.unlink()
        except OSError:
            pass
    
    def queue_command(self, command: str) -> Tuple[bool, str]:
        """
        Queue a command to be sent to Arduino.
        The serial_ingest.py process will pick it up and send it.
        
        Args:
            command: Command to send (e.g., "START", "STOP", "TOGGLE")
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            if not self._acquire_file_lock():
                return False, "Could not acquire lock. Another process may be accessing the command queue."
            
            try:
                # Read existing queue
                commands = self._read_command_queue()
                
                # Add new command
                commands.append({
                    'command': command,
                    'timestamp': time.time(),
                    'status': 'pending'
                })
                
                # Write back to file
                self._write_command_queue(commands)
                
                logger.info(f"Queued command '{command}' for Arduino")
                return True, f"Command '{command}' queued successfully"
            
            except Exception as e:
                logger.error(f"Error queueing command: {e}", exc_info=True)
                return False, f"Failed to queue command: {str(e)}"
            finally:
                self._release_file_lock()
    
    def get_pending_commands(self) -> List[dict]:
        """
        Get all pending commands from the queue.
        Used by serial_ingest.py to process commands.
        
        Returns:
            List of pending command dictionaries
        """
        with self._lock:
            if not self._acquire_file_lock():
                return []
            
            try:
                commands = self._read_command_queue()
                pending = [cmd for cmd in commands if cmd.get('status') == 'pending']
                return pending
            except Exception as e:
                logger.error(f"Error reading command queue: {e}", exc_info=True)
                return []
            finally:
                self._release_file_lock()
    
    def mark_command_processed(self, command_timestamp: float) -> bool:
        """
        Mark a command as processed.
        Used by serial_ingest.py after sending a command.
        
        Args:
            command_timestamp: Timestamp of the command to mark as processed
        
        Returns:
            True if successfully marked, False otherwise
        """
        with self._lock:
            if not self._acquire_file_lock():
                return False
            
            try:
                commands = self._read_command_queue()
                
                # Mark command as processed
                for cmd in commands:
                    if abs(cmd.get('timestamp', 0) - command_timestamp) < 0.001:
                        cmd['status'] = 'processed'
                        cmd['processed_at'] = time.time()
                        break
                
                # Keep only last 100 commands (cleanup old ones)
                commands = [cmd for cmd in commands if cmd.get('status') == 'processed']
                commands = commands[-100:]
                
                self._write_command_queue(commands)
                return True
            except Exception as e:
                logger.error(f"Error marking command as processed: {e}", exc_info=True)
                return False
            finally:
                self._release_file_lock()
    
    def _read_command_queue(self) -> List[dict]:
        """Read command queue from file."""
        if not self._command_queue_file.exists():
            return []
        
        try:
            with open(self._command_queue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _write_command_queue(self, commands: List[dict]):
        """Write command queue to file."""
        try:
            with open(self._command_queue_file, 'w', encoding='utf-8') as f:
                json.dump(commands, f, indent=2)
        except IOError as e:
            logger.error(f"Error writing command queue: {e}")
            raise


# Global instance
_serial_manager: Optional[SerialPortManager] = None


def get_serial_manager() -> SerialPortManager:
    """Get the global SerialPortManager instance."""
    global _serial_manager
    if _serial_manager is None:
        _serial_manager = SerialPortManager()
    return _serial_manager

