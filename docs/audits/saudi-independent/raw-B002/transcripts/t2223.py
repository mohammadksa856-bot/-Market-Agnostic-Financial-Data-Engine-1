# LUBEREF (2223) page transcriptions. Units SAR thousands. Statement pages of the annual files and of the 2026 interims are
# image-only (embedded scans): read by eye from rendered pages; arithmetic re-added.
T = [
 dict(sha="4eed9d642043", true_period="FY2025 (2025-12-31) with FY2024 comparatives", collector_label="2026|FY",
  identity="SAUDI ARAMCO BASE OIL COMPANY - LUBEREF, Saudi joint stock company, standalone annual FS with auditor report", units="SAR thousands; EPS SAR",
  read="rendered images pdf p7,8,10,11 read by eye (statements are image-only pages; p9 statement of changes in equity NOT read)",
  statements=[
   dict(name="financial_position", pdf_page=7, printed_page=5, values={"total_assets":(7606399,7739247),"total_non_current_assets":(5102794,4903137),"total_current_assets":(2503605,2836110),"cash":(987383,735171),"short_term_deposits":(385763,452304),"total_equity":(4582446,4397459),"total_liabilities":(3023953,3341788)},
     checks=[("nca",[4917823,143535,26567,14869],5102794),("ca",[643757,415563,71139,385763,987383],2503605),("ta",[5102794,2503605],7606399),("eq",[1687500,0,-48682,2943628],4582446),("ncl",[651304,133831,349599,47059,505],1182298),("cl",[1414269,238806,133867,30061,24652],1841655),("tl",[1182298,1841655],3023953),("le",[4582446,3023953],7606399),("ta24",[4903137,2836110],7739247),("eq24",[1687500,506250,-49238,2252947],4397459)]),
   dict(name="profit_or_loss_and_oci", pdf_page=8, printed_page=6, values={"revenue":(8103355,10035854),"gross_profit":(1178772,1335625),"operating_profit":(890432,1000645),"profit_before_zakat":(873935,988413),"zakat_and_income_tax":(-18620,-16385),"net_income":(855315,972028),"total_comprehensive_income":(870917,975659),"eps_sar":(5.08,5.78)},
     checks=[("gp",[8103355,-6924583],1178772),("op",[1178772,-36285,-252903,1409,-561],890432),("pbz",[890432,46649,-63146],873935),("ni",[873935,-18620],855315),("tci",[855315,15602],870917),("gp24",[10035854,-8700229],1335625),("op24",[1335625,-64210,-281252,-1500,11982],1000645)]),
   dict(name="cash_flows", pdf_page=10, printed_page=8, values={"cfo":(1517527,1808476),"cfi":(-378009,976551),"cff":(-887306,-2595816),"net_change":(252212,189211),"cash_end":(987383,735171),"capex_ppe":(-429287,-196595),"dividends_paid":(-686486,-1446993)},
     checks=[("cfi",[-429287,112,-15141,-706168,773233,4903,-5661],-378009),("cff",[-116304,-686486,-22316,-9063,-53137],-887306),("net",[1517527,-378009,-887306],252212),("cash",[735171,252212],987383),("cfo",[1517381,43500,-17566,-25788],1517527),("cfo24",[1793376,93019,-14027,-63892],1808476)]),
  ], observations=["Statutory reserve 506,250 (2024) is nil at 2025-12-31 (transferred to retained earnings; see changes-in-equity page, not read). Cash flow spans two image pages (pdf p10-11). FY2024 CF comparatives are regrouped vs the FY2024 original (lease finance cost 7,155 shown separately; depreciation split) with the same totals."]),
 dict(sha="c059af6fe42a", true_period="H1 2026 (six months to 2026-06-30; Q2-2026 column)", collector_label="2026|H1",
  identity="LUBEREF condensed interim FS (unaudited, review report)", units="SAR thousands", read="rendered images pdf p4,5,7 read by eye (p6 changes in equity NOT read; statements are image pages)",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(9600726,7606399),"total_equity":(4967791,4582446),"total_liabilities":(4632935,3023953),"cash":(1602019,987383)},
     checks=[("nca",[5063830,173303,23702,13592],5274427),("ca",[825683,1717096,33857,147644,1602019],4326299),("eq",[1687500,-48190,3328481],4967791),("tl",[1179679,3453256],4632935),("le",[4967791,4632935],9600726)]),
   dict(name="profit_or_loss_and_oci", pdf_page=5, printed_page=3, values={"revenue_q2":(3418578,2249108),"revenue_h1":(5576985,4377066),"gross_profit_h1":(1185283,607829),"operating_profit_h1":(1011771,483481),"profit_before_zakat_h1":(1017664,475424),"net_income_h1":(992065,466705),"net_income_q2":(734097,245197),"eps_h1":(5.90,2.77),"eps_q2":(4.36,1.46)},
     checks=[("gp",[5576985,-4391702],1185283),("op",[1185283,-20850,-114699,-37963],1011771),("pbz",[1011771,28690,-22797],1017664),("ni",[1017664,-25599],992065),("q2",[3418578,-2561576],857002),("oci",[992065,-18299],973766)]),
   dict(name="cash_flows", pdf_page=7, printed_page=5, values={"cfo":(1366387,458925),"cfi":(-64521,132295),"cff":(-687230,-611170),"net_change":(614636,-19950),"cash_end":(1602019,715221)},
     checks=[("net",[1366387,-64521,-687230],614636),("cash",[987383,614636],1602019),("cfi",[-302229,-146769,383084,2221,-828],-64521),("cff",[-63967,-588913,-12299,-5097,-16954],-687230)]),
  ], observations=["Q1 2026 NI 257,968 + Q2 734,097 = H1 992,065 (reconciled to a0a0c75c). Q1 dividend payable 588,913 (note 16) paid in Q2 = H1 dividends paid. Retained earnings 2,616,584 (Q1) + 734,097 - 22,200 OCI = 3,328,481 (H1)."]),
 dict(sha="a0a0c75c", true_period="Q1 2026 (three months to 2026-03-31)", collector_label="2026|Q1",
  identity="LUBEREF condensed interim FS (unaudited), English; the same quarter also exists as dc221bc3 (Arabic translation from issuer site, Arabic-Indic digits)", units="SAR thousands", read="rendered images pdf p4,5,7 read by eye",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(8818411,7606399),"total_equity":(4255402,4582446),"total_liabilities":(4563009,3023953),"cash":(1006479,987383)}, checks=[("le",[4255402,4563009],8818411),("eq",[1687500,-48682,2616584],4255402)]),
   dict(name="profit_or_loss_and_oci", pdf_page=5, printed_page=3, values={"revenue":(2158407,2127958),"gross_profit":(328281,287547),"operating_profit":(263305,226344),"profit_before_zakat":(264618,225091),"net_income":(257968,221508),"eps_sar":(1.53,1.32)}, checks=[("gp",[2158407,-1830126],328281),("op",[328281,-7977,-49911,-7088],263305),("ni",[264618,-6650],257968)]),
   dict(name="cash_flows", pdf_page=7, printed_page=5, values={"cfo":(193754,400242),"cfi":(-152910,-107000),"cff":(-21748,-17061),"net_change":(19096,276181),"cash_end":(1006479,1011352)}, checks=[("net",[193754,-152910,-21748],19096),("cash",[987383,19096],1006479)]),
  ], observations=["Arabic copy dc221bc3 checked visually (pdf p1,4,5): same figures (total assets 8,818,411; profit 257,968) - a translation duplicate of the same period, not a separate period."]),
 dict(sha="15ef1d81", true_period="FY2024 (2024-12-31) with FY2023 comparatives", collector_label="2025|FY", identity="LUBEREF annual FS", units="SAR thousands", read="rendered images pdf p7,8,10 read by eye",
  statements=[
   dict(name="financial_position", pdf_page=7, printed_page=6, values={"total_assets":(7739247,8856470),"total_equity":(4397459,4868793),"total_liabilities":(3341788,3987677),"cash":(735171,545960)}, checks=[("le",[4397459,3341788],7739247),("le23",[4868793,3987677],8856470)]),
   dict(name="profit_or_loss_and_oci", pdf_page=8, printed_page=7, values={"revenue":(10035854,9488679),"net_income":(972028,1509612),"total_comprehensive_income":(975659,1460347),"eps_sar":(5.78,8.98)}, checks=[("gp",[10035854,-8700229],1335625),("tci",[972028,3631],975659)]),
   dict(name="cash_flows", pdf_page=10, printed_page=9, values={"cfo":(1808476,2321626),"cfi":(976551,-1690985),"cff":(-2595816,-1996759),"net_change":(189211,-1366118),"cash_end":(735171,545960)}, checks=[("net",[1808476,976551,-2595816],189211),("cash",[545960,189211],735171)]),
  ], observations=["Values equal the FY2024 comparative column of the FY2025 file (no restatement); only CF line grouping differs."]),
]
