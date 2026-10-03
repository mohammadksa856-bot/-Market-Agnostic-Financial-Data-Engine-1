"""Print page text (words by row) from a PDF: python unified_page.py <pdf> <page1based> [grep]"""
import sys, pymupdf, re
d = pymupdf.open(sys.argv[1]); p = d[int(sys.argv[2]) - 1]
rows = {}
for w in p.get_text('words'):
    rows.setdefault(round(w[1] / 4), []).append(w)
g = sys.argv[3].lower() if len(sys.argv) > 3 else None
for k in sorted(rows):
    line = ' '.join(f"{w[4]}" for w in sorted(rows[k], key=lambda w: w[0]))
    if not g or g in line.lower(): print(round(rows[k][0][1]), line)
