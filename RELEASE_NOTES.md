# Release notes

## Current manuscript analysis

The current analysis is the Python [participant-calibrated ten-sensor random-sample workflow](code/analysis/within_recording_random_split/README.md). Mean participant scores are **96.16% accuracy, 96.83% macro precision, 95.34% macro recall/balanced accuracy and 96.06% macro-F1** from reused stratified 80/20 random-sample splits (10,141 test samples). Training-only three-fold selection considered 13 candidates; the selected models were 300-tree Extra Trees classifiers.

These are exploratory within-recording estimates. Training and testing share repetitions and temporally adjacent samples, and the partitions had already been inspected during development. The matched RF100 random-split comparator and nominal-repetition-held-out check are retained in the current package and manuscript supplement; neither design establishes independent-session or unseen-wearer performance.

## Version 1.1.0 — 19 September 2026

- Added the current code and aggregate-results package, pinned dependencies, settings, seeds, input/split checksums and reproduction instructions.
- Updated classification Figures 9 and 10 and their aggregate metrics.
- The release adds no individual predictions, train/test row indices or fitted models; reproduction generates them locally.
- Source datasets, acquisition code, hardware files and earlier numerical analysis records are unchanged. Older analysis documentation is labelled historical and linked to the current workflow.
- The archived Figure 6 renderer is identified separately from the current manuscript presentation.

## Historical grouped sensor-count analysis

The earlier Python [grouped nested-validation workflow](code/analysis/nested_grouped_classification.py) replaced the original MATLAB analysis at that stage of development. Its settings and results below are historical, not the current ten-sensor random-sample procedure or current Figures 9 and 10.

- Participant-specific five-fold outer validation and four-fold inner validation, grouped by stored repetition labels. These labels do not by themselves guarantee independence of complete physical cycles.
- Random forests with **20 trees for inner sensor selection** and **100 trees for outer testing**.
- Minimum leaf size 2, `max_features="sqrt"`, balanced class weights, and base random seed 42 with deterministic fold/configuration offsets.
- Non-overlapping 20-sample feature windows; imputation and standardization fitted within training folds.
- Nested-selected single sensors, pairs, and triplets compared with the ten-sensor baseline on the same outer partitions.

See the [historical analysis settings](results/nested_grouped/analysis_settings.json) for recorded software versions and the [historical results and reproduction instructions](results/nested_grouped/README.md). Earlier MATLAB results are retained as [superseded exploratory analysis](results/analysis/README.md). The later [2,032-window analysis](code/analysis/participant_calibrated/README.md) is also retained as development history. Neither archive generates the current random-sample manuscript figures.

## Version 1.0.0 — 9 September 2026

This release provides the de-identified participant datasets, the ESP32 BLE study firmware, Python acquisition software, MATLAB analysis scripts, hardware documentation, and data-processing documentation associated with the manuscript.

### Verified study configuration

- Three public participant identifiers: S01, S02, and S03.
- Data-collection date: 3 September 2026.
- Fixed resistor: 3.3 kΩ.
- Ten-channel ESP32 BLE firmware advertising as `TSHIRT_01` through the Nordic UART Service.
- Raw ADC acquisition at approximately 20 Hz.
- The original release used an 80-tree MATLAB random sample-level holdout workflow. That workflow was subsequently replaced by the historical grouped Python analysis described above; the current workflow is identified at the top of this page.

### Dataset documentation

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for the current CSV fields. The acquisition-clock correction and original-file checksums are documented in the [historical date-correction record](https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt/blob/77f5903a51cf0245eb49df8fd5a12bf64484f926/docs/date_correction_log.md).

### Scope

PCB and schematic files are not included. The Wi-Fi/UDP files under `hardware/legacy_wifi_udp/` are sanitized engineering prototypes and are not the study acquisition firmware.
