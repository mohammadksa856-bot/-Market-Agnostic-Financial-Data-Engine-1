"""Independent page-level fact checker (audit tool; read-only against data/).

Rebuilds rows from PDF word coordinates (PyMuPDF) - independent of the
finengine reader - and, for every published fact that cites a page, locates
the printed number on that page, scores the row label against the published
source_label, reports which printed column the number sits in, the column
header text above it and the printed sign.
"""
from __future__ import annotations
import json, os, re, sys, glob, difflib, collections, functools
import warnings
warnings.filterwarnings("ignore")
import fitz  # PyMuPDF

NUM = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?%?$|^\(?-\)?$")

def norm_label(s: str) -> str:
    s = (s or "").lower().replace("�", "'")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def parse_tok(t: str):
    neg = t.startswith("(") or t.startswith("-")
    core = t.strip("()-%").replace(",", "")
    if core == "":
        return None, True  # dash = nil
    try:
        return float(core), neg
    except ValueError:
        return None, neg

@functools.lru_cache(maxsize=64)
def load_doc(path):
    return fitz.open(path)

@functools.lru_cache(maxsize=512)
def page_rows(path, pno):
    d = load_doc(path)
    if pno < 1 or pno > len(d):
        return []
    p = d[pno - 1]
    words = p.get_text("words")
    rows = []
    for x0, y0, x1, y1, t, *_ in sorted(words, key=lambda z: ((z[1] + z[3]) / 2, z[0])):
        yc = (y0 + y1) / 2
        if rows and abs(rows[-1]["y"] - yc) < 2.6:
            rows[-1]["w"].append((x0, x1, t))
        else:
            rows.append({"y": yc, "w": [(x0, x1, t)]})
    out = []
    for r in rows:
        ws = sorted(r["w"])
        label_words, nums = [], []
        for x0, x1, t in ws:
            if NUM.match(t):
                v, neg = parse_tok(t)
                nums.append({"x": (x0 + x1) / 2, "t": t, "v": v, "neg": neg})
            else:
                label_words.append(t)
        out.append({"y": r["y"], "label": " ".join(label_words), "nums": nums,
                    "text": " ".join(t for _, _, t in ws),
                    "words": ws})
    return out

def _segments(words, gap=14.0):
    segs=[]; cur=None
    for x0,x1,t in words:
        if cur and x0-cur[1] <= gap:
            cur[1]=x1; cur[2].append(t)
        else:
            cur=[x0,x1,[t]]; segs.append(cur)
    return [(a,b," ".join(c)) for a,b,c in segs]

def headers_for(rows, ridx, x, maxup=45):
    """Segments in rows above ridx whose x-range covers x (column header text, top->bottom)."""
    parts=[]
    for j in range(ridx-1, max(-1, ridx-maxup), -1):
        r=rows[j]
        for a,b,t in _segments(r["words"]):
            if a-6 <= x <= b+6 and not re.fullmatch(r"[\d,().\-]+", t.replace(" ","")) :
                parts.append(t)
            elif a-6 <= x <= b+6 and re.fullmatch(r"(19|20)\d\d", t.strip()):
                parts.append(t)
        if len(parts)>=5: break
    return " / ".join(reversed(parts))


MONTHS = {m: i for i, m in enumerate(["january","february","march","april","may","june","july","august","september","october","november","december"], 1)}

def _date_units(words):
    """Find date units like 'June 30, 2024' / '30 June 2024' / '2024' in a header row -> [(xc, iso_or_year)]"""
    toks = [(x0, x1, t.strip(",.").lower()) for x0, x1, t in words]
    units = []
    i = 0
    while i < len(toks):
        x0, x1, t = toks[i]
        # Month DD YYYY
        if t in MONTHS and i + 2 < len(toks) and re.fullmatch(r"\d{1,2}", toks[i+1][2]) and re.fullmatch(r"(19|20)\d\d", toks[i+2][2]):
            units.append(((x0 + toks[i+2][1]) / 2, "%s-%02d-%02d" % (toks[i+2][2], MONTHS[t], int(toks[i+1][2])), toks[i+2][1]))
            i += 3; continue
        if re.fullmatch(r"\d{1,2}", t) and i + 2 < len(toks) and toks[i+1][2] in MONTHS and re.fullmatch(r"(19|20)\d\d", toks[i+2][2]):
            units.append(((x0 + toks[i+2][1]) / 2, "%s-%02d-%02d" % (toks[i+2][2], MONTHS[toks[i+1][2]], int(t)), toks[i+2][1]))
            i += 3; continue
        if re.fullmatch(r"(19|20)\d\d", t):
            units.append(((x0 + x1) / 2, t, x1)); i += 1; continue
        i += 1
    return units

def col_date(rows, ridx, x, maxup=45):
    best = None
    for j in range(ridx - 1, max(-1, ridx - maxup), -1):
        for xc, d, xe in _date_units(rows[j]["words"]):
            dist = abs(xc - x)
            if dist < 45 and (best is None or dist < best[0] - 1e-9 or (abs(dist-best[0])<1e-9 and len(d) > len(best[1]))):
                best = (dist, d)
        if best and len(best[1]) == 10:
            break
    return best[1] if best else None

def check_fact(path, fact, scale_override=None):
    page = fact.get("page")
    res = {"metric": fact["metric"], "label": fact["source_label"], "value": fact["value"], "page": page,
           "period_kind": fact["period_kind"], "period_end": fact["period_end"]}
    if not page:
        res["status"] = "NO_PAGE"
        return res
    try:
        val = float(fact["value"])
    except ValueError:
        res["status"] = "NONNUMERIC"
        return res
    target = abs(val)
    best = None
    for pg in (page,):
        rows = page_rows(path, pg)
        for i, r in enumerate(rows):
            real=[n for n in r["nums"] if not (re.fullmatch(r"\d{1,2}(\.\d)?",n["t"]) and not (abs(float(fact["value"]))<100 and abs(n["v"] if n["v"] is not None else -1)==abs(float(fact["value"]))))]
            for ci, n in enumerate(real):
                if n["v"] is None:
                    continue
                if abs(n["v"] - target) <= max(0.0051, target * 1e-9):
                    # label: row label else look up for preceding label-only rows (wrapped)
                    lab = r["label"]
                    k = i - 1
                    while len(lab.split()) < 3 and k >= 0 and k > i - 3 and not rows[k]["nums"]:
                        lab = rows[k]["label"] + " " + lab
                        k -= 1
                    sc = difflib.SequenceMatcher(None, norm_label(fact["source_label"]), norm_label(lab)).ratio()
                    cand = {"score": round(sc, 2), "rowlabel": lab, "col": ci, "ncols": len(real),
                            "tok": n["t"], "neg": n["neg"], "hdr": headers_for(rows, i, n["x"]), "row": i, "date": col_date(rows, i, n["x"]),
                            "rowvals": [{"t": q["t"], "v": q["v"], "neg": q["neg"], "hdr": headers_for(rows, i, q["x"]), "date": col_date(rows, i, q["x"])} for q in real]}
                    if best is None or cand["score"] > best["score"]:
                        best = cand
    if best is None:
        # search other pages of the doc
        d = load_doc(path)
        others = []
        for pg in range(1, len(d) + 1):
            if pg == page:
                continue
            for r in page_rows(path, pg):
                if any(n["v"] is not None and abs(n["v"] - target) <= 0.0051 for n in r["nums"]):
                    others.append(pg); break
        res["status"] = "NOT_ON_PAGE" if not others else "WRONG_PAGE"
        res["other_pages"] = others[:6]
        return res
    res.update(best)
    printed_neg = best["neg"]
    res["sign_ok"] = (printed_neg == (val < 0)) or val == 0
    res["status"] = "OK" if best["score"] >= 0.62 else "LABEL_LOW"
    if not res["sign_ok"]:
        res["status"] = "SIGN" if res["status"] == "OK" else res["status"] + "+SIGN"
    return res

def archive_map():
    a = json.load(open("data/raw/archive-index.json", encoding="utf8"))["artifacts"]
    m = collections.defaultdict(list)
    for x in a:
        for mf in x["metadata"].get("manifests", []):
            m[mf].append(x["local_path"])
    return m

def check_manifest(mf_path, amap=None):
    amap = amap or archive_map()
    x = json.load(open(mf_path, encoding="utf8"))
    base = os.path.basename(mf_path)
    paths = amap.get(base, [])
    out = {"manifest": base, "paths": paths, "results": []}
    if not paths or not paths[0].lower().endswith(".pdf"):
        out["note"] = "no pdf"
        return out
    for f in x["facts"]:
        out["results"].append(check_fact(paths[0], f))
    return out

if __name__ == "__main__":
    amap = archive_map()
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for mf in sys.argv[2:]:
        r = check_manifest(mf, amap)
        json.dump(r, open(os.path.join(outdir, os.path.basename(mf)), "w", encoding="utf8"), ensure_ascii=False)
        c = collections.Counter(z["status"] for z in r["results"])
        print(os.path.basename(mf), dict(c))
