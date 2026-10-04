#!/usr/bin/env bash
set -euo pipefail

package_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$package_dir"

mkdir -p build

latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir=build paper3_mdpi.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir=build paper3_supplementary.tex

if [[ -f build/paper3_mdpi.bbl ]]; then
  cp build/paper3_mdpi.bbl paper3_mdpi.bbl
elif [[ ! -f paper3_mdpi.bbl ]]; then
  printf 'Missing resolved bibliography: neither build/paper3_mdpi.bbl nor paper3_mdpi.bbl exists.\n' >&2
  exit 1
fi

printf 'Built:\n  %s\n  %s\n' \
  "$package_dir/build/paper3_mdpi.pdf" \
  "$package_dir/build/paper3_supplementary.pdf"
