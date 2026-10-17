"""Score letter samples for typicality (vs. the letter's medoid) and source quality."""
import pickle
from collections import defaultdict

import cv2
import numpy as np

from glyphs import normalize, to_canvas
from ink import SCRATCH

# page sharpness from quality ranking: stroke width / letter height (lower = sharper)
def page_sharpness():
    import subprocess, sys
    out = subprocess.run([sys.executable, "quality.py"], capture_output=True, text=True).stdout.splitlines()[1:]
    d = {}
    for line in out:
        p = line.split()
        d[int(p[0])] = float(p[3])
    return d


def ncc_dist(a, b, shift=3):
    best = -1
    for dy in range(-shift, shift + 1):
        for dx in range(-shift, shift + 1):
            bb = np.roll(np.roll(b, dy, 0), dx, 1)
            num = (a * bb).sum()
            den = np.sqrt((a * a).sum() * (bb * bb).sum()) + 1e-6
            best = max(best, num / den)
    return 1 - best


def run():
    samples = pickle.load(open(f"{SCRATCH}/samples.pkl", "rb"))
    sharp = page_sharpness()
    by = defaultdict(list)
    for i, s in enumerate(samples):
        g = normalize(s)
        if g is None:
            continue
        s["g"] = g
        c = to_canvas(g, scale=0.32, asc=2.3, desc=1.2, width=2.6)
        s["_can"] = cv2.GaussianBlur(c, (0, 0), 1.6)
        by[s["ch"]].append(s)
    for ch, ss in by.items():
        n = len(ss)
        if n >= 3:
            D = np.zeros((n, n))
            for i in range(n):
                for j in range(i + 1, n):
                    D[i, j] = D[j, i] = ncc_dist(ss[i]["_can"], ss[j]["_can"])
            med = np.median(D + np.eye(n) * 9, axis=1) if n > 3 else D.sum(1) / (n - 1)
            for i, s in enumerate(ss):
                s["typ"] = float(np.median(np.delete(D[i], i)))
        else:
            for s in ss:
                s["typ"] = 0.3
        for s in ss:
            q = sharp.get(s["page"], 0.25)
            # lower is better: atypical shape, blurry page, small source size
            s["rank"] = s["typ"] * 3 + (q - 0.15) * 2 + max(0, 22 - s["xh"]) * 0.01 + (0 if s.get("exact") else 0.05)
        ss.sort(key=lambda s: s["rank"])
    for ss in by.values():
        for s in ss:
            s.pop("_can", None)
    pickle.dump(dict(by), open(f"{SCRATCH}/ranked.pkl", "wb"))
    return by


if __name__ == "__main__":
    by = run()
    for ch in sorted(by):
        ss = by[ch]
        print(ch, len(ss), " ".join(f"{s['rank']:.2f}" for s in ss[:6]))
