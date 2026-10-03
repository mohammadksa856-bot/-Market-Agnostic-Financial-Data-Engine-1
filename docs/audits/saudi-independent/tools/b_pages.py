"""Batch1-B audit helper: y-aligned row reconstruction for PDF pages + page rendering (read-only)."""
import sys, re, fitz  # pymupdf

def rows(pdf, page, ytol=3.0):
    """Return list of (y, text) rows for 1-based page, words grouped by vertical centre then x-sorted."""
    doc = fitz.open(pdf)
    p = doc[page - 1]
    ws = p.get_text('words')  # x0,y0,x1,y1,word,block,line,wordno
    ws.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    out, cur, cy = [], [], None
    for w in ws:
        yc = (w[1] + w[3]) / 2
        if cy is None or abs(yc - cy) <= ytol:
            cur.append(w); cy = yc if cy is None else (cy + yc) / 2
        else:
            out.append((cy, cur)); cur = [w]; cy = yc
    if cur: out.append((cy, cur))
    return [(round(y, 1), '  '.join(w[4] for w in sorted(r, key=lambda w: w[0]))) for y, r in out]

NUM = re.compile(r'\(?-?\d[\d,]*\.?\d*\)?%?')
def nums(s):
    res = []
    for m in NUM.finditer(s):
        t = m.group(0)
        neg = t.startswith('(') and t.endswith(')')
        t2 = t.strip('()%').replace(',', '')
        if t2 in ('', '-'): continue
        try: v = float(t2)
        except ValueError: continue
        res.append(-v if neg else v)
    return res

def render(pdf, page, out, zoom=1.6, clip=None):
    doc = fitz.open(pdf)
    pix = doc[page - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
    pix.save(out)

def npages(pdf): return len(fitz.open(pdf))

if __name__ == '__main__':
    pdf, pg = sys.argv[1], int(sys.argv[2])
    for y, t in rows(pdf, pg): print(f'{y:7.1f} {t}')
