# MDPI-style working manuscript package

This directory is a derived presentation package for Paper 3. The targeted presubmission revision starts from repository revision `b18e9fb117828f31a01f5efcce5b0be57081fa07` and assembles clarified reporting with the official MDPI LaTeX template. It does not replace the Markdown sources in `paper/` or the repository-level `references.bib`.

This is **not yet administratively submission-ready**. The author-provided author order and affiliations have been inserted, together with ORCID identifiers for all six authors, the confirmed BR28713099 funding statement, and the tagged GitHub availability route. The target journal, final title, corresponding-author designation, keywords, and the remaining author declarations still require confirmation. Pending fields are visible rather than silently invented.

## Package layout

- `paper3_mdpi.tex`: readable main manuscript source containing the complete main text, four main figures, and three main tables.
- `paper3_supplementary.tex`: separate Supplementary Materials source containing Supplementary Methods S1--S10, Supplementary Results S1--S6, Tables S1--S4, and Figures S1--S6.
- `metadata.tex`: provisional title, author-provided author order and affiliations, supplied ORCID identifiers, a visible correspondence placeholder, working keywords, and the frozen abstract.
- `declarations.tex`: MDPI declaration fields; the author-confirmed funding statement is populated and all other unverified declarations are explicitly pending.
- `references.bib`: byte-identical copy of the repository-level bibliography.
- `references_mdpi.bib`: documented MDPI-compatible derived bibliography used for the build.
- `paper3_mdpi.bbl`: resolved numeric bibliography for the main manuscript.
- `Definitions/`: official MDPI class, bibliography styles, logos, and support files.
- `figures/`: byte-preserving copies of the ten authoritative baseline PDF figures.
- `figures_revision_20261005/`: four presentation-only copies rendered from frozen plot-data/state tables, with label or layout changes recorded in `artwork_registry.json`.
- `deliverables/targeted_revision_20261005_v1/`: versioned revised PDFs and source archive; the reviewed baseline files under `build/` remain unchanged.
- `deliverables/authorship_funding_update_20261018_v1/`: versioned PDFs and source archive after the author-list, funding, and project-linkage update.
- `deliverables/authorship_orcid_update_20261018_v2/`: versioned PDFs and source archive after completing the six-author ORCID metadata.
- `deliverables/mdpi_repository_link_20261021_v3/`: versioned PDFs and source archive containing the tagged GitHub Data Availability route.
- `source_manifest.json`: provenance, hashes, transformations, toolchain, and output inventory.
- `paper3_mdpi_source.zip`: portable source archive; it excludes generated build auxiliaries and compiled PDFs.

## Template and toolchain

- Official source page: <https://www.mdpi.com/authors/latex>
- Downloaded archive: <https://res.mdpi.com/data/MDPI_template_ACS.zip?v=20260911>
- Archive SHA-256: `62744425fbcec9cd3e58147cbee65bdec2e2ff0440f29792c26edc97a11b6c70`
- MDPI class: version `2026-09-11`, `v6.5a`
- Class options: `notspecified,article,submit,moreauthors` for the main file and `notspecified,supfile,submit,moreauthors` for the Supplement.
- Engine: pdfLaTeX through `latexmk`; bibliography backend: BibTeX with `Definitions/mdpi.bst`.

No journal was selected during assembly. The neutral official `notspecified` option is therefore intentional. The generic class would synthesize a DOI footer from class-internal volume, issue, and article placeholders; the two manuscript sources clear only that unassigned footer. No class or style file was edited.

The official archive contained no standalone license file. Original copyright and license notices embedded in the distributed MDPI files are retained verbatim, and `source_manifest.json` records their upstream archive.

## Build

Requirements: a TeX Live installation containing `latexmk`, pdfLaTeX, BibTeX, and the standard packages loaded by the MDPI class.

To rebuild the targeted revision without overwriting the reviewed baseline PDFs, run:

```sh
./build_targeted_revision.sh
```

To rebuild the later authorship/funding update, run:

```sh
./build_authorship_funding_update.sh
```

To rebuild the complete ORCID update, run:

```sh
./build_authorship_orcid_update.sh
```

To rebuild the MDPI repository-link update, run:

```sh
./build_mdpi_repository_link_update.sh
```

The script produces:

```text
deliverables/targeted_revision_20261005_v1/paper3_mdpi.pdf
deliverables/targeted_revision_20261005_v1/paper3_supplementary.pdf
deliverables/authorship_funding_update_20261018_v1/paper3_mdpi.pdf
deliverables/authorship_funding_update_20261018_v1/paper3_supplementary.pdf
deliverables/authorship_orcid_update_20261018_v2/paper3_mdpi.pdf
deliverables/authorship_orcid_update_20261018_v2/paper3_supplementary.pdf
deliverables/mdpi_repository_link_20261021_v3/paper3_mdpi.pdf
deliverables/mdpi_repository_link_20261021_v3/paper3_supplementary.pdf
```

The historical `build.sh` is retained for provenance but writes to `build/`; it is not used for this revision.

The main manuscript alone uses a BibTeX-generated bibliography. The portable archive includes the resolved `paper3_mdpi.bbl`; `latexmk` can regenerate it from `references_mdpi.bib` when required. The Supplement has no independent citations or bibliography and is built directly with pdfLaTeX through `latexmk`.

## Bibliography derivation

`references.bib` is unchanged from the repository root. `references_mdpi.bib` makes only presentation-compatibility transformations:

1. maps `eid` to `pages` for `Gali2026SystematicReview`, `Xue2020LOPA`, and `Abdullahi2024TemplateAttacks`;
2. represents `Frank2010McGillGaitDataset` as `@www`, retaining its institution, year, URL, access date (`2026-10-03`), and note;
3. removes redundant leading `Proceedings of` or `Proceedings of the` text from six conference `booktitle` fields because the MDPI bibliography style supplies that phrase.

Two verified direct-precedent entries were added: Giot et al.'s BTAS 2012 hybrid updater and its IBPC 2012 evaluation paper. Existing bibliography entries were otherwise retained. The incomplete publication metadata for `Serbin2026AdaptiveLSTM` is deliberately preserved rather than guessed.

## Verification status

The baseline outputs under `build/` are retained unchanged. Verification status for the targeted revision is recorded in `targeted_revision_audit.md` and the versioned source manifest after compilation, full-page visual inspection, and clean-extract rebuilding.
