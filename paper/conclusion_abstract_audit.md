# Conclusion/Abstract Claim Audit

## Scope and Rules

This audit covers `paper/conclusion.md` and `paper/abstract.md`. Claims were checked only against the frozen manuscript and its existing claim/provenance audits. No experiment was run, no score was regenerated, no numerical endpoint was recomputed, and no validation-stopped outer result was opened. Current-study observations require no external citation in these two sections; the Abstract contains no citations.

## Strong-Claim Audit

| Exact wording or claim | Location | Source section | Source file | Evidence class | Numerical match | Softening/scope decision |
|---|---|---|---|---|---|---|
| “Online adaptation ... turns operational decisions into inputs to the future authentication state.” | Conclusion, paragraph 1 | Methods 3.3–3.5; Discussion 5.2 | `paper/methods.md`; `paper/discussion.md` | Supported interpretation of the update equations | Not numerical | Scoped to operational online adaptation rather than all adaptive systems. |
| The study jointly examines poisoning, update authorization, temporal recovery, and feedback availability. | Conclusion, paragraph 1; Abstract, methods | Methods 3.4–3.12 | `paper/methods.md` | Direct study-scope statement | Not numerical | Describes evaluated questions without claiming complete coverage of adaptive authentication. |
| Blind accepted-only EMA was vulnerable to score-informed boundary poisoning. | Conclusion, paragraph 2; Abstract, results | Results 4.1; Methods 3.4 | `paper/results.md`; `paper/methods.md` | Direct observation under the tested threat model | Yes | “Vulnerable” is tied to the score-informed boundary strategy and maximum tested budget. |
| Poisoning affected later decisions rather than merely reusing poison observations. | Conclusion, paragraph 2 | Methods 3.4; Discussion 5.2 | `paper/methods.md`; `paper/discussion.md` | Direct protocol fact plus supported interpretation | Not numerical | Limited to source-session-group-separated held-out probes; no identity-disjoint claim for HMOG. |
| Guarded update authorization returned ASR close to Frozen while retaining the access threshold. | Conclusion, paragraph 2; Abstract, results/conclusion | Results 4.2 and 4.8; Methods 3.3 and 3.5 | `paper/results.md`; `paper/methods.md` | Direct observation and method property | Yes | Described as substantial reduction, not elimination or universal optimality. |
| The security direction was reproduced on McGill. | Conclusion, paragraphs 2 and 4; Abstract, results | Results 4.8–4.9 | `paper/results.md` | Direct cross-dataset directional observation | Yes | Explicitly called an independent mechanism-level two-day replication, not performance validation. |
| Accepted-only policies exclude rejected genuine observations and retain a selected higher-score update stream during downward shift. | Conclusion, paragraph 3; Abstract, conclusion | Methods 3.3, 3.6, 3.7; Results 4.3–4.4; Discussion 5.4 | `paper/methods.md`; `paper/results.md`; `paper/discussion.md` | Supported mechanistic interpretation | Not numerical | Uses “supports” rather than “proves”; limited to tested score streams and policies. |
| Guarded did not preserve positive late-FRR utility relative to Frozen. | Conclusion, paragraph 3; Abstract, results | Results 4.3 | `paper/results.md` | Direct observation | Not numerically expanded in Abstract | Avoids claiming that every confidence gate worsens FRR. |
| Oracle-all restored genuine observations and changed tracking, with lower FRR and higher FAR. | Conclusion, paragraph 3; Abstract, results | Results 4.4 and 4.8; Methods 3.7 | `paper/results.md`; `paper/methods.md` | Direct observation plus supported interpretation | Yes | Oracle remains explicitly diagnostic and non-deployable; no overall-improvement claim. |
| The Oracle comparison supports selective-update bias caused by accepted-only feedback censoring. | Conclusion, paragraph 3; Abstract, conclusion | Discussion 5.4–5.5; Discussion claim audit | `paper/discussion.md`; `paper/discussion_claim_audit.md` | Supported interpretation | Not numerical | Presented as authentication-specific and contributory, not a universal theorem or established standard term. |
| TQ-EMA v1 did not meet its prespecified late-FRR recovery criterion. | Conclusion, paragraph 4 | Results 4.5 | `paper/results.md` | Direct protocol outcome | No number used | Does not generalize to all quarantine methods. |
| TQ-EMA v2 and Adaptive Quantile failed their validation gates; no outer estimates exist. | Conclusion, paragraph 4; Abstract, results | Results 4.6–4.7; Methods 3.9–3.10 | `paper/results.md`; `paper/methods.md` | Direct validation-stop outcome | No outer number used | States validation failure, not outer-test failure; `outer_test_loaded=false` is preserved. |
| Prespecified recovery alternatives did not establish deployable FRR recovery. | Abstract, results | Results 4.5–4.7 | `paper/results.md` | Bounded synthesis of one outer-tested and two validation-stopped branches | Not numerical | “Did not establish” replaces a general statement that recovery methods failed. |
| McGill uses natural day separation and should not be compared directly with HMOG absolute performance. | Conclusion, paragraph 4; Abstract, methods/results | Methods 3.6 and 3.12; Results 4.8; Discussion 5.8 | `paper/methods.md`; `paper/results.md`; `paper/discussion.md` | Direct protocol distinction and scope qualification | McGill numbers match within-dataset outputs | Does not label the Day-1/Day-2 difference as proven natural behavioral concept drift. |
| Access permission and learning permission should be distinct design decisions. | Conclusion, paragraph 5; Abstract, conclusion | Methods 3.3 and 3.5; Results 4.2 and 4.8; Discussion 5.9 | `paper/methods.md`; `paper/results.md`; `paper/discussion.md` | Result-supported design implication | Not numerical | Does not claim invention of a second threshold or a complete defense. |
| Future systems need trusted recovery evidence and joint security/utility evaluation. | Conclusion, paragraph 5; Abstract, final sentence | Discussion 5.9–5.11 | `paper/discussion.md` | Scoped design implication and future-work proposal | Not numerical | Proposed direction, not an evaluated solution. |

## Numerical Claims

All numerical values appearing in the Abstract are listed below. The same HMOG ASR and Oracle values are also used in the Conclusion; the Conclusion introduces no additional numerical endpoint.

| Abstract wording | Metric and condition | Authoritative source | Exact unrounded value | Prose-rounded value | Check |
|---|---|---|---:|---:|---|
| “22.92% for Frozen” | HMOG boundary, \(K=8\), post-poison ASR | `results/paper3_attack_v2/paper3_attack_v2_summary.csv`, `frozen_post_ASR` | 22.919615705108985 | 22.92% | Matches Results 4.1–4.2. |
| “53.96% for Blind EMA” | HMOG boundary, \(K=8\), post-poison ASR | `results/paper3_attack_v2/paper3_attack_v2_summary.csv`, `ema_blind_post_ASR` | 53.957254011869495 | 53.96% | Matches Results 4.1–4.2. |
| “22.93% for Guarded EMA” | HMOG boundary, \(K=8\), \(\lambda=0.25\), post-poison ASR | `results/paper3_final_analysis_20261002_v2/paper3_final_lambda_sweep.csv`, `post_ASR` | 22.933284398976095 | 22.93% | Matches Results 4.2. |
| “improved late false rejection rate by 6.60 percentage points” | HMOG claimant-only \(D=2\), Oracle-all late-FRR gain relative to Frozen | `results/paper3_oracle_all_drift_20261001_v2/paper3_guarded_drift_paired_bootstrap.csv`, `late_FRR_gain` | 6.599999999999999 | +6.60 pp | Matches Results 4.4; positive gain means lower FRR than Frozen. |
| “late false acceptance rate increased by 6.08 points” | HMOG claimant-only \(D=2\), Oracle-all late-FAR change relative to Frozen | Same paired-bootstrap CSV, `late_FAR_change` | 6.079635898928979 | +6.08 pp | Matches Results 4.4. |
| “12.37% for Frozen” | McGill Day-2 boundary, \(K=8\), post-poison ASR | `results/paper3_external_mcgill_20261003_v1/attack_summary_bootstrap.csv`, Frozen `post_ASR` | 12.3705013249111 | 12.37% | Matches Results 4.8. |
| “32.09% for Blind EMA” | McGill Day-2 boundary, \(K=8\), post-poison ASR | Same external CSV, Blind EMA `post_ASR` | 32.09227049177825 | 32.09% | Matches Results 4.8. |
| “12.48% for the transferred Guarded rule” | McGill Day-2 boundary, \(K=8\), post-poison ASR | Same external CSV, Guarded EMA `post_ASR` | 12.475813753256453 | 12.48% | Matches Results 4.8. |

The numerals \(K=8\) and \(D=2\) are frozen protocol conditions, not computed results. Their authoritative definitions are in Methods 3.4 and 3.6.

## Wording and Consistency Checks

- No claim states that poisoning adaptive biometrics is new.
- No claim states that a second update threshold is new.
- Guarded EMA is not described as solving or completely preventing poisoning, and \(\lambda=0.25\) is not described as universally optimal.
- HMOG temporal change remains a controlled synthetic feature shift; McGill remains an independent mechanism-level replication with natural day separation.
- Oracle-all is consistently non-deployable and diagnostic.
- TQ-EMA v2 and Adaptive Quantile are described only through validation outcomes; no outer estimate is reported or implied.
- Negative branches are summarized as not establishing deployable recovery under frozen criteria, rather than as general failure of quarantine or robust tracking.
- No universal impossibility claim is made about score-level or behavioral adaptation.
- The Abstract contains no citation, no detailed hyperparameter list, and no claim that absolute HMOG and McGill performance is directly comparable.
- No inconsistency with the frozen Results or existing claim audits was found.

## Candidate Titles

1. Poisoning and Selective-Update Bias in Online Behavioral Biometric Authentication
2. Poisoning, Feedback Censoring, and Online Adaptation in Behavioral Continuous Authentication
3. Access as a Learning Gate: Poisoning and Selective Feedback in Adaptive Behavioral Authentication
4. Online Behavioral Profile Adaptation Under Poisoning and Accepted-Only Feedback
5. Separating Access from Learning: Poisoning and Feedback Censoring in Continuous Behavioral Authentication
