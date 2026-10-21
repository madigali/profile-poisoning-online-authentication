# Profile Poisoning and Selective-Update Bias in Online Behavioral Biometric Authentication

Research code, protocol specifications, frozen derived results, manuscript
sources, and an independent McGill Gait replication for a study of
behavioral-biometric continuous authentication.

The repository studies a central security–adaptation trade-off: an online
profile should follow legitimate behavioral drift without allowing accepted
impostor samples to poison its state.

## MDPI submission snapshot

The public Technologies submission snapshot is available from the Git reference
[`technologies-submission-v1.0.1`](https://github.com/madigali/profile-poisoning-online-authentication/tree/technologies-submission-v1.0.1).
It contains the manuscript sources, Supplementary Materials, protocol records,
tests, and the derived result tables and figures used in the article.

- Main-manuscript upload ZIP: [`paper/mdpi/deliverables/technologies_submission_20261021_v5/Technologies_manuscript_main.zip`](paper/mdpi/deliverables/technologies_submission_20261021_v5/Technologies_manuscript_main.zip)
- Supplementary Materials: [`paper/mdpi/deliverables/technologies_submission_20261021_v5/Technologies_supplementary.pdf`](paper/mdpi/deliverables/technologies_submission_20261021_v5/Technologies_supplementary.pdf)
- Cover letter: [`paper/mdpi/deliverables/technologies_submission_20261021_v5/Technologies_cover_letter.pdf`](paper/mdpi/deliverables/technologies_submission_20261021_v5/Technologies_cover_letter.pdf)
- Upload map: [`paper/mdpi/deliverables/technologies_submission_20261021_v5/UPLOAD_MAP.txt`](paper/mdpi/deliverables/technologies_submission_20261021_v5/UPLOAD_MAP.txt)
- Reproducibility and provenance: [`paper/mdpi/source_manifest.json`](paper/mdpi/source_manifest.json)

The repository and submission snapshot are publicly accessible. Raw HMOG and
McGill Gait data, trained weights, and local score caches are not redistributed.
The H-MOG dataset is available from its
[provider](https://hmog-dataset.github.io/hmog/) subject to the provider's terms;
the College of William and Mary bears no responsibility for the authors'
analysis or interpretation. The McGill Gait dataset is available from its
[provider](https://www.cs.mcgill.ca/~jfrank8/data/gait-dataset.html).

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

The experimental phase is closed for this submission. No third dataset,
new adaptation method, or post-result parameter sweep is planned; active work
has moved to final administrative confirmation and journal submission from the
frozen packages.

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
- Default random seed for the score-level experiments: `4242`
- McGill protocol freeze commit: `f5ef301`
- McGill locked score-cache SHA-256:
  `3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b`
- TQ-EMA v2 and adaptive quantile have `validation_failed` status with
  `outer_test_loaded=false` in their saved records.
- Historical and superseded development artifacts remain recoverable from Git
  history but are not present in the clean default branch.

## License

Original software code in `src/`, `tests/`, and `experiments/` is licensed
under the [BSD 3-Clause License](LICENSE). The software license does not apply
to the manuscript, article figures, Supplementary Materials, or third-party
files under `paper/mdpi/Definitions/`; those materials retain their respective
copyright and publishing terms. The third-party H-MOG and McGill Gait datasets
are not redistributed by this repository and remain subject to their providers'
terms.
