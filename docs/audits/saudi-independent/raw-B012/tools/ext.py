"""Row extractor for text-layer statement pages (read-only). Rows are rebuilt from word coordinates.
Usage: ext.py <symbol> <shaprefix> <bs|is|cf>=<pdfpage> ...   -> prints selected headline rows with every numeric column
       ext.py <symbol> <shaprefix> rows=<pdfpage>             -> prints all rows of the page"""
import re, sys
import pymupdf
import pg
NUM = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?$|^-$")
def rows(page):
    ws = page.get_text("words")
    ws.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    out, cur, y = [], [], None
    for w in ws:
        yc = (w[1] + w[3]) / 2
        if y is None or abs(yc - y) <= 3:
            cur.append(w); y = yc if y is None else (y + yc) / 2
        else:
            out.append(cur); cur = [w]; y = yc
    if cur: out.append(cur)
    res = []
    for r in out:
        r.sort(key=lambda w: w[0])
        label, nums = [], []
        for w in r:
            t = w[4]
            if NUM.match(t) and (nums or label or True) and (label or nums):
                nums.append(t)
            elif NUM.match(t):
                nums.append(t)
            else:
                if nums:  # text after numbers: treat as new label chunk
                    label.append(t)
                else:
                    label.append(t)
        res.append((" ".join(label), nums))
    return res
def val(t):
    if t == "-": return 0
    neg = t.startswith("(") or t.startswith("-")
    v = float(t.strip("()-").replace(",", ""))
    v = int(v) if v == int(v) and "." not in t else v
    return -v if neg else v
K = {
 "bs": [("total_assets", r"^total assets"), ("total_liabilities", r"^total liabilities$"), ("total_equity", r"^total equity$|^total shareholders.? equity$"),
        ("cash", r"^cash (and|&) (cash equivalents|bank)"), ("ppe", r"^property,? (plant )?(and|&) equipment|^property, plant and equipment"),
        ("nci", r"non-controlling"), ("total_equity_and_liabilities", r"^total equity and liabilities|^total liabilities and (share|equity)")],
 "is": [("revenue", r"^(revenues?|sales|net sales|net revenues?)$|^revenue from contracts"), ("cost_of_revenue", r"^cost of (revenues?|sales|goods sold)"), ("gross_profit", r"^gross (profit|loss)"),
        ("operating_income", r"^(operating (profit|income)|results from operating)"),
        ("pbt", r"(profit|income|loss|\(loss\)).{0,25}before (zakat|income tax|tax|income)|before zakat"), ("tax", r"^\(?zakat|^income tax|^zakat and income tax|^tax(?! claim)|^\W*kfas"),
        ("net_income", r"^\(?(net )?(profit|income|loss)\)?[ /()a-z]{0,14}for the (year|period|three|six|nine)|^net (profit|income|loss)|^profit for|^(profit|loss)[ /()a-z]{0,14}after (zakat|tax)"),
        ("parent", r"(owners|shareholders|equity holders|parent) of the (company|parent|group)|^(owners|shareholders) of|^company$|attributable to former parent"), ("nci", r"non-controlling"), ("eps", r"earnings per share|basic|diluted")],
 "cf": [("cfo", r"net cash (generated from|from|provided by|\(used in\)|used in|flows? from)[^/]{0,40}operating|net cash.*operating activities"), ("cfi", r"net cash.*investing"), ("cff", r"net cash.*financing"),
        ("net_change", r"^net (change|increase|decrease|\(decrease\)|movement).{0,40}cash|^(increase|decrease|\(decrease\)|net).{0,30}in cash"),
        ("cash_begin", r"cash.{0,40}(beginning|at (the )?(january|1 )|(january|1 jan)|1 january)"), ("cash_end", r"cash.{0,40}(at (the )?end|end of (the )?(year|period)|at (december|march|june|september|31|30)|31 december|30 (june|september))|(at (the )?end|end of (the )?(year|period)).{0,30}cash"), ("fx", r"exchange (differences|rate)|foreign (currenc|exchange)"),
        ("capex", r"^(purchase|acquisition|additions?)( of| to)? (property|plant|fixed|equipment)|^purchase of property|^capital expenditure")],
}
if __name__ == "__main__":
    sym, pre = sys.argv[1:3]
    meta, p = pg.find(sym, pre)
    doc = pymupdf.open(p)
    for a in sys.argv[3:]:
        k, n = a.split("=")
        rs = rows(doc[int(n) - 1])
        if k == "rows":
            for l, nums in rs: print(f"{l[:70]:70s}", nums)
            continue
        print("==", k, "pdf p" + n)
        for key, rx in K[k]:
            hits = [(l, nums) for l, nums in rs if nums and re.search(rx, l, re.I)]
            for l, nums in hits[:3 if key in ("nci","parent","eps","fx","tax") else 2]:
                print(f"  {key:18s} {l[:55]:55s}", [val(x) for x in nums])
