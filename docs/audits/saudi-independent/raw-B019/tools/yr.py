"""yr.py <sym> <sha,...> <out.png> [page=1] [y0=0.25] [y1=0.5]: zoomed montage of cover period bands (read-only)."""
import sys, pymupdf
from PIL import Image, ImageDraw
import pg
sym, pres, out = sys.argv[1:4]
page = int(sys.argv[4]) if len(sys.argv) > 4 else 1
y0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
y1 = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
tiles = []
for pre in pres.split(","):
    m, p = pg.find(sym, pre)
    d = pymupdf.open(p)
    pm = d[page - 1].get_pixmap(matrix=pymupdf.Matrix(1.8, 1.8))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples).crop((0, int(pm.height * y0), pm.width, int(pm.height * y1)))
    c = Image.new("RGB", (im.width, im.height + 16), "white")
    c.paste(im, (0, 16))
    ImageDraw.Draw(c).text((2, 2), f"{pre} [{m['fiscal_year']}|{m['period_slot']}] {m['pages']}p", fill="red")
    tiles.append(c)
w = max(t.width for t in tiles); h = max(t.height for t in tiles)
M = Image.new("RGB", (w, h * len(tiles)), "white")
for k, t in enumerate(tiles):
    M.paste(t, (0, k * h))
M.save(out); print(M.size)
