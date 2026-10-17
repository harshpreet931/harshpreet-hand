"""Turn ranked samples into stroke candidates and render review sheets.

Each candidate = centreline paths in x-height units (x from ink left edge,
y up from baseline), ready to be re-stroked with a uniform pen.
"""
import pickle
import sys

import cv2
import numpy as np

from glyphs import XH
from ink import SCRATCH
from strokes import centrelines, render

KEEP_SMALL = set("ij:;!?%=\"'.,") | set("ÄÖÜäöü")


def drop_specks(bm, ch):
    n, lab, st, _ = cv2.connectedComponentsWithStats(bm.astype(np.uint8), connectivity=8)
    if n <= 2:
        return bm
    areas = st[1:, cv2.CC_STAT_AREA]
    big = areas.max()
    keep = np.zeros(n, bool)
    for k in range(1, n):
        a = st[k, cv2.CC_STAT_AREA]
        if ch in KEEP_SMALL:
            keep[k] = a >= 0.03 * big
        else:
            keep[k] = a >= 0.15 * big
    return keep[lab].astype(np.uint8)


def sample_paths(s):
    g = s["g"]
    bm = drop_specks(g["bm"], s["ch"])
    paths = centrelines(bm)
    # bitmap coords (px, y down, origin top-left of glyph box) -> xh units, y up from baseline
    out = []
    for p in paths:
        x = p[:, 0] / XH
        y = -(p[:, 1] / XH + g["top"])
        out.append(np.c_[x, y])
    if not out:
        return None
    x0 = min(p[:, 0].min() for p in out)
    return [np.round(np.c_[p[:, 0] - x0, p[:, 1]], 4) for p in out]


def draw(paths, pen=0.13, scale=60, asc=2.0, desc=1.6, width=None, guides=True):
    w = width or (max(p[:, 0].max() for p in paths) + 0.5)
    H, W = int((asc + desc) * scale), int(w * scale)
    img = np.full((H, W, 3), 255, np.uint8)
    if guides:
        for yy, col in ((0, (120, 120, 255)), (1, (255, 190, 120)), (1.7, (200, 200, 200))):
            r = int((asc - yy) * scale)
            img[r, :] = col
    pix = [np.c_[(p[:, 0] + 0.25) * scale, (asc - p[:, 1]) * scale] for p in paths]
    m = render(pix, (H, W), radius=pen * scale / 2)
    img[m[:H, :W] > 0] = (0, 0, 0)
    return img


def run(chars, out, per=10):
    by = pickle.load(open(f"{SCRATCH}/ranked.pkl", "rb"))
    cands = {}
    rows = []
    for ch in chars:
        ss = by.get(ch, [])[:per]
        cl = []
        tiles = []
        for i, s in enumerate(ss):
            ps = sample_paths(s)
            if ps is None:
                continue
            cl.append(dict(paths=ps, src=(s["page"], s["wid"], s["li"]), rank=s["rank"]))
            t = draw(ps, scale=40, width=2.1)
            cv2.putText(t, str(len(cl) - 1), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 200), 1)
            tiles.append(t)
        cands[ch] = cl
        if not tiles:
            continue
        label = np.full((tiles[0].shape[0], 36, 3), 255, np.uint8)
        cv2.putText(label, ch, (6, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        row = np.hstack([label] + [np.pad(t, ((0, 0), (1, 1), (0, 0)), constant_values=150) for t in tiles])
        rows.append(row)
    W = max(r.shape[1] for r in rows)
    img = np.vstack([np.pad(r, ((0, 3), (0, W - r.shape[1]), (0, 0)), constant_values=200) for r in rows])
    cv2.imwrite(out, img)
    return cands


if __name__ == "__main__":
    chars = sys.argv[1]
    out = sys.argv[2]
    c = run(chars, out)
    old = {}
    try:
        old = pickle.load(open(f"{SCRATCH}/cands.pkl", "rb"))
    except Exception:
        pass
    old.update(c)
    pickle.dump(old, open(f"{SCRATCH}/cands.pkl", "wb"))
