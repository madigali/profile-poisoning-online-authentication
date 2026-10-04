# Editorial Revision Round 3

Revision date: 4 October 2026.

## 1. Baseline and scope

The editorial baseline is Git revision `94ebe1931fdde6ba1ce40fad24418482302f1f5c` on branch `paper3-external-replication`. Round 3 may update only the seven modular article sections, the assembled manuscript, Supplementary Methods, Supplementary Results, this audit, and `paper/content_preservation_matrix.md`. Frozen code, protocols, results, figures, manifests, tags, decision logs, and historical audits remain unchanged. The pre-existing untracked directories `release/`, `results/paper3_guarded_drift_20260930/`, and `results/paper3_oracle_all_drift_20261001/` remain outside the revision.

This is an editorial revision. It will not train a model, generate scores or attack paths, rerun a method, perform bootstrap resampling or another inference procedure, add an operating point, search the literature, or inspect validation-stopped outer outcomes.

## 2. Compression plan recorded before manuscript editing

Raw counts below use `wc -w` semantics on the Round-2 Markdown modules. Targets are editorial guides rather than journal requirements.

| Section | Round-2 raw words | Target | Planned compression | Material that must remain in the main article |
|---|---:|---:|---|---|
| Abstract | 299 | 260-290 | Define the score-informed boundary setting and synthetic HMOG shift; remove cross-cohort metric overload | Research question, design, reference amplification, nominal-1% reversal, same-cohort FRR cost, state-dependent Guarded scope |
| Introduction | 1,305 | 700-800 | Remove the dissertation chronology, merge background, and reduce six contributions to three | Prior baseline disclosure, accepted-only feedback mechanism, threat-model scope, operating-point limitation, McGill role |
| Related Work | 1,848 | 900-1,050 | Replace the broad catalogue with four focused themes and avoid discussing the present results at length | Representative mobile/inertial work; Giot; Biggio, Lovisotto, and Xue; analogous selective-feedback literature; precise residual contribution |
| Methods | 4,515 | 2,450-2,700 | Present the protocol rather than development history; move training detail, implementation precision, chronology, exclusions, recovery specifications, seeds, hashes, and invariant lists to Supplement | Dataset/partition design, score generation, calibration, EMA and Guarded equations, attack protocol, clean checkpoints, sensitivity design, endpoints, aggregation, bootstrap, evidence status |
| Results | 2,166 | 1,750-1,950 | Merge reference Blind/Guarded subsections, retain two operating-point tables, and remove prose that repeats table cells | Both reference effects, operating-point dependence, same-cohort FRR/HTER, feasibility, gate activity, clean Oracle diagnostic, McGill results, stopped branches |
| Discussion | 3,409 | 1,300-1,500 | Merge twelve subsections into five and state each major limitation once | Coupled effects, operating-point scope, state-dependent gate, Oracle interpretation, negative recovery probes, McGill scope, limitations and concise future work |
| Conclusion | 670 | 250-300 | Remove the development sequence and retain bounded implications | Coupled effects, reference amplification and strict-point reversal, Guarded margin, no demonstrated safe recovery, joint endpoint reporting |
| Total scientific modules | 14,212 | 8,000-8,500 | Reduce repeated explanation while preserving the Round-2 evidence boundary | All items listed above |

Planned Supplement expansion:

- Add the full evidence-status chronology removed from Methods.
- Preserve detailed HMOG and McGill training configurations, calibration precision, exclusions, statistical provenance, seeds, hashes, and protocol checks.
- Retain the complete TQ-EMA and Quantile specifications and validation outcomes.
- Add the figure/table mapping and any main-text methodological detail needed for reproducibility.

## 3. Required language correction

Round 3 will distinguish the common form of the authentication decision rule from realized decisions. Each adaptive method has its own current state and derived threshold, so subsequent accept/reject outcomes can differ. The malicious-update-blocking Oracle coincides with Frozen during the malicious-only phase because its profile does not update. Oracle-all retains the decision-rule form but changes update eligibility and therefore can change later thresholds and decisions. Guarded retains the access-rule form; its distinct update history can likewise change later thresholds and access outcomes.

## 4. Counting method

The final audit will report five quantities:

1. raw `wc -w` counts for each Markdown module before and after revision;
2. editorial main prose, including Abstract, after removing headings, display equations, citation commands, inline mathematical markup, insertion markers, tables, captions, and References;
3. captions and table-cell text, counted separately after removing Markdown separators;
4. References, counted separately from the assembled manuscript;
5. Supplement, reported both as raw Markdown words and as editorial prose plus display text.

This separation prevents moved tables, LaTeX commands, paths, and hashes from being presented as ordinary-prose reduction.

## 5. Execution record

### 5.1. Completed editorial changes

The seven scientific modules were compressed and reorganized without changing the title placeholder, experimental outcomes, frozen artifacts, or reference database. The Introduction now gives the inherited baseline disclosure and three contributions without the Paper-1/Paper-2/Paper-3 development narrative. Related Work retains the closest mobile-authentication, adaptive-update, biometric-poisoning, and selective-feedback precedents. Methods now presents the executed protocols in eight sections; detailed training settings, implementation precision, chronology, recovery-state specifications, seeds, hashes, and invariant checks are in Supplementary Methods S1-S10. Results follows the five-part structure specified in the revision brief. Discussion was consolidated from 12 subsections to five, and Conclusion was reduced to three bounded paragraphs.

The Supplement was expanded before corresponding detail was removed from the main article. Supplementary Methods now contains a full evidence-status chronology; detailed HMOG and McGill pipelines; calibration, threat-model, uncertainty, provenance, and reproducibility information; and the complete TQ-v1, TQ-v2, and Quantile specifications. Supplementary Results retains the stopped-branch evidence, operating-point diagnostics, additional Oracle levels, and all three frozen McGill figures.

### 5.2. Decision-rule correction

The article and Supplement now distinguish a common decision-rule form from realized decisions under method-specific state. Guarded uses the same access-rule form as the other profiles, but its different update history can change later state, thresholds, and accept/reject outcomes. The malicious-update-blocking Oracle applies the common rule to an unchanged profile and therefore coincides with Frozen only during the malicious-only phase. Oracle-all changes genuine update eligibility; its resulting state can change later thresholds and decisions. No text claims that adaptive methods necessarily make the same authentication decisions or that Guarded leaves the whole threshold trajectory unchanged. This is a wording correction only; implementation and outcomes were not changed.

### 5.3. Word counts

Raw counts use `wc -w` semantics on the Markdown modules. The editorial count tokenizes alphanumeric scientific words after removing headings, citation commands, inline mathematical markup, code spans, insertion markers, Markdown table separators, and References. Display equations, table-cell text, and captions are reported separately. This makes the prose reduction independent of moved tables and technical markup.

| Section | Round 2 raw words | Round 3 raw words | Change |
|---|---:|---:|---:|
| Abstract | 299 | 283 | -16 |
| Introduction | 1,305 | 760 | -545 |
| Related Work | 1,848 | 1,084 | -764 |
| Methods | 4,515 | 3,001 | -1,514 |
| Results | 2,166 | 2,006 | -160 |
| Discussion | 3,409 | 1,632 | -1,777 |
| Conclusion | 670 | 265 | -405 |
| **Scientific modules** | **14,212** | **9,031** | **-5,181 (-36.5%)** |

Round-3 main ordinary prose, including Abstract, contains 8,041 editorial words. Main display equations contain 80 words by the same tokenizer; main table cells contain 255; and main captions contain 327. The assembled References section contains nine raw Markdown words because reference generation remains the existing post-journal-selection placeholder. The Supplement contains 3,616 raw Markdown words: 2,424 ordinary prose, 41 display-equation words, 425 table-cell words, and 305 caption words. The higher raw main total relative to the 8,041-word prose count reflects equations, tables, captions, Markdown syntax, and insertion markers rather than hidden narrative text.

### 5.4. Section mapping

| Round-2 material | Round-3 location |
|---|---|
| Introduction background, six contributions, and research-program chronology | Shortened Introduction with three contributions and a concise inherited-baseline disclosure |
| Related Work 2.1-2.5 | Four sections: mobile authentication; adaptive profiles and poisoning; decision-conditioned feedback; study position |
| Methods 3.1-3.12 | Methods 3.1-3.8, with implementation/provenance detail in Supplementary Methods S1-S10 |
| Results 4.1-4.2 | Results 4.1 reference poisoning and Guarded updating |
| Results 4.3 | Results 4.2 operating-point sensitivity, feasibility, and gate activity |
| Results 4.4-4.5 | Results 4.3 clean temporal behavior and Oracle diagnostic |
| Results 4.7 and 4.8 | Results 4.4 McGill corroboration; duplicate cross-dataset summary removed |
| Results 4.6 | Results 4.5 concise status; full evidence in Supplementary Results S1-S3 |
| Discussion 5.1-5.12 | Five sections covering coupled effects, state-dependent authorization, Oracle/recovery evidence, external implications, and limitations/future work |

The detailed evidence-level mapping is in `paper/content_preservation_matrix.md`.

### 5.5. Figure and table mapping

| Round-2 display | Round-3 display | Frozen artifact or source | Placement |
|---|---|---|---|
| Figure 1 | Figure 1 | `figure1_poisoning_asr` | Main |
| Figure 2 | Figure 2 | `boundary_k8_effects` | Main |
| Figure 3 | Figure 3 | `figure2_security_adaptation_tradeoff` | Main |
| Figure 4 | Figure 4 | `figure3_selection_bias_mechanism` | Main |
| Figures 5-7 | Figures S4-S6 | `external_poisoning_asr`, `external_temporal_tradeoff`, `external_selection_bias_trajectory` | Supplement |
| Supplementary Figures S1-S3 | Figures S1-S3 | `calibration_vs_heldout_far`, `boundary_feasibility`, `guarded_gate_diagnostics` | Supplement |
| Tables 1-2 | Tables 1-2 | Frozen operating-point summary/effect tables | Main |
| Table 3 supporting-probe summary | Table S3 | Frozen TQ/Quantile status | Supplement; column renamed `Evaluation status` |
| Table 4 McGill effects | Table 3 | Frozen McGill poisoning and temporal packages | Main, compact numerical evidence |
| Detailed TQ validation tables | Tables S1-S2 | Frozen TQ-v1 and TQ-v2 packages | Supplement |

Figure artwork was neither regenerated nor modified. Captions now identify dataset, condition, metric, cohort/aggregation, and the meaning of uncertainty where applicable. In particular, Figure 1 describes its fold-level bands as descriptive and directs primary inference to the paired victim-bootstrap interval in the text.

### 5.6. Citation and consistency checks

The final main and Supplement modules cite 36 unique keys. All resolve in the unchanged 39-entry `references.bib`; three unused entries remain available and were not deleted for editorial economy. Literature-derived claims retained their adjacent citations after movement. The assembled manuscript uses the seven modules as its source and contains the same scientific text after figure/table placeholder numbering is resolved.

The final editorial checks confirmed that the Abstract states the synthetic HMOG shift, explains the eight selected poisoning presentations, marks Oracle-all as non-deployable, reports reference amplification and the nominal-1% reversal, and retains the genuine-rejection cost. Main Results retains the same-cohort FRR and HTER deterioration, effective Guarded-margin interpretation, calibration-transfer distinction, conditional feasibility, and McGill evidence. TQ-v2 and Quantile remain validation-stopped with `outer_test_loaded=false` and no outer estimates.

### 5.7. Unresolved source issues

Three source limitations remain explicit rather than being filled by editorial inference:

1. The inherited HMOG source does not document a scientific rationale for discarding the first 500 samples or retaining only the next two sequences per usable session.
2. Numeric HMOG session identifiers define the executed replay order, but the available source does not independently validate them as a natural behavioral chronology.
3. The exact reference HMOG approximate-EER candidate, tie, and interpolation procedure is not independently documented beyond the canonical code/output path.

These issues are disclosed in Methods, Supplementary Methods, or Discussion as appropriate. They do not authorize a protocol rewrite in this editorial revision.

### 5.8. Analysis boundary

Round 3 performed text parsing, word counts, citation-key resolution, frozen-number comparison, and structural consistency checks only. It did not train a model, generate scores or attack paths, rerun a method, resample a bootstrap, perform a new statistical test, open a validation-stopped outer result, add a dataset or operating point, modify a frozen figure, or run the experimental test suite.
