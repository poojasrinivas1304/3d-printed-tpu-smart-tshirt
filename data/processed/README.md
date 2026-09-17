# Processed participant data

This directory contains the approved, de-identified analysis files:

- [`subject_01.csv`](subject_01.csv) — S01, 16,900 rows
- [`subject_02.csv`](subject_02.csv) — S02, 16,900 rows
- [`subject_03.csv`](subject_03.csv) — S03, 16,901 rows

Each CSV is approximately 8.1 MB and may exceed GitHub's browser-preview limit. Use **Download raw file** on the file page to obtain the complete CSV; no data are omitted from the downloadable file.

The public IDs are S01, S02, and S03. The mapping to identities must remain outside the repository in an access-controlled location.

Resistance columns use the 3.3 kΩ fixed resistor. The replacement CSV exports supplied on 17 September 2026 include corrected `pc_time_unix_s` timestamps and omit the previous `session_id` field. Analysis uses `elapsed_s` and the existing protocol fields. See [`../../docs/date_correction_log.md`](../../docs/date_correction_log.md).

Only the non-data title row above the column headers was removed from each supplied export. All data rows and values were retained as supplied. Compared with the earlier release, raw ADC measurements, movement labels, quality flags and row counts are identical; derived values have small export-rounding differences (up to 0.05 Ω for resistance). Original source files and previous Git revisions remain unchanged.

See [`../../docs/data_dictionary.md`](../../docs/data_dictionary.md) for the required columns.

## Positions 4 and 5

`position_index=4` / `touch_left_shoulder` means right hand touching the left shoulder with a leftward torso twist. `position_index=5` / `touch_right_shoulder` means left hand touching the right shoulder with a rightward torso twist. Directions refer to the participant. These definitions were confirmed by the investigator on 17 September 2026; no CSV labels, measurements or timestamps were changed for this clarification. See [movement-label reconciliation](../../docs/movement_label_reconciliation.md).
