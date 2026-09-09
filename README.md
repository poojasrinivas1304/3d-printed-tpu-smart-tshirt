# 3D-printed TPU sensor-embedded loose T-shirt

Reproducibility materials for the manuscript **“3D-printed TPU sensor-embedded loose T-shirt for wireless upper-body posture sensing.”**

> **Release status:** public reproducibility package, released on 9 September 2026. Remaining maintenance checks are documented in [`PUBLIC_RELEASE_CHECKLIST.md`](PUBLIC_RELEASE_CHECKLIST.md).

## Contents

- `code/acquisition/`: BLE discovery, acquisition, preprocessing, and plotting.
- `code/analysis/`: MATLAB scripts for the sensor-combination analysis and median-curve figures.
- `data/processed/`: approved, de-identified analysis files for Subjects 1–3.
- `hardware/esp32_ble/`: ten-channel `TSHIRT_01` BLE firmware used with the primary acquisition script.
- `hardware/legacy_wifi_udp/`: sanitized Wi-Fi/UDP prototype code retained for engineering reference only.
- `results/analysis/`: generated analysis outputs; these are not committed by default.
- `docs/`: data schema, ethics/release guidance, and hardware status.

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

The three analysis-ready files are:

```text
data/processed/subject_01.csv
data/processed/subject_02.csv
data/processed/subject_03.csv
```

Then run the scripts in `code/analysis/`. Outputs are written to `results/analysis/`.

The classification script requires MATLAB's Statistics and Machine Learning Toolbox when `classifierType` is set to `randomforest` or `knn`.

## Data and ethics

The acquisition computer recorded an incorrect June calendar date. After the author confirmed that all three recordings were collected on 3 September 2026, the public copies were corrected by applying a constant date offset while preserving time of day, fractional seconds, sample spacing, elapsed time, and all sensor measurements. The original workbooks remain unchanged outside this repository, and their checksums and correction offsets are recorded in [`docs/date_correction_log.md`](docs/date_correction_log.md).

The authors report that public participant-data sharing is permitted. Public CSVs use S01–S03, omit the direct-name row, and omit absolute Unix timestamps. See [`docs/ethics_and_data_release.md`](docs/ethics_and_data_release.md).

## Citation and reuse

Citation metadata are available in [`CITATION.cff`](CITATION.cff). A formal software/data license is intentionally deferred and can be added later if requested by the supervising author, institution, repository, or journal. Until then, public visibility does not itself grant legal reuse rights.
