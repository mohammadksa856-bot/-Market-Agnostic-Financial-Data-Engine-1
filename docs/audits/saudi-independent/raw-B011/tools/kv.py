"""kv.py <sym> <sha> <pages> : key statement rows (totals, cash flow subtotals, cash roll) from the text layer, compact."""
import sys, re, pymupdf, pg
KEY = re.compile(r"^(total |net cash|net (increase|decrease|\(decrease|change)|\(?(increase|decrease)|cash and cash equivalents (at|as|-)|cash (and|&) (bank|cash eq).*(end|31|30)|revenue|sales|net (income|profit|loss)|(profit|loss|income).{0,30}for the (period|year)|basic|earnings per|gross profit|operating (profit|loss|income)|cash.*end of)", re.I)
num = re.compile(r"^[\(\-]?[\d,]+(\.\d+)?\)?%?$|^-$")
sym, h, pgs = sys.argv[1:4]
m, p = pg.find(sym, h); d = pymupdf.open(p)
for n in [int(x) for x in pgs.split(",")]:
    print("--- p", n)
    lab = ""; nums = []
    def flush():
        global lab, nums
        s = (lab + "  " + "  ".join(nums)).strip()
        if nums and KEY.search(lab.strip()): print(s[:170])
        lab = ""; nums = []
    for l in d[n-1].get_text().splitlines():
        l = l.strip()
        if not l: continue
        if num.match(l): nums.append(l)
        else:
            if nums: flush()
            lab = (lab + " " + l).strip() if len(lab) < 80 and not lab.endswith(")") else l
    flush()
