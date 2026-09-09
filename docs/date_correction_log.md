# Acquisition-clock correction log

The author confirmed that all three recordings were collected on **3 September 2026** and that the acquisition computer's calendar date was incorrect. The original workbooks remain unchanged outside this repository.

For each subject, a constant whole-day offset was added to every `pc_time_unix_s` value in the corrected audit workbook. This preserves local time of day, fractional seconds, sample spacing, elapsed time, protocol labels, and raw ADC measurements. Each `session_id` date prefix was changed to `20260903`, and subject IDs were assigned as S01–S03. The `r_s1_ohm` through `r_s10_ohm` columns were recalculated from the unchanged ADC values using the verified 3.3 kΩ fixed resistor and `R = Rf × ADC / (4095 − ADC)`. The normalized `dr_s1` through `dr_s10` values are unchanged because the constant resistance scale factor cancels in ΔR/R0. The public CSVs omit `pc_time_unix_s` because it is unnecessary for the analyses.

| Public ID | Original recorded date | Corrected date | Offset (seconds) | Source SHA-256 |
|---|---:|---:|---:|---|
| S01 | 2026-06-08 | 2026-09-03 | 7,516,800 | `6dcc64673e20ae92f4feaf37bb7f9cf94c5b435c7201fa661dddefd8558f2dba` |
| S02 | 2026-06-09 | 2026-09-03 | 7,430,400 | `774f83b36c426b7315c27538161c99649a7367935d8add5ed05f57fb2d47fb36` |
| S03 | 2026-06-08 | 2026-09-03 | 7,516,800 | `5225380beabf811bbc0f91e31e1a48b2209219c39b6c7a0b042359ab3222eae9` |

Correction recorded on 9 September 2026. The corrected workbooks contain the same log on a dedicated `Correction Log` worksheet.
