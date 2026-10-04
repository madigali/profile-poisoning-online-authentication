# Paper 3 Technical Close-out Audit

## 1. Baseline revision and scope

**Issue.** Establish the active Round-3 baseline without restoring longer Round-2 material or disturbing unrelated local work.

**Primary evidence.** The close-out started from Git revision `14843a88403ec2fde347373bcb8909dc16280822` on branch `paper3-external-replication`. The active manuscript had three contributions, eight Methods subsections, five Results subsections, and five Discussion subsections. The pre-existing untracked directories `release/`, `results/paper3_guarded_drift_20260930/`, and `results/paper3_oracle_all_drift_20261001/` were outside the change set.

**Correction.** Work was confined to citation syntax, provenance documentation, specified wording/caption corrections, bootstrap-scope reconciliation, and inspection of the scientific Supplement.

**Verification performed.** Git status and the section structure were checked before editing. No experiment, model training, score generation, bootstrap, statistical analysis, project test suite, or stopped-branch outer-outcome access was performed. No frozen table, figure, manifest, tag, threshold, parameter, or equation was changed.

**Status.** Corrected and verified.

## 2. Citation escaping and rendering

**Issue.** The source modules and assembled manuscript contained literal `\\cite{...}` tokens rather than intended one-backslash LaTeX citation commands.

**Primary evidence.** Byte-level inspection found 9 affected groups in `paper/introduction.md`, 21 in `paper/related_work.md`, 3 in `paper/methods.md`, and the same 33 groups in `paper/manuscript_full.md`. No tracked Paper 3 assembler exists; the temporary Round-3 assembler only concatenated source modules and had not introduced the extra slash.

**Correction.** Only the exact citation token was changed from `\\cite{` to `\cite{`. Mathematical and other backslashes were untouched, and the assembled manuscript was regenerated from the corrected modules.

**Verification performed.** The corrected modules contain 63 citation-key occurrences representing 36 unique keys, and the assembled manuscript retains the same ordered sequence. All 36 keys exist in `references.bib`. The bibliography retained SHA-256 `d904dbe214499758eacf3f0aec0e48d6a28c2562265a6fecd71e673523c3c7c0`; its three unused entries were not removed. A temporary smoke document used real corrected Introduction and Methods paragraphs, a grouped citation, and the Blind-EMA formula. Pandoc 3.8 with `markdown+tex_math_single_backslash` emitted neutral `natbib` LaTeX, and `latexmk -pdf -bibtex` completed without undefined-citation warnings. Extracted PDF text contained rendered author-year citations and no literal `cite{...}` or unresolved `???`; the rendered formula was visually intact. Temporary artifacts remained outside the repository in `/private/tmp/paper3_technical_closeout/`.

**Status.** Corrected and verified.

## 3. HMOG cache provenance

**Issue.** The previous statement implied reuse of exact Paper 2 scores, whereas the retained cache builder contains training and prediction code.

**Primary evidence.** The canonical Paper 2 implementation has SHA-256 `3468a5a8c6d7e0e9a6ee61da1b7c4312ce46c46fc2ff1167457e1cd5be8e2210`, matching downstream Paper 3 manifests. `src/paper3_cache_scores.py` calls the canonical training routine once per fold and saves new fold-specific checkpoints, scalers, validation scores, and drift-specific test scores. The Paper 3 cache-verification summary differs numerically from the reported Paper 2 run, including a different selected epoch in fold 4. Downstream manifests identify the resulting cache files, and method runners load those fixed arrays without retraining.

**Correction.** Main Methods and Supplementary Methods now distinguish inherited preprocessing/training procedure, a separate Paper 3 cache-generation fit, and fixed reuse of the resulting Paper 3 caches across method comparisons. They no longer claim byte-identical reuse of Paper 2 weights or predictions.

**Verification performed.** The generation source, metadata, canonical source, retained model/cache hashes, and consuming runners were inspected as text. All retained fold base, drift-score, and model files checked against the frozen TQ-v1 manifest matched its hashes.

**Status.** Documented from source, with disclosed limitations: the cache-generation metadata does not retain the input sequence-cache hash, builder Git revision, builder-source hash, or complete dependency environment; exact Paper 2 checkpoints and prediction matrices are unavailable for byte-level comparison. The current committed builder hash cannot retrospectively close those gaps.

## 4. Approximate-EER implementation

**Issue.** The Supplement said that the reference-EER algorithm was unresolved beyond the code path.

**Primary evidence.** The canonical function used by the frozen HMOG paths calls `sklearn.metrics.roc_curve(..., drop_intermediate=False)`, computes `FNR = 1 - TPR`, selects `np.nanargmin(abs(FPR - FNR))`, returns the threshold at that first minimizing index in returned-array order, and reports `(FPR + FNR) / 2` at the same index.

**Correction.** Supplementary Methods S3.1 now specifies positive and negative labels, claimant-score orientation, observation weighting, ROC construction, `drop_intermediate=False`, the minimization rule, first-minimum behavior, absence of interpolation, returned threshold, and descriptive approximate-EER value. McGill minimum-HTER calibration and low-FAR `nextafter` calibration remain separate procedures.

**Verification performed.** The executed canonical function and each frozen caller were inspected without importing a runner or recalibrating any score. The Paper 2 release records scikit-learn 1.7.2, but that version was not attributed to the separate Paper 3 cache-generation invocation because its full environment was not preserved.

**Status.** Documented from the executed canonical implementation.

## 5. Truncation rationale and chronology limitations

**Issue.** Supplementary Methods incorrectly grouped the documented 20-window cap and undocumented initial 500-sample offset under one “no rationale” statement.

**Primary evidence.** The previous paper states that the next 20 non-overlapping windows were retained to equalize session contributions and bound computation. It does not explain the initial approximately five-second/500-sample discard. The executed replay sorts numeric session identifiers and then within-session positions.

**Correction.** Main Methods and Supplementary Methods now assign the stated rationale only to the retention cap. They keep the offset rationale unresolved and do not infer sensor stabilization, optimality, representativeness, or absence of sampling bias. HMOG remains described as session-ID-ordered replay, not independently validated natural chronology; McGill day separation remains distinct.

**Verification performed.** The Dataset/Preprocessing passage of the supplied previous-paper PDF and the corresponding source constants, slicing, sequence construction, and replay ordering were inspected.

**Status.** Documented rationale for the cap; disclosed limitation for the initial offset and natural-chronology interpretation.

## 6. Local wording and caption corrections

**Issue.** Scientific text contained internal editorial wording, an overbroad statement that the attack used no labels, and an inaccurate Figure 3 interval description.

**Primary evidence.** Dataset identities define claimant/impostor and poison/probe pools; boundary ranking uses claimant scores and initial margins; Blind and Guarded do not receive online ground-truth genuineness; Oracle controls do. The frozen Figure 3 source and plot-data table show separate absolute-FAR and absolute-FRR bootstrap intervals for each method, not paired intervals of between-method differences.

**Correction.** Internal revision-round wording was removed from the manuscript and scientific Supplement. The threat model now distinguishes offline benchmark labels, score-based ranking, production-updater information, and Oracle-only labels. Figure 3 now identifies horizontal and vertical bars as 95% subject-bootstrap percentile intervals for each method's absolute late FAR and late FRR and directs paired difference intervals to the text.

**Verification performed.** The frozen plotting source, plot-data CSV, figure hashes, and rendered artwork were checked. The points and bars agree; artwork regeneration was unnecessary and was not performed.

**Status.** Corrected and verified.

## 7. Bootstrap-scope reconciliation

**Issue.** A global statement that victim-by-impostor-source analysis existed only for HMOG nominal 1%, boundary `K=8` obscured a distinct TQ-v1 clean-temporal FAR analysis.

**Primary evidence.** The historical reference poisoning package lacks source-resolved retained outcomes. The operating-point poisoning package contains a product-weight analysis only for HMOG nominal 1%, boundary `K=8` over 100 victims, 9,088 eligible paths, and 100 observed sources. The TQ-v1 clean-temporal package separately contains a late-FAR analysis over 100 victims, 100 sources, and 9,900 observed victim-source pairs, with estimate -1.939 percentage points and 95% interval [-2.476, -1.420].

**Correction.** Methods, Discussion, and Supplementary Methods now separate historical reference poisoning, operating-point poisoning sensitivity, and TQ-v1 clean-temporal sensitivity. No interval was reconstructed or extended to another dataset or condition.

**Verification performed.** The retained historical data audit, operating-point source table and manifest, TQ-v1 two-way result, implementation, and Supplementary Results statement were cross-checked.

**Status.** Corrected and verified.

## 8. Supplement completeness and cross-references

**Issue.** The actual Supplement needed inspection against main-text promises, not acceptance based on editorial audit claims.

**Primary evidence.** Supplementary Methods S1-S10 and Supplementary Results S1-S6 exist, and all current main-text namespace references resolve. Tables S1-S3 contain frozen branch outcomes. Figures S1-S6 exist at their mapped repository-relative paths and match their frozen manifests.

**Correction.** The Supplement now includes explicit cache provenance and remaining gaps, the executed approximate-EER rule, separated preprocessing rationales, corrected label roles, separated two-way-bootstrap scopes, an authoritative package registry, principal cache and operating-point schemas, TQ validation denominators and exclusion cause, and exact repository-relative Figure S1-S6 paths. It records that subject 57 was excluded in folds 3 and 4 for fewer than four complete adaptation-checkpoint session pairs, that TQ-v1 used 100 victims in the available-fold primary analysis and 99 in complete-five-fold sensitivity, and that validation-stopped branches have no outer estimate.

**Verification performed.** Supplement headings, tables, cross-references, figure paths, file existence, hashes, manifests, validation-failure records, and exclusion files were inspected directly. No local absolute path is the sole locator for a scientific Supplement artifact.

**Status.** Corrected and verified.

## 9. Files changed and checks performed

**Issue.** The close-out required a minimal, auditable change set and a synchronized assembled manuscript.

**Primary evidence.** The authoritative modules are the Round-3 source files listed below; no committed Paper 3 assembler exists.

**Correction.** The intended tracked change set is:

- `paper/introduction.md`
- `paper/related_work.md`
- `paper/methods.md`
- `paper/results.md`
- `paper/discussion.md`
- `paper/supplementary_methods.md`
- `paper/supplementary_results.md`
- `paper/manuscript_full.md`, mechanically reassembled from the corrected Round-3 modules
- `paper/technical_closeout_audit.md`, new

**Verification performed.** Citation byte scans, citation-key resolution, module-to-assembly citation-sequence comparison, neutral citation rendering, structural heading counts, main/module consistency checks, repository-relative artifact existence checks, and Git diff/status review were performed. `references.bib`, historical audits, `paper/content_preservation_matrix.md`, frozen packages, figures, manifests, tags, and pre-existing untracked experiment directories were left unchanged.

**Status.** Corrected and verified.

## 10. Remaining blockers versus disclosed limitations

**Issue.** Distinguish submission-blocking technical defects from scientific and provenance limitations that must remain disclosed.

**Primary evidence.** Citation rendering succeeds, citation keys resolve, the assembled manuscript is synchronized, package pointers resolve, and the Supplement now contains the promised method and result details. Remaining gaps concern historical provenance and study scope rather than a broken document or contradictory frozen result.

**Correction.** No new experiment or broad editorial round was opened. Remaining limitations are stated in the manuscript or this audit: incomplete cryptographic provenance of the original Paper 3 cache-generation invocation; unavailable exact Paper 2 checkpoints/predictions; unknown rationale for the initial 500-sample offset; unverified natural meaning of numeric HMOG session order; fixed-model conditional uncertainty; synthetic HMOG shift; small and severe cross-day McGill setting; source-level poisoning uncertainty available only in one operating-point condition; and no combined drift-plus-poisoning evaluation.

**Verification performed.** Main Methods, Results, Discussion, both Supplement files, frozen manifests, and historical audits were reconciled after the local corrections. Reference amplification, the nominal-1% sign reversal, same-cohort FRR/HTER reporting, and Guarded gate algebra were checked for preservation.

**Status.** No technical blocker identified before journal selection. The listed items remain disclosed limitations, not solved scientific problems.
