# Within-recording random-sample classification

The participant-specific ten-sensor procedure achieved **96.16% mean accuracy, 96.83% macro precision, 95.34% macro recall/balanced accuracy and 96.06% macro-F1** across three participants. These are arithmetic participant means from reused stratified 80/20 random-sample splits, not pooled out-of-fold window scores or independent-session validation. The 10,141 test samples come from 50,701 unchanged source rows.

Three-fold training-only selection considered 13 fixed candidates. All selected random-split classifiers were 300-tree Extra Trees models. P01 used ten standardized ADC channels plus 45 contemporaneous pairwise differences; P02 and P03 used the ten standardized channels. Scaling was fitted within each training partition. All eight labels and all phases, including initial baseline and transitions, were retained. No quality-control masks, imputation, windows, smoothing, abstention or label changes were applied in this analysis. Descriptive normalized-resistance plots use separate processing.

## Evaluation scope

Random splitting shares recorded repetitions between training and testing; on average 95.76% of test samples have an immediately adjacent training sample. The recordings and partitions had already been inspected during development, so this is not an untouched prospective test.

The same candidate-selection procedure with nominal repetitions held out achieved **46.06% mean accuracy, 45.08% macro precision, 53.47% balanced accuracy and 48.32% macro-F1**. It selected different classifiers, not the same fitted Extra Trees model tested again. Stored group boundaries do not guarantee independent complete physical cycles. Neither evaluation establishes new-session or unseen-wearer performance. Transition labels identify prompted destinations, not independently observed instantaneous posture.

The matched ten-sensor RF100 random-split comparator achieved 94.77% mean accuracy. Earlier 2,032-window analyses use different features, eligibility and validation units and remain in the previous archive; their scores are not directly interchangeable.

## Reproduction

Download and extract `code_and_aggregate_results.zip`, then enter the extracted directory. The package contains code, settings, input checksums and aggregate results only. Python 3.14.5 and the versions pinned in `requirements.txt` were used.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py selected --repository /path/to/3d-printed-tpu-smart-tshirt --output /path/to/new-selected-run
```

This verifies the three public CSV hashes, copies inputs into a new local work directory, regenerates the deterministic random splits from their seeds, refits the three selected models, verifies their aggregate metrics and confusion counts, and generates Figures 9 and 10. It verifies the published selected configurations, not the entire model-selection search. Original source data are unchanged.

To reproduce the complete fixed selection procedure, both validation designs and verification:

```bash
python reproduce.py full --repository /path/to/3d-printed-tpu-smart-tshirt --output /path/to/new-full-run --workers 4
```

The complete run performs 12 reference-model dependency fits followed by 897 inner and 54 outer fits. It takes substantially longer. Individual predictions, row indices and fitted models are generated locally; they are not distributed in this release. Choose a new output directory for each run. Computational reproduction does not constitute independent experimental validation.

## Package contents

- Original fitting, verification and dependency source files, fixed plans, portable runner and figure generator.
- `aggregate/metrics.csv`: participant and pooled results; `participant_mean_metrics.csv`: arithmetic participant means.
- `aggregate/per_class_metrics.csv`: support, precision, recall and F1 for every class.
- `aggregate/selected_models.json`, `selected_settings.csv`, `selections.json`: model settings, seeds and aggregate selection scores.
- `aggregate/split_hashes.json`, `split_diagnostics.csv`: deterministic split checksums and aggregate temporal-proximity diagnostics, without row indices.
- `aggregate/manifest.json`: candidate pool, versions, fit counts and source hashes.
- `aggregate/verified_metrics.json`: participant and pooled confusion counts and figure metrics.
- `INPUTS.json`, `FILES.json`, `RELEASE_FILES.json`: input, package and release checksums.

Data identifiers S01-S03 correspond to manuscript participants P01-P03, distinct from sensor channels S1-S10. Positions 4 and 5 retain the confirmed contralateral shoulder-touch and torso-twist definitions. Historical plans describe the computations at the time they were run. No new data collection, calibration or sensor-characterization experiment is implied.
