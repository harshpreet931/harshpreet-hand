"""Grid of every glyph variant (for design review)."""
import sys

import cv2
import numpy as np

from preview import load
from strokes import render


def grid(g, chars, out, pen=0.13, scale=44, cols=12):
    tiles = []
    for ch in chars:
        for vi, v in enumerate(g.get(ch, [])):
            W, H = int(2.4 * scale), int(3.9 * scale)
            a = np.vstack(v)
            x0, x1 = a[:, 0].min(), a[:, 0].max()
            off = (2.4 - (x1 - x0)) / 2 - x0
            base = 2.3 * scale
            img = np.full((H, W, 3), 255, np.uint8)
            for yy, col in ((0, (120, 120, 255)), (0.94, (255, 190, 120)), (1.56, (200, 200, 200))):
                img[int(base - yy * scale), :] = col
            pix = [np.c_[(p[:, 0] + off) * scale, base - p[:, 1] * scale] for p in v]
            m = render(pix, (H, W), radius=pen * scale / 2)
            img[m[:H, :W] > 0] = 0
            cv2.putText(img, f"{ch}{vi}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 200), 1)
            tiles.append(np.pad(img, ((1, 1), (1, 1), (0, 0)), constant_values=160))
    rows = []
    for i in range(0, len(tiles), cols):
        r = tiles[i:i + cols]
        r += [np.full_like(tiles[0], 255)] * (cols - len(r))
        rows.append(np.hstack(r))
    cv2.imwrite(out, np.vstack(rows))


if __name__ == "__main__":
    g = load(sys.argv[1])
    grid(g, sys.argv[2], sys.argv[3])
