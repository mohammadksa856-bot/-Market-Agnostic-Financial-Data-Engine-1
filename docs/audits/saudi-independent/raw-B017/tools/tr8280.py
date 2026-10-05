"""Transcripts/8280.json: Liva Insurance Company (formerly Al Alamiya for Cooperative Insurance) page transcriptions (SAR thousands as printed)."""
from tcommon import bs, cf, inc, write

R22 = "IFRS 4 as issued (8e205eda, Al Alamiya) versus IFRS 17 restated 2022 comparative in the FY2023 filing (c79efac6): total assets 913,730 versus 790,444, equity 314,019 versus 333,423, net result -48,775 versus -42,945, CFO 37,459 versus 41,993, CFI -41,308 versus -45,842"
R23 = "FY2023 cash flow as first issued (c79efac6) versus comparative re-presented in the FY2024 filing (b374e6d4, note 25): CFO 12,930 versus 1,003, CFI 54,781 versus 66,708 (zakat, interest and investment lines reclassified); net change 67,711 and closing cash 104,454 unchanged"
docs = [
    dict(sha256_prefix="0d5ddad6", label="FY2025 audited FS (label 2026|FY = publication year; inventory scanned_unreadable, entire file image-only)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual: pdf p9 BS (printed 8), p10 IS (9), p13 CF (12)",
         pages=dict(bs=9, is_=10, cf=13),
         bs=dict(cur=bs(1056991, 578313, 478678, 59395, 2446), prior=bs(1019046, 578495, 440551, 85512, 1114)),
         **{"is": dict(cur=inc(575028, 30732, -4092, 26640, eps_basic=0.67), prior=inc(446127, 33478, -717, 32761, eps_basic=0.82))},
         cf=dict(cur=cf(66247, -92414, 0, -26167, 84839, 58672), prior=cf(38881, -58496, 0, -19615, 104454, 84839))),
    dict(sha256_prefix="b374e6d4", label="FY2024 audited FS, 2023 and 1 Jan 2023 restated (label 2025|FY = publication year); text layer clean, income page also read as image", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="text rows plus image of pdf p10: pdf p9 BS, p10 IS, p13 CF",
         pages=dict(bs=9, is_=10, cf=13),
         bs=dict(cur=bs(1019046, 578495, 440551, 85512, 1114), prior=bs(838685, 448693, 389992, 105128, 1460, restated=True)),
         **{"is": dict(cur=inc(446127, 33478, -717, 32761, eps_basic=0.82), prior=inc(513629, 17427, -6169, 11258, eps_basic=0.28, restated=True))},
         cf=dict(cur=cf(38881, -58496, 0, -19615, 104454, 84839), prior=cf(1003, 66708, 0, 67711, 36743, 104454, restated=True))),
    dict(sha256_prefix="c79efac6", label="FY2023 audited FS as first issued, first IFRS 17 year, 2022 and 1 Jan 2022 restated (label 2024|FY = publication year); entity renamed Liva, formerly Al Alamiya", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed page 5), p8 IS (6), p11 CF (9)",
         pages=dict(bs=7, is_=8, cf=11),
         bs=dict(cur=bs(838685, 448693, 389992, 105128, 1460), prior=bs(790444, 457021, 333423, 37443, 1550, restated=True)),
         **{"is": dict(cur=inc(513629, 17427, -6169, 11258, eps_basic=0.28), prior=inc(337947, -37240, -5705, -42945, eps_basic=-1.07, restated=True))},
         cf=dict(cur=cf(12930, 54781, 0, 67711, 36743, 104454, _declared_diff={"cfo": R23, "cfi": R23}), prior=cf(41993, -45842, 0, -3849, 40592, 36743, restated=True))),
    dict(sha256_prefix="8e205eda", label="FY2022 audited FS as issued under IFRS 4, issuer name Al Alamiya for Cooperative Insurance Company (label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="text layer rows: pdf p8-9 BS, p10-11 IS, p13 CF (identities tie; premium, claims and other detail lines not transcribed)",
         pages=dict(bs="8-9", is_="10-11", cf=13),
         bs=dict(cur=bs(913730, 599711, 314019, 37443, 1550, _declared_diff={"total_assets": R22, "total_liabilities": R22, "total_equity": R22}), prior=bs(847613, 480782, 366831, 41292, 1695)),
         **{"is": dict(cur=dict(pbt=-43070, tax=-5705, net_income=-48775, ni_parent=-48775, ni_nci=0, total_revenues_ifrs4=227043, _declared_diff={"pbt": R22, "tax": R22, "net_income": R22, "ni_parent": R22}),
                       prior=dict(pbt=-27663, tax=-7714, net_income=-35377, ni_parent=-35377, ni_nci=0, total_revenues_ifrs4=109881))},
         cf=dict(cur=cf(37459, -41308, 0, -3849, 40592, 36743, _declared_diff={"cfo": R22, "cfi": R22}), prior=cf(43129, -24893, 0, 18236, 22356, 40592))),
    dict(sha256_prefix="f998e711", label="3M and 6M ended 2026-06-30 unaudited interim (inventory scanned_unreadable, whole file image-only; label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3; columns 3M 2026, 3M 2025, 6M 2026, 6M 2025), p8 CF (6; six-month only)",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(1179495, 684330, 495165, 40596, 2193), prior=bs(1056991, 578313, 478678, 59395, 2446)),
         **{"is": dict(cur=inc(411315, 19087, -2600, 16487, eps_basic=0.41), prior=inc(261368, 6510, -1253, 5257, eps_basic=0.13)),
            "is_q": dict(cur=inc(228260, 10856, -1600, 9256, eps_basic=0.23), prior=inc(136232, 3627, -212, 3415, eps_basic=0.09))},
         cf=dict(cur=cf(89748, -108553, 0, -18805, 58672, 39867), prior=cf(-64103, 25394, 0, -38709, 84839, 46130))),
    dict(sha256_prefix="8b8d8e7a", label="3M ended 2026-03-31 unaudited interim (label 2026|Q1 correct); text layer clean", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="text rows: pdf p4 BS, p5 IS, p8 CF (cash-flow page order scrambled in the text layer but values tie)",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(1137872, 651963, 485909, 61963, 2978), prior=bs(1056991, 578313, 478678, 59395, 2446)),
         **{"is": dict(cur=inc(183055, 8231, -1000, 7231, eps_basic=0.18), prior=inc(125136, 2883, -1041, 1842, eps_basic=0.05))},
         cf=dict(cur=cf(56581, -54008, 0, 2573, 58672, 61245), prior=cf(-19437, -16773, 0, -36210, 84839, 48629))),
]
H, Q = "f998e711", "8b8d8e7a"
rolls = []
for k, name in (("revenue", "insurance revenue"), ("pbt", "profit before zakat"), ("tax", "zakat"), ("net_income", "net profit")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {name}", total=[H, "is", "cur", k], parts=[[Q, "is", "cur", k], [H, "is_q", "cur", k]]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {name}", total=[H, "is", "prior", k], parts=[[Q, "is", "prior", k], [H, "is_q", "prior", k]]))
write("8280", "LIVA INSURANCE COMPANY (formerly AL ALAMIYA FOR COOPERATIVE INSURANCE COMPANY)", docs, rolls)
