import json
import time
import serial
import serial.tools.list_ports


BAUD_RATE = 115200


def find_ports():
    ports = list(serial.tools.list_ports.comports())

    print("\nAvailable serial ports:")
    if not ports:
        print("  No serial ports found.")
        return []

    for index, port in enumerate(ports):
        print(f"  [{index}] {port.device} - {port.description}")

    return ports


def choose_port():
    ports = find_ports()

    if not ports:
        print("\nESP32 was not found.")
        print("Try a different USB cable. Many cables are charge-only.")
        return None

    if len(ports) == 1:
        print(f"\nUsing only detected port: {ports[0].device}")
        return ports[0].device

    choice = input("\nEnter port number to use: ").strip()

    try:
        index = int(choice)
        return ports[index].device
    except Exception:
        print("Invalid choice.")
        return None


def format_ohms(value):
    if value is None:
        return "null"

    try:
        value = float(value)
    except Exception:
        return str(value)

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} MOhm"
    if value >= 1_000:
        return f"{value / 1_000:.2f} kOhm"

    return f"{value:.1f} Ohm"


def analyze_sensors(sensors):
    ohms_values = []

    for sensor in sensors:
        ohms = sensor.get("ohms")
        if ohms is not None:
            try:
                ohms_values.append(float(ohms))
            except Exception:
                pass

    if len(ohms_values) < 2:
        return

    minimum = min(ohms_values)
    maximum = max(ohms_values)
    difference = maximum - minimum

    print()
    print(f"Range check: min={format_ohms(minimum)} max={format_ohms(maximum)} difference={format_ohms(difference)}")

    if difference < 100:
        print("WARNING: All sensor values are almost the same.")
        print("This usually means the mux channels are floating, connected together, or not switching.")
    elif difference < 500:
        print("Notice: Sensor values are very close.")
        print("This may be okay if the sensors are relaxed, but move one sensor and check if only one changes.")
    else:
        print("Good: Sensors are showing different values.")


def print_packet(packet):
    device = packet.get("device", "unknown")
    seq = packet.get("seq", "?")
    sensors = packet.get("sensors", [])

    print("\n" + "=" * 80)
    print(f"Device: {device}    Packet: {seq}")
    print("-" * 80)
    print(f"{'Sensor':<12} {'Channel':<8} {'Resistance':<14} {'Voltage':<10} {'Raw ADC':<10}")
    print("-" * 80)

    for sensor in sensors:
        name = sensor.get("name", "unknown")
        channel = sensor.get("channel", "-")
        ohms = sensor.get("ohms")
        voltage = sensor.get("voltage")
        raw = sensor.get("raw")

        voltage_text = "---" if voltage is None else f"{float(voltage):.3f} V"
        raw_text = "---" if raw is None else f"{float(raw):.1f}"

        print(f"{name:<12} {channel!s:<8} {format_ohms(ohms):<14} {voltage_text:<10} {raw_text:<10}")

    analyze_sensors(sensors)


def main():
    port = choose_port()

    if port is None:
        return

    print(f"\nOpening {port} at {BAUD_RATE} baud...")
    print("Close Arduino Serial Monitor first if it is open.")
    print("Press the ESP32 EN/RESET button after this starts.")
    print("Press Ctrl+C to stop.\n")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)

        try:
            ser.dtr = False
            ser.rts = False
        except Exception:
            pass

        time.sleep(2)

    except Exception as error:
        print("Could not open serial port:")
        print(error)
        return

    last_packet_time = time.time()

    try:
        while True:
            line = ser.readline()

            if not line:
                if time.time() - last_packet_time > 3:
                    print("(no data yet - press ESP32 EN/RESET button)")
                    last_packet_time = time.time()
                continue

            text = line.decode("utf-8", errors="replace").strip()

            if not text:
                continue

            # Print non-JSON messages too, like "Starting..." or "Connected..."
            if not text.startswith("{"):
                print("ESP32:", text)
                continue

            try:
                packet = json.loads(text)
                last_packet_time = time.time()
                print_packet(packet)
            except json.JSONDecodeError:
                print("Could not parse JSON:")
                print(text)

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()