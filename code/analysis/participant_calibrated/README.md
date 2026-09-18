# Participant-calibrated classification archive

[Download the complete analysis ZIP](participant_calibrated_analysis.zip) (18.4 MB). SHA-256: `1c56eee702683bff936e2e1941d5ab5cb44cde4589c3bc65b67da0e843f21959`.

The packaged code passed a relocated replay: 9,512 feature vectors, 32 metric groups, 75 split checks, 60 selection checks, 45 selected outer fits and 60 selected inner fits. All 9,512 prediction rows across the four procedures were verified. See [verification.json](verification.json). These computational checks do not constitute independent experimental validation.

This archive reproduces the updated ten-sensor T-shirt analysis: **68.31% accuracy, 65.94% macro precision, 73.37% macro recall/balanced accuracy and 69.07% macro-F1** on 2,032 held-posture windows. These are exploratory participant-calibrated, pooled out-of-fold results from three existing recordings, not independent-session or participant-independent validation. Repeated algorithm development on these recordings limits interpretation of the estimates.

## Download and setup

Download or clone the complete repository. Extract `participant_calibrated_analysis.zip` and enter its `participant_calibrated_analysis/` directory. The three unchanged input CSVs are reused from the repository's `data/processed/` directory; they are not duplicated in the ZIP. Python **3.14.5** was used for verification. Install the pinned analysis environment separately from the acquisition environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py prepare --repository /path/to/3d-printed-tpu-smart-tshirt
```

`prepare` checks every input against `INPUTS.json` before copying it into the analysis layout. It also verifies the byte-preserved scientific files against `FILES.json`. Original provenance manifests retain historical filesystem paths; the verifier resolves those paths inside the extracted archive, without accessing the original computer.

## Reproduce results and manuscript figures

```bash
# Recalculate all metric groups from saved predictions and recreate Figures 9 and 10:
python reproduce.py figures --output /path/to/new-figure-output

# Independent feature/metric/split/selection checks and selected-model refitting:
python reproduce.py verify --output /path/to/new-verification-output

# Optional: rerun the complete fixed temporal candidate search (960 inner fits):
python reproduce.py fit --output /path/to/new-search-output --jobs 4
```

Use new output directories. Figure and verification runs operate in temporary copies; the archived predictions, original source files and repository datasets are not overwritten. The complete search uses the archived working-procedure selections as its prespecified reference candidate, exactly as the reported analysis did. Earlier working-search code and search records are included for provenance.

## Scientific files

- `tshirt_temporal_test_20260918/PLAN.md`: fixed temporal-feature experiment plan.
- `tshirt_temporal_test_20260918/benchmark.py`: final candidate search, training-fold preprocessing, selection and outer fitting.
- Its `results/`: all outer predictions and probabilities, pooled/participant/class metrics, 15 inner-search records, selected settings and standing-score multipliers, feature matrices, history-source indices, split audits, versions and verification results.
- `tshirt_results_update_20260918/build_figures.py`: independently recomputes metrics and produces the manuscript confusion matrix and performance plots.
- `tshirt_joint_benchmark_20260918/`: working candidate, fitting utilities, plans and complete search records.
- `tshirt_algorithm_benchmark_20260918/`: source normalization, features, preprocessing and window definitions, with earlier results retained as development history.
- `tshirt_model_validation_20260918/validate.py`: sample-level partition-disjointness checks used by the final search.
- `tshirt_finetuning_20260918/`: preceding refinement code, plan and saved outputs referenced by the provenance chain.

Participant identifiers `S1`–`S3` in the analysis map to `P01`–`P03` in the manuscript and `subject_01.csv`–`subject_03.csv` in the repository. Sensor identifiers S1–S10 are a separate numbering system. Positions 4 and 5 mean contralateral shoulder touch with a torso twist toward the touched shoulder.

## Validation scope

Complete repetitions, including reference periods, stay together. Outer testing holds out one of five repetitions per participant; inner training-only validation selects candidate settings and the standing-score multiplier. Windows and their causal history cannot share raw measurements across train/test partitions. Imputation and scaling are fitted on each training partition. All ten sensors are used. Temporal features were selected in 5 of 15 outer folds; this does not establish that temporal features always improve performance.

The 2,032 windows are not 2,032 independent participants or trials. Known protocol boundaries are used, posture blocks were fixed-order, and no new recordings were collected for this analysis. Transition outputs are agreement with the prompted destination, not independently observed instantaneous posture. Older reduced-sensor results are secondary and must not be attributed to the updated full-array procedure. Hardware calibration, durability and adhesion were not newly established by this analysis.
