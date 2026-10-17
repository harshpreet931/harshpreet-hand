"""Edits and constructed glyphs, drawn with the same pen model.

Everything here is in x-height units (baseline 0, y up) as pen centrelines.
Constructed shapes borrow the writer's own parts wherever possible (ring
i-dots, comma strokes, the x, the C, the curved arrow head) so they sit in
the same hand.
"""
import numpy as np

from design import CAP, XT, bounds, fit_box


def spline(pts, n=40, closed=False):
    """Catmull-Rom through control points."""
    P = np.asarray(pts, float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


def circle(cx, cy, r, n=28, start=0.0):
    a = np.linspace(start, start + 2 * np.pi, n)
    return np.c_[cx + r * np.cos(a), cy + r * np.sin(a)]


def dot(x, y, r=0.035):
    return circle(x, y, r, 14)


def shift(paths, dx=0.0, dy=0.0):
    return [np.c_[p[:, 0] + dx, p[:, 1] + dy] for p in paths]


def scale(paths, sx, sy=None, ox=0.0, oy=0.0):
    sy = sx if sy is None else sy
    return [np.c_[(p[:, 0] - ox) * sx + ox, (p[:, 1] - oy) * sy + oy] for p in paths]


def mirror_x(paths):
    x0, x1, _, _ = bounds(paths)
    return [np.c_[x1 - (p[:, 0] - x0), p[:, 1]] for p in paths]


def rotate(paths, deg, cx, cy):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return [np.c_[cx + (p[:, 0] - cx) * c - (p[:, 1] - cy) * s, cy + (p[:, 0] - cx) * s + (p[:, 1] - cy) * c] for p in paths]


def norm_left(paths):
    x0, _, _, _ = bounds(paths)
    return shift(paths, -x0)


def V(g, ch, i=0):
    return [p.copy() for p in g[ch][i]["paths"]]


def ring_of(ipaths):
    """The i's ring dot = the path(s) above x-height."""
    return [p for p in ipaths if p[:, 1].min() > XT * 1.05]


def stem_of(ipaths):
    return [p for p in ipaths if p[:, 1].min() <= XT * 1.05]


def compress_desc(paths, f=0.86, floor=-1.22):
    out = [np.c_[p[:, 0], np.where(p[:, 1] < 0, p[:, 1] * f, p[:, 1])] for p in paths]
    lo = min(p[:, 1].min() for p in out)
    if lo < floor:
        k = floor / lo
        out = [np.c_[p[:, 0], np.where(p[:, 1] < 0, p[:, 1] * k, p[:, 1])] for p in out]
    return out


def add_r_loop(paths, r=0.135):
    """Writer's r has a small loop where the stem meets the baseline: the stroke
    comes down the stem, curls back up to the left and closes on itself."""
    a = np.vstack(paths)
    k = np.argmin(a[:, 1])
    bx, by = a[k]
    cx, cy = bx - r * 0.55, by + r * 0.95
    loop = spline([(bx, by + 0.06), (bx - 0.02, by), (cx - r * 0.5, by + 0.02), (cx - r, cy),
                   (cx - r * 0.45, cy + r * 0.85), (bx + 0.01, cy + r * 0.55)], 10)
    return [np.c_[p[:, 0] + r * 0.9, p[:, 1]] for p in paths + [loop]]


def arrow_fit(paths, width=1.5, ymid=0.47, head=0.5):
    x0, x1, y0, y1 = bounds(paths)
    L = x1 - x0
    hx = x1 - head
    new_shaft = width - head

    def fx(x):
        return np.where(x < hx, (x - x0) * new_shaft / (hx - x0), new_shaft + (x - hx))
    out = [np.c_[fx(p[:, 0]), p[:, 1]] for p in paths]
    _, _, y0, y1 = bounds(out)
    # the shaft defines the arrow's height; centre the shaft line
    shaft_y = np.median(np.vstack(out)[:, 1])
    return shift(out, 0, ymid - shaft_y)


def build(g):
    """Mutates and extends the glyph dict g {ch: [{'paths': [...]}, ...]}."""
    P = lambda paths: dict(paths=[np.asarray(p, float) for p in paths], src="constructed")

    # --- edits on sampled glyphs -------------------------------------------
    for ch in "gjpqy":
        for v in g.get(ch, []):
            v["paths"] = compress_desc(v["paths"], 0.86 if ch in "gy" else 0.95)
    for v in g["r"]:
        v["paths"] = add_r_loop(v["paths"])
    for v in g["0"]:
        x0, x1, y0, y1 = bounds(v["paths"])
        v["paths"] = scale(v["paths"], 0.68 * (y1 - y0) / (x1 - x0), 1.0, x0, 0)
    g["="] = [P([spline([(0.0, 0.64), (0.28, 0.66), (0.56, 0.63)], 8), spline([(0.02, 0.29), (0.3, 0.3), (0.58, 0.28)], 8)])]
    for ch, w in (("+", 0.62),):
        for v in g[ch]:
            x0, x1, y0, y1 = bounds(v["paths"])
            s = w / max(x1 - x0, 1e-6)
            ps = scale(v["paths"], s, s, x0, (y0 + y1) / 2)
            v["paths"] = shift(ps, 0, 0.46 - (y0 + y1) / 2)
    for v in g["."]:
        x0, x1, y0, y1 = bounds(v["paths"])
        v["paths"] = [dot(0.03, 0.04, 0.03)]
    for v in g["→"]:
        v["paths"] = arrow_fit(v["paths"])

    ring = ring_of(V(g, "i", 0))
    ring2 = ring_of(V(g, "i", 1))
    comma = V(g, ",", 1)

    # --- capitals ---------------------------------------------------------
    # G = the writer's C + a bar and spur
    G = []
    for i in range(len(g["C"])):
        c = V(g, "C", i)
        x0, x1, y0, y1 = bounds(c)
        a = np.vstack(c)
        lower = a[a[:, 1] < 0.45 * CAP]
        ex = lower[:, 0].max() if len(lower) else x1
        bar = spline([(ex - 0.34, 0.66), (ex - 0.1, 0.68), (ex + 0.05, 0.66)], 12)
        spur = spline([(ex + 0.05, 0.66), (ex + 0.06, 0.35), (ex + 0.02, 0.12)], 12)
        G.append(P(c + [bar, spur]))
    g["G"] = G
    # J: top bar (like the writer's I) + stem + hook
    J = []
    for i, jit in enumerate((0.0, 0.03)):
        bar = spline([(0.05, CAP - 0.01), (0.4, CAP + 0.01 + jit), (0.78, CAP)], 12)
        stem = spline([(0.46, CAP + 0.01), (0.47, 0.8), (0.45, 0.28), (0.34, 0.03), (0.16, 0.0), (0.04, 0.16 + jit)], 20)
        J.append(P([bar, stem]))
    g["J"] = J
    # X = the writer's x at cap height
    g["X"] = [P(fit_box(V(g, "x", i), 0.0, CAP)[0]) for i in range(len(g["x"]))]
    # K: the writer's two K samples are small - keep them but make sure they are at cap height
    # W, V, Z: single samples are fine.

    # --- punctuation --------------------------------------------------------
    d0 = dot(0.03, 0.04, 0.03)
    g[":"] = [P([d0, dot(0.03, 0.66, 0.03)])]
    cm = norm_left(comma)
    cmx = bounds(cm)[1]
    g[";"] = [P(cm + [dot(cmx * 0.6, 0.66, 0.03)])]
    g["!"] = [P([spline([(0.1, 1.58), (0.08, 1.0), (0.05, 0.42)], 12), dot(0.04, 0.04, 0.03)])]
    g["?"] = [P([spline([(0.0, 1.30), (0.18, 1.55), (0.46, 1.58), (0.6, 1.36), (0.46, 1.06), (0.28, 0.86), (0.27, 0.46)], 16),
                 dot(0.27, 0.04, 0.03)])]
    ap = spline([(0.08, 1.62), (0.06, 1.46), (0.0, 1.30)], 10)
    g["'"] = [P([ap])]
    g["\""] = [P([ap, shift([ap], 0.24)[0]])]
    g["’"] = g["'"]
    g["‘"] = [P(rotate([ap], 180, 0.04, 1.46))]
    g["”"] = g["\""]
    g["“"] = [P(rotate([ap, shift([ap], 0.24)[0]], 180, 0.16, 1.46))]
    g["`"] = [P([spline([(0.0, 1.6), (0.12, 1.42)], 6)])]
    g["_"] = [P([spline([(0.0, -0.28), (0.45, -0.27), (0.9, -0.29)], 12)])]
    g["|"] = [P([spline([(0.02, 1.72), (0.0, 0.7), (0.02, -0.36)], 12)])]
    g["\\"] = [P(mirror_x(V(g, "/", i))) for i in range(len(g["/"]))]
    g["–"] = [P(scale(V(g, "-", 0), 1.5, 1.0, 0, 0.46))]
    g["—"] = [P(scale(V(g, "-", 0), 2.6, 1.0, 0, 0.46))]
    g["…"] = [P([d0, dot(0.33, 0.04, 0.03), dot(0.66, 0.04, 0.03)])]
    g["·"] = [P([dot(0.04, 0.46, 0.035)])]
    g["•"] = [P([circle(0.1, 0.5, 0.075, 20), circle(0.1, 0.5, 0.03, 12)])]
    g["°"] = [P([p for p in shift(ring, 0, 0)])]
    g[")"] = g[")"] + [P(mirror_x(V(g, "(", 1)))]
    g["["] = [P([spline([(0.3, 1.70), (0.02, 1.71), (0.0, 0.6), (0.02, -0.35), (0.3, -0.36)], 8)])]
    g["]"] = [P(mirror_x(g["["][0]["paths"]))]
    g["{"] = [P([spline([(0.36, 1.71), (0.18, 1.62), (0.17, 0.9), (0.02, 0.68), (0.17, 0.46), (0.16, -0.24), (0.36, -0.36)], 14)])]
    g["}"] = [P(mirror_x(g["{"][0]["paths"]))]
    g["<"] = [P([spline([(0.55, 0.9), (0.0, 0.47), (0.56, 0.05)], 10)])]
    g[">"] = [P(mirror_x(g["<"][0]["paths"]))]
    g["^"] = [P([spline([(0.0, 1.05), (0.25, 1.55), (0.5, 1.07)], 8)])]
    g["~"] = [P([spline([(0.0, 0.42), (0.16, 0.56), (0.36, 0.44), (0.56, 0.36), (0.72, 0.5)], 12)])]
    g["*"] = [P([spline([(0.25, 1.52), (0.24, 0.98)], 4), spline([(0.02, 1.38), (0.47, 1.1)], 4), spline([(0.03, 1.1), (0.46, 1.4)], 4)])]
    g["#"] = [P([spline([(0.3, 1.45), (0.2, 0.0)], 4), spline([(0.64, 1.45), (0.54, 0.0)], 4),
                 spline([(0.02, 1.0), (0.84, 1.02)], 4), spline([(0.0, 0.45), (0.8, 0.47)], 4)])]
    Sx = fit_box(V(g, "S", 0), 0.0, 1.45)[0]
    sx0, sx1, _, _ = bounds(Sx)
    g["$"] = [P(Sx + [spline([((sx0 + sx1) / 2 + 0.02, 1.62), ((sx0 + sx1) / 2 - 0.02, -0.18)], 6)])]
    o = fit_box(V(g, "o", 1), 0.0, 0.46)[0]
    ow = bounds(o)[1]
    g["%"] = [P(shift(o, 0, 1.0) + [spline([(ow + 0.55, 1.5), (0.08, -0.02)], 6)] + shift(o, ow + 0.2, 0.0))]
    a = V(g, "a", 0)
    ax0, ax1, ay0, ay1 = bounds(a)
    a = shift(scale(a, 0.8), 0.28, 0.25)
    swirl = spline([(ax1 * 0.8 + 0.34, 0.3), (ax1 * 0.8 + 0.5, 0.36), (ax1 * 0.8 + 0.62, 0.8), (0.72, 1.28), (0.2, 1.2),
                    (0.0, 0.62), (0.16, 0.08), (0.62, -0.1), (1.0, 0.02)], 16)
    g["@"] = [P(a + [swirl])]
    x = V(g, "x", 1)
    g["×"] = [P(shift(fit_box(x, 0.2, 0.74)[0], 0.02, 0))]
    g["÷"] = [P(V(g, "-", 0) + [dot(0.28, 0.82, 0.03), dot(0.28, 0.12, 0.03)])]

    # arrows in other directions from the writer's →
    rt = g["→"]
    g["←"] = [P(mirror_x(v["paths"])) for v in rt]
    up = []
    for v in rt[:2]:
        x0, x1, y0, y1 = bounds(v["paths"])
        r = rotate(v["paths"], 90, (x0 + x1) / 2, 0.47)
        rx0, _, ry0, _ = bounds(r)
        up.append(P(shift(r, -rx0, -ry0 - 0.05)))
    g["↑"] = up
    g["↓"] = [P(rotate(v["paths"], 180, bounds(v["paths"])[1] / 2, 0.75)) for v in up]

    # --- lowercase extras --------------------------------------------------
    g["ı"] = [P(stem_of(v["paths"])) for v in g["i"]]
    return g


ACCENTS = {
    # name: builder(width_center_x, top_y) -> paths
}


def accent_paths(kind, cx, top, ring):
    gap = 0.2
    y = top + gap
    if kind == "acute":
        return [spline([(cx - 0.06, y), (cx + 0.12, y + 0.24)], 6)]
    if kind == "grave":
        return [spline([(cx + 0.06, y), (cx - 0.12, y + 0.24)], 6)]
    if kind == "circ":
        return [spline([(cx - 0.17, y), (cx, y + 0.2), (cx + 0.17, y + 0.01)], 8)]
    if kind == "tilde":
        return [spline([(cx - 0.2, y + 0.04), (cx - 0.08, y + 0.16), (cx + 0.06, y + 0.06), (cx + 0.2, y + 0.16)], 8)]
    if kind == "diaer":
        # the writer dots with little rings - use two small rings
        r = ring
        rx0, rx1, ry0, ry1 = bounds(r)
        rr = scale(r, 0.5)
        rx0, rx1, ry0, ry1 = bounds(rr)
        w = rx1 - rx0
        a = shift(rr, cx - 0.17 - w / 2 - rx0, y - 0.02 - ry0)
        b = shift(rr, cx + 0.17 - w / 2 - rx0, y - 0.02 - ry0)
        return a + b
    if kind == "ring":
        return shift(ring, cx - (bounds(ring)[0] + bounds(ring)[1]) / 2, y - bounds(ring)[2])
    if kind == "cedilla":
        return [spline([(cx, 0.0), (cx - 0.01, -0.12), (cx + 0.12, -0.18), (cx + 0.08, -0.3), (cx - 0.08, -0.32)], 8)]
    raise KeyError(kind)


COMPOSITES = {
    "à": ("a", "grave"), "á": ("a", "acute"), "â": ("a", "circ"), "ã": ("a", "tilde"), "ä": ("a", "diaer"), "å": ("a", "ring"),
    "è": ("e", "grave"), "é": ("e", "acute"), "ê": ("e", "circ"), "ë": ("e", "diaer"),
    "ì": ("ı", "grave"), "í": ("ı", "acute"), "î": ("ı", "circ"), "ï": ("ı", "diaer"),
    "ò": ("o", "grave"), "ó": ("o", "acute"), "ô": ("o", "circ"), "õ": ("o", "tilde"), "ö": ("o", "diaer"),
    "ù": ("u", "grave"), "ú": ("u", "acute"), "û": ("u", "circ"), "ü": ("u", "diaer"),
    "ñ": ("n", "tilde"), "ç": ("c", "cedilla"), "ý": ("y", "acute"), "ÿ": ("y", "diaer"),
    "À": ("A", "grave"), "Á": ("A", "acute"), "Â": ("A", "circ"), "Ã": ("A", "tilde"), "Ä": ("A", "diaer"), "Å": ("A", "ring"),
    "È": ("E", "grave"), "É": ("E", "acute"), "Ê": ("E", "circ"), "Ë": ("E", "diaer"),
    "Ì": ("I", "grave"), "Í": ("I", "acute"), "Î": ("I", "circ"), "Ï": ("I", "diaer"),
    "Ò": ("O", "grave"), "Ó": ("O", "acute"), "Ô": ("O", "circ"), "Õ": ("O", "tilde"), "Ö": ("O", "diaer"),
    "Ù": ("U", "grave"), "Ú": ("U", "acute"), "Û": ("U", "circ"), "Ü": ("U", "diaer"),
    "Ñ": ("N", "tilde"), "Ç": ("C", "cedilla"), "Ý": ("Y", "acute"),
}


def build_composites(g):
    ring = [p for p in ring_of(V(g, "i", 1))]
    ring = shift(ring, -bounds(ring)[0], -bounds(ring)[2])
    for ch, (base, kind) in COMPOSITES.items():
        vs = []
        for v in g[base]:
            ps = [p.copy() for p in v["paths"]]
            x0, x1, y0, y1 = bounds(ps)
            if kind == "cedilla":
                a = np.vstack(ps)
                low = a[a[:, 1] < 0.2]
                cx = np.median(low[:, 0]) if len(low) else (x0 + x1) / 2
            else:
                cx = (x0 + x1) / 2
            top = y1 if kind != "cedilla" else 0
            if base.isupper():
                top = max(top, CAP)
                acc = accent_paths(kind, cx, top - 0.04, ring)
            else:
                acc = accent_paths(kind, cx, max(top, XT), ring)
            vs.append(dict(paths=ps + acc, src="composite"))
        g[ch] = vs
    return g
