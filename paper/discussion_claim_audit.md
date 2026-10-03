# Discussion Interpretive-Claim Audit

## Classification

- **Direct observation:** stated directly by the frozen protocol or Results.
- **Supported interpretation:** an inference supported by a controlled comparison, trajectory, or cross-dataset pattern, but not claimed as a universal causal law.
- **Speculation/proposal:** a bounded future-work or design proposition that was not tested in this paper.

Current-paper results do not require external citations. A citation is marked as needed when the text refers to prior work, introduces terminology that should be situated in a wider literature, or links the future-work agenda to the verified systematic review.

## Audited claims

| Discussion subsection | Strong claim | Supporting result or scope condition | Authoritative source | Classification | Citation needed? |
|---|---|---|---|---|---|
| 5.1 | The tested schemes exhibit a coupled security–adaptation trade-off. | Blind is poisonable; Guarded suppresses poisoning but does not improve late FRR; Oracle lowers FRR with higher FAR. | Results 4.1–4.5; Fig. [POISONING], Fig. [TRADEOFF] | Supported interpretation limited to tested protocols | No external citation |
| 5.1 | McGill reproduces the directions of the principal mechanisms. | Boundary Blind−Frozen and Guarded−Blind effects; Guarded temporal FRR; Oracle FRR/FAR direction. | Results 4.8–4.9; Table [MCGILL] | Direct cross-dataset observation | No |
| 5.2 | Accepted malicious observations can influence the future decision state under Blind EMA. | Blind alone updates on accepted poisons; Frozen/Oracle do not; future ASR is measured after state freeze. | Methods 3.3–3.4; Results 4.1 | Direct protocol fact plus supported interpretation | No |
| 5.2 | The ASR increase is not simple reuse of the poison observations. | Poison and probe samples are separated by source-session group before candidate selection. | Methods 3.4; Results 4.1 | Direct protocol property | No |
| 5.2 | Online state change is the relevant experimental difference between Blind and Frozen/Oracle in the malicious-only phase. | Paired streams and probes; Oracle blocks malicious updates and equals Frozen; Blind changes state. | Methods 3.3–3.4; methods_results_audit non-numerical checks | Supported interpretation from controlled comparison | No |
| 5.2 | Boundary is a strong score-informed attacker and is stronger than random in the tested runs. | Boundary uses score margin; its budget trend is larger than random. | Methods 3.4; Results 4.1 and 4.8 | Direct observation with scoped interpretation | No |
| 5.2 | Paper 2 identified a pathway but did not run the dedicated poisoning experiment. | Verified prior-paper audit. | paper/paper1_paper2_fact_check.md, Adaptive Agent and confirmed wording | Direct prior-work statement | **Yes: [CITATION NEEDED: Paper 2]** |
| 5.3 | Authentication and update authorization can be separated without changing the access threshold. | Guarded uses the ordinary authentication threshold plus a distinct learning gate. | Methods 3.3 and 3.5 | Direct method property | No |
| 5.3 | The separate gate reduces contamination under both frozen protocols. | Guarded MUR/ASR effects in HMOG and McGill. | Results 4.2 and 4.8 | Direct observation | No |
| 5.3 | MUR alone does not determine contamination severity. | Guarded MUR differs substantially between datasets while Guarded ASR remains near each Frozen value. | Results 4.2 and 4.8; paper/notes.md D022 | Supported cross-dataset interpretation | No |
| 5.3 | The carried-forward lambda is not a universal optimum. | Lambda sweep is explicitly exploratory; McGill transfers rather than tunes it. | Methods 3.3, 3.5, 3.12; Results 4.2 | Direct scope qualification | No |
| 5.4 | Accepted-only feedback can produce a selected update stream enriched for higher genuine scores during downward shift. | Rejected genuine candidates cannot update; Guarded trajectory rises while Oracle-all falls. | Methods 3.6–3.7; Results 4.3–4.4; Fig. [TRAJECTORY] | Supported mechanistic interpretation | **Yes for terminology/context: [CITATION NEEDED: selective-label and feedback-censoring literature]** |
| 5.4 | The update stream is not equivalent to the full genuine distribution in the tested protocol. | Update eligibility depends on current authentication; Oracle-all receives rejected genuine candidates. | Methods 3.3 and 3.7; Results 4.4 | Supported interpretation | No |
| 5.4 | The observed trajectory is not a universal censoring theorem. | Only short score-level streams and two datasets were evaluated. | Methods 3.1, 3.6, 3.12; Limitations 5.10 | Scope qualification | No |
| 5.5 | EMA moments can respond to lower genuine scores when rejected genuine evidence is restored. | Oracle-all moves the profile downward and lowers late FRR in HMOG and McGill. | Results 4.4 and 4.8 | Supported interpretation | No |
| 5.5 | Oracle-all is diagnostic, not deployable. | It requires ground-truth update labels unavailable to ordinary operation. | Methods 3.3 and 3.7 | Direct method limitation | No |
| 5.5 | Oracle-all does not establish a usable overall improvement. | FAR rises substantially and HTER does not show a clear gain. | Results 4.4 and 4.8 | Direct observation with supported interpretation | No |
| 5.6 | TQ-v1 recovery evidence was much rarer than trusted-update evidence. | Frozen event audit records far fewer recovery than trusted updates. | Results 4.5; paper/notes.md D013 | Direct observation | No |
| 5.6 | Sparse recovery is consistent with, but does not conclusively cause, the absence of FRR gain. | TQ-v1 does not meet recovery criterion; event imbalance and positive threshold movement co-occur. | Results 4.5; Fig. [TRADEOFF] | Supported interpretation, deliberately softened | No |
| 5.6 | TQ-v2 has no outer estimate. | Validation gate stops in fold 4 before outer loading. | Methods 3.9; Results 4.6; validation_failure.json | Direct protocol outcome | No |
| 5.6 | Accepted-only censoring is not the only difficulty for the frozen quantile representation. | Oracle-all Quantile improves over Accepted-only Quantile but remains worse than Frozen on validation recovery. | Results 4.7 | Supported interpretation limited to frozen representation/grid | No |
| 5.6 | Negative branches do not reject quarantine or robust tracking as general families. | Only prespecified implementations and grids were tested; stopped branches have no outer estimates. | Methods 3.8–3.10; Results 4.5–4.7 | Scope qualification | No |
| 5.7 | No tested score-level method provides a free adaptation gain. | Trade-off plot: lower FRR and FAR do not improve together across tested methods. | Results 4.3–4.5; Fig. [TRADEOFF] | Supported interpretation limited to tested methods | No |
| 5.7 | The trade-off is not an impossibility theorem. | Feature/model adaptation and trusted recovery evidence were not tested. | Methods 3.1; Limitations 5.10 | Scope qualification | No |
| 5.7 | HTER can conceal security-relevant opposing changes in FAR and FRR. | Oracle FRR decreases while FAR increases and HTER changes little. | Results 4.4 and 4.8 | Supported interpretation from metric components | No |
| 5.8 | McGill provides mechanism-level, not benchmark-level, replication. | Dataset, modality, classifier, cohort, and temporal construction differ from HMOG. | Methods 3.12; Results 4.8 | Direct scope statement | No |
| 5.8 | Natural two-day separation removes dependence on the HMOG synthetic-drift construction for the external temporal direction. | McGill Day 1/Day 2 chronology; no synthetic drift in external protocol. | Methods 3.12; experiments/external_replication_mcgill.md | Direct protocol fact | No |
| 5.8 | Severe McGill day shift limits absolute performance interpretation. | Frozen Day-2 FRR is high. | Results 4.8 | Supported interpretation | No |
| 5.9 | Learning permission should be treated separately from access permission. | Guarded reduces attack contamination while retaining the same access threshold. | Methods 3.3; Results 4.2 and 4.8 | Design implication supported by results | No |
| 5.9 | Update-stream composition and trajectories should be audited, not only aggregate decisions. | GUR/MUR and trajectory differences explain information availability not visible in HTER alone. | Results 4.2–4.5 and 4.8 | Design implication supported by results | No |
| 5.9 | Recovery evidence should be partly independent of the original access decision. | Accepted-only censoring persists; Oracle restores evidence but is non-deployable. | Results 4.3–4.5 and 4.8 | Supported design implication | No |
| 5.9 | Step-up, temporal, context, and multimodal signals are candidate recovery sources. | These signals were not tested in this paper. | Future Work 5.11 | Speculation/proposal | No citation required if retained as proposal; Related Work should contextualize |
| 5.9 | Feature/model-level adaptation is justified for future evaluation, not established as superior. | Frozen score-level branches did not meet recovery criteria; no feature/model updater was tested. | Results 4.5–4.7; Limitations 5.10 | Speculation/proposal with explicit boundary | No citation required as proposal |
| 5.10 | HMOG drift is synthetic and not natural long-term behavior. | Standardized feature-shift construction. | Methods 3.6 | Direct scope limitation | No |
| 5.10 | Later HMOG branches are exploratory rather than independent confirmation. | Same overall outer caches were inspected sequentially; D014/D016 state inferential limitation. | paper/notes.md D014, D016, D018; Methods 3.1 | Direct provenance limitation | No |
| 5.10 | TQ-v1 has no combined drift-plus-poisoning evidence. | Final summary explicitly states that the combined experiment was not run. | results/paper3_final_analysis_20261002_v2/paper3_final_summary_table.md; paper/notes.md D019 | Direct scope limitation | No |
| 5.10 | Boundary results do not generalize to every attacker interface. | Boundary uses score-informed ranking; binary-only feasibility was not implemented. | Methods 3.4; experiments protocol | Direct threat-model limitation | No |
| 5.10 | Dataset and systems generalization are limited. | One main HMOG dataset; small accelerometer-only McGill cohort; no production latency/energy study. | Methods 3.2, 3.12; paper/notes.md D021–D022 | Direct scope limitation | No |
| 5.10 | Validation-stopped branches cannot support outer-performance claims. | outer_test_loaded=false for TQ-v2 and Quantile. | Results 4.6–4.7; manifests | Direct inferential limitation | No |
| 5.11 | Larger natural multi-day studies with joint security/utility evaluation are the next empirical priority. | Follows from synthetic HMOG drift, small McGill cohort, and separate recovery/attack blocks. | Limitations 5.10; paper/paper1_paper2_fact_check.md, Paper 1 gaps | Proposal linked to verified review | **Yes: [CITATION NEEDED: Paper 1]** |
| 5.11 | Trusted step-up and multimodal evidence may reduce dependence on accepted-only feedback. | Not evaluated; logically follows from Oracle information advantage and Guarded censoring. | Results 4.4 and 4.8 | Speculation/proposal | No citation required as proposal; literature support desirable |
| 5.11 | Feature/model adaptation and change-point detection may occupy a different trade-off region. | Not evaluated in Paper 3. | Limitations 5.10 | Speculation/proposal | No citation required as proposal; literature support desirable |
| 5.11 | Field studies should measure recovery time, friction, rollback, and on-device cost. | These outcomes were outside the present protocol. | Limitations 5.10 | Speculation/proposal | No |

## Claims deliberately softened

The following stronger formulations were not used:

- “Guarded EMA solves poisoning” was narrowed to “reduced contamination and post-poison ASR under the two frozen protocols.”
- “Accepted-only learning causes universal upward drift” was narrowed to a selective-update interpretation supported by the tested trajectories.
- “Oracle proves EMA adaptation works” was narrowed to evidence that EMA can respond when all genuine candidates are available, with a substantial FAR cost.
- “TQ and quantile methods failed” was replaced with protocol-specific statements that the recovery criterion or validation gate was not satisfied.
- “McGill validates HMOG performance” was replaced with directionally consistent mechanism-level replication.
- “Score-level adaptation is impossible” was replaced with the observation that no tested score-level scheme provided a free adaptation gain.

## Citation gaps

Three placeholders remain in Discussion:

1. Paper 2, for the verified statement that it identified the label-blind poisoning pathway but did not execute the dedicated attack.
2. Selective-label or feedback-censoring literature, to contextualize the term “selective-update bias caused by accepted-only feedback censoring.”
3. Paper 1, for the verified longitudinal and adversarial-evaluation research gaps used to motivate future work.

No external citation is attached to the current paper's own results.
