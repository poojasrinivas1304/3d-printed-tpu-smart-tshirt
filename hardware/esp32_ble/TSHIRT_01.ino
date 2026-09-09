/*
  TSHIRT_01 - ESP32 10-Channel TPU T-Shirt Sensor Readout
  RAW ADC over USB Serial + BLE

  Output format on USB and BLE:
      ms,adc1,adc2,adc3,adc4,adc5,adc6,adc7,adc8,adc9,adc10

  BLE device name:
      TSHIRT_01
*/

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define NUM_SENSORS 10

const char* DEVICE_NAME = "TSHIRT_01";

const uint32_t SAMPLE_PERIOD_MS = 50;  // 20 Hz
const uint8_t AVG_SAMPLES = 8;
const size_t BLE_CHUNK_BYTES = 20;

const int sensorPins[NUM_SENSORS] = {
  36, 39, 34, 35, 32, 33, 25, 26, 27, 14
};

// Nordic UART Service UUIDs
static const char* NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";
static const char* NUS_RX_UUID      = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E";
static const char* NUS_TX_UUID      = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";

BLECharacteristic* txCharacteristic = nullptr;
bool bleConnected = false;
uint32_t lastSampleMs = 0;

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    bleConnected = true;
    Serial.println("BLE connected");
  }

  void onDisconnect(BLEServer* pServer) override {
    bleConnected = false;
    Serial.println("BLE disconnected, advertising again");
    delay(200);
    BLEDevice::startAdvertising();
  }
};

int readAveragedADC(int pin) {
  uint32_t sum = 0;
  for (uint8_t i = 0; i < AVG_SAMPLES; i++) {
    sum += analogRead(pin);
    delayMicroseconds(250);
  }
  return (int)((sum + (AVG_SAMPLES / 2)) / AVG_SAMPLES);
}

void printHeader() {
  Serial.print("ms");
  for (int i = 1; i <= NUM_SENSORS; i++) {
    Serial.print(",adc");
    Serial.print(i);
  }
  Serial.println();
}

String buildCSVLine(uint32_t nowMs) {
  String line;
  line.reserve(100);
  line += String(nowMs);

  for (int i = 0; i < NUM_SENSORS; i++) {
    int adc = readAveragedADC(sensorPins[i]);
    line += ",";
    line += String(adc);
  }

  line += "\n";
  return line;
}

void sendBLELine(const String& line) {
  if (!bleConnected || txCharacteristic == nullptr) return;

  for (size_t i = 0; i < line.length(); i += BLE_CHUNK_BYTES) {
    size_t endIndex = i + BLE_CHUNK_BYTES;
    if (endIndex > line.length()) endIndex = line.length();

    String chunk = line.substring(i, endIndex);
    txCharacteristic->setValue((uint8_t*)chunk.c_str(), chunk.length());
    txCharacteristic->notify();
    delay(2);
  }
}

void startBLE() {
  BLEDevice::init(DEVICE_NAME);
  BLEDevice::setMTU(185);

  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService* service = server->createService(NUS_SERVICE_UUID);

  txCharacteristic = service->createCharacteristic(
    NUS_TX_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  txCharacteristic->addDescriptor(new BLE2902());

  BLECharacteristic* rxCharacteristic = service->createCharacteristic(
    NUS_RX_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );

  service->start();

  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(NUS_SERVICE_UUID);
  advertising->setScanResponse(true);
  BLEDevice::startAdvertising();

  Serial.print("BLE advertising as: ");
  Serial.println(DEVICE_NAME);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  analogReadResolution(12);
  analogSetWidth(12);

  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(sensorPins[i], INPUT);
    analogSetPinAttenuation(sensorPins[i], ADC_11db);
  }

  startBLE();
  printHeader();
  lastSampleMs = millis();
}

void loop() {
  uint32_t nowMs = millis();

  if (nowMs - lastSampleMs >= SAMPLE_PERIOD_MS) {
    lastSampleMs = nowMs;

    String line = buildCSVLine(nowMs);
    Serial.print(line);
    sendBLELine(line);
  }
}
