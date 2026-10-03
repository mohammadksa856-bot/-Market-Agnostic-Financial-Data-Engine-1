"""Compare an independent page transcription (metric -> {pdf_page, label_seen, v2025, v2024}) with a manifest.
Transcription values are as printed (parentheses = negative); sign conventions are applied by
`sign` (+1/-1) per metric in the transcription when the manifest stores outflows/expenses negative."""
import json, sys
man = json.load(open(sys.argv[1], encoding="utf8"))
tr = json.load(open(sys.argv[2], encoding="utf8"))
scale = float(tr.get("scale", 1))
res = {"match": 0, "mismatch": [], "not_transcribed": [], "extra_in_transcript": []}
seen = set()
for f in man["facts"]:
    m = f["metric"]; t = tr["facts"].get(m)
    key = (m, f["period_end"][:4], f["page"])
    if t is None:
        res["not_transcribed"].append([m, f["period_end"], f["value"]]); continue
    for t1 in (t if isinstance(t, list) else [t]):
        if t1.get("page") not in (None, f["page"]): continue
        v = t1["v2025"] if f["period_end"].startswith("2025") else t1["v2024"]
        if v is None or v == []: continue
        if isinstance(v, list): v = sum(v)
        v = v * t1.get("sign", 1)
        seen.add((m, f["period_end"][:4]))
        if float(f["value"]) == v: res["match"] += 1
        else: res["mismatch"].append([m, f["period_end"], f["value"], v, t1.get("label_seen")])
        break
print(json.dumps(res, indent=1))
