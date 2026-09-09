# Public-release checklist

The repository must remain private until all blocking items are completed.

## Blocking scientific and ethics checks

- [x] Locate and verify the three participant datasets collected on 3 September 2026; the acquisition computer's calendar date was corrected with an auditable constant offset.
- [ ] Confirm that written informed consent covered the intended reuse or public sharing.
- [x] Confirm that participant-level sensor time series may be publicly released (confirmation supplied by the author; retain the supporting institutional record outside the repository).
- [x] Resolve the apparent June dates: the author confirmed an acquisition-computer date error, and the originals, checksums, offsets, and corrected copies were retained for audit.
- [x] Replace direct names with stable public IDs S01–S03; omit absolute Unix timestamps from the public CSVs.
- [ ] Consider whether timestamps, rare posture patterns, or metadata create re-identification risk.

## Blocking hardware checks

- [x] Locate the ten-channel `TSHIRT_01` ESP32 BLE firmware used for manuscript data collection.
- [x] Verify the fixed-resistor value used in the reported experiments: **3.3 kΩ**.
- [x] Verify the voltage-divider topology: fixed resistor to 3.3 V, TPU sensor to ground, with the ADC at the midpoint.
- [x] Resolve the conflicting archived resistor values: the study value is 3.3 kΩ; other prototype values are not study configurations.
- [x] PCB/schematic design files are outside the scope of this release and will not be included.

## Reproducibility checks

- [ ] Run acquisition against the final firmware and record the firmware commit identifier.
- [ ] Run both MATLAB scripts from a fresh clone using only documented inputs.
- [ ] Confirm that regenerated values and figures match the final manuscript.
- [ ] Record MATLAB, Python, ESP32 core, and library versions.
- [ ] Add a small synthetic dataset or a fully approved de-identified dataset for smoke testing.

## Publication checks

- [ ] Obtain approval from all authors for the repository contents and author order.
- [x] Licensing decision deferred by the author; add formal code/data licenses later if requested by the supervising author, institution, repository, or journal.
- [ ] Remove manuscript publisher assets that cannot be redistributed.
- [ ] Run a secret scan and privacy review over the complete Git history.
- [ ] Create the public GitHub repository only after the preceding checks pass.
- [ ] Archive a release in Zenodo, obtain a DOI, and cite the version/DOI in the manuscript.
