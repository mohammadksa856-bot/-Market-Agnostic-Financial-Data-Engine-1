# ALRAJHI TAKAFUL (8230) = Al Rajhi Company for Cooperative Insurance. SAR thousands. Insurance (IFRS 17) presentation from 2023.
# All primary statement pages of every file are image-only pages inside otherwise text PDFs: read by eye from renders.
T = [
 dict(sha="b6b4d528b5c0", true_period="FY2025 (2025-12-31) with FY2024 comparatives", collector_label="2026|FY",
  identity="Al Rajhi Company for Cooperative Insurance (A Saudi Joint Stock Company); standalone annual FS with auditors review report", units="Saudi Riyal in 000",
  read="rendered images pdf p8 (SOFP), p9 (SOI), p12 (SOCF) read by eye; p10 SOCI and p11 SOCE NOT read",
  statements=[
   dict(name="financial_position", pdf_page=8, printed_page=6, values={"total_assets":(14183992,12087407),"total_liabilities":(11648301,10006982),"total_equity":(2535691,2080425),"cash":(582152,720981),"investment_for_unit_linked_contracts":(8374752,6289550),"insurance_contract_liabilities":(10851359,9765345)},
     checks=[("ta",[582152,1701060,283951,2023623,8374752,5366,640261,107500,99988,6150,29653,286352,43184],14183992),("tl",[187422,10851359,717,508823,35145,27429,6150,31256],11648301),("eq",[1000000,440482,1022233,-35671,6589,-7682,109740],2535691),("le",[2535691,11648301],14183992),("ta24",[720981,1333001,254733,2413516,6289550,4,674669,59108,99974,3357,37485,165515,35514],12087407),("tl24",[116457,9765345,15479,0,33050,34502,3357,38792],10006982),("eq24",[1000000,349486,658248,0,0,-7831,80522],2080425)]),
   dict(name="income", pdf_page=9, printed_page=7, values={"insurance_revenue":(5322128,5391459),"insurance_service_result":(489402,221992),"net_investment_income":(-358856,605063),"net_income_before_zakat":(468866,329313),"zakat":(-13885,3030),"net_income_after_zakat":(454981,332343),"eps_sar":(4.55,3.32)},
     checks=[("isr_pre",[5322128,-4518812],803316),("nr",[-419092,105178],-313914),("isr",[803316,-313914],489402),("nif",[472214,24771],496985),("nii",[86243,128678,-573791,14],-358856),("nibz",[489402,496985,-358856,-160683,2018],468866),("ni",[468866,-13885],454981)]),
   dict(name="cash_flows", pdf_page=12, printed_page=10, values={"cfo":(-384954,-454676),"cfi":(296877,248532),"cff":(-45138,-8879),"net_change":(-133215,-215023),"cash_end":(552564,685779)},
     checks=[("pre_wc",[468866,12891,6014,7068,764,-14,6589,1931,-54396,-2852,9816],456677),("wc",[-365207,-2085202,-5362,34408,-48392,-2793,70965,1086014,-14762,508823,5614,2793],-813101),("cfo",[456677,-813101,-20958,-7572],-384954),("cfi",[-60923,60923,-1171003,1615292,-133728,-13684],296877),("cff",[-35671,-9467],-45138),("net",[-384954,296877,-45138],-133215),("cash",[685779,-133215],552564)]),
  ], observations=["Cash flow end-of-year cash 552,564 differs from SOFP cash and bank balances 582,152 by 29,588 (deposits against guarantees/statutory income; note 4, not read). Share capital 1,000,000 (thousand) FY2025; 2,000,000 at 2026-06-30 after a bonus issue, so EPS is restated on 200,000 thousand shares in 2026 interims (H1-2026 EPS 1.04; Q1-2026 EPS as first reported 1.14 on 100,000 thousand shares). Net investment income negative in 2025 because unit-linked fair value result (573,791) loss offsets insurance finance income; sign hazard for any 'investment income' mapping."]),
 dict(sha="c59c3d27b4c4", true_period="H1 2026 (three and six months to 2026-06-30)", collector_label="2026|H1",
  identity="Al Rajhi Company for Cooperative Insurance interim condensed FS (unaudited), review report dated 09 August 2026", units="Saudi Riyal in 000",
  read="rendered images pdf p4 (SOFP), p5 (SOI), p8 (SOCF) read by eye; p6 SOCI and p7 SOCE NOT read",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(14668237,14183992),"total_liabilities":(11888149,11648301),"total_equity":(2780088,2535691),"share_capital":(2000000,1000000),"cash":(571840,582152)},
     checks=[("ta",[571840,2249052,306285,1609855,8027421,168972,936070,210093,199988,8598,39603,298136,42324],14668237),("tl",[275291,11014181,238,492329,38471,24649,8598,34392],11888149),("eq",[2000000,440482,230070,-35671,6589,-7682,146300],2780088),("le",[2780088,11888149],14668237)]),
   dict(name="income", pdf_page=5, printed_page=3, values={"insurance_revenue_q2":(1531587,1380212),"insurance_revenue_h1":(3036817,2586118),"net_income_after_zakat_q2":(94336,111568),"net_income_after_zakat_h1":(207837,202365),"eps_h1_restated":(1.04,1.01),"weighted_shares_thousand":(200000,200000)},
     checks=[("h1",[214264,-6427],207837),("q2",[97533,-3197],94336),("isr",[3036817,-3049110],-12293)]),
   dict(name="cash_flows", pdf_page=8, printed_page=6, values={"cfo":(-321564,-179217),"cfi":(320366,160947),"cff":(-11780,-8270),"net_change":(-12978,-26540),"cash_end":(539586,659239)},
     checks=[("net",[-321564,320366,-11780],-12978),("cash",[552564,-12978],539586)]),
  ], observations=["Q1 2026 NI 113,501 + Q2 94,336 = H1 207,837 (reconciled against 73fc5e0c). Share capital doubled to 2,000,000 with retained earnings falling 1,022,233 -> 230,070 (bonus issue; statutory reserve unchanged). Cash-flow end cash 539,586 vs SOFP 571,840."]),
 dict(sha="73fc5e0c09a1", true_period="Q1 2026 (three months to 2026-03-31)", collector_label="2026|Q1", identity="Al Rajhi Company for Cooperative Insurance interim condensed FS (unaudited)", units="Saudi Riyal in 000",
  read="rendered images pdf p4, p5, p8 read by eye",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(13940827,14183992),"total_liabilities":(11271075,11648301),"total_equity":(2669752,2535691),"cash":(407851,582152)}, checks=[("le",[2669752,11271075],13940827)]),
   dict(name="income", pdf_page=5, printed_page=3, values={"insurance_revenue":(1505230,1205906),"net_income_after_zakat":(113501,90797),"eps_sar":(1.14,0.91)}, checks=[("ni",[116731,-3230],113501)]),
   dict(name="cash_flows", pdf_page=8, printed_page=6, values={"cfo":(-330328,-217833),"cfi":(161855,209059),"cff":(-5076,-2387),"cash_end":(379015,674618)}, checks=[("net",[-330328,161855,-5076],-173549),("cash",[552564,-173549],379015)]),
  ], observations=["EPS 1.14 is on 100,000 thousand shares (pre-bonus); H1-2026 file restates per-share data on 200,000 thousand shares."]),
 dict(sha="e3067ae108fc", true_period="FY2024 (2024-12-31) with FY2023 comparatives (IFRS 17)", collector_label="2025|FY", identity="Al Rajhi Company for Cooperative Insurance annual FS", units="SAR '000",
  read="rendered images pdf p8 (SOFP), p9 (SOI) read by eye",
  statements=[
   dict(name="financial_position", pdf_page=8, printed_page=6, values={"total_assets":(12087407,6824187),"total_liabilities":(10006982,5101401),"total_equity":(2080425,1722786)}, checks=[("le",[2080425,10006982],12087407),("le23",[1722786,5101401],6824187)]),
   dict(name="income", pdf_page=9, printed_page=7, values={"insurance_revenue":(5391459,4236470),"net_income_after_zakat":(332343,328061),"eps_sar":(3.32,3.28)}, checks=[("ni",[329313,3030],332343)]),
  ], observations=["FY2024 values equal the comparatives in the FY2025 file. FY2023 comparatives are IFRS 17 figures (total assets 6,824,187)."]),
 dict(sha="eec2df2f68d2", true_period="H1 2022 (three and six months to 2022-06-30), pre-IFRS 17 presentation", collector_label="2022|H1", identity="AL RAJHI COMPANY FOR COOPERATIVE INSURANCE interim condensed FI (unaudited)", units="SAR '000",
  read="scanned (zero text layer): rendered pdf p1,4,5 read by eye at low resolution; headline totals only",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(5345906,4641318),"total_equity":(1311876,1270416)}, checks=[]),
   dict(name="income", pdf_page=5, printed_page=3, values={"net_income_after_zakat_h1":(58030,100183),"net_income_after_zakat_q2":(20378,38477),"eps_h1":(1.45,2.50)}, checks=[]),
  ], observations=["Q1 2022 NI 37,652 (ab052783) + Q2 20,378 = H1 58,030. Cash-flow, equity statements of the three 2022 scans NOT read."]),
 dict(sha="ab052783ee", true_period="Q1 2022 (three months to 2022-03-31)", collector_label="2022|Q1", identity="Al Rajhi Company for Cooperative Insurance interim FI (unaudited)", units="SAR '000", read="scanned: rendered pdf p1,4,5 read by eye, headline totals",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(4998422,4641318),"total_equity":(1351195,1270416)}, checks=[]),
   dict(name="income", pdf_page=5, printed_page=3, values={"net_income_after_zakat":(37652,61706),"eps":(0.94,1.54)}, checks=[]),
  ], observations=[]),
 dict(sha="b285b1ca5d94", true_period="9M 2022 (three and nine months to 2022-09-30)", collector_label="2022|9M", identity="Al Rajhi Company for Cooperative Insurance interim FI (unaudited), review report dated 6 Nov 2022", units="SAR '000", read="scanned: rendered pdf p1,3,4 read by eye, SOFP totals only",
  statements=[
   dict(name="financial_position", pdf_page=4, printed_page=2, values={"total_assets":(5458673,4641318),"total_equity":(1319393,1270416)}, checks=[]),
  ], observations=["Income and cash-flow pages of the 9M 2022 scan not read."]),
]
