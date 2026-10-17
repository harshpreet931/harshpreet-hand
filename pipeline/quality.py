"""Rank pages by how good a glyph source they are (sharp, large, separated letters)."""
import glob
import pickle
import cv2
import numpy as np
from ink import SCRATCH

rows = []
for f in sorted(glob.glob(f"{SCRATCH}/seg/p*.pkl")):
    ws = pickle.load(open(f, "rb"))
    page = int(f[-7:-4])
    hs, sws, seps = [], [], []
    for w in ws:
        ls = w["letters"]
        if not (3 <= len(ls) <= 14):
            continue
        for L in ls:
            m = L["mask"].astype(np.uint8)
            x, y, bw, bh = L["bbox"]
            if bh < 8 or bw < 4:
                continue
            hs.append(bh)
            dt = cv2.distanceTransform(m, cv2.DIST_L2, 3)
            sws.append(2 * np.percentile(dt[m > 0], 90))
        # separation: average letter width vs word width
        seps.append(len(ls) / max(1, w["bbox"][2]) * 20)
    if len(hs) < 30:
        rows.append((page, 0, 0, 0, 0, len(ws)))
        continue
    h = np.median(hs); sw = np.median(sws)
    rows.append((page, h, sw, sw / h, np.median(seps), len(ws)))

rows.sort(key=lambda r: (r[3] if r[3] else 9))
print("page  letterH  strokeW  sw/h   sep  words")
for r in rows:
    print("%4d  %6.1f  %6.2f  %6.3f  %5.2f  %4d" % r)
