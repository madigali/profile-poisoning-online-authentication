# Reviewer Report

## Summary

This manuscript studies two consequences of accepted-only online adaptation in behavioral biometric authentication. First, an accepted impostor can alter a score-level EMA profile and increase subsequent acceptance of held-out impostor probes. Second, the same acceptance condition censors rejected genuine observations from the update stream, which can prevent the profile from following a downward change in genuine scores. The paper evaluates Frozen, Blind EMA, Guarded EMA, Oracle-all-genuine, and several recovery/state alternatives on HMOG, and then examines the principal directions on a two-day McGill Gait protocol.

The strongest evidence is mechanistic rather than algorithmic. The matched Guarded-versus-Oracle comparisons, state trajectories, update-rate accounting, held-out poison/probe design, and independent McGill direction are collectively useful. The work is unusually transparent about negative branches and about the fact that separate authentication and update thresholds and adaptive-biometric poisoning are prior art.

However, the present manuscript is not ready for Q1 submission. The main security effect is demonstrated primarily under a score-informed attacker at an EER-like operating point with already high baseline impostor acceptance. Candidate-search/query cost is omitted. The main HMOG poisoning figure uses descriptive intervals across five overlapping folds rather than a subject-level or cross-classified uncertainty analysis. The main Guarded parameter was carried forward from an exploratory HMOG outer-data sweep. The drift evidence is primarily synthetic, while the external cohort is small, has severe Day-2 degradation, and uses a relatively weak classifier. Finally, the manuscript devotes too much main-text space to stopped TQ/Quantile branches, making a focused mechanism paper read partly like a research diary.

My recommendation for the current version is **Major Revision**. The paper has a publishable core, but acceptance depends on presenting it as a carefully bounded mechanism study rather than as a new defense algorithm or broad external validation of deployable continuous authentication.

## Overall Assessment

### Strengths

- The poison and held-out probe observations are separated before attack selection, and the profile is frozen before future-probe evaluation.
- The study separates access authorization from update authorization and reports both malicious and genuine update availability.
- The Oracle-all intervention changes update eligibility while retaining the ordinary access decisions, which is a useful diagnostic design.
- Negative branches are governed by explicit validation gates, and TQ-EMA v2 and Quantile outer test data were not opened after validation failure.
- The manuscript acknowledges the relevant prior art instead of making implausible “first” claims.
- The McGill protocol transfers the Guarded rule without Day-2 tuning and changes dataset, classifier, modality set, and temporal setting.
- Reproducibility practices are unusually strong: frozen score caches, manifests, hashes, fixed seeds, protocol tests, and retained exclusions are described.

### Central weaknesses

- The practical security claim is difficult to interpret at a baseline HMOG ASR/FAR of roughly 23% and a McGill boundary baseline of roughly 12%. The attack amplification is real within the protocol, but these are not credible production operating points.
- The boundary attacker is score-informed and selects candidates after effectively inspecting a pool. The reported budget counts selected poisoning presentations, not the reconnaissance/query effort needed to find them.
- Guarded EMA and the two-threshold idea are incremental; the paper does not deliver a successful deployable adaptation method.
- Much of the HMOG development is exploratory because the same outer caches informed successive branches and the reported Guarded parameter came from the HMOG sweep.
- The core HMOG poisoning result does not receive the same subject-level inferential treatment as the drift and McGill effects.
- Synthetic feature-space drift cannot by itself establish natural behavioral-drift recovery.
- McGill is a useful directional replication but not strong population-level external validation.

### Bottom line

The manuscript's defensible contribution is an integrated, protocol-controlled demonstration that accepted-only feedback creates two coupled effects: an inclusion channel for accepted impostors and an exclusion channel for rejected genuine observations. That contribution is meaningful. It is not equivalent to inventing poisoning, inventing two thresholds, providing a deployable defense, or proving a general security–adaptation impossibility.

## Major Comments

### 1. The security result is tied to a permissive EER-like operating point

**Sections:** 3.3, 3.4, 4.1–4.2, 4.8, 5.2–5.3, 5.10.

The HMOG initial threshold is calibrated near equal error, and the held-out (K=0) impostor acceptance is approximately 22.92%. The corresponding clean-drift Frozen FAR is 22.86%. McGill is better but still has a 12.37% boundary baseline. These values make the system unsuitable as a practical security control before poisoning. They also create a large pool of initially accepted impostor candidates, which is a prerequisite for the boundary attack.

This does not invalidate the within-protocol causal comparison: Blind changes while Frozen/Oracle do not. It does materially limit practical relevance. A security reviewer can reasonably argue that the paper demonstrates amplification in an already insecure operating regime and has not shown that the mechanism remains consequential at deployment-oriented FAR targets.

The manuscript must foreground this issue rather than leaving it implicit in the reported numbers. It should distinguish (i) causal vulnerability of the update rule, (ii) absolute security of the classifier/threshold, and (iii) deployability. If no new analysis is performed, claims should be explicitly limited to the evaluated EER-like operating point. An operating-point sensitivity analysis using the existing scores would be the single most valuable optional experiment.

### 2. The boundary attacker needs a clearer capability and cost model

**Sections:** 3.4, 4.1, 4.8, 5.2, 5.10.

The strongest effects rely on an attacker who knows or obtains claimant scores, identifies observations accepted at the initial threshold, and ranks them by margin. The paper correctly calls this a strong score-informed benchmark, but it does not specify how the attacker obtains the scores, how many candidate observations must be screened, whether the system exposes a stable confidence value, or whether rejected reconnaissance attempts consume security-relevant queries. (K) counts selected poison presentations, not total attack effort.

The random attack is much weaker, and the McGill random (K=8) interval includes zero. Consequently, the headline security result depends on the strong attacker model. The threat model should state whether this is white-box, gray-box, API-score leakage, local-device compromise short of OS compromise, or a surrogate-ranking attacker. It should also explicitly state that a binary-feedback-only attacker has not been demonstrated. Without that clarification, readers may incorrectly interpret the boundary attack as a realistic black-box attack with only eight queries.

The required revision is mainly conceptual: provide a capability table, separate candidate discovery from poisoning budget, and describe the result as a score-access upper-bound/strong benchmark. A query-limited binary-feedback experiment would materially strengthen the paper but is not mandatory if the claim is narrowed.

### 3. Novelty is mechanistic and integrative, not algorithmic

**Sections:** 1, 2.2–2.5, 5.3–5.7, 6.

Adaptive biometric poisoning is established by Biggio, Lovisotto, Xue, and related work. Separate acceptance and update thresholds are established by Giot and the wider template-update literature. Guarded EMA is therefore an incremental instantiation of known confidence-gated updating. Oracle controls, quarantine heuristics, and quantile summaries are also not intrinsically novel methods.

The paper remains potentially publishable because it jointly evaluates held-out poisoning, update-stream composition, clean temporal behavior, feedback availability, and external direction. The strongest novelty is the empirical characterization of accepted-only feedback as both a security inclusion mechanism and a genuine-evidence censoring mechanism in mobile behavioral authentication. The manuscript should make this hierarchy unmistakable. Contribution 4, which elevates stopped recovery alternatives, currently weakens rather than strengthens the novelty statement.

The revision should reduce any appearance that Guarded EMA or the second threshold is the principal innovation. State that the contribution is a mechanism study and evaluation framework, then explain precisely what prior poisoning and two-threshold studies did not jointly measure. A Q1 reviewer who knows Biggio, Lovisotto, Xue, and Giot must be able to identify the residual contribution in one paragraph.

### 4. The confirmatory/exploratory hierarchy is not sufficiently sharp

**Sections:** 3.1, 3.5–3.10, 3.13, 4.2–4.7, 5.10.

The manuscript acknowledges sequential development on the same HMOG outer score caches. More importantly, (lambda=0.25) is a carry-forward from an exploratory HMOG poisoning sweep, so the HMOG Guarded result is not an untouched confirmatory evaluation of a prespecified parameter. TQ-v1 was outer evaluated; TQ-v2 and Quantile stopped at validation; later branches were informed by earlier observations. These distinctions are honest but dispersed.

The paper needs one explicit evidence hierarchy, preferably near the end of Study Design: which hypotheses, endpoints, parameters, and contrasts were prespecified before which data were inspected; which HMOG results are exploratory; which McGill results constitute transferred confirmation; and which are diagnostic only. The independent McGill transfer partly mitigates the HMOG selection issue, but the small cohort does not convert the entire development sequence into confirmatory evidence.

This can be fixed without a new experiment. A compact protocol chronology or evidence-status table would be more useful than repeated references to Git freezing throughout the prose.

### 5. Statistical support for the core HMOG poisoning claim is weaker than for secondary analyses

**Sections:** 3.11, 4.1–4.2, Fig. 1.

The manuscript correctly states that the five HMOG folds overlap in their fitting partitions and that 100 repeats are Monte Carlo replicates, not independent observations. Nevertheless, Fig. 1 displays 95% (t)-intervals across only five overlapping folds. Even with the caption's warning, these bands look like inferential confidence intervals and can mislead readers.

The central +31.04-point HMOG Blind-minus-Frozen effect is reported without a paired subject-level interval comparable to those reported for drift and McGill. In addition, victim-level resampling alone may understate uncertainty when the same impostor source identities contribute probes across multiple victims. The manuscript uses a victim-by-impostor-source bootstrap only for TQ-v1 FAR, not for the main poisoning endpoint. Exclusions of paths without eight accepted boundary candidates also create a conditional eligible cohort whose size and composition should be prominent.

The paper does not require null-hypothesis tests merely for convention: paired effect estimates and appropriately constructed confidence intervals are sufficient. What it does require is a declared primary contrast, uncertainty at the correct independent unit, transparent denominators, and a strategy for shared impostor-source dependence. This can be addressed by reanalysis of existing retained outputs rather than a new experiment. Secondary budgets, lambdas, drift levels, and method contrasts should be labeled exploratory or handled with a multiplicity plan.

### 6. Synthetic drift and Oracle-all do not by themselves prove natural adaptation capability

**Sections:** 3.6–3.7, 4.3–4.4, 5.4–5.7.

The claimant-only HMOG shift adds the same fold-specific direction in standardized feature space and holds impostor scores at (D=0). This is useful for isolating score-profile behavior, but (D=1,2) have no demonstrated relation to observed real behavioral changes, sensor placement changes, or day-to-day within-user variation. The transformation is not subject-specific and the LSTM's nonlinear response to it is not intrinsically interpretable.

Oracle-all is a strong intervention for identifying the effect of update eligibility because the state equation is held fixed while rejected genuine samples are restored. However, it is not a formal upper bound on useful adaptation, and its FRR improvement partly reflects threshold relaxation: even at (D=0), Oracle-all improves FRR and increases FAR. The paper should discuss this (D=0) behavior directly. The comparison supports feedback censoring as a contributor to the observed trajectories; it does not establish that censoring is the only limiting mechanism or that all genuine-score drift should be followed.

McGill provides natural day separation but not a clean measure of behavioral drift: day, acquisition, sensor, activity, and model-transfer effects are confounded. The proper conclusion is that the same feedback mechanism appears under a real cross-day shift, not that natural behavioral drift has been validated.

### 7. McGill is useful corroboration but remains weak external validation

**Sections:** 3.12, 4.8–4.9, 5.8, 5.10.

The external protocol has real strengths: Day 2 is held out, the Guarded parameter is transferred without Day-2 tuning, poison and probe identities are disjoint, and the principal boundary effect has a paired interval excluding zero. It also changes classifier and modality conditions, which is valuable for mechanism-level replication.

However, 20 subjects (18 for the boundary (K=8) contrast), 544 of 2,000 paths without eight eligible boundary candidates, 58.12% Day-1 validation top-1 accuracy, 78% Frozen Day-2 late FRR, accelerometer-only data, and an extreme Oracle FAR of 75.05% limit the strength of external claims. The replication may be dominated by severe cross-day model failure. Boundary feasibility also selects the victims/repeats for whom enough accepted candidates exist.

Thus McGill is sufficient as **directional mechanistic corroboration**, but it is insufficient as broad external validation of effect size, deployment performance, or population generalizability. This is a Major concern only if the paper uses “external validation” without qualification; it becomes Moderate if “small external mechanism-level replication” is used consistently and the eligible cohort/exclusion mechanism is emphasized.

### 8. The main paper is overextended by failed method branches

**Sections:** 3.8–3.10, 4.5–4.7, 5.6; Table 1.

TQ-v1 is scientifically useful because it shows that a plausible rejected-sample recovery path can reduce FAR without meeting the prespecified FRR recovery goal. TQ-v2 and Quantile demonstrate disciplined stopping, but their detailed state machines, grids, fold-specific failure, and validation values do not warrant their current main-text footprint. In a Q1 submission, this material risks looking like a development log rather than a focused test of a central hypothesis.

Retain one concise TQ-v1 paragraph in the main paper, because it informs the mechanism and guards against an overly simple “just quarantine rejected samples” conclusion. Reduce TQ-v2 and Quantile to one short paragraph or a compact table row stating that prespecified validation gates failed and outer data were not opened. Move formulas, grids, per-fold selection, and detailed negative diagnostics to Supplementary Material. The stopped branches should not be a top-level contribution.

## Minor Comments

1. **Title and assembly placeholders:** the manuscript still contains `[TITLE TO BE FINALIZED]`, six figure insertion markers, two table insertion markers, and a reference placeholder. These are submission blockers even though they are not scientific defects.
2. **HMOG threshold calibration:** define the exact approximate-EER algorithm, candidate thresholds, interpolation rule, impostor weighting, and tie handling. McGill tie handling is specified, but HMOG handling is not.
3. **HMOG sample truncation:** explain why the first 500 samples were discarded and why only the next 20 one-second windows were retained from each session. State how much usable session data this discards and why it does not bias chronology.
4. **Chronology:** justify that HMOG session numbering is a valid chronological order for the clean-drift replay and explain how the modulo-five split interacts with chronology.
5. **Update-threshold invariant:** state or enforce the condition ensuring (	au^{\mathrm{update}}_{u,t}\geq\tau_{u,t}). The formula is stricter only while the enrollment mean exceeds the current authentication threshold.
6. **Table 1 wording:** replace the `Decision` column and commands such as “Reject” and “Stop” with neutral journal language such as `Interpretation / protocol status`.
7. **Figure 1 wording:** “Poisoning-update budget” can be mistaken for incorporated updates. Use “presented poisoning attempts (K)” and keep MUR or incorporated counts separate.
8. **Figure 5 presentation:** the Guarded label is crowded against the upper boundary/title, the figure is extremely sparse, and no uncertainty is visible. It is better combined with the HMOG trade-off figure or moved to the supplement.
9. **Figure 6 aggregation:** the caption should state exactly how subjects were aggregated at each temporal unit and whether uncertainty is omitted. The current smooth profile lines and jagged FRR line can otherwise be mistaken for single-run trajectories.
10. **Reproducibility detail:** exact commit and SHA-256 values are valuable in a reproducibility appendix/data-availability statement, but they interrupt the main Methods narrative. Keep the repository/tag pointer in the article and move full hashes to Supplementary Material.
11. **Paper 2 metadata:** complete the Paper 2 proceedings metadata before submission if an authoritative final record exists; otherwise identify it explicitly as an accepted/in-press conference paper or manuscript, according to the target journal's policy.
12. **Readability:** several Introduction, Methods, and Discussion paragraphs repeat the full poisoning–censoring story. Shorten long multi-clause sentences and let the Results carry the numerical details once.

## Novelty Assessment

| Component | What is established | What this manuscript adds | Novelty level and overclaim risk |
|---|---|---|---|
| A. Poisoning adaptive biometric profiles | Direct prior work exists in adaptive face and fingerprint systems. | Behavioral-mobile score-profile instantiation with frozen future probes. | Incremental application; high overclaim risk if presented as a new attack class. |
| B. Separate authentication/update thresholds | Established in keystroke/template-update work and confidence-gated self-update. | Security and clean-drift evaluation of the separation in this pipeline. | Low conceptual novelty; useful control. |
| C. Guarded EMA | EMA and confidence gating are standard ingredients. | A precisely defined, reproducible instantiation with MUR/GUR and cross-dataset transfer. | Incremental engineering/methodological novelty, not a new defense principle. |
| D. Held-out poison/probe evaluation | Held-out attack evaluation is expected in sound security methodology. | Source-session separation, nested budgets, paired states, and frozen post-poison evaluation in behavioral authentication. | Moderate methodological value; not conceptually novel. |
| E. Selective-update bias / feedback censoring | Closely related to selective labels, pseudo-label confirmation bias, and endogenous sampling. | Authentication-specific formulation and direct profile-trajectory evidence. | Strongest mechanistic novelty, provided it is framed as a domain-specific manifestation rather than a newly discovered general bias. |
| F. Oracle-all diagnostic | Oracle/label-aware controls are standard experimental devices. | Holds state dynamics fixed while intervening on update eligibility. | Strong diagnostic design, modest method novelty. |
| G. TQ-EMA branches | Quarantine, temporal consistency, caps, and anchors are known defensive motifs. | Prespecified fail-closed evaluation and an informative negative result. | Limited novelty; primarily supplementary evidence. |
| H. Quantile branch | Robust quantile/median tracking is established. | A frozen q20/q50 implementation that fails validation. | Very weak standalone novelty; useful only as a bounded negative control. |
| I. External McGill replication | Replication itself is not a new method. | Independent two-day directional test with transferred Guarded rule and identity-disjoint attack pools. | Important evidential contribution, limited by (n=20) and severe shift. |
| J. Combined mechanism-study framing | Prior work often treats template updating, poisoning, and drift separately. | Links malicious inclusion and genuine-evidence exclusion in one frozen protocol and across two datasets. | Strongest overall contribution; integrative and mechanistic rather than algorithmic. |

**Strongest novelty:** the combined empirical mechanism study showing that the same accepted-only feedback rule creates both a poisoning channel and a selective evidence-censoring problem, supported by matched state trajectories and an independent directional replication.

**Weakest novelty:** Guarded EMA as a method, and especially the TQ/Quantile branches. A stricter update threshold is prior art, and the stopped branches do not establish a new effective algorithm.

The central novelty claim should therefore be: *a protocol-controlled, cross-dataset characterization of coupled malicious inclusion and genuine-evidence censoring in score-level adaptive behavioral authentication*. It should not be: *a novel two-threshold defense*.

## Methodology Assessment

### HMOG

The HMOG description is substantially reproducible. It specifies retained sessions/sequences, sensor axes, window statistics, sequence shape, session-disjoint outer assignment, fitting-only scaling, architecture, optimizer, training schedule, score definition, and use of frozen caches. The session-disjoint split and fitting-only scaler are strong leakage controls.

Remaining reproducibility gaps are the exact HMOG threshold-calibration procedure, model/training seeds, rationale for truncating each session to two sequences, exact early-stopping model-selection metric/tie behavior, and justification of session order as chronology. It should also be explicit that all 100 identities appear in fitting, validation, and test sessions: this is a within-enrolled-user verification protocol, not unseen-identity generalization.

### Poisoning protocol

The poison/probe split by whole source-session group, nested (K), matched method paths, and profile freeze before held-out evaluation are sound. The HMOG split is not source-identity-disjoint, so it mixes same-impostor/different-session and other regimes. That does not invalidate the attack but limits the generalization claim. McGill's source-identity-disjoint protocol helps, but the paper should explicitly distinguish the regimes.

The largest weakness is attack feasibility. The attacker is given enough score information to identify accepted near-boundary samples from a pool, while only the selected samples are charged to (K). This is best interpreted as conditional worst-case sensitivity of the update rule, not an eight-query black-box exploit.

### Clean drift

Separating adaptation candidates from evaluation checkpoints is a strong design choice, as is using (D=0) impostors in the claimant-only scenario. These choices isolate changes in the genuine stream and prevent evaluation samples from adapting the profile.

The limitation is construct validity. A normalized Gaussian direction in standardized handcrafted-feature space is not an empirical model of human behavioral drift. (D=1,2) are sensitivity levels, not natural drift magnitudes. Conclusions about real temporal adaptation must rely only on the much smaller McGill replication and remain mechanism-level.

### Oracle-all

Oracle-all is useful because it isolates information availability. It is unrealistic by design and should be described as a label-aware diagnostic comparator, not a deployable baseline and not a mathematical upper bound. Its FAR increase shows that following all genuine scores is not equivalent to improving the authentication system.

### TQ / Quantile

The methods are specified with impressive care, but their main-paper detail is disproportionate to their evidential role. The detailed controllers, grids, caps, and fail-closed logic belong in Supplementary Material. Main text should retain the stopping rules and the high-level reason each branch was tested.

## Statistical Assessment

The subject is the most defensible primary cluster for genuine-error comparisons. Averaging repeated paths within subject and folds within subject before paired resampling avoids treating 500 fold/repeat combinations as independent. Ten thousand paired bootstrap draws are adequate computationally, and the 99-subject complete-case check is a sensible sensitivity analysis.

However, there is cross-classified dependence in impostor outcomes: the same impostor source can contribute observations to multiple victim profiles. A victim-only bootstrap captures heterogeneity across claimants but not fully across impostor sources. The two-way victim-by-source analysis used for TQ-v1 FAR is the right type of robustness check and should be considered for the central poisoning/FAR contrasts using retained outputs. McGill has the same conceptual issue and only 18–20 victim clusters, making percentile-bootstrap tails unstable and intervals wide/discrete.

The five-fold (t)-bands in Fig. 1 should not be presented as “95%” uncertainty bands in the main scientific figure when folds overlap. The caption's disclaimer is responsible but insufficient. Show fold values/ranges descriptively or use an appropriate subject-level paired interval.

Formal null-hypothesis testing is **not inherently required**. A prespecified paired effect with a valid 95% interval answers the primary inferential question. A statistical reviewer is more likely to object to the absence of a paper-level primary contrast, the mismatch between the core claim and its uncertainty analysis, and unadjusted multiplicity across budgets/lambdas/drifts/methods than to the lack of (p)-values. State one primary security contrast and one primary adaptation contrast; label the rest exploratory or apply a planned multiplicity procedure.

The complete-case sensitivity result is promised in Methods but not visibly summarized in the main Results. Report the direction/conclusion or move the procedure to the supplement.

## Dataset / External Validation Assessment

### HMOG strengths

- 100 enrolled subjects and many sessions.
- Session-disjoint fitting, validation, and test partitions.
- Both accelerometer and gyroscope features.
- Fixed cached scores make method comparisons paired and computationally reproducible.
- Multiple session positions permit limited chronological replay.

### HMOG weaknesses

- The temporal shift is synthetic rather than naturally longitudinal.
- Only two constructed sequences per retained session are used, with limited explanation.
- The model and threshold yield high baseline FAR/ASR.
- Outer score caches informed sequential exploratory development.
- HMOG poison and probe pools are source-session-disjoint but not necessarily source-identity-disjoint.

### McGill strengths

- Independent dataset and independently trained classifier.
- Natural Day-1/Day-2 separation.
- Guarded (lambda=0.25) transferred without Day-2 tuning.
- Source-identity-disjoint poison/probe split.
- The main boundary effect is paired and its interval excludes zero.

### McGill weaknesses

- Only 20 subjects, and only 18 contribute to the boundary (K=8) contrast.
- Accelerometer-only signals and no gyroscope.
- Severe Day-2 failure: 78% Frozen late FRR.
- Modest Day-1 validation accuracy and a different model/preprocessing pipeline.
- Many boundary paths lack enough accepted candidates, producing eligibility-conditioned estimates.
- Oracle-all's very high FAR may reflect an extreme threshold collapse under domain shift rather than a representative adaptation regime.

**Conclusion on external evidence:** a reviewer can still say that external validation is small and weak. That criticism is valid if “validation” implies generalization of performance or effect magnitude. It is not fatal if the paper consistently claims only a small, independent, directional mechanism-level replication. Under that framing, McGill is a meaningful strength, but not decisive external validation.

## Threat Model Assessment

The boundary attacker is realistic only for deployments that expose scores, leak confidence ordering, permit local observation of model outputs, or admit a sufficiently accurate surrogate. The manuscript does not currently select one of these routes. A binary accept/reject interface does not reveal the margin ordering needed by the implemented selector, and the paper does not demonstrate a black-box search that reconstructs it.

Random selection is closer to an opportunistic attacker but produces much smaller effects; on McGill the paired interval includes zero. Therefore the main security conclusion is conditional on strong score access. This is acceptable for a vulnerability upper bound, but not for a claim that an ordinary device thief can achieve the reported increase with eight interactions.

The paper should add a threat-model table covering attacker knowledge, observable outputs, candidate pool, query budget, adaptation timing, replay capability, and excluded system compromises. The score-access assumption should be stated in the Abstract or Introduction, not only in Methods/Discussion. Candidate screening should be separated from the poisoning-update budget.

## Selective-Update Bias Assessment

The evidence that accepted-only eligibility changes the update stream is strong within the tested systems:

- Guarded and Oracle-all use the same EMA state equations but differ in whether rejected genuine observations are eligible.
- Their HMOG mean and threshold trajectories move in opposite directions.
- Guarded update rates fall while Oracle-all remains at 100%.
- The direction appears again under McGill Day-2 shift.
- The effect is consistent with selective-label and pseudo-label feedback concepts.

What is not yet established is that this is a fundamentally new statistical bias or a general property of all accepted-only biometric adaptation. A skeptical reviewer can call it ordinary sample-selection/confirmation bias. The correct defense is not to insist on conceptual firstness. The contribution is that the manuscript identifies, names, measures, and experimentally isolates the authentication-specific form and shows its security consequence.

The term “selective-update bias” is useful if always tied to the operational definition: *the discrepancy induced when authentication acceptance determines update eligibility*. To avoid the impression of relabeling, “accepted-only feedback censoring” should remain the primary descriptive phrase, with “selective-update bias” as the concise label. The manuscript should distinguish biased update-stream composition from statistical bias of a particular estimator.

## Structure and Presentation

At approximately 11,500 words before the final references, the manuscript is too long for the strength and breadth of its final claims. The issue is not six figures by itself; it is repetition plus detailed presentation of unsuccessful development branches.

### Recommended target

Target **7,500–8,500 words excluding references**, subject to the selected journal. A reduction of roughly **3,000–4,000 words** is realistic without removing essential evidence.

### Compression by section

- **Introduction:** cut 300–500 words by shortening the dissertation-program history and reducing repeated qualifications.
- **Related Work:** cut 500–700 words. Preserve Biggio, Lovisotto, Xue, Giot, selective labels, and the closest mobile systems; reduce broad survey cataloguing.
- **Methods:** cut 900–1,200 words by moving TQ-v2/Quantile details, grids, hashes, and invariant lists to Supplementary Material.
- **Results:** cut 300–500 words by compressing stopped branches and avoiding repetition of every value already present in tables.
- **Discussion:** cut 700–1,000 words by merging overlapping principal-findings, trade-off, implications, and conclusion-like passages.
- **Conclusion:** cut 300–500 words; it currently repeats most of Results and Discussion.

### Figures and tables

| Item | Recommendation | Reason |
|---|---|---|
| Fig. 1, HMOG poisoning ASR | **Essential** | Main security result; replace or de-emphasize overlapping-fold (t)-bands and rename (K). |
| Fig. 2, HMOG FAR–FRR trade-off | **Essential** | Concisely displays the absence of a free adaptation gain. |
| Fig. 3, HMOG trajectories | **Essential** | Best evidence for the central feedback-censoring mechanism. |
| Fig. 4, McGill poisoning | **Useful / main** | Direct external corroboration; could be combined with Fig. 1 as dataset panels. |
| Fig. 5, McGill trade-off | **Optional / supplementary** | Very sparse and conveys three numbers already reported; could be a second panel of Fig. 2. |
| Fig. 6, McGill trajectories | **Useful / supplementary** | Supports the external mechanism, but four panels are visually heavy and lack uncertainty display. Retain selected panels or move full figure to supplement. |
| Table 1, HMOG summary | **Useful / main** | Good synthesis, but replace laboratory `Decision` language with neutral protocol status. |
| Table 2, McGill effects | **Essential / main** | Provides effect sizes, intervals, and sample sizes that figures do not show. |

Six figures are not intrinsically excessive, but Figs. 2/5 and 3/6 are paired versions of the same stories. A focused main paper could use four figures (HMOG + McGill poisoning, HMOG trade-off, HMOG mechanism, compact McGill mechanism) and move the remaining detail to the supplement.

### Introduction and Related Work

The research gap is now substantially more honest than a typical adaptive-biometric paper. It explicitly concedes poisoning and two-threshold prior art. The remaining task is to make the residual gap narrower and sharper: no claim that the components are absent; only that their coupled evaluation with held-out future probes, update-stream composition, temporal recovery, and independent directional replication is limited.

Paper 1 and Paper 2 are used appropriately as program context, but the current paper should not lean on the authors' own systematic review to establish novelty. The closest primary work should do that. Paper 2 should be introduced only to define the inherited baseline and unresolved mechanism.

If a reviewer knows Biggio, Lovisotto, Xue, and Giot, the paper remains sufficiently distinct only as a **combined mechanism and evaluation study**. It is not sufficiently distinct as a new poisoning attack or new guarded updater.

### Discussion

The Discussion is scientifically cautious but overly defensive and repetitive. Qualifications appear in nearly every subsection, which can obscure the take-home message. Consolidate limitations once, then state the supported conclusion directly.

“Security–adaptation trade-off” alone is unsurprising: stricter updates reduce both malicious and genuine updates. What makes this paper potentially new is the specific causal chain and evidence:

1. accepted observations authorize profile changes;
2. near-boundary accepted impostors lower the future threshold;
3. a stricter update gate blocks that channel;
4. the same gate censors lower-scoring genuine evidence;
5. restoring that evidence reverses the trajectory but raises FAR;
6. the principal directions recur under an independent cross-day protocol.

That chain, rather than the generic word “trade-off,” should organize the Discussion.

## Top Rejection Risks

| Rank | Likely rejection reason | Likelihood | Severity | Fixable without new experiment? | Recommended response |
|---:|---|---|---|---|---|
| 1 | Main poisoning effect is shown at an already insecure EER-like operating point. | High | Major | Partly | Foreground the baseline FAR and limit practical claims; ideally add low-FAR operating-point sensitivity using existing scores. |
| 2 | Boundary attack assumes score access and ignores candidate-search/query cost. | High | Major | Partly | Specify white/gray-box capability, separate reconnaissance from (K), and call it a strong benchmark; optional binary-feedback experiment. |
| 3 | Algorithmic novelty is weak because poisoning and two-threshold updating are prior art. | High | Major | Yes | Reframe around the coupled inclusion/censoring mechanism and protocol-controlled evidence. |
| 4 | The paper does not deliver a deployable method that improves both security and adaptation. | Medium–High | Major | Yes | Present an evidence/mechanism paper, not a defense-solution paper; remove solution-oriented contribution language. |
| 5 | Sequential HMOG cache reuse and outer-data (lambda) carry-forward make the development largely exploratory. | High | Major | Yes | Add an explicit evidence hierarchy and treat McGill as the transferred test. |
| 6 | Core HMOG poisoning uncertainty relies on five overlapping-fold descriptive intervals. | High | Major | Yes, via existing-data reanalysis | Add paired subject-level and preferably victim-by-source uncertainty; declare the primary contrast. |
| 7 | HMOG synthetic drift has limited construct validity for natural behavioral adaptation. | High | Major | Partly | Restrict claims to mechanism sensitivity; use McGill only as cross-day corroboration. |
| 8 | McGill is too small, too shifted, and too weakly classified for broad external validation. | Medium–High | Major | Partly | Consistently say “small mechanism-level replication,” foreground (n=18/20), exclusions, and severe Day-2 FRR. |
| 9 | “Selective-update bias” may be seen as renaming ordinary selection/confirmation bias. | Medium | Moderate | Yes | Define it operationally and claim authentication-specific empirical characterization, not discovery of a universal bias. |
| 10 | TQ-v2/Quantile detail and repeated caveats make the paper unfocused and overlong. | High | Moderate | Yes | Move detailed failed branches and provenance mechanics to Supplementary Material; cut 3,000–4,000 words. |

## Must Fix / Should Fix / Optional

### MUST FIX

- Reframe novelty around the coupled poisoning/feedback-censoring mechanism, not Guarded EMA or a second threshold.
- State the EER-like/high-baseline-FAR limitation prominently and narrow deployment claims.
- Make attacker score access, candidate discovery, and uncounted query cost explicit.
- Declare the confirmatory/exploratory hierarchy, including HMOG cache reuse and (lambda) selection.
- Provide appropriate uncertainty and denominators for the core HMOG poisoning contrast using retained data; do not rely on overlapping-fold (t)-bands.
- Report boundary eligibility/exclusions prominently for both datasets.
- Limit McGill to small, directional, mechanism-level replication.
- Compress the main manuscript and move detailed TQ-v2/Quantile material to the supplement.
- Insert the actual tables/figures, choose the title, and generate the final references before submission.

### SHOULD FIX

- Discuss Oracle-all (D=0) behavior and avoid calling it a formal upper bound.
- Clarify HMOG chronology, threshold calibration, session truncation, and update-threshold invariants.
- Use one primary security contrast and one primary adaptation contrast; label the rest exploratory or address multiplicity.
- Replace Table 1's `Decision` language with neutral `Interpretation / protocol status` wording.
- Reduce exact hashes and protocol-test detail in the main text while preserving them in supplementary provenance.
- Consolidate limitations and remove repeated defensive caveats from every section.
- Improve figure economy by combining paired HMOG/McGill displays or moving Figs. 5–6 to the supplement.

### OPTIONAL

- Add operating-point sensitivity at prespecified lower FAR targets.
- Add a query-limited binary-feedback or surrogate-ranking attacker.
- Report computational/system costs if the target journal expects deployability evidence.
- Add a concise conceptual diagram of access decision versus update eligibility only if allowed by the journal's figure budget.

## No-New-Experiment Path

If no further experiment is run, the strongest submission path is:

1. Retitle and pitch the work as a mechanism/evaluation paper.
2. State that the boundary attack is score-informed and that (K) excludes reconnaissance cost in the Abstract, Introduction, and Threat Model.
3. State that the primary thresholds are EER-like and that absolute FAR prevents deployment claims.
4. Add a one-page evidence hierarchy separating exploratory HMOG development, validation-stopped branches, diagnostics, and transferred McGill replication.
5. Use retained outputs for a proper paired subject-level and victim-by-source uncertainty analysis of the main HMOG contrast. This is statistical reanalysis, not a new experiment.
6. Add an eligibility/denominator table for every headline contrast.
7. Reduce TQ-v2 and Quantile to supplementary negative controls and remove them from the main contribution list.
8. Cut 3,000–4,000 words, primarily from branch details, repeated qualifications, and repeated summaries.
9. Keep Figs. 1–3 as the central narrative; retain compact McGill evidence and move redundant external plots to supplementary material.
10. Select a journal that accepts security measurement, mechanistic negative results, and reproducible evaluation rather than requiring a new deployable algorithm.

This path can make the paper competitive without pretending that the current experiments establish operational security or general natural-drift adaptation.

## Need for Additional Experiments

**Answer: OPTIONAL.** No new experiment is strictly required for a carefully scoped mechanism paper. Two experiments would materially increase acceptance probability if the authors decide to add evidence:

1. **Operating-point sensitivity at deployment-oriented FAR targets** using the existing frozen scores. This directly tests whether poisoning amplification and Guarded suppression persist when the initial system is not operating near 12–23% FAR.
2. **A query-limited binary-feedback or surrogate-score attack** that counts candidate discovery as part of the budget. This converts the boundary result from a strong score-access benchmark toward a realistic attacker demonstration.

If only one is chosen, the operating-point sensitivity is more important because it addresses both practical security and the supply of accepted poisoning candidates. A third dataset or another adaptation architecture is not justified before submission.

## Title Review

**Proposed title:** *Poisoning and Selective-Update Bias in Online Behavioral Biometric Authentication*

- **Accuracy:** high; it names the two central mechanisms and the application domain.
- **Novelty signaling:** good, but “selective-update bias” may provoke a reviewer to ask whether this is simply selection bias under a new name. The manuscript must answer that question explicitly.
- **Searchability:** strong for poisoning, online adaptation, behavioral biometrics, and authentication.
- **Likely reviewer reaction:** positive if the paper is framed as mechanistic; skeptical if the title is used to imply invention of a new general bias.

The current candidate is suitable and no replacement is clearly better. A safer but slightly less distinctive fallback is *Poisoning and Accepted-Only Feedback Censoring in Online Behavioral Biometric Authentication*.

## Recommendation

**Current recommendation: Major Revision.**

There is no single fatal scientific flaw. The causal within-protocol poisoning effect is credible, the feedback-eligibility diagnostic is informative, and the external direction is useful. The current version nevertheless exposes too many attack surfaces for a Q1 reviewer: weak algorithmic novelty, permissive operating points, a strong score-access attacker, exploratory HMOG development, incomplete inference for the core HMOG claim, synthetic drift, and a small severe-shift replication.

**If the recommended non-experimental revisions are completed:** the likely recommendation would become **Minor Revision for a scope-compatible Q1 journal**, or a much stronger Major Revision response at a more algorithm-centric/security-top-tier venue. The paper would still not support claims of a deployable poisoning-resistant adaptive authenticator, but it could support a valuable mechanism and evaluation contribution.

**Critical scientific problem:** No fatal problem, but the combination of high baseline FAR and score-informed candidate selection is the most serious scientific limitation and must be treated as central, not peripheral.

## Q1 Readiness Score

| Dimension | Score / 10 | Rationale |
|---|---:|---|
| Novelty | 6.0 | Strong combined framing; weak component-level algorithmic novelty. |
| Technical rigor | 8.0 | Frozen protocols, leakage controls, stopping rules, manifests, and tests are strong. |
| Experimental design | 7.0 | Good held-out and diagnostic structure, limited by operating point, synthetic drift, and eligibility conditioning. |
| Statistics | 5.5 | Good subject aggregation for drift, but core poisoning inference and cross-classified dependence need work. |
| External validation | 6.0 | Independent and transferred, but only 20 subjects with severe Day-2 failure. |
| Reproducibility | 9.0 | Exceptional provenance and deterministic artifacts, assuming public availability is usable. |
| Writing | 7.0 | Clear and careful, but too long, repetitive, and defensive. |
| Positioning | 6.5 | Honest prior-art discussion; novelty hierarchy still needs sharpening. |
| Practical relevance | 5.5 | Important mechanism, but current operating points and attacker access limit deployment relevance. |
| **Overall Q1 readiness** | **6.5** | Promising mechanism paper requiring substantial reframing, statistical strengthening, and compression. |

### Final reviewer summary

- **Recommendation:** Major Revision.
- **Top three risks:** insecure baseline operating point; score-informed/query-unaccounted attacker; weak algorithmic novelty with exploratory HMOG development.
- **Critical scientific problem:** no fatal flaw, but the operating-point/threat-model combination is a major limitation.
- **New experiment required:** optional, not mandatory for a scoped mechanism paper.
- **Comment count:** 8 Major Comments; 12 Minor Comments.
- **Q1 readiness:** 6.5/10.
- **Journal selection:** appropriate after the Must Fix items are resolved and the paper is compressed; select a venue receptive to security measurement and mechanistic negative results.
