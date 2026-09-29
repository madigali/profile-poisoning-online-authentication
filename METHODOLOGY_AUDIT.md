# Methodology audit and revision record

## Status of the previously reported results

The numerical results produced by `hmog_baseline.py`, `hmog_lstm_light.py`,
`hmog_cache_probas.py`, `hmog_analysis.py`, and `hmog_analysis_E.py` are not
valid evidence for the manuscript. They are retained only as a record of the
earlier analysis. The revised paper must use only files in `revised_results/`
produced by `hmog_revised_experiment.py`.

The most important defect was a sensor-column parsing error. HMOG inertial CSV
files contain metadata in columns 1--3 and 7; the physical x/y/z readings are
columns 4--6. The older scripts used zero-based slice `1:4`, which included two
timestamps/identifiers and only one physical axis. One of those fields encodes
the subject/session, creating direct identity leakage and explaining the
implausibly low EER values.

## Findings and corrections

| Priority | Earlier problem | Consequence | Revised protocol |
|---|---|---|---|
| P0 | Wrong HMOG columns (`1:4` instead of `3:6`) | Subject/session metadata leaked into features | Parse only physical axes in columns 4--6 for both sensors |
| P0 | Validation samples also appeared in the training loader | Invalid early stopping and optimistic model selection | Use a session-disjoint inner validation partition and exclude it from fitting and scaler estimation |
| P0 | Random `GroupKFold` over ad-hoc blocks did not place every subject in every fold | Folds contained only 93--96 subjects and unequal test counts | Assign whole sessions by `(session_number-1) mod 5`; require all subjects in fit, validation, and test |
| P0 | Sequences could cross session boundaries and sessions were processed in ZIP order | False temporal continuity and unreliable chronology | Sort sessions numerically and construct sequences inside one session only |
| P0 | Static threshold was calibrated on the early test segment | Test-label leakage into the deployment operating point | Initialize both static and adaptive thresholds from the inner validation/enrollment partition only |
| P0 | Agent was evaluated on a stream with about 99 impostors per genuine attempt | Threshold dynamics were dominated by an unrealistic attack prevalence | Use a stated, balanced alternating stress-test stream with repeated deterministic impostor sampling |
| P0 | Rejections decayed the threshold toward zero | Fail-open behavior and high FAR after rejection bursts | Never lower the threshold because of unauthenticated rejections; update only after accepted attempts |
| P0 | Agent floor was selected using all test folds and drift levels | Circular test-set model selection | Fix agent parameters before the test run; no test-set sweep selects a headline configuration |
| P1 | LSTM and classical baselines used different observation lengths | Baseline comparison did not isolate model class | Give all methods the identical 10-by-36 sequence; flatten it only for SVM/RF input |
| P1 | Overlapping test sequences repeatedly reused the same windows | Correlated endpoints and repeated EMA updates | Use non-overlapping 10-window sequences (`sequence_step=10`) |
| P1 | EER used a 500-percentile approximation | Ties and discrete RF scores could shift the estimate | Use all exact ROC thresholds and macro-average per-subject EER |
| P1 | “Agent EER” was recomputed from test margins | A second post-hoc test threshold did not represent agent decisions | Report causal agent FAR, FRR, and HTER at its actual zero-margin decision boundary |
| P1 | Accuracy was dominated by the 99:1 one-vs-all imbalance | Misleading headline metric | Remove binary accuracy as a main metric; report macro EER and calibrated FAR/FRR/HTER |
| P1 | Baseline DET plot showed only the last subject of the last fold | Figure was mislabeled as aggregate | Remove it from the revised paper unless an aggregate curve is generated |
| P2 | Main and cache scripts injected drift into different feature subsets | Results described different experiments | Maintain one canonical implementation and save its full metadata |
| P2 | Drift magnitude was called “standard deviations per feature” although the vector was L2-normalized | Incorrect physical interpretation | Define the perturbation explicitly as an L2 displacement in standardized feature space |
| P2 | Code, tables, equations, and hyperparameters described different versions | Manuscript was not reproducible | Generate the manuscript tables only from the canonical revised result files |

## Interpretation rules for the revised manuscript

1. Clean-test EER measures score separability and may be computed from test ROC
   thresholds, but those thresholds are not used for deployed decisions.
2. FAR, FRR, and HTER use thresholds initialized exclusively from the inner
   validation/enrollment sessions.
3. The LSTM-only ablation is the same trained LSTM with its initial threshold
   frozen. The full method changes only that threshold online, so the comparison
   isolates adaptation.
4. Synthetic drift is a controlled robustness test, not proof that the injected
   shift is identical to natural behavioral drift.
5. HMOG is the only dataset available in this project. External validity remains
   a limitation until the complete protocol is repeated on an independent
   session-rich inertial dataset.
6. If the agent does not improve HTER while maintaining FAR, the manuscript must
   report the negative result rather than claim successful drift mitigation.

## Reproduction

```text
/opt/anaconda3/bin/python3 hmog_revised_experiment.py
```

The script writes per-fold results, aggregate summaries, fold/session manifests,
experiment metadata, the preprocessing cache, and the revised drift figure to
`revised_results/`.
