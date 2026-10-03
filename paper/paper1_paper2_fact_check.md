# Paper 1 / Paper 2 Primary-Source Fact Check

Audit completed: 2026-10-03. This document verifies prior-work facts for Paper 3. It does not modify or reinterpret any Paper 3 result.

## Source hierarchy and scope

The audit used the supplied version-of-record PDF for Paper 1, its locally available supplementary files, the supplied Paper 2 PDF, the canonical Paper 2 code, and the revised result/metadata exports. PDF and canonical code take precedence over inherited notes and older scripts. Where sources disagree, the disagreement is recorded rather than silently resolved.

Key source fingerprints:

| Source | SHA-256 |
|---|---|
| Paper 1 PDF, `technologies-14-00451-v2 (1).pdf` | `908d1ff42994c0e42c422e55315e496c7df74f74758a5ea5fbacf8f4524db1fa` |
| Paper 1 `Search_Strategy.txt` | `ffee1d0cb786061fe0c372a26f8d1ef23f20ae3f429d60452840de2d01d56e2b` |
| Paper 1 `Quality_Assessment_Scores.xlsx` | `a64114b953622079e257d41ba8df7534b0482eb525c150085a09d4b54b096aea` |
| Paper 2 PDF, `EUSPN_37.pdf` | `94bba99a66ca04ed116ad5bba5312d092cb8ddeb02e06af9be3bfb60ea8f9fb1` |
| Canonical Paper 2 code, `src/hmog_revised_experiment.py` | `3468a5a8c6d7e0e9a6ee61da1b7c4312ce46c46fc2ff1167457e1cd5be8e2210` |
| Paper 2 revised summary CSV | `f449e7fd9d58e35d733936573e272458ffef281016f169f0c2b9f58a08c1b31e` |
| Paper 2 revised by-fold CSV | `53ff7f009c8f33d38efa5bcac5bbb658a8b6f692441cd963adec2103efeb0caa` |

# Paper 1 Fact Check

## Bibliography

| Field | Verified value | Source location | Status |
|---|---|---|---|
| Title | *Behavioral Biometric Continuous Authentication for Mobile Devices with an Intelligent Personal Agent: A Systematic Review* | PDF p. 1 | Confirmed |
| Authors | Madi Gali; Aray Kassenkhan; Yersain Chinibayev; Aigerim Abshukirova; Vassiliy Serbin | PDF p. 1 | Confirmed |
| Journal | *Technologies* | PDF p. 1/footer | Confirmed |
| Year, volume, issue, article | 2026, 14(7), 451 | PDF p. 1 gives `2026, 14, 451`; issue 7 is confirmed by the [official MDPI article record](https://www.mdpi.com/2227-7080/14/7/451) | Confirmed |
| DOI | `10.3390/technologies14070451` | PDF p. 1 and footer | Confirmed |
| Article type | Open-access systematic review | PDF p. 1 | Confirmed |
| Dates | Received 9 June 2026; revised 8 July 2026; accepted 15 July 2026; published 22 July 2026 | PDF p. 1 | Confirmed |

Canonical citation:

> Gali, M., Kassenkhan, A., Chinibayev, Y., Abshukirova, A., & Serbin, V. (2026). Behavioral Biometric Continuous Authentication for Mobile Devices with an Intelligent Personal Agent: A Systematic Review. *Technologies, 14*(7), 451. https://doi.org/10.3390/technologies14070451

## Methodology

- The review states that it followed a PRISMA 2020-style/compliant selection process, but it was **not prospectively registered** and no formal protocol was published in advance (PDF p. 48, Section 3).
- Database queries ran from September 2025 through January 2026. Screening, eligibility assessment, backward snowballing, and forward citation tracking continued through April 2026 (PDF pp. 49–50 and 58, Sections 3.2 and 3.5; `Search_Strategy.txt`).
- Six databases were searched: Scopus, Web of Science Core Collection, IEEE Xplore, ACM Digital Library, ScienceDirect, and SpringerLink (PDF pp. 48–50 and 64–65; `Search_Strategy.txt`). Searches were restricted to title, abstract, and keyword fields.
- Five Boolean query families covered core continuous authentication, intelligent personal agents, biometric modalities plus ML, privacy-preserving mechanisms, and IoT/wearable contexts (PDF pp. 49–50; `Search_Strategy.txt`).
- The stated eligibility window was 2017–2025, English, peer-reviewed journal/conference/review articles, with topical and quality requirements. The final corpus also includes one older, snowballed 2015 study (PDF pp. 52–54 and 63–64).
- Two reviewers independently screened records; disagreements were resolved by discussion or third-reviewer adjudication (PDF pp. 57–58; `Search_Strategy.txt`). The paper does not report a numeric inter-rater reliability statistic for its own screening.
- Quality was assessed with five criteria scored 0–2: objective clarity, empirical/system grounding, performance reporting, methodological description, and contextualization. Criteria 1 and 2 were gatekeeping criteria (PDF pp. 55–56, Section 3.4).

PRISMA accounting is internally arithmetically consistent:

| Stage | Count | Source |
|---|---:|---|
| Records identified | 1,744 | PDF pp. 64–65, Figure 6; `Search_Strategy.txt` |
| Duplicates removed | 1,364 | Same |
| Title/abstract records screened | 380 | Same |
| Excluded at title/abstract | 70 | Same |
| Full texts assessed | 310 | Same |
| Full texts excluded | 230 | Same |
| Exclusion reasons | 100 insufficient rigor; 30 non-peer-reviewed; 100 duplicate/overlapping reports | Same |
| Included studies | 80 | Same |

## Dataset / Corpus

- The final corpus contains 80 works: 53 primary empirical/system-level studies and 27 systematic, narrative, or scoping reviews retained for taxonomy and methodological precedent (PDF pp. 54–55; `Search_Strategy.txt`; `Quality_Assessment_Scores.xlsx`).
- The quality workbook contains 80 rows and independently reproduces the paper's tier totals: 32 High, 44 Moderate, and 4 Low; all 80 pass the two gatekeeping criteria (PDF p. 56; `Quality_Assessment_Scores.xlsx`, sheets `Quality Scores` and `Summary`).
- The 27 review-type works are not original performance studies and should not be described as such. The paper says they are excluded from quantitative performance pooling/comparison (PDF pp. 54–55).

### Supplementary inconsistencies that must remain visible

1. The main PDF's yearly distribution (PDF pp. 63–64) does not match `Included_Studies_Reference_List.csv`. The PDF reports 2020/2021/2022/2023/2024/2025/2019 counts of 18/16/15/14/6/4/5, while the CSV yields 17/16/17/14/5/5/4. Both sum to 80. Therefore Paper 3 should cite only the broad coverage period and total corpus size, not the per-year histogram, until the supplementary list and Figure 4 are reconciled.
2. `Search_Strategy.txt` says that a 2019 study falls outside a 2017–2025 window. That is impossible. The main PDF and included-study CSV identify the out-of-window item as a 2015 study. Treat `2019` in the search supplement as a stale error.
3. `data_extraction_tables.md` labels two studies (`Lopez et al. (2021)` and `El-Kenawy et al. (2022)`) as missing from `Quality_Assessment_Scores.xlsx`. Therefore the extraction table is not a fully reconciled per-study key, even though the aggregate 53/27 and 80-study counts are confirmed elsewhere.
4. PDF p. 58 calls the corpus “80 high-quality papers,” but the declared quality distribution includes 44 Moderate and 4 Low studies. Paper 3 should use “80 included studies,” not “80 high-quality studies.”

These discrepancies do not invalidate the six-database search, PRISMA counts, 80-study total, 53/27 split, or 32/44/4 quality totals. They do prevent treating every supplementary per-study/year mapping as fully reconciled.

## Main Findings

### Research questions

The five research questions are stated in Section 1.1 (PDF pp. 5–7):

1. Performance and modality choice, including multimodal fusion.
2. Usability and user acceptance.
3. Security, privacy, and threat models.
4. Deployment constraints, cost, and temporal dynamics.
5. Application domains and IPA integration.

### Behavioral modalities

The four behavioral branches emphasized by the review are keystroke dynamics, touch/swipe interaction, gait/motion sensing, and contextual data (PDF pp. 7–8 and Sections 2.4.1–2.4.4). The review also discusses multimodal combinations and adjacent physiological modalities, but these should not be confused with its four-part behavioral taxonomy.

### Machine-learning methods

The review covers classical classifiers and feature-based ML, including SVM, kNN, random forest, and related methods; deep architectures including CNNs, RNN/LSTMs, hybrid models, and transformers; and emerging approaches including federated learning, self-supervision, and privacy-aware/distributed learning (Sections 2.6.1–2.6.3; Table 8 on PDF p. 63). Table 8 is a multi-label method distribution, so its counts exceed 80 and are not mutually exclusive.

### Security, privacy, and agent mechanisms

- Attacks discussed include spoofing/presentation attacks, mimicry, adversarial and generative attacks, reconstruction/sample inference, membership inference, model inversion/extraction, deanonymization, and federated/client poisoning or backdoors (Abstract; Sections 2.3.2, 2.7, and 5.2).
- The paper discusses poisoning as part of the threat landscape, particularly for federated/client and agent/tool contexts. It does **not** report a new poisoning experiment of its own.
- Privacy/security mechanisms include cancelable biometrics, Bloom-filter encodings, zero-knowledge proof protocols, federated learning, secure aggregation/local processing, blockchain identity management, and TEE-supported device–edge–cloud architecture (Abstract; Sections 1.2, 2.5, 2.7, and 6).
- IPA integration is primarily a synthesis and reference-architecture contribution: agents mediate modality choice, risk/context monitoring, step-up decisions, privacy policy, provenance, and device/edge/cloud data flow. It is not evidence that a deployed commercial BBCA+IPA system was empirically validated (Sections 1.1–1.2, 2.5, and 5.1).

## Research Gaps

| Working formulation | Verdict | Exact supported interpretation | Source location |
|---|---|---|---|
| No end-to-end evaluation under simultaneous adversarial and privacy threat models | **Confirmed** | The review explicitly states that no published study evaluates the complete path from sensing through feature extraction/template protection to decision under both threat-model classes at once. This is a corpus-level review conclusion, not proof of universal absence outside the search scope. | Abstract; Section 1.2, PDF p. 7; Section 5.2, PDF p. 70 |
| No standardized adversarial benchmarks | **Confirmed** | The paper identifies the absence of standardized adversarial benchmarks and, more specifically, no benchmark combining realistic attacks, longitudinal enrollment, and energy/latency measurement. | Abstract; Section 1.2, p. 7; Section 5.2, p. 70 |
| Insufficient longitudinal/ecologically valid studies | **Confirmed** | The review reports short controlled cohorts, limited long-term temporal variability, and a scarcity of ecologically valid, built-in mobile-sensor studies. | Section 2.4/Table 3 discussion, pp. 27–28; Section 5.2, pp. 69–70; Conclusion, p. 77 |
| Weak empirical integration of behavioral biometrics with IPA | **Partially confirmed** | The paper says prior surveys and empirical work rarely integrate BBCA and IPA/agent architectures and reports no evaluated deployed commercial system spanning the full intersection. “Weak empirical integration” is safe; “no integration exists” is too strong. | Introduction, pp. 3–5; Sections 1.1–1.2, pp. 5–7; Section 5.1, pp. 66–68; Section 5.2, p. 70 |
| User-centered privacy/consent gap | **Confirmed** | The review explicitly states that user acceptance of cancelable biometrics, ZKP, or federated privacy mechanisms has not been tested, despite known privacy concerns and response costs. | Abstract; Section 1.2, p. 7; Section 5.2, p. 70 |

## Confirmed Wording for Paper 3

Safe wording:

> Paper 1 systematically reviewed 80 studies (53 empirical/system-level studies and 27 reviews) retrieved through a six-database PRISMA-style process. It identified limited standardized adversarial evaluation, a lack of complete pipeline studies that jointly evaluate adversarial and privacy threats, scarce longitudinal and ecologically valid evidence, limited empirical integration with intelligent personal agents, and an unresolved user-centered consent/acceptance gap for privacy-preserving mechanisms.

Required qualifications:

- Say “primarily 2017–2025, plus one snowballed 2015 study,” not simply “all studies were from 2017–2025.”
- Say “80 included studies,” not “80 empirical studies” or “80 high-quality studies.”
- Frame “no study” conclusions as findings **within the review's searched corpus and protocol**.
- Do not claim that Paper 1 experimentally demonstrated poisoning, agent effectiveness, privacy protection, or longitudinal adaptation.

# Paper 2 Fact Check

## Bibliography

| Field | Verified value | Source location | Status |
|---|---|---|---|
| Title | *Continuous Behavioral Authentication for Mobile Devices Using an Adaptive LSTM-Based Intelligent Agent* | PDF p. 1 | Confirmed |
| Authors | Vassiliy Serbin; Madi Gali; Maksim Iavich | PDF p. 1 | Confirmed |
| Venue | 17th International Conference on Emerging Ubiquitous Systems and Pervasive Networks (EUSPN 2026), 28–30 October 2026, Almaty, Kazakhstan; Procedia Computer Science format | PDF p. 1 | Confirmed for the supplied manuscript |
| Year | 2026 | PDF p. 1 | Confirmed |
| Publication status | The supplied PDF is an Elsevier/Procedia-formatted conference manuscript or proof. It still shows `Procedia Computer Science 00 (2026) 000–000` and gives no DOI or final pages. Final proceedings metadata is therefore not verified from this artifact. | PDF pp. 1–6 | Partially confirmed |

Until a final proceedings record exists, cite it as an EUSPN 2026 conference paper/manuscript and do not invent a volume, page range, or DOI.

## Dataset

- Dataset: HMOG, closed-set verification over 100 enrolled subjects (PDF pp. 1 and 3).
- Nominal design: 24 smartphone-interaction sessions per subject, 2,400 nominal subject-sessions (PDF pp. 2–3).
- Usable data: 2,392 sessions and 4,784 sequences. Six sessions for subject `733162` were skipped because one inertial file was empty; session 24 was absent for subjects `526319` and `796581`. All 100 subjects retained enough data for all partitions (PDF p. 3; `dataset_exclusions.json`; `hmog_sequences_100.quality.json`).
- Modalities: accelerometer and gyroscope only. For each sensor CSV, only zero-based columns 3–5 (human columns 4–6), the physical x/y/z axes, are read. Metadata columns, including the session identifier, are excluded (PDF pp. 2–3; code lines 98–124).
- Sampling: the experiment assumes HMOG's nominal 100 Hz rate. It does not estimate or validate the actual sampling rate (PDF p. 3).

## Preprocessing

- Accelerometer and gyroscope rows are paired by acquisition order after truncation to the shorter file; there is no timestamp resampling (PDF p. 3; code lines 145–157).
- The first 500 samples, described as five seconds at nominal 100 Hz, are discarded (`WINDOW_OFFSET=500`).
- The next 20 non-overlapping windows of 100 samples are retained per usable session (`WINDOW_SIZE=100`, `WINDOWS_PER_SESSION=20`).
- Six statistics are computed for each of six channels: mean, standard deviation, minimum, maximum, RMS, and skewness. Each one-second window therefore has 36 features (PDF p. 3; code lines 126–164).
- A `StandardScaler` is fitted only to flattened time steps from the model-fitting partition, then applied unchanged to validation and test. This is training-only normalization (PDF p. 3; code lines 434–464).

## Protocol

- Ten adjacent one-second windows form a `10 × 36` sequence. `SEQ_STEP=10`, so sequences do not overlap and never cross session boundaries. Each usable session contributes two sequences (PDF p. 3; code lines 55–60 and 167–204).
- Five outer folds use `g(r) = (r - 1) mod 5`. For zero-based outer fold `f`, sessions with `g(r)=f` are test, `g(r)=(f+1) mod 5` are validation/calibration, and the remaining three groups are model fitting (PDF p. 3; code lines 231–236).
- Every included subject must occur in fitting, validation, and test. This is session-disjoint, closed-set cross-validation, not leave-one-subject-out or unseen-subject recognition (PDF p. 3; code lines 193–204 and 456–460).
- The realized sequence counts by fold are recorded in `revised_fold_protocol.json`: folds 1–2 use 2788/998/998 fit/validation/test sequences; fold 3 uses 2794/992/998; fold 4 uses 2994/798/992; fold 5 uses 2988/998/798. The imbalance reflects the documented missing/skipped sessions.
- Validation is used both for early stopping and claimant-specific initialization. It is test-disjoint but not a separate second calibration set (PDF p. 3).

## Models

### LSTM

- Input `10 × 36`.
- Two-layer LSTM, 64 hidden units per layer; last sequence output; layer normalization; 32-unit ReLU dense layer; dropout 0.30; 100-class softmax (PDF p. 3; code lines 239–255).
- Cross-entropy loss; Adam, learning rate `1e-3`; batch size 256; maximum 20 epochs; early-stopping patience 4 (PDF p. 3; code lines 261–310).
- The canonical code additionally uses `ReduceLROnPlateau(factor=0.5, patience=2)`, a training detail omitted from the short PDF. This is an omission, not a numerical contradiction.
- The claimant score is the corresponding class softmax probability in `[0,1]`; larger scores are more genuine-like (PDF p. 3).

### Classical baselines

- Both baselines receive the same sequence flattened to 360 dimensions (PDF p. 3).
- Linear SVM: `C=0.1`; code additionally fixes `dual=False`, `tol=1e-3`, `max_iter=1500`, and seed 42 (PDF p. 3; code lines 471–474).
- Random forest: 300 trees, unrestricted depth, square-root feature subsampling, minimum leaf size 2; code also fixes `n_jobs=-1` and seed 42 (PDF p. 3; code lines 475–482).
- These are fixed reference baselines, not tuned state-of-the-art systems and not adaptive methods.

## Adaptive Agent

For claimant `u`, validation genuine scores initialize the first moment `p_{u,0}` and second raw moment `q_{u,0}`. Before attempt `n`:

```text
sigma_{u,n-1} = sqrt(max(q_{u,n-1} - p_{u,n-1}^2, epsilon^2))
tau_{u,n}     = max(0, p_{u,n-1} - k_u sigma_{u,n-1})
d_{u,n}       = I[s_{u,n} >= tau_{u,n}]
```

If accepted (`d_{u,n}=1`):

```text
p_{u,n} = (1-alpha)p_{u,n-1} + alpha s_{u,n}
q_{u,n} = (1-alpha)q_{u,n-1} + alpha s_{u,n}^2
```

Otherwise the state is unchanged. The fixed parameters are `alpha=0.05` and `epsilon=1e-4` (PDF p. 4; code lines 331–358).

For each claimant, validation genuine and validation impostor scores define an approximate EER threshold `tau_{u,0}`. Then

```text
k_u = (p_{u,0} - tau_{u,0}) / sigma_{u,0}
```

so Frozen and EMA start at exactly the same validation-calibrated threshold. `k_u` is claimant-specific and is not selected from test outcomes. Frozen retains `tau_{u,0}`; EMA updates only after accepted attempts. Rejections do not lower the threshold (PDF p. 4).

The rule is label-blind. Consequently, an accepted impostor can update the profile. Paper 2 identifies and preserves this poisoning pathway, but it does not conduct the dedicated poisoning experiment later performed in Paper 3.

### Evaluation stream

- Genuine test sequences are processed in session and within-session chronological order.
- Each genuine attempt is followed by one zero-effort impostor score, producing an explicitly artificial balanced 50% impostor stress stream.
- For each claimant, impostors are sampled uniformly without replacement from all test sequences of the other 99 identities. Sampling is repeated 10 times, and the profile is reinitialized for every repeat.
- Frozen and EMA receive the same stream within a fold/drift condition. Decisions remain label-blind (PDF p. 4; code lines 381–426).

## Drift

- Drift is injected after training in standardized 36-dimensional feature space. A unit vector is sampled from `N(0,I_36)` with seed `42 + fold` and linearly ramped from zero to final L2 magnitude `D ∈ {0,1,2}` over each subject's chronological test sequence (PDF p. 4; code lines 366–378 and 500–503).
- The same 36-dimensional displacement is added to all ten time steps of a sequence. The magnitude refers to the per-time-step standardized feature vector.
- The direction is **one shared direction per fold**, not one independently sampled direction per subject. Within that fold, every subject is ramped along that direction.
- The transformation is applied to all test samples, including samples later used as impostors. It is therefore the “global” synthetic shift inherited by Paper 3, not claimant-only drift.
- The trained model is not retrained for drift evaluation.
- This is explicitly a synthetic feature-shift sensitivity analysis, not natural behavioral drift. Impostor streams are independently resampled across drift levels using drift-dependent seeds, so cross-level changes are not purely attributable to drift.

## Results

All values below match the PDF tables and the revised summary/by-fold CSV files after rounding.

### Metrics

- EER is approximated separately for each claimant at the held-out ROC point minimizing `|FAR-FRR|`, then macro-averaged within fold. This test-derived EER summarizes score separability and is never used as the deployed decision threshold.
- FAR and FRR are computed from the actual Frozen or chronological EMA decisions in the balanced stream. `HTER = (FAR + FRR) / 2` (PDF p. 4, Section 5; canonical code lines 312–329 and 381–426).

### Undrifted macro EER

| Model | EER, mean ± SD over five folds |
|---|---:|
| Linear SVM | 29.92% ± 0.80% |
| Random forest | 24.05% ± 0.86% |
| LSTM | 21.87% ± 1.01% |

### Validation-calibrated chronological operating points

| D | Rule | FAR | FRR | HTER |
|---:|---|---:|---:|---:|
| 0 | Frozen | 22.55% ± 1.13% | 23.82% ± 2.27% | 23.19% ± 0.95% |
| 0 | EMA | 24.46% ± 2.12% | 24.60% ± 2.04% | 24.53% ± 1.28% |
| 1 | Frozen | 22.43% ± 0.69% | 24.82% ± 1.97% | 23.63% ± 1.10% |
| 1 | EMA | 24.30% ± 2.00% | 25.73% ± 2.64% | 25.02% ± 1.66% |
| 2 | Frozen | 22.40% ± 0.85% | 27.37% ± 2.91% | 24.89% ± 1.37% |
| 2 | EMA | 24.53% ± 2.11% | 28.25% ± 4.25% | 26.39% ± 2.12% |

Using unrounded fold means, EMA increased HTER relative to Frozen by 1.34, 1.39, and 1.51 percentage points at `D=0,1,2`. Frozen had lower HTER in all five folds at every drift level (PDF p. 5; revised CSVs).

No inferential statistical test was reported. The paper explicitly treats fold means/SDs as descriptive because training and validation partitions overlap across folds; the SDs are not confidence intervals and no significance claim is made (PDF p. 5).

## Limitations

The stated limitations include (PDF p. 5, Section 7.1):

- one dataset (HMOG) and no independent-dataset validation in Paper 2;
- six empty-file sessions and two absent session directories;
- acquisition-order sensor pairing without timestamp resampling;
- use of an early 20-second session excerpt;
- modulo session splits that are not rolling-origin forecasts, have unequal realized sizes, and are not activity/context stratified;
- an artificial alternating 50% impostor stream that is not an estimate of attack prevalence or burst behavior;
- independent impostor resampling across drift levels;
- one drift direction per fold;
- only one EMA rate (`alpha=0.05`);
- no clustered confidence intervals, on-device latency, or energy measurements.

## Confirmed Wording for Paper 3

Safe wording:

> Paper 2 evaluated a fixed, accepted-only score-level EMA against an otherwise identical frozen LSTM operating point under a leakage-resistant, session-disjoint HMOG protocol. The EMA did not improve HTER: it increased mean HTER from 23.19% to 24.53% without drift and from 24.89% to 26.39% at final synthetic drift magnitude 2. Because every accepted score could update the label-blind profile, the mechanism also exposed a poisoning pathway, although Paper 2 did not itself execute a dedicated poisoning attack.

Required qualifications:

- Attribute the negative result to the **tested EMA rule and protocol**, not to online adaptation in general.
- Call the drift synthetic standardized-feature shift/sensitivity analysis, not natural behavioral drift.
- Call the protocol closed-set and session-disjoint, not subject-disjoint.
- Do not call Paper 2's fold SDs confidence intervals or claim statistical significance.
- Do not say Paper 2 empirically proved poisoning; say its accepted-only implementation permitted accepted impostors to update the profile and motivated Paper 3's attack study.

# Claim Audit

## Claims currently carried in `paper/notes.md`

| Claim | Verdict | Source | Page/section | Corrected wording |
|---|---|---|---|---|
| “Dissertation focus: behavioral-biometric continuous authentication for mobile devices with an intelligent personal agent.” | **Not confirmed as a dissertation fact by these two papers** | Project context; Paper 1 title/objective only supports the research topic | Paper 1 pp. 1, 5–7 | Keep as project-level context, not as a finding of Paper 1 or Paper 2. |
| “Paper 1 is a systematic review with adversarial/privacy, benchmark, integration, and longitudinal gaps.” | **Confirmed, but too compressed** | Paper 1 PDF and supplement | Abstract; Sections 1.2, 2.4, 5.2; pp. 1, 7, 27–28, 68–70 | “Paper 1 reviewed 80 studies and identified gaps in standardized adversarial evaluation, joint adversarial/privacy pipeline testing, longitudinal/ecologically valid evaluation, BBCA–IPA integration, and user-centered privacy/consent evidence.” |
| “Paper 2 uses HMOG accelerometer and gyroscope signals with LSTM/RF/SVM and session-disjoint evaluation.” | **Confirmed** | Paper 2 PDF; canonical code | PDF pp. 1–3; code lines 98–124, 231–255, 471–482 | Add that this is 100-subject closed-set verification, uses only physical axes, and fits scaling on model-fitting sessions only. |
| “Paper 2's EMA adaptation did not outperform a frozen threshold.” | **Confirmed** | Paper 2 PDF; revised CSVs | Abstract; Results/Conclusion, pp. 1, 5–6 | “The tested accepted-only EMA had higher HTER than Frozen at D=0,1,2; this does not generalize to every adaptation rule.” |
| “Accepted impostors can poison a label-blind adaptive profile.” | **Partially confirmed as a mechanism, not as a Paper 2 attack result** | Paper 2 PDF; canonical code | PDF pp. 4–5; code lines 347–358 and 410–419 | “Paper 2's label-blind EMA allows any accepted impostor score to update the profile, creating a poisoning pathway; dedicated poisoning impact was first measured in Paper 3.” |
| “Paper 2 evaluated synthetic drift.” | **Confirmed** | Paper 2 PDF; canonical code | PDF pp. 4–6; code lines 366–378, 500–503 | “Paper 2 evaluated global synthetic standardized-feature shift at D=0,1,2 using one direction per fold; it did not evaluate natural drift.” |

## Potentially dangerous formulations A–F

| ID | Statement | Verdict | Source location | Approved wording |
|---|---|---|---|---|
| A | “Paper 2 showed that EMA adaptation does not outperform a frozen threshold.” | **Confirmed with scope qualification** | Paper 2 Abstract; Results and Conclusion, pp. 1, 5–6 | “Under the tested session-disjoint HMOG protocol, the prespecified accepted-only EMA rule did not outperform the validation-calibrated frozen threshold.” |
| B | “Paper 2 used leakage-resistant, session-disjoint evaluation.” | **Confirmed** | Paper 2 Sections 3.1–3.2, pp. 2–3; canonical code lines 98–236 and 456–464 | Retain; optionally add “closed-set” and “training-only scaling.” |
| C | “Paper 2 used only physical accelerometer/gyroscope axes and excluded metadata/session IDs.” | **Confirmed** | Paper 2 p. 3; canonical code lines 98–124 | Retain exactly. |
| D | “Paper 2's drift is synthetic standardized-feature drift, not natural behavioral drift.” | **Confirmed** | Paper 2 Section 5, p. 4; canonical code lines 366–378 | Retain; add “one shared direction per fold, applied to all test samples.” |
| E | “Paper 1 identified adversarial robustness, benchmark standardization, and agent-integration gaps.” | **Confirmed with wording refinement** | Paper 1 Abstract; Sections 1.1–1.2 and 5.2, pp. 1, 5–7, 68–70 | “Paper 1 identified weak standardized adversarial evaluation and limited empirical integration of BBCA with IPA/agent architectures.” “Adversarial robustness” alone is a topic, not a sufficiently precise gap label. |
| F | “Paper 1 found no study evaluating a complete BBCA pipeline under simultaneous adversarial and privacy threat models.” | **Confirmed within the review corpus** | Paper 1 Abstract; Section 1.2, p. 7; Section 5.2, p. 70 | Retain with “within the reviewed corpus/search scope.” |

## Audit conclusion

- All critical Paper 1 and Paper 2 claims needed for Paper 3 are now source-checked.
- Paper 2's technical claims and headline numbers agree across PDF, canonical code, metadata, and revised CSVs. The only bibliographic item still unavailable is final proceedings volume/pages/DOI.
- Paper 1's core methodology, corpus totals, research questions, and headline gaps are confirmed. Its supplementary package contains unresolved per-year and per-study mapping inconsistencies, which are documented above and must not be silently converted into precise claims.
- The Paper 3 checklist item can be closed because these unresolved items do not affect the critical prior-work claims. The limitations above must remain attached to any future citation or manuscript wording.
