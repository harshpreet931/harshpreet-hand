"""Turn transcribed words into normalized letter samples.

Label files: labels/pNNN.txt, one line per word: `<word id>: <text>`.
Each character of <text> (spaces ignored) must correspond to one letter
candidate (coloured group) in reading order. Special tokens:
  ?      one group, skip it (unsure / damaged)
  [..]   one group that contains several letters (skip)
Words whose group count doesn't match the transcription are skipped.
"""
import glob
import os
import pickle
import re

import numpy as np

from ink import SCRATCH

HERE = os.path.dirname(os.path.abspath(__file__))
XLINE = set("acemnorsuvwxzgpqy")      # top sits on the x-height line
BASE = set("abcdefhiklmnorstuvwxz") | set("ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789") | set("&!?%#@$→")
DESC = set("gjpqy")


def parse(text):
    toks = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == " ":
            i += 1
            continue
        if ch == "\\" and i + 1 < len(text):
            toks.append(text[i + 1])
            i += 2
            continue
        if ch == "[":
            j = text.index("]", i)
            toks.append(None)
            i = j + 1
            continue
        toks.append(None if ch == "?" else ch)
        i += 1
    return toks


def robust_line(xs, ys):
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    if len(xs) >= 3 and np.ptp(xs) > 20:
        # Theil-Sen slope, clipped to small tilts
        sl = []
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                if xs[j] != xs[i]:
                    sl.append((ys[j] - ys[i]) / (xs[j] - xs[i]))
        m = float(np.clip(np.median(sl), -0.08, 0.08))
    else:
        m = 0.0
    b = float(np.median(ys - m * xs))
    return m, b


def load_labels():
    out = {}
    for f in sorted(glob.glob(f"{HERE}/labels/p*.txt")):
        page = int(re.findall(r"p(\d+)", os.path.basename(f))[0])
        for line in open(f):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#") or ":" not in line:
                continue
            wid, text = line.split(":", 1)
            out[(page, int(wid))] = text.strip()
    return out


def letter_stats(pairs_by_word):
    """Median width/height (in x-height units) per char from exactly-matched words."""
    W, H, gaps = {}, {}, []
    for w, pairs, xh in pairs_by_word:
        prev = None
        for gi, ch in pairs:
            x, y, bw, bh = w["letters"][gi]["bbox"]
            W.setdefault(ch, []).append(bw / xh)
            H.setdefault(ch, []).append(bh / xh)
            if prev is not None and prev[0] == gi - 1:
                px = w["letters"][prev[0]]["bbox"]
                gaps.append((x - (px[0] + px[2])) / xh)
            prev = (gi, ch)
    W = {k: float(np.median(v)) for k, v in W.items()}
    H = {k: float(np.median(v)) for k, v in H.items()}
    return W, H, float(np.median(gaps)) if gaps else 0.3


def default_wh(ch):
    if ch in ".,:;'":
        return 0.25, 0.3
    if ch in "-":
        return 0.5, 0.15
    if ch in "/()":
        return 0.5, 1.6
    if ch in "il1I":
        return 0.3, 1.5
    if ch in "mw":
        return 1.4, 1.0
    if ch.isupper() or ch.isdigit():
        return 0.9, 1.6
    if ch in "bdfhklt":
        return 0.8, 1.6
    if ch in "gjpqy":
        return 0.8, 1.6
    return 0.8, 1.0


def align(w, toks, W, H, gap):
    """DP alignment of letter groups to transcribed chars when counts differ.

    Returns [(group_index, char)] for groups confidently holding exactly one char.
    """
    G = w["letters"]
    n, m = len(G), len(toks)
    ws = [W.get(t, default_wh(t)[0]) if t else 0.8 for t in toks]
    hs = [H.get(t, default_wh(t)[1]) if t else 1.2 for t in toks]
    x0 = G[0]["bbox"][0]
    x1 = max(g["bbox"][0] + g["bbox"][2] for g in G)
    s = (x1 - x0) / max(0.1, sum(ws) + gap * (m - 1))  # px per x-height unit
    INF = 1e9
    D = np.full((n + 1, m + 1), INF)
    back = {}
    D[0, 0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            if D[i, j] >= INF or (i == n):
                continue
            g = G[i]["bbox"]
            # group i = noise
            if g[3] < 0.55 * s and g[2] < 0.6 * s:
                c = D[i, j] + 1.5
                if c < D[i + 1, j]:
                    D[i + 1, j] = c; back[(i + 1, j)] = (i, j, "noise")
            # group i = k letters
            for k in (1, 2, 3):
                if j + k > m:
                    break
                exp_w = s * (sum(ws[j:j + k]) + gap * (k - 1))
                cw = (np.log(max(g[2], 1) / max(exp_w, 1))) ** 2 / 0.12
                if k == 1:
                    ch = (np.log(max(g[3], 1) / max(s * hs[j], 1))) ** 2 / 0.08
                else:
                    ch = 0.0
                c = D[i, j] + cw + ch + (0 if k == 1 else 2.0 * (k - 1))
                if c < D[i + 1, j + k]:
                    D[i + 1, j + k] = c; back[(i + 1, j + k)] = (i, j, k, cw + ch)
            # groups i,i+1 = one letter (split stroke)
            if i + 2 <= n and j + 1 <= m:
                g2 = G[i + 1]["bbox"]
                uw = g2[0] + g2[2] - g[0]
                cw = (np.log(max(uw, 1) / max(s * ws[j], 1))) ** 2 / 0.12
                c = D[i, j] + cw + 2.5
                if c < D[i + 2, j + 1]:
                    D[i + 2, j + 1] = c; back[(i + 2, j + 1)] = (i, j, "split")
    if D[n, m] >= INF:
        return []
    pairs = []
    i, j = n, m
    while (i, j) != (0, 0):
        b = back[(i, j)]
        if len(b) == 4 and b[2] == 1 and b[3] < 1.5 and toks[b[1]] is not None:
            pairs.append((b[0], toks[b[1]]))
        i, j = b[0], b[1]
    return pairs[::-1]


def word_lines(w, pairs):
    xs_b, ys_b, xs_t, ys_t = [], [], [], []
    for gi, ch in pairs:
        x, y, bw, bh = w["letters"][gi]["bbox"]
        cx = x + bw / 2
        if ch in BASE:
            xs_b.append(cx); ys_b.append(y + bh)
        if ch in XLINE:
            xs_t.append(cx); ys_t.append(y)
    base = robust_line(xs_b, ys_b) if xs_b else None
    xl = robust_line(xs_t, ys_t) if xs_t else None
    xh = None
    if base and xl and len(xs_t) >= 2 and len(xs_b) >= 2:
        mid = w["bbox"][2] / 2
        v = (base[0] * mid + base[1]) - (xl[0] * mid + xl[1])
        if v > 5:
            xh = v
    return base, xl, xh


def harvest():
    labels = load_labels()
    pages = sorted({p for p, _ in labels})
    stats = dict(words=0, used=0, aligned=0, mismatch=[])
    items = []  # (page, w, toks, exact)
    for page in pages:
        ws = pickle.load(open(f"{SCRATCH}/seg/p{page:03d}.pkl", "rb"))
        byid = {w["id"]: w for w in ws}
        for (p, wid), text in labels.items():
            if p != page or wid not in byid:
                continue
            stats["words"] += 1
            if text.startswith("{"):
                # explicit {group:char, ...} assignment
                pairs = []
                for kv in text.strip("{}").split(","):
                    k, v = kv.split(":")
                    pairs.append((int(k), v.strip()))
                items.append((page, byid[wid], pairs, text))
                continue
            items.append((page, byid[wid], parse(text), text))
    # pass 1: exact matches -> letter width/height priors
    exact = []
    for page, w, toks, text in items:
        if text.startswith("{"):
            continue
        if len(toks) == len(w["letters"]):
            pairs = [(i, t) for i, t in enumerate(toks) if t is not None]
            base, xl, xh = word_lines(w, pairs)
            if xh:
                exact.append((w, pairs, xh))
    W, H, gap = letter_stats(exact)
    # pass 2: all words
    per_page = {}
    for page, w, toks, text in items:
        if text.startswith("{"):
            pairs = toks
        elif len(toks) == len(w["letters"]):
            pairs = [(i, t) for i, t in enumerate(toks) if t is not None]
            stats["used"] += 1
        else:
            pairs = align(w, toks, W, H, gap)
            if not pairs:
                stats["mismatch"].append((page, w["id"], text, len(toks), len(w["letters"])))
                continue
            stats["aligned"] += 1
        per_page.setdefault(page, []).append((w, pairs, text))
    samples = []
    for page, lst in per_page.items():
        info = []
        for w, pairs, text in lst:
            base, xl, xh = word_lines(w, pairs)
            info.append((w, pairs, text, base, xl, xh))
        pxh = [i[5] for i in info if i[5]]
        pxh = float(np.median(pxh)) if pxh else None
        for w, pairs, text, base, xl, xh in info:
            xh = xh or pxh
            if xh is None:
                continue
            if base is None:
                if xl is None:
                    continue
                base = (xl[0], xl[1] + xh)
            m, b = base
            for gi, ch in pairs:
                L = w["letters"][gi]
                x, y, bw, bh = L["bbox"]
                samples.append(dict(
                    ch=ch, page=page, wid=w["id"], li=gi, text=text,
                    mask=L["mask"], score=w["score"], bbox=L["bbox"], slope=m,
                    baseline=m * (x + bw / 2) + b, xh=xh, word_xh=xh if xh != pxh else None,
                    exact=len(pairs) == len(w["letters"]),
                ))
    stats["W"], stats["H"], stats["gap"] = W, H, gap
    return samples, stats


if __name__ == "__main__":
    samples, stats = harvest()
    pickle.dump(samples, open(f"{SCRATCH}/samples.pkl", "wb"))
    from collections import Counter
    c = Counter(s["ch"] for s in samples)
    print(f"words labeled {stats['words']}, exact {stats['used']}, aligned {stats['aligned']}, samples {len(samples)}, gap {stats['gap']:.2f}")
    print("".join(sorted(c)))
    for ch in "abcdefghijklmnopqrstuvwxyz":
        print(ch, c.get(ch, 0), end="  ")
    print()
    for ch in sorted(k for k in c if not k.islower()):
        print(ch, c[ch], end="  ")
    print()
    for m in stats["mismatch"]:
        print("MISMATCH", m)
