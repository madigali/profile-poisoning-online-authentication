# 3. Methods

## 3.1. Study design and evidence status

The study examined score-level online adaptation through held-out poisoning and clean temporal protocols. HMOG was the primary mechanistic dataset \cite{Sitova2016HMOG}. Its fixed LSTM scores supported the Blind EMA poisoning analysis, Guarded update authorization, synthetic temporal experiments, Oracle diagnostics, and prespecified recovery probes. A separately frozen McGill Gait protocol used Day 1 for development and Day 2 for evaluation \cite{Frank2010McGillGaitDataset}. Score generators remained fixed within every method comparison.

Frozen supplied the no-update baseline. Blind EMA represented the inherited accepted-only updater. Guarded EMA retained the authentication-rule form but imposed a separate confidence condition on learning. The malicious-update-blocking Oracle and Oracle-all used labels only in explicitly diagnostic update-eligibility roles. Attack experiments presented malicious observations and then froze state before evaluation; clean temporal experiments interleaved adaptation candidates with disjoint evaluation checkpoints. These protocols were analyzed separately rather than combined into a drift-plus-attack stream.

The HMOG branches were developed sequentially on the same outer score caches. Attack and Guarded analyses are therefore exploratory mechanism evidence, and the carried-forward Guarded value \(\lambda=0.25\) was selected from an exploratory HMOG sweep. TQ-EMA v2 and the Adaptive Quantile Profile stopped at validation without loading outer outcomes. The McGill protocol transferred \(\lambda=0.25\) before Day-2 scores were accessed. Operating-point sensitivity was prospectively specified after the reference caches had already been inspected. A full chronology and evidence-status table appears in Supplementary Methods S1.

Three reporting contrasts organize the analysis. The historical security contrast is HMOG reference boundary \(K=8\), Blind minus Frozen post-poison ASR. The operating-point sensitivity primary is the corresponding HMOG nominal-1% contrast and does not replace the historical analysis. The clean temporal comparison uses Guarded versus Frozen late FRR in claimant-only \(D=2\). Oracle-all and the recovery branches have diagnostic or branch-specific roles rather than sharing one confirmatory family.

The security and temporal contrasts answer different questions. The poisoning analysis estimates whether profile updating changes acceptance of unused impostor probes after a specified malicious sequence. The clean analysis estimates whether updating changes genuine rejection at later chronological checkpoints while tracking the corresponding impostor acceptance. Neither contrast alone establishes a secure adaptive system. Interpretation therefore retains the direction of ASR or FAR, FRR, HTER, update eligibility, and state movement instead of treating one aggregate as the sole endpoint.

## 3.2. Datasets and score generation

HMOG contributed 100 enrolled identities in a closed-set, session-disjoint design; it did not test unseen-subject generalization. The canonical pipeline retained 2,392 usable sessions and 4,784 sequences. For each session, it discarded the first 500 sensor samples and retained the next 20 non-overlapping 100-sample windows from the physical accelerometer and gyroscope axes. The previous study capped retention at 20 windows to equalize session contributions and bound computation; the available source does not document a scientific rationale for the initial 500-sample offset. Six statistics per axis produced a 36-dimensional window representation, and ten adjacent windows formed a non-overlapping \(10\times36\) sequence.

The pipeline assumed HMOG's nominal 100 Hz sampling rate and did not estimate realized rate. Accelerometer and gyroscope rows were paired by acquisition order after truncation to the shorter file, without timestamp resampling. The six window statistics were mean, standard deviation, minimum, maximum, root mean square, and skewness. Two sequences were retained per usable session and did not cross session boundaries.

Five outer folds assigned sessions by \(g(r)=(r-1)\bmod5\). One group was test, the next was validation/calibration, and the remaining three were used for fitting. Every subject appeared in each partition through different sessions. A StandardScaler was fitted only on fitting sequences and then held fixed. The two-layer, 64-unit LSTM used 64 hidden units per layer, layer normalization, a 32-unit ReLU layer, dropout, and a 100-class softmax. Claimant \(u\)'s score was its probability for class \(u\). The HMOG preprocessing and model-training procedure followed our previous study \cite{Serbin2026AdaptiveLSTM}. A separate Paper 3 cache-generation run trained one model per fold under that procedure, after which the resulting per-fold scores were held fixed across all present method comparisons. Supplementary Methods S2 gives optimizer, stopping, scheduler, cache provenance, and exclusion details.

The model was trained with cross-entropy and Adam, with early stopping on the validation partition. Neither the LSTM nor the fitting-only scaler was updated during poisoning or temporal adaptation. All adaptive methods operated on the same cached scalar claimant probabilities within a fold.

McGill contained raw smartphone recordings from 20 participants on two collection days. The replication used accelerometer \(x,y,z\) and gravity-adjusted magnitude in non-overlapping 128-sample windows, approximately 5.12 s at the recorded median interval. Day 1 supplied model fitting, early-stopping validation, enrollment, normalization, and threshold calibration; Day 2 remained held out for poisoning and temporal evaluation. Within each identity, Day-1 windows were divided chronologically into 60% fitting, 20% validation, and 20% enrollment/calibration. A fitting-only per-channel normalization and one-layer 64-unit LSTM produced 20-class claimant probabilities. McGill used accelerometer-derived inputs only, whereas HMOG used accelerometer and gyroscope. Supplementary Methods S5 provides optimizer, viability-gate, and preprocessing details.

The McGill run had to pass a prespecified viability gate before Day-2 scores were loaded: finite training, at least 16 validation classes, validation top-1 accuracy of at least 20%, and successful protocol checks. This gate assessed whether the frozen classifier was usable for the planned mechanism study; it was not a performance-selection search on Day 2.

## 3.3. Profile state, authentication, and update eligibility

For claimant \(u\), enrollment or validation genuine scores initialized mean \(\mu_{u,0}\) and second raw moment \(q_{u,0}\). The canonical HMOG state was

\[
\sigma_{u,t}=\sqrt{\max(q_{u,t}-\mu_{u,t}^2,\epsilon^2)},
\qquad
\tau_{u,t}=\max(0,\mu_{u,t}-k_u\sigma_{u,t}),
\]

with \(\epsilon=10^{-4}\). The claimant-specific initial threshold \(\tau_{u,0}\) was the approximate equal-error threshold on validation scores, and

\[
k_u=\frac{\mu_{u,0}-\tau_{u,0}}{\sigma_{u,0}}
\]

made the derived threshold equal to that calibration. McGill used minimum HTER on Day-1 enrollment scores and then computed \(k_u\) from the same identity. Each method applied the common authentication rule form \(a_t=\mathbb{1}[s_t\geq\tau_{u,t}]\) to its own current state and threshold. Different update histories could therefore produce different later thresholds and decisions.

The reference thresholds served as mechanistic operating points rather than deployment targets. In particular, HMOG's validation-calibrated approximate-EER rule admitted a substantial fraction of held-out impostor observations. Frozen comparisons measure changes attributable to online state updating within that operating point and feasible cohort; they do not certify the underlying classifier or threshold for deployment.

Frozen retained its initial profile. Blind EMA updated after an accepted observation with \(\alpha=0.05\):

\[
\mu_{u,t+1}=(1-\alpha)\mu_{u,t}+\alpha s_t,
\qquad
q_{u,t+1}=(1-\alpha)q_{u,t}+\alpha s_t^2.
\]

The update was label-blind. Guarded EMA used the same access-rule form and added an update condition

\[
\tau^{\mathrm{update,raw}}_{u,t}
=\tau^{\mathrm{auth}}_{u,t}+\lambda(\mu_{u,0}-\tau^{\mathrm{auth}}_{u,t}),
\]

\[
\mathrm{update\ allowed}
=\left[s_t\geq\tau^{\mathrm{auth}}_{u,t}\right]
\land
\left[s_t\geq\tau^{\mathrm{update,raw}}_{u,t}\right].
\]

Thus

\[
\tau^{\mathrm{update,effective}}_{u,t}
=\max(\tau^{\mathrm{auth}}_{u,t},\tau^{\mathrm{update,raw}}_{u,t}),
\]

and, for the evaluated \(\lambda\geq0\), the additional margin was

\[
\lambda\max(\mu_{u,0}-\tau^{\mathrm{auth}}_{u,t},0).
\]

The gate added no restriction beyond authentication when \(\tau^{\mathrm{auth}}_{u,t}\geq\mu_{u,0}\). This equation describes the executed rule; no margin floor or clipping was added.

Guarded was evaluated at \(\lambda\in\{0,0.25,0.50,0.75,1.00\}\) in an exploratory HMOG sweep. The main comparison carried \(\lambda=0.25\) forward to clean HMOG and McGill protocols. The \(\lambda=0\) implementation was checked against Blind at granular output level. This consistency check applies to that parameter condition and does not make Guarded and Blind equivalent at other \(\lambda\) values.

Two Oracle controls had different roles. During malicious-only poisoning, the malicious-update-blocking Oracle applied the authentication rule to an unchanged profile and blocked all known-impostor updates. It therefore coincided with Frozen in that phase. Blind and Guarded could acquire different states and subsequent decisions. In clean temporal streams, Oracle-all applied the same decision-rule form to its own state but made every ground-truth genuine adaptation candidate update-eligible, including rejected candidates. Oracle-all was label-aware and non-deployable.

## 3.4. Poisoning protocol and endpoints

The protected object was the claimant's online score-profile state and its derived threshold. The attack objective was to change that state so that unused impostor probes would be accepted more often. The evaluated attacker did not modify LSTM weights, enrollment data, validation data, raw sensor files, firmware, or operating-system code. Replay, sensor injection, collusion, model extraction, and gradient attacks were outside scope.

For each HMOG fold, victim, and repeat, whole \((\mathrm{source\ identity},\mathrm{session})\) groups were assigned before attack selection to either poisoning or held-out probe pools, with approximately half reserved for probes. No source-session group crossed pools, although source identities could. Dataset identity labels were used offline to define claimant, impostor, poison, and probe sets, but were not exposed to the Blind or Guarded online updater. Random attack sequences were sampled without replacement. The boundary strategy assumed claimant-score access, retained candidates accepted at the initial threshold, and ranked them by smallest non-negative margin \(s-\tau_{u,0}\); ranking used scores and margins, not model gradients or ground-truth genuineness labels. Its budget \(K\in\{0,1,2,4,8\}\) counted nested selected attempts presented to the updater; reconnaissance, candidate screening, and total query cost were unmeasured. It is therefore a score-informed benchmark rather than a demonstrated binary-feedback attack. Ground-truth labels were exposed online only to the explicitly diagnostic Oracle controls.

Compared methods received the same poison sequence and probes within a path. After \(K\) presentations, profile state was frozen before future impostor and genuine evaluation. Post-poison attack success rate (ASR) was held-out impostor acceptance. Post-poison false rejection rate (FRR) used held-out genuine observations; \(\mathrm{HTER}=(\mathrm{ASR}+\mathrm{FRR})/2\). Malicious update rate (MUR) was the fraction of presented malicious observations incorporated. A separate genuine replay measured genuine update rate without altering the poisoning endpoints.

HMOG used five folds, 100 repeats, and a fixed approximately 50% probe allocation. Reference boundary curves required eight initially accepted candidates; 49,889 of 50,000 planned paths were eligible. Boundary estimates are conditional on this feasibility rule. McGill used 100 repeats and identity-disjoint poison/probe sources; only the first temporal half of poison-source Day-2 windows supplied attack candidates and the second half of probe-source windows supplied future probes. Further threat-model and exclusion details are in Supplementary Methods S3.

HMOG used master seed 4242 for attack partitions and sequences. The common maximum-budget feasibility rule made all methods and nested budgets comparable within a path. It also conditions the reference effect on victims and repeats with sufficient initially accepted impostor candidates. Sensitivity conditions recomputed this eligibility rather than carrying infeasible reference paths forward.

The poisoning comparison included Frozen, Blind, malicious-update-blocking Oracle, and Guarded on HMOG; McGill included Frozen, Blind, and Guarded. GUR was obtained by replaying genuine observations on a copy of the post-poison state. This replay could not change the already recorded post-poison endpoints, so it measured update availability rather than longitudinal recovery.

The unit called a poisoning attempt was a selected score-bearing observation presented to the online rule. Candidate generation and ranking occurred before those presentations and were not counted as queries. Poison acceptance and malicious updating were distinct: an observation could satisfy the access rule yet fail the Guarded update condition. Likewise, post-poison ASR described decisions on the held-out probe pool and was not the acceptance rate of the poisoning candidates themselves. These distinctions were preserved in the saved path-level outputs.

## 3.5. Operating-point sensitivity

The sensitivity analysis reused frozen HMOG and McGill scores and compared each reference threshold with nominal 5% and 1% pooled calibration-FAR constraints. HMOG reference was the canonical approximate-EER threshold; McGill reference minimized Day-1 enrollment HTER. HMOG calibration used its validation partition, while McGill used Day-1 enrollment/calibration only. No test or Day-2 observation selected a threshold. For each claimant, the smallest threshold no lower than reference that met the target calibration FAR was chosen, with equal scores kept on the same side of the decision boundary. Exact float64 and tie handling is specified in Supplementary Methods S3. Nominal targets were calibration constraints, not held-out guarantees or deployment standards.

Enrollment moments remained fixed. Each new \(\tau_0\) produced a new

\[
k=(\mu_0-\tau_0)/\sigma_0,
\]

including negative values. EMA \(\alpha=0.05\), Guarded \(\lambda=0.25\), pool assignments, attack budgets, and split semantics remained fixed. Boundary candidates were reselected relative to the condition-specific \(\tau_0\). Recalibration therefore changed \(\tau_0\), associated \(k\), candidate composition, and feasible paths; it was not an isolated intervention on one threshold.

Methods were paired within each condition. Each boundary curve used its own common \(K=8\)-feasible cohort, so rows across operating points were not strictly paired causal contrasts. Random reporting used all structurally valid planned paths, while historical reference reporting retained its legacy cohort. The sensitivity primary contrast was HMOG nominal 1%, boundary \(K=8\), Blind minus Frozen post-poison ASR; it did not replace the historical reference contrast.

Pool assignments, master attack seed 4242, 100 repeats, and nested budgets were fixed. Random orders were threshold-independent. Boundary candidates were reselected within each condition using \(s\geq\tau_0\) and initial margin, with deterministic index tie-breaking. Profiles were frozen after poisoning before future ASR and FRR were evaluated.

Calibration summaries and held-out outcomes used different observations and aggregation. The reported achieved calibration FAR is an unweighted mean of claimant-profile pooled-observation rates. Full held-out Frozen results use all structurally valid random-\(K=0\) paths and hierarchical victim-macro aggregation. Conditional boundary effects use only paths feasible at \(K=8\). These denominators were retained separately in all tables.

## 3.6. Clean temporal protocols and Oracle diagnostic

HMOG clean adaptation used synthetic standardized-feature shifts \(D\in\{0,1,2\}\). A fold-specific random unit direction was ramped across each subject's test sequence and applied to every time step. The magnitudes were not calibrated to natural behavioral change, and the nonlinear score response need not have been identical across subjects. In the global scenario, claimant and impostor scores came from the same \(D\); in the primary claimant-only scenario, genuine adaptation and checkpoints used the selected \(D\), while impostor probes remained at \(D=0\).

Sessions were ordered by their recorded numeric identifiers. Within each retained session, the sequence beginning at `within=0` was an adaptation candidate and the disjoint sequence beginning at `within=10` was an evaluation-only checkpoint. Checkpoints never updated state. At least four complete session pairs were required. The first two checkpoints defined early endpoints and the last two defined late endpoints; an available middle checkpoint was retained only for trajectories. Impostor FAR used other identities at the matched session number and `within=10`, measured at the same profile state and macro-averaged across source identities. Late HTER combined temporally matched late FRR and FAR. The available source confirms this replay order but does not independently validate numeric session identifiers as natural behavioral chronology.

The temporal comparison included Frozen, Blind, Guarded, and Oracle-all. Outputs included early and late FRR/FAR, late HTER, GUR, update counts, and changes in mean, scale, and threshold. Adaptation gain was Frozen late FRR minus method late FRR. McGill selected 160 approximately equally spaced Day-2 windows per subject and formed 80 ordered adaptation-checkpoint pairs; the first and last 20 pairs defined early and late endpoints. Matched impostor checkpoints never updated a profile. Day separation reflects cross-day change but does not isolate behavior from placement, context, acquisition, or model-transfer effects.

## 3.7. Aggregation and uncertainty

Rate differences are reported in percentage points. The historical security contrast was HMOG reference boundary \(K=8\), Blind minus Frozen post-poison ASR. Repeats were averaged within victim and fold, folds within victim, and the 100 victim effects were resampled with 10,000 paired percentile-bootstrap draws. The sensitivity package used the same hierarchy with deterministic condition-specific streams. Historical and sensitivity reference intervals are therefore reported from their respective frozen packages. Full seed reconciliation is in Supplementary Methods S4.

The sensitivity primary used the same hierarchical victim estimand at HMOG nominal 1%. Table rows at other conditions and datasets are secondary. The clean temporal primary compared Guarded with Frozen late FRR in claimant-only \(D=2\). TQ-v1 retained its branch-specific success criterion. Random attacks, other budgets, lambda values, drift levels, and stopped branches were exploratory or descriptive; no post-result multiplicity correction was introduced.

For clean HMOG streams, each subject was first averaged across available folds before paired subject bootstrap. A 99-subject complete-five-fold cohort checked the TQ-v1 decision. McGill repeats were averaged within subject before paired bootstrap. HMOG folds have overlapping training partitions and Monte Carlo repeats are not independent; fold summaries and their \(t\)-bands are descriptive only. Within the poisoning operating-point analysis, a victim-by-impostor-source robustness interval exists only for HMOG nominal 1%, boundary \(K=8\); source-resolved outcomes were unavailable for the historical reference poisoning package. Separately, TQ-v1 clean temporal late FAR had its own victim-by-impostor-source sensitivity analysis. All intervals condition on fixed trained models and observed pools and do not cover training or population uncertainty.

The historical HMOG subject bootstrap used 10,000 percentile draws and direct seed 4242. The sensitivity and McGill packages also retained 10,000-draw paired victim intervals with deterministic condition-specific streams. Small reference-CI differences between historical and sensitivity tables arise from those retained streams; point estimates, cohorts, and victim effects agree. No interval was chosen for width.

Within operating-point conditions, methods were matched on poison sequences, probes, and eligibility. Across conditions, effects were not treated as paired because candidate sets and feasible cohorts could change. Rates were averaged at the victim level before resampling rather than pooling all probe windows. No null-hypothesis test was added; interpretation uses paired effects, retained percentile intervals, explicit denominators, and the prespecified scope of each contrast.

Accordingly, the paired poisoning estimand is conditional on a path satisfying the common maximum-budget eligibility rule at the operating point being reported. It is not an estimate for excluded victims or repeats assigned a zero effect. The full-cohort Frozen summaries answer a separate calibration-transfer question and use all structurally valid paths. Clean temporal estimates use subjects with the required adaptation-checkpoint sequence and do not reuse the conditional poisoning cohort. Keeping these populations separate prevents a calibration summary, an attack-conditional effect, and a temporal recovery estimate from being read as measurements on one common sample.

## 3.8. Supporting probes and reproducibility

TQ-EMA v1 admitted temporally consistent rejected near-boundary evidence through an isolated, bounded recovery path. Its primary endpoint was late-FRR gain over Frozen in claimant-only \(D=2\), subject to fixed FAR and HTER constraints. TQ-EMA v2 added a recovery episode that suppressed trusted proposals moving state upward. The Adaptive Quantile Profile replaced EMA moments with exponentially weighted \(q_{20}\) and \(q_{50}\). TQ-v2 and Quantile used fail-closed validation: outer scores remained unopened if any fold had no feasible configuration. Complete state machines, grids, equations, and criteria are in Supplementary Methods S6-S10.

TQ-v1 required a paired late-FRR-gain CI lower bound above zero, mean late-FAR increase no greater than +1.0 point, HTER degradation no greater than +0.5 point, and the same conclusion in the 99-subject complete-five-fold cohort. The FAR and HTER limits were branch-specific experimental constraints rather than deployment standards. TQ-v1 was evaluated only on clean temporal streams and was not combined with poisoning.

Frozen packages record seeds, exclusions, configurations, source and cache hashes, and whether outer data were loaded. The method, McGill, and operating-point freezes are tagged `paper3-method-freeze-2026-10-02`, `paper3-external-mcgill-v1-2026-10-03`, and `paper3-operating-point-sensitivity-v1-2026-10-04`. Supplementary Methods S4-S5 provides the package registry, recorded revisions and hashes, principal schemas, invariant checks, and external-protocol details; it also states where historical provenance is incomplete.

The recorded protocol suites covered no-update behavior, malicious-update-blocking Oracle/Frozen equivalence in malicious-only streams, nested budgets, partition disjointness, gate behavior, bounded recovery transitions, and deterministic aggregation. The reported outcomes and checks are those retained in the frozen packages.
