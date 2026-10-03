# 5. Discussion

## 5.1. Principal Findings

The results reveal a coupled security–adaptation trade-off in the tested score-level update schemes. Blind EMA exposed the adaptive profile to score-informed boundary poisoning: malicious observations that passed authentication were also allowed to modify the state used for future decisions. A separate Guarded update threshold sharply reduced this contamination pathway and returned post-poison ASR close to the Frozen operating point. The same conservative update policy, however, did not preserve late-FRR utility under claimant-only downward score shift.

The clean-drift controls locate the tension in the feedback available to the updater. Accepted-only policies observe a selected subset of genuine behavior because rejected genuine observations cannot enter the production profile. Oracle-all-genuine removed that censoring and followed the downward claimant-score shift more closely, but its threshold movement incurred a substantial FAR cost and did not yield a clear HTER advantage. TQ-EMA v1, TQ-EMA v2, and the frozen quantile representation did not establish useful recovery within their prespecified constraints. The McGill experiment reproduced the directions of the main poisoning, Guarded-defense, and feedback-censoring effects under an independent two-day protocol. Together, these findings do not identify a complete adaptive solution; they show that update security and legitimate drift recovery cannot be assessed independently under the tested protocols.

## 5.2. Poisoning Risk in Accepted-Only Online Adaptation

Blind EMA uses a single decision to authorize both access and learning. Once an impostor score exceeds the current authentication threshold, the observation is treated as eligible evidence about the claimant. The resulting state change affects the threshold applied to later attempts. Under the score-informed boundary strategy, held-out future impostor probes were accepted more frequently as the poisoning budget increased (Fig. [POISONING]).

The poison/probe separation is central to this interpretation. Attack candidates were selected only from the poisoning pool, while ASR was measured on a disjoint pool of source-session groups after adaptation had stopped. The observed increase therefore cannot be attributed to evaluating the exact observations used to poison the profile. Because Frozen and the malicious-update-blocking Oracle received the same scores without changing state, their agreement further isolates online profile modification as the relevant experimental difference.

The boundary strategy was intentionally stronger than uniform random selection. It used score information to identify already accepted observations nearest the initial boundary, whereas the random attack did not target this region and produced a smaller effect. The result should therefore be interpreted as vulnerability under a strong score-informed attacker model, not as evidence that every deployment exposes scores, supports the same query process, or will experience the same attack magnitude. Paper 2 identified the label-blind update pathway but did not execute a dedicated poisoning attack; the held-out Paper 3 protocol experimentally isolates that pathway [CITATION NEEDED: Paper 2].

## 5.3. Guarded Update Authorization as a Security Control

Guarded EMA separates two permissions: an observation may satisfy the access threshold without being trusted to modify the profile. The second threshold creates a narrower learning channel while leaving the authentication decision rule unchanged. Under boundary poisoning, this separation substantially reduced malicious incorporation and kept future ASR near Frozen (Fig. [POISONING]).

This result supports update authorization as a useful security control for adaptive profiles. It does not establish Guarded EMA as a complete adaptation policy. The exploratory lambda sweep showed that stricter gates reduce both malicious and genuine update availability. Moreover, MUR alone is not a complete measure of contamination severity. Guarded admitted a larger fraction of malicious observations on McGill than on HMOG, yet its post-poison ASR remained close to the corresponding Frozen value. Which observations enter the profile and how far they move the state matter in addition to the fraction incorporated.

The carried-forward lambda was a fixed reporting choice, not an optimized universal constant. Its effect depends on the score distribution, enrollment profile, and deployment conditions. The defensible conclusion is narrower: under both frozen protocols, a distinct update-authorization condition reduced the poisoning effect without changing the access threshold.

## 5.4. Selective-Update Bias Caused by Accepted-Only Feedback Censoring

The central adaptation problem is that the updater controls its own future evidence. During a downward genuine-score shift, some genuine observations fall below the authentication threshold. An accepted-only policy excludes those observations from learning and retains a stream enriched for higher genuine scores. Its adaptive state is therefore estimated from a selected upper subset rather than from the full claimant distribution. This process is referred to here as selective-update bias caused by accepted-only feedback censoring [CITATION NEEDED: selective-label and feedback-censoring literature].

The HMOG trajectories are consistent with this mechanism. Under claimant-only drift, the Guarded profile mean and threshold moved upward, even though the diagnostic Oracle-all state moved downward when all genuine adaptation observations were retained (Fig. [TRAJECTORY]). The gate protected the profile from low-confidence evidence, but it also removed precisely the evidence needed to represent a downward claimant shift. The resulting late-FRR pattern is consistent with a threshold that does not follow the full genuine-score distribution.

This interpretation is mechanism-specific rather than universal. The experiments concern short chronological streams, claimant softmax scores, and the tested profile rules. They do not establish a general theorem that every accepted-only biometric updater must drift upward or that all forms of confidence gating worsen FRR. They show that, in the evaluated protocols, authentication-conditioned observation created a systematic difference between the distribution presented to the updater and the distribution used to evaluate genuine access.

## 5.5. What the Oracle-All Control Shows—and What It Does Not

Oracle-all-genuine is a diagnostic upper bound on feedback availability. It preserves ordinary authentication decisions but permits every ground-truth genuine adaptation observation to update the state, including observations that the production system rejected. Its lower late FRR and downward profile trajectory indicate that the EMA moments can respond to lower genuine scores when rejected genuine evidence is restored.

This comparison supports accepted-only censoring as a contributor to the weak recovery of Blind and Guarded EMA. It does not show that unrestricted EMA is a usable solution. Oracle-all requires labels that are unavailable during ordinary deployment, and its improved genuine tracking was accompanied by a substantial increase in FAR. HTER changed little because the FRR and FAR movements opposed one another. Oracle-all is therefore evidence about recoverability and information availability, not a deployable baseline that should be selected on aggregate error.

The control also narrows the interpretation of the negative recovery results. EMA was not entirely incapable of moving with the synthetic claimant shift or the McGill day change. Rather, useful movement depended on access to observations that deployable accepted-only policies could not safely trust.

## 5.6. Why Recovery Mechanisms Did Not Restore Utility

TQ-EMA v1 created an isolated route through which rejected but near-boundary observations could contribute recovery evidence without receiving access. Its event audit nevertheless contained far fewer confirmed recovery updates than trusted high-score updates. The resulting operating point was more conservative and satisfied the safety constraints, but the method did not meet the prespecified late-FRR recovery criterion. This outcome is consistent with a recovery signal that was too infrequent to offset the dominant accepted-high-score stream; it does not establish that every quarantine design is ineffective.

TQ-EMA v2 addressed that specific imbalance by suppressing trusted updates that opposed a confirmed downward recovery episode. The fold-specific validation gate was not satisfied, so the protocol stopped before outer scores were opened. This is evidence about the frozen v2 controller under its fixed constraints, not an outer-test estimate and not a basis for post-hoc relaxation of those constraints.

The quantile branch tested whether changing the adaptive state, rather than only its admission gate, would improve recovery. Oracle-all Quantile reduced the gap associated with accepted-only censoring, but neither information regime outperformed Frozen on the validation recovery endpoint. This pattern indicates that censoring was an additional cost but not the only difficulty for the tested q20/q50 representation. The combined evidence suggests that both update admission and score-state dynamics matter when adaptation is based on short, noisy temporal streams.

These negative branches narrow the set of explanations supported by the tested implementations and prespecified parameter ranges. They do not reject quarantine, temporal evidence, or robust distribution tracking as general method families. They show that the frozen implementations did not provide evidence of useful recovery under the stated security and HTER constraints.

## 5.7. Security–Adaptation Trade-off

The trade-off figure summarizes why no tested score-level method produced a free adaptation gain (Fig. [TRADEOFF]). Permissive learning exposes a larger poisoning surface because more authenticated observations can influence future thresholds. Conservative accepted-only learning reduces that exposure but increasingly conditions adaptation on already high scores. Oracle-all occupies the opposite extreme: it responds strongly to claimant change because it observes all genuine candidates, but its unrestricted downward movement increases false acceptance.

This trade-off is observed under the present score generators, streams, and constraints; it is not an impossibility result for adaptive authentication. A system with trusted external evidence, richer temporal structure, or feature-level adaptation may occupy a different operating region. The present experiments nevertheless show why adaptation utility should not be evaluated only on genuine recovery and why poisoning resistance should not be evaluated only on malicious update counts.

HTER is useful as a balanced summary, but it can obscure the security meaning of opposing FAR and FRR movements. A decrease in FRR obtained by a comparable increase in FAR may leave HTER almost unchanged while materially changing the risk profile. FAR, FRR, ASR, update rates, and state movement should therefore remain visible as separate endpoints, with deployment-specific costs assigned before method selection.

## 5.8. External Replication on McGill Gait

McGill altered several conditions simultaneously: it contained fewer subjects, used accelerometer-derived channels without gyroscope, used a different fixed classifier, and provided a natural separation between collection days rather than synthetic feature drift. Despite these differences, the main effects reproduced directionally. Boundary poisoning increased Blind EMA ASR relative to Frozen, and the transferred Guarded rule reduced both contamination and post-poison ASR toward Frozen (Fig. [MCGILL_POISONING]).

The temporal comparison showed the same qualitative tension. Guarded did not improve late FRR relative to Frozen, whereas Oracle-all changed genuine tracking substantially and incurred a very large FAR cost (Fig. [MCGILL_TRADEOFF]; Fig. [MCGILL_TRAJECTORY]). This replication provides independent evidence that the same directional mechanisms can arise outside the HMOG protocol.

The replication does not support direct comparison of absolute HMOG and McGill error rates. Day-2 Frozen FRR on McGill was high, indicating a severe cross-day shift and weak absolute transfer of the fixed Day-1 classifier. The small cohort, missing gyroscope, boundary feasibility exclusions, and dataset-specific preprocessing further limit performance generalization. McGill is therefore evidence of mechanism-level reproducibility under a difficult two-day setting, not a benchmark claim about classifier quality.

## 5.9. Implications for Adaptive Behavioral Authentication

First, authentication confidence and update authorization should be treated as distinct design decisions. A separate update-authorization layer can reduce contamination even when the access rule itself is unchanged. This separation should be treated as a security boundary in adaptive-system design.

Second, the data observed by an online updater may be endogenous to its current threshold. Monitoring only accepted observations can hide the genuine behavior that the system most needs to recover. Evaluation should therefore audit rejected near-boundary genuine observations, update eligibility, and profile trajectories rather than reporting only aggregate acceptance rates.

Third, practical recovery requires evidence that is at least partly independent of the original access decision. Candidate sources include trusted step-up authentication, temporally consistent multi-session evidence, device or context signals, and multimodal corroboration. Such signals should authorize bounded recovery without retroactively granting access to rejected attempts.

Fourth, score-only location and scale updates may be insufficient under substantial temporal shift. Feature-level or model-level adaptation, explicit drift detection, and representations that separate claimant change from impostor overlap are justified research directions, but they require the same poisoning-aware controls as score-profile adaptation.

Finally, security and utility should be evaluated jointly. A useful protocol should measure held-out post-update attack success, genuine temporal recovery, FAR, update composition, and state displacement on the same frozen design. Rollback, rate limiting, anchors, and bounded movement remain relevant safeguards, but their value should be assessed against both adversarial contamination and legitimate drift.

## 5.10. Limitations

The HMOG temporal experiment used synthetic drift in standardized feature space. It was designed to expose score-profile dynamics under a controlled downward claimant shift, not to reproduce natural long-term behavioral evolution. The global scenario also shifts impostor observations, while the primary claimant-only scenario holds impostor scores at baseline. Neither construction captures all changes in sensor placement, activity, device state, health, environment, or user behavior that may occur in deployment.

The same overall HMOG outer score caches were reused across sequential exploratory branches. Although each branch used frozen rules and the validation-stopped methods did not access outer scores, the broader development sequence was informed by earlier observations from those caches. Later HMOG branches should therefore be treated as exploratory mechanism studies rather than independent confirmatory tests. The stopped TQ-EMA v2 and Quantile branches have no outer estimates, and TQ-EMA v1 was not evaluated in a combined drift-plus-poisoning experiment.

The boundary attacker had score-informed candidate selection. It is stronger than a purely binary-feedback attacker and may not match deployments that hide confidence scores, constrain queries, or aggregate decisions differently. Conversely, the experiments did not cover replay, sensor injection, model extraction, collusion, gradient-based attack, or compromised operating-system components. The results characterize the online profile-update surface defined in the threat model, not all attacks against mobile behavioral authentication.

Dataset coverage remains limited. HMOG was the single primary mechanistic dataset. McGill added an independent two-day replication but contained only 20 subjects, accelerometer-only inputs, no gyroscope, and a severe Day-2 shift. The boundary analysis also excluded victim-repeat paths without enough initially accepted near-boundary candidates. These properties restrict population-level and modality-level generalization.

The model scope was also narrow. The study adapted claimant softmax-score profiles generated by fixed LSTMs; it did not adapt features, representation layers, or classifier weights online. It did not compare multiple modern sequence encoders or evaluate whether calibrated likelihood ratios, embeddings, or uncertainty-aware scores would change the trade-off. No production smartphone deployment measured end-to-end latency, memory, energy, or user burden associated with recovery and step-up decisions.

Statistical inference was constrained by the available design. HMOG folds had overlapping fitting partitions and were used descriptively, while subject bootstrap intervals summarized the retained cohort rather than a universal deployment population. McGill had a small subject-level bootstrap sample. Validation-stopped branches cannot support claims about outer performance. These limitations preclude universal performance or impossibility claims and motivate independent confirmation on larger untouched longitudinal cohorts.

## 5.11. Future Work

The next priority is independent evaluation on larger multi-day datasets with natural longitudinal change, preserved chronology, multiple inertial modalities, and enough identities to support both victim- and impostor-source uncertainty. Such protocols should jointly measure adaptation utility and poisoning resistance rather than separating them into unrelated benchmarks. This direction is consistent with the longitudinal and adversarial-evaluation gaps documented in Paper 1 [CITATION NEEDED: Paper 1].

Method development should focus on trusted recovery evidence rather than broader parameter sweeps of the stopped branches. Step-up authentication, secure user-presence signals, temporally separated corroboration, and multimodal context could provide labels or confidence that are less dependent on the current biometric threshold. Their use should remain bounded, auditable, rate-limited, and reversible.

A second direction is to move beyond scalar score-profile adaptation. Drift-aware embedding updates, feature normalization, uncertainty-aware state models, and explicit change-point detection may represent claimant change without forcing a single threshold to absorb both distribution shift and security risk. These methods should be evaluated under held-out poisoning, natural drift, and combined drift-plus-attack streams with parameters fixed before outer testing.

Finally, longer field studies are needed to measure persistence, recovery time, user friction, and systems cost. A deployable evaluation should include rollback behavior, step-up frequency, on-device resource use, and the consequences of abrupt legitimate change. These studies would test whether the mechanisms observed here remain relevant when adaptation interacts with real user behavior and operational constraints.
