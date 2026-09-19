# Historical Figure 6 full-range rendering record

This directory preserves an earlier full-range rendering of Figure 6 from all three shared participant CSVs. The archived renderer includes red quality-control ticks and dots for isolated observations. Those display rules describe this archived version, not the current manuscript presentation. It is not an exact regeneration of the current displayed Figure 6. No measurements, normalization, classification results or source files are changed by this documentation update.

## Reproduce the archived rendering

Use the files in `data/processed` at input commit `899a984b25b5ff510d84a702cf7b74f8dc64f4b6`. The script checks their Git blob hashes before plotting. From the repository root, run:

```bash
python code/analysis/make_figure6_full_range.py --data-dir data/processed --out-dir results/figure6
```

The verified environment was Python 3.14.5, NumPy 2.4.6, pandas 3.0.3 and Matplotlib 3.10.9. See `Fig6_range_check.json` for the exact recorded environment and source hashes.

Outputs are `Fig6.png` (600 dpi), `Fig6_preview.png`, and `Fig6_range_check.json`. The archived output filename does not identify it as the current Overleaf asset. Do not replace the manuscript figure with this output without checking the intended display version.

## Archived display rules

- Columns correspond to P01, P02 and P03. Each contains the prompted posture index and Sensors S1–S10 over the entire recording.
- Published `dr_s1`–`dr_s10` values are used unchanged. No normalization recalculation, smoothing, resampling, downsampling or imputation is applied.
- Existing channel quality-control flags are retained: ADC counts at or below 5 or at or above 3900, or nonfinite normalized response/resistance, are masked. Red ticks show post-baseline masked sample times only; their vertical positions are not amplitudes. Missing initial-baseline normalized values remain blank.
- Lines break at masked values and host elapsed-time gaps greater than 0.25 s, without discarding either observation adjacent to a time gap. Isolated valid observations are dots so isolated peaks remain visible. These host-time breaks do not establish device sample loss.
- Each participant/channel panel uses its own linear vertical scale spanning all valid values and zero, with 10% padding (minimum 0.015). Amplitudes therefore require reading each panel's scale. Alternating shading distinguishes target blocks.

## Archived range verification

The audit covers 50,701 source rows across three recordings and 30 sensor panels. All valid values are retained exactly, all fall within the displayed limits, and source hashes remain unchanged after rendering. The range report separately records finite source extrema before quality control, valid extrema, masked counts and axis limits; quality masking must not be described as showing every raw value.

This historical plotting revision uses the published export pinned above. Its range verification applies to that rendering, not automatically to later display variants. Current classification uses the unchanged public ADC data through the [separate random-sample analysis](../../code/analysis/within_recording_random_split/README.md); these plotting rules are not classification preprocessing.
