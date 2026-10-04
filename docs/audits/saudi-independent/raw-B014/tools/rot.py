"""rot.py sym sha page angle zoom: render a page rotated (for landscape-in-portrait scans)."""
import sys, os, pymupdf, pg
from PIL import Image
sym, h, n, ang, z = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
m, p = pg.find(sym, h); d = pymupdf.open(p)
pix = d[n - 1].get_pixmap(matrix=pymupdf.Matrix(z, z))
fn = os.path.join(pg.OUT, f"{sym}_{h[:6]}_p{n}_r{ang}.png")
pix.save(fn)
im = Image.open(fn).rotate(ang, expand=True); im.save(fn); print(fn.split('scratchpad')[1])
