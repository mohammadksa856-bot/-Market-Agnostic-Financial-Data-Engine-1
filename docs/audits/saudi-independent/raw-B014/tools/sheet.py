"""sheet.py <sym> <sha> <pages> [cols] [zoom]: contact sheet PNG of several pages (for locating statements in scanned files)."""
import sys, os, pymupdf, pg
sym, h, pgs = sys.argv[1:4]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
z = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
m, p = pg.find(sym, h); d = pymupdf.open(p)
pages = [int(x) for x in pgs.split(",")] if "-" not in pgs else list(range(int(pgs.split("-")[0]), int(pgs.split("-")[1]) + 1))
pix = [d[n-1].get_pixmap(matrix=pymupdf.Matrix(z, z)) for n in pages]
w = max(x.width for x in pix); hh = max(x.height for x in pix)
rows = (len(pix) + cols - 1) // cols
sh = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, w * cols, hh * rows), False); sh.set_rect(sh.irect, (255, 255, 255))
for i, x in enumerate(pix):
    x = pymupdf.Pixmap(pymupdf.csRGB, x) if x.n != 3 else x
    x.set_origin((i % cols) * w, (i // cols) * hh); sh.copy(x, x.irect)
fn = os.path.join(pg.OUT, f"sheet_{sym}_{h[:6]}_{pages[0]}-{pages[-1]}.png"); sh.save(fn); print(fn.split("scratchpad")[1])
