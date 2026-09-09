# 3D-printed TPU sensor-embedded loose T-shirt

Reproducibility materials for the manuscript **“3D-printed TPU sensor-embedded loose T-shirt for wireless upper-body posture sensing.”**

**Release:** version 1.0.0, 9 September 2026.

## Participant datasets

The analysis-ready, de-identified files are:

- [`subject_01.csv`](data/processed/subject_01.csv) — S01, 16,900 rows
- [`subject_02.csv`](data/processed/subject_02.csv) — S02, 16,900 rows
- [`subject_03.csv`](data/processed/subject_03.csv) — S03, 16,901 rows

Each file is approximately 8.7 MB. GitHub may display “Sorry about that, but we can’t show files that are this big.” If that happens, select **Download raw file** on the file page. Column definitions and processing notes are provided in [`data/processed/README.md`](data/processed/README.md) and [`docs/data_dictionary.md`](docs/data_dictionary.md).

## Contents

- `code/acquisition/`: BLE discovery, acquisition, preprocessing, and plotting.
- `code/analysis/`: MATLAB scripts for the sensor-combination analysis and median-curve figures.
- `data/processed/`: approved, de-identified analysis files for Subjects 1–3.
- `hardware/esp32_ble/`: ten-channel `TSHIRT_01` BLE firmware used with the primary acquisition script.
- `hardware/legacy_wifi_udp/`: sanitized Wi-Fi/UDP prototype code retained for engineering reference only.
- `results/analysis/`: reference results and instructions for regenerating analysis outputs.
- `docs/`: data schema, ethics statement, date-correction record, and hardware status.

## Python setup

Python 3.10 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Discover the ESP32 and inspect its BLE service:

```bash
python code/acquisition/tshirt_ble_protocol.py scan
python code/acquisition/tshirt_ble_protocol.py inspect --name TSHIRT_01
```

Run the posture protocol. The acquisition program defaults to the verified study value of 3.3 kΩ:

```bash
python code/acquisition/tshirt_ble_protocol.py collect \
  --name TSHIRT_01 \
  --subject S01 \
  --out-dir private_data
```

Do not use names, initials, emails, medical-record numbers, or other direct identifiers as `--subject` values.

## MATLAB analysis

Run the scripts in `code/analysis/`; outputs are written to `results/analysis/`. The committed classification configuration matches the manuscript: random forest, 80 trees, minimum leaf size 2, uniform class priors, base seed 42, one deterministic run, and 20%, 30%, and 50% sample-level test fractions.

The classification script requires MATLAB's Statistics and Machine Learning Toolbox when `classifierType` is set to `randomforest` or `knn`.

## Data and ethics

The acquisition computer recorded an incorrect June calendar date. All three recordings were collected on 3 September 2026. The public copies were corrected with a constant date offset that preserves time of day, fractional seconds, sample spacing, elapsed time, and sensor measurements. The original workbooks remain unchanged outside this repository; their checksums and correction offsets are recorded in [`docs/date_correction_log.md`](docs/date_correction_log.md).

The public release is limited to de-identified sensor time series. The CSVs use S01–S03 and exclude names, contact information, the participant identity key, consent records, and absolute Unix timestamps. See [`docs/ethics_and_data_release.md`](docs/ethics_and_data_release.md).

## Citation

Citation metadata are available in [`CITATION.cff`](CITATION.cff). When reporting results, cite the exact repository commit used in addition to the associated manuscript.
