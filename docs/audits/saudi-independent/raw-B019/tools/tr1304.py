"""Page transcription for 1304 Al Yamamah Steel Industries (fiscal year ends 30 September; full SAR). Writes transcripts/1304.json."""
from trlib import *

VIS = "visual: statement pages textless, rendered and read"
D = []
RC = []
D4 = dict(cost_of_revenue="FY2023 filing re-presents 2022: operating income 12,509,260 vs 12,143,497 as issued (admin expenses 47,579,941 vs 47,945,704; other revenue 1,388,613 vs 1,754,376); profit before zakat unchanged",
          operating_income="see cost_of_revenue note", gross_profit="unchanged")

# FY2025 (year ended 30 Sep 2025)
D.append(doc("ee5be447", "FY ended 2025-09-30 consolidated FS (label 2026|FY; image-only statements)", "2025-09-30", "2024-09-30", "FY", VIS,
  dict(bs=9, is_=10, cf="12-13"),
  bs_=dict(cur=bs(1765063929, 1045189965, 719873964, 33523454, 582014778), prior=bs(1784511547, 1093545933, 690965614, 71018805, 586363003)),
  is_=dict(cur=inc(1878583619, -1677573329, 201010290, 113564581, 55994958, -78391, 55916567, 59687481, -3770914),
           prior=inc(1956591394, -1732693033, 223898361, 138637780, 80946297, -10700123, 70246174, 70800717, -554543)),
  cf_=dict(cur=cf(123279072, -37576123, -123198300, -37495351, 71018805, 33523454),
           prior=cf(187556296, -24012822, -116323840, 47219634, 23799171, 71018805))))
# FY2024
D.append(doc("64c896ec", "FY ended 2024-09-30 consolidated FS as issued (label 2025|FY; image-only statements)", "2024-09-30", "2023-09-30", "FY", VIS,
  dict(bs=10, is_=11, cf="13-14", equity=12),
  bs_=dict(cur=bs(1784511547, 1093545933, 690965614, 71018805, 586363003), prior=bs(1790893283, 1170531348, 620361935, 23799171, 597667452,
           _declared_diff=dict(total_equity="FY2023 filing prints 620,361,936 (NCI 102,214,715), one riyal rounding"))),
  is_=dict(cur=inc(1956591394, -1732693033, 223898361, 138637780, 80946297, -10700123, 70246174, 70800717, -554543),
           prior=inc(1559533721, -1587952499, -28418778, -95432612, -160586461, -4557902, -165144363, -130142311, -35002052, restated=True,
                     _declared_diff=dict(cost_of_revenue="FY2023 filing shows -1,587,828,432; reversal of PPE impairment 124,067 moved to below operating profit",
                                         gross_profit="-28,294,711 in FY2023 filing", operating_income="-95,308,545 in FY2023 filing"))),
  cf_=dict(cur=cf(187556296, -24012822, -116323840, 47219634, 23799171, 71018805),
           prior=cf(138857778, -134920370, -48470208, -44532800, 68331971, 23799171))))
# FY2023
D.append(doc("46c6fed7", "FY ended 2023-09-30 consolidated FS as issued (label 2024|FY; image-only statements)", "2023-09-30", "2022-09-30", "FY", VIS,
  dict(bs=10, is_=11, cf="13-14"),
  bs_=dict(cur=bs(1790893283, 1170531348, 620361936, 23799171, 597667452, _tol=1, _note="issuer prints total equity 620,361,936 and total liabilities 1,170,531,348 against total assets 1,790,893,283 (one riyal rounding in NCI 102,214,715)"),
           prior=bs(1919430283, 1135592305, 783837978, 68331971, 504600842)),
  is_=dict(cur=inc(1559533721, -1587828432, -28294711, -95308545, -160586461, -4557902, -165144363, -130142311, -35002052,
                   _declared_diff=dict(cost_of_revenue="FY2024 filing re-presents 2023 as -1,587,952,499", gross_profit="re-presented -28,418,778", operating_income="re-presented -95,432,612")),
           prior=inc(1464976007, -1386818845, 78157162, 12509260, -3646320, -13366753, -17013073, -26655991, 9642918, restated=True, **{"_declared_diff": D4})),
  cf_=dict(cur=cf(138857778, -134920370, -48470208, -44532800, 68331971, 23799171),
           prior=cf(-286677049, -97561307, 271208488, -113029868, 181361839, 68331971, restated=True,
                    _declared_diff=dict(cfo="FY2022 filing shows CFO -283,478,618; realized gains on financial assets 3,198,431 moved from investing", cfi="FY2022 filing shows CFI -100,759,738")))))
# FY2022
D.append(doc("4b97c75b", "FY ended 2022-09-30 consolidated FS as issued (label 2022|FY; whole file image-only; inventory class partial_statements)", "2022-09-30", "2021-09-30", "FY", VIS,
  dict(bs=10, is_=11, cf=13),
  bs_=dict(cur=bs(1919430283, 1135592305, 783837978, 68331971, 504600842), prior=bs(1596420384, 691722986, 904697398, 181361839, 447338604)),
  is_=dict(cur=inc(1464976007, -1386818845, 78157162, 12143497, -3646320, -13366753, -17013073, -26655991, 9642918),
           prior=inc(1619027590, -1254854073, 364173517, 288903423, 268935112, -24392120, 244542992, 207831707, 36711285)),
  cf_=dict(cur=cf(-283478618, -100759738, 271208488, -113029868, 181361839, 68331971),
           prior=cf(279776864, -41958282, -74913663, 162904919, 18456920, 181361839))))
SEP25 = dict(total_liabilities="2026 interim filings print 1,045,189,958 (total equity 719,873,971) vs 1,045,189,965 / 719,873,964 in the FY2025 filing: 7 riyal difference",
             total_equity="see total_liabilities")
# 9M FY26 (Jul 2025 - Jun 2026 YTD: 9 months ended 2026-06-30)
D.append(doc("8e302b19", "9M ended 2026-06-30 interim condensed consolidated (label 2026|9M; image-only statements)", "2026-06-30", "2025-06-30", "9M", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2025-09-30",
  bs_=dict(cur=bs(2273616212, 1398631017, 874985195, 77101253, 616219893), prior=bs(1765063929, 1045189958, 719873971, 33523454, 582014778, _declared_diff=SEP25)),
  is_=dict(cur=inc(1571539377, -1290783966, 280755411, 213692122, 165730566, -10619342, 155111224, 148183488, 6927736),
           prior=inc(1474620386, -1325697946, 148922440, 80875558, 37125733, 2684180, 39809913, 41912682, -2102769)),
  isq=dict(cur=inc(547461125, -432324637, 115136488, 91282690, 74617731, -4643246, 69974485, 62091181, 7883304),
           prior=inc(477453298, -420263088, 57190210, 32065821, 16668503, -1659637, 15008866, 15372711, -363845)),
  cf_=dict(cur=cf(-240449946, -72442893, 356470638, 43577799, 33523454, 77101253),
           prior=cf(-46403752, -53498968, 71143197, -28759523, 71018805, 42259282, restated=True,
                    _declared_diff=dict(cfo="9M 2025 filing shows CFO -1,820,695 and CFF 26,560,141 (finance costs paid reclassified into operating)", cff="26,560,141 in the 9M 2025 filing")))))
# H1 FY26 (6 months ended 2026-03-31)
D.append(doc("88a11f9b", "6M ended 2026-03-31 interim condensed consolidated (label 2026|H1; image-only statements)", "2026-03-31", "2025-03-31", "H1", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2025-09-30",
  bs_=dict(cur=bs(2222185703, 1417174994, 805010709, 74551400, 610090409), prior=bs(1765063929, 1045189958, 719873971, 33523454, 582014778, _declared_diff=SEP25)),
  is_=dict(cur=inc(1024078252, -858431498, 165646754, 122409431, 91112834, -5976096, 85136738, 86092306, -955568),
           prior=inc(997167089, -907153119, 90013970, 48809740, 20457233, 4343817, 24801050, 26539973, -1738923)),
  isq=dict(cur=inc(525873461, -436108825, 89764636, 68393841, 52048056, -3321978, 48726078, 48482695, 243383),
           prior=inc(512723155, -460998639, 51724516, 30117890, 16087475, 5156274, 21243749, 21948156, -704407)),
  cf_=dict(cur=cf(-245905051, -53415595, 340348592, 41027946, 33523454, 74551400),
           prior=cf(-58518874, -12980759, 65137526, -6362107, 71018805, 64656698))))
# Q1 FY26 (3 months ended 2025-12-31)
D.append(doc("302c92d2", "3M ended 2025-12-31 interim condensed consolidated (label 2026|Q1; image-only statements)", "2025-12-31", "2024-12-31", "Q1", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2025-09-30",
  bs_=dict(cur=bs(2038686062, 1282401445, 756284617, 139451032, 601576264), prior=bs(1765063929, 1045189965, 719873964, 33523454, 582014778)),
  is_=dict(cur=inc(498204792, -421573934, 76630858, 54015586, 39064771, -2654118, 36410653, 37609604, -1198951),
           prior=inc(484443933, -445290607, 39153326, 18691850, 4369758, -812457, 3557301, 4591817, -1034516)),
  cf_=dict(cur=cf(-68453438, -31282725, 205663741, 105927578, 33523454, 139451032),
           prior=cf(-21240171, -2127783, 604, -23367350, 71018805, 47651455))))
# 9M FY25 as issued
D.append(doc("1520e347", "9M ended 2025-06-30 interim condensed consolidated as issued (label 2025|9M; image-only statements)", "2025-06-30", "2024-06-30", "9M", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2024-09-30",
  bs_=dict(cur=bs(1871738968, 1166363441, 705375527, 42259282, 607685384), prior=bs(1784511547, 1093545933, 690965614, 71018805, 586363003)),
  is_=dict(cur=inc(1474620386, -1325697946, 148922440, 80875558, 37125733, 2684180, 39809913, 41912682, -2102769),
           prior=inc(1553339723, -1364462828, 188876895, 122714834, 74654528, -7174881, 67479647, 66537849, 941798)),
  isq=dict(cur=inc(477453298, -420263088, 57190210, 32065821, 16668503, -1659637, 15008866, 15372711, -363845),
           prior=inc(425680502, -378119603, 47560899, 25826759, 9134836, -2628025, 6506811, 6446945, 59866)),
  cf_=dict(cur=cf(-1820695, -53498968, 26560141, -28759523, 71018805, 42259282, _tol=1, _note="issuer prints net change -28,759,523; CFO + CFI + CFF = -28,759,522 (one riyal rounding)"),
           prior=cf(169332968, -22432484, -47826336, 99074148, 23799171, 122873319))))


def rc(name, tot, parts, tol=0):
    RC.append(dict(name=name, total=tot, parts=parts, tol=tol))


for k, tol in (("revenue", 2), ("pbt", 10), ("net_income", 10)):
    rc(f"Q1 FY26 + Q2 FY26 = 6M FY26 {k}", ["88a11f9b", "is", "cur", k], [["302c92d2", "is", "cur", k], ["88a11f9b", "is_q", "cur", k]], tol)
    rc(f"6M FY26 + Q3 FY26 = 9M FY26 {k}", ["8e302b19", "is", "cur", k], [["88a11f9b", "is", "cur", k], ["8e302b19", "is_q", "cur", k]], tol)
    rc(f"Q1 FY25 + Q2 FY25 = 6M FY25 {k}", ["88a11f9b", "is", "prior", k], [["302c92d2", "is", "prior", k], ["88a11f9b", "is_q", "prior", k]], tol)
    rc(f"6M FY25 + Q3 FY25 = 9M FY25 {k}", ["1520e347", "is", "cur", k], [["88a11f9b", "is", "prior", k], ["1520e347", "is_q", "cur", k]], 5)
if __name__ == "__main__":
    write("1304", "ALYAMAMAH STEEL (Al Yamamah Steel Industries Company)", "SAR", "full SAR", D, RC)
