# Supplementary Results

## S1. TQ-EMA v1 outer evaluation

TQ-EMA v1 reached its permitted outer evaluation in claimant-only HMOG \(D=2\). Late FRR/FAR/HTER were 33.43%/20.92%/27.18%, compared with 32.53%/22.86%/27.70% for Frozen. The paired late-FRR gain was -0.90 percentage points (95% CI [-1.80, 0.00]), so the recovery criterion was not met. Late FAR changed by -1.94 points (95% CI [-2.46, -1.43]), and HTER gain was +0.52 points (95% CI [+0.10, +0.94]). A secondary victim-by-impostor-source late-FAR bootstrap gave -1.94 points (95% CI [-2.48, -1.42]).

The complete-five-fold cohort did not reverse the decision: its late-FRR-gain CI lower bound was -1.92 points. The \(D=2\) audit recorded 1,404 trusted updates and 49 confirmed recovery updates. These totals are not independent observations.

| Fold | Selected configuration | Band / \(\sigma_{\mathrm{enroll}}\) | Confirmation sessions | Recovery \(\alpha\) | Anchor / \(\sigma_{\mathrm{enroll}}\) | Validation late-FRR gain, pp | Late-FAR change, pp | HTER change, pp |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `b0.25_m3_a0.025_A0.10` | 0.25 | 3 | 0.025 | 0.10 | 0.00 | -0.38 | -0.19 |
| 2 | `b0.50_m2_a0.025_A0.10` | 0.50 | 2 | 0.025 | 0.10 | -0.50 | -0.29 | +0.10 |
| 3 | `b0.25_m2_a0.050_A0.10` | 0.25 | 2 | 0.050 | 0.10 | -1.01 | +0.07 | +0.54 |
| 4 | `b0.25_m3_a0.025_A0.10` | 0.25 | 3 | 0.025 | 0.10 | 0.00 | -1.22 | -0.61 |
| 5 | `b0.25_m2_a0.025_A0.10` | 0.25 | 2 | 0.025 | 0.10 | -2.00 | +0.08 | +1.04 |

**Table S1.** Fold-specific TQ-v1 validation selections. Rows document selection inputs and are not pooled outer estimates. Source: `results/paper3_tq_clean_drift_20261001_v1/`.

## S2. TQ-EMA v2 validation stopping

TQ-v2 completed fold-specific validation before any outer score was loaded. Folds 1, 2, 3, and 5 had feasible selections, all with negative late-FRR gains. Fold 4 had no configuration satisfying both the +1.0-point late-FAR limit and +0.5-point HTER-degradation limit.

| Fold | Selection status | Selected late-FRR gain, pp | Late-FAR change, pp | HTER change, pp | Feasible configurations |
|---:|---|---:|---:|---:|---:|
| 1 | Feasible | -3.50 | -2.61 | +0.44 | 14 |
| 2 | Feasible | -1.50 | -2.12 | -0.31 | 24 |
| 3 | Feasible | -1.01 | -1.19 | -0.09 | 24 |
| 4 | No feasible configuration | - | - | - | 0 |
| 5 | Feasible | -2.50 | -2.28 | +0.11 | 24 |

**Table S2.** TQ-v2 validation-gate results. Fold 4 triggered the fail-closed rule. Its best unconstrained late-FRR gain was -4.55 points, and the minimum HTER degradation in the grid was +0.89 points. The manifest records `outer_test_loaded=false`; no TQ-v2 outer estimate exists. Source: `results/paper3_tq_v2_validation_failed_20261001/`.

## S3. Adaptive Quantile validation stopping

No \(\rho\in\{0.80,0.90,0.95\}\) satisfied the Accepted-only Quantile gate in any fold. The descriptively least-bad unconstrained value was \(\rho=0.95\) in each fold. At that value, across-fold descriptive means for Accepted-only Quantile were late-FRR gain -10.64 points, late-FAR change -4.89 points, and HTER change +2.87 points relative to Frozen. Oracle-all Quantile at the same \(\rho\) had late-FRR gain -4.62, late-FAR change -1.83, and HTER change +1.39 points.

Oracle-all reduced the additional FRR deficit associated with accepted-only eligibility, but neither information regime outperformed Frozen on the validation late-FRR endpoint. Fold denominators were 100, 100, 99, 99, and 100 subjects. All folds failed the gate, `outer_test_loaded=false`, and no outer Quantile estimate exists. Source: `results/paper3_quantile_validation_failed_20261001_v1/`.

| Probe | Data stage reached | Gate outcome | Outer estimate | Evaluation status |
|---|---|---|---|---|
| TQ-EMA v1 | Validation and permitted outer evaluation | Late-FRR recovery criterion not met | Yes | Stopped after outer evaluation |
| TQ-EMA v2 | Validation only | Fold 4 had no feasible configuration | No | Fail-closed validation stop |
| Adaptive Quantile Profile | Validation only | No feasible \(\rho\) in any fold | No | Fail-closed validation stop |

**Table S3.** Evaluation status of supporting recovery and state probes. Outcomes apply to the frozen implementations and parameter grids and do not reject their broader method families.

## S4. Operating-point diagnostics

The primary paired operating-point effect figure remains in the main article. Three frozen diagnostics remain supplementary because their aggregation units differ from the victim-macro effect table.

[INSERT FIGURE S1 HERE]

**Figure S1.** Achieved calibration FAR and full-cohort held-out Frozen FAR at reference, nominal-5%, and nominal-1% conditions. Calibration values are unweighted claimant-profile means; held-out values are victim-macro estimates over all structurally valid random-\(K=0\) paths. Source: frozen `calibration_vs_heldout_far` artifact.

[INSERT FIGURE S2 HERE]

**Figure S2.** Boundary-\(K=8\) feasibility across operating points. Fractions use all planned paths as the denominator. Excluded paths lacked eight initially accepted candidates and were not assigned zero ASR. Source: frozen `boundary_feasibility` artifact.

[INSERT FIGURE S3 HERE]

**Figure S3.** Guarded gate diagnostics for boundary \(K=8\). Strict-gate and \(\tau_{\mathrm{auth}}\geq\mu_{\mathrm{enroll}}\) fractions are state-weighted over eligible poisoning states. Negative-\(k\) prevalence uses all 500 HMOG claimant-fold profiles or 20 McGill claimant profiles and is not eligibility-conditioned. Source: frozen `guarded_gate_diagnostics` artifact.

## S5. Additional HMOG temporal outcomes

Oracle-all late-FRR gains over Frozen were +4.73 points at \(D=0\) (95% CI [+3.17, +6.33]), +5.10 at \(D=1\) ([+3.40, +6.80]), and +6.60 at \(D=2\) ([+4.90, +8.40]). Corresponding late-FAR changes were +5.51 ([+3.79, +7.40]), +5.67 ([+3.85, +7.71]), and +6.08 points ([+4.20, +8.16]). HTER gains were -0.39, -0.28, and +0.26 points; every HTER CI included zero. The \(D=0\) result shows that the Oracle contrast includes operating-point movement rather than recovery unique to synthetic shift.

## S6. McGill frozen figures

The main article retains McGill numerical evidence in its Results and Table 3. The three frozen McGill figures are supplementary to reduce main-text duplication.

[INSERT FIGURE S4 HERE]

**Figure S4.** McGill reference-point post-poison ASR across nested random and score-informed boundary budgets. Poison and probe source identities are disjoint, and profiles are frozen before probe evaluation. Boundary \(K=8\) uses 1,456 eligible victim-repeat paths across 18 victims; random uses all 2,000 paths across 20 subjects. Source: frozen `external_poisoning_asr` artifact.

[INSERT FIGURE S5 HERE]

**Figure S5.** McGill Day-2 late FAR-FRR operating points for Frozen, Guarded EMA, and Oracle-all. Points are subject-macro estimates over the last 20 of 80 temporal units. Oracle-all is label-aware and non-deployable. Source: frozen `external_temporal_tradeoff` artifact.

[INSERT FIGURE S6 HERE]

**Figure S6.** McGill Day-2 trajectories across 80 adaptation-checkpoint pairs. Panels show subject-macro profile mean, threshold, evaluation-only FRR, and update rate. Adaptation observations precede disjoint checkpoints, and matched impostor checkpoints do not update profiles. Source: frozen `external_selection_bias_trajectory` artifact.
