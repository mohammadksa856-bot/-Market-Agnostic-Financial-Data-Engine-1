# BAWAN (1302) page transcriptions, SAR thousands, consolidated. Statements of the annual files and interims are
# partly image-only pages (read by eye) and partly text layer. Arithmetic re-added.
T = [
 dict(sha="10bb47c75c85", true_period="FY2025 (2025-12-31) with FY2024 comparatives (restated, note 38)", collector_label="2026|FY",
  identity="BAWAN COMPANY (Saudi joint stock company), consolidated FS, EY audit report dated 5 April 2026", units="Saudi Riyals thousands",
  read="SOFP pdf p11 and cash-flow tail pdf p16 read by eye (image pages); SOPL pdf p12 and CF pdf p15 from text layer; SOCI embedded in SOPL; changes-in-equity page NOT read",
  statements=[
   dict(name="financial_position", pdf_page=11, printed_page=9, values={"total_assets":(3810359,2597898),"total_non_current_assets":(1262773,736567),"total_current_assets":(2547586,1861331),"cash":(82936,424913),"total_equity":(1126778,961470),"equity_owners":(1090040,928786),"nci":(36738,32684),"total_liabilities":(2683581,1636428)},
     checks=[("nca",[800653,72633,4397,321535,49377,14178],1262773),("ca",[993461,34154,0,1138854,18750,279431,82936],2547586),("ta",[1262773,2547586],3810359),("eq",[600000,69440,-58746,479346],1090040),("te",[1090040,36738],1126778),("ncl",[469065,196255,56465,105651],827436),("cl",[754510,781332,75000,54708,140060,14253,35341,941],1856145),("tl",[827436,1856145],2683581),("le",[1126778,2683581],3810359)]),
   dict(name="profit_or_loss_and_oci", pdf_page=12, printed_page=10, values={"revenue":(4069650,3020204),"gross_profit":(554343,333896),"profit_before_zakat":(253309,127437),"net_income":(206005,111806),"net_income_owners":(218299,106032),"net_income_nci":(-12294,5774),"total_comprehensive_income":(193391,112602)},
     checks=[("gp",[4069650,-3515307],554343),("ebit",[554343,-89657,-215480,-13695,2233,0,126452,1824],366020),("pbt",[366020,-112711],253309),("ni",[253309,-47304],206005),("attr",[218299,-12294],206005),("tci",[206005,-12614],193391)]),
   dict(name="cash_flows", pdf_page=15, printed_page=13, values={"cfo":(160288,134960),"cfi":(-301895,-106836),"cff":(-197715,365201),"net_change":(-339322,393325),"cash_end":(82936,30543)},
     checks=[("cfo",[337905,-107265,-58675,-11677],160288),("cfi",[-85405,-4364,-16508,20967,16775,-158360,-75000],-301895),("cff",[1967646,-2066091,121035,-128354,-12816,-75000,-4135],-197715),("net",[160288,-301895,-197715],-339322),("cash",[30543,-339322,394370,-2655],82936)]),
  ], observations=["CF printed label 'Net cash (generated from) / used in financing activities' is inverted for 2025: the figure (197,715) is an outflow by arithmetic. Bargain purchase gain 126,452 (business combination) inflates 2025 profit; Depreciation and amortization 209,593 vs 63,543 reflects acquisition. FY2024 comparative restated by reclassification (gross profit 333,896 vs 368,971 original) with identical profit 111,806. Cash flow shows cash excluding 394,370 restricted balance at 2024-01 transition."]),
 dict(sha="dbc5176629fa", true_period="H1 2026 (six months to 2026-06-30; Q2-2026 column); 2025 comparatives restated (note 17)", collector_label="2026|H1",
  identity="Bawan Company interim condensed consolidated FS (unaudited), review report", units="Saudi riyals thousands",
  read="SOFP pdf p4 (text) + p5 (image), SOPL pdf p6 (image), CF pdf p8 (text, note: negatives extracted as ')x(') + p9 (image); changes-in-equity NOT read",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(3761818,3810359),"total_equity":(1200187,1126778),"total_liabilities":(2561631,2683581),"cash":(162123,82936)},
     checks=[("nca",[804554,80512,4397,253624,32547,2081],1177715),("ca",[943269,33308,1080936,18746,345721,162123],2584103),("ta",[1177715,2584103],3761818),("eq",[600000,69440,-92364,585213],1162289),("te",[1162289,37898],1200187),("ncl",[471738,136048,64888,109957],782631),("cl",[675467,739712,68388,67825,177706,15344,33617,941],1779000),("le",[1200187,2561631],3761818)]),
   dict(name="profit_or_loss_and_oci", pdf_page=6, printed_page=4, values={"revenue_q2":(970519,966143),"revenue_h1":(2001842,1876321),"net_income_q2":(48646,35725),"net_income_h1":(91667,185302),"eps_h1":(1.76,3.02),"net_income_owners_h1":(105867,181043),"net_income_nci_h1":(-14200,4259)},
     checks=[("gp",[2001842,-1675839],326003),("pbt",[115260,-23593],91667),("attr",[105867,-14200],91667),("tci",[91667,-229],91438)]),
   dict(name="cash_flows", pdf_page=8, printed_page=6, values={"cfo":(229121,116224),"cfi":(-119725,-187903),"cff":(-30170,-235564),"net_change":(79226,-307243),"cash_end":(162123,114742)},
     checks=[("cfi",[-45722,-3472,4362,-581,688,-75000],-119725),("cff",[685830,-727138,-17895,31382,18750,-6965,-14134],-30170),("net",[229121,-119725,-30170],79226),("cash",[82936,79226,-39],162123)]),
  ], observations=["H1 2025 comparative is RESTATED (note 17): net profit 185,302 vs 99,208 as originally reported in 5cd5d2e5 (bargain purchase gain 126,452 recognised retrospectively on the PPA); H1 2025 original total assets 3,637,718 / equity 1,058,613. Q1 2026 NI 43,021 + Q2 48,646 = H1 91,667 reconciled. Interim PDF text layer prints negatives as ')x(' (reversed brackets) in the cash-flow pages: a sign hazard for text parsers."]),
 dict(sha="297d068f", true_period="Q1 2026 (three months to 2026-03-31); Q1 2025 restated (note 17)", collector_label="2026|Q1", identity="Bawan interim condensed consolidated FS (unaudited)", units="SAR thousands",
  read="SOPL pdf p6 image read by eye; SOFP/CF totals from text lines pdf p4,p8",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(3963270,3810359),"total_equity":(1161509,1126778)}, checks=[]),
   dict(name="profit_or_loss_and_oci", pdf_page=6, printed_page=4, values={"revenue":(1031323,910178),"gross_profit":(156341,103951),"profit_before_zakat":(56856,153433),"net_income":(43021,149577),"eps_sar":(0.87,2.49)}, checks=[("gp",[1031323,-874982],156341),("ni",[56856,-13835],43021)]),
   dict(name="cash_flows", pdf_page=8, printed_page=6, values={"cfo":(82255,-29339),"cfi":(-20542,-171423)}, checks=[]),
  ], observations=["Q1 2025 comparative restated (net profit 149,577); original Q1 2025 file 24bf0038 not value-read."]),
 dict(sha="9a3cc2116", true_period="FY2024 (2024-12-31) with FY2023 comparatives", collector_label="2025|FY", identity="Bawan consolidated annual FS", units="SAR thousands", read="rendered images pdf p7,8,11,12 read by eye",
  statements=[
   dict(name="financial_position", pdf_page=7, printed_page=5, values={"total_assets":(2597898,2164010),"total_equity":(961470,960818),"total_liabilities":(1636428,1203192),"cash":(424913,31588)}, checks=[("le",[961470,1636428],2597898),("le23",[960818,1203192],2164010)]),
   dict(name="profit_or_loss_and_oci", pdf_page=8, printed_page=6, values={"revenue":(3020204,3351813),"gross_profit":(368971,385734),"net_income":(111806,145090),"profit_continuing":(111806,147575)}, checks=[("gp",[3020204,-2651233],368971),("ni",[127437,-15631],111806)]),
   dict(name="cash_flows", pdf_page=11, printed_page=9, values={"cfo":(134960,286544),"cfi":(-106836,-75698),"cff":(365201,-211579),"cash_end":(30543,31588)}, checks=[("net",[134960,-106836,365201],393325),("cash",[31588,393325,-394370],30543)]),
  ], observations=["FY2023 includes discontinued operations (loss 2,485). In the FY2025 file the FY2024 gross profit is restated to 333,896 (reclassification of 35,075 from selling/COGS; net profit unchanged)."]),
]
