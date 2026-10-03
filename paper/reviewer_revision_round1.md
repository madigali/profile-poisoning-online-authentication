# Reviewer Revision Round 1

Revision date: 4 October 2026.

Scope: mandatory pre-submission revisions for Priorities 1–7. No model was retrained, no score was regenerated, no drift or attack path was created, no partition or seed was changed, no adaptive method was rerun, and no validation-stopped outer data was opened. Frozen result packages, manifests, original figures, and original result CSVs were not modified.

## Priority 1 — Novelty Reframing

**Reviewer concern.** The previous narrative could make Guarded EMA, a separate update threshold, or stopped recovery branches appear to be the main novelty despite direct prior art. The stronger contribution is the protocol-controlled characterization of one accepted-only feedback loop that produces malicious inclusion and genuine-evidence censoring.

**Changes.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/abstract.md` | Entire abstract | Security and adaptation findings were presented as related observations without making the coupled mechanism the first contribution | Opens with the malicious-inclusion/genuine-censoring feedback loop and describes Guarded as separate update authorization | Frozen HMOG poisoning, clean temporal, Oracle, and McGill outputs | Existing results retained; primary CI added under Priority 5 | No |
| `paper/introduction.md` | Final framing and contribution list | Held-out poisoning and Guarded could dominate the contribution hierarchy | Reordered contributions: coupled mechanism first; held-out protocol second; update authorization as control third; Oracle diagnostic fourth; McGill replication fifth | `paper/reference_claim_matrix.md`; Giot, Biggio, Lovisotto, and Xue positioning already in the literature audit | No factual result changed | No |
| `paper/related_work.md` | Synthesis | Separate thresholds and poisoning risk could be interpreted as original concepts | Explicitly identifies Giot as threshold-separation prior art and Biggio/Lovisotto/Xue as adaptive-biometric poisoning precedents; positions Paper 3 as a joint mechanism study | Existing verified citations and literature audit | No | No |
| `paper/discussion.md` | Principal findings and Guarded interpretation | Guarded risked being treated as the paper's novel defense | Describes Guarded as an established-style security intervention used to isolate update authorization; centers the coupled feedback mechanism | Frozen comparisons and prior-art audit | No | No |
| `paper/conclusion.md` | Overall claim | Algorithm-centric conclusion | Centers access/learning coupling and limits TQ/Quantile to supporting negative evidence | Frozen stage outcomes | Primary CI added under Priority 5 | No |

**Remaining risk.** The mechanism is characterized in score-level profiles on two datasets, not proven as a universal property of all accepted-only adaptive biometric systems. The manuscript now states this boundary.

**Resolution status: fully resolved for manuscript positioning.**

## Priority 2 — Operating Point

**Reviewer concern.** HMOG Frozen ASR/FAR near 23% and the McGill boundary baseline near 12% are not deployment-grade security targets. Guarded returning near Frozen must not be described as making the system secure.

**Changes.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/abstract.md` | Results/conclusion | Relative suppression could be read as absolute security | Identifies HMOG as approximately equal-error and states that returning near Frozen does not establish system security or low-FAR performance | Threshold protocol; Frozen ASR/FAR outputs | No | No |
| `paper/introduction.md` | Scope paragraph | Deployment meaning was implicit | Separates mechanistic amplification from deployment suitability | Validation threshold definition | No | No |
| `paper/methods.md` | 3.3–3.4 | Threshold was described technically but not operationally qualified | Defines the threshold as validation-calibrated and approximately EER-like; states that the contrast estimates additional acceptance relative to Frozen | Frozen protocol/configuration | No | No |
| `paper/results.md` | 4.1, 4.2, 4.8 | Guarded near Frozen could be read as a secure operating point | Reports the Frozen baseline explicitly and interprets Guarded only as suppression of additional Blind amplification | Frozen HMOG and McGill results | No | No |
| `paper/discussion.md` | 5.2, 5.3, 5.10 | Practical security limitation was not prominent enough | Distinguishes update-rule vulnerability, underlying classifier security, and deployment suitability | Observed operating points | No | No |
| `paper/conclusion.md` | Poisoning paragraph | Possible deployment overreach | Adds the EER-like/minimum-HTER qualification and rejects an absolute-security interpretation | Threshold protocols | No | No |

**Remaining risk.** Low-FAR operating-point sensitivity remains unmeasured and is now presented as an untested generalization, not hidden by the relative result.

**Resolution status: fully resolved as a disclosure/scope revision; the prohibited low-FAR experiment was not performed.**

## Priority 3 — Boundary Attacker

**Reviewer concern.** Readers could misinterpret (K=8) as a realistic eight-query black-box attack.

**Changes.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/threat_model_table.md` | New table | Capabilities and omissions were distributed across prose | Defines boundary as a score-informed strong benchmark; records score access, pool access, ranking, screening, timing, and excluded capabilities | Frozen attack implementation and protocol | No | No |
| `paper/abstract.md` | Methods qualification | Query burden not visible | States that (K) counts selected presented poisoning attempts, excluding screening/reconnaissance; binary-feedback-only attack not demonstrated | Attack code/protocol audit | No | No |
| `paper/introduction.md` | Study overview | Boundary interface insufficiently explicit | Adds score access and (K) accounting | Attack protocol | No | No |
| `paper/methods.md` | 3.4 and capability table | Boundary could be labeled black-box without qualification | Formalizes ranking by initial margin, distinguishes score access from model-internal white-box access, and enumerates exclusions | Frozen attack implementation | No | No |
| `paper/discussion.md` | 5.2 and 5.10 | Real-world feasibility could be overstated | States that total query cost and a binary-feedback search are unknown | Protocol limits | No | No |

**Remaining risk.** The total real-world reconnaissance cost and a feasible binary-feedback-only boundary search remain unmeasured.

**Resolution status: fully resolved for threat-model transparency.**

## Priority 4 — Evidence Hierarchy

**Reviewer concern.** Inherited, exploratory, diagnostic, validation-selected, validation-stopped, and transferred results were not summarized in one place.

**Changes.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/evidence_hierarchy.md` | New full table | Inferential status scattered across files | Classifies nine stages and records parameter status, data access, inferential role, and final-claim role | Frozen configs, manifests, notes, and result packages | No | No |
| `paper/methods.md` | 3.1 | Main text lacked a compact hierarchy | Adds the compact nine-stage table; marks Guarded (lambda=0.25) as exploratory carry-forward, TQ-v2/Quantile as validation-stopped, and McGill as transferred | Same provenance records | No | No |
| `paper/results.md`, `paper/discussion.md`, `paper/conclusion.md` | Cross-stage interpretation | Stopped branches could appear equivalent to outer evaluations | Separates outer results from validation-only stopping evidence | Manifests with `outer_test_loaded=false` | No | No |

**Remaining risk.** HMOG development used sequential access to the same broad outer caches, so later outer HMOG analyses remain mechanism studies rather than untouched confirmation. This is now explicit.

**Resolution status: fully resolved.**

## Priority 5 — Primary HMOG Poisoning Inference

**Reviewer concern.** Five overlapping folds cannot be treated as five independent inferential units, and the primary Blind-minus-Frozen effect lacked paired subject-level uncertainty.

**Data audit.** `paper/hmog_poisoning_inference_data_audit.md` identifies the granular frozen outcome file, its 3,991,120 rows, schema, SHA-256, compact-package hash matches, pairing keys, and unavailable source-identity fields.

**Analysis performed.** For each eligible boundary (K=8) fold-victim-repeat path, Blind post-ASR minus Frozen post-ASR was computed. Repeats were averaged within fold and victim; five fold means were then averaged within each of 100 victims. Victims were resampled with replacement for 10,000 percentile-bootstrap draws using seed 4242.

**Primary result.** Blind EMA minus Frozen post-poison ASR = **+31.04 percentage points; 95% subject-bootstrap CI [+26.95, +35.20]**, based on 100 victims, 500 fold-victim units, and 49,889 paired eligible paths.

**Derived only from retained frozen outputs; no experiment, rescoring, or attack rerun was performed.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/hmog_primary_poisoning_effect.csv` | New machine-readable output | No subject-level primary effect table | Saves 100 victim effects and contributing-path counts | Frozen `subject_repeat_metrics.csv` | Yes: derived subject effects | Yes, permitted aggregation only |
| `paper/hmog_primary_poisoning_bootstrap.csv` | New machine-readable output | No primary bootstrap distribution | Saves 10,000 victim-bootstrap means | Same frozen retained outcomes | Yes: derived bootstrap draws | Yes, permitted aggregation only |
| `paper/results.md` | 4.1 | Only descriptive fold aggregation was prominent | Adds the primary paired subject-bootstrap CI and denominators; labels remaining budgets/random comparisons exploratory | Reanalysis above | Yes: adds CI/counts; point estimate unchanged | Yes |
| `paper/methods.md` | 3.11 | Primary security contrast and hierarchy were implicit | Declares primary security/adaptation contrasts and the victim-aggregation procedure | Frozen protocol and retained data | No result changed | No experiment |
| `paper/manuscript_full.md` | Fig. 1 caption | Fold t-bands could look confirmatory | States that bands are descriptive and not used for primary inference; directs readers to the subject-bootstrap CI | Existing unchanged figure plus reanalysis | Caption only | No |

**Two-way robustness.** Infeasible. The retained outcome rows do not identify impostor sources or source-specific contributions to the probe outcome. No approximation was made and no two-way CSV was created.

**Remaining risk.** Figure 1 still contains the original descriptive fold t-bands, now explicitly subordinated to the primary subject-bootstrap inference. The granular 1.2 GB outcome file is retained in the original run workspace but not in the compact Git result package; its hash and exact provenance are recorded.

**Resolution status: partially resolved.** The requested primary subject-level inference is complete. The victim-by-impostor-source robustness interval is impossible from retained outcome-level records, and the original figure was not regenerated.

## Priority 6 — Denominators and Eligibility

**Reviewer concern.** Boundary feasibility conditions on having enough initially accepted candidates and can select easier-to-attack paths.

**Changes.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/attack_eligibility_summary.md` | New human-readable audit | Denominators and reasons were not consolidated | Reports total/eligible/excluded paths, victims, strategy rules, pool separation, and counts by 0–7 available candidates | Frozen exclusions and retained subject-repeat/by-fold files | Yes: adds denominators | Yes, permitted counting only |
| `paper/attack_eligibility_summary.csv` | New machine-readable table | No consolidated eligibility CSV | Saves four HMOG/McGill strategy rows and exclusion bins | Same frozen records | Yes: derived counts | Yes, permitted counting only |
| `paper/methods.md` | 3.4 and 3.12 | Conditional cohort not sufficiently visible | States HMOG 49,889/50,000 and McGill 1,456/2,000 boundary eligibility; explains (K=0) cohort rules | Frozen exclusions/results | Yes: adds counts | No new experiment |
| `paper/results.md` | 4.1 and 4.8 | Effective denominators absent from main results | Adds eligible/excluded paths and victim counts | Same records | Yes: adds counts | No new experiment |
| `paper/discussion.md` | Limitations | Feasibility-selection risk was understated | Explains possible overrepresentation without claiming its direction or magnitude | Eligibility audit | No | No |

**Key denominators.** HMOG boundary (K=8): 49,889 eligible and 111 excluded of 50,000 possible fold-victim-repeat paths; 100 victims and 500 fold-victim units contribute. McGill boundary (K=8): 1,456 eligible and 544 excluded of 2,000 victim-repeat paths; 18 of 20 victims contribute.

**Remaining risk.** Conditioning could bias effect magnitude. Existing records quantify selection but cannot estimate the counterfactual effect on infeasible paths.

**Resolution status: fully resolved for available retained records.**

## Priority 7 — Drift and Oracle Scope

**Reviewer concern.** Synthetic HMOG sensitivity levels could be mistaken for calibrated natural drift, McGill day separation could be treated as isolated behavior change, and Oracle-all could be overstated as a formal upper bound or correct adaptation path.

**Changes.**

| File | Section | Old issue | New wording/action | Source/evidence | Numerical content changed? | New analysis? |
|---|---|---|---|---|---|---|
| `paper/methods.md` | 3.6–3.7 and 3.12 | Drift/oracle interpretations could exceed the protocol | Defines (D=0,1,2) as controlled standardized-feature sensitivity levels; Oracle as label-aware information-availability intervention; McGill as real cross-day shift | Frozen protocols | No | No |
| `paper/results.md` | 4.4 | Oracle benefit could be attributed only to drift recovery | Adds explicit (D=0) result: FRR −4.73 points and FAR +5.51 points relative to Frozen | Frozen Oracle clean-drift output | Existing values made explicit | No |
| `paper/discussion.md` | 5.4–5.8 and limitations | “Upper bound” and “natural drift” language too strong | States that Oracle is not a formal upper bound and partly moves the operating point; enumerates McGill day-effect confounding | Frozen outputs and dataset protocol | No | No |
| `paper/abstract.md`, `paper/conclusion.md` | Interpretation | Mechanistic evidence risked causal overreach | Narrows claim to trajectory change supporting censoring as a contributor; rejects uniquely correct-path interpretation | Oracle controls and trajectories | No | No |

**Remaining risk.** HMOG does not measure natural drift magnitude, and McGill cannot isolate behavior from day-specific context, placement, acquisition, or transfer effects.

**Resolution status: fully resolved for claim scope.**

## Round-1 Disposition

- Fully resolved: Priorities 1, 2, 3, 4, 6, and 7.
- Partially resolved: Priority 5, because the primary subject-level analysis is complete but victim × impostor-source resampling is infeasible and the original Fig. 1 was not regenerated.
- Manuscript files changed: eight (`abstract.md`, `introduction.md`, `related_work.md`, `methods.md`, `results.md`, `discussion.md`, `conclusion.md`, and `manuscript_full.md`).
- No title or journal formatting was changed.
- TQ-EMA v1/v2 and Quantile scientific outcomes remain unchanged.

The paper is ready for the next explicit decision between operating-point sensitivity and manuscript compression. Operating-point sensitivity remains the higher-value scientific addition if a further experiment is authorized, because the strongest unresolved external-validity question is whether the poisoning amplification persists at deployment-oriented low-FAR thresholds. Under the present no-new-experiment scope, the correct next action is manuscript compression and submission-focused editing, with low-FAR sensitivity listed as the optional final experiment rather than implied by current evidence.
