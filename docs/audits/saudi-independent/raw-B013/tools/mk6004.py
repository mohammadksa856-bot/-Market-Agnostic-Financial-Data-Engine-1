"""Page transcription for 6004 CATRION (formerly Saudi Airlines Catering Company; full SAR). Writes transcripts/6004.json."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "6004.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, capex, cfi, cff, net, b, e, **k):
    d = dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)
    if capex is not None:
        d["capex"] = capex
    return d


def inc(rev, cost, gp, op, pbt, tax, ni, par=None, nci=None, **k):
    d = dict(revenue=rev, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, **k)
    if cost is not None:
        d["cost_of_revenue"] = cost
    if par is not None:
        d["ni_parent"] = par
        d["ni_nci"] = nci
    return d


def fix(d):
    d = dict(d)
    if "is_" in d:
        d["is"] = d.pop("is_")
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    return d


D = []
D.append(dict(sha256_prefix="20bface3", label="FY2022 audited consolidated FS of Saudi Airlines Catering Company (statement pages image-only; collector label 2023|FY = publication year)",
  period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
  reading="visual: pdf p6-10 textless; p7 BS (printed 5), p8 IS (6), p10 CF (8) rendered and read", pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(2031194829, 911268650, 1119926179, 417242028, 340951680), prior=bs(1930631082, 1058112338, 872518744, 176462367, 408006473)),
  is_=dict(cur=inc(1818006368, -1301686626, 516319742, 283964166, 285820965, -28717827, 257103138, eps_basic=3.14),
           prior=inc(1212507870, -880662708, 331845162, 60356735, 33768047, -19712588, 14055459, eps_basic=0.17)),
  cf=dict(cur=cf(346200353, -18464052, -15061554, -90359138, 240779661, 176462367, 417242028),
          prior=cf(373165315, -36172974, -35622511, -418534336, -80991532, 257453899, 176462367))))
D.append(dict(sha256_prefix="66999970", label="FY2023 audited consolidated FS of Catrion Catering Holding Co (formerly Saudi Airlines Catering); statement pages image-only (inventory class partial_statements; label 2024|FY = publication year)",
  period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
  reading="visual: pdf p7-10 textless; p7 BS (printed 5), p8 IS (6), p10 CF (8) rendered and read", pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(2194892031, 908823567, 1286068464, 702456181, 414893911), prior=bs(2031194829, 911268650, 1119926179, 417242028, 340951680)),
  is_=dict(cur=inc(2133762298, -1567769793, 565992505, 304368560, 316537740, -33880036, 282657704, eps_basic=3.45),
           prior=inc(1818006368, -1301686626, 516319742, 283964166, 285820965, -28717827, 257103138, eps_basic=3.14)),
  cf=dict(cur=cf(608006445, -135946943, -122553347, -200238945, 285214153, 417242028, 702456181),
          prior=cf(346200353, -18464052, -15061554, -90359138, 240779661, 176462367, 417242028,
                   _declared_diff={"cfo": "none; presentation only: subtotal 'cash generated from operating activities' 377,368,494 in the FY2022 file versus 384,843,240 here because the long-term bonus payment (7,474,746) is shown separately; CFO identical"}))))
D.append(dict(sha256_prefix="954d5faa", label="FY2024 audited consolidated FS (statement pages image-only; inventory class financial_statements; label 2025|FY = publication year)",
  period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
  reading="visual: pdf p7-10 textless; p7 BS (printed 5), p8 IS (6), p10 CF (8) rendered and read", pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(2687838354, 1236022691, 1451815663, 631298642, 805396744), prior=bs(2194892031, 908823567, 1286068464, 702456181, 414893911)),
  is_=dict(cur=inc(2299259701, -1657650977, 641608724, 360516516, 375713161, -22943053, 352770108, eps_basic=4.30),
           prior=inc(2133762298, -1567769793, 565992505, 304368560, 316537740, -33880036, 282657704, eps_basic=3.45)),
  cf=dict(cur=cf(461873856, -446728821, -442295837, -90735558, -71157539, 702456181, 631298642),
          prior=cf(608006445, -135946943, -122553347, -200238945, 285214153, 417242028, 702456181))))
D.append(dict(sha256_prefix="f53011f6", label="FY2025 audited consolidated FS (statement pages image-only; inventory class financial_statements; label 2026|FY = publication year)",
  period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading="visual: pdf p6-10 textless; p7 BS (printed 5), p8 IS (6), p10 CF (8) rendered and read", pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(3451579427, 1876726304, 1574853123, 398453391, 1263467340), prior=bs(2687838354, 1236022691, 1451815663, 631298642, 805396744)),
  is_=dict(cur=inc(2441044531, -1749238963, 691805568, 364830584, 330745471, -17124175, 313621296, eps_basic=3.82),
           prior=inc(2299259701, -1657650977, 641608724, 360516516, 375713161, -22943053, 352770108, eps_basic=4.30)),
  cf=dict(cur=cf(320222095, -548439846, -546664970, -6402376, -232845251, 631298642, 398453391),
          prior=cf(461873856, -446728821, -442295837, -90735558, -71157539, 702456181, 631298642))))
D.append(dict(sha256_prefix="d7dea47a", label="Unaudited interim condensed consolidated FS 3M and 6M ended 2025-06-30 (text layer drops some lines; only lines present and arithmetic-tied are transcribed)",
  period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
  reading="text layer with missing lines: pdf p4 IS (printed 2), p5 BS (3), p7 CF (5); cost of revenue and several lines not extractable and not transcribed", pages=dict(bs=5, is_=4, cf=7),
  bs=dict(cur=bs(3103400727, 1608445135, 1494955592, 304336410, 1119329211), prior=bs(2687838354, 1236022691, 1451815663, 631298642, 805396744)),
  is_=dict(cur=inc(1160839823, None, 329049468, 164351311, 149656060, -9489907, 140166153, eps_basic=1.71),
           prior=inc(1117618548, None, 301891564, 145489451, 159453319, -15043251, 144410068, eps_basic=1.76)),
  is_q=dict(cur=inc(571452671, None, 159159948, 77408753, 68250409, -2861937, 65388472, eps_basic=0.80),
            prior=inc(564805470, None, 149435020, 73574951, 78698096, -5516334, 73181762, eps_basic=0.89)),
  cf=dict(cur=cf(-64506900, -342760895, -342146289, 79690957, -326962232, 631298642, 304336410),
          prior=cf(75021280, -103601697, -97868449, -114526804, -137373973, 702456181, 565082208))))
D.append(dict(sha256_prefix="9b85d057", label="Unaudited interim condensed consolidated FS 3M and 6M ended 2026-06-30 (text layer scrambles IS and CF lines; rendered pages used for IS and CF, text for BS)",
  period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
  reading="visual: pdf p4 IS (printed 2) and p8 CF (6) rendered and read; BS pdf p6 (4) from text layer tied by identity", pages=dict(bs=6, is_=4, cf=8),
  bs=dict(cur=bs(4278720466, 2637987794, 1640732672, 342676997, 1384736022, equity_nci=32856003), prior=bs(3451579427, 1876726304, 1574853123, 398453391, 1263467340)),
  is_=dict(cur=inc(1352198759, -998286226, 353912533, 180239701, 133459456, -6235888, 127223568, 127972658, -749090, eps_basic=1.56),
           prior=inc(1160839823, -831790355, 329049468, 164351311, 149656060, -9489907, 140166153, 140166153, 0, eps_basic=1.71)),
  is_q=dict(cur=inc(688127066, -520554760, 167572306, 76997219, 49869749, -3085756, 46783993, 47560521, -776528, eps_basic=0.58),
            prior=inc(571452671, -412292723, 159159948, 77408753, 68250409, -2861937, 65388472, 65388472, 0, eps_basic=0.80)),
  cf=dict(cur=cf(364694057, -143299772, -467901954, 47431503, -55776394, 398453391, 342676997),
          prior=cf(-64506900, -342760895, -342146289, 79690957, -326962232, 631298642, 304336410))))
D.append(dict(sha256_prefix="9af63009", label="Unaudited interim condensed consolidated FS 3M ended 2026-03-31 (statement pages pdf p4-7 image-only; inventory finds only index/notes)",
  period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
  reading="visual: pdf p4 IS (printed 2), p5 BS (3), p7 CF (5) rendered and read; p6 equity statement not read", pages=dict(bs=5, is_=4, cf=7),
  bs=dict(cur=bs(4040077192, 2434850142, 1605227050, 210193256, 1354356498, equity_nci=42189857), prior=bs(3451579427, 1876726304, 1574853123, 398453391, 1263467340)),
  is_=dict(cur=inc(664071693, -477731466, 186340227, 103242482, 83589707, -3150132, 80439575, 80412137, 27438, eps_basic=0.98),
           prior=inc(589387152, -419497632, 169889520, 86942558, 81405651, -6627970, 74777681, 74777681, 0, eps_basic=0.91)),
  cf=dict(cur=cf(223926355, -73915819, -396709560, -15476930, -188260135, 398453391, 210193256),
          prior=cf(-99695038, -165005179, -164388733, 76202785, -187880986, 631298642, 443417656))))

P = lambda pre, blk, col, key: [pre, blk, col, key]
roll = []
for key in ("revenue", "cost_of_revenue", "operating_income", "pbt", "net_income", "ni_parent"):
    roll.append(dict(name=f"Q1 2026 + Q2 2026 = H1 2026 {key}", total=P("9b85d057", "is", "cur", key), parts=[P("9af63009", "is", "cur", key), P("9b85d057", "is_q", "cur", key)]))
for key in ("revenue", "gross_profit", "operating_income", "pbt", "net_income"):
    roll.append(dict(name=f"Q1 2025 (comparative in Q1 2026) + Q2 2025 = H1 2025 {key}", total=P("9b85d057", "is", "prior", key), parts=[P("9af63009", "is", "prior", key), P("9b85d057", "is_q", "prior", key)]))
t = dict(symbol="6004", name="CATRION (Catrion Catering Holding Co, formerly Saudi Airlines Catering Company)", currency="SAR", unit="full SAR (no scaling) in every filing read", docs=[fix(d) for d in D], roll_checks=roll)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("docs", len(D))
