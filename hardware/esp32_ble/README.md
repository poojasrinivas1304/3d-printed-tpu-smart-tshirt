# ESP32 BLE firmware

`TSHIRT_01.ino` is the ten-channel raw-ADC firmware paired with the repository's Python acquisition program.

## Data path

- BLE device name: `TSHIRT_01`
- Service: Nordic UART Service
- Notification rate: 20 Hz
- Payload: `ms,adc1,adc2,adc3,adc4,adc5,adc6,adc7,adc8,adc9,adc10`
- Sensor pins: GPIO 36, 39, 34, 35, 32, 33, 25, 26, 27, and 14

The firmware transmits raw ADC values and therefore does not contain a resistor constant. The downstream acquisition and postprocessing code uses the verified **3.3 kΩ** study value and the divider topology 3.3 V → fixed resistor → ADC node → TPU sensor → ground.

The Arduino sketch requires the ESP32 Arduino core and its BLE libraries (`BLEDevice`, `BLEServer`, `BLEUtils`, and `BLE2902`).
