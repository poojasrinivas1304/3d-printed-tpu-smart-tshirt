#!/usr/bin/env python3
"""Create the corrected T-shirt acquisition and voltage-divider schematic."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Arc


INK = "#17212b"
BLUE = "#2166ac"
TEAL = "#1b9e77"
ORANGE = "#d95f02"
PALE = "#f4f7f9"


def box(ax, xy, width, height, text, *, fc=PALE, ec=INK, fontsize=11, weight="normal"):
    patch = FancyBboxPatch(
        xy, width, height, boxstyle="round,pad=0.015,rounding_size=0.025",
        facecolor=fc, edgecolor=ec, linewidth=1.4,
    )
    ax.add_patch(patch)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text,
            ha="center", va="center", fontsize=fontsize, fontweight=weight, color=INK)
    return patch


def arrow(ax, start, end, color=INK, lw=1.7):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, shrinkA=2, shrinkB=2))


def resistor(ax, x0, y, x1, color=INK, lw=1.7):
    lead = (x1 - x0) * 0.16
    ax.plot([x0, x0 + lead], [y, y], color=color, lw=lw)
    ax.plot([x1 - lead, x1], [y, y], color=color, lw=lw)
    xs = [x0 + lead]
    ys = [y]
    segments = 8
    span = x1 - x0 - 2 * lead
    for i in range(1, segments + 1):
        xs.append(x0 + lead + span * i / segments)
        ys.append(y + (0.025 if i % 2 else -0.025))
    xs.append(x1 - lead); ys.append(y)
    ax.plot(xs, ys, color=color, lw=lw)


def draw() -> plt.Figure:
    fig = plt.figure(figsize=(13.2, 7.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[0.95, 1.25], width_ratios=[1.05, 1.25])

    # Panel a: physical signal path.
    ax = fig.add_subplot(grid[0, :])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("a  Garment-to-computer acquisition path", loc="left", fontweight="bold", fontsize=14)
    box(ax, (0.03, 0.25), 0.18, 0.46, "Ten printed TPU\nstrain sensors\n(S1–S10)", fc="#e8f3ef", weight="bold")
    box(ax, (0.28, 0.25), 0.17, 0.46, "Ten independent\nvoltage dividers\non the interface PCB", fc="#eef4fb")
    box(ax, (0.52, 0.25), 0.14, 0.46, "ESP32\n12-bit ADC\n20 Hz", fc="#eef4fb", weight="bold")
    box(ax, (0.73, 0.25), 0.10, 0.46, "BLE", fc="#e8f3ef", weight="bold")
    box(ax, (0.89, 0.25), 0.08, 0.46, "Laptop\nlogging", fc="#fff3e8", weight="bold")
    arrow(ax, (0.21, 0.48), (0.28, 0.48), BLUE)
    arrow(ax, (0.45, 0.48), (0.52, 0.48), BLUE)
    arrow(ax, (0.66, 0.48), (0.73, 0.48), TEAL)
    arrow(ax, (0.83, 0.48), (0.89, 0.48), TEAL)
    ax.text(0.245, 0.55, "10 wires", ha="center", fontsize=9, color=BLUE)
    ax.text(0.485, 0.55, "ADC1", ha="center", fontsize=9, color=BLUE)
    ax.text(0.695, 0.55, "wireless", ha="center", fontsize=9, color=TEAL)

    # Panel b: repeated divider topology.
    ax = fig.add_subplot(grid[1, 0])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("b  Electrical topology for each channel", loc="left", fontweight="bold", fontsize=14)
    x = 0.38
    ax.text(x, 0.91, "3.3 V", ha="center", va="center", fontsize=11, fontweight="bold", color=ORANGE)
    ax.plot([x, x], [0.87, 0.78], color=ORANGE, lw=2)
    # vertical zig-zag fixed resistor
    ys = [0.78, 0.75, 0.72, 0.69, 0.66, 0.63, 0.60, 0.57, 0.54]
    xs = [x, x-0.02, x+0.02, x-0.02, x+0.02, x-0.02, x+0.02, x-0.02, x]
    ax.plot(xs, ys, color=INK, lw=1.8)
    ax.text(x + 0.07, 0.66, r"$R_f=3.3\,\mathrm{k\Omega}$", va="center", fontsize=11)
    ax.plot([x, x], [0.54, 0.46], color=INK, lw=1.8)
    ax.add_patch(Circle((x, 0.46), 0.009, fc=BLUE, ec=BLUE))
    ax.plot([x, 0.72], [0.46, 0.46], color=BLUE, lw=2)
    ax.text(0.73, 0.46, r"ADC$_i$", va="center", fontsize=11, fontweight="bold", color=BLUE)
    ax.text(0.73, 0.40, "one independent node\nper sensor", va="top", fontsize=9, color=BLUE)
    ax.plot([x, x], [0.45, 0.37], color=INK, lw=1.8)
    # sensor as variable resistor
    ys = [0.37, 0.34, 0.31, 0.28, 0.25, 0.22, 0.19, 0.16, 0.13]
    xs = [x, x-0.02, x+0.02, x-0.02, x+0.02, x-0.02, x+0.02, x-0.02, x]
    ax.plot(xs, ys, color=INK, lw=1.8)
    ax.annotate("", xy=(x+0.035, 0.27), xytext=(x+0.13, 0.35),
                arrowprops=dict(arrowstyle="->", lw=1.3, color=TEAL))
    ax.text(x + 0.07, 0.24, r"TPU sensor $R_{s,i}$", va="center", fontsize=11)
    ax.plot([x, x], [0.13, 0.08], color=INK, lw=1.8)
    ax.plot([x-0.045, x+0.045], [0.08, 0.08], color=INK, lw=1.8)
    ax.plot([x-0.030, x+0.030], [0.055, 0.055], color=INK, lw=1.5)
    ax.plot([x-0.015, x+0.015], [0.032, 0.032], color=INK, lw=1.2)
    ax.text(x, 0.005, "GND", ha="center", fontsize=10)
    ax.text(0.05, 0.48, "Repeated independently\nfor i = 1, …, 10", ha="left", va="center", fontsize=11,
            bbox=dict(boxstyle="round,pad=0.35", fc=PALE, ec="#8a969f"))

    # Panel c: acquisition pins and equations.
    ax = fig.add_subplot(grid[1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("c  ADC channels and nominal conversion", loc="left", fontweight="bold", fontsize=14)
    box(ax, (0.04, 0.60), 0.42, 0.24,
        "S1–S10 → GPIO\n36, 39, 34, 35, 32,\n33, 25, 26, 27, 14", fc="#eef4fb", fontsize=11)
    ax.text(0.53, 0.76, r"$V_{\mathrm{ADC},i}=3.3\,N_i/4095$", fontsize=14, color=INK)
    ax.text(0.53, 0.64, r"$R_{s,i}=R_f\,N_i/(4095-N_i)$", fontsize=14, color=INK)
    ax.text(0.05, 0.40,
            "Nᵢ is the 12-bit ADC count. Values near either rail are flagged before analysis;\n"
            "Nᵢ = 4095 does not yield a finite resistance estimate.", fontsize=10.5, va="top", color=INK)
    ax.text(0.05, 0.19,
            "The count-ratio equation is the nominal divider conversion. The classification\n"
            "analysis uses normalized resistance change (ΔR/R₀), not absolute resistance.",
            fontsize=10.5, va="top", color=INK)

    return fig


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    output = repo / "results" / "nested_grouped" / "Fig3_corrected.png"
    fig = draw()
    fig.savefig(output, dpi=450, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(output)
