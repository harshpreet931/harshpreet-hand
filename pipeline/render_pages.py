"""Render every PDF page to PNG (1 px = 1 pt; the scans are embedded at that size)."""
import os
import sys

import fitz

from ink import RENDER

HERE = os.path.dirname(os.path.abspath(__file__))
pdf = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "CN_CompleteNotes_FullSyllabus.pdf")
os.makedirs(RENDER, exist_ok=True)
doc = fitz.open(pdf)
for i, page in enumerate(doc):
    out = f"{RENDER}/p{i:03d}.png"
    if not os.path.exists(out):
        page.get_pixmap(matrix=fitz.Matrix(1, 1)).save(out)
print(len(doc), "pages ->", RENDER)
