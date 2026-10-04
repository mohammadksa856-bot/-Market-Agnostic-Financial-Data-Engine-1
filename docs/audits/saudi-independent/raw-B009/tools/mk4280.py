"""Builds transcripts/4280.json (SAR thousand) from rendered statement pages. 'revenue' = Hotels and other operating revenues (the company has no single
revenue line; dividend income and equity-accounted results are separate lines); 'cost_of_revenue' = Hotels and other operating costs;
'operating_income' = Profit from operations; 'tax' = withholding and income tax plus zakat."""
from tx import I, B, C, doc, write, ref


def K(rev, cost, op, pbt, tax, ni, parent, nci, eps, **k):
    return dict(revenue=rev, cost_of_revenue=cost, operating_income=op, pbt=pbt, tax=tax, net_income=ni, ni_parent=parent, ni_nci=nci, eps=eps, **k)


D25 = B(74934321, 15915940, 59018381, 1524563, 7422158)
D24 = B(54719212, 15160370, 39558842, 1689658, 6801405)
D23 = B(54098335, 17473917, 36624418, 1923789, 6823581)
D22 = B(53155476, 20936354, 32219122, 3440947, 6508529)
docs = [
    doc("373b1daa", "FY2025 audited consolidated FS (collector label 2026|FY, classed other_no_statements_found)", "2025-12-31", "2024-12-31", "FY",
        "visual: statement pages textless images (pdf p8-12); pdf p8 BS (printed 6), p9 IS (7), p12 CF (10) rendered and read",
        {"bs": 8, "is": 9, "cf": 12},
        dict(cur=D25, prior=D24),
        dict(cur=K(1677547, -1098791, 3137059, 2308432, -195533, 2112899, 2143294, -30395, 0.58),
             prior=K(1604442, -1055330, 2388903, 1451260, -244094, 1207166, 1236970, -29804, 0.33)),
        dict(cur=C(986212, -436033, 1426150, -2576711, -164349, 1495903, 1331554),
             prior=C(2674819, -276533, 1560577, -4364680, -129284, 1625187, 1495903))),
    doc("f9757968", "FY2024 audited as filed (collector label 2025|FY)", "2024-12-31", "2023-12-31", "FY",
        "visual: whole-file scan, textless; pdf p7 BS (printed 5), p8 IS (6), p9 OCI (7), p11 CF (9) rendered and read",
        {"bs": 7, "is": 8, "cf": 11},
        dict(cur=D24, prior=D23),
        dict(cur=K(1604442, -1055330, 2388903, 1451260, -244094, 1207166, 1236970, -29804, 0.33),
             prior=K(1592719, -1183874, 2498508, 1296075, -307832, 988243, 1013243, -25000, 0.27)),
        dict(cur=C(2674819, -276533, 1560577, -4364680, -129284, 1625187, 1495903),
             prior=C(702747, -284993, 3477943, -5594060, -1413370, 3038557, 1625187))),
    doc("f15698c2", "FY2023 audited as filed (collector label 2024|FY)", "2023-12-31", "2022-12-31", "FY",
        "visual: whole-file scan, textless; pdf p7 BS (printed 5), p8 IS (6), p11 CF (9) rendered and read",
        {"bs": 7, "is": 8, "cf": 11},
        dict(cur=D23, prior=D22),
        dict(cur=K(1592719, -1183874, 2498508, 1296075, -307832, 988243, 1013243, -25000, 0.27),
             prior=K(1460652, -901603, 7910773, 7306440, -364286, 6942154, 6957868, -15714, 1.88)),
        dict(cur=C(702747, -284993, 3477943, -5594060, -1413370, 3038557, 1625187),
             prior=C(1754262, -151173, 506587, -68513, 2192336, 846221, 3038557))),
    doc("4901b251", "3M ended 2026-03-31 reviewed (English)", "2026-03-31", "2025-03-31", "Q1",
        "visual: statement pages textless images (pdf p4-8; the inventory statement_pages point at the p3 review report); pdf p4 BS (printed 3), p5 IS (4), p8 CF (7) rendered and read",
        {"bs": 4, "is": 5, "cf": 8},
        dict(cur=B(73319373, 15339655, 57979718, 2658648, 7393892), prior=D25),
        dict(cur=K(391467, -269293, 493879, 287466, -26648, 260818, 268881, -8063, 0.07),
             prior=K(353442, -242885, 695330, 455463, -39274, 416189, 431611, -15422, 0.12)),
        dict(cur=C(157567, -45118, 990256, -13738, 1134085, 1524563, 2658648),
             prior=C(339235, -90143, -68970, -250506, 19759, 1689658, 1709417)),
        bs_prior_end="2025-12-31"),
    doc("00754ef7", "3M and 6M ended 2026-06-30 reviewed (English)", "2026-06-30", "2025-06-30", "H1",
        "visual: statement pages textless images; pdf p4 BS (printed 3), p5 IS (4), p8 CF (7) rendered and read; 'is' = six months, 'is_q' = Q2",
        {"bs": 4, "is": 5, "cf": 8},
        dict(cur=B(85462792, 16202970, 69259822, 1527309, 7725326), prior=D25),
        dict(cur=K(850134, -551592, 1115609, 706859, -118261, 588598, 602114, -13516, 0.16),
             prior=K(750892, -514130, 1349309, 884719, -79985, 804734, 836713, -31979, 0.23)),
        dict(cur=C(538664, -490867, 581870, -1117788, 2746, 1524563, 1527309),
             prior=C(421748, -197396, 1219372, -1163925, 477195, 1689658, 2166853)),
        bs_prior_end="2025-12-31",
        is_q=dict(cur=K(458667, -282299, 621730, 419393, -91613, 327780, 333233, -5453, 0.09),
                  prior=K(397450, -271245, 653979, 429257, -40711, 388546, 405103, -16557, 0.11))),
]
rolls = []
for key in ("revenue", "net_income", "pbt", "operating_income"):
    rolls.append(dict(name=f"Q1+Q2=H1 2026 {key}", total=ref("00754ef7", "is", "cur", key), parts=[ref("4901b251", "is", "cur", key), ref("00754ef7", "is_q", "cur", key)]))
    rolls.append(dict(name=f"Q1+Q2=H1 2025 {key} (Q1 from Q1 2026 filing, Q2 from H1 2026 filing)", total=ref("00754ef7", "is", "prior", key),
                      parts=[ref("4901b251", "is", "prior", key), ref("00754ef7", "is_q", "prior", key)], tol=1))
write("4280", "KINGDOM (Kingdom Holding Company)", "SAR thousand in annual and interim filings alike", docs, rolls)
