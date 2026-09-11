# Response to T-shirt manuscript comments

Thank you for the detailed comments. We have revised the manuscript and analysis as follows.

1. **Sensor numbering.** We verified the physical map against Figure 2 and synchronized the figure, Table 1, Methods, channel order, and anatomical descriptions. The confirmed map is S1 right chest, S2 left chest, S3 centre chest, S4 horizontal torso, S5 right lateral torso, S6 left lateral torso, S7 lower-centre torso, S8 centre back, S9 left back, and S10 right back.

2. **Circuit and resistance calculation.** Figure 3 now shows ten independent dividers with the actual topology: 3.3 V to a 3.3 kOhm fixed resistor, then the individual ADC node, TPU sensor, and ground. The equation and public analysis use the same orientation and 3.3 kOhm value. The public resistance columns were recalculated from the retained raw ADC counts. Because the fixed-resistor factor cancels in Delta R/R0, this correction changes nominal absolute resistance but not the normalized classification input.

3. **Grouped validation.** The sample-level split was replaced by participant-specific five-fold validation grouped by complete posture repetition. Each group contains the associated standing-reference, movement, held-posture, and return-movement phases. Non-overlapping one-second windows are generated within a single phase and repetition, so measurements from one repetition cannot occur in both training and testing.

4. **Nested sensor selection.** Single sensors, pairs, and triplets are now selected only within the outer-training data using four inner repetition-grouped folds. The selected subset is evaluated once on the untouched outer fold, and all sensor-count models use the same outer partitions.

5. **Ten-sensor baseline.** The full ten-sensor model was added under the identical outer validation. Its pooled out-of-fold held-posture performance was 63.78% accuracy, 53.16% balanced accuracy, and 58.22% macro-F1. It outperformed the nested-selected triplet, which reached 49.35% balanced accuracy.

6. **Triplet claim.** The claim of a uniquely optimal triplet was removed. No triplet was selected in more than two of the 15 participant-by-outer-fold analyses, so S2-S5-S10 is no longer described as optimal.

7. **Participant- and posture-level performance.** We now report accuracy, balanced accuracy, macro-F1, and support for every participant, plus support and recall for every participant-posture combination. In the revised grouped analysis, pooled standing-straight recall is 77.97%; lower recall for sitting (28.57%) and left shoulder touch/twist (33.33%) is discussed explicitly.

8. **Transition errors.** Transition windows are defined as windows lying wholly within movement-to-target or movement-to-standing phases. The ten-sensor error rate was 36.22% for held-posture windows and 76.88% for transition windows. The discussion treats this as a quantified secondary result rather than a visual inference.

9. **Statistical analysis.** The ordinary one-way ANOVA and significance claims were removed. Figure 7 now shows descriptive participant-level trajectories, which is more appropriate for the repeated-measures feasibility sample of three participants.

10. **Sensor characterization.** We did not have independently fabricated T-shirt-sensor replicates for resistance-strain response, hysteresis, drift, cyclic repeatability, or attachment strength. The manuscript now states this limitation directly. SEM is described only as qualitative morphology of one representative interface, and adhesion or durability claims have been removed.

11. **ADC calibration and signal quality.** The Methods now give the nominal ADC-count-to-voltage and resistance equations, state that channel-specific ESP32 ADC calibration was not recorded, and define invalid/near-rail handling. S9 for S2 contained 1.86% near-saturation samples. Excluding S9 gave 52.77% balanced accuracy, close to the ten-sensor result of 53.16%, so the main comparison is not driven by that channel.

12. **Reproducibility details.** The manuscript now reports the garment size and fit, participant characteristics and eligibility criteria, software versions, exact recording-level baseline normalization, and whether protocol boundaries are required. Where historical details were not recorded, this is stated transparently: the conductive TPU manufacturer/product designation, exact garment fibre blend, and garment dimensions beyond the XL label.

13. **Distinction from the previous loose-garment paper.** The revision identifies the two directly supported differences: conductive TPU was deposited by fused-filament printing directly on the garment, and the present system uses ESP32 BLE acquisition rather than the earlier screen-printed/laboratory-DAQ architecture. Unsupported claims of lower cost, faster fabrication, and improved reliability were removed.

The reproducibility repository now contains the acquisition firmware, grouped nested-validation code, fold-level selections and predictions, participant- and posture-level metrics, ADC quality-control summaries, and scripts used to generate the revised analytical figures.
