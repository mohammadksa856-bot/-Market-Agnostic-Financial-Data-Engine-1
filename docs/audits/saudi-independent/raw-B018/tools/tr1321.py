"""Transcripts/1321.json: East Pipes Integrated Company for Industry page transcriptions. Fiscal year ends 31 March. Amounts are full Saudi riyals as printed."""
from tcommon import bs, cf, write


def isx(rev, cost, gp, op, pbt, zk, tx, ni, eps=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=zk + tx, zakat=zk, income_tax=tx, net_income=ni, ni_parent=ni, ni_nci=0, **k)
    if eps is not None:
        d["eps_basic"] = eps
    return d


BSR = ("31 March 2025 balance sheet: 1,632,108,105 total assets as audited in the FY2025 filing (285c64ee) versus 1,638,543,651 as re-presented in the FY2026 filing (c032fedd); "
       "advance for income tax 17,316,312 versus 23,751,858 and zakat and income tax provision 31,231,436 versus 37,666,982 (gross-up of 6,435,545); equity unchanged 1,134,446,848")
Q1R = ("Q1 FY26 (3M to 30 June 2025) as first reported (a97bb7a6) versus as re-presented in the Q1 FY27 filing (881ec696): other operating income 5,930,040 versus 5,648,497 and "
       "finance income 281,543 shown separately, so operating profit 104,581,273 versus 98,651,233; profit before zakat and net profit unchanged")
Q1CFR = "Q1 FY26 operating cash flow before working capital 103,638,222 as first reported versus 103,356,679 re-presented (finance income moved); net operating, investing, financing and closing cash unchanged"

docs = [
    dict(sha256_prefix="881ec696", label="3M ended 2026-06-30 interim = fiscal Q1 of FY ending 31 March 2027 (collector label 2026|Q1 is calendar-style; a 2027|Q1 results announcement also exists)", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2026-03-31", period_type="Q1 FY27",
         reading="text layer plus visual: pdf p4 IS (printed 2), p5 BS (3), p7 CF (5)", pages=dict(bs=5, is_=4, cf=7),
         bs=dict(cur=bs(1983528288, 420538661, 1562989627, 797894357, 249535408), prior=bs(1969890077, 406062778, 1563827299, 680946579, 247061434)),
         **{"is": dict(cur=isx(520665521, -383943194, 136722327, 129434284, 137165977, -6990364, -7258573, 122917040, 3.90),
                       prior=isx(385192515, -279933071, 105259444, 98651233, 101250244, -5130892, -5852002, 90267350, 2.87,
                                 _declared_diff={"operating_income": Q1R}))},
         cf=dict(cur=cf(255306555, -7347878, -131010899, 116947778, 680946579, 797894357), prior=cf(250226921, -1835467, -39503952, 208887502, 7950222, 216837724))),
    dict(sha256_prefix="c032fedd", label="FY ended 2026-03-31 audited FS (label 2026|FY = fiscal year-end year; inventory class partial_statements; audit report dated 20 May 2026)", period_end="2026-03-31", prior_end="2025-03-31", period_type="FY",
         reading="text layer: pdf p9 BS (printed 7), p8 IS (6), p11 CF (9); pdf p7 (auditor report p5) image-only", pages=dict(bs=9, is_=8, cf=11),
         bs=dict(cur=bs(1969890077, 406062778, 1563827299, 680946579, 247061434),
                 prior=bs(1638543651, 504096803, 1134446848, 7950222, 220882572, _declared_diff={"total_assets": BSR, "total_liabilities": BSR})),
         **{"is": dict(cur=isx(2297739980, -1651061139, 646678841, 614554233, 620820289, -25452722, -22105284, 573262283, 18.20),
                       prior=isx(1832845313, -1372741038, 460104275, 429802207, 425285475, -17643805, -25518062, 382123608, 12.13))},
         cf=dict(cur=cf(973110362, -42427803, -257686202, 672996357, 7950222, 680946579), prior=cf(237584204, -8502846, -287132342, -58050984, 66001206, 7950222))),
    dict(sha256_prefix="6366e4d4", label="3M and 9M ended 2025-12-31 interim = fiscal Q3 of FY ending 31 March 2026 (label 2025|9M)", period_end="2025-12-31", prior_end="2024-12-31", bs_prior_end="2025-03-31", period_type="9M FY26",
         reading="visual: pdf p4 IS (printed 2), p5 BS (3), p7 CF (5, nine months); text layer garbled", pages=dict(bs=5, is_=4, cf=7),
         bs=dict(cur=bs(1805412829, 405381179, 1400031650, 396492976, 247058260), prior=bs(1632108105, 497661257, 1134446848, 7950222, 220882572)),
         **{"is": dict(cur=isx(1596797413, -1140156526, 456640887, 452331027, 444317633, -16957060, -18511558, 408849015, 12.98),
                       prior=isx(1432475697, -1076546758, 355928939, 342525846, 331069964, -14090322, -20442058, 296537584, 9.41)),
            "is_q": dict(cur=isx(640730104, -462422034, 178308070, 177686808, 175486133, -6539283, -8945778, 160001072, 5.08),
                         prior=isx(527902502, -392153698, 135748804, 128637782, 125262602, -6305185, -6513669, 112443748, 3.57))},
         cf=dict(cur=cf(650427835, -38324519, -223560560, 388542754, 7950222, 396492976, sum_rounding=-2,
                        sum_rounding_reason="printed operating 650,427,835 + investing -38,324,519 + financing -223,560,560 = 388,542,756 but the filing prints net change 388,542,754 (verified on a zoomed render); closing cash 396,492,976 equals opening plus the printed net change"),
                 prior=cf(355646760, -7722198, -210605798, 137318764, 66001206, 203319970))),
    dict(sha256_prefix="8a30cf4b", label="3M and 6M ended 2025-09-30 interim = fiscal Q2 of FY ending 31 March 2026 (label 2025|H1)", period_end="2025-09-30", prior_end="2024-09-30", bs_prior_end="2025-03-31", period_type="H1 FY26",
         reading="visual: pdf p4 IS (printed 2), p5 BS (3), p7 CF (5, six months); text layer incomplete", pages=dict(bs=5, is_=4, cf=7),
         bs=dict(cur=bs(1606070388, 302145477, 1303924911, 399023580, 220362150), prior=bs(1632108105, 497661257, 1134446848, 7950222, 220882572)),
         **{"is": dict(cur=isx(956067309, -677734492, 278332817, 274644219, 268831500, -10417777, -9565780, 248847943, 7.90),
                       prior=isx(904573195, -684393060, 220180135, 213888064, 205807362, -7785137, -13928389, 184093836, 5.84)),
            "is_q": dict(cur=isx(570874794, -397801421, 173073373, 170062946, 167581256, -5286885, -3713778, 158580593, 5.03),
                         prior=isx(540154282, -406391354, 133762928, 127099071, 122908349, -4034245, -6024969, 112849135, 3.58))},
         cf=dict(cur=cf(521102277, -7601939, -122426980, 391073358, 7950222, 399023580), prior=cf(143695289, -3583368, -161221666, -21109745, 66001206, 44891461))),
    dict(sha256_prefix="a97bb7a6", label="3M ended 2025-06-30 interim = fiscal Q1 of FY ending 31 March 2026 (label 2025|Q1)", period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2025-03-31", period_type="Q1 FY26",
         reading="visual: pdf p4 IS (printed 2), p5 BS (3), p7 CF (5); pdf p3-7 have no text layer", pages=dict(bs=5, is_=4, cf=7),
         bs=dict(cur=bs(1676472899, 451415520, 1225057379, 216837724, 218617812), prior=bs(1632108105, 497661257, 1134446848, 7950222, 220882572)),
         **{"is": dict(cur=isx(385192515, -279933071, 105259444, 104581273, 101250244, -5130892, -5852002, 90267350, 2.87,
                               _declared_diff={"operating_income": Q1R}),
                       prior=isx(364418913, -278001706, 86417207, 86788993, 82899013, -3750892, -7903420, 71244701, 2.26))},
         cf=dict(cur=cf(250226921, -1835467, -39503952, 208887502, 7950222, 216837724), prior=cf(293933255, -691866, -159606946, 133634443, 66001206, 199635649))),
    dict(sha256_prefix="285c64ee", label="FY ended 2025-03-31 audited FS (label 2025|FY = fiscal year-end year)", period_end="2025-03-31", prior_end="2024-03-31", period_type="FY",
         reading="text layer: pdf p9 BS (printed 7), p8 IS (6), p11-12 CF (9-10)", pages=dict(bs=9, is_=8, cf="11-12"),
         bs=dict(cur=bs(1632108105, 497661257, 1134446848, 7950222, 220882572), prior=bs(1486807564, 634894318, 851913246, 66001206, 233003228)),
         **{"is": dict(cur=isx(1832845313, -1372741038, 460104275, 429802207, 425285475, -17643805, -25518062, 382123608, 12.13),
                       prior=isx(1543167801, -1192608580, 350559221, 324014024, 296861222, -11791040, -17562301, 267507881, 8.49))},
         cf=dict(cur=cf(237584204, -8502846, -287132342, -58050984, 66001206, 7950222), prior=cf(10724955, -5175602, 7058252, 12607605, 53393601, 66001206))),
    dict(sha256_prefix="038edf7d", label="FY ended 2024-03-31 audited FS (label 2024|FY = fiscal year-end year)", period_end="2024-03-31", prior_end="2023-03-31", period_type="FY",
         reading="text layer: pdf p8 BS (printed 6), p7 IS (5), p10 CF (8); pdf p3-6 (auditor report) image-only", pages=dict(bs=8, is_=7, cf=10),
         bs=dict(cur=bs(1486807564, 634894318, 851913246, 66001206, 233003228), prior=bs(987316736, 371875930, 615440806, 53393601, 245747188)),
         **{"is": dict(cur=isx(1543167801, -1192608580, 350559221, 324014024, 296861222, -11791040, -17562301, 267507881, 8.49),
                       prior=isx(1438646383, -1282846681, 155799702, 133036710, 111741404, -6761844, -5058725, 99920835, 3.17))},
         cf=dict(cur=cf(10724955, -5175602, 7058252, 12607605, 53393601, 66001206), prior=cf(17765842, -3502319, -34751531, -20488008, 73881609, 53393601))),
    dict(sha256_prefix="8f5b16dd", label="FY ended 2023-03-31 audited FS, whole-file scan (label 2023|FY; inventory class scanned_unreadable although the scan holds full statements)", period_end="2023-03-31", prior_end="2022-03-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 6), p7 IS (5), p10 CF (8); no text layer on any page", pages=dict(bs=8, is_=7, cf=10),
         bs=dict(cur=bs(987316736, 371875930, 615440806, 53393601, 245747188), prior=bs(895918698, 380928570, 514990128, 73881609, 262334824)),
         **{"is": dict(cur=isx(1438646383, -1282846681, 155799702, 133036710, 111741404, -6761844, -5058725, 99920835, 3.17),
                       prior=isx(597465405, -569720077, 27745328, 14999514, -1843436, -1061278, -340606, -3245320, -0.10))},
         cf=dict(cur=cf(17765842, -3502319, -34751531, -20488008, 73881609, 53393601), prior=cf(-98578554, -3282693, 133426413, 31565166, 42316443, 73881609))),
]
S = lambda p, blk, col, k: [p, blk, col, k]
rolls = []
for k, nm in (("revenue", "revenue"), ("pbt", "profit before zakat and tax"), ("tax", "zakat plus income tax"), ("net_income", "net profit")):
    rolls.append(dict(name=f"FY26 Q1 + Q2 = H1 {nm}", total=S("8a30cf4b", "is", "cur", k), parts=[S("a97bb7a6", "is", "cur", k), S("8a30cf4b", "is_q", "cur", k)]))
    rolls.append(dict(name=f"FY26 H1 + Q3 = 9M {nm}", total=S("6366e4d4", "is", "cur", k), parts=[S("8a30cf4b", "is", "cur", k), S("6366e4d4", "is_q", "cur", k)]))
    rolls.append(dict(name=f"FY25 Q1 + Q2 = H1 {nm} (comparatives)", total=S("8a30cf4b", "is", "prior", k), parts=[S("a97bb7a6", "is", "prior", k), S("8a30cf4b", "is_q", "prior", k)]))
    rolls.append(dict(name=f"FY25 H1 + Q3 = 9M {nm} (comparatives)", total=S("6366e4d4", "is", "prior", k), parts=[S("8a30cf4b", "is", "prior", k), S("6366e4d4", "is_q", "prior", k)]))
write("1321", "EAST PIPES INTEGRATED COMPANY FOR INDUSTRY", docs, rolls, unit="Saudi riyals (SAR), full units as printed (not thousands); fiscal year ends 31 March")
