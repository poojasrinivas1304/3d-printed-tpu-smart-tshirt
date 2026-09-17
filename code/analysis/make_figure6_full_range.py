#!/usr/bin/env python3
"""Regenerate Figure 6 from the published participant CSVs without axis clipping.

The source measurements and stored dr_s1--dr_s10 normalization are unchanged.
Quality masks and the 0.25-s host-time line-break rule match the manuscript.
No smoothing, resampling, downsampling, imputation, or amplitude-based selection.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import numpy as np
import pandas as pd

DATA_COMMIT = "899a984b25b5ff510d84a702cf7b74f8dc64f4b6"
EXPECTED_BLOBS = {
    "subject_01.csv": "475e77097760d0642c400b4001deb8e209344a93",
    "subject_02.csv": "96a096cf6c703cbeed5f615327b741a0c778e00f",
    "subject_03.csv": "572e1fb108a21adb8a84693af0d4aabad530ed69",
}
EXPECTED_ROWS = [16900, 16900, 16901]
GAP_SECONDS = 0.25


def file_hashes(path):
    content = path.read_bytes()
    blob = b"blob " + str(len(content)).encode() + b"\0" + content
    return {"git_blob_sha1": hashlib.sha1(blob).hexdigest(),
            "sha256": hashlib.sha256(content).hexdigest()}


def break_line_at_host_gaps(t, y):
    """Insert NaNs without removing either observation adjacent to a time gap."""
    gaps = np.flatnonzero(np.diff(t) > GAP_SECONDS) + 1
    return np.insert(t, gaps, t[gaps]), np.insert(y, gaps, np.nan)


def block_intervals(data):
    values = data.set_id.to_numpy()
    times = data.elapsed_s.to_numpy(dtype=float)
    starts = np.r_[0, np.flatnonzero(values[1:] != values[:-1]) + 1]
    for i, start in enumerate(starts):
        end = times[starts[i + 1]] if i + 1 < len(starts) else times[-1]
        yield int(values[start]), times[start], end


def read_sources(data_dir):
    frames, sources = [], []
    for i, filename in enumerate(EXPECTED_BLOBS):
        path = data_dir / filename
        hashes = file_hashes(path)
        if hashes["git_blob_sha1"] != EXPECTED_BLOBS[filename]:
            raise ValueError(f"{filename}: does not match the pinned published export")
        data = pd.read_csv(path)
        required = {"sample_index", "elapsed_s", "phase", "set_id", "position_index"}
        for sensor in range(1, 11):
            required.update({f"adc_s{sensor}", f"r_s{sensor}_ohm", f"dr_s{sensor}",
                             f"qc_high_adc_s{sensor}", f"qc_low_adc_s{sensor}"})
        if not required.issubset(data.columns):
            raise ValueError(f"Missing required columns in {filename}")
        assert len(data) == EXPECTED_ROWS[i]
        assert data.sample_index.is_unique
        assert np.isfinite(data.elapsed_s).all()
        assert data.elapsed_s.is_monotonic_increasing
        frames.append(data)
        sources.append({"participant": f"P{i+1:02}", "filename": filename,
                        "rows": len(data), "columns": len(data.columns), **hashes,
                        "elapsed_first_s": float(data.elapsed_s.iloc[0]),
                        "elapsed_last_s": float(data.elapsed_s.iloc[-1]),
                        "host_gaps_gt_025_s": int(data.elapsed_s.diff().gt(GAP_SECONDS).sum())})
    return frames, sources


def render(frames, output_dir):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.unicode_minus": True, "path.simplify": False,
                         "agg.path.chunksize": 0, "savefig.facecolor": "white"})
    fig, axes = plt.subplots(11, 3, figsize=(6.8, 8.05), sharex="col",
                             gridspec_kw={"height_ratios": [0.72] + [1] * 10})
    fig.subplots_adjust(left=0.122, right=0.992, top=0.948, bottom=0.091,
                        hspace=0.28, wspace=0.32)
    panel_checks = []
    xmax = max(float(d.elapsed_s.iloc[-1]) for d in frames)
    xlim = (-0.004 * xmax, xmax * 1.004)
    trace_color, qc_color = "#183f59", "#af3e2d"
    for column, data in enumerate(frames):
        participant = f"P{column+1:02}"
        t = data.elapsed_s.to_numpy(dtype=float)
        top = axes[0, column]
        tt, yy = break_line_at_host_gaps(t, data.position_index.to_numpy(dtype=float))
        top.step(tt, yy, where="post", color="#343434", linewidth=0.55)
        top.set_ylim(0.5, 8.5)
        top.set_yticks([1, 4, 8])
        top.set_title(participant, fontsize=10, fontweight="bold", pad=7)
        if column == 0:
            top.set_ylabel("Posture", fontsize=8, labelpad=7)
        for sensor in range(1, 11):
            ax = axes[sensor, column]
            adc = data[f"adc_s{sensor}"].to_numpy(dtype=float)
            hi = data[f"qc_high_adc_s{sensor}"].to_numpy(dtype=float)
            lo = data[f"qc_low_adc_s{sensor}"].to_numpy(dtype=float)
            raw = data[f"dr_s{sensor}"].to_numpy(dtype=float)
            resistance = data[f"r_s{sensor}_ohm"].to_numpy(dtype=float)
            np.testing.assert_array_equal(hi, (adc >= 3900).astype(int))
            np.testing.assert_array_equal(lo, (adc <= 5).astype(int))
            invalid = (hi != 0) | (lo != 0) | ~np.isfinite(raw) | ~np.isfinite(resistance)
            y = raw.copy()
            y[invalid] = np.nan
            finite = y[np.isfinite(y)]
            assert finite.size > 0
            lower, upper = min(float(finite.min()), 0), max(float(finite.max()), 0)
            padding = max((upper - lower) * 0.10, 0.015)
            ymin, ymax = lower - padding, upper + padding
            tx, py = break_line_at_host_gaps(t, y)
            line, = ax.plot(tx, py, color=trace_color, linewidth=0.47)
            # A valid sample between two gaps has no line segment. Show it as
            # a dot so isolated peaks are not silently invisible.
            has_value = np.isfinite(py)
            isolated = has_value & ~np.r_[False, has_value[:-1]] & ~np.r_[has_value[1:], False]
            ax.plot(tx[isolated], py[isolated], linestyle="none", marker=".",
                    markersize=1.8, color=trace_color, zorder=3)
            ax.axhline(0, color="#a2a2a2", linestyle=(0, (2, 2)), linewidth=0.35, zorder=0)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=2, min_n_ticks=2))
            formatter = ScalarFormatter(useOffset=False)
            formatter.set_scientific(False)
            ax.yaxis.set_major_formatter(formatter)
            ax.set_ylim(ymin, ymax)
            if column == 0:
                ax.set_ylabel(f"S{sensor}", rotation=0, fontsize=8.5, labelpad=12, va="center")
            postbaseline = invalid & data.phase.ne("initial_baseline").to_numpy()
            ax.plot(t[postbaseline], np.full(int(postbaseline.sum()), 0.96),
                    color=qc_color, linestyle="none", marker="|", markersize=3,
                    markeredgewidth=0.65, transform=ax.get_xaxis_transform(), zorder=4)
            plotted = np.asarray(line.get_ydata())
            plotted = plotted[np.isfinite(plotted)]
            np.testing.assert_array_equal(plotted, raw[~invalid])
            outside = int(((plotted < ymin) | (plotted > ymax)).sum())
            assert outside == 0
            assert np.all((t >= xlim[0]) & (t <= xlim[1]))
            panel_checks.append({"participant": participant, "sensor": f"S{sensor}",
                "source_rows": len(data), "plotted_valid_values": len(plotted),
                "baseline_missing_or_invalid": int((invalid & ~data.phase.ne("initial_baseline").to_numpy()).sum()),
                "postbaseline_masked_values": int(postbaseline.sum()),
                "finite_source_min_before_qc": float(np.nanmin(raw)),
                "finite_source_max_before_qc": float(np.nanmax(raw)),
                "valid_min": float(finite.min()), "valid_max": float(finite.max()),
                "y_lower": ymin, "y_upper": ymax, "clipped_valid_values": outside,
                "isolated_valid_values_shown_as_dots": int(isolated.sum()),
                "valid_values_preserved_exactly": True})
        for ax in axes[:, column]:
            for block, left, right in block_intervals(data):
                if block > 0 and block % 2:
                    ax.axvspan(left, right, color="#edf1f4", linewidth=0, zorder=-2)
            ax.set_xlim(*xlim)
            ax.set_xticks([0, 400, 800])
            ax.spines[["top", "right"]].set_visible(False)
            for side in ["left", "bottom"]:
                ax.spines[side].set_linewidth(0.5)
                ax.spines[side].set_color("#606060")
            ax.tick_params(width=0.5, length=2, pad=2, labelsize=7.8)
    fig.text(0.012, 0.49, r"Normalized resistance change, $\Delta R_i/R_{0,i}$",
             va="center", rotation=90, fontsize=9)
    fig.text(0.553, 0.048, "Host elapsed time (s)", ha="center", fontsize=8.5)
    fig.legend(handles=[Line2D([0], [0], color=trace_color, linewidth=0.8, label="Valid response"),
                        Line2D([0], [0], color=qc_color, marker="|", markersize=5,
                               linestyle="none", label="QC-masked sample (time only)")],
               loc="lower center", bbox_to_anchor=(0.55, 0.001), ncol=2,
               frameon=False, fontsize=7.8, columnspacing=1.5, handlelength=1.7)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside = []
    for item in fig.findobj(Text):
        if not item.get_visible() or not item.get_text():
            continue
        bbox = item.get_window_extent(renderer)
        # Tick text outside the axis range is suppressed by Matplotlib.
        if item.axes and item in item.axes.get_yticklabels():
            value = item.get_position()[1]
            if not item.axes.get_ylim()[0] <= value <= item.axes.get_ylim()[1]:
                continue
        if bbox.x0 < 0 or bbox.y0 < 0 or bbox.x1 > fig.bbox.width or bbox.y1 > fig.bbox.height:
            outside.append(item.get_text())
    assert not outside, outside
    fig.savefig(output_dir / "Fig6.png", dpi=600)
    fig.savefig(output_dir / "Fig6_preview.png", dpi=180)
    plt.close(fig)
    return panel_checks, {"panels": len(panel_checks), "clipped_valid_values": 0,
                          "text_outside_canvas": outside, "png_dpi": 600}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    repo = Path(__file__).resolve().parents[2]
    parser.add_argument("--data-dir", type=Path, default=repo / "data" / "processed")
    parser.add_argument("--out-dir", type=Path, default=repo / "results" / "figure6")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames, sources = read_sources(args.data_dir)
    checks, summary = render(frames, args.out_dir)
    for source in sources:
        assert file_hashes(args.data_dir / source["filename"])["sha256"] == source["sha256"]
    report = {"input_commit": DATA_COMMIT,
        "normalization": "Use the published dr_s1--dr_s10 without recalculation.",
        "mask_rule": "Nonzero channel QC flag or nonfinite normalized response/resistance; no imputation.",
        "gap_rule": "Insert a line break at host elapsed-time gaps >0.25 s, retaining both observations.",
        "axes": "Separate linear ranges per participant/channel; full valid min/max including zero plus 10% padding (minimum 0.015).",
        "display": "Entire recordings, all valid values, no smoothing/resampling/downsampling, no path simplification. Isolated valid samples are dots.",
        "qc_marks": "Post-baseline masked samples are red time-only ticks, not measured amplitudes.",
        "sources": sources, "panels": checks,
        "verification": {**summary, "source_files_unchanged": True, "source_rows": sum(len(d) for d in frames)},
        "software": {"python": sys.version.split()[0], "pandas": pd.__version__,
                     "numpy": np.__version__, "matplotlib": matplotlib.__version__}}
    (args.out_dir / "Fig6_range_check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["verification"], indent=2))
    print(args.out_dir / "Fig6.png")


if __name__ == "__main__":
    main()
