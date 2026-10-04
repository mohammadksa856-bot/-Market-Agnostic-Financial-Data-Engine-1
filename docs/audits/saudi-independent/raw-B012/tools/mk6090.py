import json
from pathlib import Path

from mt import *

HERE = Path(__file__).resolve().parent
IMG = "visual: statement pages are image-only or the text layer loses parentheses; rendered and read"
RS = True  # restated / re-presented comparative column flag

# balance sheet helpers (SAR)
D21o = B(634449790, 89230182, 545219608, 15364149, 225916614)            # Dec 2021 as in the Q1/H1 2022 filings
D21r = B(632826731, 89230182, 543596549, 15364149, 225916614, restated=RS)  # Dec 2021 restated (9M 2022 filing)
D21f = B(632826731, 89230183, 543596548, 15364149, 225916614, restated=RS)  # Dec 2021 in the FY2022 filing (1 riyal rounding)
D22 = B(637863030, 91277749, 546585281, 2045809, 221417357)
D23 = B(618379075, 110570612, 507808463, 16774263, 224688071)
D22r = B(607667918, 94260502, 513407416, 2045809, 224072972, restated=RS)
D23r = B(618379075, 144430612, 473948463, 16774263, 224688071, restated=RS)
D24 = B(520602948, 211268168, 309334780, 6163123, 205309339)
D25 = B(536007895, 225841495, 310166400, 15590653, 213831151)

docs = [
    doc("3fa8195b", "FY2022 audited consolidated FS as originally filed (whole-file scan; label 2023|FY holds FY2022)", "2022-12-31", "FY",
        IMG + " (pdf p6 BS printed 4, p7 IS printed 5, p9 CF printed 7)", {"bs": 6, "is": 7, "cf": 9}, {"bs": 4, "is": 5, "cf": 7},
        dict(cur=D22, prior=D21f),
        dict(cur=I(77893693, -66427892, 15791379, 19567392, -3069879, 16497513, 17341162, -843649, 0.33, bio_fv=4325578),
             prior=I(98509218, -70307027, 40938558, 13439528, -1778239, 11661289, 12128716, -467427, 0.23, bio_fv=12736367)),
        dict(cur=C(-30856834, 20442246, -2903752, -13318340, 15364149, 0, 2045809, -12131419), prior=C(14821926, -19291225, 13406294, 8936995, 6427154, 0, 15364149, -10227149))),
    doc("179192c6", "Q1 2022 interim (image-only statements; class partial_statements; label 2022|Q1 ok)", "2022-03-31", "Q1",
        IMG + " (pdf p5 BS printed 1, p6 IS printed 2, p8-9 CF printed 4-5)", {"bs": 5, "is": 6, "cf": [8, 9]}, {"bs": 1, "is": 2, "cf": 4},
        dict(cur=B(633285284, 84685926, 548599358, 15158706, 228705306), prior=D21o),
        dict(cur=I(26312946, -17715413, 8597533, 3755310, -415000, 3340310, 3563597, -223287, 0.07),
             prior=I(23176937, -16684157, 6492780, 2499987, -410713, 2089274, 2026665, 62609, 0.04)),
        dict(cur=C(6676457, -4980907, -1900993, -205443, 15364149, 0, 15158706, -402350), prior=C(644358, -879208, -1575000, -1809850, 6427154, 0, 4617304, -651708))),
    doc("33894f9b", "H1 2022 interim (whole file scanned; label 2022|H1 ok)", "2022-06-30", "H1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(656347493, 83111621, 573235872, 41519000, 226915598), prior=D21o),
        dict(cur=I(44157449, -31933056, 12224393, 28806824, -830000, 27976824, 28330524, -353700, 0.57),
             prior=I(42997967, -30742119, 21715091, 10769282, -821426, 9947856, 9872257, 75599, 0.20, bio_fv=9459243)),
        dict(cur=C(2187469, 25928034, -1960652, 26154851, 15364149, 0, 41519000, -7334701), prior=C(-5483075, -1666234, 13360009, 6210700, 6427154, 0, 12637854, -1438734)),
        is_q=dict(cur=I(17844503, -14217643, 3626860, 24933040, -415000, 24518040, 24648453, -130413, 0.49),
                  prior=I(19821030, -14064073, 15216200, 8263085, -410713, 7852372, 7841555, 10817, 0.16, bio_fv=9459243))),
    doc("a6b641fe", "9M 2022 interim (whole file scanned; label 2022|9M ok)", "2022-09-30", "9M",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7-8 CF printed 5-6)", {"bs": 4, "is": 5, "cf": [7, 8]}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(650462216, 80029421, 570432795, 9802065, 225856308), prior=D21r),
        dict(cur=I(57397063, -51673187, 17491533, 28041806, -1245000, 26796806, 27249386, -452580, 0.54, bio_fv=11767657),
             prior=I(62153572, -43936765, 30603901, 13438470, -1232139, 12206331, 12217958, -11627, 0.24, bio_fv=12387094)),
        dict(cur=C(-26436276, 24787845, -3913653, -5562084, 15364149, 0, 9802065, -2355386), prior=C(-3313044, -10804530, 13143632, -973942, 6427154, 0, 5453212, -10577030)),
        is_q=dict(cur=I(13239614, -7972474, 5267140, -765018, -415000, -1180018, -1081138, -98880, -0.02),
                  prior=I(19155605, -13194646, 8888810, 2669188, -410713, 2258475, 2345701, -87226, 0.05, bio_fv=2927851))),
    doc("40a33c40", "Q1 2023 interim (whole file scanned; label 2023|Q1 ok)", "2023-03-31", "Q1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(641990843, 94193554, 547797289, 4987544, 221260163), prior=D22),
        dict(cur=I(27482109, -21641373, 8865970, 2392522, -515000, 1877522, 1782675, 94847, 0.04, bio_fv=3025234),
             prior=I(26312946, -17715413, 8597533, 3755310, -415000, 3340310, 3563597, -223287, 0.07)),
        dict(cur=C(4577413, 622570, -2258248, 2941735, 2045809, 0, 4987544, -615247), prior=C(6676457, -4980907, -1900993, -205443, 15364149, 0, 15158706, -402350))),
    doc("0c25ebb7", "H1 2023 interim (text layer; statement pages read from the render; label 2023|H1 ok)", "2023-06-30", "H1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p8 CF printed 6)", {"bs": 4, "is": 5, "cf": 8}, {"bs": 2, "is": 3, "cf": 6},
        dict(cur=B(651608617, 92367120, 559241497, 11997586, 223264906), prior=D22),
        dict(cur=I(54932193, -39893353, 18064074, 14351730, -1030000, 13321730, 13181609, 140121, 0.27, bio_fv=3025234),
             prior=I(44157449, -31933056, 12224393, 28806824, -830000, 27976824, 28330524, -353700, 0.57)),
        dict(cur=C(-1749128, 13963005, -2262100, 9951777, 2045809, 0, 11997586, -6070956), prior=C(2187469, 25928034, -1960652, 26154851, 15364149, 0, 41519000, -7334701)),
        is_q=dict(cur=I(27450084, -18251980, 9198104, 11959208, -515000, 11444208, 11398934, 45274, 0.23),
                  prior=I(17844503, -14217643, 3626860, 24933040, -415000, 24518040, 24648453, -130413, 0.49))),
    doc("e2d7eedc", "9M 2023 interim (text layer; statement pages read from the render; label 2023|9M ok)", "2023-09-30", "9M",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(650726614, 86210845, 564515769, 4562877, 223346859), prior=D22),
        dict(cur=I(72287133, -53681438, 24435168, 20141002, -1545000, 18596002, 18646952, -50950, 0.37, bio_fv=5829473),
             prior=I(57397063, -51673187, 17491533, 28041806, -1245000, 26796806, 27249386, -452580, 0.54, bio_fv=11767657)),
        dict(cur=C(-3603074, 10671390, -4551248, 2517068, 2045809, 0, 4562877, -4630122), prior=C(-1436276, -212155, -3913653, -5562084, 15364149, 0, 9802065, -2355386, restated=RS)),
        is_q=dict(cur=I(17354940, -13788085, 6371094, 5789272, -515000, 5274272, 5465343, -191071, 0.11, bio_fv=2804239),
                  prior=I(13239614, -7972474, 5267140, -765018, -415000, -1180018, -1081138, -98880, -0.02)),
        restatements=["9M 2022 comparative cash flow: operating (1,436,276) and investing (212,155) (vs (26,436,276) and 24,787,845 as originally filed in a6b641fe); 25,000,000 purchase of financial investments at FVTPL moved from operating to investing; financing and net change unchanged"]),
    doc("48f29145", "FY2023 audited consolidated FS (text layer; 3 balance-sheet columns, so read from the render; label 2024|FY holds FY2023; company renamed Jazan Development and Investment Company)", "2023-12-31", "FY",
        IMG + " (pdf p9 BS printed 7, p10 IS printed 8, p12-13 CF printed 10-11)", {"bs": 9, "is": 10, "cf": [12, 13]}, {"bs": 7, "is": 8, "cf": 10},
        dict(cur=D23, prior=D22r),
        dict(cur=I(84331249, -73979148, 22267473, 4796021, -3272354, 1523667, 1759734, -236067, 0.04, bio_fv=11915372),
             prior=I(77893693, -66427892, 15791379, 12937951, -3069879, 9868072, 10711721, -843649, 0.21, bio_fv=4325578, restated=RS)),
        dict(cur=C(-9676401, 7991050, 16413805, 14728454, 2045809, 0, 16774263, -9574684), prior=C(-7856830, -2557758, -2903752, -13318340, 15364149, 0, 2045809, -12131423, restated=RS)),
        restatements=["FY2022 comparative (Restated Note 37): net profit 9,868,072 (vs 16,497,513 as originally filed in 3fa8195b), profit before zakat 12,937,951 (vs 19,567,392), cash from operations (7,856,830) (vs (30,856,834)), investing (2,557,758) (vs 20,442,246); balance sheet Dec 2022 total assets 607,667,918 (vs 637,863,030), equity 513,407,416 (vs 546,585,281); net change in cash and closing cash unchanged"]),
    doc("250bb955", "Q1 2024 interim (BS text layer; IS and CF image-only; label 2024|Q1 ok)", "2024-03-31", "Q1",
        IMG + " (pdf p5 BS printed 3, p6 IS printed 4, p8 CF printed 6)", {"bs": 5, "is": 6, "cf": 8}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(569967407, 107976795, 461990612, 2315641, 223280528), prior=D23),
        dict(cur=I(14487281, -15987032, -33579546, -40506491, -512500, -41018991, -40939975, -79016, -0.82, bio_fv=-32079795),
             prior=I(27482109, -24155774, 9818586, 2392522, -515000, 1877522, 1782675, 94847, 0.04, bio_fv=6492251, restated=RS)),
        dict(cur=C(-13430607, -902325, -125690, -14458622, 16774263, 0, 2315641, -296952), prior=C(4577413, 622570, -2258248, 2941735, 2045809, 0, 4987544, -615247)),
        restatements=["Q1 2023 comparative (Restated Note 15): cost of revenues 24,155,774 (vs 21,641,373 as originally filed in 40a33c40) and gain on biological assets 6,492,251 (vs 3,025,234); gross profit 9,818,586 (vs 8,865,970); profit before zakat and net profit unchanged"]),
    doc("816eca26", "H1 2024 interim (text layer unreliable; read from the render; label 2024|H1 ok)", "2024-06-30", "H1",
        IMG + " (pdf p5 BS printed 3, p6 IS printed 4, p8 CF printed 6)", {"bs": 5, "is": 6, "cf": 8}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(560146524, 110623306, 449523218, 9885915, 221450638), prior=D23),
        dict(cur=I(46310637, -51325927, -37095085, -52422408, -1055391, -53477799, -53430388, -47411, -1.07, bio_fv=-32079795),
             prior=I(54932193, -41268387, 20156057, 14351730, -1030000, 13321730, 13181609, 140121, 0.26, bio_fv=6492251, restated=RS)),
        dict(cur=C(-4715580, -1355603, -817165, -6888348, 16774263, 0, 9885915, -1280603), prior=C(-1749128, 13963005, -2262100, 9951777, 2045809, 0, 11997586, -6070956)),
        is_q=dict(cur=I(31823356, -35338895, -3515539, -11915917, -542891, -12458808, -12490413, 31605, -0.25),
                  prior=I(27450084, -17112369, 10337715, 11959208, -515000, 11444208, 11398934, 45274, 0.23, restated=RS)),
        restatements=["H1 2023 comparative (restated): 6M cost of revenues 41,268,387 (vs 39,893,353 in 0c25ebb7), gain on biological assets 6,492,251 (vs 3,025,234), gross profit 20,156,057 (vs 18,064,074); Q2 2023 cost 17,112,369 (vs 18,251,980), gross profit 10,337,715 (vs 9,198,104); profit before zakat and net profit unchanged"]),
    doc("b0681daa", "9M 2024 interim (text layer unreliable; read from the render; label 2024|9M ok)", "2024-09-30", "9M",
        IMG + " (pdf p5 BS printed 3, p6 IS printed 4, p8 CF printed 6)", {"bs": 5, "is": 6, "cf": 8}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(538992334, 108306025, 430686309, 10891857, 210599293), prior=D23),
        dict(cur=I(63057920, -67444268, -36466143, -56440449, -3278820, -72473858, -72276529, -197329, -1.45, bio_fv=-32079795, discontinued=-12754589),
             prior=I(61610719, -46535877, 24371332, 18211195, -1545000, 18596002, 18646952, -50950, 0.37, bio_fv=9296490, discontinued=1929807, restated=RS)),
        dict(cur=C(-129283, -4882724, -870399, -5882406, 16774263, 0, 10891857, -1884893), prior=C(-3603074, 10671390, -4551248, 2517068, 2045809, 0, 4562877, -4630122)),
        is_q=dict(cur=I(22400773, -22328768, 72005, -7838045, -2223429, -18996056, -18846138, -149918, -0.38, discontinued=-8934582),
                  prior=I(13007214, -9737625, 6073828, 3798367, -515000, 5274272, 5465343, -191071, 0.11, bio_fv=2804239, discontinued=1990905, restated=RS)),
        restatements=["9M 2023 comparative re-presented for discontinued operations: revenue 61,610,719 (vs 72,287,133 in e2d7eedc), cost 46,535,877 (vs 53,681,438), gross profit 24,371,332 (vs 24,435,168), profit before zakat from continuing operations 18,211,195 (vs 20,141,002), discontinued profit 1,929,807; net profit 18,596,002 unchanged; Q3 2023 revenue 13,007,214 (vs 17,354,940)"]),
    doc("57fe282a", "FY2024 audited consolidated FS (text layer loses signs; read from the render; label 2025|FY holds FY2024)", "2024-12-31", "FY",
        IMG + " (pdf p7 BS printed 5, p8 IS printed 6, p10-11 CF printed 8-9)", {"bs": 7, "is": 8, "cf": [10, 11]}, {"bs": 5, "is": 6, "cf": 8},
        dict(cur=D24, prior=D23r),
        dict(cur=I(78703147, -80661395, -32279872, -130956829, -8873229, -153499750, -153276957, -222793, -3.06, bio_fv=-30321624, discontinued=-13669692),
             prior=I(70154746, -57300332, 24769786, -27636488, -3272354, -32336333, -32100266, -236067, -0.64, bio_fv=11915372, discontinued=-1427491, restated=RS)),
        dict(cur=C(-3211947, -6519943, -897250, -10611140, 16774263, 0, 6163123, -2682459), prior=C(-9676401, 7991050, 16413805, 14728454, 2045809, 0, 16774263, -9574684)),
        accepted=["cf-sum:cur"],
        doc_note="printed financing total (897,250) is a transposition of (879,250), which is the sum of the three lines and the figure printed in the FY2025 comparative; printed net change (10,611,140) agrees with the corrected total",
        restatements=["FY2023 comparative (Restated Note 38): profit before zakat from continuing operations (27,636,488) (vs 4,796,021 as originally filed in 48f29145); net profit (32,336,333) (vs 1,523,667) after the expected credit loss on the guarantee commitment 33,860,000 and discontinued operations; revenue 70,154,746 (vs 84,331,249); balance sheet Dec 2023 total liabilities 144,430,612 (vs 110,570,612) and equity 473,948,463 (vs 507,808,463)"]),
    doc("4659767c", "Q1 2025 interim (text layer loses signs; read from the render; label 2025|Q1 ok)", "2025-03-31", "Q1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(549589899, 230669590, 318920309, 20047742, 203958998), prior=D24),
        dict(cur=I(27547449, -18758859, 15617999, 9503790, -1135000, 9618790, 9656911, -38121, 0.19, bio_fv=6829409, discontinued=1250000),
             prior=I(11415864, -12783839, -33447770, -106347375, -512500, -107958991, -107879975, -79016, -2.16, bio_fv=-32079795, discontinued=-1099116, restated=RS)),
        dict(cur=C(-2946068, 2027993, 14802694, 13884619, 6163123, 0, 20047742, -444507), prior=C(-13430607, -902325, -125690, -14458622, 16774263, 0, 2315641, -296952)),
        restatements=["Q1 2024 comparative (restated Note 16): revenue 11,415,864 (vs 14,487,281 as originally filed in 250bb955), profit before zakat from continuing operations (106,347,375) (vs (40,506,491)) after an expected credit loss of 66,940,000 on the financial guarantee commitment and discontinued operations (1,099,116); net loss (107,958,991) (vs (41,018,991))"]),
    doc("c21bf9b4", "H1 2025 interim (text layer loses signs; read from the render; label 2025|H1 ok)", "2025-06-30", "H1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(547796584, 211107843, 336688741, 11154588, 203477869), prior=D24),
        dict(cur=I(71788133, -46088349, 32688514, 27603578, -2310000, 26543578, 26374866, 168712, 0.53, bio_fv=9085818, bio_impair=-2097088, discontinued=1250000),
             prior=I(40609564, -44920404, -36390635, -115542403, -1055391, -120417799, -120370388, -47411, -2.41, bio_fv=-32079795, discontinued=-3820005, restated=RS)),
        dict(cur=C(6853496, 326242, -2188273, 4991465, 6163123, 0, 11154588, -2108258), prior=C(-4715580, -1355603, -817165, -6888348, 16774263, 0, 9885915, -1280603)),
        is_q=dict(cur=I(44240684, -27329490, 17070515, 18099790, -1175000, 16924790, 16717956, 206834, 0.33, bio_fv=2256409, bio_impair=-2097088),
                  prior=I(29193702, -32136565, -2942863, -9195026, -542891, -12458808, -12490413, 31605, -0.25, discontinued=-2720891, restated=RS)),
        restatements=["6M 2024 comparative re-presented for discontinued operations and the guarantee loss: revenue 40,609,564 (vs 46,310,637 as originally filed in 816eca26), profit before zakat from continuing operations (115,542,403) (vs (52,422,408)), discontinued (3,820,005); net loss (120,417,799) (vs (53,477,799)); Q2 2024 revenue 29,193,702 (vs 31,823,356)"]),
]
for d in docs:
    d["doc_note"] = d.get("doc_note", "")
    d["sign_notes"] = []
(HERE / "manual_6090.json").write_text(json.dumps(docs, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
meta = {"currency": "SAR", "unit": "SAR (full riyals; every filing prints whole riyals)",
        "skip_auto": ["0c25ebb7", "e2d7eedc", "48f29145", "816eca26", "b0681daa", "57fe282a", "4659767c", "c21bf9b4", "250bb955"],
        "skip_rolls": ["2024 H1 + Q3 = 9M", "2022 Q1 + Q2 = H1"],
        "doc_patches": [
            {"sha": "c5b60505", "path": ["is", "prior", "restated"], "value": True},
            {"sha": "c5b60505", "path": ["is_q", "prior", "restated"], "value": True},
            {"sha": "c5b60505", "path": ["restatements"], "value": ["9M 2024 comparative (restated note 18): profit before zakat from continuing operations (123,380,449) (vs (56,440,449) as originally filed in b0681daa) and net loss (139,413,858) (vs (72,473,858)) after the 66,940,000 expected credit loss on the guarantee commitment; Q3 2024 net loss (18,996,056) unchanged"]},
            {"sha": "5199e7b3", "path": ["cf", "prior", "restated"], "value": True},
            {"sha": "5199e7b3", "path": ["restatements"], "value": ["FY2024 comparative financing (879,250) corrects the printed (897,250) in 57fe282a (transposition); net change unchanged"]},
            {"sha": "431c9b8c", "path": ["is", "prior", "restated"], "value": True},
            {"sha": "431c9b8c", "path": ["restatements"], "value": ["Q1 2025 comparative re-presented: cost of revenues (23,867,214) (vs (18,758,859) in 4659767c) and fair-value gain on biological assets 11,937,764 (vs 6,829,409); gross profit 15,617,999 and net profit unchanged"]},
            {"sha": "f87d22ef", "path": ["is", "prior", "restated"], "value": True},
            {"sha": "f87d22ef", "path": ["is_q", "prior", "restated"], "value": True},
            {"sha": "f87d22ef", "path": ["is", "prior", "ni_parent"], "value": 26374866},
            {"sha": "f87d22ef", "path": ["restatements"], "value": ["H1 2025 comparative re-presented: 6M cost of revenues (62,919,179) (vs (46,088,349) in c21bf9b4) and fair-value gain 23,819,560 (vs 9,085,818 less impairment 2,097,088); Q2 2025 cost (39,051,965) (vs (27,329,490)); gross profit and net profit unchanged"]}
        ]}
(HERE / "meta_6090.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
