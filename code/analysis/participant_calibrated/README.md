# Historical participant-calibrated window analysis

**Historical analysis, not the current manuscript workflow.** For the current 96.16% mean-accuracy analysis, approved code-and-aggregate release and manuscript Figures 9 and 10, use the [within-recording random-sample package](../within_recording_random_split/README.md).

## Earlier results

The previous ten-sensor window-based procedure reported **68.31% accuracy, 65.94% macro precision, 73.37% macro recall/balanced accuracy and 69.07% macro-F1** on 2,032 held-posture windows. These are exploratory participant-calibrated, pooled out-of-fold results from the three existing recordings, not independent-session or participant-independent validation.

The previous and current procedures use different features, normalization, eligibility and validation units. Their scores are not directly interchangeable. The historical numerical records are unchanged.

## Interpretation

The earlier analysis used stored repetition groups and training-fold preprocessing. Stored labels do not by themselves establish independence of complete physical cycles, including associated returns. The 2,032 windows are not 2,032 independent participants or trials. Repeated development on the same fixed-order recordings limits interpretation.

Figures produced by the earlier workflow are historical figures, not the current manuscript Figures 9 and 10. For current reproduction commands, selected settings, software versions and aggregate results, follow the [current package instructions](../within_recording_random_split/README.md#reproduction).
