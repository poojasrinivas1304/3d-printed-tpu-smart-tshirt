#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"

// ----------------------------
// Wi-Fi settings
// ----------------------------
const char* SSID = WIFI_SSID;
const char* PASSWORD = WIFI_PASSWORD;

// Broadcast address.
// This works when the ESP32 and Raspberry Pi are on the same Wi-Fi.
// If it does not work, replace with the Raspberry Pi IP address.
IPAddress PI_IP(RPI_IP_OCTET_1, RPI_IP_OCTET_2, RPI_IP_OCTET_3, RPI_IP_OCTET_4);

const int UDP_PORT = 5005;

WiFiUDP udp;


// ----------------------------
// Circuit settings
// ----------------------------
const float VCC = 3.3;

// CD74HC4067 SIG / COM pin connected to ESP32 analog pin.
const int ADC_PIN = 34;

// CD74HC4067 select pins.
// ESP32 GPIO16 -> S0
// ESP32 GPIO17 -> S1
// ESP32 GPIO18 -> S2
// ESP32 GPIO19 -> S3
const int MUX_SELECT_PINS[4] = {16, 17, 18, 19};

const int SAMPLES = 10;
const int SEND_DELAY_MS = 100;


// ----------------------------
// Sensor list
// ----------------------------
struct Sensor {
  const char* name;
  int channel;
  float rFixed;
};

Sensor sensors[] = {
  {"sensor_1",  0, 10000.0},
  {"sensor_2",  1, 10000.0},
  {"sensor_3",  2, 10000.0},
  {"sensor_4",  3, 10000.0},
  {"sensor_5",  4, 10000.0},
  {"sensor_6",  5, 10000.0},
  {"sensor_7",  6, 10000.0},
  {"sensor_8",  7, 10000.0},
  {"sensor_9",  8, 10000.0},
  {"sensor_10", 9, 10000.0}
};

const int SENSOR_COUNT = sizeof(sensors) / sizeof(sensors[0]);

unsigned long seq = 0;


// ----------------------------
// Select multiplexer channel
// ----------------------------
void selectMuxChannel(int channel) {
  for (int bitIndex = 0; bitIndex < 4; bitIndex++) {
    int bitValue = (channel >> bitIndex) & 1;
    digitalWrite(MUX_SELECT_PINS[bitIndex], bitValue);
  }

  delay(3);
}


// ----------------------------
// Read sensor
// ----------------------------
void readSensor(int channel, float &rawAverage, float &voltage) {
  selectMuxChannel(channel);

  // Throw away first reading after switching mux channel.
  analogRead(ADC_PIN);
  analogReadMilliVolts(ADC_PIN);
  delay(2);

  long rawTotal = 0;
  long millivoltTotal = 0;

  for (int i = 0; i < SAMPLES; i++) {
    rawTotal += analogRead(ADC_PIN);
    millivoltTotal += analogReadMilliVolts(ADC_PIN);
    delay(1);
  }

  rawAverage = rawTotal / float(SAMPLES);
  float millivoltAverage = millivoltTotal / float(SAMPLES);

  voltage = millivoltAverage / 1000.0;
}


// ----------------------------
// Convert voltage to resistance
// ----------------------------
// Wiring:
// 3.3V -> shirt sensor -> ADC/mux node -> 10k fixed resistor -> GND
//
// Formula:
// R_sensor = R_fixed * (VCC / Vout - 1)
float voltageToResistance(float voltage, float rFixed) {
  if (voltage <= 0.005) {
    return -1.0;  // disconnected/open
  }

  float resistance = rFixed * ((VCC / voltage) - 1.0);

  if (resistance < 0) {
    resistance = 0;
  }

  return resistance;
}


// ----------------------------
// Build JSON message
// ----------------------------
String buildJsonMessage() {
  String json = "{";
  json += "\"device\":\"tshirt_esp32_arduino\",";
  json += "\"seq\":";
  json += String(seq);
  json += ",";
  json += "\"sensors\":[";

  for (int i = 0; i < SENSOR_COUNT; i++) {
    float raw = 0;
    float voltage = 0;

    readSensor(sensors[i].channel, raw, voltage);

    float resistance = voltageToResistance(voltage, sensors[i].rFixed);

    if (i > 0) {
      json += ",";
    }

    json += "{";
    json += "\"name\":\"";
    json += sensors[i].name;
    json += "\",";
    json += "\"channel\":";
    json += String(sensors[i].channel);
    json += ",";
    json += "\"raw\":";
    json += String(raw, 1);
    json += ",";
    json += "\"voltage\":";
    json += String(voltage, 3);
    json += ",";
    json += "\"ohms\":";

    if (resistance < 0) {
      json += "null";
    } else {
      json += String(resistance, 1);
    }

    json += "}";
  }

  json += "]}";

  return json;
}


// ----------------------------
// Setup
// ----------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Starting T-shirt ESP32 sender...");

  for (int i = 0; i < 4; i++) {
    pinMode(MUX_SELECT_PINS[i], OUTPUT);
    digitalWrite(MUX_SELECT_PINS[i], LOW);
  }

  analogReadResolution(12);

  analogSetPinAttenuation(ADC_PIN, ADC_11db);

  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Connected to Wi-Fi.");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());

  udp.begin(UDP_PORT);

  Serial.println("UDP sender ready.");
}


// ----------------------------
// Main loop
// ----------------------------
void loop() {
  String message = buildJsonMessage();

  udp.beginPacket(PI_IP, UDP_PORT);
  udp.print(message);
  udp.endPacket();

  Serial.println(message);

  seq++;

  delay(SEND_DELAY_MS);
}
