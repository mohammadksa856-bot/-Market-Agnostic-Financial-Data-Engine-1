"""Per-file identification survey: period phrases from the first pages' text layer (read-only).
Usage: survey.py <symbol>"""
import sys, json, re, os
import pymupdf
import pg
sym = sys.argv[1]
d = json.load(open(os.path.join(pg.INV, sym + ".json"), encoding="utf8"))
r = re.compile(r"(for the [a-z0-9 -]{0,40}?(?:period|year)s? ended[^\n]{0,60}|(?:three|six|nine|twelve|3|6|9|12)[- ]months?[^\n]{0,60}20\d\d|as at[^\n]{0,40}20\d\d|31 december[^\n]{0,10}20\d\d|\(unaudited\)|\(audited\))", re.I)
for f in sorted(d["files"], key=lambda f: (f["fiscal_year"] or 0, f["period_slot"] or "", f["sha256"])):
    p = os.path.join(pg.RAW, f["relpath"].replace("/", os.sep))
    doc = pymupdf.open(p)
    txt = ""
    chars = 0
    for i in range(min(4, len(doc))):
        t = doc[i].get_text(); chars += len(t); txt += t + "\n"
    ph = []
    for m in r.finditer(txt):
        s = " ".join(m.group(0).split())[:70]
        if s not in ph: ph.append(s)
    print(f["fiscal_year"], f["period_slot"], f["sha256"][:8], f["file_class"], f["pages"], "chars4p", chars, ph[:4])
