# Research Notes and Decision Log

## Provenance snapshot

- Created from the ChatGPT project “q1 second article” and the linked conversation “Перенос проекта в Codex”.
- The synced `sources/` directory was empty at creation time.
- A local prototype named `paper3_poisoning_attack_v2.py` supplied protocol details, but its required canonical module and score cache were not present.
- Paper 1 and Paper 2 were subsequently audited against their primary PDFs,
  Paper 1 supplementary materials, and the canonical Paper 2 code/results on
  2026-10-03.  The authoritative record is
  [`paper/paper1_paper2_fact_check.md`](paper1_paper2_fact_check.md).

## Primary-source-verified prior-work context

- Project-level dissertation focus, retained as context rather than as a claim
  established by either paper: behavioral-biometric continuous authentication
  for mobile devices with an intelligent personal agent.
- Paper 1 is a systematic review of 80 included works: 53 empirical/system-level
  studies and 27 reviews.  It identifies gaps in standardized adversarial
  evaluation, joint adversarial/privacy pipeline testing, longitudinal and
  ecologically valid evidence, empirical BBCA–IPA integration, and
  user-centered privacy/consent evaluation.  “No study” statements apply to
  the review's searched corpus and protocol.
- Paper 2 evaluates 100-subject, closed-set HMOG verification using only the
  physical accelerometer and gyroscope axes.  Linear SVM, random forest, and
  LSTM receive the same non-overlapping 10-second endpoint under a
  leakage-resistant, session-disjoint protocol with fitting-only scaling.
- Under that protocol, the prespecified accepted-only EMA did not outperform
  the validation-calibrated frozen threshold: HTER was `23.19%` Frozen versus
  `24.53%` EMA at `D=0`, and `24.89%` versus `26.39%` at `D=2`.
- Paper 2's label-blind rule allows an accepted impostor score to update the
  profile, establishing a poisoning pathway but not a dedicated poisoning
  attack result; Paper 3 supplies the attack experiment.
- Paper 2 evaluates global synthetic standardized-feature shift at
  `D={0,1,2}` using one direction per fold, applied to all test samples.  It is
  a sensitivity analysis, not natural behavioral drift.

## Decisions made for this scaffold

### D001 — Separate authentication from update authorization

An accepted sample is not automatically trusted for adaptation. The defense uses a second update policy.

### D002 — Working method name

Use “Trusted Quarantine EMA (TQ-EMA)” until the final algorithm is fixed and checked against naming conflicts in the literature.

### D003 — Held-out attack measurement

Poisoning candidates and future probes must be separated before candidate selection. Whole source identity-session groups cannot cross pools.

### D004 — Do not overclaim identity disjointness

Grouping by `(identity, session)` prevents session-group leakage but may place different sessions from one identity in both pools. An identity-disjoint sensitivity analysis should be considered.

### D005 — Primary endpoint candidate

Paired difference in `Delta ASR` between TQ-EMA and Blind EMA for the boundary attack at maximum preregistered `K`. Freeze this choice before final results.

### D006 — Guarded EMA gate experiment

Before implementing quarantine/TQ-EMA, evaluate a single confidence gate while
holding the attack-v2 protocol fixed.  Authentication uses the current adaptive
threshold `T_auth`; update authorization uses
`T_update = T_auth + lambda * (mu_enroll - T_auth)` for
`lambda = {0.00, 0.25, 0.50, 0.75, 1.00}`.  `mu_enroll` is the fixed mean of
the validation genuine enrollment scores, while `T_auth` is recomputed from the
current EMA state before each observation.  Guarded `lambda=0` must reproduce
Blind EMA exactly.

The attack phase remains malicious-only and the state is frozen before
post-poison ASR/FRR evaluation, matching attack v2.  Because this stream contains
no genuine update opportunities, GUR is measured in a separate chronological
clean replay on a copy of each post-poison state.  GUR is the number of genuine
samples incorporated divided by all genuine samples presented in that replay.
The replay does not affect post-poison ASR, FRR, HTER, or poisoning-state
deltas.  Thus GUR measures update availability, not longitudinal drift-recovery
utility; drift utility requires a later dedicated experiment.

### D007 — Guarded EMA exploratory run completed

Date: 2026-09-30  
Run: `results/20260930-guarded-full-r100/`  
Status: complete, exploratory

The run used the unchanged attack-v2 settings: five folds, 100 repeats, seed
4242, 50% group-disjoint probe allocation, random and boundary attacks, and
budgets `K={0,1,2,4,8}`.  Its Frozen and Blind fold-level outputs were checked
against the existing `paper3_attack_v2_by_fold.csv` and matched exactly.
Guarded `lambda=0` matched Blind EMA exactly in all granular rows.  Oracle and
Frozen matched exactly for post-poison security metrics and profile state.

Observed exploratory pattern: the gate sharply reduced malicious updates and
post-poison ASR, while GUR decreased monotonically as lambda increased.  Do not
select a confirmatory lambda from this held-out test run.  A final lambda must
be prespecified or selected on training/validation data, and GUR must not be
presented as drift-recovery utility.

### D008 — Guarded clean-drift protocol

Date: 2026-09-30  
Status: frozen before inspecting clean-drift results

Evaluate `D={0,1,2}` in two explicitly separate scenarios:

1. `global`: genuine adaptation/probes and impostor probes use the same drifted
   score cache.  This reuses the Paper 2 synthetic transformation, although the
   new disjoint checkpoint evaluation is not the Paper 2 alternating stream.
2. `claimant_only`: genuine adaptation/probes use the drifted score cache while
   impostor probes use `D=0` scores.  This isolates movement of the claimant
   distribution from artificial movement of the impostor distribution.

For each subject/fold, order sessions chronologically.  Within every complete
test session pair, use the `within=0` sequence as adaptation-only, update the
profile if authorized, and then use the disjoint `within=10` sequence as a
non-updating genuine checkpoint.  At the same profile state, measure impostor
FAR from other identities at the same session number and `within=10`, macro-
averaging source identities.  Require at least four complete pairs.  Early
FRR/FAR use the first two session checkpoints and late FRR/FAR use the last two;
an optional middle checkpoint contributes to the trajectory but not early/late
summaries.  HTER uses temporally matched late FRR and late FAR.

Primary clean utility is `Frozen late FRR - method late FRR`; positive values
mean useful adaptation.  Also report `Frozen HTER - method HTER`, GUR, and
profile displacement.  Guarded EMA uses `lambda=0.25` as an exploratory
carry-forward from the poisoning experiment, not as a confirmatory parameter.

Do not treat folds as independent replicates.  Report fold summaries as
descriptive only.  For uncertainty, first average each subject across folds and
then use a paired subject bootstrap against Frozen.  Do not create Monte Carlo
repeats for this deterministic clean-stream experiment.  FAR/HTER subject-only
bootstrap intervals are approximate because claimant and impostor-source
identities are crossed; a two-way bootstrap is reserved as a sensitivity
analysis before confirmatory claims.

### D009 — Guarded clean-drift exploratory result

Date: 2026-09-30  
Run: `results/20260930-guarded-drift-full/`  
Status: complete, exploratory

The clean-drift experiment did not establish useful online adaptation under
the current score-level EMA.  Blind/Oracle EMA had essentially no late-FRR gain
at `D=0`, negative mean gain at `D=1`, and a small uncertain positive mean gain
at `D=2`.  Guarded EMA with `lambda=0.25` reduced matched-checkpoint FAR but
increased late FRR at every drift level.  Its mean late-FRR adaptation gains
were negative, and the paired subject-bootstrap intervals were below zero.

The mechanism is consistent with selection bias: the confidence gate admits
only higher-score genuine observations, moves the threshold upward more than
Blind EMA, and therefore reduces FAR while worsening genuine rejection.  This
does not invalidate the poisoning result, but it means the current confidence
gate has demonstrated security value without demonstrated drift-adaptation
utility.  Do not claim that Guarded EMA retains useful adaptation on this
experiment.

One claimant (`sid=57`) lacked four complete session pairs in folds 4 and 5;
the same fold-level exclusions apply to every method, scenario, and drift
level.  The subject-level analysis still contains all 100 identities, with
that claimant averaged over three rather than five folds.  Nine distinct
guarded update states across five fold/drift/subject trajectories had a dynamic
authentication threshold at or above the fixed enrollment mean.  They appear
twice in exported counts because the genuine path is shared by the two
scenarios.  The separate authentication check kept the effective gate at least
as strict as authentication, and these states are explicitly counted.

### D010 — Oracle-all-genuine diagnostic

Date: 2026-10-01  
Status: frozen before inspecting Oracle-all results

Add a diagnostic `Oracle-all-genuine` control to the clean-drift experiment.
Unlike the existing accepted-only Oracle, it applies the canonical EMA moment
update to every ground-truth genuine adaptation candidate even when the
authentication decision is reject. Ground truth is used only for this
non-deployable upper-bound diagnostic. Checkpoint samples remain non-updating.

If Oracle-all provides a positive late-FRR gain, accepted-only selection bias
is the main limitation and temporal quarantine is justified. If Oracle-all
does not provide useful gain, the score-space EMA/threshold rule itself should
be redesigned before adding quarantine.

Save checkpoint trajectories for candidate/probe scores, profile mean, sigma,
authentication threshold, authentication decisions, and update events. Add a
complete-case sensitivity bootstrap using the 99 identities with all five
folds, alongside the primary all-subject bootstrap.

### D011 — Oracle-all-genuine result

Date: 2026-10-01  
Run: `results/20261001-oracle-all-drift-full/`  
Status: complete, exploratory

Oracle-all produced positive late-FRR gains at every drift level in the
claimant-only scenario: `+4.73`, `+5.10`, and `+6.60` percentage points for
`D=0,1,2`. Paired subject-bootstrap intervals excluded zero. The complete-case
99-subject sensitivity produced the same conclusion.

Oracle-all also increased late FAR by approximately `5.51`, `5.67`, and `6.08`
points. Consequently, HTER gains were small and their bootstrap intervals
included zero. The diagnostic therefore shows that the EMA moments can follow
lower genuine scores when accepted-only censoring is removed, but unrestricted
downward threshold movement creates a security cost.

This supports the selection-bias mechanism and justifies temporal quarantine
as the next method: lower but plausible observations require repeated temporal
evidence before a bounded update. It does not justify claiming that Oracle-all
is deployable or that unrestricted EMA improves overall HTER.

### D012 — TQ-EMA v1 clean-recovery protocol

Date: 2026-10-01  
Status: frozen before implementing TQ-EMA or inspecting its test results

The first deployable recovery method separates authentication trust from
adaptation evidence.  Production state contains only the canonical EMA mean,
second moment, derived sigma, and derived authentication threshold.  Quarantine
state contains scores, distinct session identifiers, a fixed downward direction,
and age.  Resetting quarantine cannot change production state.

For one session-level adaptation observation:

1. `score >= tau_update`: grant access and apply a bounded normal EMA proposal,
   where `tau_update = tau_auth + 0.25 * (mu_enroll - tau_auth)`.
2. `tau_auth <= score < tau_update`: grant access but do not update.
3. `tau_auth - b <= score < tau_auth`: deny access and admit the score only to
   the isolated recovery quarantine.
4. `score < tau_auth - b`: deny access, discard the score, and reset quarantine.

Recovery requires `m` consecutive, distinct session-level recovery candidates.
Every candidate must lie below the production mean captured when the quarantine
run began (the prespecified downward direction), and the batch range must not
exceed `r`.  Any intervening non-candidate resets the run.  A confirmed batch
uses its median as a robust target and proposes a small EMA moment update.  The
production mean and second moment are moved together; sigma and threshold are
then recomputed.  The threshold is never edited independently.

Both trusted and recovery proposals are scaled or rejected so that the accepted
transition obeys per-update `|Delta mu| <= c_mu`, per-update
`|Delta tau| <= c_tau`, and the enrollment anchor
`tau >= tau_enroll - A`.  A recovery proposal that does not lower the derived
threshold is rejected.  Thus all accepted states remain internally consistent.

All dimensional parameters use the fixed enrollment standard deviation for
that subject/fold.  The deliberately small validation grid is:

- recovery-band width `b / sigma_enroll in {0.25, 0.50, 0.75}`;
- temporal confirmation `m in {2, 3}` consecutive distinct sessions;
- recovery rate `alpha_recovery in {0.025, 0.050}`;
- anchor `A / sigma_enroll in {0.10, 0.25}`.

The remaining controls are fixed, not tuned: batch range
`r = 0.50 * sigma_enroll`, mean cap `c_mu = 0.10 * sigma_enroll`, threshold cap
`c_tau = 0.05 * sigma_enroll`, trusted-path lambda `0.25`, and canonical trusted
EMA alpha `0.05`.

Selection is nested within each outer fold.  Chronological validation session
pairs are split before tuning: the first two complete sessions initialize and
calibrate the inner profile, while the remaining sessions form the tuning
stream.  Drifted validation scores are generated from the saved fold model and
canonical synthetic-drift function without retraining.  Claimant scores use
`D=2`; impostor checkpoint scores use `D=0`.  Among configurations whose
validation subject-macro late-FAR increase over Frozen is at most `+1.0`
percentage point, choose the configuration with the largest validation
late-FRR gain.  Exact ties are resolved conservatively by preferring larger
`m`, narrower `b`, smaller recovery alpha, and the tighter anchor.  Parameters
are then frozen for that fold and applied once to its held-out test partition.

The `+1.0`-point FAR limit is a preregistered experimental security constraint,
not a universal acceptable-FAR standard.

The primary test scenario is claimant-only `D=2`.  The primary comparison is
TQ-EMA versus Frozen and the primary endpoint is
`Frozen late FRR - TQ late FRR`.  Success requires the lower endpoint of the
paired 95% subject-bootstrap interval to exceed zero and the mean late-FAR
increase to remain at most `+1.0` point.  Mean HTER degradation of at most
`+0.5` point is a secondary safety/utility constraint.  The all-available-fold
subject analysis is primary; the 99-subject complete-five-fold analysis must
preserve the conclusion.  A victim-by-impostor-source two-way bootstrap of FAR
is a secondary robustness analysis.

Clean claimant-only `D={0,1,2}` compares Frozen, Blind EMA, Guarded EMA
(`lambda=0.25`), Oracle-all-genuine, and TQ-EMA.  Oracle-all remains diagnostic
and non-deployable.  No poisoning stream is mixed into this first recovery
experiment.

### D013 — TQ-EMA v1 clean-recovery result

Date: 2026-10-01  
Run: `results/20261001-tq-clean-drift-full-v1-final/`  
Status: complete, preregistered v1 protocol; primary recovery criterion not met

Fold-specific TQ configurations were selected before loading each fold's test
scores.  The chosen configurations were:

- fold 1: `b0.25_m3_a0.025_A0.10`;
- fold 2: `b0.50_m2_a0.025_A0.10`;
- fold 3: `b0.25_m2_a0.050_A0.10`;
- fold 4: `b0.25_m3_a0.025_A0.10`;
- fold 5: `b0.25_m2_a0.025_A0.10`.

All selected configurations satisfied the validation `Delta FAR <= +1.0`
point constraint.  Validation late-FRR gains were `0.00`, `-0.50`, `-1.01`,
`0.00`, and `-2.00` points across folds, showing that this v1 grid did not
demonstrate positive recovery utility before the held-out test evaluation.

In the primary claimant-only `D=2` test, Frozen late FRR/FAR/HTER were
`32.53/22.86/27.70%`; TQ-EMA values were `33.43/20.92/27.18%`.  The paired
subject-macro late-FRR gain was therefore `-0.90` points with a 95% subject
bootstrap interval of `[-1.80, 0.00]`.  The primary recovery criterion was not
met.  The 99-subject complete-five-fold sensitivity gave the same conclusion
(`-0.91` points; lower interval endpoint `-1.92`).

TQ-EMA did satisfy the safety constraints.  Its late-FAR change relative to
Frozen was `-1.94` points (subject-bootstrap interval `[-2.46, -1.43]`), and
its HTER improved by `0.52` points (`[0.10, 0.94]`).  Independent victim and
impostor-source resampling produced nearly the same FAR estimate, `-1.94`
points, with interval `[-2.48, -1.42]`.  Thus v1 is conservative and improves
the balanced endpoint, but it cannot be claimed to restore legitimate
late-FRR adaptation relative to Frozen.

The trajectory and event audit explain the failure.  At `D=2`, TQ-EMA applied
`1,404` high-confidence trusted updates but only `49` confirmed recovery
updates.  Its mean threshold displacement remained positive (`+0.00155`),
whereas Oracle-all moved the threshold downward (`-0.00252`).  TQ-EMA improved
late FRR relative to Guarded EMA (`33.43%` versus `34.60%`) but did not reverse
the accepted-high-score selection bias enough to beat Frozen.

Implementation invariants passed: baseline rows exactly reproduced the prior
clean-drift run; recovery updates were triggered only by rejected observations
and never granted access; ordinary accepted observations below the update gate
did not update; every threshold transition respected its cap; every production
threshold respected the enrollment anchor; and no primary metric was missing.

Do not retune v1 on these test results.  A future v2 must be introduced as a
new protocol.  The most direct design question is how to keep the trusted
high-score path from overwhelming the much rarer recovery path (for example,
direction-aware balancing or suspension/rate limiting during a confirmed
downward episode), while retaining the poisoning protection already observed.

### D014 — TQ-EMA v2 recovery-episode protocol

Date: 2026-10-01  
Status: frozen before implementing v2 or inspecting v2 test results

TQ-EMA v2 changes exactly one design principle from v1: once a temporally
consistent downward recovery batch is confirmed, trusted high-score updates
that would move the profile in the opposite direction cannot dominate the
confirmed recovery evidence.  Authentication rules, access decisions,
quarantine isolation, robust median targets, moment consistency, per-transition
caps, and the enrollment anchor remain unchanged.

The production controller has two states:

1. `NORMAL`: identical to TQ-EMA v1.
2. `RECOVERY_DOWN`: entered after a v1-valid recovery batch of `m` consecutive,
   distinct session-level candidates is confirmed.  The confirmed batch first
   proposes the same bounded median-target recovery transition as v1.  Episode
   entry depends on confirmed temporal evidence, not on whether the bounded
   transition has nonzero remaining room under the anchor.

During `RECOVERY_DOWN`, authentication and access are unchanged.  Before a
trusted update is applied, v2 previews the canonical EMA moment proposal using
the normal trusted alpha.  If the proposal raises either the profile mean or
the derived authentication threshold, the trusted update is skipped entirely.
If both proposed mean and proposed threshold are non-increasing, the ordinary
v1 bounded transition is allowed.  No smaller recovery-specific trusted alpha
is introduced in v2.

An episode remains active for the next three distinct session-level adaptation
observations after confirmation.  A new confirmed recovery batch refreshes the
three-session horizon.  The horizon is fixed, not tuned.  When it expires the
controller returns to `NORMAL`.  Every non-candidate continues to reset the
quarantine evidence buffer exactly as in v1; resetting quarantine does not by
itself end an active recovery episode.

The v1 parameter grid is reused unchanged:

- `b / sigma_enroll in {0.25, 0.50, 0.75}`;
- `m in {2, 3}`;
- `alpha_recovery in {0.025, 0.050}`;
- `A / sigma_enroll in {0.10, 0.25}`;
- fixed `r=0.50 sigma`, `c_mu=0.10 sigma`, `c_tau=0.05 sigma`, trusted
  `lambda=0.25`, and normal trusted alpha `0.05`.

Selection remains fold-specific and validation-only.  To expose the episode to
a five-session trajectory, all clean `D=0` validation genuine and impostor
scores initialize/calibrate the profile, and the independently scored `D=2`
transformation of those validation sequences is replayed chronologically for
tuning; claimant scores use `D=2` and impostor checkpoints use `D=0`.  This is
a transparent synthetic validation replay, not an independent inner holdout.
It never reads an outer test score.

A validation configuration is feasible only if its subject-macro late-FAR
increase over Frozen is at most `+1.0` percentage point and its HTER degradation
is at most `+0.5` point.  Among feasible configurations, choose the largest
late-FRR gain.  Exact late-FRR ties prefer the configuration with the larger
suppressed-conflicting-trusted-update rate, then the larger recovery-update
rate, followed by the prior conservative ordering: larger `m`, narrower band,
smaller recovery alpha, and tighter anchor.  If no configuration is feasible,
selection fails closed.

The primary test scenario and success criteria remain unchanged: claimant-only
`D=2`, TQ-EMA v2 versus Frozen, lower endpoint of the paired 95% subject
bootstrap for late-FRR gain above zero, mean late-FAR change at most `+1.0`
point, HTER degradation at most `+0.5` point, and the same conclusion in the
99-subject complete-five-fold sensitivity.  The victim-by-impostor-source FAR
bootstrap remains secondary.  TQ-EMA v1 is replayed with its previously frozen
fold-specific selections for direct descriptive comparison.

Inferential limitation: the outer score caches have already been inspected for
v1, and the v2 mechanism is motivated by the v1 event audit on those caches.
Therefore the locked v2 run is an exploratory protocol-preserving comparison,
not a new independent confirmatory holdout.  A positive v2 result would require
confirmation on a new dataset, naturally later sessions, or another untouched
evaluation partition before a confirmatory claim.

### D015 — TQ-EMA v2 failed the validation gate

Date: 2026-10-01  
Run: `results/20261001-tq-v2-validation-gate-final-v2/`  
Status: validation failed; outer test not loaded

TQ-EMA v2 was implemented and its recovery-episode state machine passed the
combined v1/v2/drift unit suite.  The five-fold driver completed every
validation grid before attempting to load an outer test score.  Fold 4 had no
configuration satisfying both prespecified validation constraints, so the run
failed closed and no five-fold v2 test result was produced.

The fold-specific validation outcomes were:

- fold 1: 14 feasible configurations; selected
  `b0.25_m2_a0.025_A0.10`, late-FRR gain `-3.50` points, FAR change `-2.61`,
  HTER change `+0.44`;
- fold 2: 24 feasible; selected `b0.75_m2_a0.025_A0.10`, late-FRR gain
  `-1.50`, FAR change `-2.12`, HTER change `-0.31`;
- fold 3: 24 feasible; selected `b0.75_m2_a0.050_A0.10`, late-FRR gain
  `-1.01`, FAR change `-1.19`, HTER change `-0.09`;
- fold 4: zero feasible configurations.  The best late-FRR gain over the full
  grid was `-4.55` points.  All configurations reduced FAR by approximately
  `2.7` points, but the smallest HTER degradation was `+0.89` points, exceeding
  the frozen `+0.5`-point limit;
- fold 5: 24 feasible; selected `b0.75_m2_a0.050_A0.10`, late-FRR gain
  `-2.50`, FAR change `-2.28`, HTER change `+0.11`.

Thus v2 did not demonstrate positive recovery utility even on validation.  Its
direction-aware episode can suppress conflicting trusted updates, but the
underlying score-profile representation still trades lower FAR for worse FRR.
Relaxing the security/HTER constraints or selecting the least-bad fold-4
configuration after this result would be post hoc and is not permitted.

Per the prespecified stopping logic, do not continue tuning quarantine/EMA on
these outer caches and do not run the locked five-fold v2 test.  The next method
family should change the adaptive state representation itself, for example
validation-designed quantile or robust-distribution tracking, and must receive
a new protocol identifier and a new inferential-status statement before code
or results are compared.

### D016 — Adaptive Quantile Profile diagnostic protocol

Date: 2026-10-01  
Status: frozen before implementation or quantile validation results

This branch changes the adaptive state representation rather than adding
another EMA admission gate.  It separates two hypotheses: whether a robust
quantile state is intrinsically better suited to downward genuine-score drift,
and whether accepted-only feedback censoring remains limiting even with that
state.

For each subject/fold, use the same genuine enrollment scores and validation
EER threshold `tau0` used by the EMA baselines.  Initial quantiles are the
discrete weighted empirical quantiles `q20` and `q50`.  Enrollment samples have
equal weights `1/n`.  For normalized nonnegative weights, `Q_p` is the minimum
observed score whose sorted cumulative weight is at least `p`; no interpolation
between scores is permitted.

Define once at enrollment:

`c = (q50_0 - tau0) / (q50_0 - q20_0)`

and never update or clip `c`.  The online authentication threshold is:

`tau_t = q50_t - c * (q50_t - q20_t)`.

The formula is evaluated literally without post-hoc clipping, so the initial
quantile threshold equals `tau0` up to floating-point tolerance.  If
`q50_0 - q20_0 < 1e-8`, the subject/fold quantile path is invalid.  Record the
exclusion and remove that path only from the paired quantile comparison; do not
invent a fallback, interpolate the quantiles, or clip `c`.  Save the empirical
distribution of valid `c` values as a diagnostic.

For an authorized update with new score `s_t`, multiply every existing weight
by `rho`, append `s_t` with weight `1-rho`, and renormalize weights to sum to
one for numerical stability.  Retain all scores during this short diagnostic
stream.  Recompute discrete weighted `q20`, `q50`, and the derived threshold.

Evaluate two information regimes with the identical representation and `rho`:

1. `Accepted-only Quantile`: authenticate using the current quantile threshold;
   update only when the adaptation score is accepted.  This is the deployable
   method used for validation selection and the primary quantile comparison.
2. `Oracle-all Quantile`: compute the same authentication decision, but update
   on every ground-truth genuine adaptation candidate, including rejected
   candidates.  This is a diagnostic control, not deployable.

Within every complete session pair, `within=0` is the only adaptation
observation and `within=10` is an evaluation-only genuine checkpoint.  Matched
impostor checkpoints are also evaluation-only.  The minimum comparison is
Frozen, Blind EMA, Guarded EMA (`lambda=0.25`), Oracle-all-genuine EMA,
Accepted-only Quantile, and Oracle-all Quantile.  TQ-EMA is not repeated in the
primary quantile experiment because its stopping result is already fixed.

The only validation hyperparameter is `rho in {0.80, 0.90, 0.95}`.  `q_low=0.20`
and `q_center=0.50` are fixed.  For each fold, initialize/calibrate from its
clean `D=0` validation scores and replay the independently predicted `D=2`
transformation of those validation sequences chronologically; claimant scores
use `D=2` and impostor checkpoints use `D=0`.  This is a synthetic validation
replay, not an independent inner holdout, and it never reads outer test scores.

Only `Accepted-only Quantile` determines selection.  A `rho` is feasible when
its subject-macro late-FAR increase over Frozen is at most `+1.0` percentage
point and its HTER degradation is at most `+0.5` point.  Among feasible values,
choose the largest late-FRR gain; exact ties prefer the larger `rho` as the more
conservative/slower updater.  If any fold has no feasible `rho`, fail closed and
do not load outer test scores.  Oracle-all Quantile is reported for all three
validation values but is never tuned independently.  If outer evaluation is
allowed, both quantile regimes use the `rho` selected by Accepted-only in that
fold.

The primary outer endpoint is
`Frozen late FRR - Accepted-only Quantile late FRR` under claimant-only `D=2`.
Success requires the lower endpoint of the paired 95% subject-bootstrap
interval above zero, mean late-FAR change at most `+1.0` point, HTER degradation
at most `+0.5` point, and the same conclusion in the 99-subject complete-five-
fold sensitivity.  Secondary outputs are update/authentication rate, changes
in `q20`, `q50`, and threshold, the corresponding Oracle-all Quantile effects,
and `Accepted-only FRR - Oracle-all FRR` as the direct cost of feedback
censoring under a matched state representation.

Interpretation is prespecified: both quantile regimes working supports the
robust state under deployable censoring; only Oracle-all working identifies
feedback censoring as the remaining barrier; neither working rejects this
quantile representation; Accepted-only outperforming Oracle-all materially is
a protocol/implementation warning requiring audit.

Inferential limitation: the same outer subject/session score caches have been
inspected throughout Paper 3.  Any quantile outer evaluation is exploratory
reuse, not an untouched confirmatory test, even though validation discipline
and the fail-closed gate remain enforced.

### D017 — Adaptive Quantile Profile validation result

Date: 2026-10-01  
Run: `results/paper3_quantile_validation_failed_20261001_v1/`  
Status: validation failed; exploratory outer evaluation not performed

The frozen `q20/q50` Adaptive Quantile Profile did not meet its prespecified
validation gate.  None of `rho={0.80, 0.90, 0.95}` was feasible for
Accepted-only Quantile in any of the five folds.  The least-bad unconstrained
value was `rho=0.95` in every fold, but its late-FRR gain versus Frozen remained
negative (`-12.00`, `-12.00`, `-10.10`, `-8.59`, and `-10.50` percentage
points).  Although late FAR decreased by `2.35` to `6.24` points, HTER worsened
by `1.93` to `3.41` points, exceeding the fixed `+0.5`-point constraint in
every fold.

Across folds, descriptively and without treating folds as independent,
Accepted-only Quantile at `rho=0.95` had mean late-FRR gain `-10.64` points,
late-FAR change `-4.89` points, and HTER change `+2.87` points.  Oracle-all
Quantile at the same `rho` reduced the direct censoring cost: its mean late FRR
was about `6.02` points lower than Accepted-only.  However, Oracle-all itself
still had mean late-FRR gain `-4.62` points and HTER change `+1.39` points
versus Frozen.  The same qualitative result held throughout the grid: removing
feedback censoring improved the quantile trajectory relative to Accepted-only,
but did not make this fixed `q20/q50` representation useful relative to Frozen.

This maps to the prespecified interpretation in which neither quantile regime
works.  Accepted-only feedback censoring is a measurable additional failure
mechanism, but it is not the only barrier; the tested discrete exponentially
weighted `q20/q50` state and threshold mapping also failed to track the required
downward drift at the allowed memory values.  Do not present this result as a
general rejection of robust distribution tracking, only as rejection of this
frozen representation and grid under the current synthetic validation replay.

There were no invalid paths from the `q50_0-q20_0 < 1e-8` rule.  The 498 valid
subject/fold paths had minimum initial span approximately `0.000122`; the
unclipped diagnostic `c` values ranged from approximately `-11.48` to `7.51`.
Two validation paths (`sid=57`, folds 3 and 4) were excluded because they lacked
four complete session pairs, not because of quantile degeneracy.  The manifest
records `status=validation_failed` and `outer_test_loaded=false`; no outer
tables, bootstraps, or trajectory figures were generated.

Per the frozen stopping rule, do not relax the FAR/HTER constraints, expand the
`rho` grid, change quantiles, or run the exploratory outer evaluation for this
branch after seeing these validation results.  A subsequent method must receive
a new protocol identifier and should change the state/threshold dynamics for a
scientifically motivated reason rather than tune this failed specification.

### D018 — Paper 3 experimental freeze and final-analysis protocol

Date: 2026-10-02  
Freeze commit: `476cf91`  
Freeze tag: `paper3-method-freeze-2026-10-02`  
Status: experimental development on HMOG stopped; reporting package authorized

No additional HMOG adaptation algorithm, tuning sweep, combined drift-plus-
attack run, or stopped outer evaluation will be launched for the current paper.
The final analysis is a read-only aggregation of completed authoritative runs:

- attack v2: `paper3_attack_v2_summary.csv` and
  `paper3_attack_v2_by_fold.csv`;
- guarded poisoning: `results/paper3_guarded_20260930/`;
- clean claimant-only drift and Oracle-all diagnostic:
  `results/paper3_oracle_all_drift_20261001_v2/`;
- TQ-EMA v1: `results/paper3_tq_clean_drift_20261001_v1/`;
- TQ-EMA v2 validation stop:
  `results/paper3_tq_v2_validation_failed_20261001/`;
- Adaptive Quantile validation stop:
  `results/paper3_quantile_validation_failed_20261001_v1/`.

The manuscript hypotheses/claims are now fixed as follows.  H1: Blind EMA is
vulnerable to held-out profile poisoning, with post-poison ASR increasing with
budget and the score-informed boundary strategy providing the strongest tested
benchmark.  H2: the guarded update gate reduces malicious incorporation and
post-poison ASR relative to Blind EMA, with a measurable genuine-update cost.
H3: accepted-only gating creates selective-update bias under downward genuine-
score drift; Oracle-all is diagnostic evidence that uncensored feedback restores
some FRR tracking but moves FAR in the unsafe direction.  H4: neither TQ-EMA v1,
TQ-EMA v2, nor the frozen `q20/q50` quantile branch established deployable clean
drift recovery under their prespecified gates.  These hypotheses summarize an
exploratory sequence and were not all prospectively preregistered before the
first HMOG results; the manuscript must not label them confirmatory.

The central completed security endpoint is post-poison ASR (and within-method
change from `K=0`) at the fixed budgets `K={0,1,2,4,8}`, emphasizing boundary
`K=8`.  The primary comparisons shown in the final package are Frozen versus
Blind EMA and Blind EMA versus Guarded EMA with the already carried-forward
exploratory `lambda=0.25`.  Random attack and the full lambda sweep remain
secondary/exploratory.  The central drift endpoint is claimant-only `D=2` late
FRR gain versus Frozen.  Late FAR and HTER are paired safety endpoints.  TQ-v1
and the stopped validation branches retain their already frozen success rules:
the late-FRR-gain 95% subject-bootstrap interval must be above zero, late FAR
may increase by at most `+1.0` percentage point, and HTER may degrade by at most
`+0.5` point, with the complete-five-fold sensitivity conclusion preserved.

Do not add a retrospective universal practical threshold for poisoning ASR.
Report ASR and MUR effects in percentage points with explicit budgets and
denominators.  The `+1.0` FAR and `+0.5` HTER constraints are experiment-specific
engineering thresholds frozen before the corresponding validation selections,
not universal biometric standards.

Exclusions remain exactly those saved by each authoritative run.  Attack-v2
feasibility exclusions and source-session-group poison/probe separation are not
recomputed.  Clean-drift paths retain the recorded incomplete-session exclusion
for `sid=57`; validation runs retain their own recorded fold/path exclusions.
No complete-case set is silently substituted for the primary all-available-
subject analysis.

For attack runs, fold summaries, standard deviations, and t intervals are
descriptive protocol-stability summaries because folds overlap and Monte Carlo
repeats are not independent observations.  For clean drift, the primary
uncertainty analysis averages each subject across available folds and applies a
paired subject bootstrap; the 99-subject complete-five-fold result is a
sensitivity analysis.  FAR two-way victim/impostor-source bootstrap remains a
secondary robustness analysis.  No new null-hypothesis tests or post-result
multiplicity procedure will be introduced in the final aggregation.

The final analysis must not retrain, rescore, tune, or write into authoritative
run directories.  It must verify expected manifest statuses and stopped-outer
flags, cross-check duplicated Frozen/Blind values across result families, hash
every consumed input, and write a new immutable output directory containing
three figures, plot-data tables, the summary decision table, and a provenance
manifest.

### D019 — Final Paper 3 result package

Date: 2026-10-02  
Run: `results/paper3_final_analysis_20261002_v2/`  
Status: complete; read-only aggregation

`paper3_final_analysis.py` consumed 26 frozen inputs from commit `476cf91` and
performed no training, rescoring, adaptation, or tuning.  Its manifest confirms
that attack-v2 and guarded-run Frozen/Blind baselines match, Guarded
`lambda=0` reproduces Blind EMA, clean-drift baselines match the TQ-v1 export,
and both stopped branches retain `outer_test_loaded=false`.  All consumed inputs
and generated outputs are SHA-256 hashed.

The final poisoning figure shows random and boundary attacks with the nested
budgets `K={0,1,2,4,8}`.  Under boundary `K=8`, Blind EMA post-poison ASR was
approximately `53.96%`, versus `22.92%` for Frozen and `22.93%` for Guarded
`lambda=0.25`.  Blind MUR was `100%`; Guarded MUR was approximately `1.63%`.
The lambda sweep remains an exploratory supporting table rather than a selected
confirmatory comparison.

The final security-adaptation trade-off figure uses claimant-only `D=2` and
plots late FAR against late FRR after subject-level fold averaging.  Frozen was
`22.86%` FAR / `32.53%` FRR; Blind was `23.80%` / `32.20%`; Guarded was `21.73%`
/ `34.60%`; Oracle-all was `28.94%` / `25.93%`; and TQ-v1 was `20.92%` /
`33.43%`.  The figure therefore presents a trade-off frontier rather than a
free improvement claim.

The final mechanism figure averages each subject across available folds before
bootstrapping.  Across the five session checkpoints, Guarded profile mean and
threshold move upward while Oracle-all moves both downward.  Guarded update
rates fall from approximately `63.47%` to `51.68%`, whereas Oracle-all remains
at `100%`.  This is the central visual evidence for selective-update bias.

The summary decision table freezes six interpretations: reject Blind EMA as a
deployable adaptive policy; retain Guarded EMA only as the security baseline;
use Oracle-all only as a diagnostic; stop TQ-v1; stop TQ-v2 after validation;
and stop the frozen `q20/q50` quantile representation after validation.  TQ-v1
is not described as directly attack-validated because the combined
drift-plus-attack experiment was never run.

This package closes HMOG algorithm development for Paper 3.  The next allowed
work is manuscript drafting from the frozen package or a separately justified
decision about an untouched external dataset.  Exact inherited Paper 1/Paper 2
facts still require verification from their primary manuscripts before
submission and remain the only unchecked item in the reporting checklist.

### D020 — External replication dataset and locked protocol

Date: 2026-10-03

Protocol: `experiments/external_replication_mcgill.md`

Status: frozen before model training and before any Day-2 endpoint

whuGAIT was audited first.  Its official processed Dataset #2 has the desired
20 high-volume subjects, accelerometer plus gyroscope, two-step sequences, and
no overlap.  However, the distributed train/test matrices retain only subject
labels: day/session identifiers, timestamps, and original order are absent, and
the subject-label sequence is heavily shuffled.  It can support an attack-only
replication, but it cannot support the required real-day chronological
selective-update experiment without inventing a temporal axis.  It was
therefore rejected for the unified three-mechanism replication rather than
quietly approximated with shuffled order.

The closest directly accessible alternative is the McGill Gait Dataset.  It
contains 20 subjects, two separate days per subject, raw timestamps, and an
explicit subject/day filename scheme.  A pre-result structural audit confirmed
40 expected files, finite accelerometer channels, strictly increasing
timestamps, a 40 ms median interval in every file, no gaps above 500 ms, and
enough non-overlapping 128-sample windows for the frozen partitions.  The
archive SHA-256 is
`0e2da09c2d10fb5658c79d362e9e043a2f2822715723238b30cbebd2e7b425d9`.

The cost of this choice is explicit: McGill has triaxial accelerometer but no
gyroscope.  The replication prioritizes genuine two-day chronology over sensor
modality equality.  It uses a fixed, modest LSTM and repeats only Frozen,
Blind, Guarded (`lambda=0.25`), and Oracle-all mechanisms.  TQ-EMA, adaptive
quantiles, new methods, synthetic drift, and dataset-specific tuning remain out
of scope.  The 23 frozen protocol fields, endpoints, subject-bootstrap plan,
exclusions, stopping rules, and seeds are recorded in the protocol file and its
machine-readable JSON companion.  Any null or reversed Day-2 result will be
reported as a negative external replication without changing this protocol.

### D021 — McGill external replication result

Date: 2026-10-03

Run: `results/paper3_external_mcgill_20261003_v1/`

Status: complete; locked protocol; no tuning after Day-2 scoring

The fixed Day-1 LSTM passed its prespecified viability gate before Day 2 was
loaded: validation top-1 accuracy was `58.12%`, compared with the locked `20%`
minimum.  The score cache contains 958 Day-1 enrollment windows and 4,976
Day-2 windows and has SHA-256
`3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b`.
All 20 subjects passed the structural inclusion rules.

The main boundary-poisoning mechanism replicated.  At `K=8`, Frozen held-out
ASR was `12.37%`, Blind EMA ASR was `32.09%`, and Guarded EMA ASR was `12.48%`.
The paired Blind-minus-Frozen effect was `+19.72` percentage points with a 95%
subject-bootstrap interval of `[+5.58, +37.34]`.  The Guarded-minus-Blind ASR
effect was `-19.62` points `[-37.17, -5.60]`.  Blind incorporated every
presented boundary poison (`100%` MUR), whereas Guarded MUR was `32.22%`; the
paired reduction was `-67.78` points `[-84.30, -49.47]`.

Boundary feasibility is an important limitation rather than a hidden
exclusion.  Of 2,000 victim-repeat paths, 544 lacked eight initially accepted
near-boundary candidates.  Eighteen victims contributed at least one feasible
path to the boundary `K=8` subject analysis, with repeats averaged within
victim before the 10,000-resample subject bootstrap.  The random attack was
weaker: at `K=8`, Blind-minus-Frozen ASR was `+1.51` points with interval
`[-0.09, +4.43]`; this secondary effect is directionally positive but
inconclusive.

The real two-day temporal analysis also reproduced the selective-update
mechanism, although absolute cross-day authentication performance was poor.
Frozen late FRR/FAR were `78.00%/11.46%`.  Guarded late FRR/FAR were
`81.00%/10.29%`, with GUR `19.06%`; its late-FRR difference from Frozen was
`+3.00` points `[0.00, +7.00]`.  Guarded mean and threshold moved upward, with
mean threshold displacement `+0.0226` score units.

Oracle-all-genuine, which receives every genuine adaptation observation,
moved in the opposite direction.  Its late FRR was `12.75%`, `65.25` points
below Frozen `[-83.75, -45.50]`, and `68.25` points below Guarded
`[-85.25, -49.25]`.  Its mean threshold displacement was `-0.2426`.  This
tracking gain was insecure: Oracle late FAR rose to `75.05%`, `64.76` points
above Guarded `[+48.93, +79.24]`.  Late HTER remained similar across Frozen,
Guarded, and Oracle (`44.73%`, `45.64%`, and `43.90%`), so Oracle is evidence
about recoverability and feedback censoring, not a deployable improvement.

The retained interpretation is therefore mechanism-level external support:
score-informed boundary poisoning contaminates Blind EMA; the transferred
Guarded gate sharply reduces contamination and removes almost all of the ASR
increase; and accepted-only gating fails to follow a large real cross-day
genuine-score shift that Oracle-all can track only by paying an extreme FAR
cost.  Do not generalize the absolute rates beyond this 20-subject,
accelerometer-only dataset.  The random-attack result, high Day-2 FRR, large
boundary feasibility exclusion, and missing gyroscope must be reported
prominently.

The locked analysis was rerun from the same score cache.  All 10 CSV/Markdown
tables and all three PNG figures were byte-identical; PDF hashes differed only
because Matplotlib embeds creation metadata.  The committed run manifest
verifies every retained output hash.  No TQ-EMA, quantile, synthetic-drift, or
new-method experiment was opened.

### D022 — Experimental closure and manuscript transition

Date: 2026-10-03

Status: all Paper 3 experiments closed before manuscript drafting

The HMOG mechanism study and the independent McGill two-day replication are
sufficient for the first journal submission.  No third dataset, new TQ-EMA
variant, new adaptive-state representation, additional model, or retrospective
parameter sweep will be added before that submission.  Further experiments
would require a new decision entry and a separate scientific motivation; they
must not revise the frozen HMOG or McGill packages.

The manuscript contributions are fixed as follows:

1. **Poisoning vulnerability.** Label-blind accepted-only EMA permits
   near-boundary impostors to contaminate the adaptive profile and increase
   held-out future ASR.
2. **Security defense.** A separate confidence-gated update authorization rule
   sharply reduces malicious incorporation and post-poison ASR without changing
   the authentication decision rule.
3. **Selective-update bias.** The same accepted-only feedback structure censors
   lower-scoring genuine observations and prevents the profile from adequately
   following downward legitimate score drift.
4. **Mechanistic evidence.** Oracle-all-genuine controls show that removing
   censoring restores genuine-score tracking, but moves the operating point to
   substantially higher FAR and is therefore diagnostic rather than deployable.
5. **External replication.** The poisoning, defense, and selective-feedback
   mechanisms reproduce on the independent two-day McGill Gait dataset under a
   locked protocol and transferred Guarded parameter.

MUR must not be interpreted as contamination severity by itself.  Guarded MUR
on McGill (`32.22%`) is much higher than in the frozen HMOG result, yet McGill
post-poison ASR remains essentially at Frozen.  The security impact therefore
depends on which malicious observations enter the profile and how far they move
the mean, variance, and threshold, not only on the fraction incorporated.  This
cross-dataset contrast belongs in Discussion and does not motivate a new metric
or experiment after closure.

The writing order is now fixed operationally as Methods, Results, Discussion,
Related Work/Introduction, Limitations, Abstract, journal selection, and
submission preparation.  Methods and Results must be written directly from the
authoritative HMOG and McGill manifests/tables.  Limitations must prominently
include the 20-subject McGill cohort, accelerometer-only modality, high Day-2
Frozen FRR, boundary feasibility exclusions, synthetic HMOG drift, and the
non-deployable nature of Oracle-all.

## Paper 1/Paper 2 source audit

Status: complete on 2026-10-03.  See
[`paper/paper1_paper2_fact_check.md`](paper1_paper2_fact_check.md) for the
claim-by-claim evidence table, source locations, approved wording, hashes, and
recorded discrepancies.

- [x] Exact titles, authors, venues, dates, DOI/publication status, and citation records.
- [x] Paper 1 search dates, databases, PRISMA counts, corpus composition, research questions, and stated gaps.
- [x] HMOG subjects/sessions, sensor columns, nominal sampling assumption, exclusions, windows, sequences, and normalization.
- [x] Fold construction and realized fit/validation/test counts.
- [x] LSTM/RF/SVM architectures and fixed hyperparameters.
- [x] Score orientation, validation calibration, and EER definition.
- [x] Exact EMA equations, `alpha`, claimant-specific `k`, initialization, and accepted-only update trigger.
- [x] Paper 2 PDF numbers cross-checked against revised summary and fold CSVs; no inferential significance test was reported.
- [x] Synthetic drift definition, magnitudes, chronology, scope, and fold-level direction.

Recorded caveats: Paper 1 supplementary files disagree on the per-year
distribution and contain two unresolved extraction-table/quality-workbook
cross-references.  Paper 2's supplied PDF has placeholder Procedia volume/page
metadata and no final DOI.  Neither caveat changes the critical claims used by
Paper 3.

## Open design questions

- Is the threat model binary-feedback only, or does the attacker observe a confidence score?
- Should poison/probe pools be source-session-disjoint or fully identity-disjoint in the primary analysis?
- What is a realistic maximum query budget for the deployment scenario?
- Which temporal unit authorizes updates: window, episode, or continuous duration?
- How should legitimate device handover and abrupt genuine behavioral change be handled?
- Which rollback signal can be computed without labels?
- Which robust estimator is most stable for short quarantine batches?
- How tightly should cumulative movement be anchored to enrollment without blocking real drift?
- Is the proposed mechanism strictly score-profile adaptation, or will later experiments update model weights?
- What minimum clean utility must the defense preserve?

## Pre-registration checklist

- [x] Verify Paper 1/Paper 2 facts from primary materials (`paper/paper1_paper2_fact_check.md`; completed 2026-10-03).
- [x] Freeze hypotheses and central reporting endpoints (D018; explicitly post-result/exploratory).
- [x] Freeze cohort/exclusion rules (authoritative manifests and exclusions files).
- [x] Freeze attack budgets and attacker feedback (`K={0,1,2,4,8}`; random and score-informed boundary).
- [x] Freeze TQ-EMA parameters or tuning ranges (D012, D014; both branches closed).
- [x] Freeze primary attacker knowledge and probe-identity regime (source-session-group split; boundary is not binary-feedback-only).
- [x] Freeze statistical analyses and multiplicity handling (D018; descriptive folds, paired subject bootstrap, no new tests).
- [x] Define practical-effect handling (pre-existing `+1.0` FAR/`+0.5` HTER constraints; no retrospective universal ASR cutoff).
- [x] Hash completed configurations and consumed inputs (authoritative manifests; final aggregator must emit input hashes).

## Decision log template

```text
Date:
Decision ID:
Question:
Decision:
Evidence:
Alternatives rejected:
Protocol/results affected:
Author:
```
