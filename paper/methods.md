# 3. Methods

## 3.1. Study Design and Experimental Overview

This study examined two coupled risks in score-level online adaptation for behavioral-biometric continuous authentication: profile poisoning by accepted impostor observations and feedback censoring when rejected genuine observations are excluded from adaptation. The study was organized as a sequence of mechanism-focused experiments rather than as a general classifier benchmark. HMOG was the primary mechanistic dataset \cite{Sitova2016HMOG}. A fixed LSTM score generator inherited from Paper 2 \cite{Serbin2026AdaptiveLSTM} was used to evaluate (i) held-out poisoning of Blind EMA, (ii) confidence-gated update authorization, (iii) adaptation under synthetic temporal feature drift, and (iv) diagnostic and recovery controls. A separately locked two-day McGill Gait protocol examined whether the principal poisoning, defense, and feedback-censoring patterns transferred to an independent dataset with natural day separation \cite{Frank2010McGillGaitDataset}.

The experimental branches were developed sequentially, so their evidential roles are not interchangeable. The following compact table records the paper-level hierarchy. “Primary reporting contrast” below defines the final manuscript focus; it does not retroactively convert the exploratory HMOG development sequence into an untouched confirmatory study. TQ-EMA v2 and the Adaptive Quantile Profile used fail-closed validation: if any outer fold lacked a configuration satisfying the fixed validation constraints, outer test scores were not loaded. The McGill protocol transferred the HMOG reporting rule before Day-2 outcomes were accessed. The subsequent operating-point study was prospectively specified on score caches whose reference outcomes had already been inspected.

| Stage | Dataset | Parameter/data status | Inferential role | Outer test accessed? | Role in final claim |
|---|---|---|---|---|---|
| Paper 2 baseline | HMOG | Inherited fixed EMA and cached score pipeline | Inherited | Previously evaluated | Defines Blind EMA and the unresolved update pathway |
| Attack v2 | HMOG | Fixed attack protocol; developed on HMOG | Exploratory primary mechanism evidence | Yes | Tests malicious inclusion on future probes |
| Guarded lambda sweep | HMOG | Exploratory outer-data sweep; \(\lambda=0.25\) carried forward | Exploratory | Yes | Update-authorization intervention, not untouched parameter confirmation |
| Clean drift | HMOG | Frozen synthetic sensitivity protocol | Exploratory mechanism analysis | Yes | Tests accepted-only temporal utility |
| Oracle-all | HMOG | Label-aware fixed diagnostic | Diagnostic | Yes | Intervenes on genuine-evidence availability |
| TQ-EMA v1 | HMOG | Validation-selected under a prespecified branch rule | Branch-specific outer evaluation | Yes | Supporting negative recovery evidence |
| TQ-EMA v2 | HMOG | Validation gate failed | Validation-stopped | No | No outer estimate |
| Adaptive Quantile Profile | HMOG | Validation gate failed | Validation-stopped | No | No outer estimate |
| Transferred replication | McGill | \(\lambda=0.25\) transferred without Day-2 tuning | External directional mechanism-level replication | Yes, after the viability gate | Tests whether principal directions recur |
| Operating-point sensitivity | HMOG and McGill | Reference plus nominal-5% and nominal-1% calibration-FAR conditions; fixed scores, \(\alpha\), \(\lambda\), pools, and seeds | Prospectively specified sensitivity analysis on previously inspected caches | Previously evaluated caches reused | Defines operating-point scope of reference findings |

The full evidence-status record and protocol provenance are retained separately. HMOG method development was frozen under Git tag paper3-method-freeze-2026-10-02; the external replication was frozen under paper3-external-mcgill-v1-2026-10-03; and the operating-point package was frozen under paper3-operating-point-sensitivity-v1-2026-10-04.

## 3.2. Primary HMOG Dataset and Score Generation

The primary experiments used HMOG, with 100 enrolled subjects and a nominal design of 24 smartphone-interaction sessions per subject. The canonical preprocessing pipeline retained 2,392 usable sessions and 4,784 sequences after documented missing or empty sensor files. Only the physical x-, y-, and z-axes from the accelerometer and gyroscope were used; metadata fields and session identifiers were excluded from model input. The pipeline assumed the nominal HMOG sampling rate of 100 Hz and did not estimate the realized sampling rate.

For each session, the first 500 sensor samples were discarded. The next 20 non-overlapping windows of 100 samples were retained. Six statistics—mean, standard deviation, minimum, maximum, root mean square, and skewness—were computed for each of the six inertial channels, yielding a 36-dimensional representation per one-second window. Ten adjacent windows formed a 10 × 36 sequence. The sequence step was 10 windows, so sequences did not overlap and never crossed session boundaries.

Five session-disjoint outer folds were defined by assigning session number r to group g(r) = (r − 1) mod 5. For outer fold f, group f was the test partition, group (f + 1) mod 5 was the validation/calibration partition, and the remaining three groups were used for model fitting. Every retained subject occurred in all three partitions. A StandardScaler was fitted only to flattened time steps from the fitting partition and then applied unchanged to validation and test data.

The score generator was the canonical Paper 2 LSTM: two recurrent layers with 64 hidden units per layer, layer normalization, a 32-unit ReLU layer, dropout 0.30, and a 100-class softmax output. It was trained with cross-entropy loss and Adam at learning rate 1e-3, batch size 256, for at most 20 epochs, with early-stopping patience 4. The canonical implementation also used ReduceLROnPlateau with factor 0.5 and patience 2. The authentication score for claimant u was the softmax probability assigned to class u, with larger values interpreted as more genuine-like. Paper 3 reused the frozen per-fold LSTM score caches and did not retrain the score generator for method comparisons.

## 3.3. Authentication Score and Baseline Profiles

For claimant \(u\), validation genuine scores initialized the profile mean \(\mu_{u,0}\) and second raw moment \(q_{u,0}\). The profile standard deviation and authentication threshold before observation \(t\) were

\[
\sigma_{u,t}=\sqrt{\max\left(q_{u,t}-\mu_{u,t}^{2},\epsilon^{2}\right)},
\qquad
\tau_{u,t}=\max\left(0,\mu_{u,t}-k_u\sigma_{u,t}\right),
\]

where \(\epsilon=10^{-4}\). Validation genuine and impostor scores defined the claimant-specific approximate equal-error threshold \(\tau_{u,0}\), and

\[
k_u=\frac{\mu_{u,0}-\tau_{u,0}}{\sigma_{u,0}}
\]

made the initial adaptive threshold equal to the validation-calibrated threshold. The authentication decision was

\[
a_t=\mathbb{1}[s_t\geq \tau_{u,t}].
\]

This claimant-specific threshold was the approximate equal-error operating point inherited from the Paper 2 protocol. It was used to study relative state changes under a fixed validation-calibrated rule, not selected as a deployment-grade low-FAR target. Accordingly, the poisoning experiment estimates additional acceptance caused by adaptation relative to Frozen at this operating point; it does not establish absolute deployment security.

Frozen retained \(\tau_{u,0}\) and never changed profile state. Blind EMA used \(\alpha=0.05\) and, after an accepted observation, updated

\[
\mu_{u,t+1}=(1-\alpha)\mu_{u,t}+\alpha s_t,
\qquad
q_{u,t+1}=(1-\alpha)q_{u,t}+\alpha s_t^2.
\]

Rejected observations did not update either moment. This rule was label-blind: an accepted genuine or impostor observation was processed identically.

Guarded EMA separated access authentication from update authorization. Access continued to depend only on \(s_t\geq\tau^{\mathrm{auth}}_{u,t}\). The raw update threshold was

\[
\tau^{\mathrm{update,raw}}_{u,t}
=\tau^{\mathrm{auth}}_{u,t}+\lambda\left(\mu_{u,0}-\tau^{\mathrm{auth}}_{u,t}\right).
\]

An update was authorized only under the conjunction

\[
s_t\geq\tau^{\mathrm{auth}}_{u,t}
\quad\land\quad
s_t\geq\tau^{\mathrm{update,raw}}_{u,t}.
\]

Equivalently,

\[
\tau^{\mathrm{update,effective}}_{u,t}
=\max\left(\tau^{\mathrm{auth}}_{u,t},\tau^{\mathrm{update,raw}}_{u,t}\right),
\]

and, for the non-negative \(\lambda\) values evaluated here,

\[
\tau^{\mathrm{update,effective}}_{u,t}-\tau^{\mathrm{auth}}_{u,t}
=\lambda\max\left(\mu_{u,0}-\tau^{\mathrm{auth}}_{u,t},0\right).
\]

Thus an observation could be accepted for access but withheld from learning. When \(\tau^{\mathrm{auth}}_{u,t}\geq\mu_{u,0}\), however, the additional effective margin was zero and Guarded imposed no restriction beyond authentication in that state. This is an algebraic property of the executed rule, not a modified defense. The main carried-forward comparison used \(\lambda=0.25\); this value was an exploratory carry-forward from the HMOG poisoning sweep and was not treated as universally optimal.

Two oracle controls were kept distinct. In the malicious-only poisoning experiment, Oracle EMA made the same authentication decisions as the other methods but blocked all known-impostor profile updates; with no genuine adaptation observations in that phase, it was a contamination control expected to remain equal to Frozen. In the clean-drift experiment, Oracle-all-genuine applied the canonical EMA update to every ground-truth genuine adaptation candidate, including rejected candidates. Oracle-all used labels only to determine update eligibility and was a non-deployable diagnostic control.

## 3.4. Poisoning Threat Model

The attacker sought to modify the victim's online score profile so that future, previously unused impostor observations would be accepted more often. For each fold, victim, and Monte Carlo repeat, test-set impostor samples were partitioned before attack selection. Whole (source identity, session) groups were assigned to either a poisoning pool or a held-out probe pool, with an approximately 50% probe allocation. No source-session group crossed the two pools, although the split was not necessarily source-identity-disjoint.

Two attack strategies were evaluated. The random strategy sampled a maximum-length sequence uniformly without replacement from the poisoning pool. The boundary strategy assumed access to the claimant score, retained candidates accepted by the initial threshold, and ranked them by the smallest non-negative initial margin \(s-\tau_{u,0}\). The first candidates in this ranking formed the maximum-length sequence. This is a score-access strong benchmark: it does not require model internals or gradients, but it is not a binary-feedback-only attack. Budgets \(K\in\{0,1,2,4,8\}\) were nested prefixes of the selected maximum-length sequence. Thus, \(K\) counts selected poisoning attempts presented to the adaptive system. Candidate discovery, reconnaissance, and screening cost were not recorded in \(K\), and total query cost was not estimated. All compared methods received the same poisoning sequence and held-out probes within an eligible victim/repeat path.

| Capability or assumption | Boundary attacker | Random attacker | Deployment implication |
|---|---|---|---|
| Authentication decision observable | Yes | Yes | Both assume that an attempt can be associated with an access decision |
| Claimant score/confidence available | Yes, assumed for selection | Not required for selection | Boundary results apply directly only when score access or equivalent ranking information is available |
| Candidate pool | Held-out test impostor pool assigned before selection | Same type of pool | The experiment does not model how a real attacker acquires the complete pool |
| Candidate ranking | Initial non-negative margin | Uniform random order | Boundary selection is stronger and more informed |
| Reconnaissance/screening counted in \(K\) | No | No separate screening | \(K=8\) must not be read as an eight-query black-box attack |
| Binary-feedback-only search demonstrated | No | Random selection needs no score ranking | Practical score-free boundary search remains untested |
| Model internals, gradients, labels | Not used | Not used | The benchmark is score-informed, not automatically white-box |
| Replay, sensor injection, OS compromise | Excluded | Excluded | Results concern only the online profile-update surface |

Blind EMA incorporated every accepted malicious observation through its ordinary update rule. Frozen never updated, and Oracle EMA blocked known-malicious updates. After the \(K\) poisoning attempts, each state was frozen. Post-poison attack success rate (ASR) was the proportion of held-out impostor probes accepted by that frozen state. Post-poison false rejection rate (FRR) was the proportion of held-out genuine test observations rejected. False acceptance rate (FAR) was the proportion of impostor observations accepted; in the held-out poisoning evaluation, ASR was the attack-context FAR. Half total error rate was \(\mathrm{HTER}=(\mathrm{FAR}+\mathrm{FRR})/2\). Malicious update rate (MUR) was the number of malicious attempts incorporated into the profile divided by the number presented. Profile mean, standard deviation, and threshold displacement were retained in native score units.

The HMOG attack used five folds, 100 Monte Carlo repeats, master seed 4242, and the fixed 50% group-disjoint probe allocation. A common paired cohort required at least eight initially accepted boundary candidates; when this condition failed, the corresponding random and boundary path was excluded. Of 50,000 possible fold-victim-repeat paths, 49,889 were eligible and 111 were excluded; all 100 victims contributed at least one eligible path in every fold. Consequently, HMOG \(K=0\) and random summaries also use this common maximum-budget-feasible cohort. Boundary estimates are conditional on sufficient initially accepted candidates, which can induce feasibility selection. Repeats were averaged within victim before fold-level macro-aggregation.

## 3.5. Guarded Poisoning Experiment

The Guarded poisoning experiment compared Frozen, Blind EMA, Oracle EMA, and Guarded EMA while holding the attack-v2 protocol fixed. Guarded values \(\lambda\in\{0.00,0.25,0.50,0.75,1.00\}\) formed an exploratory sweep. The \(\lambda=0\) implementation was required to reproduce Blind EMA exactly and was checked at the granular output level.

The experiment reused the same five folds, cached LSTM scores, poison/probe partitions, nested budgets, attack sequences, 100-repeat structure, and seed as attack v2. Post-poison ASR, FRR, HTER, MUR, and profile displacement were measured before any genuine replay. Genuine update rate (GUR) was measured separately by replaying the chronological genuine test stream on a copy of each post-poison state. GUR was the number of genuine observations incorporated divided by the number presented in that replay. Because the copied replay could not alter the already measured post-poison endpoints, poisoning-experiment GUR measured update availability, not longitudinal drift-adaptation utility.

## 3.6. Operating-Point Sensitivity

The operating-point experiment was a prospectively specified sensitivity analysis on previously inspected score caches. It did not retrain either score generator or regenerate scores. For both HMOG and McGill, it compared the reference condition with nominal pooled calibration-FAR constraints of 5% and 1%. The HMOG reference threshold was the canonical approximate-EER threshold; the McGill reference threshold minimized pooled Day-1 HTER with the original higher-threshold tie break. HMOG calibration used only its original validation partition, and McGill calibration used only the original Day-1 enrollment/calibration partition. Test and Day-2 scores were never used to select a threshold.

For nominal target \(\beta\), let \(I\) denote all calibration impostor observations for one claimant profile and \(\tau_{\mathrm{ref}}\) its reference threshold. Candidate thresholds were \(\tau_{\mathrm{ref}}\) together with \(\operatorname{nextafter}(v,+\infty)\) for each unique float64 score \(v\in I\), restricted to finite values no lower than \(\tau_{\mathrm{ref}}\). The smallest candidate satisfying \(\operatorname{mean}(I\geq\tau)\leq\beta\) was selected; if the reference threshold already satisfied the constraint, it was retained. The `score >= threshold` decision rule meant that tied impostor scores crossed the boundary together. Calibration FAR and FRR used pooled observation weights. The targets were calibration constraints, not held-out FAR guarantees or deployment standards.

Enrollment mean \(\mu_0\) and second moment were unchanged. For every recalibrated \(\tau_0\), canonical initialization recomputed

\[
k=\frac{\mu_0-\tau_0}{\sigma_0}.
\]

Negative \(k\) was retained. EMA \(\alpha=0.05\), Guarded \(\lambda=0.25\), the canonical sigma floor, and dataset-specific derived-threshold behavior remained fixed. Consequently, the experiment did not isolate a change in \(\tau_0\) while holding the remaining policy and attack paths fixed: recalibration also changed claimant-specific \(k\), boundary-candidate composition, and condition-specific feasibility.

Pool assignments, master attack seed 4242, 100 repeats, budgets, and split semantics were unchanged across operating points. Random orders were sampled once per path without reference to a threshold. Boundary candidates were reselected within each condition by \(s\geq\tau_0\) and ranked by non-negative initial margin, with index as the deterministic tie break. Within a condition, Frozen, Blind EMA, and Guarded EMA received the same poisoning sequence, order, and held-out probes; profile state was frozen after poisoning before future ASR and FRR evaluation. Each boundary curve used its condition-specific common \(K=8\)-feasible cohort. Random summaries used every structurally valid planned path, while reproduction of the historical reference reports retained the legacy cohort definitions. These cohorts were not pooled or treated as paired across operating points.

The sensitivity primary contrast was HMOG nominal 1%, boundary \(K=8\), Blind EMA minus Frozen post-poison ASR; Guarded EMA minus Blind EMA on the same paths was the key secondary contrast. This sensitivity primary did not replace the historical reference reporting contrast. HMOG repeats were averaged within victim and fold and fold means within victim; McGill repeats were averaged within victim. Percentile intervals used 10,000 paired victim-bootstrap draws. A secondary product-weight victim-by-impostor-source bootstrap was available only for HMOG nominal 1%, boundary \(K=8\); it did not include classifier-training or broader population uncertainty.

## 3.7. Clean Temporal Drift Protocol

Clean adaptation was evaluated at synthetic sensitivity levels \(D\in\{0,1,2\}\). The transformation inherited from Paper 2 was applied after model training in standardized 36-dimensional feature space. For each fold, a direction was sampled from a standard multivariate normal distribution using seed \(42+f\), normalized to unit length, and linearly ramped over each subject's chronological test sequence to final Euclidean magnitude \(D\). The same displacement was added to all 10 time steps of a sequence. The \(D\) levels were not empirically calibrated to natural behavioral change. This procedure was a controlled synthetic feature-shift sensitivity analysis, not natural behavioral drift.

Two score scenarios were evaluated. In the global scenario, both claimant and impostor observations used the score cache corresponding to the same \(D\), matching the scope of the Paper 2 transformation. In the claimant-only scenario, genuine adaptation observations and genuine checkpoints used scores from the selected \(D\), whereas impostor probes used \(D=0\) scores. Claimant-only \(D=2\) was the primary mechanistic display because it changed the claimant distribution without simultaneously moving the impostor distribution.

Test sessions were ordered chronologically for each claimant and fold. Within each complete session pair, the sequence beginning at within=0 was used only as the adaptation candidate; the disjoint sequence beginning at within=10 was used only as a genuine checkpoint. Checkpoints never updated the profile. Impostor FAR was measured at the same profile state from other identities at the matched session number and within=10, then macro-averaged across impostor source identities. At least four complete session pairs were required. Early FRR/FAR used the first two checkpoints and late FRR/FAR used the last two; a middle checkpoint, when present, was retained for trajectories but not for early/late summaries. Late HTER used temporally matched late FRR and late FAR.

The clean-stream outputs included early and late FRR/FAR, late HTER, GUR, authentication and update counts, and changes in profile mean, standard deviation, and threshold. Adaptation gain was defined as Frozen late FRR minus method late FRR, so a positive value represented lower late FRR than Frozen.

## 3.8. Oracle-All-Genuine Diagnostic

Oracle-all-genuine used the same chronological adaptation candidates, evaluation-only checkpoints, impostor probes, and canonical EMA moment equations as the deployable methods. It made and recorded the ordinary authentication decision for every genuine adaptation candidate, but ground-truth genuineness authorized an update regardless of whether that decision was accept or reject. Genuine checkpoints and all impostor probes remained non-updating. Oracle-all therefore estimated the behavior of score-level EMA when accepted-only feedback censoring was removed; it was not a deployable authentication method.

Oracle-all was evaluated in both drift scenarios at \(D=0,1,2\). In addition to aggregate late FRR, late FAR, and HTER, the run retained checkpoint-level candidate scores, decisions, update events, profile moments, and thresholds for trajectory analysis.

## 3.9. Supporting Recovery and State Probes

TQ-EMA v1 introduced an isolated route through which rejected near-boundary observations could provide temporally consistent recovery evidence without receiving access. A confirmed batch from distinct sessions used its median score as a robust target for a bounded joint-moment proposal; the authentication threshold was then recomputed from the resulting internally consistent profile state. The trusted path retained Guarded \(\lambda=0.25\) and used the effective conjunction defined above. Configuration selection was nested within each outer fold and used validation data only.

The TQ-EMA v1 primary endpoint was Frozen late FRR minus TQ-EMA late FRR in claimant-only \(D=2\). The recovery criterion required the lower bound of the paired 95% subject-bootstrap interval to exceed zero, mean late-FAR increase to be no greater than +1.0 percentage point, mean HTER degradation to be no greater than +0.5 point, and the conclusion to be preserved in the 99-subject complete-five-fold cohort. The +1.0-point FAR limit was an experiment-specific constraint, not a universal standard. TQ-EMA v1 was not combined with poisoning.

TQ-EMA v2 changed only recovery-episode balancing: after confirmed downward evidence, trusted proposals that would increase either the profile mean or derived threshold were temporarily suppressed. The Adaptive Quantile Profile instead replaced EMA moments with a fixed q20/q50 exponentially weighted score representation and compared accepted-only with Oracle-all update eligibility. Both branches used validation-only, fail-closed selection: outer scores would remain unopened if any fold lacked a configuration satisfying the fixed FAR and HTER constraints. Complete state machines, parameter grids, quantile equations, initialization, and validation rules are provided in Supplementary Methods; observed stopping outcomes are reported in Results and Supplementary Results.

## 3.10. Statistical Analysis

All rate differences were reported in percentage points. The historical paper-level security reporting contrast remained HMOG reference boundary \(K=8\), Blind EMA minus Frozen post-poison ASR. The prospectively specified sensitivity primary was HMOG nominal 1%, boundary \(K=8\), Blind EMA minus Frozen post-poison ASR. The latter did not retroactively replace or confirm the historical reference contrast. The primary adaptation reporting contrast was Guarded versus Frozen late FRR in claimant-only HMOG \(D=2\), reported equivalently as Frozen-minus-Guarded late-FRR gain. These labels define the reporting focus and do not make the sequential HMOG development confirmatory. The TQ-EMA v1 endpoint retained its separate branch-specific status. Other budgets, random attacks, lambda values, drift levels, and stopped branches were secondary or exploratory; no post-hoc multiplicity correction was introduced.

For the historical reference contrast, exact Blind and Frozen outcomes were recovered from the retained frozen subject-repeat output whose fold summaries, configuration, manifest, and exclusions matched the committed authoritative package byte-for-byte. Within every eligible fold-victim-repeat path, the paired post-ASR difference was calculated. Repeats were averaged within fold and victim, and the resulting five fold-level means were averaged within each victim. The 100 victim effects were resampled with replacement using 10,000 percentile-bootstrap draws and seed 4242. This analysis used only retained outcomes. A historical victim-by-impostor-source bootstrap was infeasible because source contributions were not retained in that granular output.

The operating-point package used the same hierarchical victim aggregation but generated key-specific deterministic random streams from master bootstrap seed 20261004. Its reference point estimate and victim effects reproduced the historical analysis to floating-point tolerance; its slightly different reference interval reflects Monte Carlo resampling, not a changed estimand or cohort. Source-specific probe records were retained only for the HMOG nominal-1% boundary-\(K=8\) sensitivity condition. The secondary product-weight bootstrap independently resampled observed victim and impostor-source identities. It did not cover other operating points, McGill, model training, or population uncertainty.

In the remaining HMOG poisoning summaries, Monte Carlo repeats were averaged within subject and subjects were macro-averaged within fold. Across-fold means, standard deviations, standard errors, and \(t\)-intervals were descriptive protocol-stability summaries only. The five outer folds had overlapping fitting partitions, and the repeated attack paths were Monte Carlo replicates; neither was treated as a set of independent observations for confirmatory inference.

For clean drift, each subject was first averaged across its available folds. Paired subject effects relative to Frozen were then resampled with replacement using 10,000 percentile-bootstrap draws to obtain 95% confidence intervals. The primary cohort retained every subject with available paired data. A sensitivity analysis used the 99 subjects with complete data in all five folds. For TQ-EMA v1 late FAR, a secondary two-way bootstrap independently resampled victim identities and impostor-source identities. No new null-hypothesis tests or post-result multiplicity correction were introduced; secondary contrasts and parameter sweeps remained exploratory.

The McGill analysis averaged attack repeats within subject and used paired subject effects with 10,000 percentile-bootstrap draws. Eligibility and denominators were reported for each contrast. There were no folds in the McGill analysis.

## 3.11. External Replication on McGill Gait

whuGAIT Dataset #2 was examined before the external protocol was frozen \cite{Zou2020WhuGait}. Its processed archive contained shuffled train/test signal matrices and subject labels but did not preserve day, session, timestamp, or original-order fields. File order could therefore not support the planned temporal replication without constructing an artificial chronology. The dataset was not used for the unified poisoning-and-temporal replication.

The external protocol instead used the official McGill Gait archive \cite{Frank2010McGillGaitDataset}, which contained raw timestamped recordings from 20 subjects (w001–w020) on two collection days. Day 1 was used for model development, normalization, enrollment, and threshold calibration; Day 2 was held out for the attack and temporal analyses. McGill lacked gyroscope data, so the replication used only accel_x, accel_y, accel_z, and the supplied gravity-adjusted accelerometer magnitude. Magnetometer, orientation, and temperature channels were excluded. The recorded median sample interval was 40 ms (approximately 25 Hz); no interpolation was applied. Inputs were non-overlapping 128-sample windows (approximately 5.12 s) with shape 128 × 4.

One pooled per-channel z-score transform was fitted only to Day-1 training windows. Within each subject, Day-1 windows were split chronologically into 60% model fitting, 20% early-stopping validation, and 20% enrollment/calibration using floor-valued cut points. The fixed classifier was a one-layer unidirectional LSTM with input size 4, hidden size 64, final-hidden-state classification, and a 20-class linear head. Training used class-weighted cross-entropy, Adam with learning rate 0.001 and weight decay 0.0001, batch size 128, at most 30 epochs, and validation-loss early stopping with patience 5. The claimant score was the corresponding softmax probability.

The McGill EMA used \(\alpha=0.05\) and standard-deviation floor \(10^{-4}\). The initial threshold was calibrated on Day-1 enrollment scores by minimum HTER, with exact ties resolved toward the higher threshold; \(k\) was then fixed from the enrollment mean, standard deviation, and threshold. Guarded EMA used \(\lambda=0.25\), transferred unchanged from the HMOG reporting comparison. No McGill lambda sweep or post-Day-2 parameter tuning was permitted.

The poisoning replication used random and score-informed boundary attacks, nested \(K\in\{0,1,2,4,8\}\), 100 repeats, and a source-identity-disjoint poison/probe split as close to 50/50 as possible. Only the first temporal half of poison identities' Day-2 windows was eligible for poisoning, and only the second half of probe identities' Day-2 windows was used for held-out ASR. States were frozen before probe and genuine evaluation. The poisoning comparison included Frozen, Blind EMA, and Guarded EMA. Random selection retained all 2,000 victim-repeat paths across 20 victims. Boundary \(K=8\) retained 1,456 paths across 18 victims and excluded 544 paths that lacked eight initially accepted candidates; boundary \(K=0\) used the same maximum-budget-feasible cohort.

For the temporal analysis, 160 approximately equally spaced Day-2 windows were selected per subject and paired into 80 chronological units, each containing an adaptation window followed by a disjoint evaluation-only checkpoint. The first and last 20 units defined early and late endpoints. The temporal comparison included Frozen, Guarded EMA, and Oracle-all-genuine; matched impostor checkpoints never updated any profile.

Before any Day-2 score was loaded, the run was required to stop if training became non-finite, fewer than 16 classes occurred in Day-1 validation, validation top-1 accuracy was below 20%, or protocol-invariant tests and a synthetic smoke run did not pass. After this gate, all preprocessing, architecture, profile, attack, exclusion, and analysis choices remained fixed. These dataset-specific preprocessing and classifier choices were specified before training; the HMOG Guarded rule, attack budgets, repeat count, and update equations were not retuned to McGill.

## 3.12. Reproducibility and Protocol Freezing

The HMOG method freeze is identified by tag paper3-method-freeze-2026-10-02 at commit 476cf91; the committed external result package is identified by tag paper3-external-mcgill-v1-2026-10-03 at commit 06feb48; and the operating-point package is identified by tag paper3-operating-point-sensitivity-v1-2026-10-04 at commit 77f11de. Machine-readable configurations record seeds, folds, attack budgets, grids, stopping rules, statistical units, and output definitions. Run manifests record source and cache hashes, execution environment, run status, and whether outer test data were loaded. The score models were fixed, and the sensitivity analysis reused previously inspected caches. The final HMOG aggregator and the Round-2 manuscript integration were read-only with respect to experimental outcomes: neither performed retraining, rescoring, adaptation, tuning, nor new inference.

SHA-256 hashes were retained for consumed score caches, source files, protocol files, raw external archives, and generated outputs. The external McGill archive hash was 0e2da09c2d10fb5658c79d362e9e043a2f2822715723238b30cbebd2e7b425d9, and the locked McGill score-cache hash was 3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b. Deterministic reruns reproduced the retained McGill CSV, Markdown, and PNG outputs byte-for-byte; PDF hash changes were confined to embedded creation metadata.

Unit and protocol-invariant tests covered no-update behavior, oracle/frozen equivalence in malicious-only streams, nested budgets, split disjointness, update gating, bounded transitions, enrollment anchors, recovery isolation, state-machine behavior, and deterministic analysis. The recorded invariant suites and smoke checks completed successfully. The TQ-EMA v2 and Adaptive Quantile manifests record validation failure and outer_test_loaded=false; these stopped branches were not reopened during final aggregation.
