function replaceBetween(source, start, end, replacement) {
  const i = source.indexOf(start);
  const j = source.indexOf(end, i + start.length);
  if (i < 0 || j < 0 || j <= i) {
    throw new Error(`Could not replace section from ${start} to ${end}`);
  }
  return source.slice(0, i) + replacement.trim() + "\n\n" + source.slice(j);
}

function replaceFigure(source, filename, replacement) {
  const token = `{figures/${filename}}`;
  const hit = source.indexOf(token);
  if (hit < 0) throw new Error(`Missing figure ${filename}`);
  const start = source.lastIndexOf("\\begin{figure}", hit);
  const endToken = "\\end{figure}";
  const end = source.indexOf(endToken, hit);
  if (start < 0 || end < 0) throw new Error(`Could not delimit figure ${filename}`);
  return source.slice(0, start) + replacement.trim() + "\n" + source.slice(end + endToken.length);
}

function sensorSection(sensorMap) {
  if (!Array.isArray(sensorMap) || sensorMap.length !== 10) {
    throw new Error("sensorMap must contain ten confirmed entries");
  }
  const prose = sensorMap.map((x, i) => `S${i + 1} (${x.side.toLowerCase()}, ${x.location.toLowerCase()})`).join(", ");
  const rows = sensorMap.map((x, i) => `        ${i + 1} & ${x.side} & ${x.location} \\\\`).join("\n");
  return String.raw`
\subsection*{Sensor arrangement on the T-shirt}

Ten printed TPU strain sensors were integrated into the loose-fitting garment at locations expected to deform during the prescribed upper-body movements. Right and left refer to the anatomical sides of the wearer. The channel labels were verified against the physical garment and wiring before analysis: ${prose}. Figure~\ref{fig:tshirt_sensor_placement}, Table~\ref{tab:sensor_locations}, the acquisition-channel order, and all channel-specific interpretations use this mapping.

\begin{table}[t]
    \centering
    \caption{Verified mapping between acquisition channel and garment location.}
    \label{tab:sensor_locations}
    \begin{tabular}{lll}
        \toprule
        Sensor number & Garment side & Sensor location \\
        \midrule
${rows}
        \bottomrule
    \end{tabular}
\end{table}

The distributed layout was intended to sample garment deformation across the chest, torso and back. Because the T-shirt was loose fitting, each channel measured local textile deformation rather than joint angle directly.`;
}

export function reviseMain(source, facts) {
  const required = ["conductiveProduct", "garmentComposition", "garmentDimensions", "participantsText", "sensorMap"];
  for (const key of required) if (!facts[key]) throw new Error(`Missing confirmed fact: ${key}`);

  let out = source;

  out = replaceBetween(out, "\\begin{abstract}", "\\end{abstract}", String.raw`
\begin{abstract}
Loose garments are attractive sensing platforms, but their signals are affected by fabric drape, folding, fit and local sensor--textile coupling. We developed a size-XL nylon T-shirt with ten fused-filament-printed conductive-TPU sensors, an ESP32 ten-channel readout and Bluetooth Low Energy transmission. Three participants completed five repetitions of eight upper-body positions. Scanning electron microscopy showed the morphology of a representative printed TPU--textile interface but was not used to infer adhesion or durability. For classification, complete posture repetitions were kept intact in participant-specific five-fold outer validation. Non-overlapping one-second windows were generated within protocol phases; imputation, standardization and sensor selection were fitted only on training data through inner repetition-grouped validation. On held-posture windows, the ten-sensor model achieved pooled out-of-fold accuracy of 63.8\%, balanced accuracy of 53.2\% and macro-F1 of 58.2\%. Nested-selected single-sensor, pair and triplet models reached balanced accuracies of 35.9\%, 45.2\% and 49.4\%, respectively; no triplet was selected consistently across folds. Ten-sensor error was 36.2\% during held postures and 76.9\% during transitions. These results support the feasibility of wireless posture-dependent sensing from directly printed TPU elements on a loose T-shirt, while also showing that sensor reduction, generalization and material reliability require substantially broader validation.`);

  out = out.replace(
    `The objective of this work was to evaluate whether a directly printed TPU sensor array on a loose T-shirt could produce posture-dependent signals and support classification of upper-body positions. The printed TPU--textile interface was first examined using scanning electron microscopy. The T-shirt was then tested on three participants during eight upper-body positions, including standing straight, arm raising, shoulder-touch-and-twist movements, both-arm raising, forward bending, and sitting. The resulting normalized resistance signals were analyzed using statistical testing, inter-sensor correlation, and machine-learning-based sensor-subset selection.\nThis work contributes to printed smart garments in three ways. First, it demonstrates direct fused-filament printing of TPU-based strain sensors onto a loose nylon T-shirt. Second, it integrates the printed sensors with a compact ESP32-based wireless readout system for ten-channel acquisition. Third, it evaluates the role of sensor placement and sensor combinations in posture classification, showing that a reduced subset of distributed sensors can capture useful deformation patterns from a loose garment. Together, these contributions support directly printed TPU sensors as a customizable route toward wireless textile-based motion-sensing garments.`,
    `The objective of this work was to evaluate whether a directly printed TPU sensor array on a loose T-shirt could produce posture-dependent signals and support classification of upper-body positions. The printed TPU--textile interface was examined qualitatively by scanning electron microscopy, and the T-shirt was tested on three participants during eight upper-body positions. Recording-baseline-normalized signals were assessed descriptively and by repetition-grouped, nested machine-learning validation.\nThis work contributes a distinct smart-garment prototype architecture comprising direct fused-filament deposition of TPU sensors on the garment and compact ten-channel ESP32 BLE acquisition. It also provides a leakage-resistant comparison of nested-selected single sensors, pairs and triplets with the complete array. The full array outperformed the reduced subsets, so the results are presented as a feasibility benchmark rather than evidence for an optimal reduced layout.`
  );

  out = replaceBetween(out, "\\subsection*{Materials}", "\\subsection*{Fabrication of TPU sensors}", String.raw`
\subsection*{Materials}

The piezoresistive element was printed from ${facts.conductiveProduct}. The non-conductive backing was white Luocute TPU (1.75~mm, Shore hardness 95A). The substrate was a size-XL white stretchable activewear T-shirt made from ${facts.garmentComposition}. Its physical dimensions were ${facts.garmentDimensions}. The garment was used as received, without washing, chemical or plasma treatment, or mechanical pre-stretching.

Copper-tape electrodes were approximately \SI{1}{\centi\metre} $\times$ \SI{1}{\centi\metre}, and insulated 30~AWG wires connected the printed elements to the readout circuit. The non-conductive TPU served as a compliant backing/interlayer. Adhesion strength was not quantified in this study.`);

  out = replaceBetween(out, "\\subsection*{Sensor arrangement on the T-shirt}", "\\subsection*{Electrical readout and wireless acquisition}", sensorSection(facts.sensorMap));

  out = replaceBetween(out, "\\subsection*{Electrical readout and wireless acquisition}", "\\subsection*{Experimental protocol}", String.raw`
\subsection*{Electrical readout and wireless acquisition}

Each printed sensor was measured by an independent voltage divider connected to an ESP32 development board. S1--S10 were connected to GPIO 36, 39, 34, 35, 32, 33, 25, 26, 27 and 14, respectively. For every channel, a nominal \SI{3.3}{\kilo\ohm} fixed resistor was connected between the \SI{3.3}{\volt} supply and the ADC node, and the TPU sensor was connected between that node and ground:
\[
\SI{3.3}{\volt}\rightarrow R_f\rightarrow V_{\mathrm{ADC},i}\rightarrow R_{s,i}\rightarrow\mathrm{GND}.
\]
The corrected topology is shown in Figure~\ref{fig:wireless_readout_setup}; the ten ADC nodes were not electrically joined.

The ESP32 ADC was configured for 12-bit output and 11-dB attenuation. Eight readings per channel, separated by \SI{250}{\micro\second}, were averaged and rounded at each sample. The firmware advertised as \texttt{TSHIRT\_01} and transmitted ten raw ADC counts at approximately \SI{20}{\hertz} through the Nordic UART Service BLE profile. Custom Python software using Bleak logged the records on a laptop.

For ADC count $N_i$, the nominal count-to-voltage and divider conversions were
\begin{equation}
V_{\mathrm{ADC},i}=3.3\frac{N_i}{4095},\qquad
R_{s,i}=R_f\frac{N_i}{4095-N_i}.
\label{eq:resistance_conversion}
\end{equation}
No channel-specific calibration of ESP32 ADC nonlinearity was recorded; absolute voltage and resistance are therefore nominal divider estimates rather than calibrated metrological measurements. All public resistance columns and the present reanalysis were calculated uniformly from the retained raw counts with $R_f=\SI{3.3}{\kilo\ohm}$. The normalized quantity used for classification was
\begin{equation}
\frac{\Delta R_i(t)}{R_{0,i}}=\frac{R_i(t)-R_{0,i}}{R_{0,i}}.
\label{eq:normalized_resistance}
\end{equation}

\begin{table}[t]
    \centering
    \caption{Electrical readout and wireless acquisition parameters.}
    \label{tab:readout_parameters}
    \begin{tabular}{ll}
        \toprule
        Parameter & Value \\
        \midrule
        Readout board & ESP32 development board \\
        Sensing channels & 10 independent voltage dividers \\
        Fixed resistor, $R_f$ & \SI{3.3}{\kilo\ohm}, nominal \\
        Supply & \SI{3.3}{\volt} \\
        ADC & 12 bit (0--4095 counts), 11-dB attenuation \\
        Averaging & 8 readings per channel \\
        Effective sampling rate & Approximately \SI{20}{\hertz} \\
        Wireless link & BLE, Nordic UART Service \\
        \bottomrule
    \end{tabular}
\end{table}`);

  out = replaceBetween(out, "\\subsection*{Participants}", "\\subsection*{Ethics approval and informed consent}", String.raw`
\subsection*{Participants}

${facts.participantsText} All participants completed the same fixed laboratory protocol while wearing the same size-XL garment. These fit characteristics are relevant because local drape and sensor loading can vary with the wearer. No clinical or diagnostic measurements were collected. Participant data were collected on 3 September 2026.`);

  out = replaceBetween(out, "\\subsection*{Data processing and normalization}", "\\subsection*{Statistical analysis}", String.raw`
\subsection*{Data processing and normalization}

Raw counts were converted using Eq.~\ref{eq:resistance_conversion}. For each participant and channel, $R_{0,i}$ was the median resistance during the recording's initial five-second standing-straight baseline. The same recording-level baseline was then used throughout that participant's recording. Thus, normalization required one initial calibration period and did not require advance knowledge of the later repetition boundaries. A constant change in the assumed fixed-resistor value scales both $R_i$ and $R_{0,i}$ equally and therefore cancels in $\Delta R/R_0$.

Counts at or near an ADC rail were flagged before analysis. Samples with $N_i\leq5$, $N_i\geq3900$, a non-finite divider estimate, or a missing normalized value were treated as invalid for that channel. No temporal smoothing was applied. For classification, invalid feature values were median-imputed using only the corresponding training fold. Protocol labels and timestamps recorded by the acquisition program synchronized electrical samples with the reference, movement and held-posture periods.`);

  out = replaceBetween(out, "\\subsection*{Statistical analysis}", "\\subsection*{Sensor optimization and classification analysis}", String.raw`
\subsection*{Descriptive analysis}

Given the feasibility sample of three participants and the repeated-measures design, participant-level summaries were prioritized over hypothesis testing. For each participant, sensor and posture, the median valid $\Delta R/R_0$ during held-posture samples was calculated and plotted directly. No one-way ANOVA or sensor-wise significance claim was retained because an ordinary one-way model would not account for within-participant dependence and ten separate sensor tests would require multiplicity control.

Pairwise Pearson coefficients were calculated descriptively within each posture to visualize shared variation between channels. Absolute correlation, $|r|$, was displayed, but it was not treated as evidence that a channel was independently informative or redundant.`);

  out = replaceBetween(out, "\\subsection*{Sensor optimization and classification analysis}", "\\subsection*{Software}", String.raw`
\subsection*{Sensor selection and classification analysis}

Posture classification was evaluated separately for each participant. A group was defined as one complete target-posture repetition, including its standing reference, movement to the target, target hold and return movement. Repetition number defined five outer folds, so no measurement from a held-out repetition appeared in training. Non-overlapping 20-sample windows (approximately 1~s) were constructed separately within each phase and group; windows never crossed a phase, repetition or validation boundary.

Seven features were calculated per sensor and window: mean, standard deviation, median, interquartile range, minimum, maximum and end-to-end slope. Held-posture windows formed the primary analysis. Each model was a random forest with 100 trees, minimum leaf size 2, square-root feature subsampling and balanced class weights. Within each outer-training set, missing-value imputation and feature standardization were fitted on training data only and then applied to held-out data.

Sensor reduction used nested sequential forward selection. Four inner folds, also grouped by repetition number, ranked each single sensor, then each pair containing the selected single sensor, and then each triplet extending the selected pair. Inner mean balanced accuracy was the ranking criterion. The selected single, pair and triplet were each evaluated once on the untouched outer fold. A prespecified model using all ten sensors was evaluated on the identical outer partitions. Selection frequency across the 15 participant-by-outer-fold analyses quantified stability; no subset selected after inspecting an outer test fold was reported.

Accuracy, balanced accuracy and macro-F1 were calculated from pooled out-of-fold held-window predictions and for each participant. Class support and recall were reported for each participant and posture. To quantify transition-related errors, the held-posture-trained models also predicted non-overlapping windows from movement-to-target and movement-to-standing phases; error rates were reported separately for held and transition periods. These are within-participant repetition-level estimates and do not measure performance for unseen wearers or independent sessions.`);

  out = replaceBetween(out, "\\subsection*{Software}", "\\section*{Results}", String.raw`
\subsection*{Software}

Acquisition used the public ESP32 firmware and custom Python/Bleak logger. The grouped reanalysis used Python 3.14.5, pandas 3.0.3, NumPy 2.4.6, scikit-learn 1.8.0 and Matplotlib 3.10.9. The exact code, seed, feature definitions, fold assignments, predictions and quality-control summaries are available at \href{https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt}{the public GitHub repository}. The earlier MATLAB exploratory script is retained only as a labelled legacy analysis and was not used for the revised performance claims.`);

  out = replaceBetween(out, "\\subsection*{Morphology of the printed TPU--textile interface}", "\\subsection*{Normalized sensor responses across participants}", String.raw`
\subsection*{Morphology of the printed TPU--textile interface}

Figure~\ref{fig:sem_micrograph} shows a representative TPU-on-nylon sample prepared under the garment printing conditions. The printed region covered the underlying fibrous topography, while yarn bundles remained visible at exposed openings and the cut edge. At higher magnification, the printed surface contained fused-filament striations and localized particulate features. These images describe surface morphology and apparent contact in one representative sample; they do not quantify adhesion, attachment strength, strain transfer or durability.`);

  out = replaceBetween(out, "\\subsection*{Normalized sensor responses across participants}", "\\subsection*{Position-dependent sensor response}", String.raw`
\subsection*{Normalized sensor responses across participants}

Figure~\ref{fig:normalized_sensor_responses} shows recording-baseline-normalized $\Delta R/R_0$ for all ten channels and three participants. The signals changed across posture blocks, but amplitudes, polarities and transient shapes differed between channels, repetitions and participants. Peaks and baseline shifts were also present. The traces therefore demonstrate posture-dependent garment signals under this protocol, not calibrated strain or repeatability of independently fabricated sensors.`);

  out = replaceBetween(out, "\\subsection*{Position-dependent sensor response}", "\\subsection*{Inter-sensor correlation across body positions}", String.raw`
\subsection*{Participant-level posture response}

Figure~\ref{fig:position_dependent_boxplots} presents the median held-posture response for every participant, channel and posture. Several channels show large posture-associated changes for one participant but smaller or differently signed changes for another, illustrating the influence of garment fit and deformation path. Because only three participants were studied, these plots are descriptive. They do not identify statistically significant or population-level position-sensitive channels.`);

  out = replaceBetween(out, "\\subsection*{Inter-sensor correlation across body positions}", "\\subsection*{Sensor optimization and posture classification}", String.raw`
\subsection*{Inter-sensor correlation across body positions}

The posture-stratified absolute correlation matrices in Figure~\ref{fig:position_wise_correlations} changed across positions. Some channel pairs shared stronger variation in particular postures, whereas others remained weakly correlated. These descriptive relationships motivated an explicit nested comparison of reduced subsets with the complete array; correlation alone was not used to choose sensors.`);

  out = replaceBetween(out, "\\subsection*{Sensor optimization and posture classification}", "\\subsection*{Temporal distribution of classification errors}", String.raw`
\subsection*{Grouped validation and sensor-count comparison}

Table~\ref{tab:classification_holdout} summarizes the pooled out-of-fold held-window predictions. Balanced accuracy increased from 35.9\% with the nested-selected single sensor to 45.2\% with a pair and 49.4\% with a triplet. The full ten-sensor baseline performed best, with 63.8\% accuracy, 53.2\% balanced accuracy and 58.2\% macro-F1. Sensor reduction therefore decreased performance in this analysis.

\begin{table}[t]
\centering
\caption{Pooled out-of-fold performance for held-posture windows. Sensor subsets were selected inside each outer-training fold.}
\label{tab:classification_holdout}
\begin{tabular}{lrrrr}
\toprule
Configuration & Accuracy & Balanced accuracy & Macro-F1 & Support \\
\midrule
Selected single & 43.60\% & 35.94\% & 35.55\% & 2032 \\
Selected pair & 50.30\% & 45.18\% & 45.04\% & 2032 \\
Selected triplet & 55.22\% & 49.35\% & 50.57\% & 2032 \\
All ten sensors & 63.78\% & 53.16\% & 58.22\% & 2032 \\
\bottomrule
\end{tabular}
\end{table}

No triplet dominated the inner selections. The most frequent triplet was selected in only 2 of 15 participant-by-outer-fold analyses, and several triplets shared that frequency (Supplementary Table~S2). Accordingly, neither S2--S5--S10 nor any other triplet is described as uniquely optimal.

\begin{table}[t]
\centering
\caption{Participant-specific pooled out-of-fold results for the ten-sensor model.}
\label{tab:participant_classification}
\begin{tabular}{lrrrr}
\toprule
Participant & Accuracy & Balanced accuracy & Macro-F1 & Support \\
\midrule
S1 & 66.03\% & 54.49\% & 59.36\% & 677 \\
S2 & 63.42\% & 52.78\% & 57.26\% & 678 \\
S3 & 61.89\% & 52.16\% & 57.00\% & 677 \\
\bottomrule
\end{tabular}
\end{table}`);

  out = replaceBetween(out, "\\subsection*{Temporal distribution of classification errors}", "\\section*{Discussion}", String.raw`
\subsection*{Class-level and transition-related errors}

For the ten-sensor model, pooled recalls were 78.0\% for standing straight, 60.1\% for left arm raise, 46.9\% for right arm raise, 33.3\% for left shoulder touch and twist, 53.7\% for right shoulder touch and twist, 50.3\% for both arms raise, 74.3\% for forward bend and 28.6\% for sitting. The high support and recall of the repeated standing reference contributed substantially to overall accuracy; the lower recalls for sitting and several arm/shoulder postures explain why balanced accuracy was only 53.2\%. Participant-by-posture support and recall are reported in Supplementary Table~S3.

Transition windows were defined as non-overlapping windows wholly contained in either movement-to-target or movement-to-standing phases. The ten-sensor model's pooled error rate was 36.2\% for held-posture windows and 76.9\% for transition windows. Figure~\ref{fig:classification_errors_confusion} reports the fold-level comparison, pooled confusion matrix, participant-by-posture recall and held-versus-transition errors. The transition result is secondary because transition windows were predicted by models trained on held postures and the protocol did not define separate movement classes.`);

  out = replaceBetween(out, "\\section*{Discussion}", "\\section*{Conclusion}", String.raw`
\section*{Discussion}

The directly printed T-shirt produced multichannel resistance patterns that varied with the prescribed upper-body positions, but the grouped analysis gives a more cautious estimate of posture discrimination than the earlier sample-level split. When complete repetitions were separated and sensor selection was nested, the full ten-sensor model reached 53.2\% balanced accuracy. The selected triplet reached 49.4\%, and its membership varied markedly across folds. The present data therefore do not support a uniquely optimal three-channel layout or a claim that three sensors preserve ten-sensor performance.

Class-level results show where performance was gained and lost. Standing straight and forward bend had pooled recalls of 78.0\% and 74.3\%, whereas sitting and left shoulder touch/twist reached only 28.6\% and 33.3\%. The repeated standing reference also represented about half of the held windows. Reporting accuracy alone would consequently overstate performance; balanced accuracy, macro-F1, class support and recall are necessary for interpretation.

Transitions were quantitatively more difficult than held postures. Their 76.9\% error rate is consistent with a loose garment continuing to drape and fold while the participant moves, but the analysis does not establish the physical cause of each error. A future model should define transition classes explicitly or use sequence models and independent sessions designed around dynamic movement.

The participant-level response plots also show substantial between-wearer variation. All models here were participant specific, and all participants wore the same size-XL garment. These results should therefore not be interpreted as subject-independent recognition. Larger studies should stratify garment size and fit, randomize posture order, repeat donning and doffing, and evaluate independent days and unseen participants.

The electrical audit resolved the divider orientation and fixed-resistor label. The revised circuit has a separate ADC node for every channel, with the fixed resistor connected to 3.3~V and the TPU element to ground. Because the ESP32 ADC was not calibrated channel by channel, the absolute resistance values are nominal estimates. The classification relied on $\Delta R/R_0$, for which a common fixed-resistor scaling factor cancels. S9 in S2 contained 1.86\% near-saturation readings; excluding S9 produced a similar balanced accuracy of 52.8\%, so the principal sensor-count comparison was not driven by that channel.

SEM documented the morphology of one representative printed interface but did not measure adhesion or durability. No independent T-shirt-sensor series was characterized for resistance--strain response, hysteresis, drift, cyclic repeatability or attachment strength. The conclusions are therefore limited to prototype fabrication and short laboratory posture recordings. Quantitative electromechanical and attachment testing across independently fabricated sensors, together with washing and wear tests, is needed before reliability claims can be made.

Relative to the previous loose-garment work, the present study changes two concrete system elements: conductive TPU was deposited by fused-filament printing directly on the garment, and signals were acquired through an ESP32 BLE system rather than the earlier screen-printed/laboratory-DAQ implementation \cite{elgendi2026optimized}. These differences establish a distinct prototype architecture; they do not by themselves demonstrate lower cost, faster fabrication or improved reliability.

Overall, the work provides a reproducible feasibility dataset and identifies the limits of the current design. The full array outperformed reduced subsets under leakage-resistant validation, performance varied by posture and participant, and transition recognition remained weak. These findings define specific engineering and validation targets for the next iteration rather than supporting deployment-level claims.`);

  out = replaceBetween(out, "\\section*{Conclusion}", "\\section*{Data Availability}", String.raw`
\section*{Conclusion}

A loose size-XL T-shirt with ten directly printed TPU sensing elements and ESP32 BLE acquisition generated posture-dependent signals in three participants. Under repetition-grouped nested validation, the ten-sensor model achieved 63.8\% accuracy, 53.2\% balanced accuracy and 58.2\% macro-F1 on held-posture windows and outperformed the nested-selected reduced subsets. No triplet was selected consistently. Errors were higher during transitions, and class recall ranged from 28.6\% to 78.0\%. The study supports prototype feasibility but not a uniquely optimal sensor subset, subject-independent classification, calibrated strain measurement, adhesion strength or durability. Those questions require larger independent-session studies and quantitative characterization across separately fabricated sensors.`);

  out = replaceFigure(out, "Fig3.png", String.raw`
\begin{figure}[t]
    \centering
    \includegraphics[width=0.98\linewidth]{figures/Fig3.png}
    \caption{Corrected readout and wireless acquisition architecture. (a) Signal path from ten printed TPU sensors through independent voltage dividers and the ESP32 to BLE logging. (b) Each channel uses the topology \SI{3.3}{\volt} $\rightarrow R_f\rightarrow$ independent ADC node $\rightarrow R_s\rightarrow$ ground, with nominal $R_f=\SI{3.3}{\kilo\ohm}$. (c) GPIO mapping and nominal count-based voltage and resistance equations.}
    \label{fig:wireless_readout_setup}
\end{figure}`);

  out = replaceFigure(out, "Fig5.png", String.raw`
\begin{figure}[t]
    \centering
    \includegraphics[width=0.95\linewidth]{figures/Fig5.png}
    \caption{Qualitative SEM morphology of a representative printed TPU--textile interface. (a) Overview of the printed region and exposed nylon yarns at the sample edge. (b) Higher-magnification image acquired at $620\times$ with a $200~\mu\mathrm{m}$ scale bar, showing fused-filament surface striations and local openings. These images were not used to quantify adhesion, attachment strength or durability.}
    \label{fig:sem_micrograph}
\end{figure}`);

  out = replaceFigure(out, "Fig7.png", String.raw`
\begin{figure}[p]
    \centering
    \includegraphics[width=0.98\linewidth]{figures/Fig7.png}
    \caption{Descriptive participant-level held-posture responses. Each panel represents one channel; markers show the median valid recording-baseline-normalized $\Delta R/R_0$ for S1, S2 and S3 at Positions 1--8. Lines connect each participant's values only to aid visual comparison. No confidence interval or inferential test is implied.}
    \label{fig:position_dependent_boxplots}
\end{figure}`);

  out = replaceFigure(out, "Fig9.png", String.raw`
\begin{figure}[p]
    \centering
    \includegraphics[width=0.98\linewidth]{figures/Fig9.png}
    \caption{Repetition-grouped nested-validation results. (a) Outer-fold balanced accuracy for nested-selected single sensors, pairs and triplets and the full ten-sensor baseline; each point is one participant-by-outer-fold result and the horizontal line is the mean. (b) Row-normalized pooled out-of-fold confusion matrix for the ten-sensor model on held-posture windows. (c) Ten-sensor recall by participant and posture. (d) Participant-specific error rates for held-posture and transition windows. Sensor selection, imputation and standardization were performed using training data only.}
    \label{fig:classification_errors_confusion}
\end{figure}`);

  out = out.replace(/normalized resistance changes and local baseline correction/g, "recording-baseline-normalized resistance changes");
  out = out.replace(/local baseline correction and multi-channel classification/g, "recording-level baseline normalization and multi-channel classification");
  out = out.replace(/a low-cost and customizable route toward/g, "a route toward");
  out = out.replace(/backing and adhesion layer/g, "backing\/interlayer");

  const forbidden = ["86.94", "95.72", "81.3\\%", "93.5\\%", "sample-level holdout values", "statistically significant sensors"];
  for (const term of forbidden) if (out.includes(term)) throw new Error(`Outdated term remains in main manuscript: ${term}`);
  return out;
}

export function reviseSupplement(source) {
  const headerEnd = source.indexOf("\\section*{Supplementary Note S1:");
  const end = source.lastIndexOf("\\end{document}");
  if (headerEnd < 0 || end < 0) throw new Error("Could not delimit supplementary body");
  const body = String.raw`
\section*{Supplementary Note S1: Public data organization}

The public archive contains one de-identified CSV file per participant: \texttt{subject\_01.csv} (16,900 rows), \texttt{subject\_02.csv} (16,900 rows) and \texttt{subject\_03.csv} (16,901 rows). Each row contains elapsed time, protocol and phase labels, raw ten-channel ADC counts, nominal resistance values, recording-baseline-normalized responses and ADC quality-control flags. Direct identifiers, the participant identity key, consent records, device/network addresses and absolute Unix timestamps are excluded.

All three recordings were collected on 3 September 2026. An incorrect acquisition-computer calendar produced the June dates in the source workbooks; the public copies apply a constant whole-day correction while preserving time of day, fractional seconds, relative sample timing, labels and sensor measurements. The audit trail is in \texttt{docs/date\_correction\_log.md}.

\section*{Supplementary Note S2: Reproducibility files}

The reproducibility package is available at \href{https://github.com/poojasrinivas1304/3d-printed-tpu-smart-tshirt}{GitHub}. Table~\ref{tab:supp_code} lists the primary files. The legacy MATLAB sample-level holdout script is retained for audit history but is not used for revised manuscript performance claims.

\begin{table}[htbp]
\centering
\caption{Principal acquisition, firmware and analysis files.}
\label{tab:supp_code}
\small
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{0.42\textwidth}Y@{}}
\toprule
File & Purpose \\
\midrule
\path{hardware/esp32_ble/TSHIRT_01.ino} & Ten-channel ESP32 BLE firmware; transmits raw ADC records at approximately 20~Hz. \\
\path{code/acquisition/tshirt_ble_protocol.py} & BLE acquisition, protocol labels, nominal resistance conversion, normalization, QC flags and logging. \\
\path{code/analysis/nested_grouped_classification.py} & Primary repetition-grouped nested validation, sensor selection, ten-sensor baseline, transition analysis and ADC QC. \\
\path{code/analysis/make_figure7_participant_responses.py} & Descriptive participant-level posture-response figure. \\
\path{code/analysis/make_figure3_hardware_schematic.py} & Corrected independent-divider hardware schematic. \\
\bottomrule
\end{tabularx}
\end{table}

\section*{Supplementary Note S3: Classification configuration}

Each participant contributed five repetitions of each of the eight posture classes. A validation group comprised one complete target-posture repetition, including its associated standing-reference and movement phases. Repetition number defined the five outer folds. All phases from a held-out repetition were therefore excluded from training.

Non-overlapping 20-sample windows were constructed within phase boundaries. Seven features were calculated per sensor: mean, standard deviation, median, interquartile range, minimum, maximum and end-to-end slope. Held-posture windows were used for the primary classification. Transition windows were evaluated secondarily using the held-posture-trained models.

Sensor selection was nested inside each outer training set. Four inner folds, grouped by repetition number, ranked a single sensor, then pairs extending that sensor, and then triplets extending the selected pair. Missing-value imputation and standardization were fitted independently in each training fold. Random forests used balanced class weights, square-root feature subsampling, minimum leaf size 2, 20 trees for inner ranking and 100 trees for outer evaluation. The random seed was 42 with deterministic fold offsets.

\begin{table}[htbp]
\centering
\caption{Selected-triplet stability across the 15 participant-by-outer-fold analyses. No triplet was selected in more than two analyses.}
\label{tab:supp_stability}
\begin{tabular}{lr}
\toprule
Selected triplet & Count (of 15) \\
\midrule
S2--S3--S8 & 2 \\
S2--S7--S8 & 2 \\
S3--S6--S8 & 2 \\
S4--S7--S8 & 2 \\
All other selected triplets & 1 each \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[p]
\centering
\caption{Ten-sensor out-of-fold class support and recall for every participant and posture.}
\label{tab:supp_posture}
\small
\begin{tabular}{llrr}
\toprule
Participant & Posture & Support & Recall \\
\midrule
S1 & Standing straight & 337 & 81.60\% \\
S1 & Left arm raise & 49 & 57.14\% \\
S1 & Right arm raise & 47 & 53.19\% \\
S1 & Left shoulder touch and twist & 49 & 38.78\% \\
S1 & Right shoulder touch and twist & 49 & 57.14\% \\
S1 & Both arms raise & 50 & 46.00\% \\
S1 & Forward bend & 48 & 77.08\% \\
S1 & Sitting & 48 & 25.00\% \\
S2 & Standing straight & 341 & 77.42\% \\
S2 & Left arm raise & 47 & 72.34\% \\
S2 & Right arm raise & 49 & 44.90\% \\
S2 & Left shoulder touch and twist & 47 & 8.51\% \\
S2 & Right shoulder touch and twist & 49 & 63.27\% \\
S2 & Both arms raise & 48 & 66.67\% \\
S2 & Forward bend & 48 & 68.75\% \\
S2 & Sitting & 49 & 20.41\% \\
S3 & Standing straight & 339 & 74.93\% \\
S3 & Left arm raise & 47 & 51.06\% \\
S3 & Right arm raise & 47 & 42.55\% \\
S3 & Left shoulder touch and twist & 48 & 52.08\% \\
S3 & Right shoulder touch and twist & 49 & 40.82\% \\
S3 & Both arms raise & 49 & 38.78\% \\
S3 & Forward bend & 48 & 77.08\% \\
S3 & Sitting & 50 & 40.00\% \\
\bottomrule
\end{tabular}
\end{table}

\section*{Supplementary Note S4: ADC quality control}

S9 for S2 was the only participant-channel combination with more than 1\% near-saturation samples: 315 of 16,900 samples (1.86\%) were at or above 3900 counts, all at 4095. These samples produced non-finite nominal resistance values and were treated as missing. Training-fold median imputation was used only after partitioning. A sensitivity model excluding S9 yielded pooled held-window accuracy of 62.75\%, balanced accuracy of 52.77\% and macro-F1 of 57.46\%, similar to the ten-sensor model (63.78\%, 53.16\% and 58.22\%).

\end{document}
`;
  return source.slice(0, headerEnd) + body.trimStart();
}
