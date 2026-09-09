# Data dictionary

Each row represents one sampled time point. The MATLAB analysis requires the following core fields; the acquisition program may provide additional quality-control fields.

| Field | Type | Description |
|---|---|---|
| `subject_id` | string | De-identified study code only. |
| `session_id` | string | De-identified recording-session code. Avoid calendar timestamps in public releases unless approved. |
| `sample_index` | integer | Sequential sample number. |
| `elapsed_s` | number | Seconds from the start of the recording. |
| `set_id` | integer | Protocol set number. |
| `rep` | integer | Repetition number within a set. |
| `phase` | string | Protocol phase, such as `initial_baseline`, `transition`, or `hold`. |
| `position_index` | integer | Posture class from 1 through 8. |
| `position_name` | string | Human-readable posture label. |
| `is_hold` | logical/integer | Whether the sample belongs to a steady hold interval. |
| `adc_s1` … `adc_s10` | number | Raw ADC measurements from sensors 1–10. |
| `r_s1_ohm` … `r_s10_ohm` | number | Derived sensor resistance in ohms. |
| `dr_s1` … `dr_s10` | number | Normalized resistance change, `(R-R0)/R0`. |
| `qc_high_adc_s1` … `qc_high_adc_s10` | logical/integer | High/saturated ADC flags. |
| `qc_low_adc_s1` … `qc_low_adc_s10` | logical/integer | Low/saturated ADC flags. |

Public files should omit `pc_time_unix_s`, device addresses, network addresses, names, initials, contact details, consent documentation, and the private identifier key unless their inclusion has been specifically approved.

