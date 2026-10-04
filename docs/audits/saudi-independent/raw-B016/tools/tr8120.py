"""Page transcript for 8120 Gulf Union Alahlia Cooperative Insurance (SAR full riyals as printed). FY2022 and FY2023 statements; 9M 2022 read visually where noted."""
from trlib import bs, write


def isx(rev, pbt, tax, ni, eps=None, **k):
    d = dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni)
    if eps is not None:
        d["eps_basic"] = eps
    d.update(k)
    return d


def cf(cfo, cfi, cff, net, begin, end, fx=0, **k):
    d = dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=begin, fx=fx, cash_end=end)
    d.update(k)
    return d


def D(sha, label, pe, pr, typ, reading, pages, BS, IS, CF, ISQ=None, bs_prior_end=None, restatements=None):
    d = dict(sha256_prefix=sha, label=label, period_end=pe, prior_end=pr, period_type=typ, reading=reading, pages=pages, bs=BS, cf=CF)
    d["is"] = IS
    if ISQ:
        d["is_q"] = ISQ
    if bs_prior_end:
        d["bs_prior_end"] = bs_prior_end
    if restatements:
        d["restatements"] = restatements
    return d


B24 = bs(1195977828, 569278629, 626699199, cash=53973519)
B25 = bs(1157085266, 588142634, 568942632, cash=52830964, ppe=6076605)
IS24 = isx(804752396, 51551645, -7906129, 43645516, 0.95)
CF24 = cf(64857695, -62517531, -3481121, -1140957, 55114476, 53973519)
IS23 = isx(624483382, 127037351, -2000000, 125037351, 2.72)
CF23 = cf(138843962, -181717783, -2330085, -45203906, 100318382, 55114476)
BSD23 = bs(1067226470, 519234645, 547991825, cash=55114476)

docs = [
    D("ecca065f", "FY2025 audited FS inside the annual report (collector label 2026|FY = publication year); IFRS 17, single company statements", "2025-12-31", "2024-12-31", "FY",
      "text layer: pdf p8 BS (printed 7), p9 IS (8), p12-13 CF (11-12)", dict(bs=8, is_=9, cf="12-13"),
      dict(cur=B25, prior=bs(1195977828, 569278629, 626699199, cash=53973519, ppe=7696401)),
      dict(cur=isx(1038197346, -72826718, -10800000, -83626718, -1.82), prior=IS24),
      dict(cur=cf(-89145754, 92414262, -4411063, -1142555, 53973519, 52830964), prior=CF24)),
    D("72d9553f", "FY2024 audited FS inside the annual report (label 2025|FY = publication year)", "2024-12-31", "2023-12-31", "FY",
      "text layer: pdf p8 BS (printed 7), p9 IS (8), p12-13 CF (11-12)", dict(bs=8, is_=9, cf="12-13"),
      dict(cur=B24, prior=BSD23), dict(cur=IS24, prior=IS23), dict(cur=CF24, prior=CF23)),
    D("e9810ff7", "FY2023 audited FS inside the annual report (label 2024|FY = publication year); statement pages are image-only; 2022 and 1 Jan 2022 restated for IFRS 17", "2023-12-31", "2022-12-31", "FY",
      "visual: pdf p11 BS (printed 10), p12 IS (11), p16-17 CF (15-16) rendered and read", dict(bs=11, is_=12, cf="16-17"),
      dict(cur=bs(1067226470, 519234645, 547991825, cash=55114476, ppe=8420561),
           prior=bs(946808543, 531371863, 415436680, cash=100318382, ppe=7565938, restated=True)),
      dict(cur=IS23, prior=isx(506772116, -16299703, -2000000, -18299703, -0.47, restated=True)),
      dict(cur=CF23, prior=cf(-71567190, -167610757, 224518081, -14659866, 114978248, 100318382, restated=True)),
      restatements=["FY2022 restated for the IFRS 4 to IFRS 17 transition (notes 3 and 4): total assets 1,053,695,384 as issued -> 946,808,543; total equity 334,592,277 -> 415,436,680; net result 2,523,564 profit -> 18,299,703 loss; pre-zakat result 4,523,564 -> -16,299,703; cash 100,322,227 -> 100,318,382; opening 1 Jan 2022 equity 132,025,122 -> 202,916,630; cash flow cfo -73,849,036 -> -71,567,190, cfi -165,328,911 -> -167,610,757"]),
    D("bf341b2f", "FY2022 audited FS as issued under IFRS 4 inside the annual report (label 2023|FY = publication year)", "2022-12-31", "2021-12-31", "FY",
      "text layer: pdf p10 BS (printed 9), p11-12 IS (10-11), p16-17 CF (15-16)", dict(bs=10, is_="11-12", cf="16-17"),
      dict(cur=bs(1053695384, 719103107, 334592277, cash=100322227, ppe=7565938), prior=bs(930757029, 798731907, 132025122, cash=114982093, ppe=8854908)),
      dict(cur=isx(434827553, 4523564, -2000000, 2523564, 0.07, _declared_diff={"revenue": "IFRS 4 total revenues (net premiums earned plus commissions); not comparable to IFRS 17 insurance revenue"}),
           prior=isx(594396964, -139189259, -2000000, -141189259, -5.67)),
      dict(cur=cf(-73849036, -165328911, 224518081, -14659866, 114982093, 100322227), prior=cf(-158345932, 94895746, -1075750, -64525936, 179508029, 114982093))),
    D("c5cbd36d", "9M 2022 interim, whole-file scan (label 2022|9M correct; inventory class scanned_unreadable but it holds full statements); nine and three months; IFRS 4; CF not read", "2022-09-30", "2021-09-30", "9M",
      "visual: pdf p4 BS (printed 3), p6 IS continued (printed 5) rendered and read", dict(bs=4, is_="5-6"),
      dict(cur=bs(1030146416, 703806124, 326340292, cash=91632827, ppe=7091485), prior=bs(930757029, 798731907, 132025122, cash=114982093, ppe=8854908)),
      dict(cur=isx(None, -14565443, -1500000, -16065443, -0.45), prior=isx(None, -120653435, -2000000, -122653435, -4.92)),
      {},
      ISQ=dict(cur=isx(None, 4107073, -500000, 3607073, 0.08), prior=isx(None, -17055510, 0, -17055510, -0.68)),
      bs_prior_end="2021-12-31"),
    D("f518cfe1", "9M 2025 interim (label 2025|9M correct); nine and three months", "2025-09-30", "2024-09-30", "9M",
      "text layer: pdf p4 BS (printed 3), p5 IS (4), p8-9 CF (7-8)", dict(bs=4, is_=5, cf="8-9"),
      dict(cur=bs(1146695301, 599663911, 547031390, cash=64231340), prior=B24),
      dict(cur=isx(766336128, -76647409, -8100000, -84747409, -1.85), prior=isx(568479632, 44079814, -5906129, 38173685, 0.83)),
      dict(cur=cf(-72105728, 86454438, -4090889, 10257821, 53973519, 64231340), prior=cf(26620732, -61849326, -2634114, -37862708, 55114476, 17251768)),
      ISQ=dict(cur=isx(258114857, -14218197, -2700000, -16918197, -0.37), prior=isx(210004511, 13043192, -1500000, 11543192, 0.25)),
      bs_prior_end="2024-12-31"),
    D("4bc33d9d", "H1 2025 interim (label 2025|H1 correct); six and three months", "2025-06-30", "2024-06-30", "H1",
      "text layer: pdf p4 BS (printed 3), p5 IS (4), p8-9 CF (7-8)", dict(bs=4, is_=5, cf="8-9"),
      dict(cur=bs(1172394405, 608444818, 563949587, cash=24082069), prior=B24),
      dict(cur=isx(508221271, -62429212, -5400000, -67829212, -1.48), prior=isx(358475121, 31036622, -4406129, 26630493, 0.58)),
      dict(cur=cf(-30154022, 3665111, -3402539, -29891450, 53973519, 24082069), prior=cf(18788382, -46812142, -2289720, -30313480, 55114476, 24800996)),
      ISQ=dict(cur=isx(260210425, -25181102, -2700000, -27881102, -0.61), prior=isx(192520476, 10743236, -3656129, 7087107, 0.15)),
      bs_prior_end="2024-12-31"),
    D("a9efebce", "Q1 2026 interim (label 2026|Q1 correct)", "2026-03-31", "2025-03-31", "Q1",
      "text layer: pdf p4 BS (printed 3), p5 IS (4), p8-9 CF (7-8)", dict(bs=4, is_=5, cf="8-9"),
      dict(cur=bs(1167306762, 594167970, 573138792, cash=95736669), prior=B25),
      dict(cur=isx(241432967, 5696160, -1500000, 4196160, 0.09), prior=isx(248010846, -37248110, -2700000, -39948110, -0.87)),
      dict(cur=cf(-13068983, 56567123, -592435, 42905705, 52830964, 95736669), prior=cf(-7416386, -2061142, -2036437, -11513965, 53973519, 42459554)),
      bs_prior_end="2025-12-31"),
    D("6d995550", "H1 2026 interim (label 2026|H1 correct); six and three months", "2026-06-30", "2025-06-30", "H1",
      "text layer: pdf p4 BS (printed 2), p5 IS (3), p8 CF (6)", dict(bs=4, is_=5, cf=8),
      dict(cur=bs(1107201197, 536576333, 570624864, cash=57419539), prior=B25),
      dict(cur=isx(464732809, 5477983, -3795751, 1682232, 0.04), prior=isx(508221271, -62429212, -5400000, -67829212, -1.48)),
      dict(cur=cf(-61441487, 68973114, -2943052, 4588575, 52830964, 57419539), prior=cf(-30154022, 3665111, -3402539, -29891450, 53973519, 24082069)),
      ISQ=dict(cur=isx(223299842, -218177, -2295751, -2513928, -0.05), prior=isx(260210425, -25181102, -2700000, -27881102, -0.61)),
      bs_prior_end="2025-12-31"),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    for blk in ("is", "is_q"):
        for col in ("cur", "prior"):
            c = d.get(blk, {}).get(col)
            if c and c.get("revenue") is None:
                c.pop("revenue", None)
    if not d.get("cf"):
        d.pop("cf")

rolls = [
    dict(name="2025 H1 net income = Q1 2025 (Q1 2026 filing prior column) + Q2 2025", total=["4bc33d9d", "is", "cur", "net_income"], parts=[["a9efebce", "is", "prior", "net_income"], ["4bc33d9d", "is_q", "cur", "net_income"]]),
    dict(name="2025 H1 insurance revenue = Q1 + Q2", total=["4bc33d9d", "is", "cur", "revenue"], parts=[["a9efebce", "is", "prior", "revenue"], ["4bc33d9d", "is_q", "cur", "revenue"]]),
    dict(name="2025 9M net income = H1 + Q3", total=["f518cfe1", "is", "cur", "net_income"], parts=[["4bc33d9d", "is", "cur", "net_income"], ["f518cfe1", "is_q", "cur", "net_income"]]),
    dict(name="2025 9M insurance revenue = H1 + Q3", total=["f518cfe1", "is", "cur", "revenue"], parts=[["4bc33d9d", "is", "cur", "revenue"], ["f518cfe1", "is_q", "cur", "revenue"]]),
    dict(name="2024 9M net income = H1 2024 + Q3 2024", total=["f518cfe1", "is", "prior", "net_income"], parts=[["4bc33d9d", "is", "prior", "net_income"], ["f518cfe1", "is_q", "prior", "net_income"]]),
    dict(name="2026 H1 net income = Q1 2026 + Q2 2026", total=["6d995550", "is", "cur", "net_income"], parts=[["a9efebce", "is", "cur", "net_income"], ["6d995550", "is_q", "cur", "net_income"]]),
    dict(name="2026 H1 insurance revenue = Q1 + Q2", total=["6d995550", "is", "cur", "revenue"], parts=[["a9efebce", "is", "cur", "revenue"], ["6d995550", "is_q", "cur", "revenue"]]),
    dict(name="2026 H1 pre-zakat result = Q1 + Q2", total=["6d995550", "is", "cur", "pbt"], parts=[["a9efebce", "is", "cur", "pbt"], ["6d995550", "is_q", "cur", "pbt"]]),
]
write("8120", "GULF UNION ALAHLIA COOPERATIVE INSURANCE COMPANY", "SAR", "SAR full riyals as printed", docs, rolls)
