#include <Adafruit_MAX31865.h>

// Constants
#define RREF      430.0
#define RNOMINAL  100.0
#define TEMP_THRESHOLD_C -160   /// CHANGE TEMPERATURE THRESHOLD AS NEEDED

// Relay pin for solenoid control
/// CHANGE AS NEEDED for more or less relays
/// Relays should range from A15-A8 on PCB in descending order
const int relay_1 = A15;
const int relay_2 = A14;
const int relay_3 = A13;
const int relay_4 = A12;

// SPI pins (SHARED SPI PINS for MAX31865s)
const int clkPin = 33;
const int sdoPin = 35;
const int sdiPin = 37;

// Unique CS pins for each MAX31865
/// CHANGE AS NEEDED for more or less relays
/// Make sure to look at what connects to the PCB
const int cs1 = 47; // Sensor 1
const int cs2 = 39; // Sensor 2
const int cs3 = 41; // Sensor 3
const int cs4 = 43; // Sensor 4

// MAX31865 sensors
/// CHANGE AS NEEDED for more or less
Adafruit_MAX31865 sensor_1 = Adafruit_MAX31865(cs1, sdiPin, sdoPin, clkPin);
Adafruit_MAX31865 sensor_2 = Adafruit_MAX31865(cs2, sdiPin, sdoPin, clkPin);
Adafruit_MAX31865 sensor_3 = Adafruit_MAX31865(cs3, sdiPin, sdoPin, clkPin);
Adafruit_MAX31865 sensor_4 = Adafruit_MAX31865(cs4, sdiPin, sdoPin, clkPin);

// State variables
/// CHANGE number AS NEEDED for more or less
/// CHANGE the number or true and false to match the number in bracket
bool auto_fill[4] = {true, true, true, true};
bool filling[4] = {false, false, false, false};

void setup() {
  Serial.begin(115200);
  Serial.println("Initializing LN2 Filling System...");

  // Initialize sensors
  /// CHANGE AS NEEDED for more or less
  sensor_1.begin(MAX31865_4WIRE);
  sensor_2.begin(MAX31865_4WIRE);
  sensor_3.begin(MAX31865_4WIRE);
  sensor_4.begin(MAX31865_4WIRE);
  delay(500);

  // Set up relay pins   ; HIGH is Solenoid OFF
  /// Change as needed for more or less
  pinMode(relay_1, OUTPUT);
  pinMode(relay_2, OUTPUT);
  pinMode(relay_3, OUTPUT);
  pinMode(relay_4, OUTPUT);
  digitalWrite(relay_1, HIGH); 
  digitalWrite(relay_2, HIGH);
  digitalWrite(relay_3, HIGH);
  digitalWrite(relay_4, HIGH);

  Serial.println("System Ready. Waiting for commands...");
}

void loop() {
  float temperatures[4] = {                 /// CHANGE the number AS NEEDED
    sensor_1.temperature(RNOMINAL, RREF),
    sensor_2.temperature(RNOMINAL, RREF),
    sensor_3.temperature(RNOMINAL, RREF),
    sensor_4.temperature(RNOMINAL, RREF)
  };

  // Print temperatures
  for (int i = 0; i < 4; i++) {     /// Change the number in i<# as needed
    Serial.print("Sensor ");
    Serial.print(i + 1);
    Serial.print(" Temperature = ");
    Serial.print(temperatures[i]);
    Serial.println(" °C");
  }

  // Handle serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    for (int i = 0; i < 4; i++) {                /// CHANGE the number in i<# as needed
      String on_cmd = "ON_" + String(i + 1);
      String off_cmd = "OFF_" + String(i + 1);
      String auto_on_cmd = "AUTO_ON_" + String(i + 1);
      String auto_off_cmd = "AUTO_OFF_" + String(i + 1);

      if (command == on_cmd) {
        filling[i] = true;
        digitalWrite(A15 - i, LOW);  // turn ON
        Serial.println("Manual ON: Sensor " + String(i + 1) + " Filling started");
      }
      else if (command == off_cmd) {
        filling[i] = false;
        digitalWrite(A15 - i, HIGH);  // turn OFF
        Serial.println("Manual OFF: Sensor " + String(i + 1) + " Filling stopped");
      }
      else if (command == auto_on_cmd) {
        auto_fill[i] = true;
        Serial.println("Auto-fill enabled for Dewar " + String(i + 1));
      }
      else if (command == auto_off_cmd) {
        auto_fill[i] = false;
        Serial.println("Auto-fill disabled for Dewar " + String(i + 1));
      }
    }
  }

  // Auto-stop logic
  for (int i = 0; i < 4; i++) {                 /// CHANGE the number in i<# as needed
    if (auto_fill[i] && filling[i] && (temperatures[i] <= TEMP_THRESHOLD_C)) {
      filling[i] = false;
      digitalWrite(A15 - i, HIGH);  // Stop filling
      Serial.println("AUTO_OFF_" + String(i + 1));
      Serial.println("Sensor " + String(i + 1) + ": Temperature threshold reached, stopping filling.");
    }
  }

  delay(1000);
}
