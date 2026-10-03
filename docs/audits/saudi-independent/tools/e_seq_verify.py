"""Batch2-E: column-sequence verifier for PDFs whose text layer lists the current-year
column first and the prior-year column afterwards (Yamama layout).
For every manifest fact: the published value must occur at the same row index in the
current-year sequence (and the nearest preceding label must resemble the source_label)
and in the prior-year sequence of the cited page.
Usage: e_seq_verify.py <manifest.json> <source.pdf> [out.json]"""
import json, re, sys
import pymupdf

AMT = re.compile(r"^\(?-?\d[\d, ]*(?:\.\d+)?\)?$")
NOTE = re.compile(r"^\(\d{1,2}(?:-\d{1,2})?\)$")

def norm(s): return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def amt(t):
    t = t.strip().replace(", ", ",")
    if NOTE.match(t) or not AMT.match(t): return None
    neg = t.startswith("(")
    t2 = t.strip("()").replace(",", "")
    try: v = float(t2)
    except: return None
    return -v if neg else v

def seqs(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    try: k = lines.index("2024")
    except ValueError: return None, None
    def build(ls):
        out, lab = [], ""
        for l in ls:
            v = amt(l)
            if v is None:
                if re.search(r"[A-Za-z]", l) and not NOTE.match(l): lab = l if not lab or lab.endswith(("and", "of", "for")) is False else lab + " " + l
                continue
            out.append((lab, v)); lab = ""
        return out
    return build(lines[:k]), [v for _, v in build(lines[k:])]

def main():
    man = json.load(open(sys.argv[1], encoding="utf8")); doc = pymupdf.open(sys.argv[2])
    cache = {}
    def get(i):
        if i not in cache: cache[i] = seqs(doc[i].get_text())
        return cache[i]
    rows = []
    for f in man["facts"]:
        pg = f["page"]; pv = float(f["value"]); is_cur = f["period_end"].startswith("2025")
        row = dict(metric=f["metric"], label=f["source_label"], period_end=f["period_end"], page=pg, published=f["value"])
        got = None
        for off in (2, 1, 3, 0):
            i = pg - 1 + off
            if not (0 <= i < len(doc)): continue
            s25, s24 = get(i)
            if not s25: continue
            if f["source_label"].count(" + "):
                continue
            idx = [j for j, (lab, v) in enumerate(s25) if (v == pv if is_cur else False)]
            if not is_cur:
                idx = [j for j, v in enumerate(s24) if v == pv]
            if idx: got = (i, s25, s24, idx); break
        if not got and " + " in f["source_label"]:
            row["status"] = "composite_manual"; rows.append(row); continue
        if not got:
            row["status"] = "value_not_found"; rows.append(row); continue
        i, s25, s24, idx = got
        row["pdf_page"] = i + 1; row["counts"] = [len(s25), len(s24)]
        # label check on row(s) holding the value
        cands = []
        for j in idx:
            lab = s25[j][0] if j < len(s25) else ""
            other = (s24[j] if j < len(s24) else None) if is_cur else s25[j][1] if j < len(s25) else None
            cands.append((j, lab, other))
        row["candidates"] = [{"row": j, "label_seen": lab, "other_year_value": o} for j, lab, o in cands]
        lw = set(norm(f["source_label"]).split())
        ok = any(len(lw & set(norm(lab).split())) >= max(1, min(2, len(lw))) for _, lab, _ in cands)
        row["status"] = "match_row" if ok else "label_check_manual"
        rows.append(row)
    summ = {}
    for r in rows: summ[r["status"]] = summ.get(r["status"], 0) + 1
    out = dict(manifest=sys.argv[1], pdf=sys.argv[2], summary=summ, rows=rows)
    if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], "w", encoding="utf8"), indent=1, ensure_ascii=False)
    print(summ)
    for r in rows:
        if r["status"] != "match_row": print(r["status"], r["metric"], "|", r["label"], r["period_end"], r["published"], r.get("candidates"))

if __name__ == "__main__": main()
