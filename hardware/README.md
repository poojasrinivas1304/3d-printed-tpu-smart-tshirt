# Hardware status

The included `esp32_ble/TSHIRT_01.ino` firmware sends newline-delimited BLE notifications containing:

```text
millis,adc1,adc2,adc3,adc4,adc5,adc6,adc7,adc8,adc9,adc10
```

It advertises as `TSHIRT_01`, samples ten ADC channels at 20 Hz, and uses the Nordic UART Service. Resistance and normalized resistance are calculated by the Python acquisition program using the verified 3.3 kΩ fixed-resistor value.

The `legacy_wifi_udp/` directory contains sanitized prototype code for a different Wi-Fi/UDP path. It uses a CD74HC4067 multiplexer and ten sensor channels but must not be represented as the manuscript acquisition firmware without experimental verification.

PCB and schematic design files are outside the agreed scope of the public repository and will not be included.

The fixed-resistor value used in the reported study was confirmed by the author as **3.3 kΩ**. The divider is arranged as 3.3 V → fixed resistor → ADC node → TPU sensor → ground.
