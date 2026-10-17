"""Normalize letter samples into baseline-aligned, x-height-scaled bitmaps."""
import pickle

import cv2
import numpy as np

from ink import SCRATCH

XH = 100  # design raster: pixels per x-height


def normalize(s, xh_px=XH, pad=3):
    """Return (bitmap uint8 0/1, origin_x, baseline_row) in design raster."""
    x, y, bw, bh = s["bbox"]
    score = s["score"].astype(np.float32)
    H, W = score.shape
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(W, x + bw + pad), min(H, y + bh + pad)
    m = s["mask"].astype(np.uint8)
    region = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    sc = (score * region)[y0:y1, x0:x1]
    # letter-level threshold at half the stroke peak
    inside = score[m > 0]
    peak = np.percentile(inside, 90) if inside.size else 1
    f = xh_px / s["xh"]
    big = cv2.resize(sc, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    # de-rotate by the word slope around the crop centre
    ang = np.degrees(np.arctan(s["slope"]))
    base_row = (s["baseline"] - y0) * f
    if abs(ang) > 0.3:
        c = (big.shape[1] / 2, base_row)
        M = cv2.getRotationMatrix2D(c, ang, 1.0)
        big = cv2.warpAffine(big, M, (big.shape[1], big.shape[0]), flags=cv2.INTER_CUBIC)
    bm = (big > 0.5 * peak).astype(np.uint8)
    # keep only components of meaningful size (drop halo specks)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bm, connectivity=8)
    keep = np.zeros(n, bool)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] >= 0.004 * xh_px * xh_px:
            keep[k] = True
    bm = keep[lab].astype(np.uint8)
    ys, xs = np.nonzero(bm)
    if len(xs) == 0:
        return None
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return dict(bm=bm[by0:by1, bx0:bx1], top=(by0 - base_row) / xh_px, bottom=(by1 - base_row) / xh_px,
                width=(bx1 - bx0) / xh_px)


def to_canvas(g, scale=0.32, asc=2.1, desc=1.0, width=2.4):
    """Place a normalized glyph on a fixed canvas (for comparisons / montages)."""
    k = XH * scale
    Hc, Wc = int((asc + desc) * k), int(width * k)
    can = np.zeros((Hc, Wc), np.float32)
    bm = cv2.resize(g["bm"].astype(np.float32), None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    top = int(round((asc + g["top"]) * k))
    left = int(round((Wc - bm.shape[1]) / 2))
    h, w = bm.shape
    ys, xs = max(0, top), max(0, left)
    ye, xe = min(Hc, top + h), min(Wc, left + w)
    if ye > ys and xe > xs:
        can[ys:ye, xs:xe] = bm[ys - top:ye - top, xs - left:xe - left]
    return can


if __name__ == "__main__":
    import sys
    samples = pickle.load(open(f"{SCRATCH}/samples.pkl", "rb"))
    chars = sys.argv[1] if len(sys.argv) > 1 else "abcdefghijklmnopqrstuvwxyz"
    out = sys.argv[2] if len(sys.argv) > 2 else f"{SCRATCH}/montage.png"
    per = 24
    rows = []
    for ch in chars:
        ss = [s for s in samples if s["ch"] == ch][:per]
        tiles = []
        for s in ss:
            g = normalize(s)
            if g is None:
                continue
            c = to_canvas(g)
            # baseline & x-line guides
            k = XH * 0.32
            img = (255 - c * 255).astype(np.uint8)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            yb = int(2.1 * k); yx = int(1.1 * k)
            img[yb, :] = (img[yb, :] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
            img[yx, :] = (img[yx, :] * 0.5 + np.array([255, 150, 0]) * 0.5).astype(np.uint8)
            tiles.append(img)
        if not tiles:
            continue
        h, w = tiles[0].shape[:2]
        row = np.full((h, 40 + per * (w + 2), 3), 255, np.uint8)
        cv2.putText(row, ch, (8, h // 2 + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        for i, t in enumerate(tiles):
            row[:, 40 + i * (w + 2): 40 + i * (w + 2) + w] = t
        rows.append(row)
        rows.append(np.full((3, row.shape[1], 3), 200, np.uint8))
    cv2.imwrite(out, np.vstack(rows))
