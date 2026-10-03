# Paper 3 operating-point sensitivity protocol

**Inferential label:** Prospectively specified operating-point sensitivity analysis on previously inspected score caches.

**Frozen:** 2026-10-04, before inspection of the new 5% and 1% sensitivity outcomes.

This is a sensitivity analysis of the already studied profile-poisoning mechanism. It is not an untouched confirmatory experiment, independent external validation, or externally preregistered study. HMOG and McGill outcomes from the reference operating points were inspected previously.

## Scope and immutable inputs

No model is trained and no score is regenerated. The experiment reads only the frozen HMOG validation/test score caches and the frozen McGill Day-1 enrollment/Day-2 score cache listed in the JSON companion to this protocol. Existing result packages and freeze tags are read-only.

The datasets are HMOG and McGill. The methods are Frozen, Blind EMA, and Guarded EMA with `lambda=0.25`. EMA `alpha=0.05`, the canonical sigma floor, profile equations, comparison `score >= threshold`, attack strategies (`random`, `boundary`), budgets (`K={0,1,2,4,8}`), 100 repeats, pool construction, and master attack seed 4242 remain unchanged.

## Operating points and calibration

Each claimant/fold has three conditions:

1. `reference`: HMOG approximate-EER threshold from the canonical ROC rule; McGill minimum-HTER threshold with the original high-threshold tie break.
2. `far_5pct`: nominal pooled empirical calibration FAR target 0.05.
3. `far_1pct`: nominal pooled empirical calibration FAR target 0.01.

HMOG uses its original validation scores. McGill uses Day-1 enrollment/calibration scores and not the early-stopping validation partition. Day-2/test scores are never passed to threshold calibration.

For target `beta`, let `I` be all calibration impostor observations pooled with equal observation weight and let `tau_ref` be the reference threshold. Candidates are

`{tau_ref} union {nextafter(v,+infinity): v is a unique float64 value in I and nextafter(v,+infinity) >= tau_ref}`.

The selected threshold is the smallest finite float64 candidate satisfying `mean(I >= threshold) <= beta`. If `tau_ref` already satisfies the target, it is retained. Ties in impostor scores therefore cross the decision boundary together. Thresholds are not rounded. Calibration FAR/FRR use pooled observation weights; the number of distinct impostor identities and the resolution `1/n_impostor_observations` are reported. Nominal calibration targets are not interpreted as held-out FAR guarantees.

The genuine enrollment mean and second moment are unchanged. For every new threshold, canonical initialization recomputes `k=(mu0-tau0)/sigma0`; `k` is fixed thereafter. Negative `k` is retained. HMOG preserves its canonical non-negative derived-threshold floor; McGill preserves its canonical unfloored derived threshold.

Guarded EMA uses the existing two-condition rule:

`score >= tau_auth` and `score >= tau_auth + lambda*(mu_enroll-tau_auth)`.

Thus the effective update threshold is the maximum of the authentication and raw update thresholds. No margin floor or alternative anchor is introduced when `tau_auth >= mu_enroll`.

## Pools, attacks, and cohorts

Pools are constructed once per dataset/fold/victim/repeat before operating-point-specific eligibility is evaluated. HMOG keeps whole `(source identity, session)` groups disjoint between poison and probe pools. McGill keeps source identities disjoint and uses the first temporal half of poison identities and the second temporal half of probe identities. Pool identifiers are hashes of ordered indices and must be identical across operating points.

Random sequences are sampled once per path, without replacement, independently of thresholds. Boundary sequences are condition-specific: candidates satisfy `score >= tau0` and are ordered by smallest non-negative initial margin, with index as deterministic tie break. Budgets are nested prefixes. All methods within a condition receive the same sequence, order, probes, and initial threshold.

The planned cohort begins with all 5x100x100 HMOG fold/victim/repeat paths and all 20x100 McGill victim/repeat paths that satisfy the unchanged structural pool requirements. Random results use every structurally valid path. Boundary curves at every K use the operating-point-specific common K=8-feasible cohort. Separately, feasibility for K=1,2,4,8 is reported over the full planned cohort. A zero-feasibility condition has missing conditional estimates and confidence intervals, never zero-valued ASR.

Reference reproduction uses the authoritative historical cohort definitions: HMOG uses the legacy common boundary-K=8-feasible cohort for both random and boundary; McGill uses all valid random paths and the K=8-feasible boundary cohort. Reproduction is checked before any 5%/1% outcome is computed.

## Endpoints and diagnostics

The primary new contrast is HMOG `far_1pct`, boundary K=8, Blind EMA minus Frozen post-poison ASR. The key secondary contrast is Guarded EMA minus Blind EMA on the identical eligible paths. The 5% target, reference condition, McGill, random attack, and smaller budgets are secondary.

Stored endpoints include calibration FAR/FRR and profile initialization; full-path pre-poison Frozen FAR/FRR/HTER; post-poison ASR, FRR, HTER, poison acceptance, malicious update count/rate, and mean/sigma/threshold displacement; three paired method contrasts; K-specific feasibility; and update-gate diagnostics. A Guarded pre-observation state is called *strict* when its effective update threshold is greater than its authentication threshold. We report initial gate width, counts/fractions of poisoning states with `tau_auth >= mu_enroll`, strict-gate states, and authenticated observations blocked by the gate.

Source-specific accepted/total held-out probe counts are stored for the primary HMOG 1% boundary K=8 comparison, if feasible. Their sums must reproduce path-level ASR.

## Statistical analysis

Rates in granular Parquet files are fractions; summary CSV rates/effects are percentage points. For HMOG, repeats are averaged within victim/fold and fold means are then averaged within victim. For McGill, repeats are averaged within victim. The victim is the resampling unit for 10,000-draw percentile paired bootstrap confidence intervals. Folds and repeats are not treated as independent subjects. An estimable condition with fewer than 10 eligible victims is labelled sparse/descriptive; a condition with no paired victims has no CI.

The prespecified source sensitivity analysis for the primary comparison uses an independent product-weight bootstrap. Each draw resamples eligible victim identities and observed impostor-source identities independently with replacement. Their multinomial multiplicities weight source accepted/total counts within each path; source-weighted path rates are then aggregated with the same repeat-within-fold, fold-within-victim, and equal-victim weighting as the primary analysis. Draws in which a path has zero weighted probe denominator omit that path; a draw with no paired victim estimate is missing. This analysis is secondary and does not account for training/model uncertainty.

Bootstrap seeds are derived deterministically from master seed 20261004 and stable SHA-256 hashes of analysis keys. No p-value search, cross-target paired interpretation, or target selection is performed.

## Reference gate and technical stopping rules

Authoritative reference endpoints are read from the frozen packages, never from this protocol. HMOG fold-level common-cohort endpoints and McGill path-level endpoints must match within absolute tolerance `1e-9` in their exported units, with identical reference path counts. If either check fails, the run stops before computing new sensitivity outcomes and writes a discrepancy report.

The run also stops before sensitivity outcomes for a missing/hash-mismatched cache, unresolved split semantics, leakage, failed invariant test, or equation mismatch. It does not stop for a null effect, loss of Guarded benefit, boundary infeasibility, negative `k`, or mismatch between nominal and held-out FAR.

## Preservation

The full run writes a new, non-overwriting result directory. Its manifest records cache, protocol, and source hashes; code revision; seeds; schemas; cohort definitions; exclusions; and reference status. Compressed Parquet contains path and source contribution data required to recompute statistics. Any file too large for ordinary Git is retained as an immutable local artifact with its SHA-256 recorded; the compact summaries, manifest, code, protocol, and report remain in Git. No manuscript file is updated by this run.
