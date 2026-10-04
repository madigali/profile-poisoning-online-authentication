# Supplementary Results

## S1. TQ-EMA v1 Outer Evaluation

TQ-EMA v1 reached its permitted outer evaluation in claimant-only HMOG \(D=2\). Late FRR/FAR/HTER were 33.43%/20.92%/27.18%, compared with 32.53%/22.86%/27.70% for Frozen. The paired late-FRR gain was −0.90 percentage points (95% CI [−1.80, 0.00]); the prespecified positive-recovery criterion was therefore not met. Late FAR changed by −1.94 points (95% CI [−2.46, −1.43]), and HTER gain was +0.52 points (95% CI [+0.10, +0.94]). A secondary victim-by-impostor-source late-FAR bootstrap gave −1.94 points (95% CI [−2.48, −1.42]).

The complete-five-fold cohort did not reverse the decision: its late-FRR-gain confidence-interval lower bound was −1.92 points. Across the \(D=2\) event audit, TQ-EMA v1 applied 1,404 trusted updates and 49 confirmed recovery updates. These are aggregate event counts, not independent observations.

Fold-specific validation selected the following frozen configurations:

| Fold | Selected configuration | Band / \(\sigma_{\mathrm{enroll}}\) | Confirmation sessions | Recovery \(\alpha\) | Anchor / \(\sigma_{\mathrm{enroll}}\) | Validation late-FRR gain, pp | Validation late-FAR change, pp | Validation HTER change, pp |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `b0.25_m3_a0.025_A0.10` | 0.25 | 3 | 0.025 | 0.10 | 0.00 | −0.38 | −0.19 |
| 2 | `b0.50_m2_a0.025_A0.10` | 0.50 | 2 | 0.025 | 0.10 | −0.50 | −0.29 | +0.10 |
| 3 | `b0.25_m2_a0.050_A0.10` | 0.25 | 2 | 0.050 | 0.10 | −1.01 | +0.07 | +0.54 |
| 4 | `b0.25_m3_a0.025_A0.10` | 0.25 | 3 | 0.025 | 0.10 | 0.00 | −1.22 | −0.61 |
| 5 | `b0.25_m2_a0.025_A0.10` | 0.25 | 2 | 0.025 | 0.10 | −2.00 | +0.08 | +1.04 |

These validation rows document fold-specific selection; they are not pooled outer estimates. The authoritative package is `results/paper3_tq_clean_drift_20261001_v1/`.

## S2. TQ-EMA v2 Validation Stopping

TQ-EMA v2 completed fold-specific validation before any outer score was loaded. Folds 1, 2, 3, and 5 had feasible selected configurations, but their selected late-FRR gains were all negative. Fold 4 had no configuration satisfying both the +1.0-percentage-point late-FAR limit and the +0.5-point HTER-degradation limit.

| Fold | Selection status | Selected validation late-FRR gain, pp | Late-FAR change, pp | HTER change, pp | Feasible configurations |
|---:|---|---:|---:|---:|---:|
| 1 | Feasible | −3.50 | −2.61 | +0.44 | 14 |
| 2 | Feasible | −1.50 | −2.12 | −0.31 | 24 |
| 3 | Feasible | −1.01 | −1.19 | −0.09 | 24 |
| 4 | No feasible configuration | — | — | — | 0 |
| 5 | Feasible | −2.50 | −2.28 | +0.11 | 24 |

For fold 4, the best unconstrained late-FRR gain was −4.55 points and the minimum HTER degradation anywhere in the grid was +0.89 points. The fail-closed rule was triggered by this fold. The manifest records `outer_test_loaded=false`; no TQ-EMA v2 outer estimate exists. The authoritative package is `results/paper3_tq_v2_validation_failed_20261001/`.

## S3. Adaptive Quantile Validation Stopping

No value in the frozen \(\rho\in\{0.80,0.90,0.95\}\) grid satisfied the Accepted-only Quantile validation gate in any fold. The descriptively least-bad unconstrained value was \(\rho=0.95\) in each fold; it was not a successfully selected deployable configuration. At \(\rho=0.95\), the frozen across-fold descriptive means for Accepted-only Quantile were late-FRR gain −10.64 percentage points, late-FAR change −4.89 points, and HTER change +2.87 points relative to Frozen. Oracle-all Quantile at the same \(\rho\) had late-FRR gain −4.62 points, late-FAR change −1.83 points, and HTER change +1.39 points.

Oracle-all reduced the additional FRR deficit associated with accepted-only censoring, but neither information regime outperformed Frozen on the validation late-FRR endpoint. The fold validation denominators were 100, 100, 99, 99, and 100 subjects. All five folds failed the gate, the manifest records `outer_test_loaded=false`, and no outer quantile estimate exists. The authoritative package is `results/paper3_quantile_validation_failed_20261001_v1/`.

## S4. Protocol Decisions for Supporting Probes

| Probe | Data stage reached | Gate outcome | Outer estimate | Decision |
|---|---|---|---|---|
| TQ-EMA v1 | Validation plus permitted outer evaluation | Primary late-FRR recovery criterion not met | Yes | Stop |
| TQ-EMA v2 | Validation only | Fold 4 had no feasible configuration | No | Fail closed |
| Adaptive Quantile Profile | Validation only | No feasible \(\rho\) in any fold | No | Fail closed |

These results apply to the frozen implementations and parameter grids. They do not reject quarantine, temporal evidence, or robust distribution tracking as method families.

## S5. Operating-Point Diagnostic Figures

The primary operating-point effect figure is retained in the main manuscript. Three additional frozen diagnostics are assigned to the Supplement because their denominators differ from the victim-macro effect table.

[INSERT FIGURE S1 HERE]

**Figure S1.** Achieved calibration FAR and full-cohort held-out Frozen FAR across reference, nominal-5%, and nominal-1% conditions. Source: `results/paper3_operating_point_sensitivity_20261004_v1/figures/calibration_vs_heldout_far.pdf`. Calibration targets are constraints on calibration observations, not held-out guarantees.

[INSERT FIGURE S2 HERE]

**Figure S2.** Boundary-candidate feasibility at each operating point. Source: `results/paper3_operating_point_sensitivity_20261004_v1/figures/boundary_feasibility.pdf`. Feasibility is calculated over all planned paths; excluded paths are not treated as zero-ASR outcomes.

[INSERT FIGURE S3 HERE]

**Figure S3.** Guarded gate diagnostics for boundary \(K=8\). Source: `results/paper3_operating_point_sensitivity_20261004_v1/figures/guarded_gate_diagnostics.pdf`. Strict-gate and `tau_auth >= mu_enroll` fractions are state-weighted over eligible poisoning states. Initial negative-\(k\) prevalence uses all 500 HMOG claimant-fold profiles or all 20 McGill claimant profiles and is not an eligibility-conditioned state fraction.
