"""sheet.py <sym> <sha> <pages> [cols] : contact sheet of page thumbnails (png) in the scratchpad (not in git) to locate statement pages on scanned files."""
import sys,pymupdf,pg,os
sym,h,pgs=sys.argv[1:4];cols=int(sys.argv[4]) if len(sys.argv)>4 else 4
m,p=pg.find(sym,h);d=pymupdf.open(p)
ns=[int(x) for x in pgs.split(',')] if '-' not in pgs else list(range(int(pgs.split('-')[0]),int(pgs.split('-')[1])+1))
z=0.55;ims=[]
for n in ns:
    pm=d[n-1].get_pixmap(matrix=pymupdf.Matrix(z,z));ims.append((n,pm))
w=max(i[1].width for i in ims);hh=max(i[1].height for i in ims);rows=(len(ims)+cols-1)//cols
sheet=pymupdf.Pixmap(pymupdf.csRGB,pymupdf.IRect(0,0,w*cols,hh*rows),False);sheet.clear_with(255)
for k,(n,pm) in enumerate(ims):
    pm=pymupdf.Pixmap(pymupdf.csRGB,pm) if pm.colorspace!=pymupdf.csRGB else pm
    pm.set_origin((k%cols)*w,(k//cols)*hh);sheet.copy(pm,pm.irect)
fn=os.path.join(pg.OUT,f"sheet_{sym}_{h[:6]}_{ns[0]}-{ns[-1]}.png");sheet.save(fn);print(fn)
