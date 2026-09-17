# Release notes

## Current manuscript analysis

The primary analysis is the Python [grouped nested-validation workflow](code/analysis/nested_grouped_classification.py), not the earlier random sample-level MATLAB holdout analysis.

- Participant-specific five-fold outer validation and four-fold inner validation, grouped by complete posture repetition.
- Random forests with **20 trees for inner sensor selection** and **100 trees for outer testing**.
- Minimum leaf size 2, `max_features="sqrt"`, balanced class weights, and base random seed 42 with deterministic fold/configuration offsets.
- Non-overlapping 20-sample feature windows; imputation and standardization fitted within training folds.
- Nested-selected single sensors, pairs, and triplets compared with the ten-sensor baseline on the same outer partitions.

See the [analysis settings](results/nested_grouped/analysis_settings.json) for recorded software versions and the [current results and reproduction instructions](results/nested_grouped/README.md). Earlier MATLAB results are retained as [superseded exploratory analysis](results/analysis/README.md).

## Version 1.0.0 — 9 September 2026

This release provides the de-identified participant datasets, the ESP32 BLE study firmware, Python acquisition software, MATLAB analysis scripts, hardware documentation, and data-processing documentation associated with the manuscript.

### Verified study configuration

- Three public participant identifiers: S01, S02, and S03.
- Data-collection date: 3 September 2026.
- Fixed resistor: 3.3 kΩ.
- Ten-channel ESP32 BLE firmware advertising as `TSHIRT_01` through the Nordic UART Service.
- Raw ADC acquisition at approximately 20 Hz.
- The original release used an 80-tree MATLAB random sample-level holdout workflow. That workflow has been superseded by the grouped Python analysis described above.

### Dataset documentation

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for the current CSV fields. The acquisition-clock correction and original-file checksums are documented in the [historical date-correction record](https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt/blob/77f5903a51cf0245eb49df8fd5a12bf64484f926/docs/date_correction_log.md).

### Scope

PCB and schematic files are not included. The Wi-Fi/UDP files under `hardware/legacy_wifi_udp/` are sanitized engineering prototypes and are not the study acquisition firmware.
