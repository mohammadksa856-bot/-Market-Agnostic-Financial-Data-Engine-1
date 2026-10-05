"""Transcripts/8150.json: ACIG (Allied Cooperative Insurance Group) page transcriptions (SAR thousands as printed)."""
from tcommon import bs, cf, inc, write

PRES = "presentation change: share of surplus from insurance pools (4,052 in FY2024) moved from other income into the insurance service result in the FY2025 filing; result before zakat unchanged"
CFR = "cash-flow re-presentation between FY2024 filing and FY2025 comparative: operating 400/401 lower and investing 401 lower (commission/other investment income lines); net change and closing cash identical"
RND = "FY2023 filing prints operating 139,651, investing -480,540, financing -1,806, net -342,695 and closing cash 141,636 against the FY2024 comparative 139,650, -480,543, -1,805, -342,698, 141,633; the as-issued closing cash 141,636 also differs from its own balance sheet cash 141,633"
Q1CF = "the Q1 2025 comparative cash-flow column printed in the Q1 2026 filing does not equal the Q1 2025 original: it carries the full-year 2024 investing and financing figures (575,514 and -5,379) and closing cash 674,858 against the original 23,630"
R22 = "IFRS 4 as issued (68cf632f) versus IFRS 17 restated comparative in the FY2023 filing (2ff65236)"

docs = [
    dict(sha256_prefix="3933b6d2", label="FY2025 audited FS (label 2026|FY = publication year; PDF metadata title 'ACIG FS - Draft 2025 - 28032026.xlsx')", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 6), p9 IS (7), p12 CF (10); pdf p3-9, 11-12 textless",
         pages=dict(bs=8, is_=9, cf=12),
         bs=dict(cur=bs(994738, 772538, 222200, 350661, 6928), prior=bs(894529, 641378, 253151, 654668, 3544)),
         **{"is": dict(cur=inc(993236, -41600, 410, -41190, eps_basic=-1.42, insurance_service_result=-30412, _extra_keys=["insurance_service_result"]),
                       prior=inc(883353, -9383, -7100, -16483, eps_basic=-0.57, insurance_service_result=-22745, _extra_keys=["insurance_service_result"],
                                 _declared_diff={"insurance_service_result": PRES}))},
         cf=dict(cur=cf(99708, -400233, -3482, -304007, 654668, 350661),
                 prior=cf(-57100, 575514, -5379, 513035, 141633, 654668, _declared_diff={"cfo": CFR, "cfi": CFR}))),
    dict(sha256_prefix="dfb54378", label="FY2024 audited FS (label 2025|FY = publication year); Dec 2023 and 1 Jan 2023 restated", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p9 BS (printed 7), p10 IS (8), p13 CF (11); pdf p3-13 textless",
         pages=dict(bs=9, is_=10, cf=13),
         bs=dict(cur=bs(894529, 641378, 253151, 654668, 3544),
                 prior=bs(897720, 643377, 254343, 141633, 3376, restated=True)),
         **{"is": dict(cur=inc(883353, -9383, -7100, -16483, eps_basic=-0.57, insurance_service_result=-26797, _extra_keys=["insurance_service_result"]),
                       prior=inc(974681, 72206, -8800, 63406, eps_basic=2.18))},
         cf=dict(cur=cf(-57501, 575915, -5379, 513035, 141633, 654668), prior=cf(139650, -480543, -1805, -342698, 484331, 141633))),
    dict(sha256_prefix="2ff65236", label="FY2023 audited FS as issued, first IFRS 17 year, Dec 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p9 BS (printed 7), p10 IS (8), p13 CF (11); pdf p3-13 textless",
         pages=dict(bs=9, is_=10, cf=13),
         bs=dict(cur=bs(929554, 675211, 254343, 141633, 3376), prior=bs(762789, 573842, 188947, 484331, 4596, restated=True)),
         **{"is": dict(cur=inc(974681, 72206, -8800, 63406, eps_basic=2.18), prior=inc(672811, -24776, 7432, -17344, eps_basic=-0.82, restated=True))},
         cf=dict(cur=cf(139651, -480540, -1806, -342695, 484331, 141636, _declared_diff={"cfo": RND, "cfi": RND, "cff": RND, "net_change": RND, "cash_end": RND}),
                 prior=cf(111410, 176590, 143397, 431397, 52934, 484331, restated=True))),
    dict(sha256_prefix="68cf632f", label="FY2022 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p8 BS assets (printed 6), p9 BS liabilities and equity (7), p10 IS (8), p13 CF (11); pdf p3-13 textless",
         pages=dict(bs="8-9", is_=10, cf=13),
         bs=dict(cur=bs(904738, 742427, 162311, 484418, 4596), prior=bs(593255, 561219, 32036, 52973, 5411)),
         **{"is": dict(cur=dict(pbt=-20732, tax=7432, net_income=-13300, ni_parent=-13300, ni_nci=0, eps_basic=-0.47, gross_premiums_written=830694, net_revenues_ifrs4=598781),
                       prior=dict(pbt=-104008, tax=-10576, net_income=-114584, ni_parent=-114584, ni_nci=0, eps_basic=-6.07, gross_premiums_written=592588, net_revenues_ifrs4=489075))},
         cf=dict(cur=cf(123092, 164956, 143397, 431445, 52973, 484418), prior=cf(-23041, -66789, -2134, -91964, 144937, 52973))),
    dict(sha256_prefix="1d3df0b6", label="3M and 6M ended 2026-06-30 interim (label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3; columns 3M 2026, 3M 2025, 6M 2026, 6M 2025), p8 CF (6, six months); pdf p3-8 textless",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(865804, 647761, 218043, 177935, 6126), prior=bs(994738, 772538, 222200, 350661, 6928)),
         **{"is": dict(cur=inc(655973, -3361, -796, -4157, eps_basic=-0.14), prior=inc(410227, 16863, -1748, 15115, eps_basic=0.52)),
            "is_q": dict(cur=inc(339383, 13681, -166, 13515, eps_basic=0.46), prior=inc(222439, 2021, -684, 1337, eps_basic=0.05))},
         cf=dict(cur=cf(-178281, 7355, -1801, -172727, 350661, 177935, rounding=1, rounding_reason="printed opening 350,661 plus printed net change -172,727 is 177,934; the filing prints closing cash 177,935 (equal to the balance sheet), a 1 thousand rounding inconsistency in the source"), prior=cf(15808, -268591, -1802, -254585, 654668, 400083))),
    dict(sha256_prefix="0295b4ee", label="3M ended 2026-03-31 interim (label 2026|Q1 correct; inventory class other_no_statements_found although full statements are present)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p5 BS (printed 3), p6 IS (4), p9 CF (7); statement pages have no text layer",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(946670, 742142, 204528, 293329, 6562), prior=bs(994738, 772538, 222200, 350661, 6928)),
         **{"is": dict(cur=inc(316590, -17042, -630, -17672, eps_basic=-0.61), prior=inc(187788, 15010, -1064, 13946, eps_basic=0.48))},
         cf=dict(cur=cf(-59454, 3923, -1801, -57332, 350661, 293329),
                 prior=cf(-36910, 575514, -5379, 533225, 141633, 674858, _declared_diff={"cfo": Q1CF, "cfi": Q1CF, "cff": Q1CF, "net_change": Q1CF, "cash_end": Q1CF}))),
    dict(sha256_prefix="05567ee8", label="3M and 9M ended 2025-09-30 interim (label 2025|9M correct)", period_end="2025-09-30", prior_end="2024-09-30", bs_prior_end="2024-12-31", period_type="9M",
         reading="visual: pdf p5 BS (printed 3), p6 IS (4; 3M and 9M), p9 CF (7, nine months); pdf p3-9 textless",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(1067885, 854718, 213167, 386719, 7527), prior=bs(894529, 641378, 253151, 654668, 3544)),
         **{"is": dict(cur=inc(654226, -39929, -2564, -42493, eps_basic=-1.46), prior=inc(698979, 34417, -3600, 30817, eps_basic=1.06)),
            "is_q": dict(cur=inc(243999, -56792, -816, -57608, eps_basic=-1.98), prior=inc(251842, -72, 3000, 2928, eps_basic=0.10))},
         cf=dict(cur=cf(142861, -407328, -3482, -267949, 654668, 386719), prior=cf(-4850, 1307, -3482, -7025, 141633, 134608))),
    dict(sha256_prefix="896ce8df", label="3M and 6M ended 2025-06-30 interim (label 2025|H1 correct; inventory class other_no_statements_found although full statements are present)", period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
         reading="visual: pdf p5 BS (printed 3), p6 IS (4; 3M and 6M), p9 CF (7, six months); pdf p3-9 textless",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(918789, 648014, 270775, 400083, 5591), prior=bs(894529, 641378, 253151, 654668, 3544)),
         **{"is": dict(cur=inc(410227, 16863, -1748, 15115, eps_basic=0.52), prior=inc(447137, 34487, -6600, 27887, eps_basic=0.96)),
            "is_q": dict(cur=inc(222439, 2021, -684, 1337, eps_basic=0.05), prior=inc(215718, 7890, -5000, 2890, eps_basic=0.10))},
         cf=dict(cur=cf(15808, -268591, -1802, -254585, 654668, 400083), prior=cf(-7273, -36363, -1801, -45437, 141633, 96196))),
    dict(sha256_prefix="a215c221", label="3M ended 2025-03-31 interim (label 2025|Q1 correct)", period_end="2025-03-31", prior_end="2024-03-31", bs_prior_end="2024-12-31", period_type="Q1",
         reading="visual: pdf p5 BS (printed 3), p6 IS (4), p9 CF (7); pdf p3-9 textless",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(867814, 598376, 269438, 23630, 4375), prior=bs(894529, 641378, 253151, 654668, 3544)),
         **{"is": dict(cur=inc(187788, 15010, -1064, 13946, eps_basic=0.48), prior=inc(231419, 26594, -1600, 24994, eps_basic=0.86))},
         cf=dict(cur=cf(-31534, -597534, -1970, -631038, 654668, 23630), prior=cf(-60056, 8396, -3482, -55142, 141633, 86491))),
]
S = lambda p, blk, col, k: [p, blk, col, k]
rolls = []
for k, nm in (("revenue", "revenue"), ("pbt", "result before zakat"), ("tax", "zakat"), ("net_income", "net result")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {nm}", total=S("1d3df0b6", "is", "cur", k), parts=[S("0295b4ee", "is", "cur", k), S("1d3df0b6", "is_q", "cur", k)]))
    rolls.append(dict(name=f"2025 H1 + Q3 = 9M {nm}", total=S("05567ee8", "is", "cur", k), parts=[S("896ce8df", "is", "cur", k), S("05567ee8", "is_q", "cur", k)]))
    r = dict(name=f"2025 Q1 + Q2 = H1 {nm} (source filings)", total=S("896ce8df", "is", "cur", k), parts=[S("a215c221", "is", "cur", k), S("896ce8df", "is_q", "cur", k)])
    if k in ("pbt", "net_income"):
        r["expected_diff"] = -168
        r["reason"] = "Q1 2025 original prints result before zakat 15,010 and Q2 (3M) 2,021 in the H1 2025 filing, but the six-month figure there is 16,863; the original filings themselves differ by 168"
    rolls.append(r)
write("8150", "ALLIED COOPERATIVE INSURANCE GROUP (ACIG)", docs, rolls)
