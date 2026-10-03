"""Independent verification of Pillar 3 (KM1 etc.) facts: row/cell vs printed table. Audit tool (read-only)."""
import sys, json, glob, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import pagecheck as pc

NUMTOK = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?%?$")
MON = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

def row_by_id(rows, rid):
    for r in rows:
        ws = [t for _,_,t in r["words"]]
        if ws and ws[0].lower() == rid.lower():
            return r
    return None

def numeric_cells(r, ncols=None):
    """Trailing run of numeric tokens of the row (label text may itself contain numbers)."""
    ws = [t for _,_,t in r["words"]][1:]
    out = []
    for t in reversed(ws):
        if NUMTOK.match(t) or t == "-":
            out.append(t)
        else:
            break
    out = list(reversed(out))
    if ncols and len(out) > ncols:
        out = out[len(out) - ncols:]
    return out

def header_dates(rows, upto):
    """find header row with >=3 month-year tokens above row index upto"""
    for j in range(upto - 1, max(-1, upto - 40), -1):
        toks = [t for _,_,t in rows[j]["words"]]
        dates = []
        for k, t in enumerate(toks):
            m = re.fullmatch(r"([A-Za-z]{3})[a-z]*[- ']?(\d{2,4})", t)
            if m and m.group(1).lower() in MON:
                y = int(m.group(2)); y = y + 2000 if y < 100 else y
                dates.append(f"{y}-{MON[m.group(1).lower()]:02d}")
            elif t.lower().rstrip(",") in ("january","february","march","april","may","june","july","august","september","october","november","december") and k+1 < len(toks):
                pass
        if len(dates) >= 3:
            return dates
    return None

def check_manifest(path, amap):
    x = json.load(open(path, encoding="utf8"))
    b = os.path.basename(path)
    paths = amap.get(b, [])
    res = []
    if not paths:
        return {"manifest": b, "note": "no archived doc", "results": []}
    pdf = paths[0]
    maxcol = collections.defaultdict(int)
    for lst0 in (x["facts"], x.get("excluded_facts", [])):
        for f0 in lst0:
            if f0.get("cell") and f0.get("page"):
                k0 = (f0["page"], f0.get("table"))
                maxcol[k0] = max(maxcol[k0], ord(f0["cell"].lower()) - 96)
    for kind, lst in (("published", x["facts"]), ("excluded", x.get("excluded_facts", []))):
        for f in lst:
            r = {"kind": kind, "metric": f["metric"], "period_end": f["period_end"], "value": f["value"], "page": f.get("page"),
                 "table": f.get("table"), "row": f.get("row"), "cell": f.get("cell"), "reason": f.get("reason")}
            if not (f.get("page") and f.get("row") and f.get("cell")):
                r["status"] = "NO_COORDS"; res.append(r); continue
            rows = pc.page_rows(pdf, f["page"])
            row = row_by_id(rows, str(f["row"]))
            if row is None:
                r["status"] = "ROW_NOT_FOUND"; res.append(r); continue
            cells = numeric_cells(row, maxcol[(f["page"], f.get("table"))])
            idx = ord(f["cell"].lower()) - 97
            r["row_text"] = row["text"][:140]
            if idx >= len(cells):
                r["status"] = "CELL_MISSING"; res.append(r); continue
            tok = cells[idx]
            try:
                pv = float(tok.strip("()%").replace(",", ""))
            except ValueError:
                r["status"] = "NONNUM"; res.append(r); continue
            val = float(f["value"])
            scale = f.get("scale")
            if f.get("unit") == "ratio":
                ok = abs(pv / 100 - val) <= 0.0006 or abs(pv - val) <= 0.0006
            else:
                ok = abs(pv - val) <= 0.51
            r["printed"] = tok
            hd = header_dates(rows, rows.index(row))
            if hd and idx < len(hd):
                r["col_date"] = hd[idx]
                r["date_ok"] = hd[idx] == f["period_end"][:7]
            r["status"] = "OK" if ok else "VALUE_MISMATCH"
            res.append(r)
    return {"manifest": b, "pdf": pdf, "results": res}

if __name__ == "__main__":
    amap = pc.archive_map()
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    for mf in sys.argv[2:]:
        r = check_manifest(mf, amap)
        json.dump(r, open(os.path.join(outdir, os.path.basename(mf)), "w", encoding="utf8"), ensure_ascii=False)
        c = collections.Counter((z["status"], z.get("date_ok")) for z in r["results"])
        print(os.path.basename(mf), dict(c))
