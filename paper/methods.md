# 3. Methods

## 3.1. Study Design and Experimental Overview

This study examined two coupled risks in score-level online adaptation for behavioral-biometric continuous authentication: profile poisoning by accepted impostor observations and feedback censoring when rejected genuine observations are excluded from adaptation. The study was organized as a sequence of mechanism-focused experiments rather than as a general classifier benchmark. HMOG was the primary mechanistic dataset \cite{Sitova2016HMOG}. A fixed LSTM score generator inherited from Paper 2 \cite{Serbin2026AdaptiveLSTM} was used to evaluate (i) held-out poisoning of Blind EMA, (ii) confidence-gated update authorization, (iii) adaptation under synthetic temporal feature drift, and (iv) diagnostic and recovery controls. A separately locked two-day McGill Gait protocol examined whether the principal poisoning, defense, and feedback-censoring patterns transferred to an independent dataset with natural day separation \cite{Frank2010McGillGaitDataset}.

The experimental branches were developed sequentially. Each branch specified its data access, parameter-selection rule, endpoints, and stopping rule before its corresponding evaluation. TQ-EMA v2 and the Adaptive Quantile Profile used fail-closed validation: if any outer fold lacked a configuration satisfying the fixed validation constraints, outer test scores were not loaded. HMOG method development was frozen under Git tag paper3-method-freeze-2026-10-02; the external replication was frozen under paper3-external-mcgill-v1-2026-10-03.

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

Frozen retained \(\tau_{u,0}\) and never changed profile state. Blind EMA used \(\alpha=0.05\) and, after an accepted observation, updated

\[
\mu_{u,t+1}=(1-\alpha)\mu_{u,t}+\alpha s_t,
\qquad
q_{u,t+1}=(1-\alpha)q_{u,t}+\alpha s_t^2.
\]

Rejected observations did not update either moment. This rule was label-blind: an accepted genuine or impostor observation was processed identically.

Guarded EMA separated access authentication from update authorization. Access continued to depend only on \(s_t\geq\tau_{u,t}\). For an authenticated observation, the update threshold was

\[
\tau^{\mathrm{update}}_{u,t}
=\tau_{u,t}+\lambda\left(\mu_{u,0}-\tau_{u,t}\right),
\]

and the profile was updated only if \(s_t\geq\tau^{\mathrm{update}}_{u,t}\). Thus an observation could be accepted for access but withheld from learning. The main carried-forward comparison used \(\lambda=0.25\); this value was an exploratory carry-forward from the HMOG poisoning sweep and was not treated as universally optimal.

Two oracle controls were kept distinct. In the malicious-only poisoning experiment, Oracle EMA made the same authentication decisions as the other methods but blocked all known-impostor profile updates; with no genuine adaptation observations in that phase, it was a contamination control expected to remain equal to Frozen. In the clean-drift experiment, Oracle-all-genuine applied the canonical EMA update to every ground-truth genuine adaptation candidate, including rejected candidates. Oracle-all used labels only to determine update eligibility and was a non-deployable diagnostic control.

## 3.4. Poisoning Threat Model

The attacker sought to modify the victim's online score profile so that future, previously unused impostor observations would be accepted more often. For each fold, victim, and Monte Carlo repeat, test-set impostor samples were partitioned before attack selection. Whole (source identity, session) groups were assigned to either a poisoning pool or a held-out probe pool, with an approximately 50% probe allocation. No source-session group crossed the two pools, although the split was not necessarily source-identity-disjoint.

Two attack strategies were evaluated. The random strategy sampled a maximum-length sequence uniformly without replacement from the poisoning pool. The boundary strategy retained candidates accepted by the initial threshold and ranked them by the smallest non-negative initial margin \(s-\tau_{u,0}\); the first candidates in this ranking formed the maximum-length sequence. Boundary selection was therefore a score-informed strong benchmark rather than a binary-feedback-only attack. Budgets \(K\in\{0,1,2,4,8\}\) were nested prefixes of the same maximum-length sequence. All compared methods received the same poisoning sequence and held-out probes within an eligible victim/repeat path.

Blind EMA incorporated every accepted malicious observation through its ordinary update rule. Frozen never updated, and Oracle EMA blocked known-malicious updates. After the \(K\) poisoning attempts, each state was frozen. Post-poison attack success rate (ASR) was the proportion of held-out impostor probes accepted by that frozen state. Post-poison false rejection rate (FRR) was the proportion of held-out genuine test observations rejected. False acceptance rate (FAR) was the proportion of impostor observations accepted; in the held-out poisoning evaluation, ASR was the attack-context FAR. Half total error rate was \(\mathrm{HTER}=(\mathrm{FAR}+\mathrm{FRR})/2\). Malicious update rate (MUR) was the number of malicious attempts incorporated into the profile divided by the number presented. Profile mean, standard deviation, and threshold displacement were retained in native score units.

The HMOG attack used five folds, 100 Monte Carlo repeats, master seed 4242, and the fixed 50% group-disjoint probe allocation. Repeats were averaged within victim before fold-level macro-aggregation.

## 3.5. Guarded Poisoning Experiment

The Guarded poisoning experiment compared Frozen, Blind EMA, Oracle EMA, and Guarded EMA while holding the attack-v2 protocol fixed. Guarded values \(\lambda\in\{0.00,0.25,0.50,0.75,1.00\}\) formed an exploratory sweep. The \(\lambda=0\) implementation was required to reproduce Blind EMA exactly and was checked at the granular output level.

The experiment reused the same five folds, cached LSTM scores, poison/probe partitions, nested budgets, attack sequences, 100-repeat structure, and seed as attack v2. Post-poison ASR, FRR, HTER, MUR, and profile displacement were measured before any genuine replay. Genuine update rate (GUR) was measured separately by replaying the chronological genuine test stream on a copy of each post-poison state. GUR was the number of genuine observations incorporated divided by the number presented in that replay. Because the copied replay could not alter the already measured post-poison endpoints, poisoning-experiment GUR measured update availability, not longitudinal drift-adaptation utility.

## 3.6. Clean Temporal Drift Protocol

Clean adaptation was evaluated at synthetic drift magnitudes \(D\in\{0,1,2\}\). The transformation inherited from Paper 2 was applied after model training in standardized 36-dimensional feature space. For each fold, a direction was sampled from a standard multivariate normal distribution using seed \(42+f\), normalized to unit length, and linearly ramped over each subject's chronological test sequence to final Euclidean magnitude \(D\). The same displacement was added to all 10 time steps of a sequence. This procedure was a synthetic feature-shift sensitivity analysis, not natural behavioral drift.

Two score scenarios were evaluated. In the global scenario, both claimant and impostor observations used the score cache corresponding to the same \(D\), matching the scope of the Paper 2 transformation. In the claimant-only scenario, genuine adaptation observations and genuine checkpoints used scores from the selected \(D\), whereas impostor probes used \(D=0\) scores. Claimant-only \(D=2\) was the primary mechanistic display because it changed the claimant distribution without simultaneously moving the impostor distribution.

Test sessions were ordered chronologically for each claimant and fold. Within each complete session pair, the sequence beginning at within=0 was used only as the adaptation candidate; the disjoint sequence beginning at within=10 was used only as a genuine checkpoint. Checkpoints never updated the profile. Impostor FAR was measured at the same profile state from other identities at the matched session number and within=10, then macro-averaged across impostor source identities. At least four complete session pairs were required. Early FRR/FAR used the first two checkpoints and late FRR/FAR used the last two; a middle checkpoint, when present, was retained for trajectories but not for early/late summaries. Late HTER used temporally matched late FRR and late FAR.

The clean-stream outputs included early and late FRR/FAR, late HTER, GUR, authentication and update counts, and changes in profile mean, standard deviation, and threshold. Adaptation gain was defined as Frozen late FRR minus method late FRR, so a positive value represented lower late FRR than Frozen.

## 3.7. Oracle-All-Genuine Diagnostic

Oracle-all-genuine used the same chronological adaptation candidates, evaluation-only checkpoints, impostor probes, and canonical EMA moment equations as the deployable methods. It made and recorded the ordinary authentication decision for every genuine adaptation candidate, but ground-truth genuineness authorized an update regardless of whether that decision was accept or reject. Genuine checkpoints and all impostor probes remained non-updating. Oracle-all therefore estimated the behavior of score-level EMA when accepted-only feedback censoring was removed; it was not a deployable authentication method.

Oracle-all was evaluated in both drift scenarios at \(D=0,1,2\). In addition to aggregate late FRR, late FAR, and HTER, the run retained checkpoint-level candidate scores, decisions, update events, profile moments, and thresholds for trajectory analysis.

## 3.8. TQ-EMA v1

TQ-EMA v1 added an isolated recovery path while retaining the Guarded trusted path at \(\lambda=0.25\). Production state contained the EMA mean, second moment, derived standard deviation, and derived authentication threshold. Quarantine state contained only candidate scores, distinct session identifiers, a downward-shift direction, and age. Resetting quarantine did not alter production state.

For each session-level adaptation observation, the state transition was:

1. If \(s\geq\tau^{\mathrm{update}}\), access was granted and a bounded canonical EMA proposal was considered.
2. If \(\tau^{\mathrm{auth}}\leq s<\tau^{\mathrm{update}}\), access was granted but the profile was not updated.
3. If \(\tau^{\mathrm{auth}}-b\leq s<\tau^{\mathrm{auth}}\), access was denied and the observation was placed only in recovery quarantine.
4. If \(s<\tau^{\mathrm{auth}}-b\), access was denied, the observation was discarded, and quarantine was reset.

Recovery required \(m\) consecutive candidates from distinct sessions. Every candidate had to be below the production mean recorded when the quarantine run began, and the batch range could not exceed \(r\). Any intervening non-candidate reset the run. A confirmed batch used the median score as a robust target and proposed a small joint update of the first and second moments. Standard deviation and threshold were then recomputed; the threshold was never edited independently. Accepted trusted and recovery transitions had to satisfy \(|\Delta\mu|\leq c_\mu\), \(|\Delta\tau|\leq c_\tau\), and the enrollment anchor \(\tau\geq\tau_{\mathrm{enroll}}-A\). A recovery proposal that did not lower the derived threshold was rejected.

Dimensional controls were scaled by the fixed enrollment standard deviation. The validation grid was \(b/\sigma_{\mathrm{enroll}}\in\{0.25,0.50,0.75\}\), \(m\in\{2,3\}\), recovery rate \(\alpha_{\mathrm{recovery}}\in\{0.025,0.050\}\), and \(A/\sigma_{\mathrm{enroll}}\in\{0.10,0.25\}\). Fixed controls were \(r=0.50\sigma_{\mathrm{enroll}}\), \(c_\mu=0.10\sigma_{\mathrm{enroll}}\), \(c_\tau=0.05\sigma_{\mathrm{enroll}}\), trusted-path \(\lambda=0.25\), and trusted-path \(\alpha=0.05\).

Selection was nested within each outer fold and used validation data only. The first two complete chronological validation sessions initialized and calibrated the inner profile; the remaining sessions formed the tuning stream. Claimant validation scores used the independently generated \(D=2\) cache and impostor checkpoints used \(D=0\). Among configurations with subject-macro late-FAR change no greater than +1.0 percentage point relative to Frozen, the configuration with the largest late-FRR gain was selected, with conservative tie-breaking. The +1.0-point limit was an experiment-specific security constraint, not a universal FAR standard.

The primary endpoint was Frozen late FRR minus TQ-EMA late FRR in claimant-only \(D=2\). The recovery criterion required the lower bound of the paired 95% subject-bootstrap interval to exceed zero, mean late-FAR increase to be no greater than +1.0 point, mean HTER degradation to be no greater than +0.5 point, and the conclusion to be preserved in the complete-five-fold sensitivity cohort. TQ-EMA v1 was a separately frozen protocol branch and was not mixed with poisoning in this experiment.

## 3.9. TQ-EMA v2

TQ-EMA v2 changed one controller property relative to v1. Confirmation of a valid downward recovery batch entered a RECOVERY_DOWN episode after first applying the same bounded median-target recovery proposal. During the episode, authentication and access rules were unchanged. Before a trusted update, the controller previewed the canonical EMA proposal; the update was skipped if it increased either the profile mean or the derived authentication threshold, and otherwise the ordinary bounded transition was allowed. The episode remained active for the next three distinct session-level adaptation observations and was refreshed by a new confirmed recovery batch. Quarantine reset did not terminate an active episode.

The v1 grid, caps, anchor, and trusted-path parameters were retained. Fold-specific selection used only a synthetic validation replay: clean \(D=0\) validation scores initialized and calibrated the profile, claimant observations used independently scored \(D=2\) validation transformations, and impostor checkpoints used \(D=0\). A configuration was feasible only when late-FAR increase was at most +1.0 percentage point and HTER degradation was at most +0.5 point. Selection failed closed if any fold lacked a feasible configuration. The gate failed in fold 4; consequently, outer test scores were not loaded and no outer TQ-EMA v2 estimate was produced.

## 3.10. Adaptive Quantile Profile

The Adaptive Quantile Profile replaced the EMA moments with a discrete exponentially weighted empirical score distribution. Enrollment observations started with equal weights. For normalized non-negative weights, \(Q_p\) was the smallest observed score whose sorted cumulative weight was at least \(p\), without interpolation. The state retained \(q_{20}=Q_{0.20}\) and \(q_{50}=Q_{0.50}\). At enrollment,

\[
c=\frac{q_{50,0}-\tau_0}{q_{50,0}-q_{20,0}},
\qquad
\tau_t=q_{50,t}-c\left(q_{50,t}-q_{20,t}\right).
\]

The value of \(c\) was fixed and not clipped, making the initial quantile threshold equal to the validation-calibrated threshold within floating-point tolerance. A path was invalid if \(q_{50,0}-q_{20,0}<10^{-8}\). No fallback estimator or interpolation was introduced.

For an authorized observation \(s_t\), existing weights were multiplied by \(\rho\), \(s_t\) was appended with weight \(1-\rho\), weights were renormalized, and \(q_{20}\), \(q_{50}\), and the derived threshold were recomputed. Accepted-only Quantile updated only after authentication acceptance. Oracle-all Quantile made the same authentication decision but updated from every ground-truth genuine adaptation candidate; it was diagnostic and non-deployable.

The only tuned parameter was \(\rho\in\{0.80,0.90,0.95\}\); the two quantile levels were fixed. Validation used the same claimant-only synthetic replay structure as TQ-EMA v2. Accepted-only Quantile alone determined feasibility and selection, using the +1.0-point FAR and +0.5-point HTER constraints. If any fold lacked a feasible \(\rho\), outer test scores were not to be loaded. No \(\rho\) was feasible in any fold, and the branch therefore stopped at validation with outer_test_loaded=false.

## 3.11. Statistical Analysis

All rate differences were reported in percentage points. In the HMOG poisoning experiments, Monte Carlo repeats were averaged within subject and subjects were macro-averaged within fold. Across-fold means, standard deviations, standard errors, and \(t\)-intervals were descriptive protocol-stability summaries only. The five outer folds had overlapping fitting partitions, and the repeated attack paths were Monte Carlo replicates; neither was treated as a set of independent observations for confirmatory inference.

For clean drift, each subject was first averaged across its available folds. Paired subject effects relative to Frozen were then resampled with replacement using 10,000 percentile-bootstrap draws to obtain 95% confidence intervals. The primary cohort retained every subject with available paired data. A sensitivity analysis used the 99 subjects with complete data in all five folds. For TQ-EMA v1 late FAR, a secondary two-way bootstrap independently resampled victim identities and impostor-source identities. No new null-hypothesis tests or post-result multiplicity correction were introduced; secondary contrasts and parameter sweeps remained exploratory.

The McGill analysis averaged attack repeats within subject and used paired subject effects with 10,000 percentile-bootstrap draws. Eligibility and denominators were reported for each contrast. There were no folds in the McGill analysis.

## 3.12. External Replication on McGill Gait

whuGAIT Dataset #2 was examined before the external protocol was frozen \cite{Zou2020WhuGait}. Its processed archive contained shuffled train/test signal matrices and subject labels but did not preserve day, session, timestamp, or original-order fields. File order could therefore not support the planned temporal replication without constructing an artificial chronology. The dataset was not used for the unified poisoning-and-temporal replication.

The external protocol instead used the official McGill Gait archive \cite{Frank2010McGillGaitDataset}, which contained raw timestamped recordings from 20 subjects (w001–w020) on two collection days. Day 1 was used for model development, normalization, enrollment, and threshold calibration; Day 2 was held out for the attack and temporal analyses. McGill lacked gyroscope data, so the replication used only accel_x, accel_y, accel_z, and the supplied gravity-adjusted accelerometer magnitude. Magnetometer, orientation, and temperature channels were excluded. The recorded median sample interval was 40 ms (approximately 25 Hz); no interpolation was applied. Inputs were non-overlapping 128-sample windows (approximately 5.12 s) with shape 128 × 4.

One pooled per-channel z-score transform was fitted only to Day-1 training windows. Within each subject, Day-1 windows were split chronologically into 60% model fitting, 20% early-stopping validation, and 20% enrollment/calibration using floor-valued cut points. The fixed classifier was a one-layer unidirectional LSTM with input size 4, hidden size 64, final-hidden-state classification, and a 20-class linear head. Training used class-weighted cross-entropy, Adam with learning rate 0.001 and weight decay 0.0001, batch size 128, at most 30 epochs, and validation-loss early stopping with patience 5. The claimant score was the corresponding softmax probability.

The McGill EMA used \(\alpha=0.05\) and standard-deviation floor \(10^{-4}\). The initial threshold was calibrated on Day-1 enrollment scores by minimum HTER, with exact ties resolved toward the higher threshold; \(k\) was then fixed from the enrollment mean, standard deviation, and threshold. Guarded EMA used \(\lambda=0.25\), transferred unchanged from the HMOG reporting comparison. No McGill lambda sweep or post-Day-2 parameter tuning was permitted.

The poisoning replication used random and score-informed boundary attacks, nested \(K\in\{0,1,2,4,8\}\), 100 repeats, and a source-identity-disjoint poison/probe split as close to 50/50 as possible. Only the first temporal half of poison identities' Day-2 windows was eligible for poisoning, and only the second half of probe identities' Day-2 windows was used for held-out ASR. States were frozen before probe and genuine evaluation. The poisoning comparison included Frozen, Blind EMA, and Guarded EMA.

For the temporal analysis, 160 approximately equally spaced Day-2 windows were selected per subject and paired into 80 chronological units, each containing an adaptation window followed by a disjoint evaluation-only checkpoint. The first and last 20 units defined early and late endpoints. The temporal comparison included Frozen, Guarded EMA, and Oracle-all-genuine; matched impostor checkpoints never updated any profile.

Before any Day-2 score was loaded, the run was required to stop if training became non-finite, fewer than 16 classes occurred in Day-1 validation, validation top-1 accuracy was below 20%, or protocol-invariant tests and a synthetic smoke run did not pass. After this gate, all preprocessing, architecture, profile, attack, exclusion, and analysis choices remained fixed. These dataset-specific preprocessing and classifier choices were specified before training; the HMOG Guarded rule, attack budgets, repeat count, and update equations were not retuned to McGill.

## 3.13. Reproducibility and Protocol Freezing

The HMOG method freeze is identified by tag paper3-method-freeze-2026-10-02 at commit 476cf91; the committed external result package is identified by tag paper3-external-mcgill-v1-2026-10-03 at commit 06feb48. Machine-readable configurations record seeds, folds, attack budgets, grids, stopping rules, statistical units, and output definitions. Run manifests record source and cache hashes, execution environment, run status, and whether outer test data were loaded. The final HMOG aggregator was read-only: it consumed frozen results and performed no retraining, rescoring, adaptation, or tuning.

SHA-256 hashes were retained for consumed score caches, source files, protocol files, raw external archives, and generated outputs. The external McGill archive hash was 0e2da09c2d10fb5658c79d362e9e043a2f2822715723238b30cbebd2e7b425d9, and the locked McGill score-cache hash was 3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b. Deterministic reruns reproduced the retained McGill CSV, Markdown, and PNG outputs byte-for-byte; PDF hash changes were confined to embedded creation metadata.

Unit and protocol-invariant tests covered no-update behavior, oracle/frozen equivalence in malicious-only streams, nested budgets, split disjointness, update gating, bounded transitions, enrollment anchors, recovery isolation, state-machine behavior, and deterministic analysis. The recorded invariant suites and smoke checks completed successfully. The TQ-EMA v2 and Adaptive Quantile manifests record validation failure and outer_test_loaded=false; these stopped branches were not reopened during final aggregation.
