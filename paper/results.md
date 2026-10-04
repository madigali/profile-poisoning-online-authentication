# 4. Results

## 4.1. Reference-Operating-Point Poisoning Effect of Blind EMA

Under the HMOG boundary attack at \(K=8\), post-poison ASR was 22.92% for Frozen and 53.96% for Blind EMA, a Blind-minus-Frozen increase of +31.04 percentage points. After averaging repeats within each fold and victim and then folds within victim, the paired subject-bootstrap 95% CI was [+26.95, +35.20] across 100 victims. The analysis contained 500 contributing fold-victim units and 49,889 eligible fold-victim-repeat paths; 111 of 50,000 possible paths lacked eight initially accepted boundary candidates. Blind ASR increased monotonically across the nested boundary budgets: 22.92%, 27.50%, 33.68%, 44.31%, and 53.96% at \(K=0,1,2,4,8\), respectively. The random attack produced a smaller increase over the same budgets, from 22.92% at \(K=0\) to 23.38%, 23.88%, 25.09%, and 27.55%. The non-primary budgets and random comparisons were exploratory. These attack-budget results are shown in Fig. [POISONING] and summarized in Table [MAIN_RESULTS].

The 22.92% Frozen value is the baseline held-out impostor acceptance at the validation-calibrated, approximately equal-error operating point. The comparison establishes additional acceptance caused by Blind adaptation under the tested protocol; it does not establish that the underlying operating point meets deployment-grade security requirements.

## 4.2. Guarded Update Authorization at the Reference Operating Point

At boundary \(K=8\), post-poison ASR was 22.92% for Frozen, 53.96% for Blind EMA, and 22.93% for Guarded EMA with \(\lambda=0.25\). Blind EMA incorporated all presented boundary poisons (MUR 100.00%), whereas Guarded EMA incorporated 1.63%. Guarded \(\lambda=0\) reproduced Blind EMA in the frozen consistency check. Guarded returning ASR near Frozen indicates suppression of the additional Blind poisoning amplification; it does not make the high-baseline operating point secure.

The complete lambda sweep was exploratory. At boundary \(K=8\), MUR decreased from 100.00% at \(\lambda=0\) to 0.13% at \(\lambda=1\), while genuine update availability in the separate replay decreased from 85.96% to 41.78%. The carried-forward \(\lambda=0.25\) result was therefore reported as a fixed security comparison rather than as a universally optimal setting (Fig. [POISONING]; Table [MAIN_RESULTS]).

## 4.3. Operating-Point Dependence of Poisoning and Update Gating

### Calibration and held-out Frozen performance

Table [OP-A] separates calibration outcomes from full structurally valid held-out Frozen performance. The nominal targets constrained pooled calibration-impostor observations; they were not held-out FAR guarantees. At the nominal-1% condition, achieved mean calibration FAR was 0.91% on HMOG and 0.79% on McGill, whereas held-out FAR was 1.04% and 2.14%, respectively. The stricter conditions also had high held-out FRR: 80.79% on HMOG and 90.25% on McGill. These full-cohort values are not the baselines for the conditional boundary effects below.

| Dataset | Condition | Achieved calibration FAR | Full held-out Frozen FAR | Full held-out Frozen FRR | Cohort |
|---|---:|---:|---:|---:|---|
| HMOG | Reference (approximate EER) | 23.01% | 22.92% | 24.95% | 500 calibration profiles; 100 held-out victims |
| HMOG | Nominal 5% calibration FAR | 4.93% | 5.07% | 57.88% | 500 calibration profiles; 100 held-out victims |
| HMOG | Nominal 1% calibration FAR | 0.91% | 1.04% | 80.79% | 500 calibration profiles; 100 held-out victims |
| McGill | Reference (minimum HTER) | 6.89% | 12.20% | 78.81% | 20 calibration profiles; 20 held-out victims |
| McGill | Nominal 5% calibration FAR | 3.66% | 7.37% | 82.43% | 20 calibration profiles; 20 held-out victims |
| McGill | Nominal 1% calibration FAR | 0.79% | 2.14% | 90.25% | 20 calibration profiles; 20 held-out victims |

**Table [OP-A].** Calibration FAR and full-cohort held-out Frozen performance. Calibration values are unweighted means across claimant profiles of profile-specific pooled-observation rates. Held-out values use all structurally valid random-\(K=0\) paths and hierarchical victim-macro aggregation. They are not conditional boundary-attack baselines.

### Conditional boundary effects

The boundary-\(K=8\) effect depended strongly on the recalibrated operating point (Table [OP-B]; Fig. [OPERATING_POINT_EFFECTS]). On HMOG, Blind-minus-Frozen post-poison ASR was +31.04 percentage points at reference, +2.49 points at nominal 5%, and −0.447 points at nominal 1%. On McGill, the corresponding effects were +19.72, +0.20, and −0.354 points; the nominal-5% interval included zero. Guarded-minus-Blind was strongly negative at the reference points, smaller at nominal 5%, and near zero at nominal 1%. These rows are paired within an operating point, but they are not strictly paired cross-target effects because recalibration changed \(\tau_0\), claimant-specific \(k\), selected boundary candidates, and feasible paths.

| Dataset | Condition | Blind EMA − Frozen ASR, pp [95% CI] | Guarded EMA − Blind EMA ASR, pp [95% CI] | Eligible paths | Victims | Victim-fold units |
|---|---:|---:|---:|---:|---:|---:|
| HMOG | Reference | +31.04 [+26.97, +35.11] | −31.02 [−35.15, −26.98] | 49,889 / 50,000 | 100 | 500 |
| HMOG | Nominal 5% | +2.49 [+0.95, +4.38] | −3.09 [−4.91, −1.61] | 49,753 / 50,000 | 100 | 500 |
| HMOG | Nominal 1% | −0.447 [−0.502, −0.393] | −0.009 [−0.020, −0.001] | 9,088 / 50,000 | 100 | 302 |
| McGill | Reference | +19.72 [+5.50, +37.24] | −19.62 [−36.77, −5.66] | 1,456 / 2,000 | 18 | — |
| McGill | Nominal 5% | +0.20 [−0.05, +0.53] | −0.26 [−0.58, −0.03] | 1,369 / 2,000 | 18 | — |
| McGill | Nominal 1% | −0.354 [−0.552, −0.186] | 0.000 [0.000, 0.000] | 1,001 / 2,000 | 17 | — |

**Table [OP-B].** Conditional boundary-\(K=8\) paired post-poison ASR effects. Each row uses its own operating-point-specific common \(K=8\)-feasible cohort and a 10,000-draw paired victim bootstrap. Three-decimal precision is retained for near-zero nominal-1% effects. Historical reference sections retain their original authoritative intervals; the reference rows here use the sensitivity package's deterministic bootstrap streams. The reproduced victim effects and point estimates were the same, while percentile limits differed slightly because of Monte Carlo resampling.

For the primary sensitivity condition—HMOG nominal 1%, boundary \(K=8\)—the victim-by-impostor-source robustness interval was −0.447 points [−0.515, −0.383] for Blind minus Frozen and −0.009 points [−0.022, −0.001] for Guarded minus Blind. This secondary bootstrap covered 100 victims, 9,088 paths, and 100 observed impostor sources only in this condition; it did not include model-training or population uncertainty.

### Post-poison genuine rejection on the same cohort

On the 9,088-path HMOG nominal-1% boundary cohort, Frozen post-ASR/FRR/HTER were 0.826%/80.18%/40.50%, whereas Blind EMA values were 0.379%/87.07%/43.73%. Blind-minus-Frozen FRR was +6.89 percentage points (95% CI [+5.63, +8.27]), and HTER was +3.22 points (95% CI [+2.59, +3.91]). Thus lower post-poison ASR did not imply harmless profile updates: genuine rejection increased on the same calibrated and eligibility-matched cohort. This was not a separately designed availability or denial-of-service attack.

### Feasibility and gate activity

Strict calibration reduced boundary feasibility. HMOG nominal 1% retained 9,088 of 50,000 planned \(K=8\) paths, spanning 100 victims but only 302 of 500 victim-fold combinations. McGill retained 1,001 of 2,000 paths across 17 victims. Missing paths lacked eight initially accepted candidates; they were excluded rather than assigned ASR zero.

The original enrollment-anchored gate also became less frequently restrictive. Among all Guarded boundary-\(K=8\) poisoning states, the effective gate exceeded authentication in 19.22% of 72,704 HMOG nominal-1% states and 13.49% of 8,008 McGill states; \(\tau_{\mathrm{auth}}\geq\mu_{\mathrm{enroll}}\) held in 80.78% and 86.51% of those states. Separately, initial \(k<0\) occurred in 88.6% of all 500 HMOG claimant-fold profiles and 75.0% of all 20 McGill profiles. The latter are all-profile initialization denominators, not eligibility-conditioned attack-state fractions, and the sign of \(k\) alone does not identify the cause of each outcome. On McGill nominal 1%, Blind and Guarded had the same victim-macro post-ASR estimate, but MUR was 69.36% and 62.32%, respectively; equal aggregate ASR therefore did not imply identical state trajectories.

## 4.4. Guarded EMA Does Not Preserve Clean-Drift FRR Utility

In the primary claimant-only \(D=2\) HMOG scenario, Frozen late FRR/FAR/HTER were 32.53%/22.86%/27.70%. Blind EMA yielded 32.20%/23.80%/28.00%, and Guarded EMA yielded 34.60%/21.73%/28.16% (Fig. [TRADEOFF]).

Relative to Frozen, Blind EMA had a late-FRR gain of +0.33 percentage points (95% CI [−1.20, +1.93]), a late-FAR change of +0.93 points (95% CI [−0.58, +2.64]), and an HTER gain of −0.30 points (95% CI [−1.02, +0.40]). Guarded EMA had a late-FRR gain of −2.07 points (95% CI [−3.53, −0.63]), a late-FAR change of −1.14 points (95% CI [−2.29, +0.12]), and an HTER gain of −0.46 points (95% CI [−1.16, +0.21]). Thus, the Guarded point estimate had lower late FAR but higher late FRR than Frozen; its prespecified clean-drift FRR utility was not positive.

## 4.5. Oracle-All-Genuine Isolates Feedback Censoring

Oracle-all-genuine reduced claimant-only late FRR relative to Frozen at every HMOG drift level. Late-FRR gains were +4.73 percentage points at \(D=0\) (95% CI [+3.17, +6.33]), +5.10 points at \(D=1\) (95% CI [+3.40, +6.80]), and +6.60 points at \(D=2\) (95% CI [+4.90, +8.40]).

The corresponding late-FAR changes were +5.51 points (95% CI [+3.79, +7.40]), +5.67 points (95% CI [+3.85, +7.71]), and +6.08 points (95% CI [+4.20, +8.16]). HTER gains remained small: −0.39 points at \(D=0\) (95% CI [−1.22, +0.42]), −0.28 points at \(D=1\) (95% CI [−1.26, +0.65]), and +0.26 points at \(D=2\) (95% CI [−0.59, +1.09]). Each HTER interval included zero.

The Oracle-all effect was already present at \(D=0\): late FRR was 4.73 percentage points lower than Frozen while late FAR was 5.51 points higher. Thus, part of the Oracle contrast reflects movement of the operating point when all genuine observations are allowed to lower the profile, rather than recovery uniquely attributable to synthetic drift.

The claimant-only \(D=2\) trajectories also differed in direction. Across the five retained checkpoints, the Guarded profile mean and threshold moved upward, while both Oracle-all quantities moved downward. Guarded update rate decreased from 63.47% at the first checkpoint to 51.68% at the fifth; Oracle-all update rate remained 100%. These trajectories are shown in Fig. [TRAJECTORY]. Oracle-all changed genuine tracking in this label-aware diagnostic while incurring a higher FAR; it was not evaluated as a deployable method or a formally optimal adaptation path.

## 4.6. Supporting Recovery and State Probes

In claimant-only \(D=2\), TQ-EMA v1 had a paired late-FRR gain of −0.90 percentage points (95% CI [−1.80, 0.00]), so its prespecified recovery criterion was not met. Its late-FAR change was −1.94 points (95% CI [−2.46, −1.43]), and HTER gain was +0.52 points (95% CI [+0.10, +0.94]). The event audit recorded 1,404 trusted updates and 49 confirmed recovery updates. TQ-EMA v1 therefore remained on the lower-FAR, higher-FRR side of Frozen in Fig. [TRADEOFF] and was stopped.

TQ-EMA v2 then failed its fail-closed validation rule because fold 4 had no configuration satisfying both safety constraints. No Adaptive Quantile \(\rho\) was feasible in all folds. For both branches, outer test scores were not loaded and no outer estimates exist. Detailed validation diagnostics and the complete TQ/Quantile specifications are reported in Supplementary Results and Supplementary Methods; Table [MAIN_RESULTS] retains their protocol status without presenting validation summaries as outer performance.

## 4.7. External Replication on McGill Gait

The fixed Day-1 McGill classifier attained 58.12% validation top-1 accuracy and passed the prespecified 20% viability gate before Day 2 was loaded.

Under the Day-2 boundary attack at \(K=8\), held-out ASR was 12.37% for Frozen, 32.09% for Blind EMA, and 12.48% for Guarded EMA. The paired Blind-minus-Frozen effect was +19.72 percentage points (95% CI [+5.58, +37.34]), and the Guarded-minus-Blind effect was −19.62 points (95% CI [−37.17, −5.60]). Blind MUR was 100.00%, whereas Guarded MUR was 32.22%; the paired Guarded-minus-Blind MUR difference was −67.78 points (95% CI [−84.30, −49.47]). Boundary \(K=8\) retained 1,456 of 2,000 possible victim-repeat paths across 18 victims; 544 paths lacked eight initially accepted boundary candidates and were recorded as feasibility exclusions. The boundary \(K=0\) baseline used the same maximum-budget-feasible cohort. Random selection retained all 2,000 paths across all 20 subjects.

The 12.37% Frozen boundary baseline was produced by the fixed Day-1 validation-calibrated minimum-HTER threshold. As in HMOG, Guarded returning ASR near this baseline indicates suppression of additional poisoning amplification, not deployment security at a prespecified low-FAR target.

The random \(K=8\) effect was smaller. Blind-minus-Frozen ASR was +1.51 points across 20 subjects, and its 95% CI [−0.09, +4.43] included zero. The poisoning results are shown in Fig. [MCGILL_POISONING] and Table [MCGILL].

For the Day-2 temporal analysis, Frozen late FRR/FAR were 78.00%/11.46%, Guarded values were 81.00%/10.29%, and Oracle-all values were 12.75%/75.05%. The corresponding late HTER values were 44.73%, 45.64%, and 43.90%. Guarded-minus-Frozen late FRR was +3.00 points (95% CI [0.00, +7.00]). Oracle-all-minus-Frozen late FRR was −65.25 points (95% CI [−83.75, −45.50]), while Oracle-all-minus-Guarded late FAR was +64.76 points (95% CI [+48.93, +79.24]). These results are reported as a mechanism-level external replication, not as a state-of-the-art McGill performance benchmark (Fig. [MCGILL_TRADEOFF]; Fig. [MCGILL_TRAJECTORY]).

## 4.8. Summary Across Datasets

At the historical reference operating points, the score-informed boundary benchmark increased Blind EMA post-poison ASR on HMOG and McGill, and Guarded reduced the additional effect toward Frozen. That direction was not invariant under recalibration: the effect narrowed at nominal 5%, the McGill nominal-5% interval included zero, and the mean Blind-minus-Frozen effect was negative at nominal 1% on both datasets. The strict conditions also produced high genuine rejection and fewer feasible boundary paths, while the original Guarded anchor often supplied no additional effective margin. In the separate temporal evaluations, accepted-only Guarded adaptation did not produce lower late FRR than Frozen, and Oracle-all changed genuine tracking together with higher FAR. The operating-point sensitivity study bounded the reference poisoning results; it was not another benign-drift experiment.
