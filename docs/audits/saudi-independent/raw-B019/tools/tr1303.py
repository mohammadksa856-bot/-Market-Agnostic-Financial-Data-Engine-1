"""Page transcription for 1303 EIC (Electrical Industries Company; full SAR; no non-controlling interests). Writes transcripts/1303.json."""
from trlib import *

VIS = "visual: statement pages textless, rendered and read"
D = []
RC = []
CF23 = dict(cfo="FY2023 filing prints CFO 107,136,111 and CFI -29,689,779 vs 107,137,204 / -29,690,872 in the FY2024 filing (dividend income 1,093 moved from investing to operating); net change -54,202,129 unchanged",
            cfi="see cfo")
CF22 = dict(cfo="FY2022 filing prints CFO -87,649,795 and CFI -10,430,908 vs -87,650,807 / -10,429,895 in the FY2023 filing (dividend income 1,013 and a 1,012 adjustments subtotal difference); net change 56,676,583 unchanged", cfi="see cfo")
D.append(doc("d2f5da16", "FY2025 consolidated FS (label 2026|FY = publication year; image-only statements; inventory class partial_statements)", "2025-12-31", "2024-12-31", "FY", VIS,
  dict(bs=7, is_=8, cf=10),
  bs_=dict(cur=bs(2595425829, 1297420808, 1298005021, 350381125, 434603710),
           prior=bs(1950988134, 1004926370, 946061764, 188914979, 273156644)),
  is_=dict(cur=inc(2296241064, -1435971524, 860269540, 674626448, 664163773, -34234722, 629929051),
           prior=inc(1987068838, -1321753783, 665315055, 455954824, 422210524, -20479695, 401730829)),
  cf_=dict(cur=cf(673500466, -175466761, -340977020, 157056685, 188914979, 350381125, fx=4409461),
           prior=cf(688229937, -43070547, -522622919, 122536471, 68308676, 188914979, fx=-1930168))))
D.append(doc("032188a2", "FY2024 consolidated FS as issued (image-only statements; label 2025|FY = publication year; inventory class partial_statements)", "2024-12-31", "2023-12-31", "FY", VIS,
  dict(bs=7, is_=8, cf=10),
  bs_=dict(cur=bs(1950988134, 1004926370, 946061764, 188914979, 273156644), prior=bs(1895923381, 1151124984, 744798397, 68308676, 252989939)),
  is_=dict(cur=inc(1987068838, -1321753783, 665315055, 455954824, 422210524, -20479695, 401730829),
           prior=inc(1559350954, -1158055809, 401295145, 264522077, 229587686, -28553699, 201033987)),
  cf_=dict(cur=cf(688229937, -43070547, -522622919, 122536471, 68308676, 188914979, fx=-1930168),
           prior=cf(107137204, -29690872, -131648461, -54202129, 122295427, 68308676, fx=215378))))
D.append(doc("6473e18e", "FY2023 consolidated FS as issued (image-only statements; label 2024|FY = publication year; inventory class other_no_statements_found)", "2023-12-31", "2022-12-31", "FY", VIS,
  dict(bs=7, is_=8, cf=10),
  bs_=dict(cur=bs(1895923381, 1151124984, 744798397, 68308676, 252989939), prior=bs(1673769304, 1043008429, 630760875, 122295427, 253890680)),
  is_=dict(cur=inc(1559350954, -1158055809, 401295145, 264522077, 229587686, -28553699, 201033987),
           prior=inc(1066088833, -828466825, 237622008, 131609442, 112031818, -17861808, 94170010)),
  cf_=dict(cur=cf(107136111, -29689779, -131648461, -54202129, 122295427, 68308676, fx=215378, _declared_diff=CF23),
           prior=cf(-87650807, -10429895, 154757285, 56676583, 65630379, 122295427, fx=-11535))))
D.append(doc("4419e469", "FY2022 consolidated FS as issued (image-only statements; label 2023|FY = publication year)", "2022-12-31", "2021-12-31", "FY", VIS,
  dict(bs=7, is_=8, cf=10),
  bs_=dict(cur=bs(1673769304, 1043008429, 630760875, 122295427, 253890680), prior=bs(1248033291, 660230498, 587802793, 65630379, 270564761)),
  is_=dict(cur=inc(1066088833, -828466825, 237622008, 131609442, 112031818, -17861808, 94170010),
           prior=inc(770687910, -621137738, 149550172, 70258311, 62341921, -13496451, 48845470)),
  cf_=dict(cur=cf(-87649795, -10430908, 154757285, 56676583, 65630379, 122295427, fx=-11535, _tol=1, _declared_diff=CF22,
                  _note="issuer prints net change 56,676,583; CFO + CFI + CFF = 56,676,582 (one riyal rounding)"),
           prior=cf(12131969, -25101690, 7821299, -5148422, 70792172, 65630379, fx=-13371))))
D.append(doc("6128a0a9", "3M and 6M ended 2026-06-30 interim condensed consolidated (image-only statements; label 2026|H1; inventory class other_no_statements_found)", "2026-06-30", "2025-06-30", "H1", VIS,
  dict(bs=5, is_=6, cf=8), bs_prior_end="2025-12-31",
  bs_=dict(cur=bs(2545113264, 1264610874, 1280502390, 143212164, 500592832), prior=bs(2595425829, 1297420808, 1298005021, 350381125, 434603710)),
  is_=dict(cur=inc(1370004882, -852412148, 517592734, 420657934, 414790919, -12487987, 402302932),
           prior=inc(1038043433, -661204393, 376839040, 287955704, 281812896, -21664884, 260148012)),
  isq=dict(cur=inc(708570009, -440844831, 267725178, 217987445, 213399683, -1867098, 211532585),
           prior=inc(531357608, -340112302, 191245306, 150062413, 147237264, -10520184, 136717080)),
  cf_=dict(cur=cf(195246399, -83215122, -318746818, -206715541, 350381125, 143212164, fx=-453420),
           prior=cf(242748098, -54306337, -172193595, 16248166, 188914979, 212871847, fx=7708702))))
D.append(doc("b8df8fee", "3M ended 2026-03-31 interim condensed consolidated (image-only statements; label 2026|Q1; inventory class other_no_statements_found)", "2026-03-31", "2025-03-31", "Q1", VIS,
  dict(bs=5, is_=6, cf=8), bs_prior_end="2025-12-31",
  bs_=dict(cur=bs(2587739986, 1240425497, 1347314489, 244095598, 462370773), prior=bs(2595425829, 1297420808, 1298005021, 350381125, 434603710)),
  is_=dict(cur=inc(661434873, -411567317, 249867556, 202670489, 201391236, -10620889, 190770347),
           prior=inc(506685825, -321092091, 185593734, 137893291, 134575632, -11144700, 123430932)),
  cf_=dict(cur=cf(72627200, -37527028, -140918666, -105818494, 350381125, 244095598, fx=-467033),
           prior=cf(168994483, -21374485, -36985343, 110634655, 188914979, 301751107, fx=2201473))))
D.append(doc("7f200b75", "3M and 9M ended 2025-09-30 interim condensed consolidated (image-only statements; label 2025|9M; inventory class other_no_statements_found)", "2025-09-30", "2024-09-30", "9M", VIS,
  dict(bs=5, is_=6, cf=8), bs_prior_end="2024-12-31",
  bs_=dict(cur=bs(2361870110, 1268805454, 1093064656, 300559789, 330564705), prior=bs(1950988134, 1004926370, 946061764, 188914979, 273156644)),
  is_=dict(cur=inc(1598066902, -997696296, 600370606, 461026316, 451589205, -30374042, 421215163),
           prior=inc(1542823203, -1039102657, 503720546, 346266506, 319917070, -22720252, 297196818)),
  isq=dict(cur=inc(560023469, -336491903, 223531566, 173070612, 169776309, -8709158, 161067151),
           prior=inc(505846108, -320075876, 185770232, 135095675, 126925173, -5572070, 121353103)),
  cf_=dict(cur=cf(501537265, -79776895, -317381277, 104379093, 188914979, 300559789, fx=7265717),
           prior=cf(333187153, -28664122, -227779061, 76743970, 68308676, 145695361, fx=642715))))


def rc(name, tot, parts):
    RC.append(dict(name=name, total=tot, parts=parts))


for k in ("revenue", "cost_of_revenue", "net_income"):
    rc(f"Q1 2026 + Q2 2026 = 6M 2026 {k}", ["6128a0a9", "is", "cur", k], [["b8df8fee", "is", "cur", k], ["6128a0a9", "is_q", "cur", k]])
    rc(f"Q1 2025 + Q2 2025 = 6M 2025 {k}", ["6128a0a9", "is", "prior", k], [["b8df8fee", "is", "prior", k], ["6128a0a9", "is_q", "prior", k]])
    rc(f"6M 2025 + Q3 2025 = 9M 2025 {k}", ["7f200b75", "is", "cur", k], [["6128a0a9", "is", "prior", k], ["7f200b75", "is_q", "cur", k]])
if __name__ == "__main__":
    write("1303", "EIC (Electrical Industries Company)", "SAR", "full SAR", D, RC)
