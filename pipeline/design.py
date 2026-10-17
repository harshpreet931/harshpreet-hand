"""Assemble the glyph design: sampled strokes + normalization + constructions.

Output: ../design/glyphs.json  {char: [ {paths: [[[x,y],...],...]}, ... ]}
Units: x-height = 1.0, baseline y = 0, y up. Paths are pen centrelines.
"""
import json
import os
import pickle

import numpy as np

from candidates import sample_paths
from ink import SCRATCH

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.join(HERE, "..", "design")

# centreline targets (x-height units). Ink extends pen/2 beyond these.
XT = 0.94          # x-height letters
ASC = 1.64         # b d h k l
CAP = 1.56
DIG = 1.42
XLET = set("acemnorsuvwxz")
ASCL = dict(b=ASC, d=ASC, h=ASC, k=ASC, l=ASC, f=1.66, t=1.40)
DESCL = set("gpqy")


def bounds(paths):
    a = np.vstack(paths)
    return a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()


def fit_box(paths, bottom, top):
    """Uniformly scale so the vertical extent is [bottom, top]."""
    x0, x1, y0, y1 = bounds(paths)
    s = (top - bottom) / max(1e-6, y1 - y0)
    return [np.c_[(p[:, 0] - x0) * s, (p[:, 1] - y0) * s + bottom] for p in paths], s


def fit_top(paths, top):
    """Scale about the (estimated) baseline so the top lands on `top`."""
    x0, x1, y0, y1 = bounds(paths)
    s = top / max(1e-6, y1)
    return [np.c_[(p[:, 0] - x0) * s, p[:, 1] * s] for p in paths], s


def normalize(ch, paths):
    paths = [np.asarray(p, float) for p in paths]
    if ch in XLET:
        return fit_box(paths, 0.0, XT)
    if ch in ASCL:
        return fit_box(paths, 0.0, ASCL[ch])
    if ch == "i":
        return fit_box(paths, 0.0, 1.74)
    if ch in DESCL:
        return fit_top(paths, XT)
    if ch == "Q":
        return fit_top(paths, CAP)
    if ch.isupper() or ch == "&":
        return fit_box(paths, 0.0, CAP)
    if ch.isdigit():
        return fit_box(paths, 0.0, DIG)
    if ch in "()":
        return fit_box(paths, -0.36, 1.70)
    if ch == "/":
        return fit_box(paths, -0.1, 1.62)
    if ch == ".":
        return centre_at(paths, 0.05, 0.0)
    if ch == ",":
        return fit_box(paths, -0.32, 0.14)
    if ch in "-=+":
        x0, x1, y0, y1 = bounds(paths)
        return centre_at(paths, 0.46, None)
    return paths, 1.0


def centre_at(paths, ymid, ybottom):
    x0, x1, y0, y1 = bounds(paths)
    if ybottom is not None:
        dy = ybottom - y0
    else:
        dy = ymid - (y0 + y1) / 2
    return [np.c_[p[:, 0] - x0, p[:, 1] + dy] for p in paths], 1.0


def load_sampled():
    picks = json.load(open(os.path.join(DESIGN, "picks.json")))
    by = pickle.load(open(f"{SCRATCH}/ranked.pkl", "rb"))
    index = {}
    for ch, ss in by.items():
        for s in ss:
            index[(ch, s["page"], s["wid"], s["li"])] = s
    out = {}
    for ch, srcs in picks.items():
        out[ch] = []
        for src in srcs:
            s = index.get((ch, *src))
            if s is None:
                print("missing sample", ch, src)
                continue
            ps = sample_paths(s)
            ps, sc = normalize(ch, ps)
            if ch.islower() and not (0.65 < sc < 1.5):
                print(f"warn: {ch} {src} scale {sc:.2f}")
            out[ch].append(dict(paths=ps, src=src))
    return out


def save(glyphs, name="glyphs.json"):
    ser = {ch: [dict(paths=[np.round(p, 4).tolist() for p in v["paths"]], **{k: v[k] for k in v if k != "paths"})
                for v in vs] for ch, vs in glyphs.items()}
    json.dump(ser, open(os.path.join(DESIGN, name), "w"))


if __name__ == "__main__":
    import construct
    g = load_sampled()
    save(g, "glyphs_sampled.json")
    g = construct.build(g)
    g = construct.build_composites(g)
    # natural bounce: each alternate sits a hair higher/lower and is a touch
    # bigger/smaller, like consecutive letters written by hand
    JIT = [(1.0, 0.0), (1.02, 0.014), (0.985, -0.012)]
    for ch, vs in g.items():
        if not ch.isalnum():
            continue
        for i, v in enumerate(vs):
            s, dy = JIT[i % 3]
            v["paths"] = [np.c_[np.asarray(p)[:, 0] * s, np.asarray(p)[:, 1] * s + dy] for p in v["paths"]]
    save(g, "glyphs.json")
    print(len(g), "glyphs,", sum(len(v) for v in g.values()), "variants")
