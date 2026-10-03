# Introduction and Related Work Audit

Audit date: 3 October 2026.

Files audited:

- `paper/introduction.md`
- `paper/related_work.md`
- `paper/literature_audit.md`
- `paper/reference_claim_matrix.md`
- `references.bib`
- `paper/paper1_paper2_fact_check.md`

## Citation Coverage

- `references.bib` contains 39 unique entries.
- Every BibTeX key cited in the Introduction and Related Work exists in `references.bib`.
- The new Introduction and Related Work contain no `[CITATION NEEDED]` placeholders.
- Primary studies are used for specific methods, datasets, attack mechanisms, and empirical settings. Surveys are used for broad field-level statements and qualified research-gap synthesis.
- General machine-learning sources are labeled as analogous where they are used to contextualize, rather than directly evidence, the biometric mechanism.

## Strong-Claim Audit

| Strong literature-derived claim | Citation(s) | Source type | Support class | Audit decision |
|---|---|---|---|---|
| Continuous mobile authentication reassesses identity beyond initial login. | `Crawford2013ContinuousFramework`; `Abuhamad2021SensorSurvey` | Primary architecture paper + survey | DIRECT / REVIEW-LEVEL | Retained with “complement” framing; no claim that it replaces all initial authentication. |
| Smartphone behavioral authentication uses touch, keystroke, gait/motion, context, and multimodal evidence. | `Mahfouz2017SmartphoneSurvey`; `Abuhamad2021SensorSurvey`; `Stylios2021MobileSurvey` | Surveys | REVIEW-LEVEL | Retained as broad taxonomy; representative systems cited separately. |
| Touch and inertial behavior can provide repeated identity evidence. | `Frank2013Touchalytics`; `Sitova2016HMOG`; `Fereidooni2023AuthentiSense` | Primary studies | DIRECT | Retained without transferring reported accuracy across protocols. |
| Behavioral evidence varies across sessions/time and motivates adaptation. | `Frank2013Touchalytics`; `Giot2011KeystrokeUpdate`; `Ryu2023AdaptiveBiometrics` | Primary studies + review | DIRECT / REVIEW-LEVEL | Retained; not universally labeled as natural concept drift. |
| Template update can be supervised or self-/semi-supervised. | `Rattani2009TemplateUpdate`; `Didaci2014UnsupervisedUpdate` | Review + direct analysis | DIRECT / REVIEW-LEVEL | Retained. |
| Self-update couples current recognition errors to future state. | `Didaci2014UnsupervisedUpdate`; direct poisoning papers | Primary/theoretical | DIRECT | Retained as mechanism, not universal outcome magnitude. |
| Separate authentication and update thresholds have prior precedent. | `Giot2011KeystrokeUpdate` | Primary study | DIRECT | Retained and used to limit novelty. |
| Adaptive biometric templates can be poisoned. | `Biggio2012PoisoningAdaptive`; `Biggio2013FacePoisoning`; `Lovisotto2020BiometricBackdoors`; `Xue2020LOPA` | Primary attack studies | DIRECT | Retained; modalities and attacker models are kept distinct from Paper 3. |
| General online learning also admits sequential poisoning formulations. | `Zhang2020OnlinePoisoning` | General ML primary study | ANALOGOUS | Retained only with explicit non-biometric qualification. |
| Selective decisions can determine which labels/outcomes are observed. | `Lakkaraju2017SelectiveLabels` | General ML/decision primary study | ANALOGOUS | Retained as context; not equated with biometric update eligibility. |
| Self-training can reinforce pseudo-label errors. | `Arazo2020ConfirmationBias` | General ML primary study | ANALOGOUS | Retained as context; no direct biometric claim. |
| Deployed decisions can change future data distributions. | `Perdomo2020PerformativePrediction` | General ML theoretical study | ANALOGOUS | Retained with a narrower mapping than performative prediction. |
| “Selective-update bias caused by accepted-only feedback censoring” names the Paper 3 mechanism. | Paper 3 definition plus the three sources above | Paper-specific term + analogous context | PAPER-SPECIFIC | Explicitly stated not to be established terminology. |
| Reviews report limited continuous/mobile adaptive-biometric and longitudinal evaluation. | `Ryu2023AdaptiveBiometrics`; `Gali2026SystematicReview` | Systematic reviews | REVIEW-LEVEL | Retained with corpus/scope qualifications. |
| Prior work provides limited joint evaluation of poisoning resistance, temporal recovery, and feedback availability under one protocol. | Component literature plus `Ryu2023AdaptiveBiometrics`; `Gali2026SystematicReview` | Cross-literature synthesis | REVIEW-LEVEL SYNTHESIS | Retained as “limited joint evaluation”; no universal absence or firstness claim. |
| Paper 2 used accepted-only EMA, did not improve Frozen HTER, and did not run a dedicated poisoning attack. | `Serbin2026AdaptiveLSTM`; local fact-check | Primary prior paper | DIRECT, LOCALLY VERIFIED | Retained exactly within the fact-check boundary. |
| HMOG, McGill, and whuGAIT metadata/citations are correctly distinguished. | `Sitova2016HMOG`; `Frank2010McGillGaitDataset`; `Zou2020WhuGait` | Original paper / official dataset source | DIRECT | Retained. McGill exact archive facts come from its official page. |
| Threshold movement changes FAR/FRR trade-offs. | `Jain2004BiometricRecognition`; `Joshi2020AdaptiveThreshold` | Foundational + primary example | DIRECT | Retained without claiming that literature predicts Paper 3's measured trade-off. |
| Passive/context evidence can trigger stronger explicit authentication. | `Riva2012ProgressiveAuthentication`; `Hayashi2013CASA`; `Crawford2013ContinuousFramework` | Primary mobile-authentication studies | DIRECT | Retained as recovery architecture context, not as a tested Paper 3 defense. |

## Claims Softened or Excluded

| Stronger formulation | Final formulation/decision | Reason |
|---|---|---|
| “Paper 3 is the first poisoning attack on adaptive biometrics.” | Excluded. | Direct face and fingerprint poisoning studies predate Paper 3. |
| “Guarded EMA introduces a novel second threshold.” | Reframed as evaluating separate update authorization in the frozen Paper 3 protocol. | Giot et al. previously used separate acceptance and update thresholds. |
| “No prior work jointly studies security and utility.” | “The audited literature provides limited joint evaluation of held-out poisoning, genuine recovery, and feedback availability under one frozen mobile-behavioral protocol.” | The broad absence claim is not supportable. |
| “Behavioral biometrics naturally undergo concept drift.” | Reframed as session/time/context variability and linked cautiously to the broader concept-drift literature. | Not every temporal difference meets the formal concept-drift definition. |
| “McGill provides natural behavioral drift.” | “McGill provides natural day separation.” | Day effects can include behavior, context, device placement, and acquisition conditions. |
| “Selective-update bias is an established literature term.” | Explicitly introduced as Paper 3's authentication-specific term. | Exact phrase was not found in verified sources. |
| “General online poisoning proves biometric vulnerability.” | General online poisoning is labeled analogous; biometric claims rely on biometric primary studies. | Learners, observations, and attacker interfaces differ. |
| “Step-up or multimodal recovery resolves feedback censoring.” | Retained only as future-work motivation. | Not tested by Paper 3 or established by the cited sources for this mechanism. |
| “Paper 2 demonstrated poisoning.” | Explicitly excluded. | Paper 2 identified the label-blind pathway but ran no dedicated poisoning experiment. |

## Citation Placeholders and Gaps

The new Introduction and Related Work have no unresolved citation placeholders. Three placeholders remain in the previously frozen Discussion because the task authorized only three wording edits there:

1. `[CITATION NEEDED: Paper 2]` can later be replaced with `\cite{Serbin2026AdaptiveLSTM}` once Discussion citation insertion is authorized.
2. `[CITATION NEEDED: selective-label and feedback-censoring literature]` can later be replaced with a qualified combination of `\cite{Lakkaraju2017SelectiveLabels,Arazo2020ConfirmationBias,Perdomo2020PerformativePrediction}`.
3. `[CITATION NEEDED: Paper 1]` can later be replaced with `\cite{Gali2026SystematicReview}`.

No source was found that directly studies the exact accepted-only claimant-score censoring mechanism under mobile behavioral profile adaptation. This is not treated as a missing citation for an established fact; it is stated as the paper's mechanism-specific framing supported by its own controls.

## Metadata Issues

| Entry | Issue | Resolution |
|---|---|---|
| `Serbin2026AdaptiveLSTM` | Supplied proof has no final Procedia volume, pages, or DOI. | Included as an EUSPN 2026 conference manuscript/proof; no DOI or pages invented. |
| `Frank2010McGillGaitDataset` | Official dataset citation has no DOI. | Cited as an official McGill dataset webpage with access date. |
| `Frank2010ActivityGait` | Peer-reviewed companion study does not by itself document every property of the exact 20-subject two-day archive. | Archive facts use the official dataset page; the AAAI paper is not substituted for it. |
| `Bo2013SilentSense` | DOI metadata returns only the first page, while proceedings/DBLP identify pages 187--190. | Pages 187--190 retained from the official proceedings record/DBLP cross-check. |
| `Jiang2024MAUTH` | DOI was registered/available online in 2023; final volume, issue, and pagination are 2024. | Final journal year and pagination used, DOI retained. |
| `Baaqeel2022AdaptiveSpoofingSurvey` | First published online in December 2021; volume 11 issue 2 is 2022. | Bibliographic year set to 2022 with an online-publication note. |
| Author diacritics | Some DOI exports and BibTeX processors vary in Unicode handling. | Stable ASCII forms are used in keys/author fields; DOIs preserve identity. |

No duplicate BibTeX keys or duplicate DOI entries were found.

## Novelty Impact

The audit found two bodies of work that materially narrow component-level novelty:

1. `Giot2011KeystrokeUpdate` establishes prior use of distinct acceptance and update thresholds in behavioral biometric template updating.
2. `Biggio2012PoisoningAdaptive`, `Biggio2013FacePoisoning`, `Lovisotto2020BiometricBackdoors`, and `Xue2020LOPA` establish prior poisoning of adaptive biometric templates.

These papers do **not** remove the paper's narrower positioning. The supported contribution is the joint mobile-behavioral mechanism study: held-out future-probe poisoning, update authorization, clean temporal recovery, accepted-only feedback censoring, validation-stopped recovery branches, and independent two-day replication under frozen protocols. This is presented as a scoped empirical contribution, not a first-ever or universal claim.

## Final Consistency Check

- Paper 1 is used for qualified corpus-level gaps and not as a substitute for primary methods.
- Paper 2 is described according to the local fact-check and is not credited with Paper 3's attack.
- HMOG synthetic drift and McGill natural day separation remain distinct.
- Oracle-all remains explicitly diagnostic and non-deployable.
- Introduction contributions correspond to completed Paper 3 experiments, including negative validation-stopped branches.
- Introduction and Related Work contain no detailed Paper 3 result percentages and do not pre-announce the Results section.
- Methods, Results, frozen outputs, manifests, scripts, and the decision log were not modified.
