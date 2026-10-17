"""Stroke reconstruction: bitmap -> skeleton graph -> smooth centrelines -> pen.

Photos blur the ballpoint strokes, so instead of tracing blobby pixels we
recover the pen path (centreline) and re-draw it with a clean round nib.
"""
import cv2
import numpy as np
from skimage.morphology import skeletonize, remove_small_holes

from glyphs import XH

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def clean_bitmap(bm, xh=XH):
    pad = 12
    b = np.pad(bm.astype(np.float32), pad)
    b = cv2.GaussianBlur(b, (0, 0), xh * 0.025)
    b = b > 0.5
    b = remove_small_holes(b, max_size=int((xh * 0.05) ** 2))
    return b, pad


def neighbours(sk, y, x):
    H, W = sk.shape
    out = []
    for dy, dx in NB:
        yy, xx = y + dy, x + dx
        if 0 <= yy < H and 0 <= xx < W and sk[yy, xx]:
            out.append((yy, xx))
    return out


def trace_graph(sk):
    """Return list of polylines (each an array of (x, y)) covering the skeleton."""
    sk = sk.copy()
    ys, xs = np.nonzero(sk)
    deg = {}
    for y, x in zip(ys, xs):
        deg[(y, x)] = len(neighbours(sk, y, x))
    nodes = {p for p, d in deg.items() if d != 2}
    visited = set()
    paths = []

    def walk(start, nxt):
        path = [start, nxt]
        visited.add(frozenset((start, nxt)))
        prev, cur = start, nxt
        while cur not in nodes:
            nb = [q for q in neighbours(sk, *cur) if q != prev and frozenset((cur, q)) not in visited]
            if not nb:
                break
            # prefer 4-connected continuation
            nb.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            q = nb[0]
            visited.add(frozenset((cur, q)))
            path.append(q)
            prev, cur = cur, q
            if cur == start:
                break
        return path

    for n in nodes:
        for q in neighbours(sk, *n):
            if frozenset((n, q)) not in visited:
                paths.append(walk(n, q))
    # pure cycles (no nodes)
    for p in deg:
        if deg[p] == 2 and not any(frozenset((p, q)) in visited for q in neighbours(sk, *p)):
            q = neighbours(sk, *p)[0]
            paths.append(walk(p, q))
    return [np.array([(x, y) for y, x in path], np.float32) for path in paths if len(path) >= 2], nodes, deg


def path_len(p):
    return float(np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1))) if len(p) > 1 else 0.0


def prune(sk, spur):
    """Remove short endpoint->junction branches (skeleton noise), iteratively."""
    sk = sk.copy()
    for _ in range(3):
        paths, nodes, deg = trace_graph(sk)
        removed = False
        for p in paths:
            a = (int(p[0][1]), int(p[0][0])); b = (int(p[-1][1]), int(p[-1][0]))
            da, db = deg.get(a, 0), deg.get(b, 0)
            is_spur = (da == 1 and db >= 3) or (db == 1 and da >= 3)
            if is_spur and path_len(p) < spur:
                end = a if da == 1 else b
                for x, y in p.astype(int):
                    if (y, x) != (b if end == a else a):
                        sk[y, x] = False
                removed = True
        if not removed:
            break
        sk = skeletonize(sk)
    return sk


def resample(p, step=1.5):
    if len(p) < 2:
        return p
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    if d[-1] < step:
        return p[[0, -1]]
    t = np.arange(0, d[-1], step)
    t = np.r_[t, d[-1]]
    return np.c_[np.interp(t, d, p[:, 0]), np.interp(t, d, p[:, 1])]


def smooth(p, sigma, closed=False):
    if len(p) < 5:
        return p
    k = int(sigma * 3)
    w = np.exp(-0.5 * (np.arange(-k, k + 1) / sigma) ** 2)
    w /= w.sum()
    if closed:
        q = np.vstack([p[-k - 1:-1], p, p[1:k + 1]])
        return np.c_[np.convolve(q[:, 0], w, "valid"), np.convolve(q[:, 1], w, "valid")]
    # pin endpoints: pad by reflection so ends stay put
    q = np.vstack([2 * p[0] - p[k:0:-1], p, 2 * p[-1] - p[-2:-k - 2:-1]])
    return np.c_[np.convolve(q[:, 0], w, "valid"), np.convolve(q[:, 1], w, "valid")]


def _dir_at(p, at_start, n=8):
    """Unit direction pointing *away* from the path end (into the junction)."""
    q = p if at_start else p[::-1]
    k = min(len(q) - 1, n)
    v = q[0] - q[k]
    nv = np.linalg.norm(v)
    return v / nv if nv > 0 else v


def merge_through_junctions(paths, tol=2.5, max_dev=50):
    """Join path pairs that meet at a junction and continue ~straight through it."""
    paths = [p for p in paths if len(p) >= 2]
    changed = True
    while changed:
        changed = False
        ends = []
        for i, p in enumerate(paths):
            ends.append((i, True, p[0]))
            ends.append((i, False, p[-1]))
        best = None
        for a in range(len(ends)):
            for b in range(a + 1, len(ends)):
                i, sa, pa = ends[a]
                j, sb, pb = ends[b]
                if i == j or np.linalg.norm(pa - pb) > tol:
                    continue
                # count how many path ends meet here (only merge at real junctions)
                da = _dir_at(paths[i], sa)
                db = _dir_at(paths[j], sb)
                # straight continuation: directions into the junction are opposite
                dev = np.degrees(np.arccos(np.clip(-np.dot(da, db), -1, 1)))
                if dev < max_dev and (best is None or dev < best[0]):
                    best = (dev, i, sa, j, sb)
        if best:
            _, i, sa, j, sb = best
            pi = paths[i] if not sa else paths[i][::-1]   # ends at junction
            pj = paths[j] if sb else paths[j][::-1]       # starts at junction
            merged = np.vstack([pi, pj[1:]])
            paths = [p for k, p in enumerate(paths) if k not in (i, j)] + [merged]
            changed = True
    return paths


def drop_stubs(paths, min_len):
    return [p for p in paths if path_len(p) >= min_len or len(paths) == 1]


def centrelines(bm, xh=XH):
    """Binary glyph (design raster) -> list of smooth centreline polylines."""
    b, pad = clean_bitmap(bm, xh)
    sk = skeletonize(b)
    sk = prune(sk, spur=xh * 0.14)
    paths, nodes, deg = trace_graph(sk)
    # tiny edges inside junction clusters are artefacts
    paths = [p for p in paths if path_len(p) > 2.5 or len(paths) == 1]
    paths = merge_through_junctions([p.astype(np.float64) for p in paths])
    paths = drop_stubs(paths, xh * 0.04)
    out = []
    for p in paths:
        closed = len(p) > 8 and np.linalg.norm(p[0] - p[-1]) < 2.5
        q = resample(p, 1.0)
        q = smooth(q, sigma=xh * 0.035, closed=closed)
        q = resample(q, 1.5)
        out.append(q - pad)
    return out


def render(paths, shape, radius, scale=1.0, margin=0):
    """Draw polylines with a round nib. Returns uint8 0/1 bitmap."""
    H, W = shape
    img = np.zeros((int(H * scale) + 2 * margin, int(W * scale) + 2 * margin), np.uint8)
    r = max(1, int(round(radius * scale)))
    for p in paths:
        q = np.round((p * scale + margin) * 16).astype(np.int32)
        if len(q) == 1:
            cv2.circle(img, tuple(q[0]), r * 16, 1, -1, cv2.LINE_8, 4)
            continue
        cv2.polylines(img, [q.reshape(-1, 1, 2)], False, 1, 2 * r, cv2.LINE_8, 4)
        cv2.circle(img, tuple(q[0]), r * 16, 1, -1, cv2.LINE_8, 4)
        cv2.circle(img, tuple(q[-1]), r * 16, 1, -1, cv2.LINE_8, 4)
    return img
