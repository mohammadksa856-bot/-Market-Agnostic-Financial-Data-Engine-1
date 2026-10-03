"""Locate primary-statement pages and image-only pages in a raw PDF. usage: loc.py SYM SHA_PREFIX"""
import sys, re, pymupdf
sys.path.insert(0, __file__.rsplit('tools',1)[0] + 'tools')
from pg import path
sys.stdout.reconfigure(encoding='utf-8')
KEY = re.compile(r"(statement[s]? of (financial position|financial condition|income|profit|comprehensive|cash flow|changes in|operations)|balance sheet|income statement|cash flows? statement|statement of insurance operations)", re.I)
sym, pre = sys.argv[1:3]
d = pymupdf.open(path(sym, pre))
empty = [i+1 for i, p in enumerate(d) if len(p.get_text().strip()) < 60]
print("pages", len(d), "image/empty pages:", empty[:60], "..." if len(empty) > 60 else "")
for i, p in enumerate(d):
    t = p.get_text()
    head = " ".join(t.split())[:350]
    m = KEY.search(head)
    if m and not re.search(r"notes to the|^index|\bnote\b \d", head[:60], re.I):
        print(i+1, "|", head[:170])
