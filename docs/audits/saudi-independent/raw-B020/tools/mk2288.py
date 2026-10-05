"""Builds transcripts/2288.json (Nofoth Food Products) from clean text layers and rendered Arabic scan pages viewed in the B020 session. Full SAR."""
from tb import *


def I(rev, cost, gp, op, pbt, tax, ni, eps=None):
    return col(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, eps=eps)


def B(ta, tl, te, cash=None, ppe=None):
    return col(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe)


def C(cfo, cfi, cff, net, beg, end, capex=None):
    return col(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=beg, cash_end=end, capex=capex)


def dd(c, **why):
    c = dict(c)
    c["_declared_diff"] = why
    return c


TXT = "text layer clean, tied by arithmetic"
D = []
D.append(doc("e0dc6e6f", "FY2025 audited FS (label 2026|FY = publication year); FY2024 comparatives re-presented in the cash flow; EPS 2024 restated for the 1:1 bonus issue", "2025-12-31", "2024-12-31", "FY",
             TXT + " (pdf p6, 7, 9-10; pdf p3-5 textless not opened)", {"bs": 6, "is": 7, "cf": "9-10"},
             bs=(B(275802474, 90469455, 185333019, 6409575, 73745456), B(235756759, 94437330, 141319429, 3775047, 71539197)),
             is_=(I(429604219, -162598307, 267005912, 55996572, 58206587, -1464412, 56742175, 0.60), I(365059686, -138751207, 226308479, 50012746, 53039860, -1403675, 51636185, 0.54)),
             cf=(C(60386005, -24911390, -32840087, 2634528, 3775047, 6409575, -15378564),
                 dd(C(90360701, -62014634, -34921442, -6575375, 10350422, 3775047, -42319121),
                    cfo="FY2024 filing as issued shows 93,728,021 (income receipt from murabaha deposits 3,367,320 moved to investing)", cfi="FY2024 filing as issued shows -65,381,954")),
             restatements=["FY2024 cash flow: CFO 93,728,021 -> 90,360,701 and CFI -65,381,954 -> -62,014,634 (3,367,320 murabaha income receipt), net change unchanged; FY2024 EPS 1.08 -> 0.54 and FY2023 EPS 0.89 for the 1:1 bonus issue (48,000,000 transferred to capital in 2025)"]))
D.append(doc("c0a96163", "FY2024 audited FS as issued (label 2025|FY = publication year)", "2024-12-31", "2023-12-31", "FY",
             "text layer for BS and CF totals (tie by arithmetic; digits partly split in the text); income statement page rendered and read (pdf p7)", {"bs": 6, "is": 7, "cf": 9},
             bs=(B(235756759, 94437330, 141319429, 3775047, 71539197), B(162867287, 56484055, 106383232, 10350422, 40837346)),
             is_=(I(365059686, -138751207, 226308479, 50012746, 53039860, -1403675, 51636185, 1.08), I(308189985, -125218746, 182971239, 42689134, 44443602, -1772847, 42670755, 0.89)),
             cf=(C(93728021, -65381954, -34921442, -6575375, 10350422, 3775047, -42319121), C(69062490, -68421930, -18636780, -17996220, 28346642, 10350422, -13365002))))
D.append(doc("9d036ce5", "FY2023 audited FS as issued, Arabic scan (33 pages, 100% textless), collector label 2024|FY; income statement page read from the image (pdf p7)", "2023-12-31", "2022-12-31", "FY",
             "visual: whole-file scan, income statement page rendered and read (Arabic-Indic digits), tied by arithmetic; other pages not read", {"is": 7},
             is_=(dd(I(308189985, -125218746, 182971239, 42728293, 44443602, -1772847, 42670755, 1.78),
                     operating_income="FY2024 filing shows 42,689,134 for 2023: the expected credit loss 39,159 is a line below main operating profit in this original", eps="FY2024 filing shows 0.89 (bonus issue not yet reflected: 24,000,000 shares)"),
                  I(270199270, -122441240, 147758030, None, 32374634, -887923, 31486711))))
D[-1]["is"]["prior"] = {k: v for k, v in D[-1]["is"]["prior"].items() if v is not None}
D.append(doc("4f4be7af", "FY2022 audited FS as issued, Arabic scan (28 pages, 100% textless), collector label 2023|FY; BS, IS and CF pages rendered (pdf p6, 7, 9)", "2022-12-31", "2021-12-31", "FY",
             "visual: whole-file scan, Arabic-Indic digits; BS and IS lines tied by arithmetic and BS totals confirmed against clean comparatives in the H1 2023 filing; CF page not transcribed (digits do not tie)", {"bs": 6, "is": 7},
             bs=(B(123397680, 54980590, 68417090, 28346642, 37026885), None),
             is_=(dd(I(268819480, -122441240, 146378240, None, 32374634, -887923, 31486711), revenue="the FY2023 filing re-presents 2022 revenue as 270,199,270 (cost 122,441,240 unchanged, gross profit 147,758,030; profit before zakat and net profit identical)", gross_profit="re-presented 147,758,030"), None),
             bs_note="the scan reads 123,397,780 and 54,980,690 for total assets and liabilities at 1.5x zoom (hundreds digit ambiguous); the clean comparatives in the H1 2023 filing give 123,397,680 and 54,980,590, which tie to equity 68,417,090, and are used"))
D[-1]["is"]["cur"] = {k: v for k, v in D[-1]["is"]["cur"].items() if v is not None}
D.append(doc("35e63450", "H1 2026 interim FS (six-month period ended 2026-06-30, unaudited)", "2026-06-30", "2025-06-30", "H1", TXT + " (pdf p4-5, 7-8)", {"bs": 4, "is": 5, "cf": "7-8"}, bs_prior_end="2025-12-31",
             bs=(B(289405944, 103471398, 185934546, 5118358, 73226349), B(275802474, 90469455, 185333019, 6409575, 73745456)),
             is_=(I(215508401, -81096751, 134411650, 24460519, 25351854, -753634, 24598220, 0.26), I(219789372, -80855383, 138933989, 32635878, 33861102, -1159198, 32701904, 0.34)),
             isq=(I(106150005, -39879725, 66270280, 10379851, 10568379, -288624, 10279755, 0.11), I(105494150, -39832224, 65661926, 12381752, 13040410, -565622, 12474788, 0.13)),
             cf=(C(32462575, -2463934, -31289858, -1291217, 6409575, 5118358, -3694934), C(33520325, -7671684, -20699493, 5149148, 3775047, 8924195, -8962504))))
D.append(doc("47c2d415", "Q1 2026 interim FS (three-month period ended 2026-03-31, unaudited)", "2026-03-31", "2025-03-31", "Q1", TXT + " (pdf p4-5, 7-8)", {"bs": 4, "is": 5, "cf": "7-8"}, bs_prior_end="2025-12-31",
             bs=(B(288287918, 92922288, 195365630, 17218439, 72751796), B(275802474, 90469455, 185333019, 6409575, 73745456)),
             is_=(I(109358396, -41162228, 68196168, 14080668, 14783475, -465010, 14318465, 0.15), I(114295222, -41023159, 73272063, 20254126, 20820692, -593576, 20227116, 0.21)),
             cf=(C(17934824, -847938, -6278022, 10808864, 6409575, 17218439, -1528942), C(18237862, -791169, -4357927, 13088766, 3775047, 16863813, -2081989))))
D.append(doc("04ac1de0", "H1 2025 interim FS as issued (six-month period ended 2025-06-30, unaudited)", "2025-06-30", "2024-06-30", "H1", TXT + " (pdf p4-5, 7-8; comparatives columns interleaved in the text, identified by arithmetic)", {"bs": 4, "is": 5, "cf": "7-8"}, bs_prior_end="2024-12-31",
             bs=(B(256767944, 94654970, 162112974, None, 73762879), B(235756759, 94437330, 141319429, 3775047, 71539197)),
             is_=(I(219789372, -80855383, 138933989, 32635878, 33861102, -1159198, 32701904), I(179320013, -68781845, 110538168, 26323372, 28530399, -1392631, 27137768)),
             isq=(I(105494150, -39832224, 65661926, 12381752, 13040410, -565622, 12474788), I(84097010, -32835019, 51261991, 9593769, 10941467, -693544, 10247923)),
             cf=(dd(col(cfo=35233995, net_change=5149148, cash_begin=3775047), cfo="the H1 2026 filing re-presents H1 2025 CFO as 33,520,325 (investment income and murabaha lines moved to investing)"), col(cfo=38313131, net_change=1444218, cash_begin=10350422))))
D.append(doc("5ee1f67a", "9M 2025 interim FS (nine-month period ended 2025-09-30, unaudited)", "2025-09-30", "2024-09-30", "9M", TXT + " (pdf p4-5, 7-8; comparatives interleaved)", {"bs": 4, "is": 5, "cf": "7-8"}, bs_prior_end="2024-12-31",
             bs=(B(268128552, 94486123, 173642429, None, 73084233), B(235756759, 94437330, 141319429, 3775047, 71539197)),
             is_=(I(324680590, -121225253, 203455337, 44079692, 45884753, -1653394, 44231359), I(266459224, -103221666, 163237558, 34700915, 37993011, -1902393, 36090618)),
             isq=(I(104891218, -40369870, 64521348, 11443814, 12023651, -494196, 11529455), I(87139211, -34439821, 52699390, 8377543, 9462612, -509762, 8952850)),
             cf=(col(cfo=49263669, net_change=11863603, cash_begin=3775047), col(cfo=59223204, net_change=677540, cash_begin=10350422))))
D.append(doc("58588e3a", "Q1 2025 interim FS as issued (three-month period ended 2025-03-31, unaudited); EPS before the 2025 bonus issue", "2025-03-31", "2024-03-31", "Q1", TXT + " (pdf p4-5, 7-8)", {"bs": 4, "is": 5, "cf": "7-8"}, bs_prior_end="2024-12-31",
             bs=(B(259642049, 98095504, 161546545, None, 70302595), B(235756759, 94437330, 141319429, 3775047, 71539197)),
             is_=(I(114295222, -41023159, 73272063, 20254126, 20820692, -593576, 20227116, 0.42), I(95223003, -35946826, 59276177, 16729603, 17588932, -699087, 16889845, 0.35)),
             cf=(dd(col(cfo=20118128, cfi=-2671435, cff=-4357927, cash_begin=3775047, cash_end=16863813), cfo="the Q1 2026 filing re-presents Q1 2025 CFO as 18,237,862 (1,880,266 murabaha income receipt moved)", cfi="re-presented -791,169"), None)))
D[-1]["cf"].pop("prior", None)
D.append(doc("2ead71ac", "H1 2024 interim FS as issued (six-month period ended 2024-06-30, unaudited; Saudi listed joint stock company)", "2024-06-30", "2023-06-30", "H1", TXT + " (pdf p4-5, 7-8)", {"bs": 4, "is": 5, "cf": "7-8"}, bs_prior_end="2023-12-31",
             bs=(B(195814987, 77828624, 117986363, None, 42026107), B(162867287, 56484055, 106383232, 10350422, 40837346)),
             is_=(I(179320013, -68781845, 110538168, 26323372, 28530399, -1392631, 27137768, 0.57), I(155621374, -64152640, 91468734, 23422828, 22665679, -614223, 22051456, 0.46)),
             cf=(C(38313131, -22472587, -14396326, 1444218, 10350422, 11794640), C(34384671, -4566657, -12272313, 17545701, 28346642, 45892343))))
D.append(doc("192af7ac", "H1 2023 interim FS as issued (six-month period ended 2023-06-30, unaudited)", "2023-06-30", "2022-06-30", "H1", TXT + " (pdf p4-5; cash flow page not read)", {"bs": 4, "is": 5}, bs_prior_end="2022-12-31",
             bs=(B(143438737, 57770191, 85668546, None, 36825807), B(123397680, 54980590, 68417090, None, 37026885)),
             is_=(I(155621374, -64152640, 91468734, 23422828, 22665679, -614223, 22051456, 0.92), I(135722913, -63442347, 72280566, 15397160, 15794399, -423234, 15371165, 0.64))))


def S(p, b, c, k):
    return (p, b, c, k)


R = []
ALL = ("revenue", "cost_of_revenue", "gross_profit", "operating_income", "pbt", "tax", "net_income")
for k in ("revenue", "operating_income", "pbt", "tax", "net_income"):
    R.append(roll(f"Q1 + Q2 2026 = H1 2026 {k}", S("35e63450", "is", "cur", k), [S("47c2d415", "is", "cur", k), S("35e63450", "is_q", "cur", k)]))
for k in ALL:
    R.append(roll(f"Q1 + Q2 2025 = H1 2025 {k}", S("04ac1de0", "is", "cur", k), [S("58588e3a", "is", "cur", k), S("04ac1de0", "is_q", "cur", k)]))
    R.append(roll(f"H1 + Q3 2025 = 9M 2025 {k}", S("5ee1f67a", "is", "cur", k), [S("04ac1de0", "is", "cur", k), S("5ee1f67a", "is_q", "cur", k)]))
    R.append(roll(f"Q1 2024 + Q2 2024 = H1 2024 {k}", S("2ead71ac", "is", "cur", k), [S("58588e3a", "is", "prior", k), S("04ac1de0", "is_q", "prior", k)]))
    R.append(roll(f"H1 2024 + Q3 2024 = 9M 2024 {k}", S("5ee1f67a", "is", "prior", k), [S("2ead71ac", "is", "cur", k), S("5ee1f67a", "is_q", "prior", k)]))
write("2288", "NOFOTH (Nofoth Food Products Company)", "SAR", "full SAR (no scaling) in every filing read", D, R,
      notes=["Q1 2026 + Q2 2026 = H1 2026 holds for revenue, operating profit, profit before zakat, zakat and net profit but NOT for cost of sales and gross profit (Q1 41,162,228 + Q2 39,879,725 = 81,041,953 versus H1 81,096,751; difference 54,798 moved between cost of sales and G&A in the H1 statement)."])
