"""Locate primary-statement pages in a raw PDF and print their text compactly (read-only).
Usage: stm.py <symbol> <shaprefix> [find | show p1,p2 ]"""
import sys, re
import pymupdf
import pg
sym, pre = sys.argv[1:3]
cmd = sys.argv[3] if len(sys.argv) > 3 else "find"
meta, p = pg.find(sym, pre)
doc = pymupdf.open(p)
T = {"bs": r"statements? of financial position|balance sheet", "is": r"statements? of (?:profit|income|comprehensive|operations)|profit or loss", "cf": r"statements? of cash flows?", "eq": r"statements? of changes in (?:shareholders|equity)"}
if cmd == "find":
    for i, pg_ in enumerate(doc, 1):
        t = pg_.get_text()
        head = " ".join(t.split())[:400].lower()
        hits = [k for k, v in T.items() if re.search(v, head)]
        n = len(re.findall(r"\d{1,3}(?:,\d{3})+", t))
        if hits and n > 12: print(i, hits, "nums", n, "|", " ".join(t.split())[:110])
        elif len(t) < 50: print(i, "textless", len(t))
else:
    for n in [int(x) for x in sys.argv[4].split(",")]:
        print(f"--- p{n}")
        lines = [" ".join(l.split()) for l in doc[n-1].get_text().splitlines()]
        print("\n".join(l for l in lines if l))
