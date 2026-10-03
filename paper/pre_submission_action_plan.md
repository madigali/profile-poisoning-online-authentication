# Pre-Submission Action Plan

This plan converts the independent reviewer critique into a submission sequence. It assumes that frozen experimental outputs remain unchanged unless a task is explicitly marked as requiring an experimental change.

## Priority 1 — Lock the paper's actual contribution

- **Task:** Rewrite the contribution hierarchy so that the primary contribution is the coupled mechanism study: accepted-only feedback enables malicious inclusion and genuine-evidence censoring. Present Guarded EMA as a prior-art-consistent control, not as the invention of a two-threshold defense. Remove TQ-v2/Quantile from the headline contribution list.
- **Why:** The most likely novelty rejection is “poisoning and separate update thresholds are already known.” The paper survives that objection only through its joint mechanistic evidence and evaluation design.
- **File/section:** `paper/introduction.md` (research gap and contributions), `paper/related_work.md` (Sections 2.2–2.5), `paper/discussion.md` (Sections 5.1, 5.3–5.7), `paper/conclusion.md`.
- **Experimental change required?** No.
- **Expected impact on acceptance:** Very high. Converts the paper from a weak algorithm-novelty claim into a defensible mechanism/evaluation contribution.

## Priority 2 — Make the operating-point limitation impossible to miss

- **Task:** State that the principal thresholds are EER-like and that baseline HMOG/McGill impostor acceptance is already high. Separate causal attack amplification from absolute system security and deployment suitability. Avoid any implication that returning Guarded ASR to Frozen makes the system secure.
- **Why:** A Q1 security reviewer may otherwise dismiss the attack as a consequence of an already insecure threshold.
- **File/section:** `paper/abstract.md`, `paper/introduction.md`, `paper/methods.md` Section 3.3, `paper/results.md` Sections 4.1–4.2 and 4.8, `paper/discussion.md` Sections 5.2–5.3 and 5.10.
- **Experimental change required?** No for the required framing. An optional operating-point sensitivity analysis would be additional experimental evidence.
- **Expected impact on acceptance:** Very high. Prevents a fair limitation from becoming an apparent oversight or overclaim.

## Priority 3 — Formalize the boundary-attacker model and attack cost

- **Task:** Add a compact capability table covering score access, candidate-pool access, observable output, candidate discovery, presented poison budget, total query cost, timing, and excluded capabilities. State explicitly that (K) counts selected poisoning attempts and excludes reconnaissance. Classify the implemented boundary attack as score-informed gray/white-box benchmarking, not binary-feedback black box.
- **Why:** The headline effect depends on access to score ordering. Without a precise interface, practical threat relevance is ambiguous.
- **File/section:** `paper/methods.md` Section 3.4; short disclosures in `paper/abstract.md`, `paper/introduction.md`, and `paper/discussion.md` Sections 5.2 and 5.10.
- **Experimental change required?** No for clarification. Yes only if adding a binary-feedback/query-limited attack.
- **Expected impact on acceptance:** Very high. Makes the security claim auditable and prevents the “eight-query black-box attack” misreading.

## Priority 4 — Declare one evidence hierarchy

- **Task:** Add a concise protocol chronology/evidence-status table that labels: inherited Paper 2 baseline; exploratory HMOG attack; exploratory HMOG lambda sweep; diagnostic Oracle-all; outer-evaluated TQ-v1; validation-stopped TQ-v2 and Quantile; transferred McGill replication. State when parameters and endpoints were frozen and which results are confirmatory versus exploratory.
- **Why:** Reused HMOG outer caches and sequential method development weaken confirmatory claims even though individual branches followed documented gates.
- **File/section:** `paper/methods.md` Section 3.1 or 3.13; corresponding qualification in `paper/discussion.md` Section 5.10.
- **Experimental change required?** No.
- **Expected impact on acceptance:** High. Converts a potential hidden flexibility concern into transparent evidential accounting.

## Priority 5 — Strengthen inference for the core HMOG poisoning contrast

- **Task:** Using retained subject/path outputs, report a paired subject-level interval for the primary HMOG boundary (K=8) Blind-minus-Frozen contrast and, if the data structure permits, a victim-by-impostor-source robustness interval. Declare one primary security comparison and one primary adaptation comparison. Treat budgets, lambdas, other drift levels, and secondary methods as exploratory or define a multiplicity rule.
- **Why:** The central security claim currently relies on means and descriptive intervals across five overlapping folds, while secondary analyses receive stronger bootstrap treatment.
- **File/section:** `paper/methods.md` Section 3.11; `paper/results.md` Sections 4.1–4.2; Fig. 1 caption; Table 1 or a dedicated effect table.
- **Experimental change required?** No new experiment; this is analysis of existing frozen outputs. Do not change scores, partitions, attacks, or method states.
- **Expected impact on acceptance:** Very high, especially with statistical reviewers.

## Priority 6 — Publish denominators and eligibility clearly

- **Task:** Add a compact cohort/exclusion table for HMOG and McGill: subjects, folds, victim-repeat paths, eligible (K=8) paths, exclusions by reason, and effective sample size for each headline contrast. Explain that boundary estimates are conditional on sufficient initially accepted candidates.
- **Why:** Eligibility is part of attack feasibility and can select less secure victims. McGill reports 18 victims and 544/2,000 excluded paths, but the design needs equally visible HMOG accounting.
- **File/section:** `paper/methods.md` Sections 3.4 and 3.12; `paper/results.md` Sections 4.1–4.2 and 4.8; supplementary exclusion table.
- **Experimental change required?** No; summarize retained exclusion files.
- **Expected impact on acceptance:** High. Improves validity, transparency, and interpretation of attack feasibility.

## Priority 7 — Narrow drift and Oracle claims

- **Task:** Describe HMOG (D=0,1,2) only as controlled synthetic feature-space sensitivity levels. Explain that McGill is cross-day shift, not isolated biological/behavioral drift. Discuss Oracle-all behavior at (D=0) and describe it as an information-availability intervention rather than a formal upper bound.
- **Why:** Oracle FRR reduction with FAR increase can arise through threshold relaxation, and the synthetic transformation lacks empirical mapping to natural drift magnitude.
- **File/section:** `paper/methods.md` Sections 3.6–3.7; `paper/results.md` Section 4.4; `paper/discussion.md` Sections 5.4–5.8 and 5.10.
- **Experimental change required?** No.
- **Expected impact on acceptance:** High. Preserves the mechanistic inference while removing overinterpretation.

## Priority 8 — Reduce the failed branches to their scientific role

- **Task:** Keep a short main-text TQ-v1 result because it tests a plausible recovery route. Reduce TQ-v2 and Quantile to one concise main paragraph/table row saying that validation gates failed and outer data were not loaded. Move controller details, grids, fold diagnostics, and stopped-branch outputs to Supplementary Material.
- **Why:** Excess detail makes the paper resemble a laboratory diary and dilutes the stronger poisoning/censoring story.
- **File/section:** `paper/methods.md` Sections 3.8–3.10; `paper/results.md` Sections 4.5–4.7; `paper/discussion.md` Section 5.6; Table 1; new supplement.
- **Experimental change required?** No.
- **Expected impact on acceptance:** High. Improves focus and makes the negative results look disciplined rather than improvised.

## Priority 9 — Compress the manuscript to journal scale

- **Task:** Reduce the main text from approximately 11,500 to 7,500–8,500 words excluding references. Target cuts: Introduction 300–500; Related Work 500–700; Methods 900–1,200; Results 300–500; Discussion 700–1,000; Conclusion 300–500 words.
- **Why:** The current length exceeds the evidential breadth and repeats the central story across Introduction, Results, Discussion, and Conclusion.
- **File/section:** All main manuscript source files, with the largest cuts in `paper/methods.md`, `paper/discussion.md`, and `paper/conclusion.md`.
- **Experimental change required?** No.
- **Expected impact on acceptance:** High. Produces a clearer Q1 narrative and reduces reviewer fatigue.

## Priority 10 — Rationalize figures and tables

- **Task:** Keep HMOG Figs. 1–3 central. Keep McGill poisoning in the main paper, preferably combined with HMOG poisoning. Combine the McGill trade-off with the HMOG trade-off or move it to Supplementary Material. Move the full McGill four-panel trajectory to Supplementary Material or retain only the most diagnostic panels. Replace Fig. 1's overlapping-fold “95%” bands with a less misleading display when the statistical revision is performed. Rename (K) as presented poisoning attempts. Relabel Table 1 `Decision` as `Interpretation / protocol status`.
- **Why:** The current six figures are not excessive by count, but two pairs repeat the same story and some visual elements imply stronger uncertainty support than the design provides.
- **File/section:** Results figures/captions; Table 1; journal artwork package.
- **Experimental change required?** No. Figure regeneration from frozen summaries and approved existing-data uncertainty analysis only.
- **Expected impact on acceptance:** Medium–high. Clarifies the main evidence and prevents statistical/visual misreading.

## Priority 11 — Complete methodological reproducibility details

- **Task:** Specify the HMOG approximate-EER procedure and tie handling; model/training seeds; rationale for discarding the first 500 samples and retaining the next 20 windows; chronological validity of session order; and the condition ensuring the update threshold remains at least the authentication threshold. State explicitly that the protocol evaluates enrolled identities across unseen sessions, not unseen subjects.
- **Why:** The broad pipeline is reproducible, but these details are needed for an independent implementation.
- **File/section:** `paper/methods.md` Sections 3.2–3.3 and supplementary protocol.
- **Experimental change required?** No.
- **Expected impact on acceptance:** Medium. Closes predictable reproducibility questions.

## Priority 12 — Complete journal-facing assembly

- **Task:** Apply the selected title, insert the actual six/condensed figures and two tables, generate references from `references.bib`, verify Paper 2's final bibliographic status, add data/code availability and ethics statements as required, and remove all assembly markers.
- **Why:** The current full manuscript still contains title, figure/table, and reference placeholders.
- **File/section:** `paper/manuscript_full.md`, figure/table package, `references.bib`, journal template.
- **Experimental change required?** No.
- **Expected impact on acceptance:** Mandatory for submission; primarily editorial rather than scientific.

## Priority 13 — Select the journal by contribution type

- **Task:** Shortlist Q1 venues that accept security measurement, biometric-system evaluation, reproducibility, and negative mechanistic evidence. Avoid venues whose review norm requires a novel deployable algorithm or state-of-the-art recognition accuracy as the primary contribution.
- **Why:** The same manuscript can be viewed as a strong mechanism study or a weak defense paper depending on venue fit.
- **File/section:** Submission strategy; no manuscript change until author guidelines are selected.
- **Experimental change required?** No.
- **Expected impact on acceptance:** High. Aligns reviewer expectations with the paper's real strength.

## Priority 14 — Optional experiment with the highest return

- **Task:** If one additional experiment is authorized, evaluate the frozen attack/defense mechanism at prespecified deployment-oriented FAR targets using existing score caches. Report candidate availability, Blind amplification, Guarded suppression, and uncertainty at each operating point.
- **Why:** This directly tests whether the headline result persists outside the very permissive EER-like threshold.
- **File/section:** New frozen protocol and result package; then Methods, Results, Discussion, and Fig. 1/Table 1.
- **Experimental change required?** Yes.
- **Expected impact on acceptance:** Potentially very high. This is the single experiment most likely to neutralize the strongest security objection.

## Priority 15 — Optional attacker-realism experiment

- **Task:** If a second experiment is authorized, implement a binary-feedback/query-limited or surrogate-ranking attacker and charge candidate discovery to the total query budget.
- **Why:** This tests whether the score-informed boundary effect is reachable through a plausible external interface.
- **File/section:** New threat-model protocol and result package; then Methods, Results, Discussion, and attack figure/table.
- **Experimental change required?** Yes.
- **Expected impact on acceptance:** High for cybersecurity venues; lower priority than operating-point sensitivity.

## Submission gate

Proceed to journal selection after Priorities 1–8 are resolved in a revision plan and the author decides whether Priority 5's existing-data statistical analysis is feasible. Proceed to journal formatting only after the target venue and final title are selected. Do not add a third dataset or another adaptation architecture before first submission unless a specific target journal requires it.
