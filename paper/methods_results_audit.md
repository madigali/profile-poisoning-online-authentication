# Methods and Results Numerical-Provenance Audit

## Scope and rules

This audit covers every numerical claim in paper/methods.md and paper/results.md. No model was retrained, no score was regenerated, no validation-stopped outer test was opened, and no frozen result file was modified. Result values were copied from the committed frozen packages. Unless stated otherwise, rates and effects in the manuscript were rounded to two decimal places for prose; equations, hyperparameters, seeds, counts, hashes, and Git identifiers were retained exactly.

The authoritative HMOG package is the registry in results/README.md and the final read-only aggregation in results/paper3_final_analysis_20261002_v2. For clean drift, the authoritative Oracle package is results/paper3_oracle_all_drift_20261001_v2, not the similarly named non-v2 working directory. The authoritative external package is results/paper3_external_mcgill_20261003_v1.

## Figure and table placeholder mapping

| Manuscript placeholder | Frozen artifact |
|---|---|
| Fig. [POISONING] | results/paper3_final_analysis_20261002_v2/figures/figure1_poisoning_asr.pdf |
| Fig. [TRADEOFF] | results/paper3_final_analysis_20261002_v2/figures/figure2_security_adaptation_tradeoff.pdf |
| Fig. [TRAJECTORY] | results/paper3_final_analysis_20261002_v2/figures/figure3_selection_bias_mechanism.pdf |
| Table [MAIN_RESULTS] | results/paper3_final_analysis_20261002_v2/paper3_final_summary_table.md plus the frozen detailed CSVs listed below |
| Fig. [MCGILL_POISONING] | results/paper3_external_mcgill_20261003_v1/figures/external_poisoning_asr.pdf |
| Fig. [MCGILL_TRADEOFF] | results/paper3_external_mcgill_20261003_v1/figures/external_temporal_tradeoff.pdf |
| Fig. [MCGILL_TRAJECTORY] | results/paper3_external_mcgill_20261003_v1/figures/external_selection_bias_trajectory.pdf |
| Table [MCGILL] | results/paper3_external_mcgill_20261003_v1/external_replication_summary.md and the detailed frozen CSVs listed below |

## Methods claims

| Methods location | Numerical or protocol claim | Authoritative source | Frozen-source status | Prose handling |
|---|---|---|---|---|
| 3.1 | HMOG freeze tag paper3-method-freeze-2026-10-02; McGill tag paper3-external-mcgill-v1-2026-10-03 | Git annotated tags; paper/notes.md D018, D021 | Frozen | Exact |
| 3.2 | 100 subjects; nominal 24 sessions/subject; 2,392 usable sessions; 4,784 sequences | paper/paper1_paper2_fact_check.md, Paper 2 Dataset section; revised_results dataset metadata | Verified primary-source audit | Exact |
| 3.2 | 100 Hz assumption; 500-sample offset; 20 windows/session; 100 samples/window; six statistics × six channels = 36 features; 10-window sequence; step 10 | paper/paper1_paper2_fact_check.md, Preprocessing and Protocol; src/hmog_revised_experiment.py constants and feature extraction | Canonical Paper 2 pipeline | Exact |
| 3.2 | Five folds; g(r) = (r − 1) mod 5; one test group, one validation group, three fitting groups | paper/paper1_paper2_fact_check.md, Protocol; src/hmog_revised_experiment.py fold construction | Canonical Paper 2 pipeline | Exact |
| 3.2 | LSTM: two layers; hidden size 64; dense 32; dropout 0.30; 100 classes; lr 1e-3; batch 256; 20 epochs; early-stop patience 4; scheduler factor 0.5/patience 2 | paper/paper1_paper2_fact_check.md, Models/LSTM; src/hmog_revised_experiment.py | Canonical Paper 2 pipeline | Exact |
| 3.3 | EMA epsilon 1e-4; alpha 0.05; moment, sigma, threshold, k, and accepted-only update equations | paper/paper1_paper2_fact_check.md, Adaptive Agent; src/hmog_revised_experiment.py AdaptiveEMA | Canonical Paper 2 pipeline | Exact |
| 3.3/3.5 | Guarded lambda 0.25; exploratory grid 0, 0.25, 0.50, 0.75, 1.00 | paper/notes.md D006; results/paper3_guarded_20260930/config.json | Frozen protocol/run | Exact |
| 3.4 | K = 0, 1, 2, 4, 8; five folds; 100 repeats; seed 4242; 50% source-session-group probe allocation | src/paper3_poisoning_attack_v2.py defaults and run logic; results/paper3_guarded_20260930/config.json; paper/notes.md D007 | Frozen protocol/run | Exact |
| 3.6 | D = 0, 1, 2; 36-dimensional standardized shift; seed 42 + fold; 10 time steps/sequence | paper/paper1_paper2_fact_check.md, Drift; src/hmog_revised_experiment.py drift function | Verified canonical pipeline | Exact |
| 3.6 | within=0 adaptation; within=10 checkpoint; minimum four complete pairs; first two early and last two late | paper/notes.md D008; results/paper3_oracle_all_drift_20261001_v2/config.json; src/paper3_guarded_drift.py | Frozen protocol/run | Exact |
| 3.8 | TQ-v1 grid: b/sigma = 0.25, 0.50, 0.75; m = 2, 3; recovery alpha = 0.025, 0.050; anchor/sigma = 0.10, 0.25 | paper/notes.md D012; src/paper3_temporal_recovery.py; results/paper3_tq_clean_drift_20261001_v1/config.json | Frozen before outer evaluation | Exact |
| 3.8 | Fixed TQ-v1 controls: dispersion 0.50 sigma; mean cap 0.10 sigma; threshold cap 0.05 sigma; lambda 0.25; trusted alpha 0.05 | Same sources as preceding row | Frozen before outer evaluation | Exact |
| 3.8 | Validation uses first two sessions for initialization; security limits +1.0 pp FAR and +0.5 pp HTER; 95% CI criterion | paper/notes.md D012; results/paper3_tq_clean_drift_20261001_v1/primary_assessment.json | Frozen protocol | Exact |
| 3.9 | Recovery episode lasts three distinct adaptation observations; same +1.0 pp FAR/+0.5 pp HTER limits; fold 4 gate stop | paper/notes.md D014–D015; results/paper3_tq_v2_validation_failed_20261001/validation_failure.json | Frozen validation-stop package | Exact; validation outcome also reported in Results |
| 3.10 | q20/q50; invalid span below 1e-8; rho = 0.80, 0.90, 0.95; same +1.0 pp FAR/+0.5 pp HTER gate | paper/notes.md D016; src/paper3_robust_quantile.py; results/paper3_quantile_validation_failed_20261001_v1/validation_failure.json | Frozen validation-stop package | Exact |
| 3.11 | 10,000 percentile-bootstrap draws; 95% CIs; 99-subject complete-five-fold sensitivity | results/paper3_oracle_all_drift_20261001_v2/config.json and paired bootstrap CSV; results/paper3_tq_clean_drift_20261001_v1/config.json | Frozen run outputs | Exact |
| 3.12 | McGill: 20 subjects, two days, four accelerometer-derived channels, 40 ms median interval, approximately 25 Hz, 128 samples/window, approximately 5.12 s, no overlap | experiments/external_replication_mcgill.md fields 1–9; experiments/external_replication_mcgill.json dataset block | Frozen before training/Day 2 | Exact except approximate conversions as labeled |
| 3.12 | Day-1 60/20/20 split; one-layer LSTM; input 4; hidden 64; 20 classes; batch 128; 30 epochs; patience 5; lr 0.001; weight decay 0.0001 | experiments/external_replication_mcgill.md fields 10–13; companion JSON model block | Frozen before training/Day 2 | Exact |
| 3.12 | McGill alpha 0.05; sigma floor 1e-4; Guarded lambda 0.25 | experiments/external_replication_mcgill.md fields 14–15; companion JSON profile block | Frozen before Day 2 | Exact |
| 3.12 | McGill K = 0, 1, 2, 4, 8; 100 repeats; 50% identity split; 160 Day-2 windows; 80 units; first/last 20 units | experiments/external_replication_mcgill.md fields 11, 16–21; companion JSON attack/temporal blocks | Frozen before Day 2 | Exact |
| 3.12 | Viability gate: at least 16 validation classes and top-1 at least 20% | experiments/external_replication_mcgill.md field 22; companion JSON test_gate | Frozen before training/Day 2 | Exact |
| 3.13 | Freeze commits 476cf91 and 06feb48 | Git tags and commit objects | Frozen | Seven-character commit abbreviations |
| 3.13 | McGill archive and score-cache SHA-256 values | paper/notes.md D020–D021; external manifest score_cache_sha256 | Frozen provenance | Exact 64-character hashes |

## Results claims

| Results location | Numerical claim in prose | Authoritative table/field | Frozen result reproduced? | Rounding or derivation |
|---|---|---|---|---|
| 4.1 | Boundary ASR across K: Blind 22.92, 27.50, 33.68, 44.31, 53.96%; Frozen K=8 22.92% | results/paper3_final_analysis_20261002_v2/paper3_final_poisoning_plot_data.csv, boundary rows; underlying results/paper3_attack_v2/paper3_attack_v2_summary.csv | Yes | Rounded from frozen fold-macro means |
| 4.1 | Boundary K=8 Blind−Frozen +31.04 pp | results/paper3_attack_v2/paper3_attack_v2_summary.csv, strategy=boundary, K=8, metric=blind_minus_frozen_post_ASR, mean=31.03763830676051 | Yes | Rounded to +31.04; not recomputed from rounded display values |
| 4.1 | Random Blind ASR across K: 22.92, 23.38, 23.88, 25.09, 27.55% | final poisoning plot data, random Blind rows | Yes | Rounded to two decimals |
| 4.2 | Boundary K=8 Frozen/Blind/Guarded ASR 22.92/53.96/22.93%; Blind/Guarded MUR 100.00/1.63% | results/paper3_final_analysis_20261002_v2/paper3_final_lambda_sweep.csv; attack-v2 summary for Frozen/Blind | Yes | Rounded to two decimals |
| 4.2 | Lambda-sweep endpoints: MUR 100.00 to 0.13%; GUR 85.96 to 41.78% | paper3_final_lambda_sweep.csv, boundary K=8, lambda=0 and 1 rows | Yes | Rounded to two decimals; sweep labeled exploratory |
| 4.3 | D=2 Frozen FRR/FAR/HTER 32.53/22.86/27.70%; Blind 32.20/23.80/28.00%; Guarded 34.60/21.73/28.16% | results/paper3_final_analysis_20261002_v2/paper3_final_clean_drift.csv, claimant_only D=2 | Yes | Rounded to two decimals |
| 4.3 | Blind effects: FRR gain +0.33 [−1.20,+1.93], FAR +0.93 [−0.58,+2.64], HTER gain −0.30 [−1.02,+0.40] | results/paper3_oracle_all_drift_20261001_v2/paper3_guarded_drift_paired_bootstrap.csv, all_available_folds, claimant_only D=2, Blind | Yes | Rounded to two decimals |
| 4.3 | Guarded effects: FRR gain −2.07 [−3.53,−0.63], FAR −1.14 [−2.29,+0.12], HTER gain −0.46 [−1.16,+0.21] | Same paired bootstrap CSV, Guarded lambda=0.25 rows | Yes | Rounded to two decimals |
| 4.4 | Oracle FRR gains D=0/1/2: +4.73 [+3.17,+6.33], +5.10 [+3.40,+6.80], +6.60 [+4.90,+8.40] | Same paired bootstrap CSV, Oracle-all late_FRR_gain rows | Yes | Rounded to two decimals |
| 4.4 | Oracle FAR changes D=0/1/2: +5.51 [+3.79,+7.40], +5.67 [+3.85,+7.71], +6.08 [+4.20,+8.16] | Same paired bootstrap CSV, Oracle-all late_FAR_change rows | Yes | Rounded to two decimals |
| 4.4 | Oracle HTER gains D=0/1/2: −0.39 [−1.22,+0.42], −0.28 [−1.26,+0.65], +0.26 [−0.59,+1.09] | Same paired bootstrap CSV, Oracle-all HTER_gain rows | Yes | Rounded to two decimals |
| 4.4 | Five checkpoints; Guarded update rate 63.47 to 51.68%; Oracle 100% | results/paper3_final_analysis_20261002_v2/paper3_final_selection_bias_plot_data.csv, checkpoints 1 and 5 | Yes | Rounded to two decimals |
| 4.5 | TQ-v1 FRR/FAR/HTER 33.43/20.92/27.18% versus Frozen 32.53/22.86/27.70% | results/paper3_final_analysis_20261002_v2/paper3_final_clean_drift.csv, claimant_only D=2 | Yes | Rounded to two decimals |
| 4.5 | TQ FRR gain −0.90 [−1.80,0.00]; FAR −1.94 [−2.46,−1.43]; HTER gain +0.52 [+0.10,+0.94] | results/paper3_tq_clean_drift_20261001_v1/paper3_tq_paired_subject_bootstrap.csv; primary_assessment.json | Yes | Rounded to two decimals; numerical upper FRR bound 8.33e−17 rendered as 0.00 |
| 4.5 | Two-way FAR −1.94 [−2.48,−1.42] | results/paper3_tq_clean_drift_20261001_v1/paper3_tq_two_way_far_bootstrap.csv | Yes | Rounded to two decimals |
| 4.5 | 1,404 trusted and 49 recovery updates | paper/notes.md D013; event fields in results/paper3_tq_clean_drift_20261001_v1/paper3_tq_checkpoints.csv | Yes | Exact integer counts from frozen event audit |
| 4.6 | Fold 4 no feasible config; best FRR gain −4.55 pp; minimum HTER degradation +0.89 pp; outer false | results/paper3_tq_v2_validation_failed_20261001/validation_failure.json and paper3_tq_v2_selected_by_fold.csv | Yes, validation only | Rounded to two decimals; no outer result |
| 4.7 | Five folds; rho grid 0.80/0.90/0.95; no feasible rho; Accepted-only at 0.95: FRR −10.64, FAR −4.89, HTER +2.87 pp | results/paper3_quantile_validation_failed_20261001_v1/validation_failure.json; paper3_quantile_validation_summary.csv; paper/notes.md D017 | Yes, validation only | Frozen descriptive across-fold means, rounded to two decimals |
| 4.7 | Oracle-all Quantile at 0.95: FRR −4.62, FAR −1.83, HTER +1.39 pp | paper3_quantile_validation_summary.csv, five quantile_oracle rho=0.95 rows; paper/notes.md D017 for FRR/HTER | Yes, validation only | FRR and HTER are frozen D017 means. FAR −1.83 is the two-decimal unweighted mean of the five frozen fold fields (−1.8686869, −1.8636364, −2.7805915, −0.7601265, −1.8939394); no outer data used |
| 4.8 | Day-1 top-1 58.12%; gate 20% | paper/notes.md D021; experiments/external_replication_mcgill.json test_gate | Yes | Rounded run accuracy; exact gate |
| 4.8 | Boundary K=8 ASR Frozen/Blind/Guarded 12.37/32.09/12.48% | results/paper3_external_mcgill_20261003_v1/attack_summary_bootstrap.csv, boundary K=8 post_ASR rows | Yes | Rounded to two decimals |
| 4.8 | Blind−Frozen +19.72 [5.58,37.34]; Guarded−Blind −19.62 [−37.17,−5.60] pp | external paired_effects.csv, first two rows | Yes | Rounded to two decimals |
| 4.8 | MUR Blind/Guarded 100.00/32.22%; paired change −67.78 [−84.30,−49.47] pp | external attack_summary_bootstrap.csv and paired_effects.csv | Yes | Rounded to two decimals |
| 4.8 | 18 boundary victims; 544/2,000 infeasible victim-repeat paths | external paired_effects.csv n_subjects; exclusions.csv; manifest n_boundary_exclusions; paper/notes.md D021 | Yes | Exact counts |
| 4.8 | Random effect +1.51 [−0.09,+4.43] pp across 20 subjects | external paired_effects.csv, random contrast | Yes | Rounded to two decimals |
| 4.8 | Temporal FRR/FAR: Frozen 78.00/11.46%; Guarded 81.00/10.29%; Oracle 12.75/75.05%; HTER 44.73/45.64/43.90% | external temporal_summary_bootstrap.csv | Yes | Rounded to two decimals |
| 4.8 | Guarded−Frozen FRR +3.00 [0.00,+7.00]; Oracle−Frozen FRR −65.25 [−83.75,−45.50]; Oracle−Guarded FAR +64.76 [+48.93,+79.24] pp | external paired_effects.csv | Yes | Rounded to two decimals |

## Non-numerical provenance checks

- The final HMOG manifest confirms that attack-v2 and Guarded Frozen/Blind baselines match, Guarded lambda=0 matches Blind EMA, clean-drift baselines match the TQ-v1 export, and both stopped branches retain outer_test_loaded=false.
- TQ-EMA v2 and Adaptive Quantile have no outer tables, bootstraps, or outer trajectory figures. Methods and Results report validation outcomes only.
- HMOG drift is described throughout as synthetic standardized-feature drift. Only McGill uses a natural two-day temporal separation.
- Oracle EMA and Oracle-all-genuine are labeled controls or diagnostics and never described as deployable.
- The carried-forward Guarded lambda is labeled exploratory and never described as universally optimal.
- McGill is described as a mechanism-level replication and not as a direct performance benchmark against HMOG.
- whuGAIT rejection is described as a dataset-selection decision caused by missing chronology fields, not as an experimental outcome.
- The Results section contains observations and inferential status only; mechanistic causal interpretation is reserved for Discussion.

## Discrepancies and resolution

| Issue | Resolution used in Methods/Results |
|---|---|
| results/paper3_final_analysis_20261002_v2/paper3_final_checklist.json says Paper 1/Paper 2 primary facts were not yet verified. | The checklist predates the later primary-source audit at paper/paper1_paper2_fact_check.md and commit 4b83d61. The later audit is authoritative for Methods. No Paper 3 result changed. |
| The short Paper 2 PDF omits ReduceLROnPlateau, whereas the canonical code uses factor 0.5 and patience 2. | Methods discloses the canonical-code scheduler as an implementation detail. This is the same resolution recorded in the fact-check document. |
| paper/notes.md records original run-directory names, while results/README.md registers normalized committed package names. | The committed registry and manifests were used. Original names were treated as historical run identifiers, not competing numerical sources. |
| A non-v2 Oracle drift working directory is present locally. | It was not used. All Oracle drift values come from results/paper3_oracle_all_drift_20261001_v2 and the final aggregator. |
| Oracle-all Quantile late-FAR change −1.83 pp is not printed in D017 as a single aggregate. | The prose value is the two-decimal descriptive mean of the five frozen rho=0.95 Oracle fold rows in paper3_quantile_validation_summary.csv. The five inputs are listed above. This is a reporting aggregation of frozen validation outputs, not an outer-test calculation. |
| Requested test counters 47/47 and 59/59 were not found in authoritative committed artifacts. | Methods reports the documented invariant-suite coverage and successful deterministic rerun, but omits those two counters. |
| The external manifest records the code revision active when outputs were generated, while tag 06feb48 is the later commit that added the frozen outputs. | Methods identifies the tag as the committed result-package freeze and relies on the manifest for generation-time provenance. These refer to different lifecycle points and are not treated as conflicting results. |

## Citation placeholders remaining

The manuscript currently retains four explicit placeholders:

1. HMOG original dataset citation.
2. Paper 2 citation with final proceedings metadata when available.
3. McGill Gait dataset citation.
4. whuGAIT dataset/repository citation for the dataset-selection account.

No numbered or fabricated references were inserted.
