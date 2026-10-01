# Experimental Protocol

This file preserves the operational specification used during Paper 3 method
development. The completed decisions and stopping rules are recorded in
[`paper/notes.md`](../paper/notes.md), and the authoritative retained runs are
listed in [`results/README.md`](../results/README.md).

## Phase 0 — Recover and freeze the foundation

1. Import the canonical Paper 2 preprocessing and scoring pipeline.
2. Recover exact dataset partitions and EMA parameters.
3. Generate immutable fold-level score caches with sample identity, session, within-session order, and labels.
4. Reproduce published or archived Paper 2 results within a documented tolerance.
5. Hash the caches and use them unchanged for score-level attack comparisons.

## Phase 1 — Baseline reproduction

Implement and test:

- Frozen profile.
- Blind EMA using the exact Paper 2 behavior.
- Oracle EMA that scores all attempts but blocks ground-truth impostor updates.

The malicious-only control must satisfy Oracle = Frozen for decisions, FRR, ASR, and profile state when no legitimate updates occur.

## Phase 2 — Attack-only vulnerability

For each fold, victim, and repeat:

1. Build the initial profile from validation genuine scores.
2. Calibrate `tau0` using validation genuine and impostor scores.
3. Collect test genuine samples in chronological order.
4. Group test impostors by `(source identity, session)`.
5. Randomly assign whole groups to poisoning and held-out probe pools.
6. Construct one maximum-length poisoning sequence per strategy.
7. Evaluate nested prefixes for `K = 0, 1, 2, 4, 8`.
8. Feed identical sequences to paired methods.
9. Freeze state after poisoning.
10. Evaluate ASR on the untouched probe pool and FRR on genuine test samples.

### Attack strategies

- **Random:** sample poison candidates uniformly without replacement.
- **Boundary:** among candidates accepted by the initial threshold, select the smallest positive margins first.

Report feasibility exclusions. If boundary selection lacks enough candidates, remove that victim/repeat from both paired strategies rather than creating different cohorts.

## Phase 3 — Defense evaluation

Add:

- Margin-gated EMA.
- Quarantine-only EMA.
- Full TQ-EMA.
- Robust median/MAD or another prespecified robust-profile baseline.

Defense hyperparameters must be selected using training/validation data or nested validation. Test attack probes may never tune the gate, buffer, robust estimator, anchor, cap, rate limit, or rollback.

## Phase 4 — Clean drift and combined stress

Run separate blocks for:

1. No attack, no imposed drift.
2. Benign drift only.
3. Poisoning only.
4. Benign drift plus poisoning.

Clearly label synthetic drift. Prefer naturally later sessions when the dataset supports a valid longitudinal analysis. Keep drift transformations identical across methods.

Where sample coverage permits, run separate probe regimes for same-identity/different-session attacks, identity-disjoint probes, and the current mixed source-session-group split. Keep these results separate.

## Phase 5 — Ablation and sensitivity

Ablate confidence gating, temporal confirmation, quarantine, movement caps, rate limiting, and rollback. Vary the main attack and defense parameters on a declared grid. Label non-preregistered searches exploratory.

## Required outputs per run

```text
results/<run-id>/
├── config.yaml
├── manifest.json
├── exclusions.csv
├── subject_repeat_metrics.csv
├── by_subject.csv
├── by_fold.csv
├── summary.csv
├── figures/
└── run.log
```

The manifest should include code revision, timestamp, environment, dataset/cache hashes, seeds, command, host summary, and status.

## Core metrics

- `post_asr`, `delta_asr`, `post_frr`
- `poison_accept_rate`, `malicious_updates`, `mur`
- profile mean/sigma/threshold before, after, and delta
- ASR increase per malicious update and per query
- clean utility and drift recovery
- latency, memory, and update frequency

Use explicit fractions internally and convert to percentages only at export/presentation boundaries.

## Aggregation

1. Average repeats per subject within fold and condition.
2. Macro-average subjects equally within fold.
3. Use folds as the across-fold unit for mean, SD, SE, and 95% t confidence intervals.
4. Preserve paired differences between methods.
5. Also save per-subject distributions for heterogeneity and worst-case analysis.

## Minimum tests

- No update for Frozen.
- Oracle/Frozen equality in malicious-only runs.
- No state change after a rejected score.
- No source-session group crosses poison/probe pools.
- Nested budgets are prefixes of one sequence.
- Identical sequences and probes reach all paired methods.
- Defense parameters never read test-probe labels or outcomes.
- Per-update caps cannot be exceeded.
- Quarantine expiration and rollback restore the intended state.
- Same seed produces byte-equivalent assignments and sequences.

## Execution ladder

Run tests, then a tiny synthetic smoke test, one victim, one fold, all folds with few repeats, and only then the final full configuration. Never overwrite a completed final run.
