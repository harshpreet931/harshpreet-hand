"""Render specific words big with numbered letter groups: python showword.py out.png 3:38 92:19 ..."""
import pickle
import sys

import cv2
import numpy as np

from ink import SCRATCH
from segment import PALETTE

out = sys.argv[1]
tiles = []
for spec in sys.argv[2:]:
    p, wid = map(int, spec.split(":"))
    ws = pickle.load(open(f"{SCRATCH}/seg/p{p:03d}.pkl", "rb"))
    w = [x for x in ws if x["id"] == wid][0]
    bx, by, bw, bh = w["bbox"]
    t = np.full((bh, bw, 3), 255, np.uint8)
    for li, L in enumerate(w["letters"]):
        t[L["mask"]] = PALETTE[li % len(PALETTE)][::-1]
    s = min(4.0, 700 / bw, 160 / bh)
    t = cv2.resize(t, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
    t = np.pad(t, ((30, 6), (6, 6), (0, 0)), constant_values=255)
    for li, L in enumerate(w["letters"]):
        x, y, lw, lh = L["bbox"]
        cv2.putText(t, str(li), (int((x + lw / 2) * s), 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, PALETTE[li % len(PALETTE)][::-1], 2)
    cv2.putText(t, spec, (t.shape[1] - 80, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    tiles.append(t)
W = max(t.shape[1] for t in tiles)
img = np.vstack([np.pad(t, ((0, 4), (0, W - t.shape[1]), (0, 0)), constant_values=200) for t in tiles])
cv2.imwrite(out, img)
