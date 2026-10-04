"""keyrows.py <sym> <sha> [pages]: key statement rows only (totals, income subtotals, cash-flow subtotals) from the text layer. Without pages, scans all pages for statement pages."""
import sys, re, pymupdf, pg
KEY = re.compile(r"(total assets|total (current|non-?\s?current) assets|total (equity|liabilities)|total shareholders|^equity and liab|net cash|net (change|increase|decrease|\(decrease|income|profit|loss)|cash and cash equivalents? (at|as|-|in|,)|cash (and|&) (bank|cash eq).{0,40}(end|beginning)|^revenues?\b|^sales|^gross (profit|loss)|operating (profit|loss|income)|(profit|income|loss) (before|from operations|for the)|earnings per|loss per|basic|cost of (revenue|sales|goods)|property, plant|statement of (financial position|profit|cash))", re.I)
num = re.compile(r"^[\(\-]?[\d,]+(\.\d+)?\)?%?$|^-$")
sym, h = sys.argv[1:3]
m, p = pg.find(sym, h); d = pymupdf.open(p)
pgs = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
if pgs is None:
    pgs = [i + 1 for i in range(min(len(d), 14)) if len(d[i].get_text().strip()) > 200]
for n in pgs:
    out = []; lab = ""; nums = []
    def flush():
        global lab, nums
        s = (lab + "  " + "  ".join(nums)).strip()
        if (nums and KEY.search(lab.strip())) or re.search(r"statement of (financial position|profit|cash)", lab, re.I): out.append(s[:190])
        lab = ""; nums = []
    for l in d[n-1].get_text().splitlines():
        l = l.strip()
        if not l: continue
        if num.match(l) or l in ("(", ")"): nums.append(l)
        else:
            if nums: flush()
            lab = (lab + " " + l).strip() if lab and not nums else l
    flush()
    if out: print("--- p", n); print("\n".join(out))
