"""Page transcript for 8170 Al-Etihad Cooperative Insurance (SAR thousands; FY2022-as-issued in full SAR). All statement pages read visually."""
from trlib import bs, write
from tr8120 import isx, cf, D

B25 = bs(1201190, 751605, 449585, cash=94988, ppe=4911)
B24r = bs(1509526, 797869, 711657, cash=106067, ppe=7523, restated=True)
B24 = bs(1550782, 839125, 711657, cash=106067, ppe=22260)
B23 = bs(1869813, 1198193, 671620, cash=77374, ppe=19820)
IS24 = isx(1489646, 57134, -8000, 49134, 0.98)
IS23 = isx(1202169, 103896, -10000, 93896, 2.09)
CF23 = cf(280987, -393480, 0, -112493, 189867, 77374)

docs = [
    D("32269f80", "FY2025 audited FS (collector label 2026|FY = publication year); SAR thousands; image-only statement pages", "2025-12-31", "2024-12-31", "FY",
      "visual: pdf p7 BS (printed 5), p8 IS (6), p11-12 CF (9-10) rendered and read; note 35 reclassification text read", dict(bs=7, is_=8, cf="11-12"),
      dict(cur=B25, prior=B24r), dict(cur=isx(1254553, -232662, -11782, -244444, -4.89), prior=IS24),
      dict(cur=cf(-236436, 258804, -33447, -11079, 106067, 94988), prior=cf(-320454, 380422, -31275, 28693, 77374, 106067, restated=True))),
    D("7a886b41", "FY2024 audited FS as issued (label 2025|FY = publication year); SAR thousands; image-only", "2024-12-31", "2023-12-31", "FY",
      "visual: pdf p9 BS (printed 7), p10 IS (8), p13 CF (11) rendered and read", dict(bs=9, is_=10, cf=13),
      dict(cur=B24, prior=B23), dict(cur=IS24, prior=isx(1202169, 103896, -10000, 93896, 1.88)),
      dict(cur=cf(-338081, 393774, -27000, 28693, 77374, 106067), prior=CF23)),
    D("c7fd5fda", "FY2023 audited FS (label 2024|FY = publication year); SAR thousands; image-only; 2022 and 1 Jan 2022 restated and unaudited", "2023-12-31", "2022-12-31", "FY",
      "visual: pdf p11 BS (printed 9), p12 IS (10), p15 CF (13) rendered and read", dict(bs=11, is_=12, cf=15),
      dict(cur=B23, prior=bs(1515459, 978845, 536614, cash=189867, ppe=13343, restated=True)),
      dict(cur=IS23, prior=isx(1072869, 31202, -18500, 12702, 0.28, restated=True)),
      dict(cur=CF23, prior=cf(89392, -435023, 0, -345631, 535498, 189867, restated=True)),
      restatements=["FY2022 restated to IFRS 17 in the FY2023 filing and labelled Unaudited: total assets 1,810,631,516 as issued -> 1,515,459 thousand, shareholders' equity 565,258,467 (566,901,335 with accumulated surplus) -> 536,614, income attributable to shareholders 32,290,996 -> 12,702 thousand, revenue 1,037,956,465 (IFRS 4 total revenues) -> 1,072,869 (insurance revenue), CFO 89,391,163 -> 89,392 thousand; 1 Jan 2022 total assets 1,629,021,037 (31 Dec 2021 as issued) -> 1,422,604"]),
    D("108aea03", "FY2022 audited FS as issued under IFRS 4 (label 2023|FY = publication year); FULL SAR; image-only", "2022-12-31", "2021-12-31", "FY",
      "visual: pdf p8-9 BS (printed 6-7), p10-11 IS (8-9), p14 CF (12) rendered and read", dict(bs="8-9", is_="10-11", cf=14),
      dict(cur=bs(1810631516, 1243730181, 566901335, cash=189867156, ppe=13342653), prior=bs(1629021037, 1074433427, 554587610, cash=535498139, ppe=17773176)),
      dict(cur=isx(1037956465, 50790996, -18500000, 32290996, 0.72), prior=isx(764638092, 48432317, -15000000, 33432317, 0.74)),
      dict(cur=cf(89391163, -435022146, 0, -345630983, 535498139, 189867156), prior=cf(160043906, -76261618, 0, 83782288, 451715851, 535498139))),
    D("e663a175", "H1 2026 reviewed interim (label 2026|H1 correct); whole-file 51-page scan classed scanned_unreadable but holds full statements; six and three months; auditor's going-concern material uncertainty", "2026-06-30", "2025-06-30", "H1",
      "visual: pdf p3 review report, p4 BS (printed 2), p5 IS (3), p8-9 CF (6-7) rendered and read", dict(bs=4, is_=5, cf="8-9"),
      dict(cur=bs(1053867, 696476, 357391, cash=130331, ppe=4063), prior=B25),
      dict(cur=isx(603164, -88176, -4018, -92194, -1.84), prior=isx(605544, -69896, -5716, -75612, -1.51)),
      dict(cur=cf(-92818, 128161, 0, 35343, 94988, 130331), prior=cf(-124848, 126468, -30000, -28380, 106067, 77687)),
      ISQ=dict(cur=isx(301725, -51611, -1018, -52629, -1.05), prior=isx(317227, -61444, -2250, -63694, -1.27)),
      bs_prior_end="2025-12-31"),
    D("39ad317e", "Q1 2026 interim (label 2026|Q1 correct); image-only; cash-flow operating and investing sections (pdf p8) NOT read", "2026-03-31", "2025-03-31", "Q1",
      "visual: pdf p4 BS (printed 2), p5 IS (3), p9 CF tail (7) rendered and read", dict(bs=4, is_=5, cf=9),
      dict(cur=bs(1097820, 687800, 410020, cash=110139, ppe=4441), prior=B25),
      dict(cur=isx(301439, -36565, -3000, -39565, -0.79), prior=isx(288317, -8452, -3466, -11918, -0.24)),
      {}, bs_prior_end="2025-12-31"),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    d["unit"] = "SAR full riyals" if d["sha256_prefix"] == "108aea03" else "SAR thousands"
    if not d.get("cf"):
        d.pop("cf")
rolls = [
    dict(name="2026 H1 net loss = Q1 2026 + Q2 2026", total=["e663a175", "is", "cur", "net_income"], parts=[["39ad317e", "is", "cur", "net_income"], ["e663a175", "is_q", "cur", "net_income"]]),
    dict(name="2026 H1 insurance revenue = Q1 + Q2", total=["e663a175", "is", "cur", "revenue"], parts=[["39ad317e", "is", "cur", "revenue"], ["e663a175", "is_q", "cur", "revenue"]]),
    dict(name="2026 H1 pre-zakat loss = Q1 + Q2", total=["e663a175", "is", "cur", "pbt"], parts=[["39ad317e", "is", "cur", "pbt"], ["e663a175", "is_q", "cur", "pbt"]]),
    dict(name="2025 H1 net loss = Q1 2025 (Q1 2026 filing prior) + Q2 2025", total=["e663a175", "is", "prior", "net_income"], parts=[["39ad317e", "is", "prior", "net_income"], ["e663a175", "is_q", "prior", "net_income"]]),
    dict(name="2025 H1 insurance revenue = Q1 2025 + Q2 2025", total=["e663a175", "is", "prior", "revenue"], parts=[["39ad317e", "is", "prior", "revenue"], ["e663a175", "is_q", "prior", "revenue"]]),
]
if __name__ == "__main__":
    write("8170", "AL-ETIHAD COOPERATIVE INSURANCE COMPANY", "SAR", "SAR thousands as printed, except the FY2022-as-issued filing in full SAR", docs, rolls)
