"""crop.py <sym> <sha> <page> <x0> <y0> <x1> <y1> [zoom]: render a fractional crop of a page for reading small digits."""
import sys,os,pymupdf,pg
sym,h,n=sys.argv[1:4];x0,y0,x1,y1=[float(v) for v in sys.argv[4:8]];z=float(sys.argv[8]) if len(sys.argv)>8 else 3.2
m,p=pg.find(sym,h);d=pymupdf.open(p);r=d[int(n)-1].rect
fn=os.path.join(pg.OUT,'c_%s_%s_p%s_%d.png'%(sym,h[:6],n,int(y0*100)))
d[int(n)-1].get_pixmap(matrix=pymupdf.Matrix(z,z),clip=pymupdf.Rect(r.width*x0,r.height*y0,r.width*x1,r.height*y1)).save(fn);print(fn)
