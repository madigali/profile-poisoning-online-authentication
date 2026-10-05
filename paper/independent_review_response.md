# Independent Pre-Submission Review Response

This matrix responds to an independent pre-submission review. It is not a response to an editor or an official journal reviewer. The revision was restricted to source tracing, primary-literature verification, analytical clarification, metadata counts, presentation-only artwork changes, and manuscript assembly. No model was trained, no score was generated, no adaptive stream was replayed, and no endpoint or uncertainty interval was recomputed.

## M1 — Direct prior work, residual contribution, and local EMA dynamics

- **Comment summary:** The manuscript did not sufficiently distinguish its contribution from direct biometric precedents, particularly Giot et al. (2012), and did not explain a local EMA threshold effect.
- **Decision:** Accepted.
- **Primary source:** Giot, Rosenberger, and Dorizzi, “Hybrid Template Update System for Unimodal Biometric Systems,” BTAS 2012, DOI 10.1109/BTAS.2012.6374539; Giot, Rosenberger, and Dorizzi, “Performance Evaluation of Biometric Template Update,” IBPC 2012 supporting paper hosted by NIST and arXiv:1203.1502.
- **Action:** Added the two verified bibliography records. The article now states that separate authentication/update thresholds, erroneous impostor inclusion, genuine-update misses, and attempt-normalized update-selection metrics are prior art. It relates MUR to IUSR and GUR to \(1-\mathrm{GUMR}\) only under matching observations, units, update definitions, and aggregation. The three contributions are reframed positively around paired fixed-score evaluation on separated poisoning/future-probe observations, operating-point-specific consequences, and cross-dataset corroboration under the documented policy. A conditional derivation for one canonical EMA update at the current raw boundary was added.
- **Changed locations:** paper/abstract.md; paper/introduction.md; paper/related_work.md Sections 2.2--2.4; paper/methods.md Sections 3.3--3.4; paper/discussion.md Sections 5.1 and 5.3; paper/conclusion.md; paper/supplementary_methods.md Section S3.3; corresponding passages in paper/manuscript_full.md, paper/mdpi/metadata.tex, paper/mdpi/paper3_mdpi.tex, and references.bib.
- **Scientific outcomes changed:** No.
- **Remaining limitation:** This was a targeted verification of the specified closest studies, not a new systematic novelty review. No “first” claim is made.

## M2 — McGill threshold policy and Figure S6

- **Comment summary:** Main Methods described HMOG with \(\max(0,\mu-k\sigma)\), while the McGill Oracle-all threshold in Figure S6 became negative.
- **Decision:** Accepted and resolved by executed-source tracing.
- **Primary source:** McGill manifest revision 1c0eeb8fb9dbbc1113d9aa0faa48cee07c72cce9; executed source SHA-256 077412a02b4bda0e5a2461aa689703c623925f1a0ec6967c32fd01dfe5a53c1f; frozen temporal_checkpoints.csv SHA-256 4483810fcbda1ee67fa2bc5584a54012ec3e7e6fb5c7fefa329ddb84d053cd60; operating-point revision 517746fbe6e89268a603fceebefe558409eabb33.
- **Action:** Documented the executed McGill threshold as the unclipped expression \(\tau=\mu-k\sigma\), with sigma floor \(10^{-4}\), and distinguished it from HMOG's zero-clipped rule. The trace now states initialization, calibration tie-break, access comparator, Guarded conjunction, saved-state timing, and Figure S6 aggregation. Figure S6 now labels the panel “Unclipped authentication threshold,” and its caption states that the line is the arithmetic mean of saved individual thresholds after adaptation and before checkpoint evaluation, not a threshold reconstructed from aggregate moments.
- **Changed locations:** paper/methods.md Sections 3.2--3.3; paper/results.md Section 4.4; paper/discussion.md Sections 5.4--5.5; paper/supplementary_methods.md Sections S3.1 and S5; paper/supplementary_results.md Figure S6 caption; corresponding LaTeX and presentation-only Figure S6.
- **Scientific outcomes changed:** No. The source, saved fields, access decisions, and original plot are internally consistent.
- **Remaining limitation:** HMOG and McGill did not use identical threshold clipping. A clipped McGill counterfactual would be a new experiment and was not performed.

## m1 — Figure S2 feasibility caption

- **Comment summary:** The caption implied only \(K=8\), although the figure displays feasibility separately for each budget.
- **Decision:** Accepted.
- **Primary source:** Frozen eligibility_summary.csv.
- **Action:** The caption now defines every point as the fraction of planned paths with at least the displayed \(K\) candidates and separately states that operating-point effect curves use the common \(K=8\)-feasible cohort within each condition.
- **Changed locations:** paper/supplementary_results.md Figure S2 caption; paper/mdpi/paper3_supplementary.tex; presentation-only Figure S2 x-axis.
- **Scientific outcomes changed:** No.
- **Remaining limitation:** Feasibility remains conditional on the tested score-informed candidate pool and does not measure reconnaissance cost.

## m2 — Main figure labels

- **Comment summary:** Figure 1 called \(K\) an update budget, and Figure 4 used causal wording stronger than the design supported.
- **Decision:** Accepted.
- **Primary source:** Frozen poisoning and trajectory plot-data CSV files.
- **Action:** Figure 1 now says “Presented poisoning attempts K.” Figure 4 now says “Update eligibility changes profile trajectories under the imposed feature shift.” Only labels, font sizing, and layout were changed.
- **Changed locations:** Presentation-only Figures 1 and 4 and their registry under paper/mdpi/figures_revision_20261005/.
- **Scientific outcomes changed:** No. Points, intervals, cohorts, axes, and numeric arrays were preserved.
- **Remaining limitation:** The Figure 4 comparison remains diagnostic; it does not isolate update composition from update count.

## m3 — Reproducible procedure specification

- **Comment summary:** The HMOG ramp, McGill magnitude channel, temporal counts, horizon, and Oracle interpretation required exact specification.
- **Decision:** Accepted.
- **Primary source:** Hash-matched HMOG injection source; frozen drift manifests and exclusion tables; executed McGill source and official archive readme; training and score manifests.
- **Action:** Added fold/seed mapping, direction normalization, chronological rank formula, all-sequence ramp scope, timestep broadcasting, global/claimant-only construction, supplied McGill accel_mag field and units, fitting-only normalization, recorded partition counts, state-record timing, and a compact Supplement table. The text states that HMOG supplies only four or five update opportunities per included victim-fold path, that \(0.95^5\approx0.774\), and that the initial-mean coefficient first falls below one half after 14 permitted updates. Oracle-all is now explicitly described as changing both update composition and update count/frequency.
- **Changed locations:** paper/methods.md Sections 3.2 and 3.6; paper/supplementary_methods.md Sections S2 and S5; paper/supplementary_results.md Table S4; corresponding LaTeX.
- **Scientific outcomes changed:** No.
- **Remaining limitation:** The exact historical HMOG temporal-runner bytes are not retained, although its hash is recorded and the canonical injection source is hash matched. Numeric session identifiers were not independently validated as natural chronology.

## m4 — Repetition and scope

- **Comment summary:** Development-branch history and broad recovery statements were repeated.
- **Decision:** Accepted.
- **Primary source:** Current compact manuscript and frozen branch-status records.
- **Action:** Kept the stopped branches where evidentially necessary and narrowed the interpretation to “did not improve late FRR within the short evaluated replay.” The Conclusion now distinguishes the evaluated horizon from a universal inability to recover.
- **Changed locations:** paper/discussion.md Sections 5.3 and 5.5; paper/conclusion.md; corresponding LaTeX.
- **Scientific outcomes changed:** No.
- **Remaining limitation:** TQ-v1, TQ-v2, and Quantile conclusions remain specific to the frozen implementations, grids, constraints, and observed horizons.

## m5 — Readability

- **Comment summary:** Several figure labels and Supplementary Table S1 were difficult to read.
- **Decision:** Accepted.
- **Primary source:** Frozen plot-data/state tables and frozen TQ-v1 selection table.
- **Action:** Increased presentation-copy font sizing and spacing for Figures 4 and S6. Removed the redundant encoded configuration column from publication Table S1 because all encoded parameters remain in separate columns. The frozen CSV and original figure artifacts were not modified.
- **Changed locations:** paper/supplementary_results.md Table S1; paper/mdpi/paper3_supplementary.tex; presentation-only artwork.
- **Scientific outcomes changed:** No.
- **Remaining limitation:** No zoom panel was added for Figure 2 because the strict-point effects are already tabulated.

## m6 — References, availability, and administrative fields

- **Comment summary:** Direct references and an honest availability statement were needed; author-controlled administrative fields should not be guessed.
- **Decision:** Partially accepted.
- **Primary source:** Verified publisher/NIST metadata, current private repository status, and MDPI working package.
- **Action:** Added the two Giot 2012 entries. The Data Availability statement now says that raw datasets are not redistributed and the code/results repository is private with no assigned public archive or DOI. Author identities/order, affiliations, correspondence, ORCID, final keywords, contributions, funding, ethics, consent, conflicts, acknowledgments, AI-use disclosure, target journal, and final title remain visible author decisions.
- **Changed locations:** references.bib; MDPI bibliography copies; paper/mdpi/declarations.tex; paper/mdpi/README.md.
- **Scientific outcomes changed:** No.
- **Remaining limitation:** The package is a working submission draft until the author resolves the listed administrative fields and approves any public release route.

## Optional experiments not adopted

A clipped McGill replay, count-matched Oracle control, new attack, new calibration target, new dataset, and new recovery model were not performed. Their absence is handled by limiting the corresponding claims rather than implying that the controls exist.
