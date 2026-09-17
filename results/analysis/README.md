# Legacy exploratory analysis — superseded

This directory is the output location for the earlier MATLAB scripts in `code/analysis/`. These scripts and the results described below are retained for historical reference, not for current manuscript performance claims.

## Current manuscript analysis

Use [`../../code/analysis/nested_grouped_classification.py`](../../code/analysis/nested_grouped_classification.py) and the [grouped nested-validation results](../nested_grouped/README.md) for the current analysis and Figure 9. The current workflow uses 20 trees for inner sensor selection and 100 trees for outer testing. The ten-sensor baseline has pooled held-posture out-of-fold accuracy of 63.78% and balanced accuracy of 53.16%.

## Historical MATLAB configuration

- classifier: bagged decision-tree ensemble (random forest)
- trees: 80
- minimum leaf size: 2
- class prior: uniform
- base random seed: 42 with deterministic offsets
- repetitions: one deterministic run
- test fractions: 20%, 30%, and 50%
- features per sensor: current value, slope, and rolling mean and standard deviation over 5 and 20 samples
- protocol samples: full protocol, including transitions

In this superseded exploratory analysis, S2–S5–S10 was the highest-ranked three-sensor subset, with 86.94% mean accuracy and 95.72% mean balanced accuracy across the participant-by-split evaluations. The representative S01 50% holdout gave 81.3% accuracy and 93.5% balanced accuracy. These are historical numbers, not the current manuscript results, and do not establish a uniquely optimal triplet.

Random sample-level splitting allows temporally adjacent measurements and overlapping feature windows from one repetition to appear in both partitions. The historical estimates therefore must not be used as leakage-resistant validation, independent-session performance, or unseen-participant performance.

## Running the historical workflows

Run `make_accuracy_table_and_figure9_best_combination.m` in MATLAB only to execute the legacy classification workflow and its historical Figure-9-style plot. Run `make_median_curves_subjects_1_2_3.m` for the legacy median-response workflow. The latter also generates exploratory ordinary one-way ANOVA output, which is not used in the revised manuscript. Use the relevant historical repository version and inputs when reproducing historical results.

These MATLAB scripts write outputs to `results/analysis/`. For the current manuscript analysis, follow the [Python reproduction instructions](../nested_grouped/README.md#reproduction).
