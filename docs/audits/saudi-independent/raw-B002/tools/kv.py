"""Print lines matching regex from given pdf pages. usage: kv.py SYM SHA 'regex' P P ..."""
import sys, re, pymupdf, os
sys.path.insert(0, os.path.dirname(__file__))
from pg import path
sys.stdout.reconfigure(encoding='utf-8')
sym, pre, rx, *pp = sys.argv[1:]
d = pymupdf.open(path(sym, pre)); R = re.compile(rx, re.I)
for n in pp:
    print(f"--- p{n}")
    for l in d[int(n)-1].get_text("text", sort=True).splitlines():
        if R.search(l) and l.strip(): print(" ".join(l.split())[:200])
