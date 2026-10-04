"""Helper for batch B015: locate a raw file by sha prefix, print sha256, dump page text, render pages to PNG.
Usage: pg.py <symbol> <shaprefix> info | text <page,...> | grep <regex> | render <page,...> [zoom]
Pages are 1-based PDF pages. Read-only on raw files."""
import sys, json, hashlib, re, os
import pymupdf
RAW = r"C:\Users\Mohammed856\finengine-raw-odd"
INV = os.path.join(os.path.dirname(__file__), "..", "..", "raw-coverage", "companies")
OUT = os.environ.get("B015_OUT", r"C:\Users\MOHAMM~1\AppData\Local\Temp\claude\C--Users-Mohammed856-OneDrive-Documents-GitHub-pixel-perfect-showcase-276\258d8876-ee13-4e59-ad2e-034afe1d8906\scratchpad")
def find(sym, pre):
    d = json.load(open(os.path.join(INV, sym + ".json"), encoding="utf8"))
    m = [f for f in d["files"] if f["sha256"].startswith(pre)]
    assert len(m) == 1, m
    return m[0], os.path.join(RAW, m[0]["relpath"].replace("/", os.sep))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
if __name__ == "__main__":
    sym, pre, cmd = sys.argv[1:4]
    meta, p = find(sym, pre)
    doc = pymupdf.open(p)
    pages = lambda s: [int(x) for x in s.split(",")] if "-" not in s else list(range(int(s.split("-")[0]), int(s.split("-")[1]) + 1))
    if cmd == "info":
        print(p, "sha_ok", sha(p) == meta["sha256"], "pages", len(doc), json.dumps(doc.metadata, ensure_ascii=False))
    elif cmd == "text":
        for n in pages(sys.argv[4]): print(f"--- p{n}"); print(doc[n - 1].get_text())
    elif cmd == "grep":
        r = re.compile(sys.argv[4], re.I)
        for i, pg in enumerate(doc, 1):
            t = pg.get_text()
            if r.search(t): print(i, [l[:100] for l in t.splitlines() if r.search(l)][:3])
    elif cmd == "render":
        z = float(sys.argv[5]) if len(sys.argv) > 5 else 1.6
        for n in pages(sys.argv[4]):
            fn = os.path.join(OUT, f"{sym}_{pre[:6]}_p{n}.png")
            doc[n - 1].get_pixmap(matrix=pymupdf.Matrix(z, z)).save(fn); print(fn)
