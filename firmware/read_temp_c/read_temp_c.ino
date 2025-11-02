int sensorPin = A0;   // select the input pin for the temperature sensor

float sensorValue = 0;  // variable to store the sensor reading
float temperatureC = 0;  // variable to store temperature in Celsius

int tempC; // temperatue C in int
int CALIBRATION = -2;

int ledPin = 13; // onboard LED pin

int counter = 0;


void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);

  // initialize the LED pin as an OUTPUT:
  pinMode(ledPin, OUTPUT);
}

void loop() {


  // read the value from the sensor:
  sensorValue = analogRead(sensorPin);

  // use 5V witharef pin
  float voltage = sensorValue * 5 / 1024.0;
  
  // convert voltage to temperature in Celsius (for TMP36: 10mV per degree C)
  temperatureC = (voltage - 0.5) * 100 + CALIBRATION;
  tempC = round(temperatureC);

  // Output CSV format for serial capture: tempC
  // Note: Arduino cannot write directly to computer filesystem
  // A Python script (serial_ingest.py) will capture this serial output
  // and write it to storage/temp_data.csv with proper timestamps
  Serial.println(tempC);
  
  // wait 1 second :
  delay(1000);

  counter++;

  if (counter > 4) {
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
    counter = 0;
  }
}