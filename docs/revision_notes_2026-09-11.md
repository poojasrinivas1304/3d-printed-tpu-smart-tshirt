# T-shirt manuscript revision audit — 11 September 2026

## Hardware and channel identity

- The acquisition code and public datasets map S1–S10 to ESP32 GPIO 36, 39, 34, 35, 32, 33, 25, 26, 27, and 14, respectively.
- The dataset and code do not contain anatomical labels. The physical map was therefore checked against Figure 2 and confirmed by the author.
- The verified map is S1 right chest, S2 left chest, S3 centre chest, S4 horizontal torso, S5 right/lateral torso, S6 left/lateral torso, S7 lower-centre torso, S8 centre back, S9 left back, and S10 right back. This map is used consistently in the revised figure, table, acquisition-channel description and anatomical interpretation.
- The study topology documented by the author and acquisition code is 3.3 V → fixed resistor → independent ADC node → TPU sensor → GND. The corrected Figure 3 shows ten independent dividers and a 3.3 kΩ nominal fixed resistor.
- The three original workbooks contain resistance fields generated with inconsistent software constants (3.5 kΩ for Subjects 1 and 3; 3.0 kΩ for Subject 2). Public files were uniformly recalculated from raw ADC counts with 3.3 kΩ. Because a constant fixed-resistor factor cancels in ΔR/R0, this correction changes absolute resistance values but not the normalized classification input.
- The ADC-to-voltage expression is nominal: V_ADC = 3.3 N/4095. No channel-specific ESP32 ADC calibration was recorded, so absolute voltage/resistance should not be presented as metrologically calibrated.

## Leakage-resistant classification replacement

The former random sample-level holdout analysis is not suitable for a primary manuscript result because overlapping and adjacent measurements from the same repetition could appear in both partitions. It has been replaced by `code/analysis/nested_grouped_classification.py`:

- Participant-specific five-fold outer validation by repetition number.
- Complete repetitions remain intact across all phases and positions.
- Non-overlapping 20-sample (approximately 1 s) feature windows are created within each phase; no window crosses a repetition, phase, or fold boundary.
- Sensor selection uses only outer-training data through four inner repetition folds.
- Imputation and standardization are fitted within each training fold.
- Nested-selected single sensors, pairs, and triplets are compared with the ten-sensor baseline on identical outer folds.
- Held-posture windows are primary; transition windows are evaluated secondarily by the held-posture-trained models.

Pooled held-window out-of-fold results:

| Configuration | Accuracy | Balanced accuracy | Macro-F1 | Support |
|---|---:|---:|---:|---:|
| Selected single | 43.60% | 35.94% | 35.55% | 2032 |
| Selected pair | 50.30% | 45.18% | 45.04% | 2032 |
| Selected triplet | 55.22% | 49.35% | 50.57% | 2032 |
| Full ten-sensor baseline | 63.78% | 53.16% | 58.22% | 2032 |

Ten-sensor participant results:

| Participant | Accuracy | Balanced accuracy | Macro-F1 | Support |
|---|---:|---:|---:|---:|
| S1 | 66.03% | 54.49% | 59.36% | 677 |
| S2 | 63.42% | 52.78% | 57.26% | 678 |
| S3 | 61.89% | 52.16% | 57.00% | 677 |

Ten-sensor pooled class recalls were 77.97% (standing straight), 60.14% (left arm raise), 46.85% (right arm raise), 33.33% (left shoulder touch/twist), 53.74% (right shoulder touch/twist), 50.34% (both arms raise), 74.31% (forward bend), and 28.57% (sitting). The former 86.94% accuracy and 95.72% balanced-accuracy values must be removed.

The triplet selection was unstable: no triplet was selected in more than 2 of the 15 participant-by-outer-fold analyses. The data do not support calling S2–S5–S10, or any other triplet, uniquely optimal.

The ten-sensor held-posture error rate was 36.22%, compared with 76.88% during transition windows. This supports a quantitative, qualified statement that transitions were more difficult.

## Signal quality

- S9 for S2 was the only participant-channel combination with more than 1% near-saturation readings: 315/16,900 samples (1.86%) were ≥3900 counts and equal to 4095.
- Counts at either QC rail were treated as invalid and set to missing before feature extraction; training-fold medians were used for imputation.
- Excluding S9 gave 62.75% accuracy, 52.77% balanced accuracy and 57.46% macro-F1, similar to the ten-sensor result. The central conclusion therefore does not depend on the problematic S9 channel.

## Statistical and materials claims

- Ordinary one-way ANOVA is removed because it ignores within-participant dependence and is not defensible with n=3. Figure 7 is replaced with participant-level descriptive trajectories.
- SEM supports only qualitative morphology and contact observations. Claims that it establishes adhesion, attachment strength or durability are removed.
- The study did not quantify resistance–strain response, hysteresis, drift, cyclic repeatability, or attachment strength across independently fabricated T-shirt sensors. Claims are narrowed to prototype feasibility, and these measurements are listed as required future characterization.
- Unmeasured claims of lower cost, faster fabrication and improved reliability are removed.
- The distinction from the previous loose-garment paper is limited to observed design differences: direct fused-filament printing of conductive TPU and ESP32 BLE readout here, versus screen-printed sensors and laboratory DAQ previously. No superiority claim is made.

## Author-confirmed reporting details

- The conductive element was a commercially sourced graphene-based conductive TPU filament; the manufacturer and exact product designation were not recorded.
- The garment was a nylon-based activewear T-shirt. The precise fibre blend and garment dimensions were not recorded beyond the manufacturer's XL size designation.
- Three adults approximately 30 years of age participated (one female and two males). The size-XL garment accommodated all participants and was deliberately loose fitting.
- Eligibility required age of at least 18 years, capacity to provide informed consent, ability to wear the sensorized T-shirt safely and comfortably, and ability to perform the prescribed voluntary movements.
