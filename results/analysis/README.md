# Analysis results

The MATLAB scripts in `code/analysis/` write their generated tables and figures to this directory.

## Manuscript reference configuration

- classifier: bagged decision-tree ensemble (random forest)
- trees: 80
- minimum leaf size: 2
- class prior: uniform
- base random seed: 42 with deterministic offsets
- repetitions: one deterministic run
- test fractions: 20%, 30%, and 50%
- features per sensor: current value, slope, and rolling mean and standard deviation over 5 and 20 samples
- protocol samples: full protocol, including transitions

The manuscript's highest-ranked three-sensor subset was S2–S5–S10. Across the reported participant-by-split evaluations, it achieved 86.94% mean accuracy and 95.72% mean balanced accuracy. The representative S01 50% holdout achieved 81.3% accuracy and 93.5% balanced accuracy.

These are internal sample-level feasibility estimates. They are not independent-session or unseen-participant performance estimates because temporally adjacent samples and overlapping feature windows can occur in both partitions.

Run `make_accuracy_table_and_figure9_best_combination.m` from MATLAB to regenerate the classification tables and Figure 9. Run `make_median_curves_subjects_1_2_3.m` to regenerate the subject-level median-response outputs. Generated files are ignored by default so local reruns do not make the repository dirty.
