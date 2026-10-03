"""montage.py <sym> <sha> <pages,...> [scale] [cols]: contact sheet of rendered pages for presence checks (not for value reading)."""
import sys,os,pymupdf,pg
sym,h,pgs=sys.argv[1:4];sc=float(sys.argv[4]) if len(sys.argv)>4 else 0.6;cols=int(sys.argv[5]) if len(sys.argv)>5 else 3
m,p=pg.find(sym,h);d=pymupdf.open(p)
pm=[d[int(n)-1].get_pixmap(matrix=pymupdf.Matrix(sc,sc)) for n in pgs.split(',')]
w=max(x.width for x in pm);hh=max(x.height for x in pm);rows=(len(pm)+cols-1)//cols
out=pymupdf.Pixmap(pymupdf.csRGB,pymupdf.IRect(0,0,w*cols,hh*rows),False);out.clear_with(255)
for i,x in enumerate(pm):
    x=pymupdf.Pixmap(pymupdf.csRGB,x) if x.n!=3 else x
    x.set_origin((i%cols)*w,(i//cols)*hh);out.copy(x,x.irect)
fn=os.path.join(pg.OUT,'m_%s_%s.png'%(sym,h[:6]));out.save(fn);print(fn)
