# HMOG Poisoning Inference Data Audit

Audit date: 4 October 2026.

Purpose: determine whether the primary HMOG poisoning contrast can be reanalysed at the paired subject level without rerunning an experiment, regenerating scores, reconstructing attack paths, or opening validation-stopped outer data.

## Primary contrast

- Dataset: HMOG.
- Strategy: score-informed boundary benchmark.
- Budget: (K=8) selected poisoning attempts.
- Contrast: Blind EMA minus Frozen post-poison ASR.
- Unit requested for inference: victim after averaging Monte Carlo repeats within fold and victim, then averaging folds within victim.

## Retained files and row levels

| File | Location/status | Row level | Victim ID | Fold | Repeat | Strategy / K | Method | Impostor-source identity | Probe identity | Use in audit |
|---|---|---|---|---|---|---|---|---|---|---|
| `subject_repeat_metrics.csv` | Original frozen run directory; not present in the committed compact result package | fold × strategy × K × victim × repeat × policy | Yes (`sid`) | Yes | Yes | Yes | Yes (`policy_id`, `method`) | No | No | Exact Blind/Frozen path pairing and subject aggregation |
| `paper3_guarded_by_fold.csv` | Committed authoritative package | fold × strategy × K × policy | No | Yes | Aggregated | Yes | Yes | No | No | Aggregate cross-check and eligible-path totals |
| `paper3_guarded_summary.csv` | Committed authoritative package | strategy × K × policy × metric summary across folds | No | Aggregated | Aggregated | Yes | Yes | No | No | Published mean/interval provenance |
| `paper3_guarded_tradeoff.csv` | Committed authoritative package | strategy × K × policy | No | Aggregated | Aggregated | Yes | Yes | No | No | Final reporting cross-check |
| `exclusions.csv` | Committed authoritative package | excluded fold × victim × repeat path | Yes | Yes | Yes | Maximum-budget feasibility | N/A | No | No | Eligibility denominators and reasons |
| `config.json` / `manifest.json` | Committed authoritative package | Run-level provenance | N/A | N/A | N/A | Budgets, seed, folds, cache/source hashes | N/A | N/A | N/A | Run identity verification |
| `paper3_attack_v2_by_fold.csv` | Committed attack-v2 package | fold × strategy × K | No | Yes | Aggregated | Yes | Frozen/Blind/Oracle columns | No | No | Independent aggregate comparison only |

The granular file contains 3,991,120 data rows plus its header. Its columns are:

`fold, strategy, K, sid, repeat, n_enrollment, n_genuine_probes, n_impostor_probes, n_poisoning_pool, tau0, policy_id, method, lambda, lambda_value, post_ASR, post_FRR, HTER, poison_accept_rate, malicious_updates, MUR, genuine_auth_rate, genuine_updates, GUR, mu_enroll, update_threshold_initial, mean_before, mean_after, mean_delta, sigma_before, sigma_after, sigma_delta, threshold_before, threshold_after, threshold_delta`.

## Provenance verification

The granular file is retained at:

`/Users/madigali/.codex/.chatgpt-projects/g-p-6abba505c7a0819184b45c7f142edb0d/q1-third-article/results/20260930-guarded-full-r100/subject_repeat_metrics.csv`

SHA-256:

`53d1e6aed6ef4d5e1ac3df00b448ecc563f999a9b970e5e37a160777968ad73a`

The original run directory and the committed authoritative package `results/paper3_guarded_20260930/` match byte-for-byte for every compact retained run file:

| File | SHA-256 |
|---|---|
| `paper3_guarded_by_fold.csv` | `adb3c88e09bc6e9a62eded4995ca36b6253596ff37f5b6769d7b71c327b31069` |
| `paper3_guarded_summary.csv` | `36666feaf4f1d4e986008eedc9e1cb871f1b81429264aafbd7f4eaca7155a16d` |
| `paper3_guarded_tradeoff.csv` | `9beb924a7ba0137b7b4928c3367af6e40a2de500a40cb84f03f01e73153e722d` |
| `exclusions.csv` | `07d23b0135580ce8f79812b86530f510e1ce652da8dbd00372b421b39c406d33` |
| `config.json` | `8d01a320cf4c98747349a17572cd2a6d162491b08d663ca0371bc2b56847dc31` |
| `manifest.json` | `93d4c6b9fd8feeb822a1c17afdfb8551584bcb7d758e869aaa07ce6ed59c4468` |

This establishes that the granular file belongs to the same frozen run as the committed aggregate package. The granular file itself was not copied into or reconstructed from the compact package.

## Pairing audit

- Exact key: `(fold, sid, repeat, strategy, K)`.
- Every eligible boundary (K=8) key had exactly one Blind row and one Frozen row.
- Blind and Frozen rows had the same held-out impostor-probe denominator within each paired path.
- Number of paired eligible paths: 49,889.
- Number of excluded maximum-budget paths: 111.
- Possible fold-victim-repeat paths: 50,000 = 5 folds × 100 victims × 100 repeats.
- Contributing fold-victim units after repeat averaging: 500.
- Contributing victims after fold averaging: 100.
- The reaggregated mean effect reproduced the frozen fold-level Blind-minus-Frozen mean to floating-point tolerance.

Therefore, the paired subject-level analysis is feasible.

## Reanalysis method

1. For each eligible `(fold, sid, repeat)` boundary (K=8) path, calculate Blind post-ASR minus Frozen post-ASR in percentage points.
2. Average repeats within each fold and victim.
3. Average each victim across its five available fold-level means.
4. Resample the 100 victim effects with replacement for 10,000 draws using seed 4242.
5. Report the mean subject effect and the 2.5th and 97.5th percentiles.

Result:

- Mean paired effect: +31.037638 percentage points.
- 95% percentile-bootstrap CI: [+26.946230, +35.202592] percentage points.
- Reporting precision: +31.04 points, 95% CI [+26.95, +35.20].

The subject-level effects are saved in `paper/hmog_primary_poisoning_effect.csv`; the 10,000 bootstrap draws are saved in `paper/hmog_primary_poisoning_bootstrap.csv`.

**Derived only from retained frozen outputs; no experiment, rescoring, or attack rerun was performed.**

## Victim × impostor-source audit

The retained granular outcome rows do not include the identities of impostor sources contributing to each probe pool or their source-specific accepted counts. They retain only the total number of impostor probes in a path. Exact source contributions cannot be recovered from the committed summaries or from the granular metric rows.

Accordingly, a victim × impostor-source two-way bootstrap for the primary poisoning contrast is **infeasible from retained outcome-level records**. It was not approximated and `paper/hmog_primary_poisoning_two_way_bootstrap.csv` was not created. Reconstructing source contributions from score caches, seeds, or attack code would recreate partitions/path outcomes and is outside the authorized reanalysis.

## Residual provenance risk

The 1.2 GB granular file is not present in the current compact Git result package. The analysis is provenance-verifiable because its compact outputs match the authoritative package byte-for-byte and the granular SHA-256 is recorded here. For long-term reproducibility, the granular file should be deposited in a controlled archive or repository release that supports large files, without modifying the frozen experimental package.
