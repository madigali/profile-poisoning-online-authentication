# Poisoning-Resistant Online Adaptation for Mobile Authentication

Research code, frozen HMOG results, and a locked external replication for Paper 3 of a PhD project on
behavioral-biometric continuous authentication.

The repository studies a central security–adaptation trade-off: an online
profile should follow legitimate behavioral drift without allowing accepted
impostor samples to poison its state.

## Current status

The HMOG method-development phase is frozen. The completed evidence shows:

- Blind EMA is vulnerable to profile poisoning.
- A guarded update threshold sharply limits malicious updates, but accepted-only
  feedback introduces selection bias under downward genuine-score drift.
- Oracle-all-genuine updates demonstrate that the drift is trackable, but move
  the operating point toward higher FAR.
- TQ-EMA v1 does not recover FRR; TQ-EMA v2 and the adaptive-quantile branch
  failed their validation gates, so their outer tests were not run.

The independent McGill Gait replication is also complete. It reproduced the
boundary-poisoning vulnerability, the contamination reduction from the fixed
Guarded gate, and the accepted-only selection-bias mechanism. Random poisoning
was weaker and its central confidence interval included zero. McGill contains
accelerometer but no gyroscope, so this is a mechanism replication under a
different sensor setting rather than a numerically identical HMOG reproduction.

## Repository layout

```text
src/          experiment and analysis scripts
tests/        unit and protocol-invariant tests
experiments/  experimental protocol
paper/        research notes and decision log
results/      frozen authoritative tables, manifests, and figures
data/         instructions for local-only datasets and caches
```

The three publication figures and final summary table are in
[`results/paper3_final_analysis_20261002_v2`](results/paper3_final_analysis_20261002_v2).
The external-replication tables, manifest, and three figures are in
[`results/paper3_external_mcgill_20261003_v1`](results/paper3_external_mcgill_20261003_v1).

## Environment

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Raw HMOG data, trained weights, and score caches are intentionally not stored
in Git. See [`data/README.md`](data/README.md).

The McGill replication is staged so that Day 2 cannot affect model selection:

```bash
python src/paper3_external_mcgill.py audit
python src/paper3_external_mcgill.py smoke
python src/paper3_external_mcgill.py train
python src/paper3_external_mcgill.py score
python src/paper3_external_mcgill.py test \
  --output-dir results/local-mcgill-replication-check
```

The locked protocol is
[`experiments/external_replication_mcgill.md`](experiments/external_replication_mcgill.md).

## Verification

Run the test suite:

```bash
python -m pytest
```

Rebuild the final read-only aggregation from the frozen result files:

```bash
python src/paper3_final_analysis.py \
  --source-dir . \
  --output-dir results/local-final-analysis-check
```

The final-analysis script does not train, rescore, adapt, or tune a model. It
validates and aggregates already completed experiments into a new output
directory and refuses to overwrite a non-empty directory.

## Reproducibility and provenance

- Method freeze tag: `paper3-method-freeze-2026-10-02`
- Default random seed for Paper 3 score-level experiments: `4242`
- McGill protocol freeze commit: `f5ef301`
- McGill locked score-cache SHA-256:
  `3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b`
- TQ-EMA v2 and adaptive quantile have `validation_failed` status with
  `outer_test_loaded=false` in their saved records.
- Historical and superseded development artifacts remain recoverable from Git
  history but are not present in the clean default branch.

Before manuscript submission, inherited Paper 1 and Paper 2 statements must be
checked against their primary manuscripts, as recorded in `paper/notes.md`.
