# Processed participant data

This directory contains the approved, de-identified analysis files:

- `subject_01.csv`
- `subject_02.csv`
- `subject_03.csv`

The public IDs are S01, S02, and S03. The mapping to identities must remain outside the repository in an access-controlled location.

The acquisition computer's incorrect June calendar date was corrected to the author-confirmed collection date of 3 September 2026. The correction preserved time of day, all relative timing, and raw ADC measurements. Resistance columns were recalculated with the verified 3.3 kΩ fixed resistor; normalized ΔR/R0 columns remain unchanged. Absolute `pc_time_unix_s` values were omitted from the public CSVs because the analysis uses `elapsed_s`; the corrected audit workbooks retain them. See [`../../docs/date_correction_log.md`](../../docs/date_correction_log.md).

See [`../../docs/data_dictionary.md`](../../docs/data_dictionary.md) for the required columns.
