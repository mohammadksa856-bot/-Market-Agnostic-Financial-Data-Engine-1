"""kv2.py <sym> <sha> <pages>: key statement lines (searches anywhere in the joined label+numbers row), cleaned of rule characters."""
import sys, re, pymupdf, pg
PAT = re.compile(r"(total assets|total liabilities  |total equity  |property and equipment  \d|cash and (cash equivalents|bank balances)  [\d,]+  [\d,]+|revenue  |costs? of revenue  |gross profit|operating (profit|loss)|before zakat|(profit|loss)( / \(loss\))? for the (period|year)  |net cash|net (increase|decrease|\(decrease)|\(decrease\)|at beginning|at end|end of the (period|year)|total (current )?liabilities|basic and diluted|additions to property|short term deposits  [\d,]+  [\d,]+|share of results|interest income|finance costs?  )", re.I)
num = re.compile(r"^[\(\-]?[\d,]+(\.\d+)?\)?%?$|^-$")
sym, h, pgs = sys.argv[1:4]
m, p = pg.find(sym, h); d = pymupdf.open(p)
for n in [int(x) for x in pgs.split(",")]:
    print("--- p", n)
    lab = ""; nums = []
    def flush():
        global lab, nums
        s = re.sub(r"[─═]+", "", (lab + "  " + "  ".join(nums))).strip()
        s = re.sub(r"\s{3,}", "  ", s)
        if nums and PAT.search(s): print(s[:190])
        lab = ""; nums = []
    for l in d[n-1].get_text().splitlines():
        l = l.strip()
        if not l: continue
        if num.match(l): nums.append(l)
        else:
            if nums: flush()
            lab = (lab + " " + l).strip() if len(lab) < 90 and not lab.endswith(")") else l
    flush()
