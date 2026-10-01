# Local data and caches

This directory is intentionally empty in Git.

The experiments require locally obtained HMOG data and generated score/model
caches. Do not commit raw HMOG archives or participant-derived sensor data
unless redistribution rights have been verified.

Expected local artifacts include:

```text
paper3_cache/                     fixed fold-level LSTM scores and models
revised_results/hmog_sequences_100.npz
```

The canonical cache builder is `src/paper3_cache_scores.py`. Its default raw
dataset location is `~/Downloads/public_dataset`; override it with
`--data-dir` when necessary.
