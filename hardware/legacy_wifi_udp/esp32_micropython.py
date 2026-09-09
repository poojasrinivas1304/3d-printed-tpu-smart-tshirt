# main.py
# ESP32 MicroPython code
# Reads 10 resistance sensors through a CD74HC4067 multiplexer
# and sends the values wirelessly to a Raspberry Pi using UDP.

import network  # type: ignore
import socket
import time
import json
from machine import Pin, ADC  # type: ignore


# ----------------------------
# Wi-Fi settings
# ----------------------------
SSID = "YOUR_WIFI_NAME"
PASSWORD = "YOUR_WIFI_PASSWORD"

# Broadcast address. This should work if the Raspberry Pi is on the same Wi-Fi.
# If it does not work, replace with your Raspberry Pi IP address,
# for example: "192.168.1.50"
PI_IP = "255.255.255.255"
UDP_PORT = 5005


# ----------------------------
# Circuit settings
# ----------------------------
VCC = 3.3

# CD74HC4067 common signal pin connected to ESP32 ADC pin.
ADC_PIN = 34

# CD74HC4067 select pins.
# These connect to S0, S1, S2, S3.
MUX_SELECT_PINS = [16, 17, 18, 19]

# Your wiring:
#
# 3.3V -> shirt sensor -> measurement node -> 10k fixed resistor -> GND
# measurement node -> CD74HC4067 channel C0-C9
#
# Formula:
# R_sensor = R_fixed * (VCC / Vout - 1)

SENSORS = [
    {"name": "sensor_1",  "channel": 0, "r_fixed": 10000.0},
    {"name": "sensor_2",  "channel": 1, "r_fixed": 10000.0},
    {"name": "sensor_3",  "channel": 2, "r_fixed": 10000.0},
    {"name": "sensor_4",  "channel": 3, "r_fixed": 10000.0},
    {"name": "sensor_5",  "channel": 4, "r_fixed": 10000.0},
    {"name": "sensor_6",  "channel": 5, "r_fixed": 10000.0},
    {"name": "sensor_7",  "channel": 6, "r_fixed": 10000.0},
    {"name": "sensor_8",  "channel": 7, "r_fixed": 10000.0},
    {"name": "sensor_9",  "channel": 8, "r_fixed": 10000.0},
    {"name": "sensor_10", "channel": 9, "r_fixed": 10000.0},
]

SEND_DELAY_SECONDS = 0.10


# ----------------------------
# Wi-Fi setup
# ----------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(SSID, PASSWORD)

        for _ in range(60):
            if wlan.isconnected():
                break
            time.sleep(0.5)

    if not wlan.isconnected():
        raise RuntimeError("Wi-Fi connection failed. Check SSID and password.")

    print("Connected to Wi-Fi.")
    print("ESP32 network config:", wlan.ifconfig())

    return wlan


# ----------------------------
# Multiplexer setup
# ----------------------------
mux_pins = []


def setup_mux():
    global mux_pins

    mux_pins = []
    for pin_number in MUX_SELECT_PINS:
        pin = Pin(pin_number, Pin.OUT)
        pin.value(0)
        mux_pins.append(pin)


def select_mux_channel(channel):
    # CD74HC4067 uses binary selection:
    # channel 0  = 0000
    # channel 1  = 0001
    # channel 2  = 0010
    # ...
    # channel 9  = 1001

    for bit_index, pin in enumerate(mux_pins):
        bit_value = (channel >> bit_index) & 1
        pin.value(bit_value)

    # Let the analog voltage settle after switching channels.
    time.sleep_ms(3)


# ----------------------------
# ADC setup
# ----------------------------
def setup_adc():
    adc = ADC(Pin(ADC_PIN))

    # Allows wider voltage range on ESP32 ADC.
    try:
        adc.atten(ADC.ATTN_11DB)
    except Exception:
        pass

    try:
        adc.width(ADC.WIDTH_12BIT)
    except Exception:
        pass

    return adc


def read_average(adc, channel, samples=10):
    select_mux_channel(channel)

    # Throw away first reading after switching mux channel.
    adc.read_u16()
    time.sleep_ms(2)

    total = 0

    for _ in range(samples):
        total += adc.read_u16()
        time.sleep_ms(1)

    return total / samples


def raw_to_resistance(raw, r_fixed):
    # MicroPython ADC.read_u16() returns 0 to 65535.
    # Convert that to voltage.
    voltage = (raw / 65535.0) * VCC

    # If voltage is almost zero, the sensor may be open/disconnected.
    if voltage <= 0.005:
        return None, voltage

    resistance = r_fixed * ((VCC / voltage) - 1.0)

    if resistance < 0:
        resistance = 0.0

    return resistance, voltage


# ----------------------------
# Main loop
# ----------------------------
def main():
    connect_wifi()
    setup_mux()
    adc = setup_adc()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception:
        pass

    seq = 0

    while True:
        packet = {
            "device": "tshirt_esp32",
            "seq": seq,
            "sensors": []
        }

        for sensor in SENSORS:
            raw = read_average(adc, sensor["channel"])
            resistance, voltage = raw_to_resistance(raw, sensor["r_fixed"])

            packet["sensors"].append({
                "name": sensor["name"],
                "channel": sensor["channel"],
                "raw": round(raw, 1),
                "voltage": round(voltage, 3),
                "ohms": None if resistance is None else round(resistance, 1)
            })

        message = json.dumps(packet)
        sock.sendto(message.encode("utf-8"), (PI_IP, UDP_PORT))

        print(message)

        seq += 1
        time.sleep(SEND_DELAY_SECONDS)


main()