"""Raw-document page reader for audit B001 (read-only on raw files).
usage: pg.py SYM SHAPREFIX sha|find KW..|text N..|ctext N..|img N OUT [zoom]
ctext = compact text (one line per page, ' ; ' separated)."""
import sys,glob,hashlib,re
import pymupdf
RAW='C:/Users/Mohammed856/finengine-raw-odd/archive/SA'
def path(sym,pre):
    m=glob.glob(RAW+'/'+sym+'/'+pre+'*.pdf'); assert len(m)==1,m; return m[0]
if __name__=='__main__':
    sym,pre,cmd=sys.argv[1:4]; p=path(sym,pre); d=pymupdf.open(p)
    if cmd=='sha': print(hashlib.sha256(open(p,'rb').read()).hexdigest(), len(d))
    elif cmd=='find':
        kws=[k.lower() for k in sys.argv[4:]]
        for i,pg in enumerate(d):
            t=pg.get_text().lower()
            if any(k in t for k in kws): print(i+1, len(t), t[:90].replace('\n',' | '))
    elif cmd=='text':
        for a in sys.argv[4:]:
            i=int(a); print(f'#### PDF PAGE {i}'); print(d[i-1].get_text())
    elif cmd=='ctext':
        for a in sys.argv[4:]:
            i=int(a); t=d[i-1].get_text(); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\s*\n\s*',' ; ',t)
            print(f'#### PDF PAGE {i}: {t}')
    elif cmd=='crop':  # crop PAGE OUT x0 y0 x1 y1 [zoom]  (PDF points)
        i=int(sys.argv[4]); out=sys.argv[5]; x0,y0,x1,y1=map(float,sys.argv[6:10]); z=float(sys.argv[10]) if len(sys.argv)>10 else 3
        d[i-1].get_pixmap(matrix=pymupdf.Matrix(z,z),clip=pymupdf.Rect(x0,y0,x1,y1)).save(out)
    elif cmd=='img':
        i=int(sys.argv[4]); out=sys.argv[5]; z=float(sys.argv[6]) if len(sys.argv)>6 else 1.6
        d[i-1].get_pixmap(matrix=pymupdf.Matrix(z,z)).save(out)
