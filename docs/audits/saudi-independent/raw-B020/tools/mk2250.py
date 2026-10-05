"""Builds transcripts/2250.json from values typed from page images / clean text layers viewed in the B020 session. SAR thousands."""
from tb import *

X = ["equity_income"]


def I(eq, op, pbt, tax, ni, par=None, nci=None, eps=None):
    return col(equity_income=eq, operating_income=op, pbt=pbt, tax=tax, net_income=ni, ni_parent=par, ni_nci=nci, eps=eps)


def B(ta, tl, te, cash, ppe=None):
    return col(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe)


def C(cfo, cfi, cff, net, beg, end):
    return col(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=beg, cash_end=end)


VIS = "visual: statement pages textless, rendered and read"
D = []
D.append(doc("8af24f13", "FY2025 audited consolidated FS (PwC; label 2026|FY = publication year)", "2025-12-31", "2024-12-31", "FY", VIS + " (pdf p8-12)",
             {"bs": 8, "is": 9, "cf": 12}, bs=(B(8822747, 200892, 8621855, 399645, 51572), B(10101448, 266931, 9834517, 919068, 1772)),
             is_=(I(-84365, -156472, -133846, 29743, -104103, -103672, -431, -0.15), I(183396, 115046, 143627, 57616, 201243, 201243, 0, 0.27)),
             cf=(C(275644, 301974, -1097041, -519423, 919068, 399645), C(779813, 317771, -754296, 343288, 575780, 919068)), extra=X))
D.append(doc("71e433f7", "FY2024 audited consolidated FS (label 2025|FY = publication year)", "2024-12-31", "2023-12-31", "FY", VIS + " (pdf p8,9,11)",
             {"bs": 8, "is": 9, "cf": 11}, bs=(B(10101448, 266931, 9834517, 919068, 1772), B(10772372, 749808, 10022564, 575780, 1779)),
             is_=(I(183396, 115046, 143627, 57616, 201243, eps=0.27), I(188169, 125140, 180818, -68617, 112201, eps=0.15)),
             cf=(C(779813, 317771, -754296, 343288, 575780, 919068), C(43621, 712283, -380170, 375734, 200046, 575780)), extra=X))
D.append(doc("874ddc6d", "FY2023 audited consolidated FS (label 2024|FY = publication year; CF page headed statement of changes in equity in the file)", "2023-12-31", "2022-12-31", "FY",
             VIS + " (pdf p9,10,12)", {"bs": 9, "is": 10, "cf": 12}, bs=(B(10772372, 749808, 10022564, 575780, 1779), B(11054211, 367240, 10686971, 200046, 1690)),
             is_=(I(188169, 125140, 180818, -68617, 112201, 112201, 0, 0.15), I(494073, 422102, 467494, -73811, 393683, 277440, 116243, 0.41)),
             cf=(C(43621, 712283, -380170, 375734, 200046, 575780), C(473458, -392403, -1694820, -1613765, 1813811, 200046)), extra=X))
D.append(doc("c2ddeaca", "FY2022 audited consolidated FS (label 2023|FY = publication year; CF page headed profit or loss and OCI in the file)", "2022-12-31", "2021-12-31", "FY",
             VIS + " (pdf p9,10,12)", {"bs": 9, "is": 10, "cf": 12}, bs=(B(11054211, 367240, 10686971, 200046, 1690), B(12311449, 418111, 11893338, 1813811, 1651)),
             is_=(I(494073, 422102, 467494, -73811, 393683, 277440, 116243, 0.41), I(1905924, 1836814, 1847442, -29669, 1817773, 1136272, 681501, 2.53)),
             cf=(C(473458, -392403, -1694820, -1613765, 1813811, 200046), C(218521, 1057811, -628263, 648069, 1165742, 1813811)), extra=X))
D.append(doc("989c9047", "Q4 2025 interim FS (three-month period and year ended 2025-12-31, unaudited; collector label 2025|Q1 is wrong)", "2025-12-31", "2024-12-31", "Q4+FY",
             VIS + " (pdf p5 income statement only; BS, equity and CF pages not read)", {"is": 5},
             is_=(I(-84365, -156472, -133846, 29743, -104103), I(183396, 115046, 143627, 57616, 201243)),
             isq=(I(-171755, -196366, -194996, 44700, -150296), I(-67445, -88707, -79868, 91126, 11258)), extra=X))
D.append(doc("d59eef41", "Q4 2022 interim FS (three-month period and year ended 2022-12-31, unaudited; whole-file scan; collector label None|None)", "2022-12-31", "2021-12-31", "Q4+FY",
             "visual: whole-file scan, income statement page rendered and read (pdf p5, printed 4); other pages not read", {"is": 5},
             is_=(I(494073, 422102, 467494, -73811, 393683), I(1905924, 1836814, 1847442, -29669, 1817773)),
             isq=(I(-288185, -307654, -290245, -6191, -296436), I(299926, 272262, 276021, -49855, 226166)), extra=X))
D.append(doc("e0ce5fe2", "9M 2025 interim FS (nine-month period ended 2025-09-30, unaudited)", "2025-09-30", "2024-09-30", "9M",
             VIS + " (pdf p5 income statement only; BS and CF pages not read)", {"is": 5},
             is_=(I(87390, 39894, 61150, -14957, 46193, 46193, 0), I(250841, 203753, 223495, -33510, 189985, 189985, 0)),
             isq=(I(24313, 7120, 9174, -841, 8333), I(126327, 106236, 111567, -13481, 98086)), extra=X))
D.append(doc("dacda519", "H1 2025 interim FS (six-month period ended 2025-06-30, unaudited)", "2025-06-30", "2024-06-30", "H1", "text layer clean (pdf p4,5,7); equity page p6 textless, not read",
             {"bs": 4, "is": 5, "cf": 7}, bs_prior_end="2024-12-31",
             bs=(B(9284532, 222618, 9061914, 278997, 1401), B(10101448, 266931, 9834517, 919068, 1772)),
             is_=(I(63077, 32774, 51976, -14116, 37860), I(124514, 97517, 111928, -20029, 91899)),
             isq=(I(31666, 13035, 23410, -3783, 19627), I(77192, 62033, 70340, -5973, 64367)),
             cf=(C(91495, 78897, -810463, -640071, 919068, 278997), C(139675, 348510, -369758, 118427, 575780, 694207)), extra=X))
D.append(doc("83284b75", "Q1 2025 interim FS (three-month period ended 2025-03-31, unaudited)", "2025-03-31", "2024-03-31", "Q1", "text layer clean (pdf p4,5,7); selected lines",
             {"bs": 4, "is": 5, "cf": 7}, bs_prior_end="2024-12-31", bs=(B(10103446, 250696, 9852750, 985699), B(10101448, 266931, 9834517, 919068)),
             is_=(I(31411, 19739, 28566, -10333, 18233), I(47322, 35484, 41588, -14056, 27532)),
             cf=(col(cfo=36479, cfi=30152, net_change=66631, cash_begin=919068, cash_end=985699), col(cfo=105531, cfi=251010, net_change=-13217, cash_begin=575780, cash_end=562563)), extra=X))
D.append(doc("d9ac88b0", "Q1 2026 interim FS (three-month period ended 2026-03-31, unaudited)", "2026-03-31", "2025-03-31", "Q1", "text layer clean (pdf p4,5,7); p6 equity textless, not read",
             {"bs": 4, "is": 5, "cf": 7}, bs_prior_end="2025-12-31", bs=(B(9075219, 201116, 8874103, 366255, 70757), B(8822747, 200892, 8621855, 399645, 51572)),
             is_=(I(266387, 252003, 254710, -2914, 251796, 252281, -485, 0.38), I(31411, 19739, 28566, -10333, 18233, 18233, 0)),
             cf=(col(cfo=-13800, cfi=-19590, net_change=-33390, cash_begin=399645, cash_end=366255), col(cfo=36479, cfi=30152, net_change=66631, cash_begin=919068, cash_end=985699)), extra=X))
D.append(doc("b81f30d6", "H1 2026 interim FS (six-month period ended 2026-06-30, unaudited; review report dated 29 July 2026)", "2026-06-30", "2025-06-30", "H1",
             "visual: BS, IS and CF pages rendered and read (pdf p4,5,8; text layer scrambled); equity p6-7 text partly garbled, not transcribed", {"bs": 4, "is": 5, "cf": 8}, bs_prior_end="2025-12-31",
             bs=(B(8996297, 190792, 8805505, 297345, 85232), B(8822747, 200892, 8621855, 399645, 51572)),
             is_=(I(228465, 192404, 197598, -4851, 192747, 193809, -1062, 0.29), I(63077, 32774, 51976, -14116, 37860, 37860, 0, 0.05)),
             isq=(I(-37922, -59599, -57112, -1937, -59049, -58472, -577, -0.09), I(31666, 13035, 23410, -3783, 19627, 19627, 0, 0.03)),
             cf=(C(-46795, -45505, -10000, -102300, 399645, 297345), C(91495, 78897, -810463, -640071, 919068, 278997)), extra=X))


def S(p, b, c, k):
    return (p, b, c, k)


R = []
for k in ("net_income", "pbt", "operating_income", "equity_income"):
    R.append(roll(f"Q1 + Q2 2026 = H1 2026 {k}", S("b81f30d6", "is", "cur", k), [S("d9ac88b0", "is", "cur", k), S("b81f30d6", "is_q", "cur", k)]))
    R.append(roll(f"Q1 + Q2 2025 = H1 2025 {k}", S("dacda519", "is", "cur", k), [S("83284b75", "is", "cur", k), S("dacda519", "is_q", "cur", k)]))
    R.append(roll(f"H1 + Q3 2025 = 9M 2025 {k}", S("e0ce5fe2", "is", "cur", k), [S("dacda519", "is", "cur", k), S("e0ce5fe2", "is_q", "cur", k)]))
    R.append(roll(f"9M + Q4 2025 = FY2025 {k}", S("8af24f13", "is", "cur", k), [S("e0ce5fe2", "is", "cur", k), S("989c9047", "is_q", "cur", k)]))
    R.append(roll(f"Q1 + Q2 2024 = H1 2024 {k}", S("dacda519", "is", "prior", k), [S("83284b75", "is", "prior", k), S("dacda519", "is_q", "prior", k)]))
    R.append(roll(f"H1 + Q3 2024 = 9M 2024 {k}", S("e0ce5fe2", "is", "prior", k), [S("dacda519", "is", "prior", k), S("e0ce5fe2", "is_q", "prior", k)]))
    R.append(roll(f"9M + Q4 2024 = FY2024 {k}", S("71e433f7", "is", "cur", k), [S("e0ce5fe2", "is", "prior", k), S("989c9047", "is_q", "prior", k)]))
write("2250", "SIIG (Saudi Industrial Investment Group Company)", "SAR", "SAR thousands (stated on every statement)", D, R)
