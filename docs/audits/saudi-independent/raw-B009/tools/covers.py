"""covers.py <symbol> <sha-prefix,...> <out.png> [page=1] [crop=0.5] [cols=3]: montage of page crops with sha prefix captions, for identifying
scanned files by cover. Read-only on raw files; output is written outside git."""
import sys

import pymupdf
from PIL import Image, ImageDraw

import pg

sym, prefixes, out = sys.argv[1:4]
page = int(sys.argv[4]) if len(sys.argv) > 4 else 1
crop = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 3
tiles = []
for pre in prefixes.split(","):
    m, p = pg.find(sym, pre)
    d = pymupdf.open(p)
    pm = d[page - 1].get_pixmap(matrix=pymupdf.Matrix(0.9, 0.9))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    im = im.crop((0, 0, im.width, int(im.height * crop)))
    c = Image.new("RGB", (im.width, im.height + 16), "white")
    c.paste(im, (0, 16))
    ImageDraw.Draw(c).text((2, 2), f"{pre} [{m['fiscal_year']}|{m['period_slot']}] {m['pages']}p", fill="red")
    tiles.append(c)
w = max(t.width for t in tiles)
h = max(t.height for t in tiles)
rows = (len(tiles) + cols - 1) // cols
M = Image.new("RGB", (w * cols, h * rows), "white")
for k, t in enumerate(tiles):
    M.paste(t, ((k % cols) * w, (k // cols) * h))
M.save(out)
print(M.size)
