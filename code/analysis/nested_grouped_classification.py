#!/usr/bin/env python3
"""Leakage-resistant nested grouped validation for the T-shirt study.

The outer and inner folds are defined by repetition number. A fold therefore
contains the complete repetition for every target posture and participant,
including the standing reference, movement-to-target, target hold, and return
transition. Non-overlapping one-second windows are constructed separately
within each phase, so no feature window overlaps another or crosses a phase,
repetition, or validation-fold boundary. Held-posture windows are the primary
classification analysis; transition windows are evaluated secondarily by the
model trained on held postures.

For each participant and outer fold, sensor subsets are ranked only on the
outer-training data by four-fold inner grouped validation.  Sequential forward
selection chooses a single sensor, then adds one sensor to form a pair, and then
adds one sensor to form a triplet.  Each selected subset is evaluated once on
the untouched outer fold.  The full
ten-sensor array is evaluated on the same outer folds as a prespecified
baseline.  All imputation and standardization are fitted on training data only.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from joblib import Parallel, delayed


SEED = 42
POSITIONS = tuple(range(1, 9))
POSITION_NAMES = {
    1: "Standing straight",
    2: "Left arm raise",
    3: "Right arm raise",
    4: "Left shoulder touch and twist",
    5: "Right shoulder touch and twist",
    6: "Both arms raise",
    7: "Forward bend",
    8: "Sitting",
}
SENSORS = tuple(range(1, 11))
FEATURE_NAMES = ("mean", "std", "median", "iqr", "minimum", "maximum", "slope")
WINDOW_SAMPLES = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve()
    repo = here.parents[2]
    parser.add_argument("--data-dir", type=Path, default=repo / "data" / "processed")
    parser.add_argument("--out-dir", type=Path, default=repo / "results" / "nested_grouped")
    parser.add_argument("--inner-trees", type=int, default=20)
    parser.add_argument("--outer-trees", type=int, default=100)
    parser.add_argument(
        "--inner-stride", type=int, default=1,
        help="Use every nth sample within each repetition for inner subset ranking only.",
    )
    parser.add_argument("--n-jobs", type=int, default=-1)
    return parser.parse_args()


def _validate_protocol(df: pd.DataFrame, source: Path) -> None:
    required = {
        "subject_id", "elapsed_s", "set_id", "rep", "phase",
        "position_index", "is_hold",
    }
    required.update({f"r_s{s}_ohm" for s in SENSORS})
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"{source.name}: missing columns {missing}")

    work = df.loc[df["set_id"].between(1, 7), ["set_id", "rep"]].drop_duplicates()
    expected = {(set_id, rep) for set_id in range(1, 8) for rep in range(1, 6)}
    observed = {tuple(map(int, row)) for row in work.to_numpy()}
    if observed != expected:
        raise ValueError(
            f"{source.name}: grouped validation requires 35 complete set/repetition "
            f"groups; missing={sorted(expected-observed)}, extra={sorted(observed-expected)}"
        )


def _recording_normalized_group(group: pd.DataFrame) -> pd.DataFrame:
    """Use the acquisition-time recording baseline and mask invalid ADC samples.

    The public ``dr_s*`` fields were calculated from the median resistance in
    the recording's initial five-second standing baseline. Feature windows are nevertheless generated separately
    inside each repetition so no window crosses a validation boundary.
    """
    group = group.sort_values("elapsed_s").copy()
    for sensor in SENSORS:
        values = pd.to_numeric(group[f"dr_s{sensor}"], errors="coerce").astype(float)
        high_col = f"qc_high_adc_s{sensor}"
        low_col = f"qc_low_adc_s{sensor}"
        invalid = ~np.isfinite(values)
        if high_col in group:
            invalid |= pd.to_numeric(group[high_col], errors="coerce").fillna(1).ne(0)
        if low_col in group:
            invalid |= pd.to_numeric(group[low_col], errors="coerce").fillna(1).ne(0)
        group[f"x_s{sensor}"] = values.mask(invalid)
    return group


def _window_features(group: pd.DataFrame) -> pd.DataFrame:
    """Return non-overlapping one-second feature windows for one repetition."""
    group = group.sort_values("elapsed_s").copy()
    segment_break = (
        group["phase"].ne(group["phase"].shift())
        | group["position_index"].ne(group["position_index"].shift())
    ).cumsum()
    rows: list[dict[str, object]] = []
    for _, segment in group.groupby(segment_break, sort=False):
        n_complete = len(segment) // WINDOW_SAMPLES
        for window_number in range(n_complete):
            window = segment.iloc[
                window_number * WINDOW_SAMPLES : (window_number + 1) * WINDOW_SAMPLES
            ]
            row: dict[str, object] = {
                "participant": window["participant"].iloc[0],
                "group_id": window["group_id"].iloc[0],
                "set_id": int(window["set_id"].iloc[0]),
                "rep": int(window["rep"].iloc[0]),
                "phase": window["phase"].iloc[0],
                "period": "Held posture" if window["phase"].iloc[0] == "hold" else "Transition",
                "position_index": int(window["position_index"].iloc[0]),
                "elapsed_s": float(window["elapsed_s"].mean()),
                "window_in_segment": window_number + 1,
                "window_samples": WINDOW_SAMPLES,
            }
            for sensor in SENSORS:
                values = window[f"x_s{sensor}"].to_numpy(dtype=float)
                finite = values[np.isfinite(values)]
                if finite.size == 0:
                    stats = [np.nan] * len(FEATURE_NAMES)
                else:
                    slope = (finite[-1] - finite[0]) / max(1, finite.size - 1)
                    stats = [
                        np.mean(finite), np.std(finite, ddof=1) if finite.size > 1 else 0.0,
                        np.median(finite), np.percentile(finite, 75) - np.percentile(finite, 25),
                        np.min(finite), np.max(finite), slope,
                    ]
                for name, value in zip(FEATURE_NAMES, stats):
                    row[f"f_s{sensor}_{name}"] = value
            rows.append(row)
    return pd.DataFrame(rows)


def load_data(data_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for subject_index, filename in enumerate(
        ("subject_01.csv", "subject_02.csv", "subject_03.csv"), start=1
    ):
        source = data_dir / filename
        df = pd.read_csv(source)
        _validate_protocol(df, source)
        df = df[df["set_id"].between(1, 7)].copy()
        df["participant"] = f"S{subject_index}"
        df["set_id"] = df["set_id"].astype(int)
        df["rep"] = df["rep"].astype(int)
        df["position_index"] = df["position_index"].astype(int)
        df["group_id"] = (
            df["participant"] + "_set" + df["set_id"].astype(str)
            + "_rep" + df["rep"].astype(str)
        )
        normalized = [
            _window_features(_recording_normalized_group(g))
            for _, g in df.groupby("group_id", sort=False)
        ]
        frames.append(pd.concat(normalized, ignore_index=True))
    out = pd.concat(frames, ignore_index=True)
    return out


def feature_columns(combo: tuple[int, ...]) -> list[str]:
    return [f"f_s{s}_{name}" for s in combo for name in FEATURE_NAMES]


def make_model(n_trees: int, n_jobs: int, random_state: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=n_trees,
                    min_samples_leaf=2,
                    max_features="sqrt",
                    class_weight="balanced",
                    random_state=random_state,
                    n_jobs=n_jobs,
                ),
            ),
        ]
    )


ALL_FEATURE_COLUMNS = feature_columns(SENSORS)


def preprocess_split(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Fit imputation/scaling on one training fold and transform its test fold."""
    train_x = train[ALL_FEATURE_COLUMNS].to_numpy(dtype=float)
    test_x = test[ALL_FEATURE_COLUMNS].to_numpy(dtype=float)
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    scaler = StandardScaler()
    train_x = imputer.fit_transform(train_x)
    test_x = imputer.transform(test_x)
    train_x = scaler.fit_transform(train_x)
    test_x = scaler.transform(test_x)
    return (
        train_x,
        train["position_index"].to_numpy(dtype=int),
        test_x,
        test["position_index"].to_numpy(dtype=int),
    )


def feature_indices(combo: tuple[int, ...]) -> np.ndarray:
    width = len(FEATURE_NAMES)
    return np.concatenate([np.arange((sensor - 1) * width, sensor * width) for sensor in combo])


def predict_preprocessed(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    combo: tuple[int, ...],
    n_trees: int,
    random_state: int,
) -> np.ndarray:
    cols = feature_indices(combo)
    classifier = RandomForestClassifier(
        n_estimators=n_trees,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        random_state=random_state,
        n_jobs=1,
    )
    classifier.fit(train_x[:, cols], train_y)
    return classifier.predict(test_x[:, cols]).astype(int)


def fit_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    combo: tuple[int, ...],
    n_trees: int,
    n_jobs: int,
    random_state: int,
) -> np.ndarray:
    model = make_model(n_trees, n_jobs, random_state)
    model.fit(train[feature_columns(combo)], train["position_index"])
    return model.predict(test[feature_columns(combo)]).astype(int)


def score_combo_inner_prepared(
    prepared_splits: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]],
    combo: tuple[int, ...],
    outer_rep: int,
    n_trees: int,
) -> tuple[float, float]:
    fold_bacc: list[float] = []
    fold_acc: list[float] = []
    for train_x, train_y, valid_x, valid_y, inner_rep in prepared_splits:
        seed = SEED + 1000 * outer_rep + 10 * inner_rep + len(combo)
        pred = predict_preprocessed(train_x, train_y, valid_x, combo, n_trees, seed)
        truth = valid_y
        fold_bacc.append(balanced_accuracy_score(truth, pred))
        fold_acc.append(accuracy_score(truth, pred))
    return float(np.mean(fold_bacc)), float(np.mean(fold_acc))


def choose_subset(
    prepared_splits: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]],
    size: int,
    outer_rep: int,
    n_trees: int,
    n_jobs: int,
    selected: tuple[int, ...] = (),
) -> tuple[tuple[int, ...], float, float]:
    if size == 1:
        combos = list(itertools.combinations(SENSORS, 1))
    else:
        combos = [tuple(sorted((*selected, sensor))) for sensor in SENSORS if sensor not in selected]
    scores = Parallel(n_jobs=n_jobs, prefer="threads")(
        delayed(score_combo_inner_prepared)(prepared_splits, combo, outer_rep, n_trees)
        for combo in combos
    )
    ranked = [(bacc, acc, combo) for combo, (bacc, acc) in zip(combos, scores)]
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    best_bacc, best_acc, best_combo = ranked[0]
    return best_combo, best_bacc, best_acc


def evaluate_nested(
    data: pd.DataFrame,
    inner_trees: int,
    outer_trees: int,
    inner_stride: int,
    n_jobs: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction_rows: list[pd.DataFrame] = []
    fold_rows: list[dict[str, object]] = []

    for participant, participant_data in data.groupby("participant", sort=True):
      for outer_rep in range(1, 6):
        outer_train = participant_data[participant_data["rep"] != outer_rep]
        outer_test = participant_data[participant_data["rep"] == outer_rep]
        held_train = outer_train[outer_train["period"] == "Held posture"]
        held_test = outer_test[outer_test["period"] == "Held posture"]
        inner_source = held_train.iloc[::max(1, inner_stride)].copy()
        prepared_inner = []
        for inner_rep in sorted(set(inner_source["rep"])):
            inner_train = inner_source[inner_source["rep"] != inner_rep]
            inner_valid = inner_source[inner_source["rep"] == inner_rep]
            prepared_inner.append((*preprocess_split(inner_train, inner_valid), int(inner_rep)))
        outer_train_x, outer_train_y, outer_test_x, outer_test_y = preprocess_split(held_train, outer_test)
        held_test_mask = outer_test["period"].eq("Held posture").to_numpy()
        configurations: list[tuple[str, tuple[int, ...], float, float]] = []

        selected: tuple[int, ...] = ()
        for size in (1, 2, 3):
            combo, inner_bacc, inner_acc = choose_subset(
                prepared_inner, size, outer_rep, inner_trees, n_jobs, selected
            )
            configurations.append((f"Selected {size}", combo, inner_bacc, inner_acc))
            selected = combo

        configurations.append(("Full 10", SENSORS, np.nan, np.nan))
        configurations.append(("Full 9 (S9 excluded)", tuple(s for s in SENSORS if s != 9), np.nan, np.nan))

        for config_index, (label, combo, inner_bacc, inner_acc) in enumerate(configurations):
            pred = predict_preprocessed(
                outer_train_x, outer_train_y, outer_test_x, combo, outer_trees,
                SEED + 100_000 + 1000 * outer_rep + config_index,
            )
            truth = outer_test_y
            held_truth = truth[held_test_mask]
            held_pred = pred[held_test_mask]
            combo_text = "-".join(f"S{s}" for s in combo)
            fold_rows.append(
                {
                    "outer_rep": outer_rep,
                    "participant": participant,
                    "configuration": label,
                    "sensors": combo_text,
                    "inner_mean_accuracy": inner_acc,
                    "inner_mean_balanced_accuracy": inner_bacc,
                    "outer_accuracy": accuracy_score(held_truth, held_pred),
                    "outer_balanced_accuracy": balanced_accuracy_score(held_truth, held_pred),
                    "outer_macro_f1": f1_score(held_truth, held_pred, labels=POSITIONS, average="macro", zero_division=0),
                    "n_test_samples": len(held_truth),
                    "n_test_groups": held_test["group_id"].nunique(),
                }
            )

            keep = outer_test[
                ["participant", "group_id", "set_id", "rep", "phase", "period", "position_index", "elapsed_s"]
            ].copy()
            keep["configuration"] = label
            keep["sensors"] = combo_text
            keep["predicted_position"] = pred
            keep["correct"] = pred == truth
            prediction_rows.append(keep)

    return pd.concat(prediction_rows, ignore_index=True), pd.DataFrame(fold_rows)


def summarize_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    overall_rows: list[dict[str, object]] = []
    posture_rows: list[dict[str, object]] = []
    period_rows: list[dict[str, object]] = []

    for config, d_config in predictions.groupby("configuration", sort=False):
        d_held = d_config[d_config["period"] == "Held posture"]
        for participant, d in [("All", d_held), *list(d_held.groupby("participant", sort=True))]:
            truth = d["position_index"].to_numpy()
            pred = d["predicted_position"].to_numpy()
            overall_rows.append(
                {
                    "configuration": config,
                    "participant": participant,
                    "accuracy": accuracy_score(truth, pred),
                    "balanced_accuracy": balanced_accuracy_score(truth, pred),
                    "macro_f1": f1_score(truth, pred, labels=POSITIONS, average="macro", zero_division=0),
                    "support": len(d),
                }
            )
            recalls = recall_score(truth, pred, labels=POSITIONS, average=None, zero_division=0)
            supports = np.array([(truth == position).sum() for position in POSITIONS])
            for position, recall, support in zip(POSITIONS, recalls, supports):
                posture_rows.append(
                    {
                        "configuration": config,
                        "participant": participant,
                        "position": position,
                        "posture": POSITION_NAMES[position],
                        "support": int(support),
                        "recall": float(recall),
                    }
                )

        for (participant, period), d in d_config.groupby(["participant", "period"], sort=True):
            period_rows.append(
                {
                    "configuration": config,
                    "participant": participant,
                    "period": period,
                    "support": len(d),
                    "accuracy": float(d["correct"].mean()),
                    "error_rate": float(1.0 - d["correct"].mean()),
                }
            )
        for period, d in d_config.groupby("period", sort=True):
            period_rows.append(
                {
                    "configuration": config,
                    "participant": "All",
                    "period": period,
                    "support": len(d),
                    "accuracy": float(d["correct"].mean()),
                    "error_rate": float(1.0 - d["correct"].mean()),
                }
            )

    return pd.DataFrame(overall_rows), pd.DataFrame(posture_rows), pd.DataFrame(period_rows)


def qc_summary(data_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for subject_index, filename in enumerate(
        ("subject_01.csv", "subject_02.csv", "subject_03.csv"), start=1
    ):
        df = pd.read_csv(data_dir / filename)
        for sensor in SENSORS:
            adc = pd.to_numeric(df[f"adc_s{sensor}"], errors="coerce")
            resistance = pd.to_numeric(df[f"r_s{sensor}_ohm"], errors="coerce")
            rows.append(
                {
                    "participant": f"S{subject_index}",
                    "sensor": sensor,
                    "samples": len(df),
                    "adc_min": float(adc.min()),
                    "adc_max": float(adc.max()),
                    "adc_le_5": int((adc <= 5).sum()),
                    "adc_ge_3900": int((adc >= 3900).sum()),
                    "adc_equal_4095": int((adc >= 4095).sum()),
                    "percent_ge_3900": 100.0 * float((adc >= 3900).mean()),
                    "invalid_resistance": int((~np.isfinite(resistance)).sum()),
                }
            )
    return pd.DataFrame(rows)


def make_figure(
    predictions: pd.DataFrame,
    folds: pd.DataFrame,
    posture: pd.DataFrame,
    periods: pd.DataFrame,
    out_path: Path,
) -> None:
    configs = ["Selected 1", "Selected 2", "Selected 3", "Full 10"]
    colors = ["#9ecae1", "#6baed6", "#3182bd", "#08519c"]
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.2), constrained_layout=False)
    # Keep all four analytical panels on the same two-column grid.  Inset
    # colorbars prevent the heatmaps from shrinking their axes and displacing
    # panels (b) and (d) relative to one another.
    fig.subplots_adjust(left=0.07, right=0.92, bottom=0.08, top=0.95,
                        wspace=0.27, hspace=0.30)

    ax = axes[0, 0]
    for i, (config, color) in enumerate(zip(configs, colors)):
        values = folds.loc[folds["configuration"] == config, "outer_balanced_accuracy"].to_numpy() * 100
        ax.scatter(np.full_like(values, i, dtype=float), values, color=color, edgecolor="black", s=42, zorder=3)
        ax.hlines(np.mean(values), i - 0.25, i + 0.25, color="black", linewidth=2)
    ax.set_xticks(range(len(configs)), ["Selected\nsingle", "Selected\npair", "Selected\ntriplet", "All 10\nsensors"])
    ax.set_ylabel("Outer-fold balanced accuracy (%)")
    ax.set_title("a  Grouped nested-validation performance", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)

    d = predictions[(predictions["configuration"] == "Full 10") & (predictions["period"] == "Held posture")]
    cm = confusion_matrix(d["position_index"], d["predicted_position"], labels=POSITIONS, normalize="true") * 100
    ax = axes[0, 1]
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=100)
    for r in range(8):
        for c in range(8):
            ax.text(c, r, f"{cm[r,c]:.0f}", ha="center", va="center", fontsize=7,
                    color="white" if cm[r,c] > 55 else "black")
    ax.set_xticks(range(8), range(1, 9)); ax.set_yticks(range(8), range(1, 9))
    ax.set_xlabel("Predicted position"); ax.set_ylabel("True position")
    ax.set_title("b  Ten-sensor out-of-fold confusion matrix", loc="left", fontweight="bold")
    cax = inset_axes(
        ax, width="3.5%", height="85%", loc="lower left",
        bbox_to_anchor=(1.04, 0.075, 1, 1), bbox_transform=ax.transAxes,
        borderpad=0,
    )
    fig.colorbar(im, cax=cax, label="Recall within true class (%)")

    rec = posture[(posture["configuration"] == "Full 10") & (posture["participant"] != "All")]
    heat = rec.pivot(index="participant", columns="position", values="recall").reindex(index=["S1", "S2", "S3"], columns=POSITIONS) * 100
    ax = axes[1, 0]
    im2 = ax.imshow(heat.to_numpy(), cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    for r in range(heat.shape[0]):
        for c in range(heat.shape[1]):
            ax.text(c, r, f"{heat.iloc[r,c]:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if heat.iloc[r,c] > 65 else "black")
    ax.set_xticks(range(8), range(1, 9)); ax.set_yticks(range(3), ["S1", "S2", "S3"])
    ax.set_xlabel("Position"); ax.set_ylabel("Participant")
    ax.set_title("c  Ten-sensor recall by participant and posture", loc="left", fontweight="bold")
    cax2 = inset_axes(
        ax, width="3.5%", height="85%", loc="lower left",
        bbox_to_anchor=(1.04, 0.075, 1, 1), bbox_transform=ax.transAxes,
        borderpad=0,
    )
    fig.colorbar(im2, cax=cax2)

    per = periods[(periods["configuration"] == "Full 10") & (periods["participant"] != "All")]
    pivot = per.pivot(index="participant", columns="period", values="error_rate").reindex(["S1", "S2", "S3"]) * 100
    ax = axes[1, 1]
    x = np.arange(3); width = 0.26
    held_bars = ax.bar(
        x - width/2, pivot["Held posture"], width, label="Held posture",
        color="#9ecae1", edgecolor="#1f1f1f", linewidth=0.8,
    )
    transition_bars = ax.bar(
        x + width/2, pivot["Transition"], width, label="Transition",
        color="#3182bd", edgecolor="#1f1f1f", linewidth=0.8,
    )
    ax.set_xticks(x, ["S1", "S2", "S3"])
    ax.set_ylabel("Error rate (%)")
    ax.set_title("d  Errors during held and transition periods", loc="left", fontweight="bold")
    ax.set_ylim(0, 100)
    ax.bar_label(held_bars, fmt="%.1f", padding=3, fontsize=8)
    ax.bar_label(transition_bars, fmt="%.1f", padding=3, fontsize=8)
    ax.legend(frameon=False, loc="upper center", ncol=2)
    ax.grid(axis="y", alpha=0.25)
    ax.set_box_aspect(1)

    fig.savefig(out_path, dpi=600, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    data = load_data(args.data_dir)
    predictions, folds = evaluate_nested(
        data, args.inner_trees, args.outer_trees, args.inner_stride, args.n_jobs
    )
    overall, posture, periods = summarize_metrics(predictions)
    qc = qc_summary(args.data_dir)

    stability = (
        folds[folds["configuration"].str.startswith("Selected")]
        .groupby(["configuration", "sensors"], as_index=False)
        .agg(selection_count=("outer_rep", "count"))
    )
    stability["selection_frequency"] = stability["selection_count"] / 15.0

    outputs = {
        "outer_fold_results.csv": folds,
        "outer_fold_predictions.csv": predictions,
        "overall_and_participant_metrics.csv": overall,
        "participant_posture_metrics.csv": posture,
        "held_transition_metrics.csv": periods,
        "selection_stability.csv": stability,
        "adc_quality_summary.csv": qc,
    }
    for filename, table in outputs.items():
        table.to_csv(args.out_dir / filename, index=False)

    make_figure(predictions, folds, posture, periods, args.out_dir / "Fig9_grouped_nested.png")

    settings = {
        "validation": "participant-specific five outer folds by repetition number; four inner folds by repetition number",
        "selection": "nested sequential forward selection (single, then pair, then triplet)",
        "group_definition": "target set + repetition within participant; all reference, transition and hold samples kept together",
        "normalization": "acquisition-time delta R/R0 using median resistance in the recording's initial five-second standing baseline",
        "features": list(FEATURE_NAMES),
        "primary_analysis": "held-posture windows",
        "transition_analysis": "secondary predictions from the held-posture-trained model",
        "feature_window_samples": WINDOW_SAMPLES,
        "feature_windows_overlap": 0,
        "inner_trees": args.inner_trees,
        "outer_trees": args.outer_trees,
        "inner_stride": args.inner_stride,
        "random_seed": SEED,
        "software": {
            "python": __import__("sys").version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": __import__("sklearn").__version__,
            "matplotlib": __import__("matplotlib").__version__,
        },
    }
    (args.out_dir / "analysis_settings.json").write_text(json.dumps(settings, indent=2) + "\n")

    print("\nOuter-fold results")
    print(folds.to_string(index=False))
    print("\nPooled and participant metrics")
    print(overall.to_string(index=False))
    print(f"\nSaved outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
