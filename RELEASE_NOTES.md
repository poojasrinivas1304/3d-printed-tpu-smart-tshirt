# Release notes

## Version 1.0.0 — 9 September 2026

This release provides the de-identified participant datasets, the ESP32 BLE study firmware, Python acquisition software, MATLAB analysis scripts, hardware documentation, and data-processing documentation associated with the manuscript.

### Verified study configuration

- Three public participant identifiers: S01, S02, and S03.
- Data-collection date: 3 September 2026.
- Fixed resistor: 3.3 kΩ.
- Ten-channel ESP32 BLE firmware advertising as `TSHIRT_01` through the Nordic UART Service.
- Raw ADC acquisition at approximately 20 Hz.
- Random-forest manuscript configuration: 80 trees, minimum leaf size 2, uniform priors, base seed 42, and one deterministic run.

### Data protection

The public CSVs exclude direct names, contact information, the participant identity key, signed consent forms, device and network addresses, and absolute Unix timestamps. The acquisition-clock correction and original-file checksums are documented in `docs/date_correction_log.md`.

### Scope

PCB and schematic files are not included. The Wi-Fi/UDP files under `hardware/legacy_wifi_udp/` are sanitized engineering prototypes and are not the study acquisition firmware.
