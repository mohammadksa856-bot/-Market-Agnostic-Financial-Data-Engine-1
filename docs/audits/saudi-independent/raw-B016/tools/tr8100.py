"""Page transcript for 8100 SAICO (Saudi Arabian Cooperative Insurance Company). SAR thousands except FY2022-as-issued (full SAR). All statement pages read visually (image-only or garbled OCR layer)."""
from trlib import bs, write
from tr8120 import isx, cf, D

B25 = bs(2224346, 1809129, 415217, cash=180006, ppe=65992)
B24 = bs(1964290, 1582458, 381832, cash=98374, ppe=61763)
IS24 = isx(1080637, 53985, -4667, 49318, 1.64)
CF24 = cf(184315, -260245, 0, -75930, 174304, 98374)

docs = [
    D("c3fdea9b", "FY2025 audited FS (collector label 2026|FY = publication year); SAR thousands; text layer garbled, read from images", "2025-12-31", "2024-12-31", "FY",
      "visual: pdf p8 BS (printed 8), p9 IS (9), p13 CF (13) rendered at 2x and read", dict(bs=8, is_=9, cf=13),
      dict(cur=B25, prior=B24), dict(cur=isx(1156884, 28431, -6254, 22177, 0.74), prior=IS24),
      dict(cur=cf(16647, 64985, 0, 81632, 98374, 180006), prior=CF24)),
    D("3751df76", "FY2024 audited FS (label 2025|FY = publication year); SAR thousands; image-only statement pages", "2024-12-31", "2023-12-31", "FY",
      "visual: pdf p7 BS (printed 7), p8 IS (8), p12 CF (12) rendered and read", dict(bs=7, is_=8, cf=12),
      dict(cur=B24, prior=bs(2128264, 1814662, 313602, cash=174304, ppe=55476)),
      dict(cur=IS24, prior=isx(1044519, 78333, -7235, 71098, 2.37)),
      dict(cur=CF24, prior=cf(18708, 112524, 0, 131232, 43072, 174304))),
    D("6120d98d", "FY2023 audited FS (label 2024|FY = publication year); SAR thousands; image-only; 2022 and 1 Jan 2022 restated for IFRS 17/9", "2023-12-31", "2022-12-31", "FY",
      "visual: pdf p10 BS (printed 8), p11 IS (9), p15 CF (13) rendered and read; equity statement pdf p13 (printed 11) read for the opening restatement", dict(bs=10, is_=11, cf=15, equity=13),
      dict(cur=bs(2128264, 1814662, 313602, cash=174304, ppe=55476), prior=bs(1150965, 915527, 235438, cash=43072, ppe=29055, restated=True)),
      dict(cur=isx(1044519, 78333, -7235, 71098, 2.37), prior=isx(911675, -54408, -7239, -61647, -2.05, restated=True)),
      dict(cur=cf(18708, 112524, 0, 131232, 43072, 174304), prior=cf(18145, -27101, 0, -8956, 52028, 43072, restated=True)),
      restatements=["FY2022 restated for IFRS 17 and IFRS 9 transition (note 4): total assets 1,461,610 thousand as issued (1,461,610,325 full SAR) -> 1,150,965; total equity 257,924 -> 235,438; net loss -37,205 -> -61,647; cash 36,736 -> 43,072; CFO 10,943 -> 18,145; CFI -26,235 -> -27,101. Opening equity at 1 Jan 2022: 292,735 as previously reported, IFRS 17 adjustment -25,851 and IFRS 9 adjustment +25,137, restated 292,021 (equity statement pdf p13)."]),
    D("1601d15b", "FY2022 audited FS as issued under IFRS 4 (label 2023|FY = publication year); FULL SAR (not thousands); image-only statement pages", "2022-12-31", "2021-12-31", "FY",
      "visual: pdf p8 BS (printed 6), p9 IS (7), p13 CF (11) rendered and read", dict(bs=8, is_=9, cf=13),
      dict(cur=bs(1461610325, 1203686226, 257924099, cash=36736221), prior=bs(1355443724, 1062708155, 292735569, cash=52028429)),
      dict(cur=isx(None, -29965305, -7239413, -37204718, -1.24), prior=isx(None, -55537579, -7097100, -62634679, -2.09)),
      dict(cur=cf(10942990, -26235198, 0, -15292208, 52028429, 36736221), prior=cf(-37658082, 39686784, 0, 2028702, 49999727, 52028429))),
    D("01c03433", "H1 2026 reviewed interim (label 2026|H1 correct); SAR thousands; image-only statement pages; six and three months", "2026-06-30", "2025-06-30", "H1",
      "visual: pdf p4 BS (printed 3), p5 IS (4), p9 CF (8) rendered at 1.7x and read", dict(bs=4, is_=5, cf=9),
      dict(cur=bs(2180071, 1748903, 431168, cash=224464, ppe=67342), prior=B25),
      dict(cur=isx(743740, 18627, -2676, 15951, 0.53), prior=isx(555692, 30787, -3127, 27660, 0.92)),
      dict(cur=cf(129693, -85235, 0, 44458, 180006, 224464), prior=cf(-56256, 70039, 0, 13783, 98374, 112157)),
      ISQ=dict(cur=isx(394877, 3974, -1112, 2862, 0.10), prior=isx(292239, 14975, -1563, 13412, 0.45)),
      bs_prior_end="2025-12-31"),
    D("f37d8748", "Q1 2026 interim (label 2026|Q1 correct); SAR thousands; image-only statement pages", "2026-03-31", "2025-03-31", "Q1",
      "visual: pdf p4 BS (printed 3), p5 IS (4), p9 CF (8) rendered and read", dict(bs=4, is_=5, cf=9),
      dict(cur=bs(2344862, 1916556, 428306, cash=288354, ppe=67144), prior=B25),
      dict(cur=isx(348863, 14653, -1564, 13089, 0.44), prior=isx(263453, 15812, -1564, 14248, 0.47)),
      dict(cur=cf(157041, -48693, 0, 108348, 180006, 288354), prior=cf(114543, -1435, 0, 113108, 98374, 211482)),
      bs_prior_end="2025-12-31"),
    D("ccb6adbe", "9M 2025 interim (label 2025|9M correct); SAR thousands; image-only; nine and three months", "2025-09-30", "2024-09-30", "9M",
      "visual: pdf p4 BS (printed 3), p5 IS (4), p9 CF (8) rendered and read", dict(bs=4, is_=5, cf=9),
      dict(cur=bs(2007888, 1588297, 419591, cash=117761, ppe=64291), prior=B24),
      dict(cur=isx(848517, 39941, -4690, 35251, 1.18), prior=isx(804696, 43287, -6132, 37155, 1.24)),
      dict(cur=cf(-65263, 84650, 0, 19387, 98374, 117761), prior=cf(111045, -177623, 0, -66578, 174304, 107726)),
      ISQ=dict(cur=isx(292825, 9154, -1563, 7591, 0.25), prior=isx(268555, 14149, -2044, 12105, 0.40)),
      bs_prior_end="2024-12-31"),
    D("e17189e9", "H1 2025 interim (label 2025|H1 correct); SAR thousands; image-only; six and three months", "2025-06-30", "2024-06-30", "H1",
      "visual: pdf p4 BS (printed 4), p5 IS (5), p9 CF (9) rendered and read", dict(bs=4, is_=5, cf=9),
      dict(cur=bs(1969074, 1557074, 412000, cash=112157, ppe=63328), prior=B24),
      dict(cur=isx(555692, 30787, -3127, 27660, 0.92), prior=isx(536141, 29138, -4088, 25050, 0.84)),
      dict(cur=cf(-56256, 70039, 0, 13783, 98374, 112157), prior=cf(104590, -178306, 0, -73716, 174304, 100588)),
      ISQ=dict(cur=isx(292239, 14975, -1563, 13412, 0.45), prior=isx(259109, 23886, -2044, 21842, 0.73)),
      bs_prior_end="2024-12-31"),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    d["unit"] = "SAR full riyals" if d["sha256_prefix"] == "1601d15b" else "SAR thousands"
    for blk in ("is", "is_q"):
        for col in ("cur", "prior"):
            c = d.get(blk, {}).get(col)
            if c and c.get("revenue") is None:
                c.pop("revenue", None)

rolls = [
    dict(name="2026 H1 net income = Q1 + Q2", total=["01c03433", "is", "cur", "net_income"], parts=[["f37d8748", "is", "cur", "net_income"], ["01c03433", "is_q", "cur", "net_income"]]),
    dict(name="2026 H1 insurance revenue = Q1 + Q2", total=["01c03433", "is", "cur", "revenue"], parts=[["f37d8748", "is", "cur", "revenue"], ["01c03433", "is_q", "cur", "revenue"]]),
    dict(name="2026 H1 pre-zakat income = Q1 + Q2", total=["01c03433", "is", "cur", "pbt"], parts=[["f37d8748", "is", "cur", "pbt"], ["01c03433", "is_q", "cur", "pbt"]]),
    dict(name="2025 H1 net income = Q1 2025 (Q1 2026 filing prior) + Q2 2025", total=["e17189e9", "is", "cur", "net_income"], parts=[["f37d8748", "is", "prior", "net_income"], ["e17189e9", "is_q", "cur", "net_income"]]),
    dict(name="2025 H1 insurance revenue = Q1 2025 + Q2 2025", total=["e17189e9", "is", "cur", "revenue"], parts=[["f37d8748", "is", "prior", "revenue"], ["e17189e9", "is_q", "cur", "revenue"]]),
    dict(name="2025 9M net income = H1 + Q3", total=["ccb6adbe", "is", "cur", "net_income"], parts=[["e17189e9", "is", "cur", "net_income"], ["ccb6adbe", "is_q", "cur", "net_income"]]),
    dict(name="2025 9M insurance revenue = H1 + Q3", total=["ccb6adbe", "is", "cur", "revenue"], parts=[["e17189e9", "is", "cur", "revenue"], ["ccb6adbe", "is_q", "cur", "revenue"]]),
    dict(name="2024 9M net income = H1 2024 + Q3 2024", total=["ccb6adbe", "is", "prior", "net_income"], parts=[["e17189e9", "is", "prior", "net_income"], ["ccb6adbe", "is_q", "prior", "net_income"]]),
    dict(name="2024 9M insurance revenue = H1 2024 + Q3 2024", total=["ccb6adbe", "is", "prior", "revenue"], parts=[["e17189e9", "is", "prior", "revenue"], ["ccb6adbe", "is_q", "prior", "revenue"]]),
]
if __name__ == "__main__":
    write("8100", "SAUDI ARABIAN COOPERATIVE INSURANCE COMPANY (SAICO)", "SAR", "SAR thousands as printed, except the FY2022-as-issued filing in full SAR", docs, rolls)
