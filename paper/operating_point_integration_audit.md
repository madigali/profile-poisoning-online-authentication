# Operating-Point Integration Audit

Audit date: 4 October 2026.

## Scope and freeze status

This audit is the source-and-cohort map for Reviewer Revision Round 2. It precedes the Round-2 manuscript edits. It records only values already present in the frozen package `results/paper3_operating_point_sensitivity_20261004_v1/`; no score generation, trajectory construction, bootstrap, threshold selection, or new statistical analysis was performed for this integration.

The sensitivity analysis is described as a **prospectively specified sensitivity analysis on previously inspected score caches**. It is not an untouched confirmatory experiment or an externally preregistered study. Its primary contrast is HMOG nominal-1% calibration, boundary strategy, \(K=8\), Blind EMA minus Frozen post-poison ASR. This does not replace the historical HMOG reference reporting contrast.

Freeze tag checked: `paper3-operating-point-sensitivity-v1-2026-10-04`, pointing to revision `77f11de` at the time of this audit.

## Integrity verification

All 20 entries under `manifest.json/generated_files`, plus the protocol file, matched their recorded SHA-256 values. The top-level `source_sha256` did not match the current runner byte-for-byte:

| Item | Manifest top-level SHA-256 | Current SHA-256 | Resolution |
|---|---|---|---|
| `src/paper3_operating_point_sensitivity.py` | `fbcb564380b0728317fac66fbca7c7070653c09f80e2afdfc577b54b7977d859` | `ad60757e59a402b6c574af042bcc40aaf15ecd6c0e1d42c70db9ea734ede9002` | Not silently substituted. The current hash exactly matches `manifest.json/post_run_actions[0].source_sha256`. That recorded action regenerated figures from the frozen CSV tables only at revision `6a04f24`, removing lines between operating-point-specific cohorts; no outcomes or statistics were recomputed. The generated files still match their manifest hashes. |

The reference-reproduction gate passed. `reference_reproduction.csv` reports HMOG fold-level and McGill path-level matches within the locked (10^{-9}) tolerance.

## Cohort and denominator map

| Code | Cohort | Definition and weighting | Permitted use |
|---|---|---|---|
| A | Calibration | HMOG: 500 claimant-fold profiles; McGill: 20 claimant profiles. Each profile's FAR/FRR is calculated on its original validation/enrollment calibration observations; displayed summaries are unweighted profile means. | Calibration FAR/FRR and initialization diagnostics only. |
| B | Full structurally valid held-out | Random \(K=0\), Frozen, all planned structurally valid paths: HMOG 50,000 fold-victim-repeat paths and McGill 2,000 victim-repeat paths. HMOG repeats are averaged within victim/fold, folds within victim, then victims equally; McGill repeats are averaged within victim, then victims equally. | Held-out Frozen FAR, FRR, and HTER. Not the baseline for conditional boundary effects. |
| C | Condition-specific boundary-\(K=8\)-feasible | Within each dataset and operating point, only paths with at least eight initially accepted boundary candidates. All methods are paired on the same paths within a condition. HMOG hierarchy: repeats within victim/fold, folds within victim, equal victims; McGill: repeats within victim, equal victims. | Conditional boundary curves, absolute post-poison outcomes, and paired effects within one operating point. Cross-target effects are not strictly paired. |
| D | Legacy reference | HMOG historical common boundary-\(K=8\)-feasible cohort for both strategies; McGill all valid random paths and reference boundary-\(K=8\)-feasible paths. | Historical reference reproduction and historical figures/results only. |
| E | State-level gate diagnostics | Guarded boundary-\(K=8\) poisoning states within cohort C. Strict-gate and `tau_auth >= mu_enroll` fractions sum state counts. `accepted_blocked_by_gate_rate` uses all presented poisoning observations, \(n_{paths}\times8\), as denominator. `mean_MUR` is the unweighted path mean. | Gate activity; not victim-bootstrap inference and not claimant-profile prevalence. |
| F | Claimant-fold initialization | All 500 HMOG claimant-fold profiles or all 20 McGill claimant profiles in `calibration_by_claimant.csv`, whether or not their attack paths are \(K=8\)-feasible. | Initial \(k<0\) and initial `tau_auth >= mu_enroll` prevalence only. |

Rates in granular outputs are fractions; the summary CSVs used below report percent or percentage points as declared in their `unit` field.

## Numerical claim map A: calibration

Exact filter for every row: `calibration_by_claimant.csv`, `dataset=<Dataset>`, `condition=<Condition>`; take the unweighted mean across cohort A. No CI is attached to these descriptive calibration means.

| Dataset | Condition | Metric | Cohort | Exact value (%) | Displayed value (%) | Source/filter |
|---|---|---|---|---:|---:|---|
| HMOG | reference | Achieved calibration FAR | A, 500 claimant-fold profiles | 23.009342 | 23.01 | `achieved_calibration_far_pct` |
| HMOG | reference | Calibration FRR | A, 500 claimant-fold profiles | 22.995000 | 23.00 | `calibration_frr_pct` |
| HMOG | nominal 5% (`far_5pct`) | Achieved calibration FAR | A, 500 claimant-fold profiles | 4.927028 | 4.93 | `achieved_calibration_far_pct` |
| HMOG | nominal 5% | Calibration FRR | A, 500 claimant-fold profiles | 57.336667 | 57.34 | `calibration_frr_pct` |
| HMOG | nominal 1% (`far_1pct`) | Achieved calibration FAR | A, 500 claimant-fold profiles | 0.906233 | 0.91 | `achieved_calibration_far_pct` |
| HMOG | nominal 1% | Calibration FRR | A, 500 claimant-fold profiles | 80.390000 | 80.39 | `calibration_frr_pct` |
| McGill | reference | Achieved calibration FAR | A, 20 claimant profiles | 6.886746 | 6.89 | `achieved_calibration_far_pct` |
| McGill | reference | Calibration FRR | A, 20 claimant profiles | 7.677244 | 7.68 | `calibration_frr_pct` |
| McGill | nominal 5% | Achieved calibration FAR | A, 20 claimant profiles | 3.660792 | 3.66 | `achieved_calibration_far_pct` |
| McGill | nominal 5% | Calibration FRR | A, 20 claimant profiles | 24.240523 | 24.24 | `calibration_frr_pct` |
| McGill | nominal 1% | Achieved calibration FAR | A, 20 claimant profiles | 0.791320 | 0.79 | `achieved_calibration_far_pct` |
| McGill | nominal 1% | Calibration FRR | A, 20 claimant profiles | 57.260661 | 57.26 | `calibration_frr_pct` |

The nominal labels 5% and 1% are calibration constraints, not observed held-out FAR guarantees.

## Numerical claim map B: full held-out Frozen performance

Exact filter for every row: `operating_point_summary.csv`, `strategy=random`, `K=0`, `method=Frozen`, plus the listed dataset, condition, and metric. Cohort B and hierarchical victim weighting apply. The main OP-A table displays FAR and FRR; HTER is retained here for provenance if referenced in prose or Supplement.

| Dataset | Condition | Metric | \(n\) victims | Exact mean (%) | Displayed (%) | 95% victim-bootstrap CI (%) |
|---|---|---|---:|---:|---:|---|
| HMOG | reference | Held-out FAR (`post_ASR`) | 100 | 22.921580 | 22.92 | [21.389995, 24.506606] |
| HMOG | reference | Held-out FRR (`post_FRR`) | 100 | 24.951667 | 24.95 | [23.344917, 26.561708] |
| HMOG | reference | HTER | 100 | 23.936623 | 23.94 | [22.536006, 25.308796] |
| HMOG | nominal 5% | Held-out FAR | 100 | 5.069950 | 5.07 | [4.980975, 5.157275] |
| HMOG | nominal 5% | Held-out FRR | 100 | 57.885000 | 57.88 | [54.184875, 61.475125] |
| HMOG | nominal 5% | HTER | 100 | 31.477475 | 31.48 | [29.671251, 33.297101] |
| HMOG | nominal 1% | Held-out FAR | 100 | 1.037118 | 1.04 | [1.001278, 1.072309] |
| HMOG | nominal 1% | Held-out FRR | 100 | 80.790000 | 80.79 | [78.065000, 83.465125] |
| HMOG | nominal 1% | HTER | 100 | 40.913559 | 40.91 | [39.528402, 42.210360] |
| McGill | reference | Held-out FAR | 20 | 12.201235 | 12.20 | [7.317035, 17.847859] |
| McGill | reference | Held-out FRR | 20 | 78.809093 | 78.81 | [64.057360, 91.235723] |
| McGill | reference | HTER | 20 | 45.505164 | 45.51 | [38.315324, 51.937613] |
| McGill | nominal 5% | Held-out FAR | 20 | 7.368754 | 7.37 | [4.486386, 10.608105] |
| McGill | nominal 5% | Held-out FRR | 20 | 82.431319 | 82.43 | [68.720883, 94.180950] |
| McGill | nominal 5% | HTER | 20 | 44.900036 | 44.90 | [38.081029, 50.820839] |
| McGill | nominal 1% | Held-out FAR | 20 | 2.142469 | 2.14 | [1.228292, 3.216727] |
| McGill | nominal 1% | Held-out FRR | 20 | 90.254674 | 90.25 | [80.474941, 97.647526] |
| McGill | nominal 1% | HTER | 20 | 46.198572 | 46.20 | [41.483799, 49.815164] |

CI source: `operating_point_summary.csv`; 10,000-draw percentile victim bootstrap with key-derived seeds from master seed 20261004. The main OP-A table does not need to display these absolute-rate CIs.

## Numerical claim map C: conditional boundary \(K=8\) ASR effects

Exact filter for every row: `paired_effects_bootstrap.csv`, `strategy=boundary`, `K=8`, `metric=post_ASR`, plus dataset, condition, and contrast. Unit: percentage points. Cohort C and paired hierarchical victim weighting apply. CIs are 10,000-draw percentile victim-bootstrap intervals.

| Dataset | Condition | Contrast | Eligible paths | Victims | Victim-fold units | Exact effect [CI], pp | Displayed effect [CI], pp |
|---|---|---|---:|---:|---:|---|---|
| HMOG | reference | Blind EMA − Frozen | 49,889 / 50,000 | 100 | 500 | 31.037638 [26.966964, 35.106318] | +31.04 [+26.97, +35.11] |
| HMOG | reference | Guarded EMA − Blind EMA | 49,889 / 50,000 | 100 | 500 | -31.023970 [-35.145287, -26.977394] | -31.02 [-35.15, -26.98] |
| HMOG | nominal 5% | Blind EMA − Frozen | 49,753 / 50,000 | 100 | 500 | 2.491035 [0.953863, 4.377143] | +2.49 [+0.95, +4.38] |
| HMOG | nominal 5% | Guarded EMA − Blind EMA | 49,753 / 50,000 | 100 | 500 | -3.086723 [-4.912814, -1.608488] | -3.09 [-4.91, -1.61] |
| HMOG | nominal 1% | Blind EMA − Frozen | 9,088 / 50,000 | 100 | 302 | -0.447472 [-0.501858, -0.392954] | -0.447 [-0.502, -0.393] |
| HMOG | nominal 1% | Guarded EMA − Blind EMA | 9,088 / 50,000 | 100 | 302 | -0.008945 [-0.020157, -0.001396] | -0.009 [-0.020, -0.001] |
| McGill | reference | Blind EMA − Frozen | 1,456 / 2,000 | 18 | Not applicable (no folds) | 19.721769 [5.498731, 37.240872] | +19.72 [+5.50, +37.24] |
| McGill | reference | Guarded EMA − Blind EMA | 1,456 / 2,000 | 18 | Not applicable | -19.616457 [-36.769674, -5.661234] | -19.62 [-36.77, -5.66] |
| McGill | nominal 5% | Blind EMA − Frozen | 1,369 / 2,000 | 18 | Not applicable | 0.197818 [-0.050534, 0.531112] | +0.20 [-0.05, +0.53] |
| McGill | nominal 5% | Guarded EMA − Blind EMA | 1,369 / 2,000 | 18 | Not applicable | -0.260031 [-0.579399, -0.025518] | -0.26 [-0.58, -0.03] |
| McGill | nominal 1% | Blind EMA − Frozen | 1,001 / 2,000 | 17 | Not applicable | -0.354437 [-0.551523, -0.186408] | -0.354 [-0.552, -0.186] |
| McGill | nominal 1% | Guarded EMA − Blind EMA | 1,001 / 2,000 | 17 | Not applicable | 0.000000 [0.000000, 0.000000] | 0.000 [0.000, 0.000] |

Three decimals are retained for nominal-1% near-zero effects so that their sign and interval are not hidden. McGill nominal-1% equality of post-poison ASR does not imply identical update trajectories: the same cohort has Blind MUR 69.364656% and Guarded MUR 62.318087%, with a paired difference of -7.046569 points [−18.504902, 0.000000].

## Numerical claim map D: same-cohort post-poison FRR and HTER

The main same-cohort example is HMOG nominal 1%, boundary \(K=8\). Absolute rows come from `operating_point_summary.csv`; exact filters are `dataset=HMOG`, `condition=far_1pct`, `strategy=boundary`, `K=8`, and the listed method/metric. Paired rows come from `paired_effects_bootstrap.csv` with the same keys and listed contrast/metric. Cohort C contains 9,088 paths, 100 victims, and 302 victim-fold units.

| Method / contrast | Metric | Exact value (%) or pp | Displayed | CI source |
|---|---|---:|---:|---|
| Frozen | post-ASR | 0.826411% | 0.826% | `operating_point_summary.csv`: [0.753283, 0.902476]% |
| Frozen | post-FRR | 80.182361% | 80.18% | same: [77.056931, 83.176417]% |
| Frozen | HTER | 40.504386% | 40.50% | same: [38.974093, 41.972302]% |
| Blind EMA | post-ASR | 0.378938% | 0.379% | same: [0.308655, 0.454319]% |
| Blind EMA | post-FRR | 87.073292% | 87.07% | same: [84.094291, 89.904598]% |
| Blind EMA | HTER | 43.726115% | 43.73% | same: [42.233459, 45.124995]% |
| Blind EMA − Frozen | post-ASR | -0.447472 pp | -0.447 pp | `paired_effects_bootstrap.csv`: [−0.501858, −0.392954] |
| Blind EMA − Frozen | post-FRR | +6.890931 pp | +6.89 pp | same: [+5.627308, +8.273628] |
| Blind EMA − Frozen | HTER | +3.221729 pp | +3.22 pp | same: [+2.586190, +3.907842] |

Interpretation boundary: lower post-poison ASR did not imply harmless updates; genuine rejection increased on the same eligible cohort. This is not evidence from a separately designed availability/denial-of-service attack objective.

## Numerical claim map E: \(K=8\) feasibility

Exact filter: `eligibility_summary.csv`, `strategy=boundary`, `K=8`, plus dataset and condition. Counts are over the full planned path grid before conditional outcome estimation. Infeasible paths are exclusions, not ASR=0 observations.

| Dataset | Condition | Eligible / planned paths | Eligible fraction | Victims | Victim-fold units |
|---|---|---:|---:|---:|---:|
| HMOG | reference | 49,889 / 50,000 | 0.99778 | 100 | 500 |
| HMOG | nominal 5% | 49,753 / 50,000 | 0.99506 | 100 | 500 |
| HMOG | nominal 1% | 9,088 / 50,000 | 0.18176 | 100 | 302 |
| McGill | reference | 1,456 / 2,000 | 0.72800 | 18 | 18 |
| McGill | nominal 5% | 1,369 / 2,000 | 0.68450 | 18 | 18 |
| McGill | nominal 1% | 1,001 / 2,000 | 0.50050 | 17 | 17 |

## Numerical claim map F: Guarded gate activity and initialization

Exact state/path filter: `gate_diagnostics.csv`, `strategy=boundary`, `K=8`, plus dataset and condition. `gate_stricter_state_fraction` and `tau_auth_ge_mu_fraction` are state-weighted over `gate_states`. `accepted_blocked_by_gate_rate` divides the count of authenticated-but-not-updated observations by all presented poisoning observations (\(n_{paths}\times8\)), not by accepted observations. `mean_MUR` is an unweighted path mean. Initial \(k<0\) fractions are merged from all cohort-F profiles and must not be described as eligibility-conditioned attack-state fractions.

| Dataset | Condition | Paths | Gate states | Strict-state fraction | `tau_auth >= mu_enroll` state fraction | Authenticated-but-blocked / all presented | Path-mean Guarded MUR | All-profile \(k<0\) fraction (denominator) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| HMOG | reference | 49,889 | 399,112 | 1.000000 | 0.000000 | 392,981 / 399,112 = 0.984638 | 0.015362 | 0.000 (0/500) |
| HMOG | nominal 5% | 49,753 | 398,024 | 0.500045 | 0.499955 | 111,814 / 398,024 = 0.280923 | 0.637509 | 0.494 (247/500) |
| HMOG | nominal 1% | 9,088 | 72,704 | 0.192245 | 0.807755 | 3,090 / 72,704 = 0.042501 | 0.750000 | 0.886 (443/500) |
| McGill | reference | 1,456 | 11,648 | 0.967720 | 0.032280 | 8,915 / 11,648 = 0.765367 | 0.234633 | 0.050 (1/20) |
| McGill | nominal 5% | 1,369 | 10,952 | 0.736852 | 0.263148 | 4,408 / 10,952 = 0.402484 | 0.504657 | 0.250 (5/20) |
| McGill | nominal 1% | 1,001 | 8,008 | 0.134865 | 0.865135 | 491 / 8,008 = 0.061314 | 0.620380 | 0.750 (15/20) |

The gate algebra is descriptive of the already executed rule:

\[
\text{update allowed}=\text{authentication accepted}\;\land\;s\geq\tau_{\mathrm{update,raw}},
\]
\[
\tau_{\mathrm{update,raw}}=\tau_{\mathrm{auth}}+\lambda(\mu_{\mathrm{enroll}}-\tau_{\mathrm{auth}}),
\qquad
\tau_{\mathrm{update,effective}}=\max(\tau_{\mathrm{auth}},\tau_{\mathrm{update,raw}}).
\]

For the tested \(\lambda\ge0\), the additional effective margin is
\(\lambda\max(\mu_{\mathrm{enroll}}-\tau_{\mathrm{auth}},0)\). Thus it is zero when \(\tau_{\mathrm{auth}}\ge\mu_{\mathrm{enroll}}\). Gate inactivity, similar final ASR, and identical trajectories are distinct propositions.

## Numerical claim map G: victim-by-source robustness scope

Exact filter: `two_way_sensitivity.csv`, `dataset=HMOG`, `condition=far_1pct`, `strategy=boundary`, `K=8`. This secondary product-weight bootstrap is available only for the primary sensitivity condition. It uses 100 victims, 9,088 paths, 100 observed impostor sources, and 10,000 valid draws.

| Contrast | Exact effect [95% CI], pp | Displayed effect [95% CI], pp |
|---|---|---|
| Blind EMA − Frozen post-ASR | -0.447472 [−0.515142, −0.383425] | -0.447 [−0.515, −0.383] |
| Guarded EMA − Blind EMA post-ASR | -0.008945 [−0.021966, −0.001324] | -0.009 [−0.022, −0.001] |
| Guarded EMA − Frozen post-ASR | -0.456418 [−0.522305, −0.395239] | -0.456 [−0.522, −0.395] |

This analysis resamples observed victims and impostor-source identities but does not include classifier-training or broader population uncertainty. It must not be generalized to other operating points, McGill, or the historical reference run.

## Historical versus sensitivity reference CI

| Reporting context | Cohort/estimand/weighting | Point estimate | Bootstrap | Authoritative CI |
|---|---|---:|---|---|
| Historical HMOG reference section | D: 49,889 reference boundary-\(K=8\)-feasible paths; victim effect after repeat-within-fold and fold-within-victim averaging | +31.037638 pp | 10,000 percentile draws, direct seed 4242 | [+26.946230, +35.202592] pp (`paper/hmog_primary_poisoning_bootstrap.csv`) |
| New sensitivity table, reference row | C at reference: same 49,889 paths; same estimand and hierarchical weighting | +31.037638 pp | 10,000 percentile draws, key-derived seed from master 20261004 | [+26.966964, +35.106318] pp (`paired_effects_bootstrap.csv`) |
| Historical McGill reference section | D: 1,456 reference boundary-\(K=8\)-feasible paths; repeat mean within each of 18 victims | +19.721769 pp | 10,000 percentile draws, protocol seed 20261003 with contrast-specific deterministic offset | [+5.579173, +37.344069] pp (`results/paper3_external_mcgill_20261003_v1/paired_effects.csv`) |
| New McGill sensitivity table, reference row | C at reference: same 1,456 paths; same estimand and victim weighting | +19.721769 pp | 10,000 percentile draws, key-derived seed from master 20261004 | [+5.498731, +37.240872] pp (`paired_effects_bootstrap.csv`) |

For HMOG, the 100 victim effects agree to floating-point tolerance (maximum absolute difference \(5.68\times10^{-14}\) pp). Across both datasets, the reproduced point estimate, eligible cohort, estimand, weighting, resample count, and percentile procedure match their historical counterparts. The small CI differences are attributable to Monte Carlo resampling under different deterministic random streams, not to changed effects or cohorts. Historical sections retain HMOG [+26.95, +35.20] and McGill [+5.58, +37.34]; the sensitivity table consistently uses HMOG [+26.97, +35.11] and McGill [+5.50, +37.24]. No interval is selected for width.

## Protocol facts used in Methods

These are non-outcome claims, with sources `experiments/paper3_operating_point_sensitivity.md`, its JSON companion, and the executed runner:

- Frozen HMOG and McGill score caches were reused; models and scores were not regenerated.
- Reference, nominal-5%, and nominal-1% calibration conditions were evaluated.
- HMOG reference used the canonical approximate-EER rule; McGill reference used minimum pooled HTER with a higher-threshold tie break.
- Target calibration used only original validation/enrollment impostor observations. Candidate thresholds were the reference threshold plus `nextafter(v,+infinity)` for unique impostor scores \(v\), restricted to candidates no lower than reference; the smallest finite candidate satisfying pooled empirical FAR at or below the target was selected. Tied impostor scores crossed the boundary together. Day-2/test scores were excluded from calibration.
- Enrollment mean and second moment remained fixed. For each recalibrated threshold, claimant-specific \(k=(\mu_0-\tau_0)/\sigma_0\) was recomputed and not clipped; \(\alpha=0.05\), \(\lambda=0.25\), and the canonical sigma/floor behavior were fixed.
- Pool semantics, attack seed 4242, 100 repeats, and nested budgets were fixed. Random sequences were threshold-independent. Boundary candidates were operating-point-specific (`score >= tau0`) and ranked by non-negative initial margin.
- Within a condition, methods received matched poisoning sequences and probe pools. Profiles were frozen after poisoning before future ASR/FRR evaluation.
- Boundary curves used their condition-specific common \(K=8\)-feasible cohort. Random summaries used all structurally valid paths. Legacy reference reproduction retained its separate historical cohort rules.
- Victim-bootstrap intervals condition on fixed models and observed pools. Source-specific records and the two-way robustness analysis exist only for HMOG nominal 1%, boundary \(K=8\).

## Figure provenance and placement

The main sensitivity figure is the existing frozen `figures/boundary_k8_effects.pdf` (and PNG) from the sensitivity package. Its post-run revision intentionally leaves operating-point-specific conditional effects as unconnected points. The calibration-versus-held-out FAR figure and gate-diagnostic/feasibility figures are supplementary because the main text already contains OP-A/OP-B tables and the diagnostics have heterogeneous denominators. No frozen figure is overwritten.
