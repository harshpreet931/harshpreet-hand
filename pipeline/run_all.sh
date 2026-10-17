#!/usr/bin/env bash
# Rebuild Harshpreet Hand from the notes PDF.
#   ./run_all.sh          full pipeline (≈10 min)
#   ./run_all.sh font     only rebuild fonts + specimen from design/glyphs.json
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" != "font" ]]; then
  python3 render_pages.py          # PDF -> page images
  python3 segment_all.py           # ink extraction, words, letter groups
  python3 harvest.py | tail -3     # labels/*.txt -> letter samples
  python3 select_samples.py > /dev/null   # typicality + sharpness ranking
  python3 design.py                # picks + normalization + constructions -> design/glyphs.json
fi
python3 build_font.py            # -> dist/*.ttf, *.woff, *.woff2
python3 make_specimen.py "${HH_WORK:-../work}/specimen-inline.html"
