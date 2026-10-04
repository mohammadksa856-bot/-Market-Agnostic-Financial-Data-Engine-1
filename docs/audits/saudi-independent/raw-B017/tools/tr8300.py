"""Transcripts/8300.json: Wataniya Insurance Company page transcriptions (SAR thousands as printed)."""
from tcommon import bs, cf, inc, write

R22 = "IFRS 4 as issued (c0492e7e) versus IFRS 17 restated comparative in the FY2023 filing (5d5ba5ed): measurement basis changed (premium-based to insurance-revenue-based, reinsurance and insurance contract grossing)"
docs = [
    dict(sha256_prefix="b8fd2d1c", label="FY2025 audited FS (label 2026|FY = publication year)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 7), p8 IS (8), p12 CF (12); pdf p7-12 textless",
         pages=dict(bs=7, is_=8, cf=12),
         bs=dict(cur=bs(2043961, 1385974, 657987, 102074, 9056), prior=bs(2134822, 1525188, 609634, 53693, 12877)),
         **{"is": dict(cur=inc(1837593, 49490, -12400, 37090, eps_basic=0.93), prior=inc(1796142, 116783, -13733, 103050, eps_basic=2.58))},
         cf=dict(cur=cf(-65851, 116322, -2090, 48381, 53693, 102074), prior=cf(249035, -217026, -1046, 30963, 22730, 53693))),
    dict(sha256_prefix="b23739e4", label="FY2024 audited FS (label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p7 BS, p8 IS, p12 CF; pdf p7-12 textless",
         pages=dict(bs=7, is_=8, cf=12),
         bs=dict(cur=bs(2134822, 1525188, 609634, 53693, 12877), prior=bs(1864246, 1375968, 488278, 22730, 11565)),
         **{"is": dict(cur=inc(1796142, 116783, -13733, 103050, eps_basic=2.58), prior=inc(1378636, 96493, -11912, 84581, eps_basic=2.11))},
         cf=dict(cur=cf(249035, -217026, -1046, 30963, 22730, 53693), prior=cf(397089, -445211, 0, -48122, 70852, 22730))),
    dict(sha256_prefix="5d5ba5ed", label="FY2023 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 8), p9 IS (9), p13 CF (13); pdf p8-13 textless",
         pages=dict(bs=8, is_=9, cf=13),
         bs=dict(cur=bs(1864246, 1375968, 488278, 22730, 11565), prior=bs(1333966, 933928, 400038, 70852, 17318, restated=True)),
         **{"is": dict(cur=inc(1378636, 96493, -11912, 84581, eps_basic=2.11), prior=inc(835084, -21171, -6491, -27662, eps_basic=-0.74, restated=True))},
         cf=dict(cur=cf(397089, -445211, 0, -48122, 70852, 22730), prior=cf(57318, -216998, 188406, 28726, 42126, 70852, restated=True))),
    dict(sha256_prefix="c0492e7e", label="FY2022 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p7 BS, p8 IS, p11-12 CF; pdf p7-12 textless",
         pages=dict(bs=7, is_=8, cf="11-12"),
         bs=dict(cur=bs(1916140, 1535681, 380459, 70856, 17318, _declared_diff={"total_assets": R22, "total_liabilities": R22, "total_equity": R22, "cash": "cash 70,856 as issued versus 70,852 restated (4 thousand difference carried to opening cash 42,130 versus 42,126; cause not stated on pages read)"}),
                 prior=bs(1347237, 1136042, 211195, 42130, 17403)),
         **{"is": dict(cur=dict(pbt=-11853, tax=-6491, net_income=-18344, ni_parent=-18344, ni_nci=0, eps_basic=-0.49, total_revenues_ifrs4=557772, _declared_diff={"pbt": R22, "net_income": R22, "ni_parent": R22}),
                       prior=dict(pbt=-50474, tax=-4002, net_income=-54476, ni_parent=-54476, ni_nci=0, eps_basic=-1.80, total_revenues_ifrs4=553167))},
         cf=dict(cur=cf(62175, -221855, 188406, 28726, 42130, 70856, _declared_diff={"cfo": R22, "cfi": R22, "cash_end": R22}), prior=cf(-63984, 25381, 0, -38603, 80733, 42130))),
    dict(sha256_prefix="b538bac9", label="3M and 6M ended 2026-06-30 reviewed interim (label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p4 BS, p5 IS (columns: 3M 2026, 3M 2025, 6M 2026, 6M 2025), p8 CF (6M); pdf p4-8 textless",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(2431939, 1765516, 666423, 294607, 11474), prior=bs(2043961, 1385974, 657987, 102074, 9056)),
         **{"is": dict(cur=inc(1342569, 15126, -6000, 9126, eps_basic=0.23), prior=inc(903086, 13684, -7000, 6684, eps_basic=0.17)),
            "is_q": dict(cur=inc(707289, 23084, -3750, 19334, eps_basic=0.48), prior=inc(450919, 3946, -3500, 446, eps_basic=0.01))},
         cf=dict(cur=cf(340628, -143313, -4782, 192533, 102074, 294607), prior=cf(-55188, 46120, -1045, -10113, 53693, 43580))),
    dict(sha256_prefix="3c17b8d5", label="3M ended 2026-03-31 reviewed interim (label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p4 BS, p5 IS, p8 CF; pdf p4-8 textless",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(2332360, 1684427, 647933, 184228, 11174), prior=bs(2043961, 1385974, 657987, 102074, 9056)),
         **{"is": dict(cur=inc(635280, -7958, -2250, -10208, eps_basic=-0.25), prior=inc(452167, 9738, -3500, 6238, eps_basic=0.16))},
         cf=dict(cur=cf(252162, -166271, -3737, 82154, 102074, 184228), prior=cf(5598, 174871, 0, 180469, 53693, 234162))),
]
H, Q = "b538bac9", "3c17b8d5"
rolls = []
for k, name in (("revenue", "revenue"), ("pbt", "loss before zakat and tax"), ("tax", "zakat and income tax"), ("net_income", "net result")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {name}", total=[H, "is", "cur", k], parts=[[Q, "is", "cur", k], [H, "is_q", "cur", k]]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {name}", total=[H, "is", "prior", k], parts=[[Q, "is", "prior", k], [H, "is_q", "prior", k]]))
write("8300", "WATANIYA INSURANCE COMPANY", docs, rolls)
