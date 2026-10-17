"""Segment a binarized notebook page into words and letter candidates.

Writes a pickle per page with word crops + per-letter-candidate masks, and a
contact-sheet PNG of numbered words (tinted per letter candidate) used for
manual transcription.
"""
import os
import pickle
import sys

import cv2
import numpy as np

from ink import SCRATCH, binarize, load_page

SEG = f"{SCRATCH}/seg"
os.makedirs(SEG, exist_ok=True)

PALETTE = [(230, 25, 75), (60, 140, 60), (0, 90, 220), (245, 130, 48), (145, 30, 180),
           (0, 160, 160), (200, 40, 200), (120, 110, 0), (0, 0, 128), (128, 0, 0)]


def components(mask):
    n, lab, st, cen = cv2.connectedComponentsWithStats(mask, connectivity=8)
    comps = []
    for k in range(1, n):
        x, y, w, h, a = st[k]
        if a < 8:
            continue
        if h <= 4 and w >= 10:  # leftover rule fragment
            continue
        if h > 95 or w > 220:  # diagram boxes / long arrows
            continue
        comps.append(dict(k=k, x=x, y=y, w=w, h=h, a=a))
    return lab, comps


def group_words(mask, lab, comps, gapx=22, gapy=9):
    keep = np.zeros(lab.max() + 1, bool)
    for c in comps:
        keep[c["k"]] = True
    m = keep[lab].astype(np.uint8)
    d = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_RECT, (gapx, gapy)))
    n, wl = cv2.connectedComponents(d, connectivity=8)
    words = {}
    for c in comps:
        ys, xs = np.nonzero(lab[c["y"]:c["y"] + c["h"], c["x"]:c["x"] + c["w"]] == c["k"])
        wid = wl[c["y"] + ys[0], c["x"] + xs[0]]
        words.setdefault(wid, []).append(c)
    return list(words.values())


def xoverlap(a, b):
    lo = max(a["x"], b["x"])
    hi = min(a["x"] + a["w"], b["x"] + b["w"])
    return max(0, hi - lo)


def merge_letters(ccs):
    """Merge components that stack vertically (i-dots, t-bars, split strokes)."""
    groups = [dict(x=c["x"], y=c["y"], w=c["w"], h=c["h"], ks=[c["k"]], a=c["a"]) for c in ccs]
    changed = True
    while changed:
        changed = False
        groups.sort(key=lambda g: g["x"] + g["w"] / 2)
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                a, b = groups[i], groups[j]
                ov = xoverlap(a, b)
                if ov >= 0.5 * min(a["w"], b["w"]):
                    x0 = min(a["x"], b["x"]); y0 = min(a["y"], b["y"])
                    x1 = max(a["x"] + a["w"], b["x"] + b["w"]); y1 = max(a["y"] + a["h"], b["y"] + b["h"])
                    groups[i] = dict(x=x0, y=y0, w=x1 - x0, h=y1 - y0, ks=a["ks"] + b["ks"], a=a["a"] + b["a"])
                    del groups[j]
                    changed = True
                    break
            if changed:
                break
    groups.sort(key=lambda g: g["x"] + g["w"] / 2)
    return groups


def process(page):
    bgr = load_page(page)
    score, mask = binarize(bgr)
    lab, comps = components(mask)
    words = group_words(mask, lab, comps)
    out = []
    for ccs in words:
        x0 = min(c["x"] for c in ccs); y0 = min(c["y"] for c in ccs)
        x1 = max(c["x"] + c["w"] for c in ccs); y1 = max(c["y"] + c["h"] for c in ccs)
        if x1 - x0 < 6 or y1 - y0 < 10:
            continue  # dots, specks
        if len(ccs) > 40:
            continue
        groups = merge_letters(ccs)
        pad = 4
        X0, Y0 = max(0, x0 - pad), max(0, y0 - pad)
        X1, Y1 = min(mask.shape[1], x1 + pad), min(mask.shape[0], y1 + pad)
        sub = lab[Y0:Y1, X0:X1]
        letters = []
        for g in groups:
            m = np.isin(sub, g["ks"])
            letters.append(dict(bbox=(g["x"] - X0, g["y"] - Y0, g["w"], g["h"]), mask=m))
        out.append(dict(page=page, bbox=(X0, Y0, X1 - X0, Y1 - Y0), letters=letters,
                        score=score[Y0:Y1, X0:X1].astype(np.float16)))
    # reading order: sort by line (y center bucket), then x
    out.sort(key=lambda w: (w["bbox"][1] + w["bbox"][3] / 2) // 40 * 10000 + w["bbox"][0])
    for i, w in enumerate(out):
        w["id"] = i
    with open(f"{SEG}/p{page:03d}.pkl", "wb") as f:
        pickle.dump(out, f)
    return out


def is_texty(w):
    hs = [L["bbox"][3] for L in w["letters"]]
    ws_ = [L["bbox"][2] for L in w["letters"]]
    if max(hs) < 10:
        return False
    if len(hs) == 1 and (ws_[0] > 4 * hs[0] or hs[0] > 70):
        return False
    return True


def sheet(words, path, cols=4, cellw=330, cellh=78, scale=1.6, start=0, count=None):
    words = words[start:start + count] if count else words[start:]
    rows = (len(words) + cols - 1) // cols
    img = np.full((rows * cellh, cols * cellw, 3), 255, np.uint8)
    for n, w in enumerate(words):
        r, c = divmod(n, cols)
        bx, by, bw, bh = w["bbox"]
        tile = np.full((bh, bw, 3), 255, np.uint8)
        for li, L in enumerate(w["letters"]):
            tile[L["mask"]] = PALETTE[li % len(PALETTE)][::-1]
        s = min(scale, (cellw - 50) / bw, (cellh - 6) / bh)
        tile = cv2.resize(tile, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        th, tw = tile.shape[:2]
        oy, ox = r * cellh + 3, c * cellw + 46
        img[oy:oy + th, ox:ox + tw] = tile
        cv2.putText(img, str(w["id"]), (c * cellw + 2, r * cellh + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        cv2.putText(img, f"{len(w['letters'])}", (c * cellw + 2, r * cellh + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
        cv2.rectangle(img, (c * cellw, r * cellh), ((c + 1) * cellw - 1, (r + 1) * cellh - 1), (220, 220, 220), 1)
    cv2.imwrite(path, img)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        p = int(p)
        ws = process(p)
        per = 48
        for s in range(0, len(ws), per):
            sheet(ws, f"{SEG}/sheet_p{p:03d}_{s // per}.png", start=s, count=per)
        print(p, len(ws), "words")
