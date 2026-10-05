"""sheet.py <symbol> <sha-prefix> <pages e.g. 3-13> <out.png> [cols=4] [scale=0.45]: contact sheet of pages of one file to locate statements.
Read-only on raw files; output written outside git."""
import sys

import pymupdf
from PIL import Image, ImageDraw

import pg

sym, pre, rng, out = sys.argv[1:5]
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
sc = float(sys.argv[6]) if len(sys.argv) > 6 else 0.45
a, b = (int(x) for x in rng.split("-")) if "-" in rng else (int(rng), int(rng))
m, p = pg.find(sym, pre)
d = pymupdf.open(p)
tiles = []
for n in range(a, b + 1):
    pm = d[n - 1].get_pixmap(matrix=pymupdf.Matrix(sc, sc))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    c = Image.new("RGB", (im.width, im.height + 14), "white")
    c.paste(im, (0, 14))
    ImageDraw.Draw(c).text((2, 1), f"p{n}", fill="red")
    tiles.append(c)
w = max(t.width for t in tiles)
h = max(t.height for t in tiles)
rows = (len(tiles) + cols - 1) // cols
M = Image.new("RGB", (w * cols, h * rows), "white")
for k, t in enumerate(tiles):
    M.paste(t, ((k % cols) * w, (k // cols) * h))
M.save(out)
print(M.size)
