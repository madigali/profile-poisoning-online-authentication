# Local data and caches

This directory is intentionally empty in Git.

The experiments require locally obtained HMOG/McGill data and generated score/model
caches. Do not commit raw archives or participant-derived sensor data
unless redistribution rights have been verified.

Expected local artifacts include:

```text
paper3_cache/                     fixed fold-level LSTM scores and models
revised_results/hmog_sequences_100.npz
~/Downloads/McGillGait/gait-dataset/          raw two-day McGill CSV files
~/Downloads/McGillGait/paper3_external_cache_v1/
                                              Day-1 model and locked score cache
```

The canonical cache builder is `src/paper3_cache_scores.py`. Its default raw
dataset location is `~/Downloads/public_dataset`; override it with
`--data-dir` when necessary.

The McGill archive is obtained from the
[official dataset page](https://www.cs.mcgill.ca/~jfrank8/data/gait-dataset.html).
The archive used by the locked replication has SHA-256
`0e2da09c2d10fb5658c79d362e9e043a2f2822715723238b30cbebd2e7b425d9`.
The raw archive, extracted CSV files, model checkpoint, and score cache stay
outside Git; the committed result manifest records their provenance hashes.
