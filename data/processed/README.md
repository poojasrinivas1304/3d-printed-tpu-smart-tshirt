# Processed participant data

This directory contains the approved, de-identified analysis files:

- [`subject_01.csv`](subject_01.csv) — S01, 16,900 rows
- [`subject_02.csv`](subject_02.csv) — S02, 16,900 rows
- [`subject_03.csv`](subject_03.csv) — S03, 16,901 rows

Each CSV is approximately 8.7 MB and may exceed GitHub's browser-preview limit. Use **Download raw file** on the file page to obtain the complete CSV; no data are omitted from the downloadable file.

The public IDs are S01, S02, and S03. The mapping to identities must remain outside the repository in an access-controlled location.

Resistance columns were recalculated with the verified 3.3 kΩ fixed resistor; normalized ΔR/R0 columns remain unchanged. Absolute `pc_time_unix_s` values were omitted from the public CSVs because the analysis uses `elapsed_s`; the corrected audit workbooks retain them. See [`../../docs/date_correction_log.md`](../../docs/date_correction_log.md).

See [`../../docs/data_dictionary.md`](../../docs/data_dictionary.md) for the required columns.

## Positions 4 and 5

`position_index=4` / `touch_left_shoulder` means right hand touching the left shoulder with a leftward torso twist. `position_index=5` / `touch_right_shoulder` means left hand touching the right shoulder with a rightward torso twist. Directions refer to the participant. These definitions were confirmed by the investigator on 17 September 2026; no CSV labels, measurements or timestamps were changed for this clarification. See [movement-label reconciliation](../../docs/movement_label_reconciliation.md).
