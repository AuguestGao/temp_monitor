"""Serial ingest script to capture Arduino serial data and write to CSV."""
import serial
import serial.tools.list_ports
import csv
import logging
from datetime import datetime, timezone
import time
import sys
import platform
import os

# Import configuration
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import get_config, get_default_serial_ports
from utils.logging_config import setup_logging
from services.serial_manager import get_serial_manager

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Get configuration
Config = get_config()

# Configuration from config module
BAUD_RATE = Config.SERIAL_BAUD_RATE
CSV_FILE = Config.TEMP_DATA_CSV_FILE
DEFAULT_PORTS = get_default_serial_ports()


def find_arduino_port():
    """Auto-detect Arduino serial port by checking common ports."""
    # First, try to find via USB VID/PID (more reliable)
    for port in serial.tools.list_ports.comports():
        # Common Arduino vendor IDs from config
        if port.vid and port.vid in Config.ARDUINO_VENDOR_IDS:
            logger.info(f"Found Arduino-like device at: {port.device}")
            print(f"Found Arduino-like device at: {port.device}")
            return port.device
    
    # Fallback: try common port names
    for port_name in DEFAULT_PORTS:
        try:
            # Try to open the port to verify it exists
            test_ser = serial.Serial(port_name, BAUD_RATE, timeout=0.5)
            test_ser.close()
            logger.info(f"Found serial port: {port_name}")
            print(f"Found serial port: {port_name}")
            return port_name
        except (serial.SerialException, OSError, ValueError):
            # ValueError can occur if port name is invalid
            continue
    
    return None


def list_available_ports():
    """List all available serial ports."""
    ports = serial.tools.list_ports.comports()
    if ports:
        print("\nAvailable serial ports:")
        for port in ports:
            desc = port.description if port.description else "Unknown"
            print(f"  - {port.device}: {desc}")
    else:
        print("\nNo serial ports found.")

def ensure_csv_header(file_path):
    """Ensure CSV file exists with header row."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['recordedAt', 'tempC'])

def check_permissions(port_path):
    """Check if user has permissions to access the serial port."""
    if platform.system() == 'Linux':
        if not os.access(port_path, os.R_OK | os.W_OK):
            logger.error(f"Permission denied for {port_path}")
            print(f"\n⚠️  Permission denied for {port_path}")
            print("You may need to:")
            print("  1. Add your user to the 'dialout' group:")
            print("     sudo usermod -a -G dialout $USER")
            print("  2. Log out and log back in (or restart)")
            print("  3. Or run with sudo (not recommended)")
            return False
    return True


def main():
    """Main serial ingest loop."""
    # Get serial port from command line argument or auto-detect
    if len(sys.argv) > 1:
        serial_port = sys.argv[1]
        print(f"Using specified port: {serial_port}")
    else:
        print("Auto-detecting Arduino serial port...")
        serial_port = find_arduino_port()
        
        if not serial_port:
            print("❌ Could not auto-detect Arduino port")
            list_available_ports()
            print("\nUsage: python serial_ingest.py [PORT]")
            print("Example: python serial_ingest.py /dev/ttyUSB0")
            sys.exit(1)
    
    # Check permissions (especially important on Raspberry Pi)
    if not check_permissions(serial_port):
        sys.exit(1)
    
    logger.info(f"Connecting to serial port {serial_port} at {BAUD_RATE} baud...")
    print(f"Connecting to serial port {serial_port} at {BAUD_RATE} baud...")
    
    try:
        ser = serial.Serial(serial_port, BAUD_RATE, timeout=Config.SERIAL_TIMEOUT)
        logger.info(f"Connected to serial port {serial_port}. Writing to {CSV_FILE}")
        print(f"✅ Connected! Reading data and writing to {CSV_FILE}")
        print("Press Ctrl+C to stop\n")
        
        ensure_csv_header(CSV_FILE)
        
        # Initialize serial manager for command processing
        serial_manager = get_serial_manager()
        last_command_check = time.time()
        COMMAND_CHECK_INTERVAL = 0.5  # Check for commands every 0.5 seconds
        
        while True:
            # Check for pending commands and send them
            current_time = time.time()
            if current_time - last_command_check >= COMMAND_CHECK_INTERVAL:
                pending_commands = serial_manager.get_pending_commands()
                for cmd in pending_commands:
                    try:
                        command = cmd.get('command', '')
                        command_timestamp = cmd.get('timestamp', 0)
                        
                        # Send command to Arduino
                        command_with_newline = f"{command}\n"
                        ser.write(command_with_newline.encode('utf-8'))
                        ser.flush()
                        
                        logger.info(f"Sent queued command '{command}' to Arduino")
                        print(f"📤 Sent command: {command}")
                        
                        # Mark command as processed
                        serial_manager.mark_command_processed(command_timestamp)
                    except Exception as e:
                        logger.error(f"Error sending queued command: {e}", exc_info=True)
                        print(f"⚠️  Error sending command: {e}")
                
                last_command_check = current_time
            
            # Read temperature data from Arduino
            if ser.in_waiting > 0:
                try:
                    # Read line from serial
                    raw_line = ser.readline()
                    
                    # Decode with error handling
                    try:
                        line = raw_line.decode('utf-8').strip()
                    except UnicodeDecodeError as e:
                        logger.warning(f"Failed to decode line as UTF-8: {e}")
                        print(f"⚠️  Failed to decode line (skipping): {raw_line[:50]}")
                        continue
                    
                    if line:
                        # Parse temperature value as float (supports both int and decimal)
                        try:
                            tempC = float(line)
                        except ValueError:
                            logger.warning(f"Invalid temperature value: '{line}'")
                            print(f"⚠️  Invalid temperature value: '{line}' (expected a number)")
                            continue
                        
                        # Validate temperature range from config
                        if tempC < Config.TEMP_MIN_CELSIUS or tempC > Config.TEMP_MAX_CELSIUS:
                            logger.warning(f"Temperature {tempC}°C outside valid range [{Config.TEMP_MIN_CELSIUS}, {Config.TEMP_MAX_CELSIUS}]")
                            print(f"⚠️  Temperature {tempC}°C outside valid range [{Config.TEMP_MIN_CELSIUS}, {Config.TEMP_MAX_CELSIUS}]")
                            continue
                        
                        # Generate timestamp
                        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        
                        # Append to CSV file (Path object works with open() in Python 3.6+)
                        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp, tempC])
                        
                        logger.debug(f"Temperature reading: {tempC}°C at {timestamp}")
                        print(f"[{timestamp}] {tempC}°C")
                        
                except ValueError as e:
                    logger.warning(f"Error parsing line '{line if 'line' in locals() else 'unknown'}': {e}")
                    print(f"⚠️  Error parsing line: {e}")
                except Exception as e:
                    logger.error(f"Error processing data: {e}", exc_info=True)
                    print(f"⚠️  Error processing data: {e}")
            
            time.sleep(Config.SERIAL_READ_DELAY)  # Small delay to prevent CPU spinning
            
    except serial.SerialException as e:
        logger.error(f"Serial port error: {e}", exc_info=True)
        print(f"❌ Serial port error: {e}")
        print(f"\nPlease check:")
        print(f"1. Arduino is connected and powered on")
        print(f"2. Serial port is correct: {serial_port}")
        print(f"3. No other program is using the serial port")
        if platform.system() == 'Linux':
            print(f"4. You have permissions (run: groups | grep dialout)")
        list_available_ports()
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied: {e}", exc_info=True)
        print(f"❌ Permission denied: {e}")
        if platform.system() == 'Linux':
            print("\nOn Raspberry Pi, add your user to the dialout group:")
            print("  sudo usermod -a -G dialout $USER")
            print("Then log out and back in, or restart.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Serial ingest stopped by user")
        print("\n\nStopping serial ingest...")
        if 'ser' in locals():
            ser.close()
            logger.info("Serial port closed")
        print("✅ Disconnected")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

