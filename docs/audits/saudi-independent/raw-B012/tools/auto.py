"""Auto-transcribe text-layer primary statements for every inventory file of a symbol (read-only; offline).
Writes <out>/auto_<symbol>.json with, per file: detected period, statement pdf pages, printed page numbers, headline rows (cur/prior),
unit scale and flags.  Image-only files are reported as 'textless' (they need visual reading).
Usage: auto.py <symbol> [outdir]"""
import json, os, re, sys
import pymupdf
import pg, ext
MON = "january february march april may june july august september october november december".split()
D1 = re.compile(r"(\d{1,2})\s+(" + "|".join(MON) + r")\s+(\d{4})", re.I)
D2 = re.compile(r"(" + "|".join(MON) + r")\s+(\d{1,2}),?\s+(\d{4})", re.I)
def dates(t):
    f = []
    for m in D1.finditer(t): f.append((m.start(), f"{m.group(3)}-{MON.index(m.group(2).lower())+1:02d}-{int(m.group(1)):02d}"))
    for m in D2.finditer(t): f.append((m.start(), f"{m.group(3)}-{MON.index(m.group(1).lower())+1:02d}-{int(m.group(2)):02d}"))
    return [d for _, d in sorted(f)]
def head(t, n=600): return " ".join(t.split())[:n]
def pick(doc, kind, lim=60):
    for i in range(min(len(doc), lim)):
        t = doc[i].get_text(); h = head(t).lower(); tl = t.lower()
        if "notes to the" in h[:200] or "index" in h[:80]: continue
        nn = len(re.findall(r"\d{1,3}(?:,\d{3})+", t))
        if nn < 8: continue
        if kind == "bs" and re.search(r"statements? of financial position|balance sheet", h) and "total assets" in tl: return i
        if kind == "is" and re.search(r"statements? of (profit|income|comprehensive|operations)|profit or loss|statements? of income", h) and re.search(r"\n(revenues?|sales|net sales|net revenues?|revenue from)", tl) : return i
        if kind == "cf" and re.search(r"statements? of cash flows?", h) and "operating activities" in tl: return i
    for i in range(min(len(doc), lim)):
        t = doc[i].get_text(); tl = t.lower(); h = head(t).lower()
        if "notes to the" in h[:300] or "index" in h[:80] or len(re.findall(r"\d{1,3}(?:,\d{3})+", t)) < 8: continue
        if kind == "is" and "gross profit" in tl and re.search(r"revenues?|sales", tl) and "total assets" not in tl: return i
        if kind == "cf" and "operating activities" in tl and "investing activities" in tl and re.search(r"net cash|cash generated|cash flows? (generated|from|used)", tl): return i
        if kind == "bs" and "total assets" in tl and "total liabilities" in tl: return i
    return None
def printed(t):
    ls = [l.strip() for l in t.splitlines() if l.strip()]
    for l in reversed(ls[-6:]):
        m = re.fullmatch(r"[-– ]*(\d{1,3})[-– ]*", l)
        if m: return int(m.group(1))
    for l in ls[:10]:
        if re.fullmatch(r"\d{1,3}", l): return int(l)
    return None
def getrows(doc, i, need):
    rs = ext.rows(doc[i])
    if i + 1 < len(doc) and not any(re.search(need, l, re.I) and n for l, n in rs):
        rs += ext.rows(doc[i + 1]); return rs, [i + 1, i + 2]
    return rs, [i + 1]
def sel(rs, kind, ncols):
    out = {}
    for key, rx in ext.K[kind]:
        for l, nums in rs:
            if nums and re.search(rx, l, re.I):
                v = [ext.val(x) for x in nums]
                if len(v) < ncols: continue
                v = v[-ncols:]
                out.setdefault(key, v); break
    return out
def run(sym, outdir):
    inv = json.load(open(os.path.join(pg.INV, sym + ".json"), encoding="utf8"))
    res = []
    for f in sorted(inv["files"], key=lambda f: (f["fiscal_year"] or 0, f["period_slot"] or "", f["sha256"])):
        p = os.path.join(pg.RAW, f["relpath"].replace("/", os.sep)); doc = pymupdf.open(p)
        r = {"sha": f["sha256"], "label": f"{f['fiscal_year']}|{f['period_slot']}", "cls": f["file_class"], "pages": f["pages"], "flags": []}
        chars = sum(len(doc[i].get_text()) for i in range(min(8, len(doc))))
        if chars < 200: r["flags"].append("textless"); res.append(r); continue
        pb, pi, pc = pick(doc, "bs"), pick(doc, "is"), pick(doc, "cf")
        r["pdf"] = {"bs": pb and pb + 1, "is": pi and pi + 1, "cf": pc and pc + 1}
        if None in (pb, pi, pc): r["flags"].append("statement page not found: " + ",".join(k for k, v in zip("bs is cf".split(), (pb, pi, pc)) if v is None))
        if pi is not None:
            ti = doc[pi].get_text(); h = head(ti, 900).lower()
            ds = dates(head(ti, 900)); r["period_end"] = ds[0] if ds else None
            if re.search(r"year ended|year-ended|for the year|financial year", h) and not re.search(r"three|six|nine|quarter", h[:300]): pt = "FY"
            elif re.search(r"nine", h): pt = "9M"
            elif re.search(r"six", h): pt = "H1"
            elif re.search(r"three|quarter", h): pt = "Q"
            else: pt = "?"
            cov = head(doc[0].get_text(), 500).lower(); cds = dates(head(doc[0].get_text(), 500))
            if not r["period_end"] and cds: r["period_end"] = cds[0]
            if pt == "?":
                pt = "FY" if re.search(r"year[- ]ended", cov) else "9M" if "nine" in cov else "H1" if "six" in cov else "Q" if "three" in cov else "?"
            r["period_type"] = pt
            r["scale_text"] = re.findall(r"(?:in|expressed in) [^\n.]{0,30}(?:thousand|['’]000|million|riyals?|usd|sar|dollars?)[^\n.]{0,20}|\(all amounts[^)]{0,60}\)|all amounts[^\n]{0,50}", ti, re.I)[:2]
            r["unit_hint"] = re.search(r"thousand|['’]000", ti, re.I) is not None
            nc = 4 if pt in ("H1", "9M") else 2
            rs, pgs = getrows(doc, pi, r"net income|profit\)?[ /()a-z]{0,12}for the|loss\)?[ /()a-z]{0,12}for the")
            r["pdf"]["is"] = pgs; r["printed_is"] = printed(ti)
            r["is"] = sel(rs, "is", nc); r["is_cols"] = nc
            if not r["is"].get("net_income"): r["flags"].append("no net_income row")
        if pb is not None:
            tb = doc[pb].get_text(); ds = dates(head(tb, 900)); r["bs_end"] = ds[0] if ds else None; r["bs_prior_end"] = ds[1] if len(ds) > 1 else None
            rs, pgs = getrows(doc, pb, r"total liabilities$|total equity and liabilities"); r["pdf"]["bs"] = pgs; r["printed_bs"] = printed(tb)
            r["bs"] = sel(rs, "bs", 2)
            if len(ds) and re.search(r"thousand|['’]000", head(tb, 900), re.I): r["unit_hint"] = True
        if pc is not None:
            tc = doc[pc].get_text(); rs, pgs = getrows(doc, pc, r"cash.{0,40}(at (the )?end|end of (the )?(year|period)|at (december|march|june|september|31|30))|(at (the )?end|end of (the )?(year|period)).{0,30}cash"); r["pdf"]["cf"] = pgs; r["printed_cf"] = printed(tc)
            ds = dates(head(tc, 900)); r["cf_end"] = ds[0] if ds else None
            r["cf"] = sel(rs, "cf", 2)
        res.append(r)
    json.dump(res, open(os.path.join(outdir, f"auto_{sym}.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
    return res
if __name__ == "__main__":
    sym = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("B012_OUT", ".") 
    for r in run(sym, out):
        print(r["label"], r["sha"][:8], r["cls"], r.get("period_type"), r.get("period_end"), "bs_end", r.get("bs_end"), r.get("bs_prior_end"), r.get("pdf"), r["flags"], "scale", r.get("scale_text"), r.get("unit_hint"))
