"""Ink extraction: isolate blue-pen strokes from notebook photos.

Removes paper texture, ruled lines, red margins, lighting gradients and
back-page show-through, returning a float "ink strength" map in [0,1].
"""
import cv2
import numpy as np

import os

# Intermediate data (page renders, segmentation, samples). Regenerable; not
# part of the deliverable. Override with HH_WORK=/some/dir.
SCRATCH = os.environ.get("HH_WORK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work"))
RENDER = f"{SCRATCH}/render"


def load_page(i):
    return cv2.imread(f"{RENDER}/p{i:03d}.png")  # BGR


def ink_strength(bgr):
    img = bgr.astype(np.float32)
    B, G, R = img[..., 0], img[..., 1], img[..., 2]
    # Blueness: ink is saturated blue; paper is pale lavender, ruled lines are
    # grey-blue, the margin is red, show-through is faint and desaturated.
    blu = np.clip((B - (R + G) / 2) / np.maximum(B, 1), 0, 1)
    # Remove the page's local "paper blueness" (lavender tint varies with light).
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    paper = cv2.morphologyEx(blu, cv2.MORPH_OPEN, k)
    paper = cv2.GaussianBlur(paper, (0, 0), 10)
    s = np.clip(blu - paper, 0, 1)
    # Darkness relative to local background (bright paper).
    gray = 0.45 * R + 0.45 * G + 0.10 * B
    bg = cv2.dilate(gray, k)
    bg = cv2.GaussianBlur(bg, (0, 0), 10)
    dark = np.clip((bg - gray) / np.maximum(bg, 1), 0, 1)
    # Page mask: exclude red tablecloth / dark surroundings.
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return s, dark


def line_kernel(length, angle_deg):
    a = np.deg2rad(angle_deg)
    h = int(np.ceil(abs(np.tan(a)) * length)) + 1
    k = np.zeros((h, length), np.uint8)
    xs = np.arange(length)
    ys = np.round(xs * np.tan(a)).astype(int)
    ys -= ys.min()
    k[ys, xs] = 1
    return k


def remove_rules(weak, run=45, reach=4):
    w = weak.astype(np.uint8)
    lines = np.zeros_like(w)
    # rules curve / tilt with the page, so try a fan of shallow angles
    for ang in (-5, -3.5, -2, -1, 0, 1, 2, 3.5, 5):
        lines |= cv2.morphologyEx(w, cv2.MORPH_OPEN, line_kernel(run, ang))
    # thicken slightly vertically to catch the antialiased rule edges
    lines = cv2.dilate(lines, np.ones((3, 1), np.uint8))
    lines = lines.astype(bool)
    rest = weak & ~lines
    # restore rule pixels that are bridged vertically by ink (letter crossings)
    up = np.zeros_like(rest)
    dn = np.zeros_like(rest)
    for d in range(1, reach + 1):
        up[d:] |= rest[:-d]
        dn[:-d] |= rest[d:]
    bridge = lines & up & dn
    # only bridge narrow columns (letter strokes), not long stretches
    return lines & ~bridge


def binarize(bgr, half=0.5):
    s, dark = ink_strength(bgr)
    score = np.sqrt(s * dark)
    score = cv2.GaussianBlur(score, (0, 0), 0.6)
    # Robust threshold: Otsu on pixels that have any ink signal.
    v = score[score > 0.05]
    if len(v) < 100:
        return score, np.zeros_like(score, np.uint8)
    t, _ = cv2.threshold((np.clip(v, 0, 1) * 255).astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    t = max(t / 255.0, 0.12)
    # Half-maximum rule: a pixel is ink if it reaches `half` of the local stroke
    # peak. Keeps stroke widths faithful on blurry photos.
    peak = cv2.dilate(score, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    halfmax = score > half * peak
    strong = (score > t) & halfmax
    weak = (score > t * 0.55) & halfmax
    # Ruled-line removal (staff-line style): long horizontal runs are notebook
    # rules / underlines. Remove them, but keep pixels where a letter stroke
    # passes vertically through the rule.
    lines = remove_rules(weak)
    # keep rule pixels that are much stronger than the rule itself: that is
    # ink written on top of the rule (e.g. descender loops)
    if lines.any():
        rule_level = np.median(score[lines])
        lines &= score < rule_level + 0.22
    weak = weak & ~lines
    strong = strong & ~lines
    # Hysteresis: strong seeds grown into weaker connected ink.
    n, lab = cv2.connectedComponents(weak.astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool)
    keep[np.unique(lab[strong])] = True
    keep[0] = False
    mask = keep[lab].astype(np.uint8)
    return score, mask


if __name__ == "__main__":
    import sys
    i = int(sys.argv[1])
    bgr = load_page(i)
    score, mask = binarize(bgr)
    out = sys.argv[2]
    cv2.imwrite(out + "_score.png", (255 - np.clip(score * 255 * 2, 0, 255)).astype(np.uint8))
    cv2.imwrite(out + "_mask.png", (255 - mask * 255).astype(np.uint8))
