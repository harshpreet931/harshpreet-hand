"""Export real pipeline artefacts for the Remotion video (work/video_assets/)."""
import json
import os
import pickle

import cv2
import numpy as np

from candidates import drop_specks
from glyphs import normalize
from harvest import load_labels
from ink import SCRATCH, binarize, ink_strength, load_page
from strokes import centrelines

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "work", "video_assets")
DESIGN = os.path.join(HERE, "..", "design")
INK = np.array([140, 47, 31], np.uint8)  # BGR of #1f2f8c


def ensure(d):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
    return os.path.join(OUT, d)


def ink_rgba(mask, color=INK):
    h, w = mask.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = color
    out[..., 3] = (mask * 255).astype(np.uint8)
    return out


def pages():
    d = ensure("pages")
    for i in range(120):
        im = load_page(i)
        t = cv2.resize(im, (216, 288), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{d}/p{i:03d}.jpg", t, [cv2.IMWRITE_JPEG_QUALITY, 78])


def ink_stages():
    d = ensure("ink")
    bgr = load_page(2)
    y0, y1, x0, x1 = 820, 1070, 180, 1560
    crop = bgr[y0:y1, x0:x1]
    cv2.imwrite(f"{d}/photo.jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
    s, dark = ink_strength(bgr)
    blu = np.clip(s[y0:y1, x0:x1] * 2.2, 0, 1)
    cv2.imwrite(f"{d}/signal.png", ink_rgba(blu, np.array([90, 60, 40], np.uint8)))
    score, mask = binarize(bgr)
    cv2.imwrite(f"{d}/mask.png", ink_rgba(mask[y0:y1, x0:x1].astype(np.float32)))
    return dict(width=x1 - x0, height=y1 - y0)


WORDS = [(4, 33), (81, 7), (4, 10), (38, 31), (92, 19), (93, 38), (98, 64), (96, 21), (92, 17), (81, 42), (52, 51), (84, 127)]
PALETTE = [(230, 25, 75), (60, 140, 60), (0, 90, 220), (245, 130, 48), (145, 30, 180), (0, 160, 160), (200, 40, 200), (120, 110, 0)]


def words():
    d = ensure("words")
    labels = load_labels()
    meta = []
    for k, (p, wid) in enumerate(WORDS):
        ws = {w["id"]: w for w in pickle.load(open(f"{SCRATCH}/seg/p{p:03d}.pkl", "rb"))}
        w = ws[wid]
        X, Y, bw, bh = [int(v) for v in w["bbox"]]
        im = load_page(p)
        pad = 6
        c = im[max(0, Y - pad):Y + bh + pad, max(0, X - pad):X + bw + pad]
        H = 120
        c = cv2.resize(c, (int(c.shape[1] * H / c.shape[0]), H), interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(f"{d}/w{k:02d}.jpg", c, [cv2.IMWRITE_JPEG_QUALITY, 88])
        # letter groups tinted
        seg = np.zeros((bh + 8, bw + 8, 4), np.uint8)
        for li, L in enumerate(w["letters"]):
            m = L["mask"]
            col = PALETTE[li % len(PALETTE)]
            seg[:m.shape[0], :m.shape[1]][m] = (*col[::-1], 255)
        seg = seg[:bh + 2 * 4, :bw + 2 * 4]
        seg = cv2.resize(seg, (int(seg.shape[1] * H / seg.shape[0]), H), interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(f"{d}/s{k:02d}.png", seg)
        text = labels.get((p, wid), "")
        if text.startswith("{"):
            text = "Jitter" if (p, wid) == (92, 19) else "Queuing"
        meta.append(dict(img=f"words/w{k:02d}.jpg", seg=f"words/s{k:02d}.png", label=text.replace("\\?", "?"),
                         w=c.shape[1], h=H, page=p + 1, groups=len(w["letters"])))
    return meta


def samples():
    d = ensure("samples")
    by = pickle.load(open(f"{SCRATCH}/ranked.pkl", "rb"))
    picks = json.load(open(os.path.join(DESIGN, "picks.json")))
    rows = []
    for ch in "adegr":
        ss = by[ch]
        pick_src = [tuple(x) for x in picks[ch]]
        chosen = [s for s in ss if (s["page"], s["wid"], s["li"]) in pick_src]
        others = [s for s in ss[:30] if (s["page"], s["wid"], s["li"]) not in pick_src]
        # interleave: 9 others + the 3 picks at fixed positions
        seq = others[:9]
        slots = {"a": (1, 5, 10), "d": (3, 4, 9), "e": (0, 7, 11), "g": (2, 6, 8), "r": (4, 8, 10)}[ch]
        for pos, s in zip(slots, chosen):
            seq.insert(pos, s)
        tiles = []
        for i, s in enumerate(seq[:12]):
            g = s.get("g") or normalize(s)
            bm = g["bm"]
            XHP = 58  # x-height in tile pixels
            TW, TH = 130, int(3.0 * XHP)
            f = XHP / 100
            b = cv2.resize(bm.astype(np.float32), None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
            tile = np.zeros((TH, TW, 4), np.uint8)
            top = int(round((1.75 + g["top"]) * XHP))
            left = (TW - b.shape[1]) // 2
            hh, ww = b.shape
            ys, xs = max(0, top), max(0, left)
            ye, xe = min(TH, top + hh), min(TW, left + ww)
            if ye > ys and xe > xs:
                sub = b[ys - top:ye - top, xs - left:xe - left]
                tile[ys:ye, xs:xe, :3] = INK
                tile[ys:ye, xs:xe, 3] = np.clip(sub * 255, 0, 255).astype(np.uint8)
            fn = f"samples/{ch}{i:02d}.png"
            cv2.imwrite(os.path.join(OUT, fn), tile)
            tiles.append(dict(src=fn, pick=(s["page"], s["wid"], s["li"]) in pick_src, page=s["page"] + 1))
        rows.append(dict(ch=ch, count=len(ss), tiles=tiles))
    return rows


def redraw():
    """One real sample: photo -> binary -> centreline -> pen."""
    d = ensure("redraw")
    by = pickle.load(open(f"{SCRATCH}/ranked.pkl", "rb"))
    picks = json.load(open(os.path.join(DESIGN, "picks.json")))
    src = tuple(picks["g"][0])
    s = [x for x in by["g"] if (x["page"], x["wid"], x["li"]) == src][0]
    ws = {w["id"]: w for w in pickle.load(open(f"{SCRATCH}/seg/p{s['page']:03d}.pkl", "rb"))}
    w = ws[s["wid"]]
    X, Y = int(w["bbox"][0]), int(w["bbox"][1])
    x, y, bw, bh = [int(v) for v in s["bbox"]]
    im = load_page(s["page"])
    pad = 4
    c = im[Y + y - pad:Y + y + bh + pad, X + x - pad:X + x + bw + pad]
    cv2.imwrite(f"{d}/photo.png", cv2.resize(c, None, fx=12, fy=12, interpolation=cv2.INTER_NEAREST))
    g = s.get("g") or normalize(s)
    bm = drop_specks(g["bm"], "g")
    paths = centrelines(bm)
    cv2.imwrite(f"{d}/bitmap.png", ink_rgba(bm.astype(np.float32), np.array([120, 90, 70], np.uint8)))
    return dict(photo=dict(w=c.shape[1] * 12, h=c.shape[0] * 12, src_w=int(c.shape[1]), src_h=int(c.shape[0])),
                bitmap=dict(w=int(bm.shape[1]), h=int(bm.shape[0])),
                paths=[np.round(p, 2).tolist() for p in paths], page=s["page"] + 1, word=s["text"])


# ---------- handwriting animation data from the real font design ----------
SB, PEN, SPACE = 0.13, 0.13, 0.72


def order_paths(paths):
    """Writing order: main strokes left->right, then dots/rings/accents."""
    def is_dot(p):
        return p[:, 1].min() > 1.02 or (np.ptp(p[:, 0]) < 0.3 and np.ptp(p[:, 1]) < 0.3 and p[:, 1].min() > 0.9)
    main = [p for p in paths if not is_dot(p)]
    dots = [p for p in paths if is_dot(p)]
    out = []
    for p in sorted(main, key=lambda p: p[:, 0].min()) + dots:
        a, b = p[0], p[-1]
        # start at the upper-left end
        if (b[0] - a[0]) + 0.5 * (a[1] - b[1]) < 0 and not np.allclose(a, b):
            p = p[::-1]
        out.append(p)
    return out


def phrase(text, design, start_variant=0):
    x = 0.0
    cyc = start_variant
    glyphs = []
    for ch in text:
        if ch == " ":
            x += SPACE
            cyc = 0
            continue
        vs = design.get(ch)
        if not vs:
            x += SPACE
            continue
        v = vs[cyc % len(vs)] if (ch.isalnum()) else vs[0]
        cyc += 1
        P = [np.asarray(p) for p in v["paths"]]
        a = np.vstack(P)
        x0, x1 = a[:, 0].min(), a[:, 0].max()
        left = x + SB + PEN / 2 - x0
        P = order_paths([np.c_[p[:, 0] + left, p[:, 1]] for p in P])
        segs = []
        for p in P:
            d = "M" + " L".join(f"{px:.3f} {-py:.3f}" for px, py in p)
            L = float(np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1))) if len(p) > 1 else 0.01
            segs.append(dict(d=d, len=round(max(L, 0.01), 4)))
        glyphs.append(dict(ch=ch, paths=segs))
        x += (x1 - x0) + PEN + 2 * SB
    return dict(text=text, width=round(x, 3), glyphs=glyphs)


def writing():
    design = json.load(open(os.path.join(DESIGN, "glyphs.json")))
    phrases = ["my notes", "a font", "Harshpreet Hand", "hello", "i", "l", "r", "d", "t", "2", "&", "→", "Claude Opus 5.5"]
    return {p: phrase(p, design) for p in phrases}


if __name__ == "__main__":
    import sys
    meta = {}
    steps = sys.argv[1:] or ["pages", "ink", "words", "samples", "redraw", "writing"]
    if "pages" in steps:
        pages()
    if "ink" in steps:
        meta["ink"] = ink_stages()
    if "words" in steps:
        meta["words"] = words()
    if "samples" in steps:
        meta["samples"] = samples()
    if "redraw" in steps:
        meta["redraw"] = redraw()
    if "writing" in steps:
        meta["writing"] = writing()
    path = os.path.join(OUT, "assets.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(meta)
    json.dump(old, open(path, "w"))
    print({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in old.items()})
