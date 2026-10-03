"""Read-only page reader for the B002 raw audit (never writes into the raw dir).
usage: pg.py SYMBOL SHA_PREFIX info | text P.. | find PHRASE.. | render P..
text: 1-based pdf pages; find: pages whose first 400 chars contain a phrase (statement title pages)."""
import sys, glob, hashlib, os
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')
RAW = r"C:\Users\Mohammed856\finengine-raw-odd\archive\SA"
OUT = os.environ.get('RENDER_DIR', r"C:\Users\MOHAMM~1\AppData\Local\Temp\claude\C--Users-Mohammed856-OneDrive-Documents-GitHub-pixel-perfect-showcase-276\258d8876-ee13-4e59-ad2e-034afe1d8906\scratchpad")
def path(sym, pre):
    m = glob.glob(os.path.join(RAW, sym, pre + "*.pdf"))
    assert len(m) == 1, m
    return m[0]
def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()
if __name__ == '__main__':
    sym, pre, mode, *a = sys.argv[1:]
    p = path(sym, pre); d = pymupdf.open(p)
    if mode == 'info':
        print(p, len(d), sha(p), d.metadata.get('creationDate'), d.metadata.get('creator'))
    elif mode == 'text':
        for n in a:
            n = int(n); print(f"--- pdf p{n} ---"); print(d[n-1].get_text("text", sort=True))
    elif mode == 'find':
        for i, pg in enumerate(d):
            t = " ".join(pg.get_text().lower().split())[:400]
            hit = [w for w in a if w.lower() in t]
            if hit: print(i+1, hit, t[:110])
    elif mode == 'render':
        for n in a:
            n = int(n); f = os.path.join(OUT, f"{sym}_{pre}_p{n}.png"); d[n-1].get_pixmap(dpi=100).save(f); print(f)
