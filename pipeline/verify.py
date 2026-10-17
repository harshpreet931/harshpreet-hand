"""Render text through HarfBuzz (shaping: calt/kern) + FreeType (rasterizing)."""
import sys

import freetype
import numpy as np
import uharfbuzz as hb
from PIL import Image


def shape(fontfile, text, features=None):
    blob = hb.Blob.from_file_path(fontfile)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return buf.glyph_infos, buf.glyph_positions, font


def render(fontfile, lines, size=64, features=None, line_h=1.9, pad=20, fg=0, bg=255):
    ft = freetype.Face(fontfile)
    ft.set_char_size(size * 64)
    upm = ft.units_per_EM
    sc = size / upm
    rows = []
    for text in lines:
        infos, poss, _ = shape(fontfile, text, features)
        width = int(sum(p.x_advance for p in poss) * sc) + 2 * pad
        H = int(size * line_h)
        img = np.full((H, max(width, 10)), bg, np.uint8)
        x = pad
        base = int(size * 1.0)
        for info, pos in zip(infos, poss):
            ft.load_glyph(info.codepoint, freetype.FT_LOAD_DEFAULT)
            ft.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
            bmp = ft.glyph.bitmap
            if bmp.width:
                a = np.array(bmp.buffer, np.uint8).reshape(bmp.rows, bmp.pitch)[:, :bmp.width]
                gx = int(round(x + pos.x_offset * sc)) + ft.glyph.bitmap_left
                gy = base - ft.glyph.bitmap_top - int(pos.y_offset * sc)
                y0, x0 = max(gy, 0), max(gx, 0)
                y1, x1 = min(gy + a.shape[0], H), min(gx + a.shape[1], img.shape[1])
                if y1 > y0 and x1 > x0:
                    sub = a[y0 - gy:y1 - gy, x0 - gx:x1 - gx].astype(np.float32) / 255
                    img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * (1 - sub) + fg * sub).astype(np.uint8)
            x += pos.x_advance * sc
        rows.append(img)
    W = max(r.shape[1] for r in rows)
    return np.vstack([np.pad(r, ((0, 0), (0, W - r.shape[1])), constant_values=bg) for r in rows])


if __name__ == "__main__":
    font = sys.argv[1]
    out = sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 56
    lines = sys.argv[4:] or [
        "the quick brown fox jumps over the lazy dog",
        "Hello, I'm Harshpreet. I build things for the web.",
        "Networks, routers & packets: data flows -> fast!",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
        "letters look different: llll eeee ssss tttt 1111",
    ]
    Image.fromarray(render(font, lines, size)).save(out)
    infos, _, font_ = shape(font, "hello llll")
    print([font_.glyph_to_string(i.codepoint) for i in infos])
