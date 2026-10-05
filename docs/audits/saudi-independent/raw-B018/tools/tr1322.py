"""Transcripts/1322.json: Al Masane Al Kobra Mining Company (AMAK) page transcriptions. Amounts are full Saudi riyals as printed.
tax = zakat + income tax + severance fees (severance fees are printed between profit before zakat, income tax and severance fees and net profit)."""
from tcommon import bs, cf, write


def isx(rev, cost, gp, op, pbt, zk, tx, sev, ni, eps=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=zk + tx + sev, zakat=zk, income_tax=tx, severance_fees=sev,
             net_income=ni, ni_parent=ni, ni_nci=0, **k)
    if eps is not None:
        d["eps_basic"] = eps
    return d


SEV = ("severance fees (a levy on mining revenue) are presented as a separate line below 'profit before zakat, income tax and severance fees' from the FY2024 filing; "
       "the FY2023 and FY2022 filings as issued deduct them inside direct costs; FY2023 as issued: direct costs 371,999,011 and profit before zakat and income tax 60,456,930, "
       "restated in the FY2024 filing (Note 35): direct costs 364,454,879, profit before severance fees 68,001,062, severance fees 7,544,132; net profit 54,582,956 unchanged")
S9M = "9M and H1 2024 comparatives marked restated (Note 18) in the 2025 interim filings (severance fees reclassified); their own 2024 interim filings are not in the value-read set"
H1R = "printed one-riyal differences between the H1 2025 original filing and the H1 2026 comparative column (cash from operations 161,063,297 versus 161,063,296; net cash from operations 112,313,177 versus 112,313,176)"

docs = [
    dict(sha256_prefix="65d75123", label="3M and 6M ended 2026-06-30 interim (label 2026|H1 correct); latest period in the collection; byte-different duplicate 9b555f86 has identical text on all 26 pages", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual plus text layer: pdf p4 BS (printed 2), p5 IS (3; 3M and 6M), p7 CF (5)", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1752537567, 331695043, 1420842524, 11770271, 745255892), prior=bs(1548195235, 222563771, 1325631464, 14547517, 682846641)),
         **{"is": dict(cur=isx(455375691, -302004582, 153371109, 116457901, 113024018, -2693306, -4479619, -11089257, 94761836, 1.07),
                       prior=isx(478335686, -283955565, 194380121, 159133192, 157283277, -3563514, -5530089, -19902404, 128287270, 1.45)),
            "is_q": dict(cur=isx(236966964, -171401006, 65565958, 44313754, 42398532, -1467036, -2798326, -3475382, 34657788, 0.39),
                         prior=isx(258563288, -148137630, 110425658, 91018151, 90060341, -2137763, -2891431, -11983526, 73047621, 0.82))},
         cf=dict(cur=cf(31923567, -132550813, 97850000, -2777246, 14547517, 11770271),
                 prior=cf(112313176, -71897987, -44300586, -3885396, 14015883, 10130487, sum_rounding=1,
                          sum_rounding_reason="printed operating 112,313,176 - investing 71,897,987 - financing 44,300,586 = -3,885,397 but the filing prints net decrease -3,885,396 (the H1 2025 original prints operating 112,313,177 and ties exactly)",
                          _declared_diff={"cfo": H1R}))),
    dict(sha256_prefix="1bc66fa2", label="3M ended 2026-03-31 interim (label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3), p7 CF (5)", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1639762241, 253604109, 1386158132, 14304672, 748863570), prior=bs(1548195235, 222563771, 1325631464, 14547517, 682846641)),
         **{"is": dict(cur=isx(218408727, -130603576, 87805151, 72144147, 70625486, -1226270, -1681293, -7613875, 60104048, 0.68),
                       prior=isx(219772398, -135817934, 83954464, 68115042, 67222937, -1425751, -2638657, -7918878, 55239651, 0.62))},
         cf=dict(cur=cf(43984894, -64227739, 20000000, -242845, 14547517, 14304672), prior=cf(140883275, -38236941, -114706848, -12060514, 14015883, 1955369))),
    dict(sha256_prefix="6646c89e", label="FY ended 2025-12-31 audited FS (label 2026|FY = publication year)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="text layer: pdf p7 BS (printed 5), p8 IS (6), p10 CF (8)", pages=dict(bs=7, is_=8, cf=10),
         bs=dict(cur=bs(1548195235, 222563771, 1325631464, 14547517, 682846641), prior=bs(1499099462, 246969121, 1252130341, 14015883, 741554652)),
         **{"is": dict(cur=isx(1026083423, -590656264, 435427159, 367483577, 360176905, -3015260, -11590102, -64973560, 280597983, 3.17),
                       prior=isx(780648910, -492319476, 288329434, 222353400, 217622936, -7575961, -3614542, -28533687, 177898746, 2.01))},
         cf=dict(cur=cf(469947428, -226606224, -242809570, 531634, 14015883, 14547517), prior=cf(316603936, -215185494, -198342580, -96924138, 110940021, 14015883))),
    dict(sha256_prefix="2a555f18", label="3M and 9M ended 2025-09-30 interim (label 2025|9M correct)", period_end="2025-09-30", prior_end="2024-09-30", bs_prior_end="2024-12-31", period_type="9M",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3; 3M and 9M), p7 CF (5, nine months); pdf p4-7 have no text layer", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1564556242, 309447155, 1255109087, 57340257, 700342623), prior=bs(1499099462, 246969121, 1252130341, 14015883, 741554652)),
         **{"is": dict(cur=isx(749392665, -433251796, 316140869, 263991366, 260323477, -3931990, -8976131, -37758350, 209657006, 2.37),
                       prior=isx(553769936, -341623321, 212146615, 163071093, 159184094, -6038160, -1964441, -14485317, 136696176, 1.55, restated=True)),
            "is_q": dict(cur=isx(271056979, -149296231, 121760748, 104858174, 103040200, -368476, -3446042, -17855946, 81369736, 0.92),
                         prior=isx(215957769, -126269558, 89688211, 74952630, 73317392, -2340577, -2390401, -8833877, 59752537, 0.68, restated=True))},
         cf=dict(cur=cf(306804765, -138371524, -125108867, 43324374, 14015883, 57340257), prior=cf(221505622, -185466802, -123238701, -87199881, 110940021, 23740140, restated=True))),
    dict(sha256_prefix="27bb4851", label="3M and 6M ended 2025-06-30 interim (label 2025|H1 correct)", period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3; 3M and 6M), p7 CF (5, six months); text layer partly empty", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1571679227, 287329813, 1284349414, 10130487, 698650838), prior=bs(1499099462, 246969121, 1252130341, 14015883, 741554652)),
         **{"is": dict(cur=isx(478335686, -283955565, 194380121, 159133192, 157283277, -3563514, -5530089, -19902404, 128287270, 1.45),
                       prior=isx(337812167, -215353763, 122458404, 88118463, 85866701, -3697583, 425960, -5651440, 76943638, 0.87, restated=True)),
            "is_q": dict(cur=isx(258563288, -148137630, 110425658, 91018151, 90060341, -2137763, -2891431, -11983526, 73047621, 0.82),
                         prior=isx(203312649, -115866231, 87446418, 70250932, 68549509, -2084328, 1005020, -5651440, 61818761, 0.70, restated=True))},
         cf=dict(cur=cf(112313177, -71897987, -44300586, -3885396, 14015883, 10130487), prior=cf(103759381, -140369853, -56522646, -93133118, 110940021, 17806903, restated=True))),
    dict(sha256_prefix="8070bf28", label="FY ended 2024-12-31 audited FS (label 2025|FY = publication year); 2023 comparative restated (Note 35)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 5), p8 IS (6), p10 CF (8); pdf p3, 5-10 have no text layer", pages=dict(bs=7, is_=8, cf=10),
         bs=dict(cur=bs(1499099462, 246969121, 1252130341, 14015883, 741554652), prior=bs(1454213834, 233983794, 1220230040, 110940021, 373911992)),
         **{"is": dict(cur=isx(780648910, -492319476, 288329434, 222353400, 217622936, -7575961, -3614542, -28533687, 177898746, 2.01),
                       prior=isx(487894683, -364454879, 123439804, 64010622, 68001062, -2314785, -3559189, -7544132, 54582956, 0.73, restated=True))},
         cf=dict(cur=cf(316603936, -215185494, -198342580, -96924138, 110940021, 14015883), prior=cf(291184903, -398406228, -163230562, -270451887, 381391908, 110940021, restated=True))),
    dict(sha256_prefix="3ca65fbb", label="FY ended 2023-12-31 audited FS as issued (label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 5), p8 IS (6), p10 CF (8); pdf p3, 5-10 have no text layer", pages=dict(bs=7, is_=8, cf=10),
         bs=dict(cur=bs(1454213834, 233983794, 1220230040, 110940021, 373911992), prior=bs(1547870546, 327673357, 1220197189, 381391908, 395950754)),
         **{"is": dict(cur=dict(revenue=487894683, cost_of_revenue=-371999011, gross_profit=115895672, operating_income=56466490, pbt=60456930, tax=-5873974, zakat=-2314785, income_tax=-3559189,
                                net_income=54582956, ni_parent=54582956, ni_nci=0, eps_basic=0.73,
                                _declared_diff={k: SEV for k in ("cost_of_revenue", "gross_profit", "operating_income", "pbt")}),
                       prior=isx(582768703, -374408470, 208360233, 143946711, 142609575, -11381929, -4896500, 0, 126331146, 2.02))},
         cf=dict(cur=cf(291184903, -398406228, -163230562, -270451887, 381391908, 110940021), prior=cf(139899376, -146017203, 312790097, 306672270, 74719638, 381391908))),
    dict(sha256_prefix="36790b12", label="FY ended 2022-12-31 audited FS as issued (label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 5), p8 IS (6), p10 CF (8); pdf p6-10 have no text layer", pages=dict(bs=7, is_=8, cf=10),
         bs=dict(cur=bs(1547870546, 327673357, 1220197189, 381391908, 395950754), prior=bs(1112261198, 463825120, 648436078, 74719638, 426891258)),
         **{"is": dict(cur=isx(582768703, -374408470, 208360233, 143946711, 142609575, -11381929, -4896500, 0, 126331146, 2.02),
                       prior=isx(586653318, -318955821, 267697497, 216614416, 203132539, -8844831, 2977061, 0, 197264769, 3.60))},
         cf=dict(cur=cf(139899376, -146017203, 312790097, 306672270, 74719638, 381391908), prior=cf(178501176, -72076278, -66874878, 39550020, 35169618, 74719638))),
]
S = lambda p, blk, col, k: [p, blk, col, k]
rolls = []
for k, nm in (("revenue", "revenue"), ("pbt", "profit before zakat, income tax and severance fees"), ("tax", "zakat plus income tax plus severance fees"), ("net_income", "net profit")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {nm}", total=S("65d75123", "is", "cur", k), parts=[S("1bc66fa2", "is", "cur", k), S("65d75123", "is_q", "cur", k)]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {nm} (2025 comparatives in the 2026 filings; one to two riyal printed rounding)", total=S("65d75123", "is", "prior", k), parts=[S("1bc66fa2", "is", "prior", k), S("65d75123", "is_q", "prior", k)], tol=2))
    rolls.append(dict(name=f"2025 H1 + Q3 = 9M {nm}", total=S("2a555f18", "is", "cur", k), parts=[S("27bb4851", "is", "cur", k), S("2a555f18", "is_q", "cur", k)]))
write("1322", "AL MASANE AL KOBRA MINING COMPANY (AMAK)", docs, rolls, unit="Saudi riyals (SAR), full units as printed (not thousands)")
