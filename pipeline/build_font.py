"""Build the handwriting font (TTF/WOFF/WOFF2) from design/glyphs.json.

pen centrelines --(round nib)--> bitmap @ 1px/unit --(potrace)--> cubic
outlines --(cu2qu)--> TrueType, plus calt variant cycling, ss01, kerning.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image
from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path

from strokes import render

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DESIGN = os.path.join(ROOT, "design")
DIST = os.path.join(ROOT, "dist")

FAMILY = "Harshpreet Hand"
PS_FAMILY = "HarshpreetHand"
VERSION = "1.000"
OFL = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
       "This license is available with a FAQ at: https://openfontlicense.org")
UPM = 1000
S = 440                 # font units per x-height (design unit)
SB = 0.13 * S           # ink-to-ink half gap (notes: ~0.2 xh; slightly tightened for reading)
SPACE = 0.72 * S
TIGHT = set(".,:;'’‘\"“”!")   # glyphs that want smaller side bearings
WEIGHTS = {"Regular": dict(pen=0.13, wclass=400), "Bold": dict(pen=0.20, wclass=700)}


def glyph_name(ch):
    cp = ord(ch)
    n = UV2AGL.get(cp)
    return n if n else f"uni{cp:04X}"


def trace(paths, pen_u):
    """paths (font units, y up) -> RecordingPen of outlines in bitmap-local coords.

    Returns (recording, x0, y1, margin, H) so callers can place it.
    """
    a = np.vstack(paths)
    x0, x1, y0, y1 = a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()
    m = int(pen_u) + 6
    W = int(np.ceil(x1 - x0)) + 2 * m
    H = int(np.ceil(y1 - y0)) + 2 * m
    pix = [np.c_[p[:, 0] - x0 + m, (y1 + m) - p[:, 1]] for p in paths]
    bm = render(pix, (H, W), radius=pen_u / 2)[:H, :W]
    with tempfile.TemporaryDirectory() as td:
        pbm = os.path.join(td, "g.pbm")
        svg = os.path.join(td, "g.svg")
        Image.fromarray(((1 - bm) * 255).astype(np.uint8)).convert("1").save(pbm)
        subprocess.run(["potrace", pbm, "-s", "-o", svg, "-u", "1", "--flat", "-a", "1.2", "-O", "1.0", "-t", "4"],
                       check=True)
        txt = open(svg).read()
    rec = RecordingPen()
    for d in re.findall(r'<path d="([^"]+)"', txt, re.S):
        parse_path(d, rec)
    return rec, x0, y1, m, H, bm


class Glyph:
    def __init__(self, name, ch, paths, pen_u, lsb, rsb):
        self.name, self.ch = name, ch
        P = [np.asarray(p, float) * S for p in paths]
        rec, x0, y1, m, H, bm = trace(P, pen_u)
        # potrace coords: X from left, Y up from bitmap bottom
        # font x = X - m + lsb ; font y = y1 + m - H + Y
        dx = -m + lsb
        dy = y1 + m - H
        self.rec = rec
        self.transform = (1, 0, 0, 1, dx, dy)
        ink_w = (np.vstack(P)[:, 0].max() - np.vstack(P)[:, 0].min()) + pen_u
        self.advance = int(round(ink_w + lsb + rsb))
        # profiles for kerning: per 20-unit band, leftmost/rightmost ink x
        self.bm, self.bm_dx, self.bm_top = bm, dx, y1 + m  # bitmap row r -> y = bm_top - r

    def draw_tt(self, glyf_pen):
        rec = RecordingPen()
        tp = TransformPen(rec, self.transform)
        self.rec.replay(tp)
        ap = AreaPen()
        rec.replay(ap)
        target = glyf_pen
        cu = Cu2QuPen(target, max_err=2.0, reverse_direction=False)
        # TrueType: outer contours clockwise -> negative area in AreaPen
        if ap.value > 0:
            rec.replay(ReverseContourPen(cu))
        else:
            rec.replay(cu)

    def profile(self, band=20, lo=-800, hi=1200):
        H, W = self.bm.shape
        nb = (hi - lo) // band
        left = np.full(nb, np.inf)
        right = np.full(nb, -np.inf)
        rows = np.nonzero(self.bm.any(axis=1))[0]
        for r in rows:
            y = self.bm_top - r
            b = int((y - lo) // band)
            if 0 <= b < nb:
                xs = np.nonzero(self.bm[r])[0]
                left[b] = min(left[b], xs[0] + self.bm_dx)
                right[b] = max(right[b], xs[-1] + self.bm_dx)
        return left, right


def build(weight, glyphs_json="glyphs.json"):
    cfg = WEIGHTS[weight]
    pen_u = cfg["pen"] * S
    design = json.load(open(os.path.join(DESIGN, glyphs_json)))
    design_sampled = json.load(open(os.path.join(DESIGN, "glyphs_sampled.json")))
    jobs = []
    for ch, vs in design.items():
        base = glyph_name(ch)
        tight = ch in TIGHT
        lsb = SB * (0.45 if tight else 1.0)
        rsb = SB * (0.9 if tight else 1.0)
        for i, v in enumerate(vs):
            nm = base if i == 0 else f"{base}.alt{i}"
            jobs.append((nm, ch, v["paths"], lsb, rsb))
    # ss01: plain r (no base loop) straight from the samples
    for i, v in enumerate(design_sampled["r"]):
        jobs.append(("r.ss01" if i == 0 else f"r.ss01.alt{i}", None, v["paths"], SB, SB))

    with ThreadPoolExecutor(max_workers=8) as ex:
        built = list(ex.map(lambda j: Glyph(j[0], j[1], j[2], pen_u, j[3], j[4]), jobs))
    G = {g.name: g for g in built}

    order = [".notdef", "space", "uni00A0"] + [g.name for g in built]
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {32: "space", 0xA0: "uni00A0"}
    for g in built:
        if g.ch and "." not in g.name:
            cmap[ord(g.ch)] = g.name
    fb.setupCharacterMap(cmap)

    glyf = {}
    metrics = {}
    # .notdef: a hand-drawn-ish box
    nd = Glyph(".notdef", None, [np.array([[0, 0], [0.7, 0], [0.7, 1.56], [0, 1.56], [0, 0]])], pen_u, SB, SB)
    for g in [nd] + built:
        pen = TTGlyphPen(None)
        g.draw_tt(pen)
        gl = pen.glyph()
        glyf[g.name] = gl
    for nm in ("space", "uni00A0"):
        glyf[nm] = TTGlyphPen(None).glyph()
    fb.setupGlyf(glyf)
    for g in [nd] + built:
        gl = glyf[g.name]
        gl.recalcBounds(fb.font["glyf"])
        metrics[g.name] = (g.advance, getattr(gl, "xMin", 0))
    metrics["space"] = (int(SPACE), 0)
    metrics["uni00A0"] = (int(SPACE), 0)
    fb.setupHorizontalMetrics(metrics)

    ymax = max(getattr(glyf[n], "yMax", 0) for n in glyf)
    ymin = min(getattr(glyf[n], "yMin", 0) for n in glyf)
    asc, desc = 950, -550
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    xh = int(round(0.94 * S + pen_u / 2))
    cap = int(round(1.56 * S + pen_u / 2))
    style = weight
    fb.setupNameTable({
        "copyright": "Copyright 2026 Harshpreet Singh",
        "familyName": FAMILY,
        "styleName": style,
        "uniqueFontIdentifier": f"{PS_FAMILY}-{style};{VERSION}",
        "fullName": f"{FAMILY} {style}",
        "version": f"Version {VERSION}",
        "psName": f"{PS_FAMILY}-{style}",
        "designer": "Harshpreet Singh (handwriting)",
        "description": "A font made from Harshpreet Singh's handwritten Computer Networks notes: "
                       "ring-dotted i, looped l and r, curled d, and three variants per letter "
                       "that rotate automatically (calt).",
        "sampleText": "Hello, I'm Harshpreet - I build things for the web.",
        "licenseDescription": OFL,
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(
        sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
        usWinAscent=max(asc, ymax), usWinDescent=max(-desc, -ymin),
        sxHeight=xh, sCapHeight=cap, usWeightClass=cfg["wclass"],
        fsSelection=(0x20 if weight == "Bold" else 0x40) | 0x80,  # BOLD/REGULAR + USE_TYPO_METRICS
        achVendID="HPSH", fsType=0, version=4,
    )
    fb.setupPost(isFixedPitch=0, underlinePosition=-180, underlineThickness=int(pen_u * 0.8))
    from fontTools.misc.timeTools import timestampNow
    fb.setupHead(unitsPerEm=UPM, fontRevision=float(VERSION), macStyle=1 if weight == "Bold" else 0,
                 created=timestampNow(), modified=timestampNow())

    fea = features(design, G)
    addOpenTypeFeaturesFromString(fb.font, fea)
    os.makedirs(DIST, exist_ok=True)
    base = os.path.join(DIST, f"{PS_FAMILY}-{style}")
    fb.save(base + ".ttf")
    from fontTools.ttLib import TTFont
    for flavor in ("woff", "woff2"):
        f = TTFont(base + ".ttf")
        f.flavor = flavor
        f.save(f"{base}.{flavor}")
    from ink import SCRATCH
    os.makedirs(SCRATCH, exist_ok=True)
    open(os.path.join(SCRATCH, f"features-{style}.fea"), "w").write(fea)
    return base + ".ttf"


def features(design, G):
    cyc_def, cyc_a1, cyc_a2 = [], [], []
    for ch, vs in design.items():
        if len(vs) < 2 or not (ch.isalnum()):
            continue
        b = glyph_name(ch)
        cyc_def.append(b)
        cyc_a1.append(f"{b}.alt1")
        cyc_a2.append(f"{b}.alt2" if len(vs) > 2 else b)
    single = [glyph_name(ch) for ch, vs in design.items() if len(vs) == 1 and ch.isalnum()]
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", ""]
    lines.append(f"@cyc_def = [{' '.join(cyc_def)}];")
    lines.append(f"@cyc_a1 = [{' '.join(cyc_a1)}];")
    lines.append(f"@cyc_a2 = [{' '.join(cyc_a2)}];")
    lines.append(f"@cyc_one = [{' '.join(single)}];")
    lines.append("")
    # Rotate through the writer's variants so repeated letters never look stamped.
    lines.append("feature calt {")
    lines.append("  lookup cycle {")
    lines.append("    sub @cyc_a1 @cyc_def' by @cyc_a2;")
    lines.append("    sub [@cyc_def @cyc_one] @cyc_def' by @cyc_a1;")
    lines.append("  } cycle;")
    lines.append("} calt;")
    lines.append("")
    rs = sorted(n for n in G if n.startswith("r.ss01"))
    src = ["r"] + [f"r.alt{i}" for i in range(1, len(rs)) if f"r.alt{i}" in G]
    dst = rs[:len(src)]
    lines.append("feature ss01 {")
    lines.append('  featureNames { name "Plain r (no base loop)"; };')
    lines.append(f"  sub [{' '.join(src)}] by [{' '.join(dst)}];")
    lines.append("} ss01;")
    lines.append("")
    lines.append(kerning(design, G))
    return "\n".join(lines)


def kerning(design, G, band=20, lo=-800, hi=1200):
    """Optical kerning from ink profiles, per base-letter class (incl. variants)."""
    classes = {}
    for ch, vs in design.items():
        b = glyph_name(ch)
        members = [b] + [f"{b}.alt{i}" for i in range(1, len(vs))]
        members = [m for m in members if m in G]
        if not members:
            continue
        L = R = None
        for m in members:
            l, r = G[m].profile(band, lo, hi)
            adv = G[m].advance
            rr = adv - r  # distance from ink to advance edge (right side bearing profile)
            L = l if L is None else np.minimum(L, l)
            R = rr if R is None else np.minimum(R, rr)
        # dilate a band so shapes don't collide diagonally
        L = np.minimum(L, np.minimum(np.r_[L[1:], np.inf], np.r_[np.inf, L[:-1]]) + 8)
        R = np.minimum(R, np.minimum(np.r_[R[1:], np.inf], np.r_[np.inf, R[:-1]]) + 8)
        classes[ch] = (b, members, L, R)
    ref = 2 * SB
    kern_chars = [c for c in classes if c.isalnum() or c in ".,:;!?)(-'\"&"]
    out = []
    pairs = []
    for a in kern_chars:
        for c in kern_chars:
            _, _, _, Ra = classes[a]
            _, _, Lc, _ = classes[c]
            gap = Ra + Lc
            ok = np.isfinite(gap)
            if ok.sum() < 3:
                continue
            g = gap[ok].min()
            k = (ref - g) * 0.6
            k = max(-0.3 * S, min(0.0, k))
            if k <= -20:
                pairs.append((a, c, int(round(k / 2) * 2)))
    for ch in kern_chars:
        b, members, _, _ = classes[ch]
        out.append(f"@k_{b.replace('.', '_')} = [{' '.join(members)}];")
    out.append("feature kern {")
    for a, c, k in pairs:
        A = glyph_name(a).replace(".", "_")
        C = glyph_name(c).replace(".", "_")
        out.append(f"  pos @k_{A} @k_{C} {k};")
    out.append("} kern;")
    print(f"kerning pairs: {len(pairs)}", file=sys.stderr)
    return "\n".join(out)


if __name__ == "__main__":
    for w in sys.argv[1:] or ["Regular", "Bold"]:
        print(build(w))
