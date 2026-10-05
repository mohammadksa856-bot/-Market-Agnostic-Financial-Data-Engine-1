"""Builds transcripts/2084.json (Miahona) from values read from clean text layers and from rendered scan pages viewed in the B020 session. Full SAR throughout."""
from tb import *

X = ["other_income", "rev_plus_oi"]


def I(rev, cost, gp, op, pbt, tax, ni, par=None, nci=None, eps=None, oi=None):
    c = col(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, ni_parent=par, ni_nci=nci, eps=eps, other_income=oi)
    if oi is not None:
        c["rev_plus_oi"] = rev + oi  # derived by the transcript builder from two read values
    return c


def B(ta, tl, te, cash, ppe):
    return col(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe)


def C(cfo, cfi, cff, net, beg, end, capex):
    return col(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=beg, cash_end=end, capex=capex)


def dd(c, **why):
    c = dict(c)
    c["_declared_diff"] = why
    return c


TXT = "text layer clean, tied by arithmetic"
IMG = "visual: scanned pages rendered and read, tied by arithmetic"
D = []
D.append(doc("f0476a54", "FY2025 audited consolidated FS (EY report 16 March 2026; label 2026|FY = publication year); FY2024 comparatives re-presented", "2025-12-31", "2024-12-31", "FY",
             TXT + " (pdf p8-10, 12-13; pdf p7 auditor report page viewed)", {"bs": 8, "is": 9, "cf": "12-13"},
             bs=(B(1684649081, 1205632804, 479016277, 305710999, 8776601), B(1150284034, 704364002, 445920032, 144203173, 6938217)),
             is_=(I(699654359, -585995154, 113659205, 83951077, 82377370, -6615737, 75761633, 72414951, 3346682, 0.45, 12907499),
                  dd(I(385089058, -298631518, 86457540, 54703178, 47429106, -6422028, 41007078, 40726824, 280254, 0.25, 6885469),
                     cost_of_revenue="FY2024 filing as issued shows -292,324,966", gross_profit="FY2024 filing as issued shows 92,764,092",
                     other_income="FY2024 filing as issued shows 578,917 (6,306,552 moved from cost and G&A lines into other income), rev_plus_oi follows")),
             cf=(C(158917989, -238414192, 241004029, 161507826, 144203173, 305710999, -5485713), C(138205461, -186150414, 55981912, 8036959, 136166214, 144203173, -1281508)), extra=X,
             restatements=["FY2024 comparatives re-presented: cost of revenue -292,324,966 -> -298,631,518, gross profit 92,764,092 -> 86,457,540, other income 578,917 -> 6,885,469; operating profit 54,703,178, profit before zakat 47,429,106, net profit 41,007,078 and all cash flow totals unchanged"]))
D.append(doc("f455db46", "FY2024 audited consolidated FS as issued (label 2025|FY = publication year); FY2023 comparatives re-presented", "2024-12-31", "2023-12-31", "FY", TXT + " (pdf p7-9, 11-12)",
             {"bs": 7, "is": 8, "cf": "11-12"},
             bs=(B(1150284034, 704364002, 445920032, 144203173, 6938217), B(989339885, 596101525, 393238360, 136166214, 8413083)),
             is_=(I(385089058, -292324966, 92764092, 54703178, 47429106, -6422028, 41007078, 40726824, 280254, 0.25, 578917),
                  dd(I(324462898, -233514801, 90948097, 70255592, 63256712, -6334598, 56922114, 56718308, 203806, 0.35, 470902),
                     cost_of_revenue="FY2023 filing as issued shows -215,055,671", gross_profit="FY2023 filing as issued shows 109,407,227")),
             cf=(C(138205461, -186150414, 55981912, 8036959, 136166214, 144203173, -1281508),
                 dd(C(113207840, -21770484, -23092528, 68344828, 67821386, 136166214, -2622159),
                    cfo="FY2023 filing as issued shows 132,579,327", cfi="FY2023 filing as issued shows -41,608,343", cff="FY2023 filing as issued shows -22,626,156"))))
D.append(doc("a3f066cc", "FY2023 audited consolidated FS as issued (A Saudi Joint Stock Company - Closed; label 2024|FY = publication year)", "2023-12-31", "2022-12-31", "FY", TXT + " (pdf p7-9, 12-13)",
             {"bs": "7-8", "is": 9, "cf": "12-13"},
             bs=(B(989339885, 596101525, 393238360, 136166214, 8413083), B(963013736, 620508311, 342505425, 67821386, 8445830)),
             is_=(I(324462898, -215055671, 109407227, 70255592, 63256712, -6334598, 56922114, 56718308, 203806, 0.35, 470902),
                  I(276023072, -189164297, 86858775, 56606227, 55459289, -5349242, 50110047, 50110047, 0, 0.31, 1647992)),
             cf=(C(132579327, -41608343, -22626156, 68344828, 67821386, 136166214, -2622159), C(60009671, -51861522, -36205864, -28057715, 95879101, 67821386, -4749099)), extra=X))
D.append(doc("05646437", "FY2022 consolidated FS of Miahona Company Limited (LLC), signed 29 June 2023; whole-file scan (46 of 48 pages textless); label 2024|FY is wrong", "2022-12-31", "2021-12-31", "FY (as originally issued)",
             IMG + " (pdf p5 BS, p6 IS, p9 CF; the BS liabilities totals are not transcribed, see note)", {"bs": 5, "is": 6, "cf": 9},
             bs=(col(total_assets=965436912, total_equity=342505425, cash=103177386, ppe=8445830), col(total_assets=948626104, total_equity=304859937, cash=111235101, ppe=5993186)),
             is_=(I(276023072, -189164297, 86858775, 56606227, 55459289, -5349242, 50110047, oi=1647992), I(255898372, -181542320, 74356052, 33334801, 29751628, -4419776, 25331852, oi=151504)),
             cf=(dd(C(39850677, -11384973, -36523419, -8057715, 111235101, 103177386, -4749099),
                    cfo="the FY2023 filing re-presents 2022 CFO as 60,009,671", cfi="re-presented -51,861,522", cff="re-presented -36,205,864", net_change="re-presented -28,057,715",
                    cash_end="the FY2023 filing shows 67,821,386 (term deposits of 35,356,000 no longer counted as cash)"),
                 C(29740523, -14515947, -32265084, -17040508, 128275609, 111235101, -2911341)), extra=X,
             bs_cur_declared="total assets 965,436,912 here versus 963,013,736 in the FY2023 filing (difference 2,423,176)"))
D[-1]["bs"]["cur"]["_declared_diff"] = {"total_assets": "the FY2023 filing shows 963,013,736 for 2022 (re-presented, difference 2,423,176)"}
D.append(doc("413e7003", "H1 2026 interim FS (six-month period ended 2026-06-30, unaudited)", "2026-06-30", "2025-06-30", "H1", TXT + " (pdf p4-6, 8-9)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2025-12-31",
             bs=(B(1624441396, 1146865895, 477575501, 64849287, 8165529), B(1684649081, 1205632804, 479016277, 305710999, 8776601)),
             is_=(I(233761394, -207271273, 26490121, 10687718, 9988513, -3521040, 6467473, 5475866, 991607, 0.03, 183212), I(361733011, -279275714, 82457297, 75853191, 73767242, -3555506, 70211736, 68779240, 1432496, 0.43, 12709052)),
             isq=(I(116049119, -103298685, 12750434, 4652819, 5192170, -1833279, 3358891, 2845493, 513398, 0.02, 0), I(186560822, -165898698, 20662124, 9927258, 9877559, -1515551, 8362008, 7351586, 1010422, 0.05, -11678)),
             cf=(C(2424038, -241644662, -1641088, -240861712, 305710999, 64849287, -996564), C(70558418, -97930856, 101525134, 74152696, 144203173, 218355869, -4510525)), extra=X))
D.append(doc("98300ac7", "Q1 2026 interim FS (three-month period ended 2026-03-31, unaudited)", "2026-03-31", "2025-03-31", "Q1", TXT + " (pdf p4-5, 8-9)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2025-12-31",
             bs=(B(1623074429, 1133412303, 489662126, 72284285, 8975927), B(1684649081, 1205632804, 479016277, 305710999, 8776601)),
             is_=(I(117712275, -103972588, 13739687, 6034899, 4796343, -1687761, 3108582, 2630373, 478209, 0.02, 183212), I(175172189, -113377016, 61795173, 65925933, 63889683, -2039955, 61849728, 61427654, 422074, 0.38, 12720730)),
             cf=(C(2463144, -211029260, -24860598, -233426714, 305710999, 72284285, -918333), C(78428771, -9616500, 1437802, 70250073, 144203173, 214453246, -3138099)), extra=X))
D.append(doc("3af14a6b", "H1 2025 interim FS (six-month period ended 2025-06-30, unaudited)", "2025-06-30", "2024-06-30", "H1", TXT + " (pdf p4-5, 8-9)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2024-12-31",
             bs=(B(1442033968, 970251820, 471782148, 218355869, 10176451), B(1150284034, 704364002, 445920032, 144203173, 6938217)),
             is_=(I(361733011, -279275714, 82457297, 75853191, 73767242, -3555506, 70211736, 68779240, 1432496, 0.43, 12709052),
                  dd(I(151844695, -115729479, 36115216, 32144180, 30170882, -2088139, 28082743, 27600547, 482196, 0.17, 9351577),
                     cost_of_revenue="H1 2024 filing as issued shows -104,032,573 (11,696,906 moved from G&A)", gross_profit="H1 2024 filing as issued shows 47,812,122")),
             isq=(I(186560822, -165898698, 20662124, 9927258, 9877559, -1515551, 8362008, 7351586, 1010422, 0.05, -11678),
                  dd(I(70240479, -54914365, 15326114, 9038747, 9338972, -1241515, 8097457, 7925646, 171811, 0.05, 1520563),
                     cost_of_revenue="H1 2024 filing as issued shows Q2 2024 cost -51,110,426", gross_profit="H1 2024 filing as issued shows Q2 2024 gross profit 19,130,053")),
             cf=(C(70558418, -97930856, 101525134, 74152696, 144203173, 218355869, -4510525), C(54617960, -75039806, 53113694, 32691848, 136166214, 168858062, -739725)), extra=X))
D.append(doc("ef50f362", "9M 2025 interim FS (nine-month period ended 2025-09-30, unaudited)", "2025-09-30", "2024-09-30", "9M", TXT + " (pdf p4-5, 8-9)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2024-12-31",
             bs=(B(1614490927, 1143320556, 471170371, 260967255, 10263226), B(1150284034, 704364002, 445920032, 144203173, 6938217)),
             is_=(I(536869598, -437510052, 99359546, 83906143, 80897244, -5592916, 75304328, 73342076, 1962252, 0.47, 12709052),
                  dd(I(248079325, -183615346, 64463979, 51906315, 47787951, -2980545, 44807406, 44137077, 670329, 0.28, 7631423),
                     cost_of_revenue="9M 2024 filing as issued shows -167,944,649 (derived, see note) with G&A -34,493,802 (comparatives show -18,823,103)", gross_profit="9M 2024 filing as issued shows 80,134,676",
                     operating_income="9M 2024 filing as issued shows 51,906,313 (2 lower)", pbt="as issued 47,787,949 (2 lower)", net_income="as issued 44,807,404 (2 lower)", ni_parent="as issued 44,137,075 (2 lower)")),
             isq=(I(175136587, -158234338, 16902249, 8052952, 7130002, -2037410, 5092592, 4562836, 529756, 0.03, 0),
                  dd(I(88501460, -67885867, 20615593, 19762135, 17617069, -892406, 16724663, 16536530, 188133, 0.10, 6013016),
                     revenue="9M 2024 filing as issued shows Q3 2024 revenue 88,483,460 (18,000 lower; other income 6,031,016)", cost_of_revenue="as issued -63,912,076", gross_profit="as issued 24,571,384",
                     operating_income="as issued 19,762,133", pbt="as issued 17,617,067", net_income="as issued 16,724,661", ni_parent="as issued 16,536,528", other_income="as issued 6,031,016")),
             cf=(C(97757614, -140449837, 159456305, 116764082, 144203173, 260967255, -5157870), C(90782809, -96690300, 47813363, 41905872, 136166214, 178072086, -1012219)), extra=X))
D.append(doc("7e883d6a", "Q1 2025 interim FS (three-month period ended 2025-03-31, unaudited)", "2025-03-31", "2024-03-31", "Q1", TXT + " (pdf p4-5, 8-9; the investing total line is absent from the page text)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2024-12-31",
             bs=(B(1317761048, 821460754, 496300294, 214453246, 9407953), B(1150284034, 704364002, 445920032, 144203173, 6938217)),
             is_=(I(175172189, -113377016, 61795173, 65925933, 63889683, -2039955, 61849728, 61427654, 422074, 0.38, 12720730), I(81604216, -60815114, 20789102, 23105433, 20831910, -846624, 19985286, 19674901, 310385, 0.12, 7831014)),
             cf=(col(cfo=78428771, cff=1437802, cash_end=214453246), col(cfo=48342843, cff=53403909, cash_end=87801610)), extra=X))
D.append(doc("8c4b7564", "9M 2024 interim FS as issued (nine-month period ended 2024-09-30, unaudited; scanned statement pages p4-9 textless)", "2024-09-30", "2023-09-30", "9M", IMG + " (pdf p4 BS, p5 IS, p6 OCI, p8-9 CF)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2023-12-31",
             bs=(B(1077011151, 657672718, 419338433, 178072086, 7371039), B(989339885, 596101525, 393238360, 136166214, 8413083)),
             is_=(I(248079325, -167944649, 80134676, 51906313, 47787949, -2980545, 44807404, 44137075, 670329, 0.27, 7631423), I(225616990, -146013219, 79603771, 52224740, 48185241, -4189070, 43996171, 43923024, 73147, 0.27, 401624)),
             isq=(I(88483460, -63912076, 24571384, 19762133, 17617067, -892406, 16724661, 16536528, 188133, 0.10, 6031016), I(76003625, -47045430, 28958195, 21625289, 19995292, -1082620, 18912672, 18882822, 29850, 0.12, 209498)),
             cf=(C(90782809, -96690300, 47813363, 41905872, 136166214, 178072086, -1012219), C(77632972, -50331885, -21157007, 6144080, 67821386, 73965466, -2157046)), extra=X,
             cost_note="the 9M cost of revenue digits read (167,944,619) in the scan; revenue minus the printed gross profit 80,134,676 and H1 + Q3 (104,032,573 + 63,912,076) both give 167,944,649, used here"))
D.append(doc("1b2ace76", "H1 2024 interim FS as issued (six-month period ended 2024-06-30, unaudited)", "2024-06-30", "2023-06-30", "H1", TXT + " (pdf p4-5, 8-9)", {"bs": 4, "is": 5, "cf": "8-9"}, bs_prior_end="2023-12-31",
             bs=(B(1095967595, 670403363, 425564232, 168858062, 7793895), B(989339885, 596101525, 393238360, 136166214, 8413083)),
             is_=(I(151844695, -104032573, 47812122, 32144180, 30170882, -2088139, 28082743, 27600547, 482196, 0.17, 9351577), I(149613365, -98967789, 50645576, 30599451, 28189949, -3106450, 25083499, 25040202, 43297, 0.16, 192126)),
             isq=(I(70240479, -51110426, 19130053, 9038747, 9338972, -1241515, 8097457, 7925646, 171811, 0.05, 1520563), I(84545878, -52208960, 32336918, 20072688, 18725584, -1735802, 16989782, 16946485, 43297, 0.11, -67510)),
             cf=(C(54617960, -75039806, 53113694, 32691848, 136166214, 168858062, -739725), C(56330007, -49638246, -2764767, 3926994, 67821386, 71748380, -1376396)), extra=X))


def S(p, b, c, k):
    return (p, b, c, k)


R = []
ALL = ("revenue", "cost_of_revenue", "gross_profit", "operating_income", "pbt", "tax", "net_income", "ni_parent", "ni_nci")
for k in ALL:
    R.append(roll(f"Q1 + Q2 2026 = H1 2026 {k}", S("413e7003", "is", "cur", k), [S("98300ac7", "is", "cur", k), S("413e7003", "is_q", "cur", k)]))
    R.append(roll(f"Q1 + Q2 2025 = H1 2025 {k}", S("3af14a6b", "is", "cur", k), [S("7e883d6a", "is", "cur", k), S("3af14a6b", "is_q", "cur", k)]))
    R.append(roll(f"H1 + Q3 2025 = 9M 2025 {k}", S("ef50f362", "is", "cur", k), [S("3af14a6b", "is", "cur", k), S("ef50f362", "is_q", "cur", k)]))
    R.append(roll(f"H1 2023 + Q3 2023 = 9M 2023 {k}", S("8c4b7564", "is", "prior", k), [S("1b2ace76", "is", "prior", k), S("8c4b7564", "is_q", "prior", k)]))
for k in ("revenue", "operating_income", "pbt", "tax", "net_income", "ni_parent", "ni_nci"):
    R.append(roll(f"Q1 2024 (Q1 2025 comparatives) + Q2 2024 = H1 2024 {k}", S("1b2ace76", "is", "cur", k), [S("7e883d6a", "is", "prior", k), S("1b2ace76", "is_q", "cur", k)]))
for k in ("cost_of_revenue", "operating_income", "pbt", "tax", "net_income", "ni_parent", "ni_nci", "rev_plus_oi"):
    R.append(roll(f"H1 2024 + Q3 2024 = 9M 2024 (own filings) {k}", S("8c4b7564", "is", "cur", k), [S("1b2ace76", "is", "cur", k), S("8c4b7564", "is_q", "cur", k)]))
write("2084", "MIAHONA (Miahona Company)", "SAR", "full SAR (no scaling) in every filing read", D, R,
      notes=["9M 2024 own filing: revenue 248,079,325 does not equal H1 151,844,695 + Q3 88,483,460 (difference 7,751,170) because the nine-month column moves 7,751,170 from other income into revenue while the Q3 column does not; revenue plus other income ties exactly (rev_plus_oi roll)."])
