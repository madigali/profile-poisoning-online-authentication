# 4. Results

## 4.1. Reference-point poisoning and Guarded updating

At the HMOG reference point, boundary poisoning increased post-poison ASR from 22.92% for Frozen to 53.96% for Blind EMA at \(K=8\). The paired Blind-minus-Frozen effect was +31.04 percentage points (historical 95% CI [+26.95, +35.20]) across 100 victims, 500 victim-fold units, and 49,889 eligible paths. Blind ASR increased with the nested boundary budget from 22.92% at \(K=0\) to 27.50%, 33.68%, 44.31%, and 53.96% at \(K=1,2,4,8\). The corresponding random curve reached 27.55% at \(K=8\), making the boundary benchmark the stronger reference attack (Fig. 1).

The 22.92% Frozen baseline reflects the validation-calibrated approximate-EER operating point. The paired contrast estimates additional acceptance after Blind updating within this feasible cohort. It does not imply that the unpoisoned classifier met a deployment security target.

Guarded EMA with \(\lambda=0.25\) produced 22.93% post-poison ASR and 1.63% MUR at boundary \(K=8\), compared with Blind MUR of 100%. This metric-level proximity to Frozen indicates suppression of the additional Blind amplification at the reference point, not equivalence of states or deployment security. The exploratory \(\lambda\) sweep reduced boundary-\(K=8\) MUR from 100.00% at \(\lambda=0\) to 0.13% at \(\lambda=1\), while genuine update availability in a separate replay fell from 85.96% to 41.78%. Guarded \(\lambda=0\) reproduced Blind exactly as a consistency check.

[INSERT FIGURE 1 HERE]

**Figure 1.** HMOG reference-point post-poison ASR on held-out impostor probes across nested numbers of presented poisoning attempts \(K\). Poison and probe source-session groups were disjoint, and the profile was frozen before probe evaluation. Lines are victim-macro fold summaries for Frozen, Blind EMA, and Guarded EMA (\(\lambda=0.25\)); shaded fold-level \(t\)-bands are descriptive because the five fitting partitions overlap. The paired victim-bootstrap interval for the primary boundary \(K=8\) contrast is reported in the text.

## 4.2. Operating-point sensitivity, feasibility, and gate activity

Nominal calibration targets did not determine held-out FAR (Table 1). Under the nominal-1% condition, mean achieved calibration FAR was 0.91% on HMOG and 0.79% on McGill, whereas full-cohort held-out Frozen FAR was 1.04% and 2.14%. Full-cohort Frozen FRR was 80.79% and 90.25%, respectively. These values describe all structurally valid held-out paths and are not baselines for the conditional boundary effects.

| Dataset | Condition | Achieved calibration FAR | Full held-out Frozen FAR | Full held-out Frozen FRR | Cohort |
|---|---:|---:|---:|---:|---|
| HMOG | Reference (approximate EER) | 23.01% | 22.92% | 24.95% | 500 calibration profiles; 100 held-out victims |
| HMOG | Nominal 5% calibration FAR | 4.93% | 5.07% | 57.88% | 500 calibration profiles; 100 held-out victims |
| HMOG | Nominal 1% calibration FAR | 0.91% | 1.04% | 80.79% | 500 calibration profiles; 100 held-out victims |
| McGill | Reference (minimum HTER) | 6.89% | 12.20% | 78.81% | 20 calibration profiles; 20 held-out victims |
| McGill | Nominal 5% calibration FAR | 3.66% | 7.37% | 82.43% | 20 calibration profiles; 20 held-out victims |
| McGill | Nominal 1% calibration FAR | 0.79% | 2.14% | 90.25% | 20 calibration profiles; 20 held-out victims |

**Table 1.** Calibration and full-cohort held-out Frozen performance. Calibration values are unweighted means of claimant-profile pooled-observation rates. Held-out values use all structurally valid random-\(K=0\) paths with victim-macro aggregation. Nominal targets are calibration constraints, not held-out guarantees.

The boundary-\(K=8\) Blind-minus-Frozen effect decreased from +31.04 to +2.49 and then -0.447 points across HMOG reference, nominal-5%, and nominal-1% conditions (Table 2; Fig. 2). McGill showed +19.72, +0.20, and -0.354 points; the nominal-5% CI included zero. Guarded-minus-Blind was strongly negative at reference, smaller at nominal 5%, and near zero at nominal 1%. Cross-target rows are not strictly paired because recalibration changed \(\tau_0\), claimant-specific \(k\), selected candidates, and feasible paths.

| Dataset | Condition | Blind EMA - Frozen ASR, pp [95% CI] | Guarded EMA - Blind EMA ASR, pp [95% CI] | Eligible paths | Victims | Victim-fold units |
|---|---:|---:|---:|---:|---:|---:|
| HMOG | Reference | +31.04 [+26.97, +35.11] | -31.02 [-35.15, -26.98] | 49,889 / 50,000 | 100 | 500 |
| HMOG | Nominal 5% | +2.49 [+0.95, +4.38] | -3.09 [-4.91, -1.61] | 49,753 / 50,000 | 100 | 500 |
| HMOG | Nominal 1% | -0.447 [-0.502, -0.393] | -0.009 [-0.020, -0.001] | 9,088 / 50,000 | 100 | 302 |
| McGill | Reference | +19.72 [+5.50, +37.24] | -19.62 [-36.77, -5.66] | 1,456 / 2,000 | 18 | - |
| McGill | Nominal 5% | +0.20 [-0.05, +0.53] | -0.26 [-0.58, -0.03] | 1,369 / 2,000 | 18 | - |
| McGill | Nominal 1% | -0.354 [-0.552, -0.186] | 0.000 [0.000, 0.000] | 1,001 / 2,000 | 17 | - |

**Table 2.** Conditional boundary-\(K=8\) paired post-poison ASR effects. Each condition uses its own common feasible cohort and a 10,000-draw paired victim bootstrap. The reference rows use the sensitivity package's retained random streams; historical reference intervals remain in Section 4.1 and the McGill corroboration. Three decimals preserve near-zero effects.

[INSERT FIGURE 2 HERE]

**Figure 2.** Operating-point dependence of boundary-\(K=8\) post-poison ASR effects. Points are Blind EMA minus Frozen and Guarded EMA minus Blind EMA with paired victim-bootstrap 95% intervals. Operating points are not connected because their feasible cohorts can differ. Source: frozen `boundary_k8_effects` artifact.

For the sensitivity primary, a secondary victim-by-impostor-source bootstrap gave -0.447 points [−0.515, −0.383] for Blind minus Frozen and -0.009 points [−0.022, −0.001] for Guarded minus Blind. It covered 100 victims, 9,088 paths, and 100 observed impostor sources only in HMOG nominal 1%, boundary \(K=8\); it did not add training or population uncertainty.

The negative strict-point ASR effect did not indicate harmless updating. On the same 9,088-path HMOG nominal-1% cohort, Frozen ASR/FRR/HTER were 0.826%/80.18%/40.50%, while Blind values were 0.379%/87.07%/43.73%. Blind increased FRR by 6.89 points (95% CI [+5.63, +8.27]) and HTER by 3.22 points (95% CI [+2.59, +3.91]). The experiment did not specify a separate availability-oriented attacker, so this result is not presented as a demonstrated denial-of-service attack.

Strict calibration also reduced feasibility. HMOG nominal 1% retained 9,088 of 50,000 planned boundary paths across 100 victims and 302 of 500 victim-fold units; McGill retained 1,001 of 2,000 paths across 17 victims. Excluded paths lacked eight initially accepted candidates and were not assigned zero ASR. At this condition the Guarded gate exceeded authentication in 19.22% of 72,704 HMOG poisoning states and 13.49% of 8,008 McGill states. Initial \(k<0\) occurred in 443 of all 500 HMOG claimant-fold profiles and 15 of all 20 McGill profiles, a different denominator. The sign of \(k\) alone does not explain the aggregate reversal. On McGill nominal 1%, Blind and Guarded had equal aggregate ASR but MURs of 69.36% and 62.32%; equal endpoints did not imply equal updates or trajectories.

The gate percentages are state-weighted diagnostics, while the paired ASR effects are victim-macro estimates and the negative-\(k\) values use all calibration profiles. They are presented together to describe the mechanism but should not be read as interchangeable sampling units.

## 4.3. Clean temporal behavior and Oracle diagnostic

Under the primary claimant-only HMOG synthetic shift at \(D=2\), Frozen late FRR/FAR/HTER were 32.53%/22.86%/27.70%. Guarded values were 34.60%/21.73%/28.16%, corresponding to a late-FRR gain of -2.07 points (95% CI [-3.53, -0.63]) relative to Frozen. Blind late FRR was 32.20%, with a gain of +0.33 points (95% CI [-1.20, +1.93]). Neither accepted-only method showed a clear improvement in the prespecified late-FRR endpoint (Fig. 3).

Blind late FAR changed by +0.93 points (95% CI [-0.58, +2.64]) and its HTER gain was -0.30 points (95% CI [-1.02, +0.40]). Guarded late FAR changed by -1.14 points (95% CI [-2.29, +0.12]), while its HTER gain was -0.46 points (95% CI [-1.16, +0.21]). Guarded's lower FAR point estimate was accompanied by higher FRR rather than a free improvement.

Oracle-all made every ground-truth genuine adaptation candidate update-eligible. At \(D=2\), its late-FRR gain over Frozen was +6.60 points (95% CI [+4.90, +8.40]), accompanied by a +6.08-point late-FAR change (95% CI [+4.20, +8.16]). At \(D=0\), it already lowered late FRR by 4.73 points and raised late FAR by 5.51 points. Its result therefore reflects operating-point movement as well as response to synthetic shift. Guarded mean and threshold moved upward across the five retained checkpoints, while the Oracle-all state moved downward; Guarded update rate fell from 63.47% to 51.68%, and Oracle-all update eligibility remained 100% (Fig. 4).

Oracle-all HTER gains relative to Frozen were -0.39, -0.28, and +0.26 points at \(D=0,1,2\), and all three CIs included zero. The opposing FRR and FAR changes therefore produced little balanced-error improvement. Complete intermediate-level effects are reported in Supplementary Results S5.

[INSERT FIGURE 3 HERE]

**Figure 3.** HMOG late FAR-FRR operating points under claimant-only synthetic shift \(D=2\). Points are subject-macro estimates for Frozen, Blind EMA, Guarded EMA (\(\lambda=0.25\)), Oracle-all, and TQ-EMA v1; bars are paired subject-bootstrap 95% intervals after subject-level aggregation. Lower values on both axes are preferable.

[INSERT FIGURE 4 HERE]

**Figure 4.** HMOG profile trajectories under claimant-only synthetic shift \(D=2\). Panels show change from enrollment in profile mean and authentication threshold, plus genuine update rate, across five evaluation checkpoints for Guarded EMA and Oracle-all. Lines are subject-level means and bands are subject-bootstrap 95% intervals. Oracle-all is label-aware and non-deployable.

## 4.4. McGill cross-day corroboration

The frozen Day-1 McGill classifier attained 58.12% validation top-1 accuracy and passed its prespecified 20% viability gate before Day-2 scores were loaded. At reference boundary \(K=8\), ASR was 12.37% for Frozen, 32.09% for Blind, and 12.48% for Guarded (Table 3). The paired Blind-minus-Frozen effect was +19.72 points (historical 95% CI [+5.58, +37.34]); Guarded-minus-Blind was -19.62 points (95% CI [-37.17, -5.60]). Blind MUR was 100%, and Guarded MUR was 32.22%. The eligible cohort contained 1,456 of 2,000 paths across 18 victims; 544 paths lacked eight accepted candidates. The random-\(K=8\) Blind effect was +1.51 points across all 20 subjects, with a CI [-0.09, +4.43] that included zero.

In the Day-2 temporal stream, Guarded late FRR was 81.00% versus 78.00% for Frozen, while Oracle-all FRR was 12.75%. Oracle-all FAR reached 75.05%, compared with 11.46% for Frozen and 10.29% for Guarded. The results reproduce the reference-point directions under a difficult cross-day setting but do not establish comparable absolute performance or isolate behavioral drift. Frozen McGill figures are retained in Supplementary Results S6.

Guarded-minus-Frozen late FRR was +3.00 points (95% CI [0.00, +7.00]). Oracle-all-minus-Frozen FRR was -65.25 points (95% CI [-83.75, -45.50]), while Oracle-all-minus-Guarded FAR was +64.76 points (95% CI [+48.93, +79.24]). These large opposing changes explain why the three late HTER values were much closer than their separate FAR and FRR components.

| McGill analysis | Cohort | Frozen | Blind EMA | Guarded EMA | Oracle-all | Paired effect [95% CI], pp |
|---|---|---:|---:|---:|---:|---|
| Reference boundary \(K=8\), post-ASR | 1,456 paths; 18 victims | 12.37% | 32.09% | 12.48% | - | Blind - Frozen: +19.72 [+5.58, +37.34] |
| Day-2 late FRR / FAR / HTER | 20 subjects | 78.00 / 11.46 / 44.73% | - | 81.00 / 10.29 / 45.64% | 12.75 / 75.05 / 43.90% | Guarded - Frozen FRR: +3.00 [0.00, +7.00] |

**Table 3.** McGill reference poisoning and cross-day temporal evidence. Poisoning effects average repeats within victims before paired subject bootstrap. Temporal endpoints are subject-macro rates over the last 20 of 80 adaptation-checkpoint pairs. Oracle-all uses labels only for update eligibility and is not deployable.

## 4.5. Supporting recovery and state probes

TQ-EMA v1 reached outer evaluation but did not meet its recovery criterion. In claimant-only \(D=2\), late-FRR gain was -0.90 points (95% CI [-1.80, 0.00]); late FAR changed by -1.94 points, and HTER gain was +0.52 points. The event audit recorded 1,404 trusted and 49 recovery updates. TQ-EMA v2 then failed its validation gate because fold 4 had no configuration satisfying both safety constraints. No Adaptive Quantile setting was feasible in all folds. The latter branches have `outer_test_loaded=false` and no outer estimates. Their complete specifications and validation outcomes appear in Supplementary Methods S6-S10 and Supplementary Results S1-S3.

TQ-v1's complete-five-fold sensitivity did not reverse the stopping decision. TQ-v2 had feasible selections in four folds, but all selected late-FRR gains were negative; fold 4 triggered the fail-closed rule. These validation values are documented in the Supplement and are not presented as outer performance.
