#!/usr/bin/env bash
set -euo pipefail

package_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$package_dir"

release_dir="deliverables/authoritative_submission_20261021_v4"
build_dir="$release_dir/build"
mkdir -p "$build_dir"

latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_mdpi.tex
bibtex "$build_dir/paper3_mdpi"
latexmk -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_mdpi.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$build_dir" paper3_supplementary.tex

cp "$build_dir/paper3_mdpi.bbl" paper3_mdpi.bbl
cp "$build_dir/paper3_mdpi.pdf" "$release_dir/paper3_mdpi.pdf"
cp "$build_dir/paper3_supplementary.pdf" "$release_dir/paper3_supplementary.pdf"

printf 'Built authoritative MDPI package:\n  %s\n  %s\n' \
  "$package_dir/$release_dir/paper3_mdpi.pdf" \
  "$package_dir/$release_dir/paper3_supplementary.pdf"
