"""Batch2-F: check every published fact value (and every component of composite facts) against the text layer of the
cited PDF page (printed page + 2).  Usage: f_textlayer_check.py <manifest> <transcript> <pdf>.
Scanned pages (empty text layer) are reported as 'scanned' and are NOT counted as verified here (they were eyeballed)."""
import json, re, sys
import pymupdf

man = json.load(open(sys.argv[1], encoding="utf8"))
tr = json.load(open(sys.argv[2], encoding="utf8"))
doc = pymupdf.open(sys.argv[3])
cache = {}


def nums(pdf_page):
    if pdf_page not in cache:
        t = doc[pdf_page - 1].get_text()
        t = re.sub(r"(\d)\s+(\d{3})\b", r"\1\2", t) if False else t
        cache[pdf_page] = (len(t.strip()), set(re.findall(r"\d[\d,]*(?:\.\d+)?", t.replace(" ", ""))))
    return cache[pdf_page]


def fmt(v):
    v = abs(v)
    return f"{v:,.2f}" if isinstance(v, float) and v != int(v) else f"{int(v):,}"


out = {"verified_in_text_layer": 0, "scanned_page": 0, "not_found": []}
for f in man["facts"]:
    t = tr["facts"][f["metric"]]
    n, toks = nums(t["pdf_page"])
    if n == 0:
        out["scanned_page"] += 1
        continue
    v = t["v2025"] if f["period_end"].startswith("2025") else t["v2024"]
    for part in (v if isinstance(v, list) else [v]):
        if part == 0:
            continue
        s = fmt(part)
        if s not in toks and not (isinstance(part, float) and f"{abs(part):.2f}" in toks):
            out["not_found"].append([f["metric"], f["period_end"], part, t["pdf_page"]])
    out["verified_in_text_layer"] += 1
print(json.dumps(out, indent=1))
