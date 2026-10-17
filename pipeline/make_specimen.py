"""Generate the specimen page: dist/specimen.html (relative font files) and an
inlined copy (fonts + image as data URIs) for publishing as a single page."""
import base64
import json
import os
import sys

import cv2

from ink import SCRATCH, load_page

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "..", "dist")


def faces(inline):
    out = []
    for w, name in ((400, "Regular"), (700, "Bold")):
        fn = f"HarshpreetHand-{name}.woff2"
        if inline:
            b64 = base64.b64encode(open(os.path.join(DIST, fn), "rb").read()).decode()
            src = f'url("data:font/woff2;base64,{b64}") format("woff2")'
        else:
            src = f'url("{fn}") format("woff2"), url("HarshpreetHand-{name}.woff") format("woff")'
        out.append('@font-face { font-family: "Harshpreet Hand"; src: %s; font-weight: %d; font-style: normal; font-display: swap; }'
                   % (src, w))
    return "\n".join(out)


def main(inline_out):
    tpl = open(os.path.join(HERE, "specimen_template.html")).read()
    crop = load_page(4)[770:975, 285:1650]
    ok, jpg = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 84])
    open(os.path.join(DIST, "notes-sample.jpg"), "wb").write(jpg.tobytes())
    design = json.load(open(os.path.join(HERE, "..", "design", "glyphs.json")))
    triples = "".join(c for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                      if len(design.get(c, [])) >= 3)
    for inline, path in ((False, os.path.join(DIST, "specimen.html")), (True, inline_out)):
        html = tpl.replace("/*FONTFACES*/", faces(inline)).replace("{{TRIPLES}}", triples)
        img = "data:image/jpeg;base64," + base64.b64encode(jpg.tobytes()).decode() if inline else "notes-sample.jpg"
        html = html.replace("{{NOTES_IMG}}", img)
        if not inline:
            html = "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" \
                   + html.replace("<div class=\"page\">", "</head>\n<body>\n<div class=\"page\">", 1) + "\n</body>\n</html>\n"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(html)
        print(path, len(html) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else f"{SCRATCH}/artifact/harshpreet-hand.html")
