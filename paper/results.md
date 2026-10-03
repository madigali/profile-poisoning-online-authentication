# 4. Results

## 4.1. Poisoning Vulnerability of Blind EMA

Under the HMOG boundary attack at \(K=8\), post-poison ASR was 22.92% for Frozen and 53.96% for Blind EMA, a Blind-minus-Frozen increase of +31.04 percentage points. Blind ASR increased monotonically across the nested boundary budgets: 22.92%, 27.50%, 33.68%, 44.31%, and 53.96% at \(K=0,1,2,4,8\), respectively. The random attack produced a smaller increase over the same budgets, from 22.92% at \(K=0\) to 23.38%, 23.88%, 25.09%, and 27.55%. These attack-budget results are shown in Fig. [POISONING] and summarized in Table [MAIN_RESULTS].

## 4.2. Guarded Update Authorization Suppresses Poisoning

At boundary \(K=8\), post-poison ASR was 22.92% for Frozen, 53.96% for Blind EMA, and 22.93% for Guarded EMA with \(\lambda=0.25\). Blind EMA incorporated all presented boundary poisons (MUR 100.00%), whereas Guarded EMA incorporated 1.63%. Guarded \(\lambda=0\) reproduced Blind EMA in the frozen consistency check.

The complete lambda sweep was exploratory. At boundary \(K=8\), MUR decreased from 100.00% at \(\lambda=0\) to 0.13% at \(\lambda=1\), while genuine update availability in the separate replay decreased from 85.96% to 41.78%. The carried-forward \(\lambda=0.25\) result was therefore reported as a fixed security comparison rather than as a universally optimal setting (Fig. [POISONING]; Table [MAIN_RESULTS]).

## 4.3. Guarded EMA Does Not Preserve Clean-Drift FRR Utility

In the primary claimant-only \(D=2\) HMOG scenario, Frozen late FRR/FAR/HTER were 32.53%/22.86%/27.70%. Blind EMA yielded 32.20%/23.80%/28.00%, and Guarded EMA yielded 34.60%/21.73%/28.16% (Fig. [TRADEOFF]).

Relative to Frozen, Blind EMA had a late-FRR gain of +0.33 percentage points (95% CI [−1.20, +1.93]), a late-FAR change of +0.93 points (95% CI [−0.58, +2.64]), and an HTER gain of −0.30 points (95% CI [−1.02, +0.40]). Guarded EMA had a late-FRR gain of −2.07 points (95% CI [−3.53, −0.63]), a late-FAR change of −1.14 points (95% CI [−2.29, +0.12]), and an HTER gain of −0.46 points (95% CI [−1.16, +0.21]). Thus, the Guarded point estimate had lower late FAR but higher late FRR than Frozen; its prespecified clean-drift FRR utility was not positive.

## 4.4. Oracle-All-Genuine Isolates Feedback Censoring

Oracle-all-genuine reduced claimant-only late FRR relative to Frozen at every HMOG drift level. Late-FRR gains were +4.73 percentage points at \(D=0\) (95% CI [+3.17, +6.33]), +5.10 points at \(D=1\) (95% CI [+3.40, +6.80]), and +6.60 points at \(D=2\) (95% CI [+4.90, +8.40]).

The corresponding late-FAR changes were +5.51 points (95% CI [+3.79, +7.40]), +5.67 points (95% CI [+3.85, +7.71]), and +6.08 points (95% CI [+4.20, +8.16]). HTER gains remained small: −0.39 points at \(D=0\) (95% CI [−1.22, +0.42]), −0.28 points at \(D=1\) (95% CI [−1.26, +0.65]), and +0.26 points at \(D=2\) (95% CI [−0.59, +1.09]). Each HTER interval included zero.

The claimant-only \(D=2\) trajectories also differed in direction. Across the five retained checkpoints, the Guarded profile mean and threshold moved upward, while both Oracle-all quantities moved downward. Guarded update rate decreased from 63.47% at the first checkpoint to 51.68% at the fifth; Oracle-all update rate remained 100%. These trajectories are shown in Fig. [TRAJECTORY]. Oracle-all improved genuine tracking in this diagnostic comparison while incurring a higher FAR; it was not evaluated as a deployable method.

## 4.5. TQ-EMA v1

In claimant-only \(D=2\), TQ-EMA v1 produced late FRR/FAR/HTER of 33.43%/20.92%/27.18%, compared with 32.53%/22.86%/27.70% for Frozen. The paired late-FRR gain was −0.90 percentage points (95% CI [−1.80, 0.00]); the prespecified FRR recovery criterion was therefore not met. The late-FAR change was −1.94 points (95% CI [−2.46, −1.43]), and HTER improved by +0.52 points (95% CI [+0.10, +0.94]). The two-way victim-by-impostor-source FAR bootstrap gave a similar −1.94-point estimate (95% CI [−2.48, −1.42]).

Across the \(D=2\) event audit, TQ-EMA v1 applied 1,404 trusted updates and 49 confirmed recovery updates. The method remained on the lower-FAR, higher-FRR side of Frozen in Fig. [TRADEOFF]. Its primary late-FRR recovery criterion was not met, and the branch was stopped (Table [MAIN_RESULTS]).

## 4.6. TQ-EMA v2 Validation Stopping

TQ-EMA v2 completed its fold-specific validation grids before any outer test score was loaded. No fold showed a positive selected validation late-FRR gain. Fold 4 had no configuration satisfying both the +1.0-percentage-point late-FAR limit and the +0.5-point HTER-degradation limit; its best late-FRR gain over the full grid was −4.55 points, and the minimum HTER degradation was +0.89 points. The fail-closed stopping rule was triggered. The manifest records validation failure and outer_test_loaded=false, so no TQ-EMA v2 outer-test result is reported.

## 4.7. Adaptive Quantile Validation Stopping

No value in the frozen \(\rho\in\{0.80,0.90,0.95\}\) grid satisfied the Accepted-only Quantile validation gate in any of the five folds. At the descriptively least-bad value, \(\rho=0.95\), Accepted-only Quantile had mean late-FRR gain −10.64 percentage points, late-FAR change −4.89 points, and HTER change +2.87 points relative to Frozen.

At the same \(\rho\), Oracle-all Quantile had mean late-FRR gain −4.62 points, late-FAR change −1.83 points, and HTER change +1.39 points relative to Frozen. Its late FRR was lower than that of Accepted-only Quantile, but both quantile regimes remained worse than Frozen on the validation late-FRR endpoint. The branch stopped at validation in all five folds; outer test scores were not loaded, and no outer quantile estimate is reported.

## 4.8. External Replication on McGill Gait

The fixed Day-1 McGill classifier attained 58.12% validation top-1 accuracy and passed the prespecified 20% viability gate before Day 2 was loaded.

Under the Day-2 boundary attack at \(K=8\), held-out ASR was 12.37% for Frozen, 32.09% for Blind EMA, and 12.48% for Guarded EMA. The paired Blind-minus-Frozen effect was +19.72 percentage points (95% CI [+5.58, +37.34]), and the Guarded-minus-Blind effect was −19.62 points (95% CI [−37.17, −5.60]). Blind MUR was 100.00%, whereas Guarded MUR was 32.22%; the paired Guarded-minus-Blind MUR difference was −67.78 points (95% CI [−84.30, −49.47]). Boundary \(K=8\) included 18 victims with at least one eligible repeat. Of 2,000 victim-repeat paths, 544 lacked eight initially accepted boundary candidates and were recorded as feasibility exclusions.

The random \(K=8\) effect was smaller. Blind-minus-Frozen ASR was +1.51 points across 20 subjects, and its 95% CI [−0.09, +4.43] included zero. The poisoning results are shown in Fig. [MCGILL_POISONING] and Table [MCGILL].

For the Day-2 temporal analysis, Frozen late FRR/FAR were 78.00%/11.46%, Guarded values were 81.00%/10.29%, and Oracle-all values were 12.75%/75.05%. The corresponding late HTER values were 44.73%, 45.64%, and 43.90%. Guarded-minus-Frozen late FRR was +3.00 points (95% CI [0.00, +7.00]). Oracle-all-minus-Frozen late FRR was −65.25 points (95% CI [−83.75, −45.50]), while Oracle-all-minus-Guarded late FAR was +64.76 points (95% CI [+48.93, +79.24]). These results are reported as a mechanism-level external replication, not as a state-of-the-art McGill performance benchmark (Fig. [MCGILL_TRADEOFF]; Fig. [MCGILL_TRAJECTORY]).

## 4.9. Summary Across Datasets

Across HMOG and McGill, the score-informed boundary attack increased Blind EMA post-poison ASR, and the transferred Guarded update-authorization rule reduced post-poison ASR toward the corresponding Frozen value. In the temporal evaluations, accepted-only Guarded adaptation did not produce lower late FRR than Frozen. Oracle-all substantially changed genuine tracking in both datasets, together with higher FAR. Table [MAIN_RESULTS] and Table [MCGILL] summarize the observed within-dataset effects and their stated inferential status.
