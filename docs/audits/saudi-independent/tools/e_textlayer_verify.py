"""Batch2-E: compare manifest facts with the PDF text layer of the SOURCE document.

Independent of the engine reader: finds each fact's source_label on the cited
printed page (page offset auto-detected), takes the last two numeric tokens
following the label (current / prior year), and compares with the published
value (value * scale handled: manifest value is in statement units).
Usage: e_textlayer_verify.py <manifest.json> <source.pdf> [out.json]
"""
import json, re, sys
import pymupdf

NUM = re.compile(r"^\(?\)?[\d,]+(?:\.\d+)?\)?\(?$|^-$")

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def parse_tokens(lines):
    """Turn raw text lines into numeric tokens (value, is_dash). Handles split '(' '43,847' ')' and reversed ')236('."""
    toks = []
    pend = False
    for ln in lines:
        t = ln.strip()
        if not t:
            continue
        if t == "(":
            pend = True; continue
        if t == "-":
            toks.append(0.0); continue
        if re.fullmatch(r"[\(\)]+", t):
            continue
        m = re.fullmatch(r"([\(\)]*)([\d,]+(?:\.\d+)?)([\(\)]*)", t)
        if m:
            neg = ("(" in m.group(1)) or (")" in m.group(1) and "(" in m.group(3)) or ")" in m.group(1) or ")" in m.group(3)
            # "(236)", ")236(" and "(236" / "236)" all negative
            v = float(m.group(2).replace(",", ""))
            toks.append(-v if (neg or pend) else v)
            pend = False
    return toks

def find_offset(doc):
    for i, p in enumerate(doc):
        t = p.get_text().upper()
        if "STATEMENT OF FINANCIAL POSITION" in t and "ASSETS" in t:
            m = re.search(r"^\s*(\d{1,3})\s*$", p.get_text(), re.M)
            return i, p.get_text()
    return None, None

def page_lines(doc, idx):
    return [l for l in doc[idx].get_text().split("\n")]

def locate(lines, label):
    nl = norm(label)
    nl = re.sub(r"^(earnings per share )?", "", nl)
    exact, pre, rev = [], [], []
    for i, l in enumerate(lines):
        n = norm(l)
        if not n: continue
        if n == nl: exact.append(i)
        elif len(nl) > 6 and n.startswith(nl): pre.append(i)
        elif len(n) > 6 and nl.startswith(n) and n not in ("total equity", "finance cost", "finance costs"): rev.append(i)
    return exact + pre + rev

def values_after(lines, i):
    out = []
    j = i + 1
    # stop at next line that contains letters (next label)
    buf = []
    while j < len(lines):
        t = lines[j].strip()
        if re.search(r"[A-Za-z؀-ۿ]", t):
            break
        buf.append(t); j += 1
    return parse_tokens(buf)

def main():
    man = json.load(open(sys.argv[1], encoding="utf8"))
    doc = pymupdf.open(sys.argv[2])
    res = []
    # offset: printed page p -> pdf index. detect via printed page numbers in text
    printed = {}
    for i, p in enumerate(doc):
        for m in re.finditer(r"^\s*(\d{1,3})\s*$", p.get_text()[:400], re.M):
            printed.setdefault(int(m.group(1)), i)
    for f in man["facts"]:
        pg = f.get("page")
        row = {"metric": f["metric"], "label": f["source_label"], "period_end": f["period_end"],
               "period_kind": f["period_kind"], "page": pg, "published": f["value"]}
        cands = []
        if pg in printed: cands.append(printed[pg])
        for off in (1, 2, 0, 3):
            if pg is not None and 0 <= pg - 1 + off < len(doc): cands.append(pg - 1 + off)
        found = None
        parts = [x.strip() for x in f["source_label"].split(" + ")]
        for ci in dict.fromkeys(cands):
            lines = page_lines(doc, ci)
            pv_ = []
            for part in parts:
                got = None
                for h in locate(lines, part):
                    v = values_after(lines, h)
                    if v: got = v; break
                pv_.append(got)
            if all(pv_) and (len(parts) == 1 or all(len(v) >= 2 for v in pv_)):
                if len(parts) == 1: found = (ci, pv_[0]); break
                # sum the last two columns of each part
                a = sum(v[-2] for v in pv_); b = sum(v[-1] for v in pv_)
                found = (ci, [a, b]); break
        if not found:
            row["status"] = "label_not_found"; res.append(row); continue
        ci, vals = found
        cur = vals[-2] if len(vals) >= 2 else vals[-1]
        pri = vals[-1] if len(vals) >= 2 else None
        # column choice: 2025 col first, 2024 second
        is_cur = f["period_end"].startswith("2025")
        src = cur if is_cur else pri
        row.update(pdf_page=ci + 1, source_tokens=vals)
        if src is None:
            row["status"] = "no_prior_col"
        else:
            pv = float(f["value"])
            row["source_value"] = src
            row["status"] = "match" if pv == src else (("sign_convention" if f["metric"] == "depreciation_amortization" else "sign_only") if abs(pv) == abs(src) else "MISMATCH")
        res.append(row)
    summ = {}
    for r in res: summ[r["status"]] = summ.get(r["status"], 0) + 1
    out = {"manifest": sys.argv[1], "pdf": sys.argv[2], "summary": summ, "rows": res}
    if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], "w", encoding="utf8"), indent=1, ensure_ascii=False)
    print(summ)
    for r in res:
        if r["status"] != "match": print(r["status"], r["metric"], "|", r["label"], "|", r["period_end"], r.get("page"), r["published"], r.get("source_tokens"))

if __name__ == "__main__": main()
