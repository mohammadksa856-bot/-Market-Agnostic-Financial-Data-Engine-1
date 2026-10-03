# Transcription of headline values read from the original pages (text layer of born-digital PDFs, cross-checked by arithmetic).
# Units: SAR thousands. Sign: as printed (outflows negative). Each check = parts sum to total.
T = [
 dict(sha="02f1136204a7", true_period="FY2025 (2025-12-31) with FY2024 comparatives", collector_label="2026|FY",
  identity="YANBU NATIONAL PETROCHEMICAL COMPANY (YANSAB), Saudi joint stock company; standalone annual financial statements; auditor report included",
  units="All amounts in thousands of Saudi Riyals; EPS in SAR", read="text-layer, all statement pages (pdf p8-12); arithmetic re-added",
  statements=[
   dict(name="financial_position", pdf_page=8, printed_page=7, values={"total_assets":(13259624,14124175),"total_non_current_assets":(7993040,8443876),"total_current_assets":(5266584,5680299),"cash":(174601,97708),"short_term_investments":(2341194,3041380),"total_equity":(10748845,11236659),"total_liabilities":(2510779,2887516)},
     checks=[("assets",[7993040,5266584],13259624),("assets_2024",[8443876,5680299],14124175),("nca",[7403285,81878,7286,310626,189965],7993040),("ca",[688936,1495202,256452,310199,2341194,174601],5266584),("equity",[5625000,257608,4866237],10748845),("liab",[1087855,1422924],2510779),("le",[10748845,2510779],13259624)]),
   dict(name="income", pdf_page=9, printed_page=8, values={"revenue":(5601167,6160538),"gross_profit":(646428,954086),"operating_income":(63406,403733),"income_before_zakat":(169022,498470),"zakat":(-89924,-78136),"net_income":(79098,420334),"eps_sar":(0.14,0.75)},
     checks=[("gp",[5601167,-4954739],646428),("op",[646428,-151491,-437031,32920,-27420],63406),("pbt",[63406,164019,-58403],169022),("ni",[169022,-89924],79098),("ni24",[498470,-78136],420334)]),
   dict(name="comprehensive_income", pdf_page=10, printed_page=9, values={"total_comprehensive_income":(74686,460856),"oci":(-4412,40522)}, checks=[("tci",[79098,-4412],74686)]),
   dict(name="changes_in_equity", pdf_page=11, printed_page=10, values={"closing_equity_2025":10748845,"dividends_2025":-562500,"dividends_2024":-1125000}, checks=[("eq",[11236659,74686,-562500],10748845)]),
   dict(name="cash_flows", pdf_page=12, printed_page=11, values={"cfo":(1218789,1593181),"cfi":(-14990,-952405),"cff":(-1126906,-993205),"net_change":(76893,-352429),"cash_end":(174601,97708),"capex_ppe":(-379028,-267738),"dividends_paid":(-1126215,-984973)},
     checks=[("net",[1218789,-14990,-1126906],76893),("cash",[97708,76893],174601),("cfi",[-5025685,5714585,-379028,-499968,175106],-14990),("cff",[-691,-1126215],-1126906)]),
  ], observations=["Cash end 174,601 = SOFP cash (note 14). Standalone company, no consolidation. No discontinued operations. FY2024 comparatives equal the FY2024 original (checked)."]),
 dict(sha="92b22cbe379b", true_period="H1 2026 (six months to 2026-06-30; quarter column Q2-2026)", collector_label="2026|H1",
  identity="YANSAB condensed interim financial statements, review report", units="SAR thousands", read="text-layer pdf p4-8; arithmetic re-added; Q2 = H1 - Q1 reconciled",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=3, values={"total_assets":(13236141,13259624),"total_equity":(10468495,10748845),"total_liabilities":(2767646,2510779),"cash":(561691,174601)}, checks=[("assets",[7779038,5457103],13236141),("le",[10468495,2767646],13236141)]),
   dict(name="income", pdf_page=5, printed_page=4, values={"revenue_q2":(1878881,1393932),"revenue_h1":(3199011,2905994),"net_income_q2":(258814,44552),"net_income_h1":(270043,58218),"income_before_zakat_h1":(319888,107236),"eps_h1":(0.48,0.10)}, checks=[("h1ni",[319888,-49845],270043),("q2ni",[287836,-29022],258814)]),
   dict(name="comprehensive_income", pdf_page=6, printed_page=5, values={"tci_h1":(282150,61709)}, checks=[("tci",[270043,12107],282150)]),
   dict(name="cash_flows", pdf_page=8, printed_page=7, values={"cfo_h1":(215740,485554),"cfi_h1":(734023,282677),"cff_h1":(-562673,-564848),"cash_end":(561691,301091)}, checks=[("net",[215740,734023,-562673],387090),("cash",[174601,387090],561691)]),
  ], observations=["Includes impairment of PP&E 104,270 (note 4) in H1/Q2 other operating expenses. Q1 2026 NI 11,229 + Q2 258,814 = H1 270,043 (cross-document check vs 420bab2a)."]),
 dict(sha="420bab2a", true_period="Q1 2026 (three months to 2026-03-31)", collector_label="2026|Q1", identity="YANSAB condensed interim FS", units="SAR thousands", read="text-layer pdf p4,5,7,8 key lines",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=3, values={"total_assets":(12775298,13259624),"total_equity":(10173384,10748845),"cash":(220262,174601)}, checks=[("le",[10173384,2601914],12775298)]),
   dict(name="income", pdf_page=5, printed_page=4, values={"revenue":(1320130,1512062),"net_income":(11229,13666),"income_from_operations":(12175,7968)}, checks=[]),
   dict(name="cash_flows", pdf_page=8, printed_page=7, values={"cfo":(206790,274077),"cfi":(397227,292612),"cash_end":(220262,103173)}, checks=[("cash",[174601,45661],220262)]),
  ], observations=["Dividends paid Q1 (557,829) - declared 562,500 per statement of changes in equity."]),
 dict(sha="d37eba16", true_period="FY2024 (2024-12-31) with FY2023 comparatives", collector_label="2024|FY (duplicate text: 0bd45a56 labelled 2025|FY)", identity="YANSAB annual FS", units="SAR thousands", read="text-layer key lines pdf p7-11",
  statements=[
   dict(name="financial_position", pdf_page=7, printed_page=6, values={"total_assets":(14124175,14781886),"total_equity":(11236659,11900803),"total_liabilities":(2887516,2881083)}, checks=[("le",[11236659,2887516],14124175)]),
   dict(name="income", pdf_page=8, printed_page=7, values={"gross_profit":(954086,-53365),"net_income":(420334,-485144)}, checks=[]),
   dict(name="comprehensive_income", pdf_page=9, printed_page=8, values={"tci":(460856,-462550)}, checks=[]),
   dict(name="cash_flows", pdf_page=11, printed_page=10, values={"cfo":(1593181,971622),"cfi":(-952405,520807),"cff":(-993205,-1274782),"cash_end":(97708,450137)}, checks=[("net",[1593181,-952405,-993205],-352429)]),
  ], observations=["All FY2024 values equal the FY2024 comparative column in the FY2025 file (no restatement)."]),
 dict(sha="fac312f6", true_period="FY2023 (2023-12-31) with FY2022 comparatives", collector_label="2023|FY (duplicate text: 7846fe50 labelled 2024|FY)", identity="YANSAB annual FS", units="SAR thousands", read="text-layer key lines pdf p8-12",
  statements=[
   dict(name="financial_position", pdf_page=8, printed_page=7, values={"total_assets":(14781886,16679591),"total_equity":(11900803,14050853),"total_liabilities":(2881083,2628738)}, checks=[("le",[11900803,2881083],14781886)]),
   dict(name="comprehensive_income", pdf_page=10, printed_page=9, values={"tci":(-462550,695962)}, checks=[]),
   dict(name="cash_flows", pdf_page=12, printed_page=11, values={"cfo":(971622,1872729),"cfi":(520807,-261267),"cff":(-1274782,-1708323),"cash_end":(450137,232490),"capex":(-918404,-427984)}, checks=[("net",[971622,520807,-1274782],217647)]),
  ], observations=["FY2023 net loss (485,144) per FY2024 comparative column; FY2023 SOI page (pdf p9) not line-read in this file, total-comprehensive-loss (462,550) read."]),
 dict(sha="8a16842a", true_period="FY2022 (2022-12-31) with FY2021 comparatives", collector_label="2023|FY", identity="YANSAB annual FS (pdf p3-6 image-only: auditor report scan; statements text)", units="SAR thousands", read="text-layer key lines pdf p7-8",
  statements=[
   dict(name="financial_position", pdf_page=7, printed_page=None, values={"total_assets":(16679591,18160910),"total_equity":(14050853,15042391)}, checks=[("le",[14050853,2628738],16679591)]),
   dict(name="income", pdf_page=8, printed_page=None, values={"gross_profit":(970422,2245868),"income_before_zakat":(555392,1728701),"net_income":(414145,1531299)}, checks=[]),
   dict(name="comprehensive_income", pdf_page=9, printed_page=None, values={"tci":(695962,1603809)}, checks=[]),
  ], observations=["Cash flow statement of FY2022 not line-read (FY2022 cash movement visible in FY2023 file comparatives: cfo 1,872,729)."]),
]
