# Legacy Wi-Fi/UDP prototype

This directory is retained as engineering reference only. It does not implement the BLE stream expected by `code/acquisition/tshirt_ble_protocol.py`.

Two alternative ESP32 implementations are present:

- `esp32_arduino/tshirt_esp32_sender.ino`
- `esp32_micropython.py`

Both send JSON packets over UDP to `raspberry_pi/rpi_resistance_display.py`. Archived variants use prototype resistor values that do not represent the verified 3.3 kΩ study configuration. Verify the physical circuit before use.

For the Arduino version, copy `esp32_arduino/secrets.example.h` to `secrets.h`, enter local test-network settings, and never commit that file.
