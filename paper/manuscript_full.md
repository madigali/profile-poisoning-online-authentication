# [TITLE TO BE FINALIZED]

## Abstract

Behavioral continuous authentication can update a user's profile during operation, but accepted-only adaptation creates one feedback loop with two coupled effects: accepted impostor observations can enter the future profile state, while rejected genuine observations are censored from learning. This study characterizes that malicious-inclusion/genuine-censoring mechanism in score-level online behavioral authentication. The primary HMOG analysis used held-out random and score-informed boundary poisoning, controlled synthetic claimant-only sensitivity shifts, and matched Frozen, Blind exponential moving-average (EMA), Guarded EMA, and label-aware Oracle-all-genuine controls. The boundary strategy is a strong score-access benchmark: \(K\) counts selected poisoning attempts presented to the updater, not candidate screening or reconnaissance, and a binary-feedback-only attack was not demonstrated. The principal directions were then evaluated in an independent two-day McGill Gait mechanism-level replication.

At the HMOG validation-calibrated, approximately equal-error operating point, post-poison attack success rate under the boundary strategy at \(K=8\) was 22.92% for Frozen, 53.96% for Blind EMA, and 22.93% for Guarded EMA. The paired Blind-minus-Frozen increase was +31.04 percentage points (95% subject-bootstrap CI [+26.95, +35.20]). During the HMOG claimant-only sensitivity condition at \(D=2\), accepted-only Guarded adaptation did not lower late false rejection rate relative to Frozen. Oracle-all restored rejected genuine observations to the update stream and improved late false rejection rate by 6.60 points, but late false acceptance rate increased by 6.08 points. On McGill, boundary-attack success rates at \(K=8\) were 12.37% for Frozen, 32.09% for Blind EMA, and 12.48% for the transferred Guarded rule under a real cross-day shift. Prespecified recovery/state probes did not establish improved false-rejection recovery under their frozen constraints.

These results support a coupled mechanism under the tested protocols: separate update authorization suppresses the additional poisoning-induced amplification relative to Blind EMA, while conservative accepted-only learning censors low-scoring genuine evidence that changes the adaptive trajectory. Returning ASR near Frozen does not establish that the underlying system is secure, and the experiment does not establish performance at deployment-oriented low-FAR operating points. Removing censoring changes genuine tracking but can incur a large false-acceptance cost. Poisoning resistance and adaptation utility should therefore be evaluated jointly, with trusted recovery evidence considered separately from ordinary authentication confidence.

# 1. Introduction

Authentication at device unlock establishes who was present at one point in time; it does not by itself verify that the same person continues to operate the device throughout the session. Continuous behavioral authentication addresses this temporal gap by repeatedly estimating identity from signals generated during ordinary interaction. On smartphones, these signals include touch and keystroke dynamics, gait and hand motion, and combinations of motion, interaction, and usage context \cite{Mahfouz2017SmartphoneSurvey,Abuhamad2021SensorSurvey,Stylios2021MobileSurvey}. Representative systems have shown that touchscreen behavior and inertial measurements can provide unobtrusive identity evidence without requiring a separate biometric action for every decision \cite{Frank2013Touchalytics,Sitova2016HMOG,Fereidooni2023AuthentiSense}. Multimodal designs further combine touch, movement, and contextual information when one behavioral source is unavailable or unreliable \cite{Shen2022MMAuth}. Continuous authentication is therefore attractive as a complement to initial login, but it places identity decisions inside a changing stream rather than a single controlled transaction.

That stream is not stationary. Behavioral measurements can vary across sessions, activities, sensor orientations, acquisition conditions, and time. Touchalytics, for example, reported different operating characteristics across intra-session, inter-session, and delayed evaluations, while multi-session keystroke studies motivated updating because the enrolled reference may cease to represent later typing behavior \cite{Frank2013Touchalytics,Giot2011KeystrokeUpdate}. More generally, adaptive-biometric research treats template ageing and intra-class variation as reasons to revise a stored reference during operation \cite{Rattani2009TemplateUpdate,Ryu2023AdaptiveBiometrics}. Online profile or template update is a natural response: new observations can refresh the state used for future authentication rather than leaving the enrollment profile fixed. Yet adaptation also changes the security boundary. The system must decide not only whether an observation is sufficiently genuine-like to grant access, but also whether it is sufficiently trustworthy to alter future decisions.

Unsupervised and semi-supervised update methods commonly obtain labels from the current matcher rather than from an external authority \cite{Rattani2009TemplateUpdate,Didaci2014UnsupervisedUpdate}. This convenience creates an attack surface. If an impostor observation is accepted and then reused as claimant evidence, the profile can be moved in a direction that changes later authentication outcomes. Prior work has demonstrated this risk in adaptive face systems, including template-compromise and biometric-backdoor attacks, and in self-updating fingerprint authentication \cite{Biggio2012PoisoningAdaptive,Biggio2013FacePoisoning,Lovisotto2020BiometricBackdoors,Xue2020LOPA}. Sequential contamination is also studied in the broader online-learning literature, although those formulations are not biometric evidence and rely on different learners and attacker capabilities \cite{Zhang2020OnlinePoisoning}. These studies establish that poisoning is not unique to the present work. They also make clear that a mobile behavioral profile should not be evaluated as if every accepted operational sample were a reliable training label.

A conservative update rule creates a second, less visible problem. If authentication acceptance is required before a genuine observation can enter the update stream, the current decision boundary determines what the learner will be allowed to observe. Genuine samples that fall below the threshold during a downward behavioral shift are rejected and censored from adaptation, while higher-scoring samples remain available. Related problems appear in selective-label settings, where prior decisions determine which outcomes are observed, and in self-training, where model-generated pseudo-labels can reinforce earlier errors \cite{Lakkaraju2017SelectiveLabels,Arazo2020ConfirmationBias}. Performative-prediction research provides a broader account of deployed decisions changing the distributions encountered by later learning \cite{Perdomo2020PerformativePrediction}. None of these literatures directly studies the score-profile mechanism evaluated here. We therefore use the term *selective-update bias caused by accepted-only feedback censoring* for this authentication-specific case: the access decision selects the evidence from which the future authentication state is learned.

Existing research provides strong foundations for mobile behavioral authentication, biometric template updating, and adaptive-template poisoning, but their interaction remains insufficiently characterized. A recent review of adaptive biometric authentication found limited attention to continuous mobile operation and large-scale longitudinal evaluation \cite{Ryu2023AdaptiveBiometrics}. Our systematic review similarly identified, within its searched corpus, gaps in standardized adversarial evaluation, longitudinal and ecologically valid evidence, and empirical integration of behavioral continuous authentication with intelligent personal-agent architectures \cite{Gali2026SystematicReview}. The component literatures should not be mistaken for an absence of prior work: separate update thresholds have precedent in keystroke template updating \cite{Giot2011KeystrokeUpdate}, and adaptive biometric poisoning has been demonstrated for other modalities. The narrower gap is joint evaluation. In the literature reviewed here, joint evaluation of held-out poisoning, legitimate temporal recovery, update-stream composition, and feedback availability remains limited.

This study continues a two-paper research program on behavioral-biometric continuous authentication for mobile intelligent agents. Paper 1 synthesized 80 included studies and documented the qualified gaps above \cite{Gali2026SystematicReview}. Paper 2 then evaluated a session-disjoint HMOG pipeline with a fixed LSTM score generator and an accepted-only exponential moving-average (EMA) score profile \cite{Serbin2026AdaptiveLSTM}. That EMA rule did not improve HTER relative to a frozen threshold in the tested conditions. Because it was label-blind, an accepted impostor could enter the profile, but Paper 2 did not conduct a dedicated poisoning experiment. Paper 3 takes that mechanism as its starting point rather than attributing the present attack evaluation to the earlier study.

Paper 3 evaluates the security and adaptation consequences of score-level online updating in a sequence of frozen experiments. First, it measures random and score-informed near-boundary poisoning using poison samples separated from future impostor probes. The boundary strategy assumes access to claimant scores and ranks initially accepted candidates by margin; \(K\) counts only the selected attempts subsequently presented for poisoning, not reconnaissance or candidate screening. It is therefore a strong score-access benchmark, not a demonstrated binary-feedback-only attack. Second, the study uses Guarded EMA as an experimental update-authorization control: it retains the authentication threshold but adds the separate learning threshold already motivated by prior template-update work. Third, matched Frozen, Blind, Guarded, and label-aware Oracle-all-genuine controls test how accepted-only eligibility changes the genuine evidence available to the updater. Recovery-state and quantile-profile branches serve as prespecified supporting probes and stop when their validation constraints are not met. Finally, the principal directions are evaluated under a separately frozen two-day McGill Gait protocol. HMOG uses controlled synthetic standardized-feature sensitivity shifts, whereas McGill provides a real Day-1/Day-2 shift that may combine behavior, context, placement, acquisition, and model-transfer effects.

The paper makes five contributions, ordered by their role in the scientific claim:

1. It characterizes one accepted-only feedback loop that produces two coupled effects in the tested systems: malicious inclusion when accepted impostor observations alter future profile state, and genuine-evidence censoring when rejected genuine observations are excluded from adaptation.
2. It provides a held-out poisoning protocol with nested budgets, preselection poison/probe separation, frozen future-probe evaluation, explicit eligibility accounting, and a primary paired subject-level effect estimate.
3. It evaluates a separate update-authorization threshold as a security control and experimental intervention, while recognizing that confidence-gated and two-threshold template update is prior art rather than a new algorithmic principle.
4. It uses a label-aware, non-deployable Oracle-all information-availability intervention, temporal trajectories, and update-rate accounting to isolate how accepted-only eligibility changes the adaptive stream.
5. It provides an independent directional mechanism-level replication on the two-day McGill Gait dataset, transferring the HMOG Guarded rule without Day-2 tuning.

The reported thresholds are validation-calibrated, approximately equal-error operating points rather than deployment-grade low-FAR targets. The experiments test relative poisoning-induced amplification and feedback mechanisms at those operating points; Guarded returning ASR near Frozen does not establish absolute system security. The contributions do not claim a universally safe adaptive authenticator, a novel two-threshold invention, or a general impossibility result. Their purpose is to make the coupled security and information-selection effects of online behavioral adaptation observable, reproducible, and separately testable.

# 2. Related Work

## 2.1. Behavioral Continuous Authentication on Mobile Devices

Continuous mobile authentication uses evidence produced during ordinary device use to reassess whether the current operator remains consistent with the enrolled user. Surveys organize this evidence into touch and swipe dynamics, keystroke behavior, gait and motion, voice, application or contextual patterns, and multimodal combinations \cite{Mahfouz2017SmartphoneSurvey,Abuhamad2021SensorSurvey,Stylios2021MobileSurvey}. Modalities differ in availability. Touch and keystroke evidence depends on particular user actions, whereas inertial sensors can capture hand movement, posture, or gait during broader classes of activity. Multimodal systems attempt to compensate for missing or context-sensitive signals by combining multiple sources, but they add fusion, calibration, and resource-management decisions \cite{Ross2003InformationFusion,Shen2022MMAuth}.

Several representative systems illustrate this progression. Touchalytics modeled touchscreen interaction and explicitly compared intra-session, inter-session, and delayed authentication \cite{Frank2013Touchalytics}. SilentSense combined touch dynamics with device movement to authenticate users in static and mobile conditions \cite{Bo2013SilentSense}. HMOG introduced hand-movement, orientation, and grasp features derived from smartphone inertial and interaction data and released the dataset that underlies the primary pipeline in this paper \cite{Sitova2016HMOG}. More recent systems have expanded the representation and deployment setting: MMAuth fuses motion, touch, and usage context; AuthentiSense uses inertial motion with few-shot learning; and MAUTH derives identity evidence from subtle motion associated with muscular tremor \cite{Shen2022MMAuth,Fereidooni2023AuthentiSense,Jiang2024MAUTH}. These works establish the breadth of mobile behavioral evidence, but their model architectures and evaluation units are not directly interchangeable.

Gait data provide an additional temporal and cross-session perspective. The official McGill mobile-phone gait archive contains recordings from 20 individuals on two collection days and is the authority for the external dataset used here \cite{Frank2010McGillGaitDataset}. The associated research program studied activity and gait recognition using mobile sensors \cite{Frank2010ActivityGait}. Other work evaluated smartphone gait under live imitation attacks \cite{Muaaz2017GaitImitation}, while whuGAIT was developed for gait recognition under less constrained smartphone collection \cite{Zou2020WhuGait}. Paper 3 does not treat these datasets as exchangeable benchmarks: HMOG and McGill differ in subjects, modalities, tasks, classifiers, and chronology. McGill is used as an independent mechanism-level replication rather than as evidence that absolute error rates transfer across datasets.

The continuous-authentication literature therefore provides convincing evidence that mobile behavior can carry identity information. It also shows why fixed-condition accuracy is only one part of evaluation. Session, activity, sensor, and context differences affect the evidence available to the classifier, and an online system must decide what to do when the current observations no longer resemble enrollment. That decision motivates adaptive biometric profiles.

## 2.2. Adaptive Biometric Profiles and Template Updating

Template update modifies a biometric reference after enrollment so that it can remain representative of later genuine observations. This objective is related to the broader concept-drift problem of learning under changing data distributions \cite{Gama2014ConceptDrift,Lu2019ConceptDrift}. Foundational biometric work distinguishes supervised update, in which trusted labels are supplied externally, from semi-supervised or unsupervised update, in which the matcher assigns operational samples to the user and then reuses them for adaptation \cite{Rattani2009TemplateUpdate,Didaci2014UnsupervisedUpdate}. The latter avoids repeated manual enrollment but couples recognition errors to future model state.

Behavioral biometrics make this problem concrete because their distributions can vary across sessions. Giot et al. studied multi-session keystroke dynamics and proposed semi-supervised update rules with separate acceptance and update thresholds \cite{Giot2011KeystrokeUpdate}. That work is important for positioning Paper 3: the conceptual separation between an access threshold and a stricter learning threshold is prior art. The contribution of Guarded EMA is therefore not invention of a second threshold. It is the evaluation of that separation inside the frozen Paper 3 poisoning protocol, together with malicious and genuine update rates, clean temporal behavior, and external replication.

Unsupervised template-update analyses have examined self-update and related schemes in which confidently classified operational samples are used to refresh a gallery \cite{Didaci2014UnsupervisedUpdate}. Adaptive algorithms have also been applied directly to accelerometer biometric streams, demonstrating that inertial identity evidence can be treated as non-stationary data rather than only as a fixed batch-classification problem \cite{Pisani2017AccelerometerAdaptation}. A recent systematic review describes a wider design space that includes query-acceptance rules, confidence-based updates, classifier retraining, user-specific decisions, and structural adaptation; it also reports limited continuous/mobile and large-scale longitudinal evaluation within the surveyed adaptive-biometric literature \cite{Ryu2023AdaptiveBiometrics}.

These approaches differ critically in their source of trust. Supervised update assumes a verified genuine label. Self-update assumes that matcher confidence is an adequate proxy for that label. Some systems use a higher update threshold than the authentication threshold, reducing but not eliminating the possibility of an accepted impostor entering the reference. Others update galleries in batches, use co-update across modalities, or retrain a classifier. The security question is thus inseparable from the sampling question: an adaptive method must specify not only *how* its state moves but *which observations it is allowed to see*.

Paper 2 instantiated one accepted-only score-profile rule on HMOG. It updated EMA moments after accepted attempts and otherwise retained the existing state \cite{Serbin2026AdaptiveLSTM}. Under the verified Paper 2 protocol, the adaptive rule did not improve HTER over Frozen, and the paper identified that an accepted impostor could contaminate the label-blind profile. It did not conduct a dedicated poisoning experiment. Paper 3 preserves that implementation as the Blind EMA baseline, experimentally isolates the contamination path, and then uses clean controls to examine the information excluded by accepted-only updating.

## 2.3. Poisoning and Adversarial Threats

Adaptive biometric poisoning predates this study. Biggio et al. formalized poisoning of adaptive biometric systems and later evaluated attacks designed to compromise face templates under multiple template and matcher configurations \cite{Biggio2012PoisoningAdaptive,Biggio2013FacePoisoning}. Lovisotto et al. showed that an attacker could construct a sequence of intermediate face samples that exploited unsupervised template updating to establish a biometric backdoor; they also evaluated a detector based on the directionality of consecutive updates \cite{Lovisotto2020BiometricBackdoors}. Xue et al. demonstrated a sequential poisoning method against online self-updating fingerprint authentication \cite{Xue2020LOPA}. These are direct biometric precedents, so neither poisoning adaptive templates nor defending them can be claimed as first introduced by Paper 3.

The attack surface considered here is narrower in some respects and different in others. Paper 3 does not modify LSTM weights, enrollment data, sensor firmware, or raw biometric templates. It attacks the online score-profile state by presenting impostor observations that already satisfy the authentication rule, then measures future success on held-out impostor probes after adaptation is frozen. Its boundary strategy uses score information and should be read as a strong benchmark, not as a binary-feedback-only attacker. The study also differs from presentation or imitation attacks. For example, smartphone gait has been evaluated against live mimicry \cite{Muaaz2017GaitImitation}, but evading a fixed matcher at decision time is not the same as contaminating an adaptive state to change later decisions.

Online poisoning is also studied in general machine learning. Zhang et al. formulate sequential contamination of an online learner as a control problem \cite{Zhang2020OnlinePoisoning}. That work helps frame how early malicious inputs can affect later model behavior, but it is analogous rather than direct evidence for biometric authentication: the learner, observation space, attacker interface, and acceptance process differ. Recent biometric-template surveys provide wider taxonomies of attacks and protections \cite{Baaqeel2022AdaptiveSpoofingSurvey,Abdullahi2024TemplateAttacks}; specific claims about adaptive poisoning in this paper rely on the primary face and fingerprint studies above.

## 2.4. Selective Feedback and Adaptation Bias

Most adaptive-biometric work emphasizes erroneous inclusion: an impostor is incorrectly labeled genuine and enters the template. Paper 3 additionally considers erroneous *exclusion*. When only accepted observations are eligible for learning, the authentication decision controls which part of the claimant-score distribution becomes visible to the updater. Under a downward shift, rejected genuine observations carry evidence that the profile may need to move, but the production updater never receives that evidence.

The closest established concepts arise outside biometric authentication. The selective-labels literature studies settings in which a decision determines which outcomes will later be observed, making the labeled dataset conditional on previous choices \cite{Lakkaraju2017SelectiveLabels}. Self-training research documents confirmation bias when model-generated pseudo-labels are reused and errors reinforce subsequent learning \cite{Arazo2020ConfirmationBias}. Performative prediction considers the broader case in which deployed predictions and associated decisions alter the future distribution on which a model is retrained or evaluated \cite{Perdomo2020PerformativePrediction}.

These concepts are related but not identical to the mechanism in Paper 3. In selective-label applications, the missing information is typically an unobserved outcome following a human or algorithmic decision. In accepted-only authentication, the true genuine/impostor label exists for evaluation but is unavailable to the deployed updater, and the decision censors eligibility for state update. Likewise, the claimant's underlying behavior need not change *because* of the authentication decision, so the mechanism is narrower than performative prediction. We use *selective-update bias caused by accepted-only feedback censoring* as an authentication-specific description, not as an established term imported from those literatures. The Oracle-all control is designed to expose the information difference: it changes update eligibility while leaving ordinary access decisions recorded and unchanged.

## 2.5. Research Gap and Positioning

Prior research already supplies each major component of the Paper 3 problem. Mobile behavioral authentication has been evaluated across touch, motion, gait, context, and multimodal evidence. Adaptive-biometric research has developed supervised and self-updating templates, including confidence gates and separate update thresholds. Face and fingerprint studies have established that unsupervised update can be poisoned. Selective-label and self-training research explains, by analogy, why decision-conditioned feedback can produce a biased learning stream.

What remains limited is joint, protocol-controlled evidence connecting these components. Reviews of adaptive biometric systems report sparse continuous/mobile and large-scale longitudinal evaluation \cite{Ryu2023AdaptiveBiometrics}, while our prior systematic review identified limited standardized adversarial benchmarks and longitudinal/ecologically valid evidence within its corpus \cite{Gali2026SystematicReview}. Prior studies do combine security and utility considerations in several settings; the narrower gap concerns their joint evaluation with held-out poisoning, legitimate temporal recovery, update composition, and feedback availability in mobile behavioral authentication, especially with fail-closed validation and independent temporal replication.

Paper 3 is positioned as a mechanism study within that gap. Its principal contribution is not poisoning or a second threshold in isolation. It characterizes how one accepted-only feedback rule creates both malicious inclusion and genuine-evidence censoring. The attack experiment asks whether accepted impostor scores alter future held-out acceptance; the Guarded comparison uses established threshold separation as a security intervention; and the clean temporal controls ask whether the same restriction removes evidence needed for claimant recovery. Oracle-all is a label-aware information-availability diagnostic rather than a deployable method. The stopped recovery branches provide supporting protocol-controlled negative evidence rather than headline algorithmic contributions. The McGill study then tests whether the principal directions recur under a different dataset, classifier, modality set, and real Day-1/Day-2 separation.

This positioning also distinguishes profile adaptation from risk-sensitive access control. Biometric thresholds trade false acceptance against false rejection, and threat-sensitive thresholding makes this cost explicit \cite{Jain2004BiometricRecognition,Joshi2020AdaptiveThreshold}. Mobile systems have also used passive confidence or context to decide when stronger explicit authentication is required \cite{Riva2012ProgressiveAuthentication,Hayashi2013CASA,Crawford2013ContinuousFramework}. Such step-up designs, multimodal corroboration, and current risk-based authentication guidance provide plausible sources of trusted recovery evidence \cite{Ross2003InformationFusion,Temoshok2025NIST80063B4}. They are not evaluated solutions in Paper 3. The present contribution is to show why future recovery evidence must be assessed simultaneously for its security provenance and its ability to escape accepted-only censoring.

# 3. Methods

## 3.1. Study Design and Experimental Overview

This study examined two coupled risks in score-level online adaptation for behavioral-biometric continuous authentication: profile poisoning by accepted impostor observations and feedback censoring when rejected genuine observations are excluded from adaptation. The study was organized as a sequence of mechanism-focused experiments rather than as a general classifier benchmark. HMOG was the primary mechanistic dataset \cite{Sitova2016HMOG}. A fixed LSTM score generator inherited from Paper 2 \cite{Serbin2026AdaptiveLSTM} was used to evaluate (i) held-out poisoning of Blind EMA, (ii) confidence-gated update authorization, (iii) adaptation under synthetic temporal feature drift, and (iv) diagnostic and recovery controls. A separately locked two-day McGill Gait protocol examined whether the principal poisoning, defense, and feedback-censoring patterns transferred to an independent dataset with natural day separation \cite{Frank2010McGillGaitDataset}.

The experimental branches were developed sequentially, so their evidential roles are not interchangeable. The following compact table records the paper-level hierarchy. “Primary reporting contrast” below defines the final manuscript focus; it does not retroactively convert the exploratory HMOG development sequence into an untouched confirmatory study. TQ-EMA v2 and the Adaptive Quantile Profile used fail-closed validation: if any outer fold lacked a configuration satisfying the fixed validation constraints, outer test scores were not loaded. The McGill protocol transferred the HMOG reporting rule before Day-2 outcomes were accessed.

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

The full evidence-status record and protocol provenance are retained separately. HMOG method development was frozen under Git tag paper3-method-freeze-2026-10-02; the external replication was frozen under paper3-external-mcgill-v1-2026-10-03.

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

Guarded EMA separated access authentication from update authorization. Access continued to depend only on \(s_t\geq\tau_{u,t}\). For an authenticated observation, the update threshold was

\[
\tau^{\mathrm{update}}_{u,t}
=\tau_{u,t}+\lambda\left(\mu_{u,0}-\tau_{u,t}\right),
\]

and the profile was updated only if \(s_t\geq\tau^{\mathrm{update}}_{u,t}\). Thus an observation could be accepted for access but withheld from learning. The main carried-forward comparison used \(\lambda=0.25\); this value was an exploratory carry-forward from the HMOG poisoning sweep and was not treated as universally optimal.

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

## 3.6. Clean Temporal Drift Protocol

Clean adaptation was evaluated at synthetic sensitivity levels \(D\in\{0,1,2\}\). The transformation inherited from Paper 2 was applied after model training in standardized 36-dimensional feature space. For each fold, a direction was sampled from a standard multivariate normal distribution using seed \(42+f\), normalized to unit length, and linearly ramped over each subject's chronological test sequence to final Euclidean magnitude \(D\). The same displacement was added to all 10 time steps of a sequence. The \(D\) levels were not empirically calibrated to natural behavioral change. This procedure was a controlled synthetic feature-shift sensitivity analysis, not natural behavioral drift.

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

All rate differences were reported in percentage points. The paper-level primary security reporting contrast was HMOG boundary \(K=8\), Blind EMA minus Frozen post-poison ASR. The primary adaptation reporting contrast was Guarded versus Frozen late FRR in claimant-only HMOG \(D=2\), reported equivalently as Frozen-minus-Guarded late-FRR gain. These labels define the final reporting focus and do not retroactively make the sequential HMOG development confirmatory. The TQ-EMA v1 late-FRR endpoint retained its separate branch-specific prespecified status. Other budgets, random attacks, lambda values, drift levels, and stopped branches were secondary or exploratory; no post-hoc multiplicity correction was introduced.

For the primary poisoning contrast, exact Blind and Frozen outcomes were recovered from the retained frozen subject-repeat output whose fold summaries, configuration, manifest, and exclusions matched the committed authoritative package byte-for-byte. Within every eligible fold-victim-repeat path, the paired post-ASR difference was calculated. Repeats were averaged within fold and victim, and the resulting five fold-level means were averaged within each victim. The 100 victim effects were resampled with replacement using 10,000 percentile-bootstrap draws and seed 4242. This analysis used only retained outcomes; no scoring, attack selection, partitioning, adaptation, or experiment was rerun. A victim-by-impostor-source bootstrap was infeasible because source-identity contributions were not retained at the granular outcome level.

In the remaining HMOG poisoning summaries, Monte Carlo repeats were averaged within subject and subjects were macro-averaged within fold. Across-fold means, standard deviations, standard errors, and \(t\)-intervals were descriptive protocol-stability summaries only. The five outer folds had overlapping fitting partitions, and the repeated attack paths were Monte Carlo replicates; neither was treated as a set of independent observations for confirmatory inference.

For clean drift, each subject was first averaged across its available folds. Paired subject effects relative to Frozen were then resampled with replacement using 10,000 percentile-bootstrap draws to obtain 95% confidence intervals. The primary cohort retained every subject with available paired data. A sensitivity analysis used the 99 subjects with complete data in all five folds. For TQ-EMA v1 late FAR, a secondary two-way bootstrap independently resampled victim identities and impostor-source identities. No new null-hypothesis tests or post-result multiplicity correction were introduced; secondary contrasts and parameter sweeps remained exploratory.

The McGill analysis averaged attack repeats within subject and used paired subject effects with 10,000 percentile-bootstrap draws. Eligibility and denominators were reported for each contrast. There were no folds in the McGill analysis.

## 3.12. External Replication on McGill Gait

whuGAIT Dataset #2 was examined before the external protocol was frozen \cite{Zou2020WhuGait}. Its processed archive contained shuffled train/test signal matrices and subject labels but did not preserve day, session, timestamp, or original-order fields. File order could therefore not support the planned temporal replication without constructing an artificial chronology. The dataset was not used for the unified poisoning-and-temporal replication.

The external protocol instead used the official McGill Gait archive \cite{Frank2010McGillGaitDataset}, which contained raw timestamped recordings from 20 subjects (w001–w020) on two collection days. Day 1 was used for model development, normalization, enrollment, and threshold calibration; Day 2 was held out for the attack and temporal analyses. McGill lacked gyroscope data, so the replication used only accel_x, accel_y, accel_z, and the supplied gravity-adjusted accelerometer magnitude. Magnetometer, orientation, and temperature channels were excluded. The recorded median sample interval was 40 ms (approximately 25 Hz); no interpolation was applied. Inputs were non-overlapping 128-sample windows (approximately 5.12 s) with shape 128 × 4.

One pooled per-channel z-score transform was fitted only to Day-1 training windows. Within each subject, Day-1 windows were split chronologically into 60% model fitting, 20% early-stopping validation, and 20% enrollment/calibration using floor-valued cut points. The fixed classifier was a one-layer unidirectional LSTM with input size 4, hidden size 64, final-hidden-state classification, and a 20-class linear head. Training used class-weighted cross-entropy, Adam with learning rate 0.001 and weight decay 0.0001, batch size 128, at most 30 epochs, and validation-loss early stopping with patience 5. The claimant score was the corresponding softmax probability.

The McGill EMA used \(\alpha=0.05\) and standard-deviation floor \(10^{-4}\). The initial threshold was calibrated on Day-1 enrollment scores by minimum HTER, with exact ties resolved toward the higher threshold; \(k\) was then fixed from the enrollment mean, standard deviation, and threshold. Guarded EMA used \(\lambda=0.25\), transferred unchanged from the HMOG reporting comparison. No McGill lambda sweep or post-Day-2 parameter tuning was permitted.

The poisoning replication used random and score-informed boundary attacks, nested \(K\in\{0,1,2,4,8\}\), 100 repeats, and a source-identity-disjoint poison/probe split as close to 50/50 as possible. Only the first temporal half of poison identities' Day-2 windows was eligible for poisoning, and only the second half of probe identities' Day-2 windows was used for held-out ASR. States were frozen before probe and genuine evaluation. The poisoning comparison included Frozen, Blind EMA, and Guarded EMA. Random selection retained all 2,000 victim-repeat paths across 20 victims. Boundary \(K=8\) retained 1,456 paths across 18 victims and excluded 544 paths that lacked eight initially accepted candidates; boundary \(K=0\) used the same maximum-budget-feasible cohort.

For the temporal analysis, 160 approximately equally spaced Day-2 windows were selected per subject and paired into 80 chronological units, each containing an adaptation window followed by a disjoint evaluation-only checkpoint. The first and last 20 units defined early and late endpoints. The temporal comparison included Frozen, Guarded EMA, and Oracle-all-genuine; matched impostor checkpoints never updated any profile.

Before any Day-2 score was loaded, the run was required to stop if training became non-finite, fewer than 16 classes occurred in Day-1 validation, validation top-1 accuracy was below 20%, or protocol-invariant tests and a synthetic smoke run did not pass. After this gate, all preprocessing, architecture, profile, attack, exclusion, and analysis choices remained fixed. These dataset-specific preprocessing and classifier choices were specified before training; the HMOG Guarded rule, attack budgets, repeat count, and update equations were not retuned to McGill.

## 3.13. Reproducibility and Protocol Freezing

The HMOG method freeze is identified by tag paper3-method-freeze-2026-10-02 at commit 476cf91; the committed external result package is identified by tag paper3-external-mcgill-v1-2026-10-03 at commit 06feb48. Machine-readable configurations record seeds, folds, attack budgets, grids, stopping rules, statistical units, and output definitions. Run manifests record source and cache hashes, execution environment, run status, and whether outer test data were loaded. The final HMOG aggregator was read-only: it consumed frozen results and performed no retraining, rescoring, adaptation, or tuning.

SHA-256 hashes were retained for consumed score caches, source files, protocol files, raw external archives, and generated outputs. The external McGill archive hash was 0e2da09c2d10fb5658c79d362e9e043a2f2822715723238b30cbebd2e7b425d9, and the locked McGill score-cache hash was 3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b. Deterministic reruns reproduced the retained McGill CSV, Markdown, and PNG outputs byte-for-byte; PDF hash changes were confined to embedded creation metadata.

Unit and protocol-invariant tests covered no-update behavior, oracle/frozen equivalence in malicious-only streams, nested budgets, split disjointness, update gating, bounded transitions, enrollment anchors, recovery isolation, state-machine behavior, and deterministic analysis. The recorded invariant suites and smoke checks completed successfully. The TQ-EMA v2 and Adaptive Quantile manifests record validation failure and outer_test_loaded=false; these stopped branches were not reopened during final aggregation.

# 4. Results

## 4.1. Poisoning Vulnerability of Blind EMA

Under the HMOG boundary attack at \(K=8\), post-poison ASR was 22.92% for Frozen and 53.96% for Blind EMA, a Blind-minus-Frozen increase of +31.04 percentage points. After averaging repeats within each fold and victim and then folds within victim, the paired subject-bootstrap 95% CI was [+26.95, +35.20] across 100 victims. The analysis contained 500 contributing fold-victim units and 49,889 eligible fold-victim-repeat paths; 111 of 50,000 possible paths lacked eight initially accepted boundary candidates. Blind ASR increased monotonically across the nested boundary budgets: 22.92%, 27.50%, 33.68%, 44.31%, and 53.96% at \(K=0,1,2,4,8\), respectively. The random attack produced a smaller increase over the same budgets, from 22.92% at \(K=0\) to 23.38%, 23.88%, 25.09%, and 27.55%. The non-primary budgets and random comparisons were exploratory. These attack-budget results are shown in Fig. 1 and summarized in Table 1.

The 22.92% Frozen value is the baseline held-out impostor acceptance at the validation-calibrated, approximately equal-error operating point. The comparison establishes additional acceptance caused by Blind adaptation under the tested protocol; it does not establish that the underlying operating point meets deployment-grade security requirements.

## 4.2. Guarded Update Authorization Suppresses Poisoning

At boundary \(K=8\), post-poison ASR was 22.92% for Frozen, 53.96% for Blind EMA, and 22.93% for Guarded EMA with \(\lambda=0.25\). Blind EMA incorporated all presented boundary poisons (MUR 100.00%), whereas Guarded EMA incorporated 1.63%. Guarded \(\lambda=0\) reproduced Blind EMA in the frozen consistency check. Guarded returning ASR near Frozen indicates suppression of the additional Blind poisoning amplification; it does not make the high-baseline operating point secure.

The complete lambda sweep was exploratory. At boundary \(K=8\), MUR decreased from 100.00% at \(\lambda=0\) to 0.13% at \(\lambda=1\), while genuine update availability in the separate replay decreased from 85.96% to 41.78%. The carried-forward \(\lambda=0.25\) result was therefore reported as a fixed security comparison rather than as a universally optimal setting (Fig. 1; Table 1).

[INSERT FIGURE 1 HERE]

**Figure 1.** HMOG post-poison attack success rate (ASR) on held-out impostor probes across nested attack budget \(K\) for (a) random and (b) score-informed boundary selection. \(K\) denotes selected poisoning attempts presented to the updater; candidate screening and reconnaissance are not counted. Frozen does not update, Blind EMA updates after accepted attack observations, and Guarded EMA uses the separate update-authorization rule with \(\lambda=0.25\). Shaded bands are descriptive 95% \(t\)-intervals across the five overlapping folds; they are not used for primary inference. The primary paired subject-bootstrap interval for boundary \(K=8\) is reported in the text.


## 4.3. Guarded EMA Does Not Preserve Clean-Drift FRR Utility

In the primary claimant-only \(D=2\) HMOG scenario, Frozen late FRR/FAR/HTER were 32.53%/22.86%/27.70%. Blind EMA yielded 32.20%/23.80%/28.00%, and Guarded EMA yielded 34.60%/21.73%/28.16% (Fig. 2).

[INSERT FIGURE 2 HERE]

**Figure 2.** HMOG security–adaptation operating points under the primary claimant-only synthetic sensitivity condition at \(D=2\). Points show subject-macro late false acceptance rate (FAR) and late false rejection rate (FRR) for Frozen, Blind EMA, Guarded EMA (\(\lambda=0.25\)), diagnostic Oracle-all-genuine, and TQ-EMA v1; horizontal and vertical bars are 95% subject-bootstrap intervals after subject-level aggregation. Lower values on both axes are preferable. The figure label “Oracle-all EMA” denotes the non-deployable Oracle-all-genuine diagnostic.


Relative to Frozen, Blind EMA had a late-FRR gain of +0.33 percentage points (95% CI [−1.20, +1.93]), a late-FAR change of +0.93 points (95% CI [−0.58, +2.64]), and an HTER gain of −0.30 points (95% CI [−1.02, +0.40]). Guarded EMA had a late-FRR gain of −2.07 points (95% CI [−3.53, −0.63]), a late-FAR change of −1.14 points (95% CI [−2.29, +0.12]), and an HTER gain of −0.46 points (95% CI [−1.16, +0.21]). Thus, the Guarded point estimate had lower late FAR but higher late FRR than Frozen; its prespecified clean-drift FRR utility was not positive.

## 4.4. Oracle-All-Genuine Isolates Feedback Censoring

Oracle-all-genuine reduced claimant-only late FRR relative to Frozen at every HMOG drift level. Late-FRR gains were +4.73 percentage points at \(D=0\) (95% CI [+3.17, +6.33]), +5.10 points at \(D=1\) (95% CI [+3.40, +6.80]), and +6.60 points at \(D=2\) (95% CI [+4.90, +8.40]).

The corresponding late-FAR changes were +5.51 points (95% CI [+3.79, +7.40]), +5.67 points (95% CI [+3.85, +7.71]), and +6.08 points (95% CI [+4.20, +8.16]). HTER gains remained small: −0.39 points at \(D=0\) (95% CI [−1.22, +0.42]), −0.28 points at \(D=1\) (95% CI [−1.26, +0.65]), and +0.26 points at \(D=2\) (95% CI [−0.59, +1.09]). Each HTER interval included zero.

The Oracle-all effect was already present at \(D=0\): late FRR was 4.73 percentage points lower than Frozen while late FAR was 5.51 points higher. Thus, part of the Oracle contrast reflects movement of the operating point when all genuine observations are allowed to lower the profile, rather than recovery uniquely attributable to synthetic drift.

The claimant-only \(D=2\) trajectories also differed in direction. Across the five retained checkpoints, the Guarded profile mean and threshold moved upward, while both Oracle-all quantities moved downward. Guarded update rate decreased from 63.47% at the first checkpoint to 51.68% at the fifth; Oracle-all update rate remained 100%. These trajectories are shown in Fig. 3.

[INSERT FIGURE 3 HERE]

**Figure 3.** HMOG profile trajectories under claimant-only synthetic sensitivity shift at \(D=2\). Panels show change from enrollment in (a) profile mean and (b) authentication threshold, together with (c) genuine update rate, across five session checkpoints for Guarded EMA (\(\lambda=0.25\)) and Oracle-all-genuine. Lines are subject-level averages and shaded bands are 95% subject-bootstrap intervals. Oracle-all uses ground-truth genuine update eligibility and is diagnostic rather than deployable.
 Oracle-all changed genuine tracking in this label-aware diagnostic while incurring a higher FAR; it was not evaluated as a deployable method or a formally optimal adaptation path.

## 4.5. TQ-EMA v1

In claimant-only \(D=2\), TQ-EMA v1 produced late FRR/FAR/HTER of 33.43%/20.92%/27.18%, compared with 32.53%/22.86%/27.70% for Frozen. The paired late-FRR gain was −0.90 percentage points (95% CI [−1.80, 0.00]); the prespecified FRR recovery criterion was therefore not met. The late-FAR change was −1.94 points (95% CI [−2.46, −1.43]), and HTER improved by +0.52 points (95% CI [+0.10, +0.94]). The two-way victim-by-impostor-source FAR bootstrap gave a similar −1.94-point estimate (95% CI [−2.48, −1.42]).

Across the \(D=2\) event audit, TQ-EMA v1 applied 1,404 trusted updates and 49 confirmed recovery updates. The method remained on the lower-FAR, higher-FRR side of Frozen in Fig. 2. Its primary late-FRR recovery criterion was not met, and the branch was stopped (Table 1).

## 4.6. TQ-EMA v2 Validation Stopping

TQ-EMA v2 completed its fold-specific validation grids before any outer test score was loaded. No fold showed a positive selected validation late-FRR gain. Fold 4 had no configuration satisfying both the +1.0-percentage-point late-FAR limit and the +0.5-point HTER-degradation limit; its best late-FRR gain over the full grid was −4.55 points, and the minimum HTER degradation was +0.89 points. The fail-closed stopping rule was triggered. The manifest records validation failure and outer_test_loaded=false, so no TQ-EMA v2 outer-test result is reported.

## 4.7. Adaptive Quantile Validation Stopping

No value in the frozen \(\rho\in\{0.80,0.90,0.95\}\) grid satisfied the Accepted-only Quantile validation gate in any of the five folds. At the descriptively least-bad value, \(\rho=0.95\), Accepted-only Quantile had mean late-FRR gain −10.64 percentage points, late-FAR change −4.89 points, and HTER change +2.87 points relative to Frozen.

At the same \(\rho\), Oracle-all Quantile had mean late-FRR gain −4.62 points, late-FAR change −1.83 points, and HTER change +1.39 points relative to Frozen. Its late FRR was lower than that of Accepted-only Quantile, but both quantile regimes remained worse than Frozen on the validation late-FRR endpoint. The branch stopped at validation in all five folds; outer test scores were not loaded, and no outer quantile estimate is reported.

[INSERT TABLE 1 HERE]

**Table 1.** Summary of HMOG poisoning security, claimant-only \(D=2\) adaptation utility, and protocol decisions for Blind EMA, Guarded EMA, Oracle-all-genuine, TQ-EMA v1, TQ-EMA v2, and the Adaptive Quantile Profile. Positive late-FRR gain denotes lower late FRR than Frozen; validation-stopped methods have no outer-test estimate.


## 4.8. External Replication on McGill Gait

The fixed Day-1 McGill classifier attained 58.12% validation top-1 accuracy and passed the prespecified 20% viability gate before Day 2 was loaded.

Under the Day-2 boundary attack at \(K=8\), held-out ASR was 12.37% for Frozen, 32.09% for Blind EMA, and 12.48% for Guarded EMA. The paired Blind-minus-Frozen effect was +19.72 percentage points (95% CI [+5.58, +37.34]), and the Guarded-minus-Blind effect was −19.62 points (95% CI [−37.17, −5.60]). Blind MUR was 100.00%, whereas Guarded MUR was 32.22%; the paired Guarded-minus-Blind MUR difference was −67.78 points (95% CI [−84.30, −49.47]). Boundary \(K=8\) retained 1,456 of 2,000 possible victim-repeat paths across 18 victims; 544 paths lacked eight initially accepted boundary candidates and were recorded as feasibility exclusions. The boundary \(K=0\) baseline used the same maximum-budget-feasible cohort. Random selection retained all 2,000 paths across all 20 subjects.

The 12.37% Frozen boundary baseline was produced by the fixed Day-1 validation-calibrated minimum-HTER threshold. As in HMOG, Guarded returning ASR near this baseline indicates suppression of additional poisoning amplification, not deployment security at a prespecified low-FAR target.

The random \(K=8\) effect was smaller. Blind-minus-Frozen ASR was +1.51 points across 20 subjects, and its 95% CI [−0.09, +4.43] included zero. The poisoning results are shown in Fig. 4 and Table 2.

[INSERT FIGURE 4 HERE]

**Figure 4.** McGill two-day mechanism-level replication of held-out post-poison ASR across nested attack budget \(K\) for random and score-informed boundary selection. Day-2 poisoning and probe identities are disjoint, and all profile states are frozen before probe evaluation. Guarded EMA uses \(\lambda=0.25\), transferred from the HMOG reporting comparison without Day-2 tuning. \(K\) denotes selected poisoning attempts presented to the updater; candidate screening and reconnaissance are not counted.


For the Day-2 temporal analysis, Frozen late FRR/FAR were 78.00%/11.46%, Guarded values were 81.00%/10.29%, and Oracle-all values were 12.75%/75.05%. The corresponding late HTER values were 44.73%, 45.64%, and 43.90%. Guarded-minus-Frozen late FRR was +3.00 points (95% CI [0.00, +7.00]). Oracle-all-minus-Frozen late FRR was −65.25 points (95% CI [−83.75, −45.50]), while Oracle-all-minus-Guarded late FAR was +64.76 points (95% CI [+48.93, +79.24]). These results are reported as a mechanism-level external replication, not as a state-of-the-art McGill performance benchmark (Figs. 5 and 6).

[INSERT FIGURE 5 HERE]

**Figure 5.** McGill Day-2 security–adaptation operating points for Frozen, Guarded EMA, and Oracle-all-genuine. Points show subject-macro late FAR and late FRR across the 20-subject temporal cohort. Oracle-all-genuine updates from every ground-truth genuine adaptation observation and is a non-deployable diagnostic. Absolute error rates are interpreted within McGill and are not directly compared with HMOG performance.


[INSERT FIGURE 6 HERE]

**Figure 6.** McGill Day-2 temporal trajectories across 80 chronological adaptation–checkpoint units. Panels show profile mean, authentication threshold, evaluation-only checkpoint FRR, and update rate for Frozen, Guarded EMA, and Oracle-all-genuine. Adaptation observations precede disjoint checkpoints, and matched impostor checkpoints never update the profiles. The figure is retained separately from Fig. 5 because it displays the temporal mechanism rather than only the final operating point.


[INSERT TABLE 2 HERE]

**Table 2.** Paired subject-bootstrap effects for the McGill two-day replication. Effects are defined as method A minus method B and reported in percentage points with 95% percentile-bootstrap intervals. Boundary \(K=8\) contrasts use the 18 eligible victims, whereas the random-attack and temporal contrasts use all 20 subjects.


## 4.9. Summary Across Datasets

Across HMOG and McGill, the score-informed boundary benchmark increased Blind EMA post-poison ASR, and the transferred Guarded update-authorization rule reduced the additional post-poison ASR toward the corresponding Frozen value. These comparisons were made at validation-calibrated operating points and do not establish low-FAR deployment performance. In the temporal evaluations, accepted-only Guarded adaptation did not produce lower late FRR than Frozen. The label-aware Oracle-all intervention changed genuine tracking in both datasets, together with higher FAR. Table 1 and Table 2 summarize the observed within-dataset effects and their stated inferential status.

# 5. Discussion

## 5.1. Principal Findings

The principal contribution is a protocol-controlled characterization of one accepted-only feedback loop with two coupled effects. On the malicious-inclusion side, impostor observations that passed authentication could modify the state used for future decisions. On the genuine-evidence side, rejected claimant observations were censored from the adaptive stream. Blind EMA exposed the first pathway; a separate Guarded update threshold sharply reduced the additional poisoning amplification but did not preserve late-FRR utility under claimant-only downward score shift.

The clean-drift controls locate the tension in the feedback available to the updater. Accepted-only policies observe a selected subset of genuine behavior because rejected genuine observations cannot enter the production profile. Oracle-all-genuine removed that censoring and followed the downward claimant-score shift more closely, but its threshold movement incurred a substantial FAR cost and did not yield a clear HTER advantage. TQ-EMA v1, TQ-EMA v2, and the Adaptive Quantile Profile did not establish useful recovery within their prespecified constraints. The McGill experiment reproduced the directions of the main poisoning, Guarded-defense, and feedback-censoring effects under an independent two-day protocol. Together, these findings do not identify a complete adaptive solution; they show that update security and legitimate drift recovery cannot be assessed independently under the tested protocols.

## 5.2. Poisoning Risk in Accepted-Only Online Adaptation

Blind EMA uses a single decision to authorize both access and learning. Once an impostor score exceeds the current authentication threshold, the observation is treated as eligible evidence about the claimant. The resulting state change affects the threshold applied to later attempts. Under the score-informed boundary strategy, held-out future impostor probes were accepted more frequently as the poisoning budget increased (Fig. 1).

The poison/probe separation is central to this interpretation. Attack candidates were selected only from the poisoning pool, while ASR was measured on a disjoint pool of source-session groups after adaptation had stopped. The observed increase therefore cannot be attributed to evaluating the exact observations used to poison the profile. Because Frozen and the malicious-update-blocking Oracle received the same scores without changing state, their agreement further isolates online profile modification as the relevant experimental difference.

The boundary strategy was intentionally stronger than uniform random selection. It assumed claimant-score access to identify already accepted observations nearest the initial boundary, whereas the random attack did not target this region and produced a smaller effect. \(K\) counts the selected attempts presented for poisoning after this ranking; it excludes candidate discovery, reconnaissance, and screening. The implemented result is therefore a strong score-access benchmark, not a demonstrated eight-query or binary-feedback-only attack. It does not establish that every deployment exposes scores, supports the same candidate search, or will experience the same attack magnitude. Paper 2 identified the label-blind update pathway but did not execute a dedicated poisoning attack; the held-out Paper 3 protocol experimentally isolates that pathway \cite{Serbin2026AdaptiveLSTM}.

The operating point is equally important. HMOG Frozen ASR was already 22.92% in the primary attack cohort, and the corresponding McGill boundary baseline was 12.37%. The study identifies relative amplification caused by state updating, but it does not establish practical security of these validation-calibrated thresholds. In addition, boundary estimates condition on paths with at least eight initially accepted candidates. This feasibility requirement may overrepresent victim/path combinations with more available false accepts, although the direction and size of that selection effect cannot be established from the present analysis.

## 5.3. Guarded Update Authorization as a Security Control

Guarded EMA separates two permissions: an observation may satisfy the access threshold without being trusted to modify the profile. This two-threshold principle is prior art; here it serves as a controlled intervention on the update channel. Under boundary poisoning, the intervention substantially reduced malicious incorporation and kept future ASR near Frozen (Fig. 1).

This result supports update authorization as a useful security control for adaptive profiles. It does not establish Guarded EMA as a complete adaptation policy. The exploratory lambda sweep showed that stricter gates reduce both malicious and genuine update availability. Moreover, MUR alone is not a complete measure of contamination severity. Guarded admitted a larger fraction of malicious observations on McGill than on HMOG, yet its post-poison ASR remained close to the corresponding Frozen value. Which observations enter the profile and how far they move the state matter in addition to the fraction incorporated.

The carried-forward lambda was an exploratory HMOG reporting choice, not an untouched confirmatory or universally optimized constant. Its effect depends on the score distribution, enrollment profile, and deployment conditions. The defensible conclusion is narrower: under both frozen protocols, a distinct update-authorization condition reduced the *additional* Blind poisoning effect without changing the access rule. Returning to the Frozen ASR does not mean that the underlying Frozen operating point is secure.

## 5.4. Selective-Update Bias Caused by Accepted-Only Feedback Censoring

The central adaptation problem is that the updater controls its own future evidence. During a downward genuine-score shift, some genuine observations fall below the authentication threshold. An accepted-only policy excludes those observations from learning and retains a stream enriched for higher genuine scores. Its adaptive state is therefore estimated from a selected upper subset rather than from the full claimant distribution. This process is referred to here as selective-update bias caused by accepted-only feedback censoring. Selective-label, pseudo-label confirmation-bias, and performative-prediction studies provide analogous context rather than direct biometric evidence \cite{Lakkaraju2017SelectiveLabels,Arazo2020ConfirmationBias,Perdomo2020PerformativePrediction}.

The HMOG trajectories are consistent with this mechanism. Under claimant-only drift, the Guarded profile mean and threshold moved upward, even though the diagnostic Oracle-all state moved downward when all genuine adaptation observations were retained (Fig. 3). The gate protected the profile from low-confidence evidence, but it also removed precisely the evidence needed to represent a downward claimant shift. The resulting late-FRR pattern is consistent with a threshold that does not follow the full genuine-score distribution.

This interpretation is mechanism-specific rather than universal. The experiments concern short chronological streams, claimant softmax scores, and the tested profile rules. They do not establish a general theorem that every accepted-only biometric updater must drift upward or that all forms of confidence gating worsen FRR. They show that, in the evaluated protocols, authentication-conditioned observation created a systematic difference between the distribution presented to the updater and the distribution used to evaluate genuine access.

## 5.5. What the Oracle-All Control Shows—and What It Does Not

Oracle-all-genuine is a label-aware information-availability intervention. It preserves ordinary authentication decisions but permits every ground-truth genuine adaptation observation to update the state, including observations that the production system rejected. Its lower late FRR and downward profile trajectory indicate that the EMA moments respond differently when rejected genuine evidence is restored. Oracle-all is not a formal upper bound on useful or secure adaptation.

This comparison supports accepted-only censoring as a contributor to the weak recovery of Blind and Guarded EMA. It does not show that unrestricted EMA is a usable or correct adaptation path. Oracle-all requires labels that are unavailable during ordinary deployment, and its lower FRR was accompanied by a substantial increase in FAR. Even at \(D=0\), Oracle-all lowered late FRR by 4.73 percentage points while increasing late FAR by 5.51 points relative to Frozen. Part of the Oracle effect therefore reflects operating-point movement and threshold relaxation rather than recovery uniquely caused by synthetic drift. HTER changed little because the FRR and FAR movements opposed one another. Oracle-all is evidence about trajectory sensitivity to information availability, not a deployable baseline that should be selected on aggregate error.

The control also narrows the interpretation of the negative recovery results. EMA was not entirely incapable of moving with the synthetic claimant shift or the McGill day change. Rather, useful movement depended on access to observations that deployable accepted-only policies could not safely trust.

## 5.6. Why Recovery Mechanisms Did Not Restore Utility

TQ-EMA v1 created an isolated route through which rejected but near-boundary observations could contribute recovery evidence without receiving access. Its event audit nevertheless contained far fewer confirmed recovery updates than trusted high-score updates. The resulting operating point was more conservative and satisfied the safety constraints, but the method did not meet the prespecified late-FRR recovery criterion. This outcome is consistent with a recovery signal that was too infrequent to offset the dominant accepted-high-score stream; it does not establish that every quarantine design is ineffective.

TQ-EMA v2 addressed that specific imbalance by suppressing trusted updates that opposed a confirmed downward recovery episode. The fold-specific validation gate was not satisfied, so the protocol stopped before outer scores were opened. This is evidence about the frozen v2 controller under its fixed constraints, not an outer-test estimate and not a basis for post-hoc relaxation of those constraints.

The quantile branch tested whether changing the adaptive state, rather than only its admission gate, would improve recovery. Oracle-all Quantile reduced the gap associated with accepted-only censoring, but neither information regime outperformed Frozen on the validation recovery endpoint. This pattern indicates that censoring was an additional cost but not the only difficulty for the tested q20/q50 representation. The combined evidence suggests that both update admission and score-state dynamics matter when adaptation is based on short, noisy temporal streams.

These negative branches narrow the set of explanations supported by the tested implementations and prespecified parameter ranges. They do not reject quarantine, temporal evidence, or robust distribution tracking as general method families. They show that the frozen implementations did not provide evidence of useful recovery under the stated security and HTER constraints.

## 5.7. Security–Adaptation Trade-off

The trade-off figure summarizes why no tested score-level method produced a free adaptation gain (Fig. 2). Permissive learning exposes a larger poisoning surface because more authenticated observations can influence future thresholds. Conservative accepted-only learning reduces that exposure but increasingly conditions adaptation on already high scores. Oracle-all occupies the opposite extreme: it responds strongly to claimant change because it observes all genuine candidates, but its unrestricted downward movement increases false acceptance.

This trade-off is observed under the present score generators, streams, and constraints; it is not an impossibility result for adaptive authentication. A system with trusted external evidence, richer temporal structure, or feature-level adaptation may occupy a different operating region. The present experiments nevertheless show why adaptation utility should not be evaluated only on genuine recovery and why poisoning resistance should not be evaluated only on malicious update counts.

HTER is useful as a balanced summary, but it can obscure the security meaning of opposing FAR and FRR movements. A decrease in FRR obtained by a comparable increase in FAR may leave HTER almost unchanged while materially changing the risk profile. FAR, FRR, ASR, update rates, and state movement should therefore remain visible as separate endpoints, with deployment-specific costs assigned before method selection.

## 5.8. External Replication on McGill Gait

McGill altered several conditions simultaneously: it contained fewer subjects, used accelerometer-derived channels without gyroscope, used a different fixed classifier, and provided a real separation between collection days rather than synthetic feature shift. The Day-1/Day-2 difference is not an isolated estimate of behavioral drift; it may combine behavior, activity, device placement, acquisition conditions, context, and model-transfer effects. Despite these differences, the main feedback directions reproduced. Boundary poisoning increased Blind EMA ASR relative to Frozen, and the transferred Guarded rule reduced both contamination and the additional post-poison ASR toward Frozen (Fig. 4).

The temporal comparison showed the same qualitative tension. Guarded did not improve late FRR relative to Frozen, whereas Oracle-all changed genuine tracking substantially and incurred a very large FAR cost (Figs. 5 and 6). This replication provides independent evidence that the same directional mechanisms can arise outside the HMOG protocol.

The replication does not support direct comparison of absolute HMOG and McGill error rates. Day-2 Frozen FRR on McGill was high, indicating a severe cross-day shift and weak absolute transfer of the fixed Day-1 classifier. The small cohort, missing gyroscope, boundary feasibility exclusions, and dataset-specific preprocessing further limit performance generalization. McGill is therefore evidence of mechanism-level reproducibility under a difficult two-day setting, not a benchmark claim about classifier quality.

## 5.9. Implications for Adaptive Behavioral Authentication

First, authentication confidence and update authorization should be treated as distinct design decisions. A separate update-authorization layer can reduce contamination even when the access rule itself is unchanged. This separation should be treated as a security boundary in adaptive-system design.

Second, the data observed by an online updater may be endogenous to its current threshold. Monitoring only accepted observations can hide the genuine behavior that the system most needs to recover. Evaluation should therefore audit rejected near-boundary genuine observations, update eligibility, and profile trajectories rather than reporting only aggregate acceptance rates.

Third, practical recovery requires evidence that is at least partly independent of the original access decision. Candidate sources include trusted step-up authentication, temporally consistent multi-session evidence, device or context signals, and multimodal corroboration. Such signals should authorize bounded recovery without retroactively granting access to rejected attempts.

Fourth, score-only location and scale updates may be insufficient under substantial temporal shift. Feature-level or model-level adaptation, explicit drift detection, and representations that separate claimant change from impostor overlap are justified research directions, but they require the same poisoning-aware controls as score-profile adaptation.

Finally, security and utility should be evaluated jointly. A useful protocol should measure held-out post-update attack success, genuine temporal recovery, FAR, update composition, and state displacement on the same frozen design. Rollback, rate limiting, anchors, and bounded movement remain relevant safeguards, but their value should be assessed against both adversarial contamination and legitimate drift.

## 5.10. Limitations

The HMOG temporal experiment used synthetic standardized-feature sensitivity levels that were not empirically calibrated to natural drift magnitudes. It was designed to expose score-profile dynamics under a controlled downward claimant condition, not to reproduce natural long-term behavioral evolution. The global scenario also shifts impostor observations, while the primary claimant-only scenario holds impostor scores at baseline. Neither construction captures all changes in sensor placement, activity, device state, health, environment, or user behavior that may occur in deployment.

The same overall HMOG outer score caches were reused across sequential exploratory branches. Although each branch used frozen rules and the validation-stopped methods did not access outer scores, the broader development sequence was informed by earlier observations from those caches. Later HMOG branches should therefore be treated as exploratory mechanism studies rather than independent confirmatory tests. The stopped TQ-EMA v2 and Quantile branches have no outer estimates, and TQ-EMA v1 was not evaluated in a combined drift-plus-poisoning experiment.

The boundary attacker had score-informed candidate selection. It is stronger than a purely binary-feedback attacker and may not match deployments that hide confidence scores, constrain queries, or aggregate decisions differently. Candidate discovery and screening were not charged to \(K\), total query cost was not measured, and a binary-feedback-only route to the ranked candidates was not demonstrated. Conversely, the experiments did not cover replay, sensor injection, model extraction, collusion, gradient-based attack, or compromised operating-system components. The results characterize the online profile-update surface defined in the threat model, not all attacks against mobile behavioral authentication.

Dataset coverage remains limited. HMOG was the single primary mechanistic dataset. McGill added an independent two-day replication but contained only 20 subjects, accelerometer-only inputs, no gyroscope, and a severe Day-2 shift. HMOG boundary results used 49,889 of 50,000 possible paths; McGill boundary results used 1,456 of 2,000 paths across 18 of 20 victims. These exclusions condition the estimates on sufficient initially accepted candidates and can introduce feasibility-selection bias. These properties restrict population-level and modality-level generalization.

The model scope was also narrow. The study adapted claimant softmax-score profiles generated by fixed LSTMs; it did not adapt features, representation layers, or classifier weights online. It did not compare multiple modern sequence encoders or evaluate whether calibrated likelihood ratios, embeddings, or uncertainty-aware scores would change the trade-off. No production smartphone deployment measured end-to-end latency, memory, energy, or user burden associated with recovery and step-up decisions.

Statistical inference was constrained by the available design. HMOG folds had overlapping fitting partitions and were used descriptively. The primary poisoning interval resampled victim-level effects after within-victim aggregation and therefore did not treat folds or Monte Carlo paths as independent. However, the retained HMOG outcome file did not preserve impostor-source contributions, so a victim-by-source bootstrap for the primary poisoning contrast was infeasible. Subject bootstrap intervals summarize the retained cohort rather than a universal deployment population, and McGill had only 18–20 subject clusters. Validation-stopped branches cannot support claims about outer performance. These limitations preclude universal performance or impossibility claims and motivate independent confirmation on larger untouched longitudinal cohorts.

## 5.11. Future Work

The next priority is independent evaluation on larger multi-day datasets with natural longitudinal change, preserved chronology, multiple inertial modalities, and enough identities to support both victim- and impostor-source uncertainty. Such protocols should jointly measure adaptation utility and poisoning resistance rather than separating them into unrelated benchmarks. This direction is consistent with the longitudinal and adversarial-evaluation gaps documented in Paper 1 \cite{Gali2026SystematicReview}.

Method development should focus on trusted recovery evidence rather than broader parameter sweeps of the stopped branches. Step-up authentication, secure user-presence signals, temporally separated corroboration, and multimodal context could provide labels or confidence that are less dependent on the current biometric threshold. Their use should remain bounded, auditable, rate-limited, and reversible.

A second direction is to move beyond scalar score-profile adaptation. Drift-aware embedding updates, feature normalization, uncertainty-aware state models, and explicit change-point detection may represent claimant change without forcing a single threshold to absorb both distribution shift and security risk. These methods should be evaluated under held-out poisoning, natural drift, and combined drift-plus-attack streams with parameters fixed before outer testing.

Finally, longer field studies are needed to measure persistence, recovery time, user friction, and systems cost. A deployable evaluation should include rollback behavior, step-up frequency, on-device resource use, and the consequences of abrupt legitimate change. These studies would test whether the mechanisms observed here remain relevant when adaptation interacts with real user behavior and operational constraints.

# 6. Conclusion

Online adaptation turns operational decisions into inputs to the future authentication state. This study characterized one accepted-only feedback loop with two coupled effects: malicious inclusion when accepted impostor observations alter the profile, and genuine-evidence censoring when rejected claimant observations are excluded from adaptation. The evaluation combined a controlled HMOG mechanism study with an independent two-day McGill directional replication rather than treating poisoning security and adaptation utility as separate tasks.

The poisoning experiments showed that Blind EMA was vulnerable to the score-informed boundary benchmark. At the maximum tested budget, \(K=8\), HMOG post-poison ASR increased from 22.92% for Frozen to 53.96% for Blind EMA; the paired subject-level increase was +31.04 percentage points (95% CI [+26.95, +35.20]). Because attack candidates and future probes were separated before selection and the profile was frozen before probe evaluation, this increase reflects a change in later decisions rather than reuse of the poisoning observations. Guarded EMA retained the access rule while imposing a separate update-authorization condition; its ASR was 22.93% in the same comparison, and the corresponding direction was reproduced on McGill. The boundary strategy assumed score access, and \(K\) excluded candidate screening and reconnaissance; a binary-feedback-only attack was not demonstrated. The approximately equal-error HMOG threshold and the McGill minimum-HTER threshold were validation-calibrated research operating points rather than deployment-grade low-FAR targets. Guarded therefore suppressed the additional Blind poisoning amplification relative to Frozen; it did not establish that the underlying system was secure.

The clean temporal experiments exposed the complementary adaptation cost. During the controlled HMOG claimant-only sensitivity shift, accepted-only policies excluded rejected genuine observations from learning and retained a higher-scoring subset. Guarded profile trajectories therefore did not follow the full genuine-score movement, and Guarded did not preserve positive late-FRR utility relative to Frozen. The label-aware Oracle-all information-availability intervention restored every genuine adaptation observation and changed the profile trajectory in the downward direction. In claimant-only HMOG at \(D=2\), it lowered late FRR by 6.60 percentage points relative to Frozen, but late FAR increased by 6.08 points. The Oracle effect was also present at \(D=0\), so it partly reflects operating-point movement rather than recovery uniquely caused by synthetic drift. Oracle-all is non-deployable and not a formal upper bound; it supports accepted-only feedback censoring as a contributor to weak recovery, not a uniquely correct adaptation path.

The prespecified recovery/state probes did not identify a deployable resolution within their frozen designs. TQ-EMA v1 did not meet its late-FRR recovery criterion. TQ-EMA v2 and the Adaptive Quantile Profile did not satisfy their validation gates, so outer test scores were not loaded and no outer estimates exist for those methods. These stopped branches are supporting negative evidence rather than headline algorithmic contributions. The McGill experiment reproduced the directions of the boundary-poisoning, update-authorization, and Oracle feedback effects under a different classifier, accelerometer-only inputs, and real Day-1/Day-2 separation. That cross-day shift can combine behavior, context, placement, acquisition, and model-transfer effects; it is a small mechanism-level replication, not isolated natural-drift measurement or benchmark validation.

The main implication is that access permission and learning permission should be treated as distinct design decisions. Separating them can substantially reduce malicious profile updates, yet making learning more conservative can also remove the genuine observations most needed for recovery. A practical adaptive authenticator may therefore require trusted recovery evidence that is not determined solely by the current access decision, together with bounded state movement and explicit monitoring of FAR, FRR, update composition, and future attack success. Larger untouched multi-day studies should evaluate such evidence, including step-up or multimodal corroboration and feature- or model-level adaptation, under benign temporal change and adversarial contamination in the same frozen protocol. The present findings define this joint evaluation problem; they do not claim a universal solution or an impossibility result for adaptive behavioral authentication.

# References

[REFERENCES TO BE GENERATED FROM `references.bib` AFTER JOURNAL SELECTION]
