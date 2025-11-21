/*
 * Temperature Monitor - Arduino Firmware
 * Reads temperature from TMP36 sensor and outputs via Serial
 * Can be controlled via serial commands: START, STOP, TOGGLE
 */

// Pin definitions
const int SENSOR_PIN = A0;
const int LED_PIN = 13;

// Serial communication
const unsigned long SERIAL_BAUD_RATE = 9600;
const unsigned long READING_INTERVAL_MS = 1000;
const unsigned long PAUSE_DELAY_MS = 100;

// Temperature sensor calibration
const float CALIBRATION_OFFSET = -2.0;
const float VOLTAGE_REFERENCE = 5.0;
const int ADC_RESOLUTION = 1024;
const float TMP36_VOLTAGE_OFFSET = 0.5;
const float TMP36_MV_PER_DEGREE = 100.0;

// State variables
bool isPaused = false;
String serialInput = "";

void setup() {
  // Initialize serial communication
  Serial.begin(SERIAL_BAUD_RATE);
  
  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Wait for serial connection (optional, useful for some boards)
  // while (!Serial) { delay(10); }
  
  Serial.println("Temperature Monitor Ready");
  Serial.println("Commands: START, STOP, TOGGLE");
}

void loop() {
  // Process serial commands
  processSerialCommands();
  
  // Handle paused state
  if (isPaused) {
    digitalWrite(LED_PIN, HIGH);
    delay(PAUSE_DELAY_MS);
    return;
  }
  
  // Normal operation: read and output temperature
  digitalWrite(LED_PIN, LOW);
  readAndOutputTemperature();
  delay(READING_INTERVAL_MS);
}

void processSerialCommands() {
  while (Serial.available() > 0) {
    char inChar = Serial.read();
    
    // Check for command terminator
    if (inChar == '\n' || inChar == '\r') {
      handleCommand();
      serialInput = "";
    } else {
      // Accumulate characters
      serialInput += inChar;
    }
  }
}

void handleCommand() {
  // Normalize input
  serialInput.trim();
  serialInput.toUpperCase();
  
  // Process command
  if (serialInput == "START") {
    isPaused = false;
    Serial.println("Status: RUNNING");
  }
  else if (serialInput == "STOP") {
    isPaused = true;
    Serial.println("Status: PAUSED");
  }
  else if (serialInput == "TOGGLE") {
    isPaused = !isPaused;
    Serial.print("Status: ");
    Serial.println(isPaused ? "PAUSED" : "RUNNING");
  }
  else if (serialInput.length() > 0) {
    Serial.print("Unknown command: ");
    Serial.println(serialInput);
    Serial.println("Available: START, STOP, TOGGLE");
  }
}

void readAndOutputTemperature() {
  // Read analog value from sensor
  int sensorValue = analogRead(SENSOR_PIN);
  
  // Convert to voltage (0-5V range)
  float voltage = (sensorValue * VOLTAGE_REFERENCE) / ADC_RESOLUTION;
  
  // Convert voltage to temperature in Celsius
  // TMP36 formula: (voltage - 0.5V) * 100 + calibration
  float temperatureC = ((voltage - TMP36_VOLTAGE_OFFSET) * TMP36_MV_PER_DEGREE) + CALIBRATION_OFFSET;
  
  // Round to integer and output
  int tempC = round(temperatureC);
  Serial.println(tempC);
  
  // Note: A Python script (serial_ingest.py) captures this serial output
  // and writes it to storage/temp_data.csv with proper timestamps
}
