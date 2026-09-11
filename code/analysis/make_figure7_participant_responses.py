#!/usr/bin/env python3
"""Create a descriptive participant-level posture-response figure."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SENSORS = range(1, 11)
POSITIONS = range(1, 9)
PARTICIPANTS = ("S1", "S2", "S3")
COLORS = {"S1": "#2166ac", "S2": "#b2182b", "S3": "#1b7837"}
MARKERS = {"S1": "o", "S2": "s", "S3": "^"}


def summarize(data_dir: Path) -> pd.DataFrame:
    rows = []
    for participant, filename in zip(PARTICIPANTS, ("subject_01.csv", "subject_02.csv", "subject_03.csv")):
        data = pd.read_csv(data_dir / filename)
        held = data[data["phase"].eq("hold")].copy()
        for sensor in SENSORS:
            values = pd.to_numeric(held[f"dr_s{sensor}"], errors="coerce")
            invalid = (
                pd.to_numeric(held[f"qc_high_adc_s{sensor}"], errors="coerce").fillna(1).ne(0)
                | pd.to_numeric(held[f"qc_low_adc_s{sensor}"], errors="coerce").fillna(1).ne(0)
            )
            held[f"valid_s{sensor}"] = values.mask(invalid)
            for position in POSITIONS:
                d = held.loc[held["position_index"].eq(position), f"valid_s{sensor}"]
                rows.append({
                    "participant": participant,
                    "sensor": sensor,
                    "position": position,
                    "median_dr_over_r0": float(np.nanmedian(d)),
                    "valid_samples": int(d.notna().sum()),
                })
    return pd.DataFrame(rows)


def draw(summary: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(5, 2, figsize=(11.5, 13.5), sharex=True, constrained_layout=True)
    axes = axes.ravel()
    for sensor, ax in zip(SENSORS, axes):
        d_sensor = summary[summary["sensor"].eq(sensor)]
        for participant in PARTICIPANTS:
            d = d_sensor[d_sensor["participant"].eq(participant)].sort_values("position")
            ax.plot(
                d["position"], d["median_dr_over_r0"], marker=MARKERS[participant],
                color=COLORS[participant], linewidth=1.6, markersize=5.5, label=participant,
            )
        ax.axhline(0, color="#7f7f7f", linewidth=0.8, linestyle="--")
        ax.text(0.02, 0.95, f"S{sensor}", transform=ax.transAxes, ha="left", va="top",
                fontsize=11, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.78))
        ax.set_xticks(list(POSITIONS))
        ax.grid(alpha=0.22)
        ax.tick_params(labelsize=9)
    for ax in axes[-2:]:
        ax.set_xlabel("Position", fontsize=10)
    for ax in axes:
        ax.set_ylabel(r"Median $\Delta R/R_0$", fontsize=9)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.015))
    fig.suptitle("Participant-level held-posture responses", fontsize=15, fontweight="bold", y=1.035)
    fig.savefig(output, dpi=450, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    out_dir = repo / "results" / "nested_grouped"
    out_dir.mkdir(parents=True, exist_ok=True)
    table = summarize(repo / "data" / "processed")
    table.to_csv(out_dir / "participant_posture_medians.csv", index=False)
    output = out_dir / "Fig7_participant_responses.png"
    draw(table, output)
    print(output)
