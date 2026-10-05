"""Page transcription for 1202 MEPCO (full SAR). Writes transcripts/1202.json."""
from trlib import *

TXT = "text layer (clean), pdf pages cited"
VIS = "visual: statement pages textless, rendered and read"
D = []
# FY2025
D.append(doc("27f0b1cb", "FY2025 consolidated FS (collector label 2026|FY = publication year)", "2025-12-31", "2024-12-31", "FY", TXT,
  dict(bs=8, is_=9, cf="11-12", equity=10),
  bs_=dict(cur=bs(2668255373, 1047516585, 1620738788, 495352589, 1431865458),
           prior=bs(2558600261, 958566909, 1600033352, 610683119, 1268700865,
                    _declared_diff=dict(ppe="FY2024 filing shows PPE 1,221,071,925 + CWIP 27,621,024 + right-of-use 20,007,916 = 1,268,700,865; FY2025 filing merges them into PPE"))),
  is_=dict(cur=inc(1060527264, -926909015, 133618249, 44967159, 35639427, -13435907, 22203520, 23410074, -1206554),
           prior=inc(1065255961, -957629091, 107626870, -52532671, -57900015, -19567985, -77468000, -77326129, -141871)),
  cf_=dict(cur=cf(123079082, -241944882, 3535270, -115330530, 610683119, 495352589),
           prior=cf(-100005234, -90046235, 744185195, 554133726, 56549393, 610683119))))
# FY2024
D.append(doc("56b0f17a", "FY2024 consolidated FS as issued (statement pages image-only; collector label 2025|FY = publication year)", "2024-12-31", "2023-12-31", "FY", VIS,
  dict(bs=8, is_=9, cf="11-12"),
  bs_=dict(cur=bs(2558600261, 958566909, 1600033352, 610683119, 1221071925),
           prior=bs(1930933950, 862730540, 1068203410, 56549393, 1111782224)),
  is_=dict(cur=inc(1065255961, -957629091, 107626870, -52532671, -57900015, -19567985, -77468000, -77326129, -141871),
           prior=inc(866752771, -823076340, 43676431, -51234467, -77758966, -9878531, -87637497, -80269141, -7368356,
                     restated=True, _declared_diff=dict(cost_of_revenue="2023 comparative restated (note 36.2): selling expenses 41,319,658 moved out of cost of revenue (FY2023 filing cost 781,756,682)", gross_profit="same reclassification, FY2023 filing gross profit 84,996,089"))),
  cf_=dict(cur=cf(-100005234, -90046235, 744185195, 554133726, 56549393, 610683119),
           prior=cf(198122581, -270057612, -16761657, -88696688, 145246081, 56549393,
                    _declared_diff=dict(cfo="FY2023 filing shows CFO 199,126,581; 1,004,000 reclassified from CFO to financing (lease principal 11,915,393 -> 10,911,393)", cff="FY2023 filing shows CFF -17,765,657")))))
# FY2023
D.append(doc("e9e1bfd9", "FY2023 consolidated FS as issued (statement pages image-only; inventory class partial_statements; label 2024|FY = publication year)", "2023-12-31", "2022-12-31", "FY", VIS,
  dict(bs=8, is_=9, cf="11-12"),
  bs_=dict(cur=bs(1930933950, 862730540, 1068203410, 56549393, 1111782224), prior=bs(1946514373, 764228251, 1182286122, 145246081, 871799672)),
  is_=dict(cur=inc(866752771, -781756682, 84996089, -51234467, -77758966, -9878531, -87637497, -80269141, -7368356),
           prior=inc(1187005798, -684219701, 502786097, 304294383, 285811277, -15081467, 270729810, 269698532, 1031278)),
  cf_=dict(cur=cf(199126581, -270057612, -17765657, -88696688, 145246081, 56549393),
           prior=cf(238674940, -165303557, -192129660, -118758277, 264004358, 145246081, restated=True,
                    _declared_diff=dict(cfo="FY2022 filing shows CFO 286,390,856: capital project advances (47,715,916) reclassified from investing to operating working capital", cfi="FY2022 filing shows CFI -213,019,473")))))
# FY2022
D.append(doc("dac8ceda", "FY2022 consolidated FS as issued (text layer; label 2023|FY = publication year)", "2022-12-31", "2021-12-31", "FY", TXT,
  dict(bs=8, is_=9, cf=11),
  bs_=dict(cur=bs(1946514373, 764228251, 1182286122, 145246081, 871799672), prior=bs(1870117781, 887221889, 982895892, 264004358, 939046594)),
  is_=dict(cur=inc(1187005798, -684219701, 502786097, 304294383, 285811277, -15081467, 270729810, 269698532, 1031278),
           prior=inc(1057399630, -663297385, 394102245, 242317938, 227824133, -6957475, 220866658, 220710095, 156563)),
  cf_=dict(cur=cf(286390856, -213019473, -192129660, -118758277, 264004358, 145246081),
           prior=cf(251301742, -57707414, 24954758, 218549086, 45455272, 264004358))))
# H1 2026
D.append(doc("3ee0937e", "3M and 6M ended 2026-06-30 interim condensed consolidated (English; image-only statements; label 2026|H1)", "2026-06-30", "2025-06-30", "H1", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2025-12-31",
  bs_=dict(cur=bs(2796333041, 1158791734, 1637541307, 454792432, 1637305852), prior=bs(2668255373, 1047516585, 1620738788, 495352589, 1431865458)),
  is_=dict(cur=inc(542305194, -459174865, 83130329, 25144216, 18052625, -4123601, 13929024, 13294448, 634576),
           prior=inc(534219588, -463211466, 71008122, 25182928, 18539346, -8194687, 10344659, 10556727, -212068)),
  isq=dict(cur=inc(298012904, -241491893, 56521011, 20373565, 17127161, -1797726, 15329435, 15288530, 40905),
           prior=inc(275129510, -238068071, 37061439, 11952251, 8904912, -3857290, 5047622, 5225375, -177753)),
  cf_=dict(cur=cf(95367830, -248794017, 112866030, -40560157, 495352589, 454792432),
           prior=cf(91471980, -133263053, -17406257, -59197330, 610683119, 551485789))))

PPE_DEC24 = dict(ppe="Dec 2024 PPE 1,241,079,841 in 2025 interim filings = FY2024 filing PPE 1,221,071,925 + right-of-use 20,007,916; the FY2025 filing re-presents it as 1,268,700,865 (also incl. CWIP 27,621,024)")
# Q1 2026
D.append(doc("1b3c4e61", "3M ended 2026-03-31 interim condensed consolidated (English; image-only statements; inventory class other_no_statements_found; label 2026|Q1)", "2026-03-31", "2025-03-31", "Q1", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2025-12-31",
  bs_=dict(cur=bs(2759060525, 1139722148, 1619338377, 463758512, 1548631166), prior=bs(2668255373, 1047516585, 1620738788, 495352589, 1431865458)),
  is_=dict(cur=inc(244292290, -217682972, 26609318, 4770651, 925464, -2325875, -1400411, -1994082, 593671),
           prior=inc(259090078, -225143395, 33946683, 13230677, 9634434, -4337397, 5297037, 5331352, -34315)),
  cf_=dict(cur=cf(35453580, -138205158, 71157501, -31594077, 495352589, 463758512),
           prior=cf(25870400, -97034065, 41173266, -29990399, 610683119, 580692720))))
# 9M 2025
D.append(doc("eb8f0442", "3M and 9M ended 2025-09-30 interim condensed consolidated (image-only statements, scrambled text layer on pdf p8; label 2025|9M)", "2025-09-30", "2024-09-30", "9M", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2024-12-31",
  bs_=dict(cur=bs(2582479172, 957422871, 1625056301, 519879203, 1196522986), prior=bs(2558600261, 958566909, 1600033352, 610683119, 1241079841, _declared_diff=PPE_DEC24)),
  is_=dict(cur=inc(813194576, -705827979, 107366597, 42215149, 35139859, -10840261, 24299598, 24866214, -566616),
           prior=inc(775423799, -671122003, 104301796, -17941132, -21401964, -12374974, -33776938, -32822276, -954662, restated=True)),
  isq=dict(cur=inc(278974988, -242616513, 36358475, 17032221, 16600513, -2645574, 13954939, 14309487, -354548),
           prior=inc(276894804, -240121662, 36773142, -14414355, -18218619, -308897, -18527516, -18500641, -26875, restated=True)),
  cf_=dict(cur=cf(123463769, -158102511, -56165174, -90803916, 610683119, 519879203),
           prior=cf(-75196195, -63286119, 714718770, 576236456, 56549393, 632785849))))
# H1 2025
D.append(doc("a7b11ec3", "3M and 6M ended 2025-06-30 interim condensed consolidated (image-only statements; label 2025|H1)", "2025-06-30", "2024-06-30", "H1", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2024-12-31",
  bs_=dict(cur=bs(2616384899, 1005283537, 1611101362, 551485789, 1219527909), prior=bs(2558600261, 958566909, 1600033352, 610683119, 1241079841, _declared_diff=PPE_DEC24)),
  is_=dict(cur=inc(534219588, -463211466, 71008122, 25182928, 18539346, -8194687, 10344659, 10556727, -212068),
           prior=inc(498528995, -431000341, 67528654, -3526777, -3183345, -12066077, -15249422, -14321635, -927787, restated=True)),
  isq=dict(cur=inc(275129510, -238068071, 37061439, 11952251, 8904912, -3857290, 5047622, 5225375, -177753),
           prior=inc(255076049, -211218759, 43857290, 7708685, 9394513, -5930258, 3464255, 4038532, -574277, restated=True)),
  cf_=dict(cur=cf(91471980, -133263053, -17406257, -59197330, 610683119, 551485789),
           prior=cf(-7560759, -99697086, 668408657, 561150812, 56549393, 617700205))))
# Q1 2025
D.append(doc("d841b90b", "3M ended 2025-03-31 interim condensed consolidated (image-only statements; inventory class partial_statements; label 2025|Q1)", "2025-03-31", "2024-03-31", "Q1", VIS,
  dict(bs=4, is_=5, cf="7-8"), bs_prior_end="2024-12-31",
  bs_=dict(cur=bs(2624755442, 1019337553, 1605417889, 580692720, 1237846587), prior=bs(2558600261, 958566909, 1600033352, 610683119, 1241079841, _declared_diff=PPE_DEC24)),
  is_=dict(cur=inc(259090078, -225143395, 33946683, 13230677, 9634434, -4337397, 5297037, 5331352, -34315),
           prior=inc(243452946, -219775825, 23677121, -11235462, -12577858, -6135819, -18713677, -18360167, -353510, restated=True)),
  cf_=dict(cur=cf(25870400, -97034065, 41173266, -29990399, 610683119, 580692720),
           prior=cf(9700501, -21763181, 654009249, 641946569, 56549393, 698495962))))
# Q1 2024 (own filing, text layer)
D.append(doc("8969f4f0", "3M ended 2024-03-31 interim condensed consolidated as issued (text layer; label 2024|Q1)", "2024-03-31", "2023-03-31", "Q1", TXT,
  dict(bs=4, is_=5, cf=7), bs_prior_end="2023-12-31",
  bs_=dict(cur=bs(2596427873, 936828421, 1659599452, 698495962, 1093168387), prior=bs(1930933950, 862730540, 1068203410, 56549393, 1111782224)),
  is_=dict(cur=inc(243452946, -210944782, 32508164, -11235462, -12577858, -6135819, -18713677, -18360167, -353510,
                   _declared_diff=dict(cost_of_revenue="Q1 2025 filing restates Q1 2024 (note 19): selling expense 8,831,043 moved into cost of revenue (219,775,825)", gross_profit="same reclassification (23,677,121 restated)")),
           prior=inc(223948896, -188654501, 35294395, 2294098, -3714598, -3385732, -7100330, -6557685, -542645)),
  cf_=dict(cur=cf(9700501, -21763181, 654009249, 641946569, 56549393, 698495962), prior=cf(102260899, -80439594, 18894175, 40715480, 145246081, 185961561))))
RC = [
  dict(name="Q1 2026 + Q2 2026 = 6M 2026 revenue", total=["3ee0937e", "is", "cur", "revenue"], parts=[["1b3c4e61", "is", "cur", "revenue"], ["3ee0937e", "is_q", "cur", "revenue"]]),
  dict(name="Q1 2026 + Q2 2026 = 6M 2026 net income", total=["3ee0937e", "is", "cur", "net_income"], parts=[["1b3c4e61", "is", "cur", "net_income"], ["3ee0937e", "is_q", "cur", "net_income"]]),
  dict(name="Q1 2025 + Q2 2025 = 6M 2025 revenue", total=["a7b11ec3", "is", "cur", "revenue"], parts=[["d841b90b", "is", "cur", "revenue"], ["a7b11ec3", "is_q", "cur", "revenue"]]),
  dict(name="Q1 2025 + Q2 2025 = 6M 2025 net income", total=["a7b11ec3", "is", "cur", "net_income"], parts=[["d841b90b", "is", "cur", "net_income"], ["a7b11ec3", "is_q", "cur", "net_income"]]),
  dict(name="6M 2025 + Q3 2025 = 9M 2025 revenue", total=["eb8f0442", "is", "cur", "revenue"], parts=[["a7b11ec3", "is", "cur", "revenue"], ["eb8f0442", "is_q", "cur", "revenue"]]),
  dict(name="6M 2025 + Q3 2025 = 9M 2025 net income", total=["eb8f0442", "is", "cur", "net_income"], parts=[["a7b11ec3", "is", "cur", "net_income"], ["eb8f0442", "is_q", "cur", "net_income"]]),
  dict(name="6M 2024 restated + Q3 2024 restated = 9M 2024 restated revenue", total=["eb8f0442", "is", "prior", "revenue"], parts=[["a7b11ec3", "is", "prior", "revenue"], ["eb8f0442", "is_q", "prior", "revenue"]]),
  dict(name="6M 2024 restated + Q3 2024 restated = 9M 2024 restated net income", total=["eb8f0442", "is", "prior", "net_income"], parts=[["a7b11ec3", "is", "prior", "net_income"], ["eb8f0442", "is_q", "prior", "net_income"]]),
]
if __name__ == "__main__":
    write("1202", "MEPCO (Middle East Company for Manufacturing and Producing Paper)", "SAR", "full SAR", D, RC)
