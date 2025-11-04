"""Serial ingest script to capture Arduino serial data and write to CSV."""
import serial
import serial.tools.list_ports
import csv
from datetime import datetime, timezone
import time
import sys
import platform
import os

# Import configuration
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import get_config, get_default_serial_ports

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
            print(f"Found Arduino-like device at: {port.device}")
            return port.device
    
    # Fallback: try common port names
    for port_name in DEFAULT_PORTS:
        try:
            # Try to open the port to verify it exists
            test_ser = serial.Serial(port_name, BAUD_RATE, timeout=0.5)
            test_ser.close()
            print(f"Found serial port: {port_name}")
            return port_name
        except (serial.SerialException, OSError):
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
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['recordedAt', 'tempC'])

def check_permissions(port_path):
    """Check if user has permissions to access the serial port."""
    if platform.system() == 'Linux':
        if not os.access(port_path, os.R_OK | os.W_OK):
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
    
    print(f"Connecting to serial port {serial_port} at {BAUD_RATE} baud...")
    
    try:
        ser = serial.Serial(serial_port, BAUD_RATE, timeout=Config.SERIAL_TIMEOUT)
        print(f"✅ Connected! Reading data and writing to {CSV_FILE}")
        print("Press Ctrl+C to stop\n")
        
        ensure_csv_header(CSV_FILE)
        
        while True:
            if ser.in_waiting > 0:
                try:
                    # Read line from serial
                    line = ser.readline().decode('utf-8').strip()
                    
                    if line:
                        # Parse temperature value as integer (Arduino outputs int)
                        tempC = int(line)
                        
                        # Validate temperature range from config
                        if tempC < Config.TEMP_MIN_CELSIUS or tempC > Config.TEMP_MAX_CELSIUS:
                            print(f"⚠️  Temperature {tempC}°C outside valid range [{Config.TEMP_MIN_CELSIUS}, {Config.TEMP_MAX_CELSIUS}]")
                            continue
                        
                        # Generate timestamp
                        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        
                        # Append to CSV file
                        with open(CSV_FILE, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([timestamp, tempC])
                        
                        print(f"[{timestamp}] {tempC}°C")
                        
                except ValueError as e:
                    print(f"⚠️  Error parsing line '{line}': {e}")
                except Exception as e:
                    print(f"⚠️  Error processing data: {e}")
            
            time.sleep(Config.SERIAL_READ_DELAY)  # Small delay to prevent CPU spinning
            
    except serial.SerialException as e:
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
        print(f"❌ Permission denied: {e}")
        if platform.system() == 'Linux':
            print("\nOn Raspberry Pi, add your user to the dialout group:")
            print("  sudo usermod -a -G dialout $USER")
            print("Then log out and back in, or restart.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nStopping serial ingest...")
        if 'ser' in locals():
            ser.close()
        print("✅ Disconnected")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

