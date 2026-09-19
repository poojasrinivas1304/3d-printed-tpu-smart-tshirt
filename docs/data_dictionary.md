# Data dictionary

Each row represents one sampled time point. The table describes the main fields in the processed CSVs. The [current random-sample classifier](../code/analysis/within_recording_random_split/README.md) uses `adc_s1`–`adc_s10` as its ten sensor inputs and `position_index` as the target label. Training-fitted standardization is applied; one selected participant model also uses same-sample pairwise differences. Resistance, normalized-response and quality-control fields are not classifier inputs or exclusion criteria in that analysis. Relative time, phase and repetition fields support partitioning or diagnostics, not predictive features. `pc_time_unix_s` is metadata and is not used for classification. Descriptive resistance figures and historical analyses use separate processing, documented with their respective workflows.

| Field | Type | Description |
|---|---|---|
| `subject_id` | string | De-identified study code only. |
| `pc_time_unix_s` | number | Corrected Unix timestamp in seconds, retained from the supplied exports. See the [historical date-correction record](https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt/blob/77f5903a51cf0245eb49df8fd5a12bf64484f926/docs/date_correction_log.md). |
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

The current exports omit `session_id`, which was present in the earlier CSV release. One recording is provided per subject file.

## Movement labels

Left and right refer to the participant's anatomical sides. The `position_name` identifiers are unchanged in the released CSVs. For Positions 4 and 5, the identifier names the shoulder touched; the opposite hand touches that shoulder while the torso twists toward it.

| `position_index` | `position_name` | Movement definition |
|---|---|---|
| 1 | `standing_straight` | Standing straight. |
| 2 | `raise_left_arm` | Left arm raise. |
| 3 | `raise_right_arm` | Right arm raise. |
| 4 | `touch_left_shoulder` | Right hand touching the left shoulder with a leftward torso twist. |
| 5 | `touch_right_shoulder` | Left hand touching the right shoulder with a rightward torso twist. |
| 6 | `raise_both_arms` | Both arms raise. |
| 7 | `bend_forward` | Forward bend. |
| 8 | `sit` | Sitting. |

The compact analysis labels **Left shoulder touch and twist** and **Right shoulder touch and twist** denote Positions 4 and 5, respectively. See the [movement-label correction record](movement_label_reconciliation.md) for the discrepancy in the earlier acquisition-code labels and its resolution.
