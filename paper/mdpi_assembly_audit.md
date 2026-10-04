# Paper 3 MDPI LaTeX Assembly Audit

## 1. Outcome and scope

The frozen Paper 3 manuscript was assembled as a separate **MDPI-style working manuscript package** under `paper/mdpi/`. The assembly changed presentation only. It did not retrain a model, rerun an experiment, recompute a statistic, alter an endpoint, add a scientific claim, or overwrite the authoritative Markdown and bibliography files.

The package is not submission-ready. Journal choice and author-controlled metadata remain pending and are shown explicitly as placeholders.

Assembly source state:

- repository: `/Users/madigali/Documents/PythoProjects/q1`
- branch: `paper3-external-replication`
- source revision: `ad00fb0254f166c146638bfc5c1457552f9593f5`
- assembly date: 2026-10-04
- pre-existing untracked paths preserved and excluded from assembly staging: `release/`, `results/paper3_guarded_drift_20260930/`, and `results/paper3_oracle_all_drift_20261001/`

## 2. Official template provenance

The template came from the official MDPI author page:

- page: <https://www.mdpi.com/authors/latex>
- downloaded archive: <https://res.mdpi.com/data/MDPI_template_ACS.zip?v=20260911>
- archive SHA-256: `62744425fbcec9cd3e58147cbee65bdec2e2ff0440f29792c26edc97a11b6c70`
- class identification: `Definitions/mdpi.cls`, `2026-09-11`, `v6.5a`

No target journal was approved. The main source therefore uses the official neutral options `notspecified,article,submit,moreauthors`; the Supplement uses `notspecified,supfile,submit,moreauthors`. Choosing a topical journal during assembly would have invented publication metadata.

The `Definitions/` files were retained without edits. The archive contained no standalone license file; upstream notices embedded in those files remain intact. File-level hashes are recorded in `paper/mdpi/source_manifest.json`.

## 3. Assembly structure

The package contains:

- one readable main source, `paper3_mdpi.tex`, with the complete main text;
- one separate `paper3_supplementary.tex`;
- `metadata.tex` and `declarations.tex` for author-controlled fields;
- a byte-identical `references.bib` copy and an MDPI-compatible `references_mdpi.bib` build derivative;
- a resolved `paper3_mdpi.bbl`;
- the official `Definitions/` support directory;
- ten authoritative PDF figures in `figures/`;
- `build.sh`, `README.md`, and `source_manifest.json`;
- verified main and Supplement PDFs under `build/`;
- `paper3_mdpi_source.zip`, a portable source-only archive.

The main file contains four figures and three tables. The Supplement contains Figures S1--S6 and Tables S1--S3, with Supplementary Methods S1--S10 and Supplementary Results S1--S6.

## 4. Metadata and declarations

The following fields were not recoverable as approved submission metadata and were not guessed:

- target journal;
- final title approval;
- author identities and order;
- affiliations;
- corresponding-author details;
- ORCID identifiers;
- keyword approval;
- author contributions;
- funding;
- institutional review and informed consent statements;
- data availability statement;
- acknowledgments, including any required AI-assisted-tool disclosure;
- conflicts of interest.

The working title is `Poisoning and Selective-Update Bias in Online Behavioral Biometric Authentication`. It is marked provisional in `metadata.tex`. The visible author and affiliation fields say that confirmation is pending. Declaration fields likewise state `Author confirmation pending.` The existence and inventory of the separate Supplement are the only finalized declaration facts.

The class requires numeric internal volume, issue, and article fields even in generic submit mode. They are set to technical zero placeholders while publication dates and year are blank. The generic class otherwise synthesizes an unassigned DOI footer. The manuscript preambles clear only that footer and preserve the remaining official layout; no class file was modified.

## 5. Bibliography audit

The repository-level `references.bib` and the package copy are byte-identical:

`d904dbe214499758eacf3f0aec0e48d6a28c2562265a6fecd71e673523c3c7c0`

The root bibliography contains 39 entries. The main manuscript has 63 citation occurrences referring to 36 unique keys. Citation order in the assembled TeX is identical to `paper/manuscript_full.md`; all 36 cited entries resolve, and the generated `.bbl` contains 36 `\bibitem` records. The Supplement has no independent citations.

`references_mdpi.bib` performs only three compatibility transformations:

1. `eid` is mapped to `pages` for `Gali2026SystematicReview`, `Xue2020LOPA`, and `Abdullahi2024TemplateAttacks` so article numbers render with the numeric MDPI style.
2. `Frank2010McGillGaitDataset` is represented as `@www`, retaining institution, year, URL, access date (`2026-10-03`), and note.
3. Redundant leading `Proceedings of` or `Proceedings of the` wording is removed from six conference `booktitle` fields because `mdpi.bst` inserts it.

Checks confirmed that the `.bbl` contains article numbers `451`, `102046`, and `102144`, preserves the McGill dataset URL, contains no `In Proceedings of the Proceedings`, no unresolved `??`, and no fabricated completion of the still-incomplete `Serbin2026AdaptiveLSTM` publication record.

## 6. Figure and table provenance

All figure copies are byte-identical to their frozen result artifacts. Destination/source mapping and SHA-256 values are recorded in `source_manifest.json`. The verified destination hashes are:

- Figure 1: `68f8ec856d00676124682d53e3a230620e60a71edc56529bcc6863a7dc1c522a`
- Figure 2: `e7193bc47f9b5fa3d84d834f1d07a23aceeba657ca669770dcad3058b9a0dedd`
- Figure 3: `ac84b16e3517cf6613802be6e1935d6968c5b48bc9efa4b5c5b59b35629fabb5`
- Figure 4: `cd88c9c2feee045d89b269aa9d9746656fbc61ed0a95710bb07dea937da94018`
- Figure S1: `53f6d132b3cd023d38b277e9bf2e0e5862af467753b61ff3fb40466626506854`
- Figure S2: `c654f1832dd626e2efc9ae5836e7a9bc07a522793bd3489ca98ccf85bed688e9`
- Figure S3: `4400da4ba4b1f94473cc5ef61f61c2b65d19524881b70a8941c73fd2c64e3eb5`
- Figure S4: `62da00ef4d38fbe3f6bb5a31d0bc2f46e8a1ca86ec162b090925a7f3283c7531`
- Figure S5: `1be4e784fb101a46409c1e7372ab0ae34ad953786b1b6b2d1c6e490728cf3be7`
- Figure S6: `e7e81b055d9ef6a33b525508c9fd157bbea021773ee2b0c1bf6e09948fe3c8a3`

Tables were transcribed into MDPI-compatible `table`/`tabularx` structures without changing values, labels, cohorts, intervals, or captions. Table S1 uses a dedicated full-width page and was inspected at native rendered resolution.

## 7. Build configuration and results

Build stack:

- pdfLaTeX: `pdfTeX 3.141592653-2.6-1.40.27 (TeX Live 2025/Homebrew)`
- orchestrator: `latexmk 4.86a`
- bibliography: `BibTeX 0.99d` with `Definitions/mdpi.bst`

`./build.sh` builds both documents. The main manuscript uses the supplied BibTeX-generated `.bbl` and can regenerate it from `references_mdpi.bib` when needed. The Supplement has no bibliography.

Final distributed outputs:

- `build/paper3_mdpi.pdf`: 22 A4 pages, SHA-256 `9b466df586a99dd56530894911f803a7050ee32c1a6680f9317d476256986acc`
- `build/paper3_supplementary.pdf`: 13 A4 pages, SHA-256 `cc2011c7a6850da1c70571a29cc94cb26f9d51dfd2c17c3ff6f2c2dc5ff39098`

Final log scan found:

- zero LaTeX errors;
- zero undefined citations;
- zero undefined references;
- zero multiply defined labels;
- zero overfull boxes;
- zero main-file warnings matching the audit scan;
- one harmless Supplement `Underfull \hbox` notice caused by line breaking a long provenance path.

Locale fallback messages from the local Perl installation are environmental shell notices, not TeX document defects.

## 8. Visual QA

Both final PDFs were rasterized at 150 dpi. Every page was viewed:

- main manuscript: pages 1--22;
- Supplement: pages S1--S13.

The review covered title blocks, headers and footers, equations, lists, cross-references, all seven main tables/figures combined, all nine Supplement tables/figures combined, references, declaration placeholders, page breaks, and margins. No text, figure, caption, or table was clipped. Figure labels and legends are readable. The Supplement title appears once, and neither document displays a synthetic DOI. The wide Table S1 was additionally inspected as an individual page at original resolution.

## 9. Content-preservation checks

The following automated checks passed:

- main citation-key sequence exactly equals the frozen Markdown sequence;
- 63 citation occurrences and 36 unique cited entries are preserved;
- six numbered main sections and all 22 main subsections are present;
- Supplementary Methods S1--S10, Results S1--S6, and S3.1--S3.2 are present;
- main figure/table counts are 4/3;
- Supplement figure/table counts are 6/3;
- representative numerical claims (`22.92%`, `53.96%`, `12.37%`, `32.09%`, `80.79%`, `90.25%`) and `outer_test_loaded=false` are present in extracted PDF text where expected;
- the package bibliography copy is byte-identical to the root file;
- all ten figure copies are byte-identical to their authoritative sources.

Frozen source hashes were rechecked after assembly. The authoritative files remained unchanged:

- `paper/manuscript_full.md`: `91cfb3df5dfa1259b9898b38786d7fcba1082886e71c8937824561db8386fd9c`
- `paper/supplementary_methods.md`: `e21aa2eca445aca247ef7f313d32812cd3ceccec023ef4becb632587b1223745`
- `paper/supplementary_results.md`: `41fecd5e48eb1923ae4d756648bc8299feda1a7c1bbbb379b900f2f455679792`
- `paper/notes.md`: `f3879c7f7a9ae50f024aa728d6e5d36a07726bbd4a69c028776eaa9ae37cef03`
- `paper/technical_closeout_audit.md`: `f9a478871c655f1e2c7c1afbcbf897eb402109ddcfcf9c1317d8dd28f126f9bf`

## 10. Portable archive verification

`paper/mdpi/paper3_mdpi_source.zip` contains 33 source/support files under one top-level directory, `paper3_mdpi_source/`. It excludes the `build/` directory, compiled manuscript PDFs, logs, auxiliary files, QA renders, and generator scratch files. It includes the two TeX sources, metadata and declarations, both bibliography files, the resolved `.bbl`, official template support files, all ten figure PDFs, build script, README, and manifest.

Final archive SHA-256:

`b0a44ee9dbe18f16cfb2fc988276261831f5f1e02da382c1eaaeb5e8066646e3`

The final archive was extracted into a fresh temporary directory and rebuilt with `./build.sh`. The clean build completed successfully and produced 22 main pages and 13 Supplement pages. Its log scan reproduced the same single harmless Supplement underfull-box notice and no errors, undefined references, undefined citations, or overfull boxes. PDF byte hashes are not required to match across builds because the TeX engine records compilation metadata.

## 11. Remaining author decisions

Before journal submission, the author must select the journal and then update its class option, approve or revise the title and keywords, provide authorship/affiliation/correspondence/ORCID data, and complete every declaration. The final journal instructions should then be checked for naming, supplementary-file upload, data statement, AI-tool disclosure, and source-archive requirements.

No further scientific experiment is required by this assembly task. Any later scientific edit must be made first in the authoritative manuscript sources and then deliberately propagated to the derived package.
