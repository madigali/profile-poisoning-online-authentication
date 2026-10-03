# External replication protocol — McGill Gait

**Protocol ID:** `paper3-external-mcgill-v1`  
**Frozen:** 2026-10-03, before model training and before any Day-2 score or
endpoint was computed  
**Status:** locked external-replication protocol

## Dataset decision

whuGAIT was evaluated first because it has accelerometer and gyroscope data
from 20 high-volume participants collected over two days. The official
processed Dataset #2 archive is not suitable for the temporal part of this
replication: it contains six signal matrices and one subject-label vector for
each of the shuffled train and test partitions, but no day, session, timestamp,
or original-order field. The observed label order is heavily interleaved
(41,875 subject runs among 44,339 train rows and 4,680 runs among 4,936 test
rows), so file order cannot be treated as chronology. Using that order for a
selective-update-bias experiment would fabricate a temporal axis.

The external replication therefore uses the McGill Gait Dataset. It preserves
the property most important for the third experiment: 20 subjects each have a
raw, timestamped walk on Day 1 and a second raw, timestamped walk on Day 2.
Its limitation is explicit: it has triaxial accelerometer and magnetometer/
orientation data but no gyroscope. Only accelerometer-derived channels are used.

Official sources:

- whuGAIT repository and dataset description:
  <https://github.com/qinnzou/Gait-Recognition-Using-Smartphones>
- McGill Gait Dataset:
  <https://www.cs.mcgill.ca/~jfrank8/data/gait-dataset.html>
- McGill archive:
  <https://www.cs.mcgill.ca/~jfrank8/data/gait-dataset.tar.gz>

Downloaded archive hashes:

- whuGAIT Dataset #2 ZIP: `bb6f71910867c73070d5fd4faeff97fc5edc4b3a39dc6f0edd2ef5858740be9f`
- McGill archive: `0e2da09c2d10fb5658c79d362e9e043a2f2822715723238b30cbebd2e7b425d9`

Raw archives and derived windows remain local and are not committed.

## Frozen protocol fields

1. **Dataset version and source.** The unversioned official McGill archive
   whose SHA-256 is listed above is the authoritative input.
2. **Subjects.** Use subjects `w001` through `w020`. No subject selection is
   based on classifier scores or authentication outcomes.
3. **Temporal structure.** Day 1 is model development and enrollment. Day 2 is
   the untouched attack and temporal-adaptation day. File timestamps define
   within-day order.
4. **Inclusion/exclusion.** A subject must have both days, finite required
   channels, strictly increasing timestamps, at least 100 Day-1 windows and at
   least 160 Day-2 windows. An incomplete trailing window is discarded. Any
   exclusion and reason must be saved before endpoint aggregation. The
   structural audit found all 20 subjects eligible.
5. **Sensor channels.** Use `accel_x`, `accel_y`, `accel_z`, and the supplied
   `accel_mag` (`sqrt(x^2+y^2+z^2)-9.8066`). Magnetometer, orientation, and the
   empty temperature channel are excluded.
6. **Sampling frequency.** Use the recorded samples without interpolation.
   Every file has a 40 ms median interval, corresponding to approximately
   25 Hz; this is an observed property, not an author-stated nominal rate.
7. **Window size.** 128 consecutive samples, approximately 5.12 seconds.
8. **Sequence representation.** Each model input has shape `128 x 4` in the
   channel order fixed in item 5.
9. **Overlap.** None. Windows are contiguous and non-overlapping within a day.
10. **Normalization.** One pooled z-score transform per channel, fitted only
    to Day-1 training windows. Standard deviations below `1e-8` are replaced by
    `1.0`. The frozen transform is applied to every later partition.
11. **Partitions.** For each subject, chronological Day-1 windows are split
    `60%/20%/20%`: model train, early-stopping validation, and enrollment/
    threshold calibration. Integer cut points are `floor(0.60*n)` and
    `floor(0.80*n)`. Day 2 is never used for fitting, early stopping,
    normalization, threshold calibration, or parameter choice. For temporal
    analysis, select 160 approximately equally spaced Day-2 windows per subject
    by deterministic integer indices spanning the full day and pair them into
    80 ordered units: adaptation window then disjoint checkpoint window.
12. **Classifier.** A fixed single-layer unidirectional LSTM with input size 4,
    hidden size 64, final-hidden-state classification, and a 20-class linear
    head. Use class-weighted cross entropy, Adam (`lr=0.001`, weight decay
    `0.0001`), batch size 128, at most 30 epochs, and validation-loss early
    stopping with patience 5. No architecture or optimizer sweep is allowed.
13. **Score.** The claimant score is the softmax probability assigned to the
    claimed identity. Higher is more genuine-like.
14. **EMA.** Use `alpha=0.05`. Track mean `mu` and second moment `q`; derive
    `sigma=max(sqrt(max(q-mu^2,0)),1e-4)`. Calibrate the initial authentication
    threshold on Day-1 enrollment scores by minimum HTER, breaking exact ties
    in favor of the higher threshold. Set
    `k=(mu_enroll-tau_auth)/sigma_enroll`, then recompute online thresholds as
    `tau=mu-k*sigma`. Frozen never changes state; Blind updates after every
    accepted observation; Oracle-all updates from every ground-truth genuine
    adaptation observation, including rejected observations.
15. **Guarded lambda.** Fix `lambda=0.25`, transferred unchanged from the HMOG
    reporting comparison. `T_update=T_auth+0.25*(mu_enroll-T_auth)`. Access is
    decided only by `T_auth`; an accepted sample updates only if it also meets
    the update gate. No lambda sweep is permitted on McGill.
16. **Attack budgets.** Nested `K={0,1,2,4,8}`.
17. **Poison construction.** For each victim and Monte Carlo repeat, randomly
    assign whole non-victim source identities to poison and probe groups as
    close to 50/50 as possible. Only the chronological first half of a poison
    identity's Day-2 windows is eligible for poisoning; only the second half of
    a probe identity's windows is used for held-out ASR. Random poisoning draws
    one maximum-length sequence without replacement, and each K is a prefix.
18. **Boundary attack.** From the same poison pool, keep candidates accepted by
    the initial frozen threshold and rank them by smallest non-negative initial
    margin. Select the first eight and use nested prefixes. This is a
    score-informed strong benchmark, not a binary-feedback-only attack.
19. **Disjointness.** Poison and probe samples are disjoint in source identity,
    file, and temporal half. Profile state is frozen after poisoning. Probe
    samples and genuine FRR samples never update the profile. Temporal
    checkpoints never update any method.
20. **Metrics.** Attack/defense: post-poison ASR, FAR, FRR, HTER, poison
    acceptance rate, MUR, malicious update count, and mean/sigma/threshold
    displacement. Temporal: early and late checkpoint FRR, temporally matched
    FAR, HTER, GUR, profile displacement, and checkpoint trajectories. Early
    and late are the first and last 20 of 80 temporal units.
21. **Statistics.** Average Monte Carlo repeats within subject first. Use
    paired subject effects across the eligible subjects and 10,000 percentile
    bootstrap resamples. Report mean effect in percentage points, 95% CI,
    subject count, and exclusions. Fixed central contrasts are: Blind minus
    Frozen ASR under boundary `K=8`; Guarded minus Blind ASR and MUR under
    boundary `K=8`; and Guarded minus Oracle-all late FRR on Day 2. Other
    budgets and random attacks are secondary. No fold-based inference is used.
22. **Stopping rules.** Before Day 2 is scored, stop if training loss becomes
    non-finite, fewer than 16 classes are represented in Day-1 validation, or
    validation top-1 accuracy is below `20%`. Protocol-invariant tests and a
    synthetic smoke run must pass before the real test run. After any Day-2
    endpoint is inspected, no preprocessing, architecture, EMA, lambda, K,
    attack, exclusion, or analysis parameter may change. A null or reversed
    effect is retained as a negative external replication.
23. **Seeds.** Model/data-loader seed `4242`; attack master seed `4242` with a
    deterministic victim/repeat derivation; subject-bootstrap seed `20261003`.
    CPU deterministic algorithms are requested and the resolved environment is
    written to the run manifest.

## Interpretation boundaries

The replication tests directions and mechanisms, not numerical equality with
HMOG. The McGill sensor and activity context differs from HMOG, so a successful
result supports cross-dataset mechanism reproducibility, not universal
performance. The missing gyroscope is a stated limitation. Oracle-all remains
diagnostic and non-deployable. No TQ-EMA, quantile method, new adaptive
algorithm, or synthetic drift is part of this protocol.
