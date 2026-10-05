#!/usr/bin/env bash
set -euo pipefail

package_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$package_dir"

release_dir="deliverables/targeted_revision_20261005_v1"
build_dir="$release_dir/build"
mkdir -p "$build_dir"

latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_mdpi.tex
# With an out-of-tree build and a resolved bibliography retained beside the
# source, latexmk can reuse the source-side .bbl instead of regenerating it in
# the versioned build directory. Run BibTeX explicitly on the fresh auxiliary
# file, then let latexmk complete the required TeX passes.
bibtex "$build_dir/paper3_mdpi"
latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_mdpi.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_supplementary.tex

cp "$build_dir/paper3_mdpi.bbl" paper3_mdpi.bbl
cp "$build_dir/paper3_mdpi.pdf" "$release_dir/paper3_mdpi.pdf"
cp "$build_dir/paper3_supplementary.pdf" "$release_dir/paper3_supplementary.pdf"

printf 'Built targeted revision:\n  %s\n  %s\n' \
  "$package_dir/$release_dir/paper3_mdpi.pdf" \
  "$package_dir/$release_dir/paper3_supplementary.pdf"
