# Targeted Pre-Submission Revision Audit

## Scope and baseline

- Revision type: targeted response to an independent pre-submission review, not an official editorial revision.
- Baseline branch: paper3-external-replication.
- Baseline revision: b18e9fb117828f31a01f5efcce5b0be57081fa07.
- Reviewed baseline PDFs retained under paper/mdpi/build/.
- Pre-existing unrelated untracked directories were excluded from the revision and staging.
- Prohibited operations were not performed: no training, scoring, attack replay, adaptive replay, metric recomputation, bootstrap, hypothesis test, new calibration target, count-matched Oracle, new algorithm, or new dataset.

## M2 executed-source trace

### McGill reference implementation

The frozen manifest records executed revision 1c0eeb8fb9dbbc1113d9aa0faa48cee07c72cce9, source SHA-256 077412a02b4bda0e5a2461aa689703c623925f1a0ec6967c32fd01dfe5a53c1f, protocol SHA-256 69aa325074a42dd02eb74fdec4ca0ae53ecc90b9f855c46e522a7b1bbcadb06b, and score-cache SHA-256 3f390ab19fbea15582fbb5a646cf7e631b77b744ab101e97d83edb533717a79b.

Executed chain:

1. \(\mu_0\) is the mean of claimant enrollment scores.
2. \(q_0\) is their mean squared score.
3. \(\sigma=\max(\sqrt{\max(q-\mu^2,0)},10^{-4})\).
4. \(\tau_0\) minimizes pooled Day-1 HTER, with exact ties resolved toward the higher threshold.
5. \(k=(\mu_0-\tau_0)/\sigma_0\).
6. Every later authentication threshold is the unclipped \(\tau=\mu-k\sigma\).
7. Access uses score greater than or equal to tau.
8. Guarded requires both score greater than or equal to tau_auth and score greater than or equal to \(\tau_{\mathrm{auth}}+0.25(\mu_{\mathrm{enroll}}-\tau_{\mathrm{auth}})\).
9. For each temporal unit, access/update are evaluated using the pre-update state; a permitted adaptation update occurs; the disjoint checkpoint is evaluated with the post-update state; that post-update state is saved.
10. Figure S6 groups saved rows by method and unit and averages individual subject fields. It does not reconstruct a threshold from aggregate moments.

### Arithmetic checks on frozen saved state

Permitted pointwise arithmetic was applied to saved fields only. Across 4,800 McGill temporal rows, the trace found no authentication-flag mismatch and no update-event mismatch. Maximum post-update discrepancies were approximately \(9.7\times10^{-17}\) for mean, \(5.6\times10^{-16}\) for sigma, and \(1.9\times10^{-15}\) for threshold. The sigma floor was inactive in all saved temporal states. Negative thresholds occurred in 958 rows, exclusively for Oracle-all; the subject-macro mean became negative at unit 14 and was negative in 53 of 80 units. Historical poisoning thresholds also matched \(\mu-k\sigma\) within \(4.7\times10^{-16}\).

### Cross-dataset policy

HMOG's canonical code uses \(\max(0,\mu-k\sigma)\). McGill transfers the moment state, alpha, sigma floor, claimant-specific \(k\), comparator, and Guarded lambda, but not the zero lower clamp. This is an executed dataset-policy difference and was not labelled as a prespecified intervention. Because cached scores are non-negative, clipping a negative threshold to zero would preserve access decisions at an otherwise fixed state, but it can change the Guarded update threshold and later trajectory. No clipped replay was performed.

The operating-point implementation at revision 517746fbe6e89268a603fceebefe558409eabb33 hash-verifies and loads the same McGill source/cache and retains the unclipped threshold. Its reference reproduction passed all 51,840 McGill rows within \(10^{-9}\).

## M1 literature verification

- Giot2012HybridTemplateUpdate was verified as an IEEE BTAS 2012 paper, pages 1--7, DOI 10.1109/BTAS.2012.6374539.
- It explicitly defines \(\mathrm{IUSR}=U_i/N_i\) and \(\mathrm{GUMR}=(N_g-U_g)/N_g\), uses a double-threshold semi-supervised updater, and discusses both erroneous impostor inclusion and missed genuine updates.
- Giot2012TemplateUpdateEvaluation was verified as an IBPC 2012 supporting paper hosted by NIST and available as arXiv:1203.1502. No DOI or formal proceedings publisher was assigned in the bibliography.
- MUR corresponds to IUSR and GUR to \(1-\mathrm{GUMR}\) only under matching observation sets, units, update definitions, and aggregation.
- The revised contribution does not claim invention of two thresholds, discovery of update inclusion/exclusion errors, a new universal MUR/GUR family, or a first biometric poisoning attack.

## Analytical derivation

For one permitted canonical EMA update,

\[
\sigma_{t+1}^2=(1-\alpha)\left[\sigma_t^2+\alpha(s_t-\mu_t)^2\right].
\]

At \(s_t=\mu_t-k\sigma_t\), with fixed \(k\), \(0<\alpha<1\), \(\sigma_t>0\), and inactive floor/clipping branches,

\[
\Delta\tau=k\sigma_t\left[(1-\alpha)-\sqrt{(1-\alpha)(1+\alpha k^2)}\right].
\]

The bracket is negative. Therefore the local threshold change is negative for \(k>0\), positive for \(k<0\), and zero for \(k=0\). The derivation was algebraically checked and is labelled as an explanatory presubmission addition, not a new empirical result. It is not generalized to non-boundary samples, denied updates, changing \(k\), different cohorts, or multi-step ASR.

## Procedure and count trace

### HMOG shift

- Public folds 1--5 map to internal zero-based folds 0--4 and drift seeds 42--46.
- One fold-specific 36-vector is sampled from a standard Gaussian and normalized by \(\lVert z\rVert_2+10^{-12}\).
- Every original standardized test sequence is ranked by numeric session and within-session start; the ramp fraction is \(j/(n-1)\).
- The same displacement is broadcast to all ten time steps in one sequence.
- The within=0 adaptation and within=10 checkpoint sequences are selected only after the all-sequence drift scores are cached.
- Global uses selected-\(D\) claimant and impostor scores; claimant-only combines selected-\(D\) claimant scores with \(D=0\) impostor scores.
- Recorded temporal inventory: 498 eligible victim-fold paths, 2,386 adaptation candidates, 2,386 checkpoints, 996 early checkpoints, and 996 late checkpoints.

### McGill

- The executed reader uses supplied accel_x, accel_y, accel_z, and accel_mag.
- The archive documents \(\mathrm{accel\_mag}=\sqrt{x^2+y^2+z^2}-9.8066\) and acceleration in \(\mathrm{m/s^2}\); the pipeline does not recompute this field.
- Recorded Day-1 counts: 2,840 fitting, 948 validation, 958 enrollment/calibration windows.
- Recorded Day-2 temporal inventory: 1,600 adaptation candidates and 1,600 checkpoints across 20 subjects, with 400 early and 400 late checkpoints.

### Horizon and Oracle

HMOG has four or five permitted adaptation opportunities per included path. For canonical alpha 0.05, the initial-mean coefficient is \(0.95^n\), equals approximately 0.774 after five permitted updates, and first falls below one half at 14 whole updates. This is not wall-clock recovery time or threshold convergence. Oracle-all changes both which observations update and how many updates occur; no count-matched control was performed.

## Presentation-only artwork

The original figures and their hashes remain unchanged. Four separate publication copies are rendered only from frozen numeric tables:

| Original | Publication copy | Allowed change | Numeric source |
|---|---|---|---|
| HMOG Figure 1 | figures_revision_20261005/figure1_poisoning_asr.pdf | x-axis wording | paper3_final_poisoning_plot_data.csv |
| HMOG Figure 4 | figures_revision_20261005/figure4_selection_bias_mechanism.pdf | title, font sizing, legend spacing | paper3_final_selection_bias_plot_data.csv |
| Supplement Figure S2 | figures_revision_20261005/figureS2_boundary_feasibility.pdf | x-axis wording/ticks | eligibility_summary.csv |
| Supplement Figure S6 | figures_revision_20261005/figureS6_external_selection_bias_trajectory.pdf | threshold-panel title, font sizing, layout | temporal_checkpoints.csv |

The machine-readable artwork_registry.json records original, input, and publication hashes. No plotted point, interval, cohort, axis quantity, or scientific endpoint was changed.

## Numerical preservation

- Frozen result tables, caches, original figure artifacts, manifests, tags, and historical audits were not modified.
- New manuscript statements use existing saved outcomes or permitted source/metadata arithmetic.
- No historical CSV column was renamed and no metric was recalculated.
- The scientific results and reported confidence intervals are unchanged.

## Build and visual verification

The versioned build completed with pdfLaTeX/BibTeX through Latexmk. The main manuscript contains 24 pages and the Supplement contains 14 pages. The final logs contain no LaTeX error, fatal error, undefined citation, undefined reference, or overfull box. The Supplement retains two underfull-box notices: one wide-table alignment and one long provenance path. Both affected pages were inspected at full rendered resolution and showed no clipping, overlap, or unreadable text.

All 24 main pages and all 14 Supplement pages were rendered to 150-dpi PNG files and visually inspected. The focused review included the revised main Figures 1 and 4, Supplement Figures S2 and S6, the new Table S4, the simplified landscape Table S1, the local EMA derivation, the bibliography, declarations, headers, footers, and page numbering. No black boxes, missing glyphs, cropped content, broken equations, or figure-label collisions were observed.

The final source archive contains 40 entries and excludes compiled PDFs, build auxiliaries, result directories, score caches, raw data, generated logo conversions, and operating-system metadata. It was extracted into a fresh temporary directory and rebuilt with `./build_targeted_revision.sh`. The clean build again produced 24 main pages and 14 Supplement pages, with the same zero-error/zero-undefined/zero-overfull outcome and the same two visually harmless Supplement underfull notices.

Baseline PDF preservation was rechecked:

- baseline main SHA-256: `9b466df586a99dd56530894911f803a7050ee32c1a6680f9317d476256986acc`;
- baseline Supplement SHA-256: `cc2011c7a6850da1c70571a29cc94cb26f9d51dfd2c17c3ff6f2c2dc5ff39098`.

Final targeted-revision outputs:

- main PDF SHA-256: `320cafa5dc416b9f53f49440432ac4b7edfbfb632d48e6f368dea1af66554e60`;
- Supplement PDF SHA-256: `7591154087bc2a8034296437a38edf2ac1f3abb4ca9445dc0e353e792083eb2d`;
- source ZIP SHA-256: `7189d5a8d737b8e1b5eb801e1dba86b542bae7217355e53f1363a64452f050b0`;
- source-manifest SHA-256: `2cdd4e4493a24381aa4c40c8e1942d697400f4d1bc98c883fe99b9a46b555fa8`.

## Authorship and funding update (2026-10-18)

The author list, affiliations, three supplied ORCID identifiers, BR28713099 funding statement, and one explicitly prospective Discussion sentence were added without changing experimental data or results. The supplied Word author table had SHA-256 `2ad3657f04bbf74be383946d32d7f43902d3affa728b1ea8068087b098663cca` and was used as a source rather than committed to the repository.

The updated main manuscript and Supplement compiled successfully to 24 and 14 pages. Their final logs contained no LaTeX error, fatal error, undefined citation, undefined reference, or overfull box. The first pages of both documents, main Discussion page 21, and main declarations page 22 were rendered at 160 dpi and visually inspected; the author block, ORCID icons, future-work sentence, and funding statement were legible and unclipped. The new source archive was extracted into a fresh directory and rebuilt successfully with the included update script.

Versioned update outputs:

- main PDF SHA-256: `d45716043706c9b17c828440d46160965898b5a28ee5d7fa987dfbde0ad0b3c0`;
- Supplement PDF SHA-256: `cac685f0550ce0428f28c1956ea852a6319d0a99afd29e95c134b0b01abaaf54`;
- source ZIP SHA-256: `79c8cde1fc5a7f157935e500e1e2665524854bfbac184bed15471ea845741a1b`.

### Complete ORCID update (v2)

The three subsequently supplied identifiers were added to the existing author records: Madi Gali (`0009-0006-2621-0454`), Vassiliy Serbin (`0000-0002-5807-3873`), and Aray Kassenkhan (`0000-0002-6355-9544`). Together with the three identifiers already supplied in the author table, the main manuscript and Supplement now display six ORCID icons. All six PDF link targets were inspected programmatically and matched the recorded identifiers.

The v2 main manuscript and Supplement compiled successfully to 24 and 14 pages. Their first pages were rendered at 170 dpi and visually inspected; the six icons, author names, affiliation markers, and surrounding text were legible and unclipped. The v2 source archive was extracted into a fresh directory and rebuilt successfully with its included build script.

Versioned v2 outputs:

- main PDF SHA-256: `9d807e5c4040591cfe3295fa1d86d36a4e77c3d71225619cfc2ffab28197af17`;
- Supplement PDF SHA-256: `a1b57cef5abd937c012406a73fe08a1922cf627fe71e9e2a6ab4700f28bab0b6`;
- source ZIP SHA-256: `c60b74d4c96112f6ddec42d396cd0363f8413b3c163e7f5480e0e2be728939cf`.

## Unresolved author decisions

On 2026-10-18, the author confirmed the following order: Madi Gali, Vassiliy Serbin, Aray Kassenkhan, Aliya Turegeldinova, Bakytzhan Amralinova, and Shyndauyl Nugumanov. Affiliations for the first three authors were carried forward from the verified primary Paper 1 metadata; the supplied author table provided the affiliations, e-mail addresses, and ORCID identifiers for Turegeldinova, Amralinova, and Nugumanov. The author subsequently supplied ORCID identifiers for Gali (`0009-0006-2621-0454`), Serbin (`0000-0002-5807-3873`), and Kassenkhan (`0000-0002-6355-9544`). The established publication names Madi Gali, Vassiliy Serbin, and Aray Kassenkhan were retained in the article; academic titles and positions were used to verify the existing departmental affiliations but were not added to the MDPI author line. The author also supplied the final BR28713099 funding statement. These administrative edits did not alter any experiment, endpoint, result, or interpretation.

The target journal and title remain unapproved. Corresponding-author designation, final keywords, contributions, ethics review, consent, conflicts, acknowledgments, and AI-use disclosure require author confirmation. Raw datasets are not redistributed. The code/results repository is private, and no public archive or DOI is currently assigned; the final availability route requires an author decision.

## MDPI repository-link update (2026-10-21)

The journal-facing code and derived-results route was frozen as the Git tag
`paper3-mdpi-submission-2026-10-21` at
`https://github.com/madigali/paper3-poisoning-resistant-adaptation/tree/paper3-mdpi-submission-2026-10-21`.
The root README now provides direct entry points to the versioned manuscript,
Supplementary Materials, portable LaTeX archive, and provenance manifest. The
Data Availability statement names the same immutable tagged revision and states
that the repository remains private during manuscript preparation, with access
available from the authors upon reasonable request. No public availability or
repository DOI is claimed, and no raw HMOG or McGill Gait data are redistributed.

This was an administrative and reproducibility-linkage update only. It did not
change a scientific method, experimental result, figure, table, citation, or
interpretation.

The versioned main manuscript and Supplement compiled successfully to 24 and
14 pages. Their final logs contained no LaTeX error, fatal error, undefined
citation, undefined reference, or overfull box. Main page 22 was rendered at
180 dpi and visually inspected; the tagged URL wrapped cleanly, remained
legible, and did not collide with line numbers or surrounding declarations. The
portable source archive passed integrity testing and a clean-extract rebuild
with the included repository-link build script, again producing 24 and 14
pages.

Versioned repository-link outputs:

- main PDF SHA-256: `40364fdaa9a9cb2f84f28cba8120c4216e335ffe559b33c816d1f4cd1b26fa23`;
- Supplement PDF SHA-256: `122dc4f7499b81146ddb1266836e862c19860611efbafc6319aa5b9acbb82afb`;
- source ZIP SHA-256: `43ce103248c7c65aab1f7d2a50c97a7018e5d7ffee6f26e234e0f32131dc590d`;
- source-manifest SHA-256: `c1f30e1f1142e671da8693736fafedd72f2ef38ab62f8404556fff85c70f965a`.

There is no evidence-integrity blocker arising from M2 if the article reports the executed dataset-specific policy. Requiring identical zero clipping across HMOG and McGill would create a new experiment and would require replacement of the affected McGill outcomes.
