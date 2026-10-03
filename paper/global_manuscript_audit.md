# Global Manuscript Audit

Audit date: 4 October 2026.

Scope: `paper/abstract.md`, `paper/introduction.md`, `paper/related_work.md`, `paper/methods.md`, `paper/results.md`, `paper/discussion.md`, `paper/conclusion.md`, `paper/manuscript_full.md`, and `references.bib`. Frozen numerical outputs and experiment artifacts were read only. No experiment, rescoring, tuning, or result aggregation was run.

Issue count after review:

| Severity | Found | Automatically corrected | Remaining |
|---|---:|---:|---:|
| Critical | 0 | 0 | 0 |
| Major | 4 | 2 | 2 |
| Minor | 5 | 2 | 3 |
| Editorial | 4 | 3 | 1 |

Issue register:

| ID | Severity | File | Section | Issue | Recommended correction | Automatically corrected? |
|---|---|---|---|---|---|---|
| GMA-01 | Major | `paper/methods.md` | 3.1, 3.12 | Five verified dataset/Paper 2 citation placeholders remained. | Insert `Sitova2016HMOG`, `Serbin2026AdaptiveLSTM`, `Frank2010McGillGaitDataset`, and `Zou2020WhuGait` where applicable. | Yes. |
| GMA-02 | Major | `paper/discussion.md` | 5.2, 5.4, 5.11 | Three verified citation placeholders remained. | Cite Paper 2 and Paper 1; cite selective-label, confirmation-bias, and performative-prediction work with an explicit analogous-not-direct qualification. | Yes. |
| GMA-03 | Editorial | `paper/abstract.md` | Results sentence | “Deployable false-rejection recovery” was stronger than required. | Use “did not establish improved false-rejection recovery under the frozen constraints.” | Yes. |
| GMA-04 | Editorial | `paper/conclusion.md` | Final paragraph | “Therefore needs” overstated the recovery implication. | Use “may therefore require” and retain the access-decision qualification. | Yes. |
| GMA-05 | Minor | `paper/introduction.md`; `paper/discussion.md`; `paper/conclusion.md` | 1; 5.1; 6 | A method list and two summaries used shortened or variant method names before a clear local mapping. | Use Blind EMA, Guarded EMA, Adaptive Quantile Profile, and Oracle-all consistently. | Yes. |
| GMA-06 | Editorial | `paper/discussion.md` | 5.2–5.8 | Semantic figure placeholders remained after figure order was known. | Replace them with Figs. 1–6. | Yes. |
| GMA-07 | Minor | `paper/results.md`; `paper/manuscript_full.md` | 4.1–4.9 | Frozen Results retains semantic figure/table placeholders. | Preserve the frozen source section; resolve all placeholders during manuscript assembly. | Yes in `manuscript_full.md`; source Results intentionally unchanged. |
| GMA-08 | Minor | Frozen HMOG Figs. 1–3 | Figure labels | Fig. 1 says “poisoning-update budget,” which can be mistaken for incorporated updates; Figs. 2–3 use “Oracle-all EMA” rather than Oracle-all-genuine. | Keep frozen figures unchanged and disambiguate both labels in the captions. | No figure edit; captions corrected. |
| GMA-09 | Minor | Frozen Table 1 artifact | Main-results presentation | The `Decision` column uses laboratory workflow language such as “Reject” and “Stop.” | Before journal typesetting, consider a neutral `Interpretation/status` heading while preserving all values and stopping outcomes. | No; author/journal presentation decision required. |
| GMA-10 | Minor | `references.bib` | `Serbin2026AdaptiveLSTM` | Final Procedia volume, pages, and DOI remain unverified. | Retain the verified conference-manuscript metadata and update only from an authoritative final record in a later task. | No; no metadata invented. |
| GMA-11 | Major | `paper/manuscript_full.md` | Title | The final title has intentionally not been selected. | Select a title after reviewer-style critique and journal choice; current recommendation is Candidate 1. | No; author decision required. |
| GMA-12 | Major | `paper/manuscript_full.md`; `references.bib` | Global format | Journal-specific structure, citation rendering, and reference style are unknown. | Select the target journal, then apply its template and bibliography style without altering frozen scientific content. | No; explicitly out of scope. |
| GMA-13 | Editorial | Existing section-level audit files | Historical audit snapshots | Earlier audits still record the placeholders and pre-integration wording that were present when those audits were written. | Preserve them as dated provenance snapshots and treat this global audit as the current integration status. | No; prior audit artifacts were intentionally not rewritten. |

## 1. Scientific consistency

The manuscript's central chain is consistent across sections: accepted-only Blind EMA exposes a poisoning path; Guarded EMA separates access from update authorization and suppresses the tested poisoning effect; accepted-only policies censor rejected genuine observations during downward score movement; Oracle-all-genuine restores those observations but incurs FAR cost; prespecified recovery/state alternatives do not establish improved recovery under their frozen constraints; McGill provides an independent two-day mechanism-level replication.

The five Introduction contributions map directly to Methods 3.4–3.12, Results 4.1–4.9, Discussion 5.2–5.8, and Conclusion. No sixth contribution was introduced. Methods describes design and protocol rather than novelty. Results primarily reports observations and inferential status; mechanistic and design interpretations remain in Discussion. No substantive scientific correction was made.

## 2. Numerical consistency

All manuscript numbers remain those audited in `paper/methods_results_audit.md` and `paper/conclusion_abstract_audit.md`. No value was recomputed. Abstract values match the frozen outputs: HMOG boundary \(K=8\) ASR 22.92%/53.96%/22.93% for Frozen/Blind/Guarded; Oracle-all claimant-only \(D=2\) late-FRR gain +6.60 percentage points with late-FAR change +6.08 points; and McGill boundary \(K=8\) ASR 12.37%/32.09%/12.48%.

Sign conventions are consistent:

- late-FRR gain and HTER gain are Frozen minus method, so positive values favor the method;
- late-FAR change is method minus Frozen, so positive values mean higher FAR;
- McGill named pairwise effects are method A minus method B;
- rate levels use percent, whereas differences use percentage points.

## 3. Citation consistency

Eight `CITATION NEEDED` occurrences were closed: five in Methods and three in Discussion. The integrated manuscript contains zero unresolved citation placeholders. All 39 cited keys exist in `references.bib`, every bibliography key is used, and no duplicate BibTeX key or DOI was found. Biber data-model validation had already passed after the verified bibliography corrections.

Primary sources support dataset, method, and poisoning claims. Surveys support broad synthesis. Paper 1 is used only for its corpus-bounded research-gap findings. General machine-learning sources remain explicitly analogous in Introduction, Related Work, and Discussion and are not presented as direct biometric evidence. Current-paper findings cite Results, figures, or tables rather than external literature.

## 4. Terminology consistency

Canonical names are used throughout: Frozen, Blind EMA, Guarded EMA, Oracle EMA, Oracle-all-genuine/Oracle-all, TQ-EMA v1, TQ-EMA v2, and Adaptive Quantile Profile. ASR, FAR, FRR, HTER, MUR, and GUR are defined in Methods before sustained use. Authentication threshold, update threshold, and update authorization remain distinct concepts.

The full term *selective-update bias caused by accepted-only feedback censoring* is defined in Introduction and Related Work as an authentication-specific framing. Discussion and Conclusion use the shortened *selective-update bias* only after that definition. The analogous selective-label literature is explicitly distinguished from direct biometric evidence.

## 5. Threat-model consistency

The boundary attacker is consistently score-informed and described as a strong benchmark rather than a binary-feedback-only or universally realistic attacker. Random and boundary selection remain separate. HMOG partitions poison and probe observations by source-session group and does not claim complete source-identity disjointness. McGill uses a source-identity-disjoint poison/probe split. In both protocols, future probes are held out from attack selection and the profile is frozen before post-poison evaluation.

## 6. Drift terminology

HMOG is consistently described as controlled synthetic drift, a claimant-only synthetic shift, or standardized-feature shift. It is not presented as natural longitudinal behavior. McGill is described as a natural Day-1/Day-2 separation or cross-day temporal setting; the text does not claim proven pure behavioral concept drift. The phrase “natural drift” occurs only in a future-work proposal and is not used to characterize HMOG.

## 7. Oracle / stopped-branch consistency

Oracle-all-genuine always uses ground-truth genuine update eligibility and remains diagnostic and non-deployable. Its lower FRR is always paired with its FAR cost; no text says that it proves EMA is a practical solution.

TQ-EMA v1 is correctly described as outer evaluated and as not meeting its prespecified late-FRR recovery criterion. TQ-EMA v2 and the Adaptive Quantile Profile are described only through validation outcomes; outer test data were not loaded and no outer estimates are reported. The manuscript does not generalize these outcomes to all quarantine or robust-distribution methods.

## 8. Cross-dataset consistency

McGill is consistently an independent, two-day, mechanism-level replication with 20 subjects, accelerometer-derived inputs, no gyroscope, separate preprocessing/classifier development, and natural day separation. Guarded \(\lambda=0.25\) was transferred rather than tuned on Day 2. Absolute HMOG and McGill error rates are not directly compared, and McGill is not described as validating HMOG benchmark performance.

## 9. Figure/table mapping

| No. | Manuscript role | Authoritative artifact | Placement |
|---:|---|---|---|
| Fig. 1 | HMOG post-poison ASR vs attack budget, random and boundary | `results/paper3_final_analysis_20261002_v2/figures/figure1_poisoning_asr.pdf` | After Results 4.2 |
| Fig. 2 | HMOG late FAR–FRR trade-off at claimant-only \(D=2\) | `results/paper3_final_analysis_20261002_v2/figures/figure2_security_adaptation_tradeoff.pdf` | After Results 4.3 |
| Fig. 3 | HMOG selective-update mechanism trajectories | `results/paper3_final_analysis_20261002_v2/figures/figure3_selection_bias_mechanism.pdf` | After Results 4.4 |
| Fig. 4 | McGill held-out poisoning replication | `results/paper3_external_mcgill_20261003_v1/figures/external_poisoning_asr.pdf` | Within Results 4.8 after attack findings |
| Fig. 5 | McGill Day-2 late FAR–FRR trade-off | `results/paper3_external_mcgill_20261003_v1/figures/external_temporal_tradeoff.pdf` | After Results 4.8 temporal findings |
| Fig. 6 | McGill profile, threshold, FRR, and update-rate trajectories | `results/paper3_external_mcgill_20261003_v1/figures/external_selection_bias_trajectory.pdf` | After Fig. 5 |
| Table 1 | Main HMOG security/adaptation summary | `results/paper3_final_analysis_20261002_v2/paper3_final_summary_table.md` | After Results 4.7 |
| Table 2 | McGill paired-effect summary | `results/paper3_external_mcgill_20261003_v1/external_replication_summary.md` | After Figs. 5–6 |

Fig. 6 should remain separate. Fig. 5 summarizes the final operating points, whereas Fig. 6 shows the temporal mechanism across 80 units; combining them would require a new figure layout and visual audit. No frozen figure was modified. Every numbered figure/table reference in `paper/manuscript_full.md` resolves to one marker and caption. No additional table was generated.

## 10. Repetition / structure

| Action | Finding | Decision |
|---|---|---|
| KEEP | Poisoning appears in Introduction as motivation, Results as observation, Discussion as interpretation, and Conclusion as synthesis. | Retain; section roles differ. |
| KEEP | Selective-update bias is defined in Introduction/Related Work, evidenced in Results, interpreted in Discussion, and summarized in Conclusion. | Retain the progression; it is the central mechanism. |
| SHORTEN | Discussion 5.1 and Conclusion both summarize the full story. | No automatic cut; consider modest compression only after a journal word limit is known. |
| SHORTEN | McGill limitations appear in Discussion and are scoped again in Conclusion. | Retain the shorter Conclusion qualification; no obvious duplicate block. |
| REMOVE | No paragraph was an obvious stylistic duplicate whose removal preserved all scientific nuance. | None removed. |
| MOVE | Figure/table captions and insertion markers belong in the assembled Results section. | Added there; no audit content was copied into the manuscript. |

The section flow is coherent: Introduction motivates the coupled problem; Related Work positions component precedents; Methods fixes the protocol; Results reports outcomes; Discussion interprets and limits them; Conclusion states the scoped implication and open problem.

## 11. Novelty-risk claims

No unsupported component-level novelty claim remains. The manuscript explicitly recognizes prior adaptive-biometric poisoning and prior use of separate update thresholds. Searches for `first`, `novel`, `prove`, `solves`, `state-of-the-art`, `impossible`, and `natural drift` found only safe contexts: ordinal protocol descriptions, explicit denials of firstness/universality, the statement that McGill is not a state-of-the-art benchmark, and future-work wording. The supported positioning is a joint, protocol-controlled mechanism study rather than invention of poisoning, template update, or the two-threshold concept.

## 12. Remaining placeholders

There are no unresolved citation placeholders. The following assembly markers are intentional:

- `[TITLE TO BE FINALIZED]`;
- six `[INSERT FIGURE N HERE]` markers;
- two `[INSERT TABLE N HERE]` markers;
- a References placeholder generated from `references.bib` after journal selection.

The frozen source file `paper/results.md` retains semantic placeholders such as `Fig. [POISONING]`; these are resolved to Figs. 1–6 and Tables 1–2 in `paper/manuscript_full.md` without editing frozen Results.

Earlier section-level audit files may still contain literal `CITATION NEEDED` text when documenting the pre-integration state. Those records are historical provenance, not unresolved citations in the current manuscript.

## 13. Metadata issues

Paper 2 remains a verified EUSPN 2026 conference manuscript/proceedings entry without confirmed final Procedia volume, page range, or DOI. No metadata was invented. The McGill dataset is cited through its official dataset page, which has no DOI. Other bibliography-specific qualifications remain documented in `paper/introduction_related_work_audit.md`.

## 14. Title ranking

Scores use a five-point scale; for overclaim risk, 5 means lowest risk.

| Rank | Candidate | Scientific accuracy | Clarity | Searchability | Low overclaim risk | Journal suitability | Assessment |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | *Poisoning and Selective-Update Bias in Online Behavioral Biometric Authentication* | 5 | 5 | 5 | 5 | 5 | Best balance; names both central mechanisms and the application domain. |
| 2 | *Poisoning, Feedback Censoring, and Online Adaptation in Behavioral Continuous Authentication* | 5 | 4 | 5 | 5 | 5 | Highly searchable and accurate, but slightly denser. |
| 3 | *Separating Access from Learning: Poisoning and Feedback Censoring in Continuous Behavioral Authentication* | 5 | 5 | 4 | 5 | 5 | Strong design message; somewhat less direct about online profile adaptation. |
| 4 | *Online Behavioral Profile Adaptation Under Poisoning and Accepted-Only Feedback* | 4 | 4 | 4 | 5 | 4 | Accurate but omits “continuous authentication” from the title. |
| 5 | *Access as a Learning Gate: Poisoning and Selective Feedback in Adaptive Behavioral Authentication* | 4 | 4 | 3 | 4 | 4 | Memorable, but “selective feedback” is less specific than the manuscript's defined term. |

No title was applied automatically.

## 15. Submission-readiness blockers

No Critical scientific blocker was found. Two Major author/workflow decisions remain: select the final title and select a target journal so its structure, citation style, word limit, and artwork requirements can be applied. Before typesetting, the author should also decide whether Table 1's `Decision` column should be relabeled to a more neutral journal-facing heading and obtain final Paper 2 proceedings metadata if it becomes available.

Readiness assessment:

- **Final reviewer-style critique:** ready.
- **Journal selection:** ready; selection itself was not performed.
- **Journal-specific formatting:** scientific content is ready, but formatting should begin only after the journal and title are selected.
