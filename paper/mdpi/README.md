# MDPI-style working manuscript package

This directory is a derived presentation package for Paper 3. It preserves the frozen scientific content at Git revision `ad00fb0254f166c146638bfc5c1457552f9593f5` and assembles it with the official MDPI LaTeX template. It does not replace the Markdown sources in `paper/` or the repository-level `references.bib`.

This is **not submission-ready**. The target journal, final title, author identities and order, affiliations, corresponding-author details, ORCID identifiers, keywords, and all author declarations still require confirmation. Pending fields are visible rather than silently invented.

## Package layout

- `paper3_mdpi.tex`: readable main manuscript source containing the complete main text, four main figures, and three main tables.
- `paper3_supplementary.tex`: separate Supplementary Materials source containing Supplementary Methods S1--S10, Supplementary Results S1--S6, Tables S1--S3, and Figures S1--S6.
- `metadata.tex`: provisional title, visible author metadata placeholders, working keywords, and the frozen abstract.
- `declarations.tex`: MDPI declaration fields; all unverified author declarations are explicitly pending.
- `references.bib`: byte-identical copy of the repository-level bibliography.
- `references_mdpi.bib`: documented MDPI-compatible derived bibliography used for the build.
- `paper3_mdpi.bbl`: resolved numeric bibliography for the main manuscript.
- `Definitions/`: official MDPI class, bibliography styles, logos, and support files.
- `figures/`: byte-preserving copies of the ten authoritative PDF figures.
- `build/`: the two verified output PDFs in the distributed package. A local rebuild also places auxiliary files here.
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

From this directory, run:

```sh
./build.sh
```

The script produces:

```text
build/paper3_mdpi.pdf
build/paper3_supplementary.pdf
```

The main manuscript alone uses a BibTeX-generated bibliography. The portable archive includes the resolved `paper3_mdpi.bbl`; `latexmk` can regenerate it from `references_mdpi.bib` when required. The Supplement has no independent citations or bibliography and is built directly with pdfLaTeX through `latexmk`.

## Bibliography derivation

`references.bib` is unchanged from the repository root. `references_mdpi.bib` makes only presentation-compatibility transformations:

1. maps `eid` to `pages` for `Gali2026SystematicReview`, `Xue2020LOPA`, and `Abdullahi2024TemplateAttacks`;
2. represents `Frank2010McGillGaitDataset` as `@www`, retaining its institution, year, URL, access date (`2026-10-03`), and note;
3. removes redundant leading `Proceedings of` or `Proceedings of the` text from six conference `booktitle` fields because the MDPI bibliography style supplies that phrase.

No citation was added, removed, or reordered. The main manuscript resolves 63 citation occurrences to 36 unique bibliography entries. The incomplete publication metadata for `Serbin2026AdaptiveLSTM` is deliberately preserved rather than guessed.

## Verification status

Both files compile successfully. The verified outputs contain 22 main-manuscript pages and 13 Supplement pages. Every page was rendered and visually inspected. The final logs contain no LaTeX errors, undefined references, undefined citations, or overfull boxes. One harmless underfull-box notice remains in the Supplement where a long provenance path is line-broken. The source ZIP was rebuilt in a fresh directory as a portability check.
