# Current manuscript classification figures

`Fig9.png` pools 10,141 random-split test samples from the three participant-specific models. Its cells show counts and row-normalized percentages. `Fig10.png` shows participant metrics and arithmetic participant means, plus recall for all eight classes. All axes use the full 0-100% performance scale.

The headline mean accuracy is 96.16%, macro precision 96.83%, balanced accuracy/macro recall 95.34%, and macro-F1 96.06%. Pooled metrics differ slightly from the arithmetic participant means. Both are retained in `verified_metrics.json`.

Recreate the figures with the [current analysis package](../../code/analysis/within_recording_random_split/README.md). These are exploratory reused random-sample splits, not independent-session validation. The repetition-grouped check remains in the same analysis archive and the manuscript supplement. Figure 6 and source datasets are unchanged.
