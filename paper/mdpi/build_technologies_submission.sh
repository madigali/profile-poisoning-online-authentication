#!/usr/bin/env bash
set -euo pipefail

package_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$package_dir"

release_dir="deliverables/technologies_submission_20261021_v5"
build_dir="$release_dir/build"
main_stage="$release_dir/main_source"
kit_stage="$release_dir/upload_kit"

rm -rf "$build_dir" "$main_stage" "$kit_stage" "$release_dir/qa_render"
mkdir -p "$build_dir" "$main_stage/Definitions" \
  "$main_stage/figures" "$main_stage/figures_revision_20261005" "$kit_stage"

latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_mdpi.tex
bibtex "$build_dir/paper3_mdpi"
latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_mdpi.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_supplementary.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" cover_letter_technologies.tex

cp "$build_dir/paper3_mdpi.bbl" paper3_mdpi.bbl
cp "$build_dir/paper3_mdpi.pdf" "$release_dir/Technologies_main_manuscript_preview.pdf"
cp "$build_dir/paper3_supplementary.pdf" "$release_dir/Technologies_supplementary.pdf"
cp "$build_dir/cover_letter_technologies.pdf" "$release_dir/Technologies_cover_letter.pdf"
cp cover_letter_technologies.txt "$release_dir/Technologies_cover_letter.txt"

cp paper3_mdpi.tex metadata.tex declarations.tex references_mdpi.bib paper3_mdpi.bbl "$main_stage/"
cp -R Definitions/. "$main_stage/Definitions/"
cp figures/figure2_boundary_k8_effects.pdf "$main_stage/figures/"
cp figures/figure3_security_adaptation_tradeoff.pdf "$main_stage/figures/"
cp figures_revision_20261005/figure1_poisoning_asr.pdf "$main_stage/figures_revision_20261005/"
cp figures_revision_20261005/figure4_selection_bias_mechanism.pdf "$main_stage/figures_revision_20261005/"

(cd "$main_stage" && zip -q -r ../Technologies_manuscript_main.zip .)

cat > "$release_dir/UPLOAD_MAP.txt" <<'EOF'
TECHNOLOGIES / MDPI UPLOAD MAP

1. Manuscript Files > Manuscript
   Upload: Technologies_manuscript_main.zip
   This ZIP contains only the main LaTeX manuscript and the files required to compile it.
   It does NOT contain the Supplementary Materials.

2. Cover Letter > Cover Letter Files
   Upload: Technologies_cover_letter.pdf
   Alternative: paste the contents of Technologies_cover_letter.txt into the text field.

3. Supplementary File(s)
   Upload: Technologies_supplementary.pdf

4. Graphical Abstract
   Leave empty unless the journal editor specifically requests one.

5. Video Abstract
   Leave empty.

6. Figures, Graphics, Images
   Leave empty for the initial submission because the four main figures are embedded in the manuscript source ZIP.

7. Copyright Permission
   Leave empty: the manuscript does not reproduce third-party copyrighted figures or tables requiring separate permission.

8. Non-published Material
   Leave empty unless you intentionally provide additional material for editorial review only.

IMPORTANT: UNPACK_FIRST_Technologies_submission_kit.zip is only a convenience bundle.
Do not upload that outer ZIP to the Manuscript field. Unpack it and upload the three files listed above to their separate fields.
EOF

cp "$release_dir/Technologies_manuscript_main.zip" "$kit_stage/"
cp "$release_dir/Technologies_cover_letter.pdf" "$kit_stage/"
cp "$release_dir/Technologies_cover_letter.txt" "$kit_stage/"
cp "$release_dir/Technologies_supplementary.pdf" "$kit_stage/"
cp "$release_dir/UPLOAD_MAP.txt" "$kit_stage/"
(cd "$kit_stage" && zip -q -r ../UNPACK_FIRST_Technologies_submission_kit.zip .)

rm -rf "$build_dir" "$main_stage" "$kit_stage"
rm -f "$package_dir/Definitions/logo-mdpi-eps-converted-to.pdf"

printf 'Built Technologies upload package:\n  %s\n  %s\n  %s\n  %s\n' \
  "$package_dir/$release_dir/Technologies_manuscript_main.zip" \
  "$package_dir/$release_dir/Technologies_cover_letter.pdf" \
  "$package_dir/$release_dir/Technologies_supplementary.pdf" \
  "$package_dir/$release_dir/UNPACK_FIRST_Technologies_submission_kit.zip"
