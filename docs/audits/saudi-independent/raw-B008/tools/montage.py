"""montage.py <symbol> <out.png> <sha:page> ... : contact sheet of rendered pages (read-only on raw files), to identify scanned files by their cover."""
import sys, pymupdf, pg
from PIL import Image
sym, out, *items = sys.argv[1:]
ims = []
for it in items:
    h, n = it.split(":")
    m, p = pg.find(sym, h)
    pix = pymupdf.open(p)[int(n) - 1].get_pixmap(matrix=pymupdf.Matrix(0.9, 0.9))
    ims.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
w = sum(i.width for i in ims); h = max(i.height for i in ims)
sheet = Image.new("RGB", (w, h), "white"); x = 0
for i in ims:
    sheet.paste(i, (x, 0)); x += i.width
sheet.save(out)
