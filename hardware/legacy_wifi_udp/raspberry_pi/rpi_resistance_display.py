#!/usr/bin/env python3
# Raspberry Pi code
# Receives wireless resistance readings over UDP and displays them on screen.

import json
import socket
import threading
import queue
import time
import tkinter as tk


UDP_PORT = 5005
STALE_AFTER_SECONDS = 2.0


data_queue = queue.Queue()


def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allows reuse after restarting the program.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Listen on all network interfaces.
    sock.bind(("0.0.0.0", UDP_PORT))

    print(f"Listening for UDP packets on port {UDP_PORT}...")

    while True:
        try:
            data, address = sock.recvfrom(4096)
            text = data.decode("utf-8")
            packet = json.loads(text)
            data_queue.put((time.time(), address, packet))
        except Exception as error:
            print("Receive error:", error)


class ResistanceDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("T-Shirt Resistance Monitor")
        self.root.configure(bg="black")

        # Fullscreen for Raspberry Pi display.
        self.root.attributes("-fullscreen", True)

        # Press Escape to exit fullscreen/program.
        self.root.bind("<Escape>", lambda event: self.root.destroy())

        self.last_update_time = 0
        self.sensor_rows = {}

        self.title_label = tk.Label(
            root,
            text="T-Shirt Resistance Monitor",
            font=("Arial", 34, "bold"),
            fg="white",
            bg="black"
        )
        self.title_label.pack(pady=25)

        self.status_label = tk.Label(
            root,
            text="Waiting for wireless data...",
            font=("Arial", 18),
            fg="yellow",
            bg="black"
        )
        self.status_label.pack(pady=10)

        self.info_label = tk.Label(
            root,
            text="",
            font=("Arial", 14),
            fg="white",
            bg="black"
        )
        self.info_label.pack(pady=5)

        self.table_frame = tk.Frame(root, bg="black")
        self.table_frame.pack(pady=30)

        self._create_header()

        self.root.after(50, self.update_display)

    def _create_header(self):
        headers = ["Sensor", "Resistance", "Voltage", "Raw ADC"]

        for col, text in enumerate(headers):
            label = tk.Label(
                self.table_frame,
                text=text,
                font=("Arial", 22, "bold"),
                fg="cyan",
                bg="black",
                padx=30,
                pady=10
            )
            label.grid(row=0, column=col, sticky="w")

    def _create_sensor_row(self, sensor_name):
        row_number = len(self.sensor_rows) + 1

        name_label = tk.Label(
            self.table_frame,
            text=sensor_name,
            font=("Arial", 24),
            fg="white",
            bg="black",
            padx=30,
            pady=10
        )
        resistance_label = tk.Label(
            self.table_frame,
            text="---",
            font=("Arial", 24, "bold"),
            fg="lime",
            bg="black",
            padx=30,
            pady=10
        )
        voltage_label = tk.Label(
            self.table_frame,
            text="---",
            font=("Arial", 24),
            fg="white",
            bg="black",
            padx=30,
            pady=10
        )
        raw_label = tk.Label(
            self.table_frame,
            text="---",
            font=("Arial", 24),
            fg="white",
            bg="black",
            padx=30,
            pady=10
        )

        name_label.grid(row=row_number, column=0, sticky="w")
        resistance_label.grid(row=row_number, column=1, sticky="w")
        voltage_label.grid(row=row_number, column=2, sticky="w")
        raw_label.grid(row=row_number, column=3, sticky="w")

        self.sensor_rows[sensor_name] = {
            "resistance": resistance_label,
            "voltage": voltage_label,
            "raw": raw_label
        }

    def update_display(self):
        received_any = False

        while not data_queue.empty():
            received_any = True
            timestamp, address, packet = data_queue.get()
            self.last_update_time = timestamp

            device = packet.get("device", "unknown")
            seq = packet.get("seq", "?")
            ip_address = address[0]

            self.status_label.config(text="Receiving data", fg="lime")
            self.info_label.config(
                text=f"Device: {device}    From: {ip_address}    Packet: {seq}"
            )

            sensors = packet.get("sensors", [])

            for sensor in sensors:
                name = sensor.get("name", "unknown")

                if name not in self.sensor_rows:
                    self._create_sensor_row(name)

                ohms = sensor.get("ohms")
                voltage = sensor.get("voltage")
                raw = sensor.get("raw")

                if ohms is None:
                    resistance_text = "Open / disconnected"
                elif ohms >= 1_000_000:
                    resistance_text = f"{ohms / 1_000_000:.2f} MΩ"
                elif ohms >= 1_000:
                    resistance_text = f"{ohms / 1_000:.2f} kΩ"
                else:
                    resistance_text = f"{ohms:.1f} Ω"

                voltage_text = "---" if voltage is None else f"{voltage:.3f} V"
                raw_text = "---" if raw is None else str(raw)

                self.sensor_rows[name]["resistance"].config(text=resistance_text)
                self.sensor_rows[name]["voltage"].config(text=voltage_text)
                self.sensor_rows[name]["raw"].config(text=raw_text)

        if not received_any:
            age = time.time() - self.last_update_time

            if self.last_update_time == 0:
                self.status_label.config(text="Waiting for wireless data...", fg="yellow")
            elif age > STALE_AFTER_SECONDS:
                self.status_label.config(text="No recent data", fg="red")

        self.root.after(50, self.update_display)


def main():
    listener_thread = threading.Thread(target=udp_listener, daemon=True)
    listener_thread.start()

    root = tk.Tk()
    app = ResistanceDisplay(root)
    root.mainloop()


if __name__ == "__main__":
    main()