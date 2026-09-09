#!/usr/bin/env python3
"""
tshirt_ble_protocol.py

BLE acquisition and protocol runner for a 10-sensor smart T-shirt.

Expected BLE notification format:
    millis,adc1,adc2,adc3,adc4,adc5,adc6,adc7,adc8,adc9,adc10\n

Also accepted:
    adc1,adc2,adc3,adc4,adc5,adc6,adc7,adc8,adc9,adc10\n

Main functions:
    1. Scan BLE devices
    2. Inspect BLE services/characteristics
    3. Run the full T-shirt posture protocol
    4. Convert ADC to resistance
    5. Compute normalized resistance change: Delta R / R0
    6. Save raw and processed CSV files
    7. Generate a Figure-6-style plot
"""

import argparse
import asyncio
import csv
import json
import math
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from bleak import BleakClient, BleakScanner


# Nordic UART Service TX characteristic.
# Many ESP32 BLE UART examples use this notify characteristic.
DEFAULT_NOTIFY_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


POSITION_NAMES = {
    1: "standing_straight",
    2: "raise_left_arm",
    3: "raise_right_arm",
    4: "cross_arms",
    5: "touch_left_shoulder",
    6: "raise_both_arms",
    7: "bend_forward",
    8: "sit",
}


@dataclass
class RecordingState:
    subject_id: str
    run_id: str
    start_time_pc: float = field(default_factory=time.time)
    sample_count: int = 0
    bad_line_count: int = 0
    running: bool = True

    current_set: int = 0
    current_rep: int = 0
    current_phase: str = "idle"
    current_position_index: int = 0
    current_position_name: str = "idle"


def parse_resistor_list(text: str, n_sensors: int) -> List[float]:
    """
    Accept either a single value:
        "3300"
    or one value per channel:
        "3300,3300,3300,..."
    """
    parts = [p.strip() for p in text.split(",") if p.strip()]
    values = [float(p) for p in parts]

    if len(values) == 1:
        return values * n_sensors

    if len(values) != n_sensors:
        raise ValueError(
            f"Expected either 1 fixed resistor value or {n_sensors} values, "
            f"but got {len(values)}."
        )

    return values


def parse_ble_line(line: bytes, n_sensors: int) -> Tuple[Optional[float], List[int]]:
    """
    Parse one BLE CSV text line.

    Accepted examples:
        b"123456,1000,1001,...,1010"
        b"1000,1001,...,1010"

    Returns:
        device_time: float or None
        adcs: list of ADC integers, length n_sensors
    """
    text = line.decode("utf-8", errors="ignore").strip()

    if not text:
        raise ValueError("Empty BLE line.")

    # Extract numeric tokens from CSV, semicolon, tab, or space separated strings.
    tokens = [t for t in re.split(r"[,;\t ]+", text) if t.strip()]
    nums = []

    for token in tokens:
        try:
            nums.append(float(token))
        except ValueError:
            # Ignore non-numeric tokens such as "ADC:" if present.
            continue

    if len(nums) == n_sensors:
        device_time = None
        adc_values = nums
    elif len(nums) >= n_sensors + 1:
        device_time = nums[0]
        adc_values = nums[-n_sensors:]
    else:
        raise ValueError(
            f"Could not parse {n_sensors} ADC values from line: {text}"
        )

    adcs = [int(round(v)) for v in adc_values]
    return device_time, adcs


async def scan_devices(timeout_s: float) -> None:
    print(f"Scanning for BLE devices for {timeout_s:.1f} s...\n")
    devices = await BleakScanner.discover(timeout=timeout_s)

    if not devices:
        print("No BLE devices found.")
        return

    for i, device in enumerate(devices):
        name = device.name or "Unknown"
        rssi = getattr(device, "rssi", "?")
        print(f"{i:02d} | name={name} | address={device.address} | rssi={rssi}")


async def resolve_device_address(
    address: Optional[str],
    name: Optional[str],
    timeout_s: float,
) -> str:
    if address:
        return address

    if not name:
        raise ValueError("Provide either --address or --name.")

    print(f"Searching for BLE device containing name: {name!r}")
    devices = await BleakScanner.discover(timeout=timeout_s)

    for device in devices:
        if device.name and name.lower() in device.name.lower():
            print(f"Found device: {device.name} [{device.address}]")
            return device.address

    raise RuntimeError(f"No BLE device found with name containing {name!r}.")


async def inspect_device(address: Optional[str], name: Optional[str], timeout_s: float) -> None:
    device_address = await resolve_device_address(address, name, timeout_s)

    print(f"Connecting to {device_address}...")
    async with BleakClient(device_address) as client:
        print(f"Connected: {client.is_connected}\n")
        print("Services and characteristics:\n")

        for service in client.services:
            print(f"[Service] {service.uuid} | {service.description}")
            for char in service.characteristics:
                props = ",".join(char.properties)
                print(f"    [Char] {char.uuid} | properties={props}")
            print()


async def choose_notify_characteristic(client: BleakClient, requested_uuid: str) -> str:
    if requested_uuid.lower() != "auto":
        return requested_uuid

    for service in client.services:
        for char in service.characteristics:
            if "notify" in char.properties or "indicate" in char.properties:
                print(f"Auto-selected notify characteristic: {char.uuid}")
                return char.uuid

    raise RuntimeError("No notify/indicate characteristic found. Use inspect mode first.")


async def countdown(seconds: float) -> None:
    if seconds <= 0:
        return

    end_time = time.monotonic() + seconds
    last_remaining = None

    while time.monotonic() < end_time:
        remaining = int(math.ceil(end_time - time.monotonic()))
        if remaining != last_remaining:
            print(f"\r    {remaining:3d} s remaining", end="", flush=True)
            last_remaining = remaining
        await asyncio.sleep(0.1)

    print("\r    done          ")


async def set_segment(
    state: RecordingState,
    position_index: int,
    phase: str,
    duration_s: float,
    set_id: int,
    rep: int,
    instruction: str,
) -> None:
    state.current_position_index = position_index
    state.current_position_name = POSITION_NAMES.get(position_index, "unknown")
    state.current_phase = phase
    state.current_set = set_id
    state.current_rep = rep

    print("\n" + "=" * 72)
    print(instruction)
    print(f"Label: position={position_index} ({state.current_position_name}), phase={phase}")
    print("=" * 72)

    await countdown(duration_s)


async def consume_notifications(
    queue: asyncio.Queue,
    state: RecordingState,
    writer: csv.DictWriter,
    raw_file,
    n_sensors: int,
    sample_rate_hz: float,
    high_adc_threshold: int,
    low_adc_threshold: int,
) -> None:
    """
    Consume BLE notification chunks, parse newline-terminated CSV samples,
    and write raw ADC data to CSV.

    Important:
        Your firmware should include a newline after each sample.
    """
    buffer = b""
    flush_every = max(1, int(sample_rate_hz))
    status_every = max(1, int(sample_rate_hz * 5))

    while state.running or not queue.empty():
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=0.2)
        except asyncio.TimeoutError:
            continue

        buffer += bytes(chunk)

        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)

            try:
                device_time, adcs = parse_ble_line(line, n_sensors)
            except Exception as exc:
                state.bad_line_count += 1
                if state.bad_line_count <= 5 or state.bad_line_count % 50 == 0:
                    print(f"\n[parse warning] {exc}")
                continue

            now = time.time()
            elapsed = now - state.start_time_pc

            high_adc_any = any(v >= high_adc_threshold for v in adcs)
            low_adc_any = any(v <= low_adc_threshold for v in adcs)

            state.sample_count += 1

            row = {
                "subject_id": state.subject_id,
                "run_id": state.run_id,
                "sample_index": state.sample_count,
                "pc_time_unix_s": now,
                "elapsed_s_pc": elapsed,
                "device_time": device_time if device_time is not None else "",
                "set_id": state.current_set,
                "rep": state.current_rep,
                "phase": state.current_phase,
                "position_index": state.current_position_index,
                "position_name": state.current_position_name,
                "high_adc_any": int(high_adc_any),
                "low_adc_any": int(low_adc_any),
            }

            for i, adc in enumerate(adcs, start=1):
                row[f"adc_s{i}"] = adc

            writer.writerow(row)

            if state.sample_count % flush_every == 0:
                raw_file.flush()

            if state.sample_count % status_every == 0:
                print(
                    f"\rSamples: {state.sample_count} | "
                    f"phase={state.current_phase} | "
                    f"position={state.current_position_index} | "
                    f"bad_lines={state.bad_line_count} | "
                    f"high_adc={int(high_adc_any)}",
                    end="",
                    flush=True,
                )


def adc_to_resistance(
    adc_values: pd.Series,
    fixed_resistor_ohm: float,
    adc_max: int,
    divider_mode: str,
) -> pd.Series:
    """
    Convert ADC to sensor resistance.

    Mode 1:
        fixed_to_vcc_sensor_to_gnd

        3.3 V -> R_fixed -> ADC node -> R_sensor -> GND

        Rs = Rf * ADC / (ADCmax - ADC)

    Mode 2:
        sensor_to_vcc_fixed_to_gnd

        3.3 V -> R_sensor -> ADC node -> R_fixed -> GND

        Rs = Rf * (ADCmax - ADC) / ADC
    """
    adc = adc_values.astype(float).clip(lower=1, upper=adc_max - 1)

    if divider_mode == "fixed_to_vcc_sensor_to_gnd":
        return fixed_resistor_ohm * adc / (adc_max - adc)

    if divider_mode == "sensor_to_vcc_fixed_to_gnd":
        return fixed_resistor_ohm * (adc_max - adc) / adc

    raise ValueError(f"Unknown divider_mode: {divider_mode}")


def postprocess_csv(
    raw_csv_path: Path,
    n_sensors: int,
    fixed_resistors_ohm: List[float],
    adc_max: int,
    divider_mode: str,
    high_adc_threshold: int,
    low_adc_threshold: int,
    initial_baseline_s: float,
) -> Path:
    print(f"\n\nPost-processing raw CSV:\n{raw_csv_path}")

    df = pd.read_csv(raw_csv_path)

    if df.empty:
        raise RuntimeError("Raw CSV is empty. No samples were recorded.")

    for i in range(1, n_sensors + 1):
        adc_col = f"adc_s{i}"
        if adc_col not in df.columns:
            raise RuntimeError(f"Missing column: {adc_col}")

        r_col = f"r_s{i}_ohm"
        dr_col = f"dr_s{i}"

        df[f"qc_high_adc_s{i}"] = (df[adc_col] >= high_adc_threshold).astype(int)
        df[f"qc_low_adc_s{i}"] = (df[adc_col] <= low_adc_threshold).astype(int)

        df[r_col] = adc_to_resistance(
            df[adc_col],
            fixed_resistors_ohm[i - 1],
            adc_max,
            divider_mode,
        )

    # Baseline: use the initial baseline segment if present.
    baseline_mask = df["phase"].astype(str).eq("initial_baseline")

    # Fallback: use the first initial_baseline_s seconds of the recording.
    if baseline_mask.sum() < 5:
        t0 = float(df["elapsed_s_pc"].min())
        baseline_mask = df["elapsed_s_pc"] <= (t0 + initial_baseline_s)

    r0_values = {}
    for i in range(1, n_sensors + 1):
        r_col = f"r_s{i}_ohm"
        dr_col = f"dr_s{i}"

        r0 = float(np.nanmedian(df.loc[baseline_mask, r_col]))
        r0_values[f"s{i}"] = r0

        if not np.isfinite(r0) or abs(r0) < 1e-12:
            df[dr_col] = np.nan
        else:
            df[dr_col] = (df[r_col] - r0) / r0

    df["qc_high_adc_any_post"] = df[[f"qc_high_adc_s{i}" for i in range(1, n_sensors + 1)]].any(axis=1).astype(int)
    df["qc_low_adc_any_post"] = df[[f"qc_low_adc_s{i}" for i in range(1, n_sensors + 1)]].any(axis=1).astype(int)

    stem = raw_csv_path.stem
    if stem.endswith("_raw"):
        processed_stem = stem[:-4] + "_processed"
    else:
        processed_stem = stem + "_processed"

    processed_path = raw_csv_path.with_name(processed_stem + ".csv")
    qc_path = raw_csv_path.with_name(processed_stem + "_r0_qc.json")

    df.to_csv(processed_path, index=False)

    qc_summary = {
        "raw_csv": str(raw_csv_path),
        "processed_csv": str(processed_path),
        "n_samples": int(len(df)),
        "n_sensors": int(n_sensors),
        "adc_max": int(adc_max),
        "divider_mode": divider_mode,
        "fixed_resistors_ohm": fixed_resistors_ohm,
        "r0_ohm": r0_values,
        "high_adc_counts": {
            f"s{i}": int(df[f"qc_high_adc_s{i}"].sum())
            for i in range(1, n_sensors + 1)
        },
        "low_adc_counts": {
            f"s{i}": int(df[f"qc_low_adc_s{i}"].sum())
            for i in range(1, n_sensors + 1)
        },
        "baseline_rows_used": int(baseline_mask.sum()),
    }

    with open(qc_path, "w", encoding="utf-8") as f:
        json.dump(qc_summary, f, indent=2)

    print(f"Processed CSV saved:\n{processed_path}")
    print(f"R0/QC JSON saved:\n{qc_path}")

    print("\nR0 values:")
    for k, v in r0_values.items():
        print(f"  {k}: {v:.3f} ohm")

    print("\nHigh-ADC event counts:")
    for i in range(1, n_sensors + 1):
        print(f"  S{i}: {int(df[f'qc_high_adc_s{i}'].sum())}")

    return processed_path


def plot_processed_csv(processed_csv_path: Path, n_sensors: Optional[int] = None) -> Path:
    df = pd.read_csv(processed_csv_path)

    if "elapsed_s_pc" not in df.columns:
        raise RuntimeError("Processed CSV must contain elapsed_s_pc.")

    if "position_index" not in df.columns:
        raise RuntimeError("Processed CSV must contain position_index.")

    if n_sensors is None:
        n_sensors = 0
        for col in df.columns:
            if re.fullmatch(r"dr_s\d+", col):
                n_sensors += 1

    if n_sensors <= 0:
        raise RuntimeError("Could not detect dr_s1...dr_sN columns.")

    t = df["elapsed_s_pc"].to_numpy()

    fig_height = max(10, 1.45 * (n_sensors + 1))
    fig, axes = plt.subplots(
        n_sensors + 1,
        1,
        figsize=(13, fig_height),
        sharex=True,
    )

    axes[0].step(t, df["position_index"], where="post", linewidth=1.0)
    axes[0].set_ylabel("Position")
    axes[0].set_title("Normalized sensor responses (Delta R / R0)")

    for i in range(1, n_sensors + 1):
        ax = axes[i]
        col = f"dr_s{i}"
        if col not in df.columns:
            raise RuntimeError(f"Missing column: {col}")

        ax.plot(t, df[col], linewidth=0.8)
        ax.set_ylabel(f"S{i}\nDR/R0")
        ax.grid(True, linewidth=0.3)

    axes[-1].set_xlabel("Time (s)")

    fig.tight_layout()

    out_path = processed_csv_path.with_name(processed_csv_path.stem + "_figure6_like.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)

    print(f"Figure saved:\n{out_path}")
    return out_path


async def run_collection(args) -> None:
    n_sensors = args.n_sensors
    fixed_resistors = parse_resistor_list(args.fixed_resistors, n_sensors)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or time.strftime("%Y%m%d_%H%M%S")
    raw_csv_path = out_dir / f"{args.subject}_{run_id}_raw.csv"

    fieldnames = [
        "subject_id",
        "run_id",
        "sample_index",
        "pc_time_unix_s",
        "elapsed_s_pc",
        "device_time",
        "set_id",
        "rep",
        "phase",
        "position_index",
        "position_name",
        "high_adc_any",
        "low_adc_any",
    ] + [f"adc_s{i}" for i in range(1, n_sensors + 1)]

    device_address = await resolve_device_address(args.address, args.name, args.scan_timeout)

    state = RecordingState(subject_id=args.subject, run_id=run_id)
    queue: asyncio.Queue = asyncio.Queue()

    def notification_handler(sender, data):
        queue.put_nowait(bytes(data))

    print(f"\nConnecting to BLE device: {device_address}")
    print(f"Raw output CSV:\n{raw_csv_path}")

    with open(raw_csv_path, "w", newline="", encoding="utf-8") as raw_file:
        writer = csv.DictWriter(raw_file, fieldnames=fieldnames)
        writer.writeheader()

        async with BleakClient(device_address) as client:
            if not client.is_connected:
                raise RuntimeError("BLE connection failed.")

            notify_uuid = await choose_notify_characteristic(client, args.char_uuid)

            print(f"Connected. Starting notifications on characteristic:\n{notify_uuid}")
            await client.start_notify(notify_uuid, notification_handler)

            consumer_task = asyncio.create_task(
                consume_notifications(
                    queue=queue,
                    state=state,
                    writer=writer,
                    raw_file=raw_file,
                    n_sensors=n_sensors,
                    sample_rate_hz=args.sample_rate_hz,
                    high_adc_threshold=args.high_adc_threshold,
                    low_adc_threshold=args.low_adc_threshold,
                )
            )

            print("\nBLE stream started.")
            print("Make sure the participant is wearing the T-shirt and standing still.")
            await asyncio.to_thread(input, "Press ENTER to start the protocol... ")

            # Initial baseline.
            await set_segment(
                state=state,
                position_index=1,
                phase="initial_baseline",
                duration_s=args.initial_baseline_s,
                set_id=0,
                rep=0,
                instruction=(
                    "INITIAL BASELINE: Participant stands straight, arms relaxed. "
                    "Do not move."
                ),
            )

            # Main protocol:
            # For each target position 2-8:
            #   repeat:
            #       transition to Position 1
            #       hold Position 1
            #       transition to target
            #       hold target
            for target_position in range(2, 9):
                set_id = target_position - 1
                target_name = POSITION_NAMES[target_position]

                for rep in range(1, args.repeats + 1):
                    await set_segment(
                        state=state,
                        position_index=1,
                        phase="transition",
                        duration_s=args.transition_s,
                        set_id=set_id,
                        rep=rep,
                        instruction=(
                            f"SET {set_id}, REP {rep}: Move to Position 1 "
                            f"({POSITION_NAMES[1]})."
                        ),
                    )

                    await set_segment(
                        state=state,
                        position_index=1,
                        phase="hold",
                        duration_s=args.hold_s,
                        set_id=set_id,
                        rep=rep,
                        instruction=(
                            f"SET {set_id}, REP {rep}: HOLD Position 1 "
                            f"({POSITION_NAMES[1]})."
                        ),
                    )

                    await set_segment(
                        state=state,
                        position_index=target_position,
                        phase="transition",
                        duration_s=args.transition_s,
                        set_id=set_id,
                        rep=rep,
                        instruction=(
                            f"SET {set_id}, REP {rep}: Move to Position "
                            f"{target_position} ({target_name})."
                        ),
                    )

                    await set_segment(
                        state=state,
                        position_index=target_position,
                        phase="hold",
                        duration_s=args.hold_s,
                        set_id=set_id,
                        rep=rep,
                        instruction=(
                            f"SET {set_id}, REP {rep}: HOLD Position "
                            f"{target_position} ({target_name})."
                        ),
                    )

            print("\nProtocol complete. Stopping BLE notifications...")
            state.current_phase = "complete"
            state.running = False

            await asyncio.sleep(0.5)
            await client.stop_notify(notify_uuid)
            await consumer_task

    print(f"\nRaw CSV saved:\n{raw_csv_path}")
    print(f"Total parsed samples: {state.sample_count}")
    print(f"Bad BLE lines: {state.bad_line_count}")

    processed_path = postprocess_csv(
        raw_csv_path=raw_csv_path,
        n_sensors=n_sensors,
        fixed_resistors_ohm=fixed_resistors,
        adc_max=args.adc_max,
        divider_mode=args.divider_mode,
        high_adc_threshold=args.high_adc_threshold,
        low_adc_threshold=args.low_adc_threshold,
        initial_baseline_s=args.initial_baseline_s,
    )

    plot_processed_csv(processed_path, n_sensors=n_sensors)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BLE data collection for 10-sensor smart T-shirt posture protocol."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_p = subparsers.add_parser("scan", help="Scan nearby BLE devices.")
    scan_p.add_argument("--scan-timeout", type=float, default=6.0)

    inspect_p = subparsers.add_parser("inspect", help="Inspect BLE services/characteristics.")
    inspect_p.add_argument("--address", type=str, default=None)
    inspect_p.add_argument("--name", type=str, default=None)
    inspect_p.add_argument("--scan-timeout", type=float, default=6.0)

    collect_p = subparsers.add_parser("collect", help="Run the full T-shirt protocol.")
    collect_p.add_argument("--address", type=str, default=None, help="BLE MAC/address.")
    collect_p.add_argument("--name", type=str, default=None, help="BLE device name substring.")
    collect_p.add_argument(
        "--char-uuid",
        type=str,
        default=DEFAULT_NOTIFY_CHAR_UUID,
        help=(
            "Notify characteristic UUID. Use 'auto' to select the first notify characteristic."
        ),
    )

    collect_p.add_argument("--subject", type=str, required=True, help="Subject ID, e.g., S01.")
    collect_p.add_argument("--run-id", type=str, default=None)
    collect_p.add_argument("--out-dir", type=str, default="tshirt_data")

    collect_p.add_argument("--n-sensors", type=int, default=10)
    collect_p.add_argument("--sample-rate-hz", type=float, default=20.0)

    collect_p.add_argument(
        "--fixed-resistors",
        type=str,
        default="3300",
        help=(
            "Fixed resistor value in ohms (default: 3300, verified for the study). "
            "Use one value or comma-separated values for each sensor."
        ),
    )

    collect_p.add_argument("--adc-max", type=int, default=4095)
    collect_p.add_argument(
        "--divider-mode",
        type=str,
        default="fixed_to_vcc_sensor_to_gnd",
        choices=["fixed_to_vcc_sensor_to_gnd", "sensor_to_vcc_fixed_to_gnd"],
    )

    collect_p.add_argument("--high-adc-threshold", type=int, default=3900)
    collect_p.add_argument("--low-adc-threshold", type=int, default=5)

    collect_p.add_argument("--initial-baseline-s", type=float, default=5.0)
    collect_p.add_argument("--hold-s", type=float, default=20.0)
    collect_p.add_argument("--transition-s", type=float, default=3.0)
    collect_p.add_argument("--repeats", type=int, default=5)
    collect_p.add_argument("--scan-timeout", type=float, default=6.0)

    post_p = subparsers.add_parser("postprocess", help="Post-process an existing raw CSV.")
    post_p.add_argument("raw_csv", type=str)
    post_p.add_argument("--n-sensors", type=int, default=10)
    post_p.add_argument(
        "--fixed-resistors",
        type=str,
        default="3300",
        help="Fixed resistor value(s) in ohms (default: 3300).",
    )
    post_p.add_argument("--adc-max", type=int, default=4095)
    post_p.add_argument(
        "--divider-mode",
        type=str,
        default="fixed_to_vcc_sensor_to_gnd",
        choices=["fixed_to_vcc_sensor_to_gnd", "sensor_to_vcc_fixed_to_gnd"],
    )
    post_p.add_argument("--high-adc-threshold", type=int, default=3900)
    post_p.add_argument("--low-adc-threshold", type=int, default=5)
    post_p.add_argument("--initial-baseline-s", type=float, default=5.0)

    plot_p = subparsers.add_parser("plot", help="Create Figure-6-style plot from processed CSV.")
    plot_p.add_argument("processed_csv", type=str)
    plot_p.add_argument("--n-sensors", type=int, default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        asyncio.run(scan_devices(args.scan_timeout))

    elif args.command == "inspect":
        asyncio.run(inspect_device(args.address, args.name, args.scan_timeout))

    elif args.command == "collect":
        asyncio.run(run_collection(args))

    elif args.command == "postprocess":
        n_sensors = args.n_sensors
        fixed_resistors = parse_resistor_list(args.fixed_resistors, n_sensors)
        postprocess_csv(
            raw_csv_path=Path(args.raw_csv),
            n_sensors=n_sensors,
            fixed_resistors_ohm=fixed_resistors,
            adc_max=args.adc_max,
            divider_mode=args.divider_mode,
            high_adc_threshold=args.high_adc_threshold,
            low_adc_threshold=args.low_adc_threshold,
            initial_baseline_s=args.initial_baseline_s,
        )

    elif args.command == "plot":
        plot_processed_csv(Path(args.processed_csv), n_sensors=args.n_sensors)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
