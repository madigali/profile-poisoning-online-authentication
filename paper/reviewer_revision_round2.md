# Reviewer Revision Round 2

Revision date: 4 October 2026.

## 1. Scope and procedural status

Reviewer Revision Round 2 integrates the frozen operating-point sensitivity package into the manuscript and Supplement. No model was trained; no score, partition, candidate sequence, trajectory, bootstrap, operating point, endpoint, or method variant was generated. Frozen CSV/Parquet files, manifests, protocol files, historical audits, notes, and tags were not modified.

The required source-and-cohort map was created before manuscript editing in `paper/operating_point_integration_audit.md`. It verifies the package hashes, distinguishes six cohort/denominator types, records exact row filters for every included numerical claim, and reconciles historical and sensitivity confidence intervals.

The sensitivity stage is described throughout as a **prospectively specified sensitivity analysis on previously inspected score caches**. It is not called an untouched confirmatory experiment or external preregistration. Its primary contrast—HMOG nominal 1%, boundary \(K=8\), Blind EMA minus Frozen post-poison ASR—does not retroactively replace the historical HMOG reference reporting contrast.

## 2. Substantive claim revisions

| Location | Old claim or risk | Revised claim/action | Supporting source | Scope limitation |
|---|---|---|---|---|
| Abstract; Introduction; Results 4.8; Discussion 5.1; Conclusion | “Blind EMA is vulnerable to poisoning and Guarded suppresses it” could be read as operating-point invariant. | Accepted impostors can alter adaptive state, but the magnitude and direction of post-poison ASR and the additional Guarded restriction depend on the recalibrated policy and its feasible attack paths. | `paired_effects_bootstrap.csv`; `eligibility_summary.csv` | The nominal-1% reversal is for the tested score-informed boundary strategy, not all poisoning attacks. |
| Results 4.1–4.2 | Reference amplification and Guarded suppression were presented without a local operating-point qualifier. | Headings and prose now label these as reference-operating-point findings. Historical HMOG/McGill estimates and historical CIs are preserved. | Historical HMOG/McGill frozen packages; Round-1 audit | Reference effects remain valid within their original cohorts; they are not deployment-security claims. |
| Abstract; Introduction contribution 3; Results 4.3; Conclusion | The paper previously said low-FAR performance was not evaluated. | The manuscript now reports reference, nominal-5%, and nominal-1% calibration conditions and states that effect direction was not invariant. | Frozen operating-point report and summary CSVs | Nominal targets are calibration constraints, not universal standards or held-out guarantees. |
| Methods 3.3; Related Work 2.2/2.5; Discussion 5.4 | Guarded was described as a generally stricter second threshold. | The exact conjunction, raw threshold, effective maximum, and margin \(\lambda\max(\mu_{\mathrm{enroll}}-\tau_{\mathrm{auth}},0)\) are given. The gate adds no margin when \(\tau_{\mathrm{auth}}\geq\mu_{\mathrm{enroll}}\). | Executed runner and frozen protocol | This is algebraic clarification of the original rule; no margin floor, clipping, anchor, or \(\lambda\) change was introduced. |
| Methods 3.6; Results 4.3; Discussion 5.2 | A threshold-only interpretation could imply that changing \(\tau_0\) caused the reversal. | Recalibration is described as changing \(\tau_0\), claimant-specific \(k\), boundary candidates, and condition-specific feasible paths. | Protocol, calibration CSV, eligibility CSV | The design does not isolate the causal contribution of any one component; negative \(k\) is not asserted as the sole cause. |
| Results 4.3; Discussion 5.2/5.8; Conclusion | A negative ASR effect might be read as harmless or beneficial poisoning. | The same HMOG nominal-1% boundary cohort now reports Blind-minus-Frozen FRR +6.89 pp and HTER +3.22 pp with CIs. | `operating_point_summary.csv`; `paired_effects_bootstrap.csv` | This is an adverse genuine-rejection outcome, not a separately designed or demonstrated denial-of-service attack. |
| Results 4.3; Discussion 5.3; Limitations | Full held-out and conditional boundary baselines could be mixed. | OP-A and OP-B use separate tables, cohort notes, and denominators. HMOG 1.04% full FAR is not used as the baseline for the −0.447-pp conditional effect; its boundary-cohort baseline is 0.826%. | `operating_point_summary.csv`; `eligibility_summary.csv` | Cross-target rows are not treated as paired causal trajectories. |
| Results 4.3; Discussion 5.4 | Equal McGill nominal-1% Blind/Guarded ASR could be read as method equivalence. | The text states that aggregate ASR was equal while MUR differed (69.36% versus 62.32%); identical trajectories are not claimed. | Operating summary and paired-effects CSV | Equal endpoint estimates do not establish identical state paths. |
| Introduction contribution 6; Results 4.7–4.8; Discussion 5.9 | McGill was described as reproducing the main poisoning direction without an operating-point qualifier. | McGill is now a replication of the reference-point directions, followed by a sensitivity result showing that they do not persist unchanged after recalibration. | Historical McGill package; operating-point package | McGill remains a small mechanism-level replication, not benchmark validation. |
| Methods 3.9; Results 4.6; Discussion 5.7 | TQ-v2 and Quantile details dominated the main narrative. | Main text retains motive, criteria/status, TQ-v1 outer result, validation stopping, and absence of outer estimates. Detailed state machines, grids, equations, and fold diagnostics moved to Supplement. | Frozen TQ/Quantile packages and manifests | Relocation does not change protocol status or hide negative results. |
| Methods 3.10; Results 4.3; Limitations | Historical lack of source identities could be read as applying to all analyses. | The historical source-level limitation is retained, while the new victim-by-source result is reported only for HMOG nominal 1%, boundary \(K=8\). | `two_way_sensitivity.csv`; historical inference-data audit | No two-way result is claimed for reference, nominal 5%, McGill, or training uncertainty. |

## 3. Claims preserved

- Accepted impostor observations can modify an adaptive profile state.
- Accepted-only eligibility excludes rejected genuine observations from the learning stream.
- The historical HMOG and McGill reference conditions show large positive Blind-minus-Frozen boundary effects and substantial Guarded suppression toward Frozen.
- The score-informed boundary benchmark is not a demonstrated binary-feedback-only attack, and \(K\) excludes reconnaissance and candidate screening.
- Oracle-all changes genuine tracking but is label-aware, non-deployable, and accompanied by higher FAR.
- TQ-EMA v1 did not meet its late-FRR recovery criterion.
- TQ-EMA v2 and Adaptive Quantile stopped at validation; their outer scores were not loaded and no outer estimates exist.
- The study does not claim a universal solution, a universal impossibility result, or deployment-grade security.

## 4. Sensitivity results retained in the main paper

The main paper now contains:

1. OP-A: achieved calibration FAR and full-cohort held-out Frozen FAR/FRR for both datasets at reference, nominal 5%, and nominal 1%.
2. OP-B: boundary-\(K=8\) Blind-minus-Frozen and Guarded-minus-Blind ASR effects, victim-bootstrap CIs, paths, victims, and HMOG victim-fold units.
3. Same-cohort HMOG nominal-1% Frozen/Blind ASR, FRR, and HTER plus paired FRR/HTER effects.
4. Nominal-1% feasibility counts and explicit exclusion semantics.
5. State-weighted strict-gate diagnostics and all-profile initial-\(k\) diagnostics with separate denominators.
6. The source-level robustness result only in its available HMOG nominal-1% scope.
7. The existing frozen `boundary_k8_effects` figure as the principal operating-point figure.

The existing calibration-transfer, boundary-feasibility, and gate-diagnostic figures are assigned to Supplementary Results because they use heterogeneous calibration, planned-path, state, and claimant-profile denominators.

## 5. Material moved to the Supplement

`paper/supplementary_methods.md` now contains the complete TQ-EMA v1 state transitions and validation grid, the TQ-EMA v2 recovery-episode controller, the Adaptive Quantile equations and initialization, and branch-specific inference/reproducibility detail.

`paper/supplementary_results.md` contains TQ-v1 absolute outer endpoints and secondary bootstrap, fold-selected v1 configurations, the fold-specific TQ-v2 validation table, the Quantile validation diagnostics, a stopped-branch status table, and the three operating-point diagnostic figure placements. Main Results retains the negative decisions and absence of outer estimates.

## 6. Abstract revision

The Abstract remains centered on the coupled malicious-inclusion/genuine-censoring mechanism. It preserves the HMOG and McGill reference amplification, adds the nominal-1% mean sign reversal, distinguishes full-cohort high FRR from conditional boundary effects, reports the same-cohort HMOG FRR/HTER deterioration, and narrows Guarded to a state-dependent reference-point result. It contains 299 words by `wc -w`, within the 250–300-word editorial target.

## 7. Location of required clarifications

| Required item | Main location | Additional detail |
|---|---|---|
| Operating-point-specific \(k\) | Methods 3.6 | Integration audit; Discussion 5.2 |
| Effective Guarded margin | Methods 3.3 | Related Work 2.2; Discussion 5.4; Supplementary Methods S2 |
| Post-poison FRR/HTER | Results 4.3, same-cohort block | Abstract; Discussion 5.2/5.8; Conclusion |
| Boundary feasibility | Results 4.3, feasibility block and OP-B | Supplementary Fig. S2; Limitations |
| Different cohorts | Methods 3.6; OP-A/OP-B notes | Integration audit cohort map; Discussion 5.3/5.11 |
| Nominal versus held-out FAR | Methods 3.6; OP-A | Abstract; Discussion 5.2; Conclusion; Supplementary Fig. S1 |

## 8. Confidence-interval reconciliation

Historical reference sections retain their historical authoritative CIs: HMOG Blind-minus-Frozen [+26.95, +35.20] pp and McGill [+5.58, +37.34] pp. OP-B uses the sensitivity package consistently, including HMOG [+26.97, +35.11] and McGill [+5.50, +37.24].

For HMOG, the historical and sensitivity analyses use the same 49,889 paths, estimand, hierarchy, 100 victim effects, 10,000-draw percentile procedure, and +31.037638-pp point estimate. Victim effects match to a maximum absolute difference of \(5.68\times10^{-14}\) pp. McGill likewise retains the same 1,456 paths, 18 victims, weighting, and +19.721769-pp estimate. The small interval differences come from different deterministic bootstrap random streams (historical HMOG seed 4242; historical McGill master seed 20261003; sensitivity master seed 20261004 with key-derived streams). No interval was selected for width and no bootstrap was rerun.

## 9. Remaining unresolved questions

- Cross-target contrasts are not isolated threshold effects because \(k\), boundary candidates, and feasible cohorts change together.
- The nominal-1% boundary result does not establish robustness to other attacker strategies or query processes.
- High strict-condition FRR limits practical interpretation, and nominal calibration FAR does not guarantee held-out FAR.
- The original Guarded anchor is inactive in a large share of strict-condition states; no revised gate was designed or tested in this revision.
- Training/model and population uncertainty remain outside the victim and limited victim-by-source bootstraps.
- McGill remains small and has severe cross-day degradation.
- Larger untouched longitudinal evaluation remains necessary.

## 10. Files changed and word counts

Updated manuscript files:

- `paper/abstract.md`
- `paper/introduction.md`
- `paper/related_work.md` (technical claim alignment only)
- `paper/methods.md`
- `paper/results.md`
- `paper/discussion.md`
- `paper/conclusion.md`
- `paper/manuscript_full.md`
- `paper/evidence_hierarchy.md`

Created files:

- `paper/operating_point_integration_audit.md`
- `paper/reviewer_revision_round2.md`
- `paper/supplementary_methods.md`
- `paper/supplementary_results.md`

Word counts (`wc -w`):

| Section/file | Words |
|---|---:|
| Abstract | 299 |
| Introduction | 1,305 |
| Related Work | 1,848 |
| Methods | 4,515 |
| Results | 2,166 |
| Discussion | 3,409 |
| Conclusion | 670 |
| Main scientific sections total | 14,212 |
| Assembled `manuscript_full.md` including captions and references | 14,728 |
| Supplementary Methods | 1,015 |
| Supplementary Results | 856 |

## Final self-check

- Sensitivity reversal is explicit in Abstract, Results, Discussion, and Conclusion.
- Historical reference results remain present and retain their authoritative intervals.
- McGill reference is identified as minimum HTER, not EER.
- Nominal FAR is not presented as guaranteed held-out FAR or a universal deployment standard.
- Full-cohort and conditional boundary values are separated.
- Same-cohort HMOG nominal-1% FRR/HTER deterioration is reported.
- Equal McGill nominal-1% ASR is not called full method equivalence.
- Guarded algebra matches the executed conjunction and effective threshold.
- Negative \(k\) is not asserted as the sole cause of the reversal.
- Gate, path, victim, victim-fold, and claimant-profile denominators are identified separately.
- Infeasible paths are exclusions, not zero-ASR outcomes.
- Lower ASR is not called harmless adaptation, general robustness, or a successful availability attack.
- The sensitivity stage is not called untouched confirmation.
- TQ/Quantile negative outcomes and no-outer status are preserved.
- No frozen result package, manifest, tag, or historical audit was modified.
