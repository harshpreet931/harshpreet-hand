"""Render text with the stroke design (pre-font preview, mimics calt cycling)."""
import json
import os
import sys

import cv2
import numpy as np

from strokes import render

DESIGN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design")


def load(name="glyphs.json"):
    g = json.load(open(os.path.join(DESIGN, name)))
    return {ch: [[np.array(p) for p in v["paths"]] for v in vs] for ch, vs in g.items()}


def layout(text, glyphs, pen=0.13, sb=0.12, space=0.62):
    """Returns list of (paths shifted) and total width, in x-height units."""
    out = []
    x = 0.0
    cyc = 0
    for ch in text:
        if ch == " ":
            x += space
            cyc = 0
            continue
        vs = glyphs.get(ch)
        if not vs:
            x += space
            continue
        v = vs[cyc % len(vs)]
        cyc += 1
        a = np.vstack(v)
        x0, x1 = a[:, 0].min(), a[:, 0].max()
        left = x + sb + pen / 2 - x0
        out.extend([np.c_[p[:, 0] + left, p[:, 1]] for p in v])
        x += (x1 - x0) + pen + 2 * sb
    return out, x


def draw_lines(lines, glyphs, pen=0.13, sb=0.12, scale=48, line_h=3.0, pad=0.4, name=None):
    laid = [layout(t, glyphs, pen, sb) for t in lines]
    W = int((max(w for _, w in laid) + 2 * pad) * scale)
    H = int((len(lines) * line_h + pad) * scale)
    img = np.full((H, W), 255, np.uint8)
    for i, (paths, w) in enumerate(laid):
        base = (i + 1) * line_h * scale - 0.9 * scale
        pix = [np.c_[(p[:, 0] + pad) * scale, base - p[:, 1] * scale] for p in paths]
        m = render(pix, (H, W), radius=pen * scale / 2)
        img[m[:H, :W] > 0] = 0
    return img


if __name__ == "__main__":
    name = sys.argv[1]
    out = sys.argv[2]
    pen = float(sys.argv[3]) if len(sys.argv) > 3 else 0.13
    g = load(name)
    lines = [
        "the quick brown fox jumps over the lazy dog",
        "Networks, routers & packets: data flows.",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "abcdefghijklmnopqrstuvwxyz 0123456789",
        "Hello, I'm Harshpreet - I build things.",
    ]
    img = draw_lines(lines, g, pen=pen)
    cv2.imwrite(out, img)
