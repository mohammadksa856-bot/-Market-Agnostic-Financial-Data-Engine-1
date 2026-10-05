"""Builds transcripts/2382.json (ADES Holding) from values read from clean text layers (and one image page) viewed in the B020 session.
Unit: SAR thousands, except the FY2023 original filing and the FY2022 special-purpose filing which are in full SAR (doc scale = 1000)."""
from tb import *


def I(rev, cost, gp, pbt, tax, ni, par=None, nci=None, eps=None):
    return col(revenue=rev, cost_of_revenue=cost, gross_profit=gp, pbt=pbt, tax=tax, net_income=ni, ni_parent=par, ni_nci=nci, eps=eps)


def B(ta, tl, te, cash, ppe):
    return col(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe)


def C(cfo, cfi, cff, net, beg, end, capex):
    return col(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=beg, cash_end=end, capex=capex)


def dd(c, **why):
    c = dict(c)
    c["_declared_diff"] = why
    return c


TXT = "text layer clean, tied by arithmetic"
D = []
# FY2025 (audited), prior column re-presents FY2024
D.append(doc("18b45d3c", "FY2025 audited consolidated FS (EY; label 2026|FY = publication year); FY2024 comparatives re-presented", "2025-12-31", "2024-12-31", "FY", TXT + " (pdf p8-10, 13-14)",
             {"bs": "8-9", "is": 10, "cf": "13-14"},
             bs=(B(31411709, 24598715, 6812994, 2458449, 25030984), B(21628690, 15090706, 6537984, 744187, 17567622)),
             is_=(I(6688959, -4155868, 2533091, 1044928, -212067, 832861, 818016, 14845, 0.74),
                  dd(I(6199022, -3841373, 2357649, 970846, -154651, 816195, 802498, 13697, 0.73),
                     cost_of_revenue="FY2024 filing shows -3,839,972 (the 1,401 inventory provision is moved into cost of revenue in the FY2025 filing)",
                     gross_profit="FY2024 filing shows 2,359,050 (same reclassification of 1,401)")),
             cf=(C(2980723, -2732219, 1465758, 1714262, 744187, 2458449, -1837878),
                 dd(C(2995912, -3182435, 498428, 311905, 432282, 744187, -2375110),
                    cfo="FY2024 filing shows 2,998,780 (2,868 re-presented between operating and investing)",
                    cfi="FY2024 filing shows -3,185,303 (acquisition of business -712,134 there versus -709,266)")),
             restatements=["FY2024 comparatives re-presented: cost of revenue -3,839,972 -> -3,841,373, gross profit 2,359,050 -> 2,357,649; CFO 2,998,780 -> 2,995,912; CFI -3,185,303 -> -3,182,435; profit before tax 970,846, net profit 816,195 and cash unchanged"]))
D.append(doc("d1d9ccba", "FY2024 audited consolidated FS as issued (EY report dated 3 March 2025; label 2025|FY = publication year); prior column is the 28 Dec 2022 to 31 Dec 2023 period", "2024-12-31", "2023-12-31", "FY",
             TXT + " (pdf p8-9, 12-13; pdf p7 is the auditor's report page, image-only, viewed)", {"is": 8, "bs": 9, "cf": "12-13"},
             bs=(B(21628690, 15090706, 6537984, 744187, 17567622), B(19422452, 13645545, 5776907, 432282, 16149784)),
             is_=(I(6199022, -3839972, 2359050, 970846, -154651, 816195, 802498, 13697, 0.73), I(4331903, -2620778, 1711125, 529379, -77301, 452078, 442097, 9981, 0.59)),
             cf=(C(2998780, -3185303, 498428, 311905, 432282, 744187, -2375110),
                 dd(C(2282704, -3736485, 1886063, 432282, 0, 432282, -4048366),
                    cfo="the FY2023 filing in full SAR shows 2,282,706,055 (2 thousand higher)",
                    cff="the FY2023 filing shows 1,886,060,723 (2 thousand lower; loans proceeds 3,351,737 vs 3,447,680 and repayments -3,554,625 vs -3,650,568 are shown gross in the FY2024 comparatives)"))))
D.append(doc("dc1de08f", "FY2023 audited consolidated FS as issued: period from 28 Dec 2022 (incorporation) to 31 Dec 2023, full SAR; label 2024|FY = publication year", "2023-12-31", None, "FY (first period)",
             TXT + " (pdf p8-9, 11; pdf p7 auditor page image-only, not opened)", {"is": 8, "bs": 9, "cf": 11}, scale=1000,
             bs=(B(19422450754, 13645544587, 5776906167, 432281641, 16149784495), None),
             is_=(I(4331902893, -2620777799, 1711125094, 529379815, -77301057, 452078758, 442097695, 9981063, 0.59), None),
             cf=(C(2282706055, -3736485137, 1886060723, 432281641, 0, 432281641, -4048365638), None)))
D.append(doc("73667c41", "special purpose consolidated FS of ADES Holding Company (Mixed Closed JSC) for 2022, 2021 and 2020, full SAR, approved 12 March 2023; label 2024|FY is wrong", "2022-12-31", "2021-12-31", "FY (special purpose, pre-IPO perimeter)",
             TXT + " (pdf p5 IS, p6 BS, p10 CF; pdf p2-4 textless auditor pages not opened)", {"is": 5, "bs": 6, "cf": 10}, scale=1000, prior2_end="2020-12-31",
             bs=(B(14501345645, 12242915101, 2258430544, 190828971, 12188121186), B(6692071970, 4768993170, 1923078800, 232860330, 5358404795)),
             is_=(I(2467200801, -1575805738, 891395063, 468344359, -70722417, 397621942, 390448249, 7173693), I(1514205630, -974883191, 539322439, 149059886, -34631296, 114428590, 107810728, 6617862)),
             cf=(C(1146247852, -6438009610, 5249730399, -42031359, 232860330, 190828971, -3923217971), C(316790012, -1463643639, 1145381902, -1471725, 234332055, 232860330, -354997191))))
# add the 2020 columns
D[-1]["bs"]["prior2"] = B(5189564336, 3487449131, 1702115205, 234332055, 3794626973)
D[-1]["is"]["prior2"] = I(1695407138, -1058790649, 636616489, 116130866, -33550188, 82580678, 73580576, 9000102)
D[-1]["cf"]["prior2"] = C(620446605, -437773095, -396845801, -214172291, 448504346, 234332055, -441110865)
D.append(doc("a111cf61", "H1 2026 interim FS (six-month period ended 2026-06-30, unaudited; EPS caption reads 'In $ per share' in the file)", "2026-06-30", "2025-06-30", "H1", TXT + " (pdf p5-7, 10-11)",
             {"bs": "5-6", "is": 7, "cf": "10-11"}, bs_prior_end="2025-12-31",
             bs=(B(31677705, 24741277, 6936428, 2434635, 24966770), B(31411709, 24598715, 6812994, 2458449, 25030984)),
             is_=(I(4544065, -2937316, 1606749, 473548, -99427, 374121, 364973, 9148, 0.33), I(3048964, -1865947, 1183017, 482343, -93982, 388361, 382758, 5603, 0.35)),
             isq=(I(2153329, -1425429, 727900, 170290, -37022, 133268, 128531, 4737, 0.12), I(1578826, -985993, 592833, 245426, -53744, 191682, 188603, 3079, 0.17)),
             cf=(C(1497493, -803940, -717367, -23814, 2458449, 2434635, -804398), C(1160528, -964795, -142916, 52817, 744187, 797004, -948920))))
D.append(doc("6a5c0453", "Q1 2026 interim FS (three-month period ended 2026-03-31, unaudited)", "2026-03-31", "2025-03-31", "Q1", TXT + " (pdf p5-7, 10-11)",
             {"bs": "5-6", "is": 7, "cf": "10-11"}, bs_prior_end="2025-12-31",
             bs=(B(31646491, 24841203, 6805288, 2435773, 24954539), B(31411709, 24598715, 6812994, 2458449, 25030984)),
             is_=(I(2390736, -1511887, 878849, 303258, -62405, 240853, 236442, 4411, 0.21), I(1470138, -879954, 590184, 236917, -40238, 196679, 194155, 2524, 0.18)),
             cf=(C(760907, -363581, -420002, -22676, 2458449, 2435773, -363412), C(625487, -474492, -598952, -447957, 744187, 296230, -457485))))
D.append(doc("1152c9a9", "H1 2025 interim FS (six-month period ended 2025-06-30, unaudited)", "2025-06-30", "2024-06-30", "H1", TXT + " (pdf p5-7, 9)",
             {"bs": "5-6", "is": 7, "cf": 9}, bs_prior_end="2024-12-31",
             bs=(B(22300057, 15664061, 6635996, 797004, 18279253), B(21628690, 15090706, 6537984, 744187, 17567622)),
             is_=(I(3048964, -1865947, 1183017, 482343, -93982, 388361, 382758, 5603, 0.35), I(3057357, -1880647, 1176710, 475351, -72377, 402974, 395831, 7143, 0.36)),
             isq=(I(1578826, -985993, 592833, 245426, -53744, 191682, 188603, 3079, 0.17), I(1525287, -951263, 574024, 243994, -41868, 202126, 198470, 3656, 0.18)),
             cf=(C(1160528, -964795, -142916, 52817, 744187, 797004, -948920), C(1699450, -1575823, 212238, 335865, 432282, 768147, -1474985))))
D.append(doc("8be70142", "9M 2025 interim FS (nine-month period ended 2025-09-30, unaudited)", "2025-09-30", "2024-09-30", "9M", TXT + " (pdf p5-7, 9-10)",
             {"bs": "5-6", "is": 7, "cf": "9-10"}, bs_prior_end="2024-12-31",
             bs=(B(22639706, 16009310, 6630396, 939589, 18344150), B(21628690, 15090706, 6537984, 744187, 17567622)),
             is_=(I(4702898, -2914465, 1788433, 755172, -147666, 607506, 597331, 10175, 0.54), I(4629953, -2837696, 1792257, 721363, -115104, 606259, 595448, 10811, 0.54)),
             isq=(I(1653934, -1048518, 605416, 272829, -53684, 219145, 214573, 4572, 0.19), I(1572596, -957049, 615547, 246012, -42727, 203285, 199617, 3668, 0.18)),
             cf=(C(1934896, -1623461, -116033, 195402, 744187, 939589, -1377272), C(2025480, -1993912, 348291, 379859, 432282, 812141, -1823049))))
D.append(doc("bd69ad32", "Q1 2025 interim FS (three-month period ended 2025-03-31, unaudited)", "2025-03-31", "2024-03-31", "Q1", TXT + " (pdf p3-4, 7)",
             {"is": 3, "bs": 4, "cf": 7}, bs_prior_end="2024-12-31",
             bs=(B(21325074, 14858456, 6466618, 296230, 17682385), B(21628690, 15090706, 6537984, 744187, 17567622)),
             is_=(I(1470138, -879954, 590184, 236917, -40238, 196679, 194155, 2524, 0.18), I(1532070, -929384, 602686, 231357, -30509, 200848, 197361, 3487, 0.18)),
             cf=(C(625487, -474492, -598952, -447957, 744187, 296230, -457485), C(1141423, -774228, -324870, 42325, 432282, 474607, -774228))))

B23 = B(19422452, 13645545, 5776907, 432282, 16149784)
D.append(doc("cc3168a8", "9M 2024 interim FS (nine-month period ended 2024-09-30, unaudited); BS cash 883,392 includes an escrow account of 71,251 excluded from cash for the cash flow", "2024-09-30", "2023-09-30", "9M", TXT + " (pdf p3-4, 7, 14)",
             {"is": 3, "bs": 4, "cf": 7}, bs_prior_end="2023-12-31", bs=(B(21055975, 14832973, 6223002, 883392, 16785472), B23),
             is_=(I(4629953, -2837696, 1792257, 721363, -115104, 606259, 595448, 10811, 0.54), I(3059554, -1863777, 1195777, 331407, -48335, 283072, 275262, 7810, 0.44)),
             isq=(I(1572596, -957049, 615547, 246012, -42727, 203285, 199617, 3668, 0.18), I(1078685, -663799, 414886, 104672, -17319, 87353, 83870, 3483, 0.10)),
             cf=(C(2025480, -1993912, 348291, 379859, 432282, 812141, -1823049), C(1463623, -2954735, 2066344, 575232, 190829, 766061, -2954757))))
D.append(doc("6bf7ba99", "H1 2024 interim FS (six-month period ended 2024-06-30, unaudited)", "2024-06-30", "2023-06-30", "H1", TXT + " (pdf p3-4, 7)",
             {"is": 3, "bs": 4, "cf": 7}, bs_prior_end="2023-12-31", bs=(B(20560888, 14249076, 6311812, 768147, 16753610), B23),
             is_=(I(3057357, -1880647, 1176710, 475351, -72377, 402974, 395831, 7143, 0.36), I(1980869, -1199978, 780891, 226736, -31017, 195719, 191393, 4326, 0.37)),
             isq=(I(1525287, -951263, 574024, 243994, -41868, 202126, 198470, 3656, 0.18), I(1026013, -616675, 409338, 122630, -16321, 106309, 103831, 2478, 0.12)),
             cf=(C(1699450, -1575823, 212238, 335865, 432282, 768147, -1474985), C(910005, -2141742, 1693288, 461551, 190829, 652380, -2141742))))
D.append(doc("15426fd5", "Q1 2024 interim FS (three-month period ended 2024-03-31, unaudited; b9a77c0c is a text-identical copy on all 33 pages)", "2024-03-31", "2023-03-31", "Q1", TXT + " (pdf p3-4, 7, selected lines)",
             {"is": 3, "bs": 4, "cf": 7}, bs_prior_end="2023-12-31", bs=(col(total_assets=20183373, total_liabilities=14098418, total_equity=6084955, cash=474607, ppe=16628205), B23),
             is_=(I(1532070, -929384, 602686, 231357, -30509, 200848, 197361, 3487, 0.18), I(954856, -583303, 371553, 104106, -14696, 89410, 87562, 1848, 0.54)),
             cf=(C(1141423, -774228, -324870, 42325, 432282, 474607, -774228), C(398551, -1034933, 825687, 189305, 190829, 380134, -1034933))))

D.append(doc("44b81bc8", "9M 2023 interim FS (nine-month period ended 2023-09-30, unaudited), full SAR; PBT and tax later re-presented in the 9M 2024 comparatives; Dec 2022 PPE re-presented", "2023-09-30", "2022-09-30", "9M",
             TXT + " (pdf p3-4, 7)", {"is": 3, "bs": 4, "cf": 7}, scale=1000, bs_prior_end="2022-12-31",
             bs=(B(18749668541, 16112198325, 2637470216, 766060913, 15224947459),
                 dd(B(14501345645, 12242915101, 2258430544, 190828971, 12066091416), ppe="the FY2022 special-purpose filing shows 12,188,121,186; the difference 122,029,770 equals the 'reimbursement of the purchase price consideration' 122,029,770 in the FY2023 cash flow; total assets are identical")),
             is_=(dd(I(3059554355, -1863777348, 1195777007, 347730492, -64658237, 283072255, 275262461, 7809794), pbt="9M 2024 comparatives show 331,407 thousand", tax="9M 2024 comparatives show -48,335 thousand; net profit identical"),
                  I(1669709781, -1059379411, 610330370, 225139138, -49400153, 175738985, 171178615, 4560370)),
             isq=(dd(I(1078685470, -663799430, 414886040, 110508040, -23155521, 87352519, 83869311, 3483208), pbt="9M 2024 comparatives show Q3 2023 pbt 104,672 thousand", tax="9M 2024 comparatives show Q3 2023 tax -17,319 thousand; net profit identical"),
                  I(590487332, -390455449, 200031883, 42602817, -19778238, 22824579, 21961766, 862813)),
             cf=(C(1463623436, -2954735453, 2066343959, 575231942, 190828971, 766060913, -2954757212), C(770774842, -4905483519, 4963347447, 828638770, 232860330, 1061499100, -2562649483))))
D.append(doc("b1e2a770", "Arabic 9M 2023 interim FS (same period as 44b81bc8; revenue 3,059,554,355 in the p3 text layer; not transcribed further)", "2023-09-30", None, "9M", "revenue line only, text layer", {"is": 3}))

def S(p, b, c, k):
    return (p, b, c, k)


R = []
for k in ("revenue", "cost_of_revenue", "gross_profit", "pbt", "tax", "net_income", "ni_parent", "ni_nci"):
    R.append(roll(f"Q1 + Q2 2026 = H1 2026 {k}", S("a111cf61", "is", "cur", k), [S("6a5c0453", "is", "cur", k), S("a111cf61", "is_q", "cur", k)]))
    R.append(roll(f"Q1 + Q2 2025 = H1 2025 {k}", S("1152c9a9", "is", "cur", k), [S("bd69ad32", "is", "cur", k), S("1152c9a9", "is_q", "cur", k)]))
    R.append(roll(f"H1 + Q3 2025 = 9M 2025 {k}", S("8be70142", "is", "cur", k), [S("1152c9a9", "is", "cur", k), S("8be70142", "is_q", "cur", k)]))
    R.append(roll(f"Q1 + Q2 2024 = H1 2024 {k}", S("1152c9a9", "is", "prior", k), [S("bd69ad32", "is", "prior", k), S("1152c9a9", "is_q", "prior", k)]))
    R.append(roll(f"H1 + Q3 2024 = 9M 2024 {k}", S("8be70142", "is", "prior", k), [S("1152c9a9", "is", "prior", k), S("8be70142", "is_q", "prior", k)]))
for k in ("revenue", "cost_of_revenue", "gross_profit", "pbt", "tax", "net_income", "ni_parent", "ni_nci"):
    R.append(roll(f"Q1 + Q2 2024 (own filings) = H1 2024 {k}", S("6bf7ba99", "is", "cur", k), [S("15426fd5", "is", "cur", k), S("6bf7ba99", "is_q", "cur", k)]))
    R.append(roll(f"H1 + Q3 2024 (own filings) = 9M 2024 {k}", S("cc3168a8", "is", "cur", k), [S("6bf7ba99", "is", "cur", k), S("cc3168a8", "is_q", "cur", k)]))
    R.append(roll(f"Q1 + Q2 2023 = H1 2023 {k}", S("6bf7ba99", "is", "prior", k), [S("15426fd5", "is", "prior", k), S("6bf7ba99", "is_q", "prior", k)]))
    R.append(roll(f"H1 + Q3 2023 = 9M 2023 {k} (tolerance 1 thousand: pbt and tax round differently)", S("cc3168a8", "is", "prior", k), [S("6bf7ba99", "is", "prior", k), S("cc3168a8", "is_q", "prior", k)], tol=1))
write("2382", "ADES (ADES Holding Company)", "SAR", "SAR thousands; FY2023 original and FY2022 special-purpose filings in full SAR (doc scale 1000)", D, R)
