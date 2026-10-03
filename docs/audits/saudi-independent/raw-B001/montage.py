"""montage.py SYM SHA OUT p1,p2,.. [zoom] : contact sheet of pages (3 per row) for locating statements."""
import sys,pymupdf
from pg import path
sym,pre,out,pages=sys.argv[1:5]; z=float(sys.argv[5]) if len(sys.argv)>5 else 0.55
d=pymupdf.open(path(sym,pre)); pix=[d[int(p)-1].get_pixmap(matrix=pymupdf.Matrix(z,z)) for p in pages.split(',')]
w=max(p.width for p in pix); h=max(p.height for p in pix); cols=min(3,len(pix)); rows=(len(pix)+cols-1)//cols
sheet=pymupdf.Pixmap(pymupdf.csRGB,pymupdf.IRect(0,0,w*cols,h*rows),False); sheet.set_rect(sheet.irect,(255,255,255))
for k,p in enumerate(pix):
    p=pymupdf.Pixmap(pymupdf.csRGB,p) if p.colorspace.n!=3 else p
    p.set_origin((k%cols)*w,(k//cols)*h); sheet.copy(p,p.irect)
sheet.save(out)
