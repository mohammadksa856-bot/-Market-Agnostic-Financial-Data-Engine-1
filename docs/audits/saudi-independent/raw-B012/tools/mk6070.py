import json
from pathlib import Path

from mt import *

HERE = Path(__file__).resolve().parent
D21 = B(750614403, 122992130, 627622273, 18027401, 507033301)
D23 = B(1110068010, 391467763, 718600247, 17558140, 595976357)
D24 = B(1157666460, 402724844, 754941616, 13601660, 772871481)
D25 = B(1299524036, 500545517, 798978519, 15728969, 797391063)
IMG = "visual: image-only statement pages rendered and read"

patches = {
    "e03814b8": {"bs": {"total_assets": [1299524036, 1157666460], "total_liabilities": [500545517, 402724844], "total_equity": [798978519, 754941616],
                        "cash": [15728969, 13601660], "ppe": [797391063, 772871481]}, "pdf_bs": [6], "printed_bs": 5, "bs_end": "2025-12-31",
                 "cf": {"cfo": [75924479, 125498486], "cfi": [-102682565, -83494035], "cff": [28885395, -45960931], "net_change": [2127309, -3956480],
                        "cash_begin": [13601660, 17558140], "cash_end": [15728969, 13601660]}, "pdf_cf": [9], "printed_cf": 8,
                 "note": "text layer drops parentheses and splits numbers (total liabilities '84', '4'; prior cost of sales 406,064,506 unsigned); BS and CF read visually (CF page pdf p9 is image-only), IS signs verified on pdf p7"},
}
isfix = {"e03814b8": {"cost_of_revenue": [-506570477, -406064506], "tax": [-2700000, -5000000], "gross_profit": [205656297, 176723638]}}
meta = {"currency": "SAR", "unit": "SAR (full riyals; every Al-Jouf filing prints whole riyals)", "patches": patches,
        "printed_offset_note": "printed page numbers are taken from the page footers (auto) or read on the rendered page (manual)",
        "doc_patches": [
            {"sha": "ee2719d5", "path": ["cf", "prior", "restated"], "value": True},
            {"sha": "ee2719d5", "path": ["restatements"], "value": ["9M 2022 comparative cash flow in the 9M 2023 filing: operating 43,470,673 (vs 43,296,130 in 87041a34), investing (124,828,535) (vs (124,906,070)), financing 83,535,473 (vs 83,787,551); net change 2,177,611 unchanged"]},
            {"sha": "0ec0360d", "path": ["cf", "prior", "restated"], "value": True},
            {"sha": "0ec0360d", "path": ["restatements"], "value": ["FY2022 comparative cash flow in the FY2023 filing: investing (149,090,110) (vs (151,204,269) as originally filed in d0639dfe) and financing 86,500,024 (vs 88,614,183); difference 2,114,159; operating and net change unchanged"]},
            {"sha": "7be75050", "path": ["restatements"], "value": ["Dec 2023 comparative property, plant and equipment 760,482,059 (vs 595,976,357 in 0ec0360d): projects under construction 164,505,702 merged into PPE; totals unchanged"]},
            {"sha": "7be75050", "path": ["bs", "prior", "restated"], "value": True},
            {"sha": "54e4ecb1", "path": ["cf", "prior", "restated"], "value": True},
            {"sha": "54e4ecb1", "path": ["restatements"], "value": ["Q1 2024 comparative cash flow: operating 27,174,055 (vs 27,901,526 in 749a7b61) and financing (2,897,824) (vs (3,625,295)); difference 727,471 (loan guarantee provision payments) re-presented; net change unchanged"]},
            {"sha": "e03814b8", "path": ["cf", "prior", "restated"], "value": True},
            {"sha": "e03814b8", "path": ["restatements"], "value": ["FY2024 comparative cash flow: operating 125,498,486 (vs 121,337,652 as originally filed in 7be75050) and financing (45,960,931) (vs (41,800,097)); difference 4,160,834 re-presented; investing and net change unchanged"]},
            {"sha": "e03814b8", "path": ["is", "cur", "cost_of_revenue"], "value": -506570477},
            {"sha": "e03814b8", "path": ["is", "prior", "cost_of_revenue"], "value": -406064506},
            {"sha": "e03814b8", "path": ["is", "cur", "tax"], "value": -2700000},
            {"sha": "e03814b8", "path": ["is", "prior", "tax"], "value": -5000000},
            {"sha": "e03814b8", "path": ["is", "cur", "eps"], "value": 2.71},
            {"sha": "e03814b8", "path": ["is", "prior", "eps"], "value": 2.51},
            {"sha": "1350aa90", "path": ["cf", "cur"], "value": dict(cfo=56304243, cfi=-41919127, cff=-10208857, net_change=4176259, cash_begin=17558140, cash_end=21734399, fx=0)},
            {"sha": "1350aa90", "path": ["cf", "prior"], "value": dict(cfo=24456365, cfi=-88855317, cff=44431313, net_change=-19967639, cash_begin=31734891, cash_end=11767252, fx=0)},
            {"sha": "1350aa90", "path": ["reading"], "value": "text layer; parentheses and thousands groups split in the cash flow page (e.g. '41,919,12' '7'), so the cash flow column was re-read from the rendered page and cross-checked with the H1 2025 comparative"},
        ]}
docs = [
    doc("42c7f999", "Q1 2022 interim (image-only statements; inventory class other_no_statements_found; label 2022|Q1 ok)", "2022-03-31", "Q1",
        IMG + " (pdf p4 BS printed 3, p5 IS printed 4, p7 CF printed 6)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(799966781, 157112675, 642854106, 20089526, 485541494), prior=B(750614403, 122992130, 627622273, 18027401, 489100879, restated=True,
                                                                                      restated_note="PPE 489,100,879 plus work under progress 17,932,422 = 507,033,301 as shown in later filings")),
        dict(cur=I(60408567, -28528237, 31880330, 16881583, -1649750, 15231833, eps=0.51), prior=I(61361300, -48881855, 12479445, 5095821, -1258405, 3837416, eps=0.13)),
        dict(cur=C(5983316, -22742887, 18821696, 2062125, 18027401, 0, 20089526), prior=C(8182150, -12654890, -8000000, -12472740, 47721786, 0, 35249046))),
    doc("ec79b9c8", "H1 2022 interim (image-only statements; label 2022|H1 ok)", "2022-06-30", "H1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(871802404, 222121109, 649681295, 38236968, 536252816), prior=B(750614403, 122992130, 627622273, 18027401, 507033301)),
        dict(cur=I(124433384, -72418516, 52014868, 25808772, -3749750, 22059022, eps=0.74), prior=I(117062518, -87833872, 29228646, 9740239, -2458405, 7281834, eps=0.24)),
        dict(cur=C(9314600, -68261623, 79156590, 20209567, 18027401, 0, 38236968), prior=C(1369448, -26994883, -9985612, -35611047, 47721786, 0, 12110739)),
        is_q=dict(cur=I(64024817, -43890279, 20134538, 8927189, -2100000, 6827189, eps=0.23), prior=I(55701218, -38952017, 16749201, 4644418, -1200000, 3444418, eps=0.11))),
    doc("87041a34", "9M 2022 interim (image-only statements; label 2022|9M ok)", "2022-09-30", "9M",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(897065420, 242544231, 654521189, 20205012, 582988231), prior=D21),
        dict(cur=I(259786584, -163770135, 96016449, 47448666, -5549750, 41898916, eps=1.40), prior=I(216871324, -168710571, 48160753, 14259683, -3658405, 10601278, eps=0.35)),
        dict(cur=C(43296130, -124906070, 83787551, 2177611, 18027401, 0, 20205012, -105421800), prior=C(6566074, -38491392, -10126091, -42051409, 47721786, 0, 5670377, -38491392)),
        is_q=dict(cur=I(135353200, -91351619, 44001581, 21639894, -1800000, 19839894, eps=0.66), prior=I(99808806, -80876699, 18932107, 4519444, -1200000, 3319444, eps=0.11))),
    doc("749a7b61", "Q1 2024 interim (image-only statements; class other_no_statements_found; label 2024|Q1 ok)", "2024-03-31", "Q1",
        IMG + " (pdf p4 BS printed 2, p5 IS printed 3, p7 CF printed 5)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5},
        dict(cur=B(1187094282, 443071313, 744022969, 17664312, 587948994), prior=D23),
        dict(cur=I(160467434, -100384481, 60082953, 36022722, -3100000, 32922722, eps=1.10), prior=I(104442493, -66629628, 37812865, 21875850, -1800000, 20075850, eps=0.67)),
        dict(cur=C(27901526, -24170059, -3625295, 106172, 17558140, 0, 17664312), prior=C(3242311, -48937957, 42076429, -3619217, 31734891, 0, 28115674))),
    doc("86afc4e9", "H1 2025 interim (image-only statements; class other_no_statements_found; label 2025|H1 ok)", "2025-06-30", "H1",
        IMG + " (pdf p4 BS printed 3, p5 IS printed 4, p7 CF printed 6)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(1292954136, 499932089, 793022047, 19191110, 781141224), prior=D24),
        dict(cur=I(325188634, -208901184, 116287450, 54580431, -1500000, 53080431, eps=1.77), prior=I(273554360, -174641286, 98913074, 51987526, -3500000, 48487526, eps=1.62)),
        dict(cur=C(51943311, -55210524, 8856663, 5589450, 13601660, 0, 19191110), prior=C(56304243, -41919127, -10208857, 4176259, 17558140, 0, 21734399)),
        is_q=dict(cur=I(154595462, -106669172, 47926290, 19023394, -600000, 18423394, eps=0.61), prior=I(113086926, -74256805, 38830121, 15964804, -400000, 15564804, eps=0.52))),
    doc("68065002", "9M 2025 interim (image-only statements; class other_no_statements_found; label 2025|9M ok); cash flow shows nine months only", "2025-09-30", "9M",
        IMG + " (pdf p4 BS printed 3, p5 IS printed 4, p7 CF printed 6)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(1340924458, 548974364, 791950094, 17329886, 793901368), prior=D24),
        dict(cur=I(503554173, -338362192, 165191981, 75108478, -2100000, 73008478, eps=2.43), prior=I(420599074, -277025645, 143573429, 71882065, -4750000, 67132065, eps=2.24)),
        dict(cur=C(55286322, -85994989, 34436893, 3728226, 13601660, 0, 17329886), prior=C(91913715, -56591026, -33217957, 2104732, 17558140, 0, 19662872,
                                                                                         restated=True)),
        is_q=dict(cur=I(178365539, -129461008, 48904531, 20528047, -600000, 19928047, eps=0.66), prior=I(147044714, -102384359, 44660355, 19894539, -1250000, 18644539, eps=0.62)),
        restatements=["9M 2024 comparative cash flow: cash from operations 91,913,715 (vs 89,836,217 as originally filed in e6f8f4d8) and financing (33,217,957) (vs (31,140,459)); difference 2,077,498 (loan guarantee provision payments) re-presented between operating and financing; net change unchanged"]),
    doc("035209e7", "Q1 2026 interim (image-only statements; class other_no_statements_found; label 2026|Q1 ok)", "2026-03-31", "Q1",
        IMG + " (pdf p4 BS printed 3, p5 IS printed 4, p7 CF printed 6)", {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6},
        dict(cur=B(1435821888, 645288542, 790533346, 34943142, 804248029), prior=D25),
        dict(cur=I(167675292, -140330292, 27345000, 2954827, -900000, 2054827, eps=0.07), prior=I(170593172, -102232012, 68361160, 35557037, -900000, 34657037, eps=1.16)),
        dict(cur=C(-8531713, -25236261, 52982147, 19214173, 15728969, 0, 34943142), prior=C(26502848, -35592280, 6869549, -2219883, 13601660, 0, 11381777))),
]
(HERE / "manual_6070.json").write_text(json.dumps(docs, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
(HERE / "meta_6070.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
