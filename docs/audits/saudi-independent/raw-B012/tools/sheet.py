"""Contact sheet of PDF pages for locating statement pages in image-only files (render outputs stay out of git).
Usage: sheet.py <symbol> <shaprefix> <first> <last> [cols]"""
import sys, os
import pymupdf
from PIL import Image
import pg
sym, pre, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
meta, p = pg.find(sym, pre); doc = pymupdf.open(p)
ims = []
for n in range(a, min(b, len(doc)) + 1):
    pm = doc[n - 1].get_pixmap(matrix=pymupdf.Matrix(0.55, 0.55)); im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples); ims.append(im)
w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (w * cols, h * rows), "white")
for i, im in enumerate(ims): sh.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
fn = os.path.join(pg.OUT, f"sheet_{sym}_{pre[:6]}_{a}-{b}.png"); sh.save(fn); print(fn, sh.size)
