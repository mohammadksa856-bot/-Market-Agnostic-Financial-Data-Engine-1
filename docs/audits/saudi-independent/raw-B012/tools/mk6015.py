import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def bs(cur, prior, page, printed, end, note="BS page image-only inside a text-layer file; read visually"):
    k = ["total_assets", "total_liabilities", "total_equity", "cash", "ppe"]
    return {"bs": {k[i]: [cur[i], prior[i]] for i in range(5)}, "pdf_bs": page, "printed_bs": printed, "bs_end": end, "note": note}


D21 = (1087914, 948202, 139712, 173996, 221919)
D22 = (1340547, 1044796, 295751, 304560, 269844)
D23 = (1556859, 1105479, 451380, 87608, 327220)
D24 = (1507400, 1109276, 398124, 81470, 328761)
D25 = (1734126, 1244152, 489974, 154337, 341405)
P = {
    "bff40b85": bs((1268679, 1041163, 227516, 273070, 248183), D21, 5, 3, "2022-09-30"),
    "341c2d0e": bs((1140218, 985472, 154746, 250039, 235988), D21, 5, 3, "2022-06-30", "BS page pdf p5 has a scrambled/garbled text layer; read visually"),
    "3645bab3": bs((1504539, 1086860, 417679, 124522, 295836), D22, 6, 4, "2023-09-30"),
    "0aa9236f": bs((1410592, 1074410, 336182, 126218, 280875), D22, 6, 4, "2023-06-30"),
    "7d3cf132": bs(D23, (1340547, 1044796, 295751, 304560, 269844), 11, 9, "2023-12-31"),
    "94583f06": bs((1468225, 1096288, 371937, 86031, 318956), D23, 5, 3, "2024-09-30"),
    "0d1be98d": bs((1425176, 1082709, 342467, 107308, 317391), D23, 5, 3, "2024-06-30"),
    "9d10f8bf": bs((1510787, 1037146, 473641, 159939, 318078), D23, 5, 3, "2024-03-31"),
    "e07a74a7": bs(D24, D23, 11, 9, "2024-12-31"),
    "8360cdb3": bs((1596823, 1164967, 431856, 109864, 325671), D24, 5, 3, "2025-03-31"),
    "78139441": bs((1542353, 1178212, 364141, 106801, 323097), D24, 5, 3, "2025-06-30"),
    "6b7ac28c": bs((1574389, 1167088, 407301, 70860, 322030), D24, 5, 3, "2025-09-30"),
    "1d753c47": bs(D25, D24, 9, 7, "2025-12-31"),
    "926c4878": bs((1757531, 1206905, 550626, 139485, 338942), D25, 5, 3, "2026-03-31"),
    "dd33ea23": bs((1695711, 1260873, 434838, 140186, 335077), D25, 5, 3, "2026-06-30"),
}
meta = {"currency": "USD", "unit": "USD thousand (US Dollars'000) in every Americana filing read; entity Americana Restaurants International PLC (ADGM), listed on Tadawul and ADX",
        "patches": P, "doc_patches": [], "printed_offset": 2}
(HERE / "meta_6015.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf8")

from mt import *

D20 = B(1016362, 929747, 86615, 196347, 207887)
Dd21 = B(1087914, 948202, 139712, 173996, 221919)
docs = [
    doc("16a1bd4e", "FY2021 special purpose carve-out FS of Americana Restaurants (Kuwait Food Co restaurant business), whole-file scan; label 2021|FY equals the fiscal year", "2021-12-31", "FY",
        VIS + " (pdf p6 BS printed 4, p7 IS printed 5, p10 CF printed 8); pre-IPO carve-out, net parent investment instead of share capital", {"bs": 6, "is": 7, "cf": 10}, {"bs": 4, "is": 5, "cf": 8},
        dict(cur=Dd21, prior=D20),
        dict(cur=I(2051747, -970351, 1081396, 222140, -15732, 206408, 203917, 2491), prior=I(1577795, -773853, 803942, 86062, -6281, 79781, 80826, -1045)),
        dict(cur=C(468849, -161568, -307867, -586, 171784, -4275, 166923, -91510), prior=C(284116, -45149, -223202, 15765, 156247, -228, 171784, -39933)), scale=1000),
    doc("bf00d061", "FY2022 consolidated FS, whole-file scan (collector label 2022|FY = FY2022: label equals fiscal year; same pages also sit in d8c7a726 labelled 2023|FY)", "2022-12-31", "FY",
        VIS + " (pdf p12 IS printed 10, p15 CF printed 13; BS pdf p11 printed 9 not read, values for the BS are in the annual report 7af927ef)", {"is": 12, "cf": 15}, {"is": 10, "cf": 13}, None,
        dict(cur=I(2378547, -1148476, 1230071, 271698, -8743, 262955, 259226, 3729, 0.03077), prior=I(2051747, -970351, 1081396, 222140, -15732, 206408, 203917, 2491, 0.02421)),
        dict(cur=C(453928, -59947, -287088, 106893, 166923, 12152, 285968, -120143), prior=C(468849, -161568, -307867, -586, 171784, -4275, 166923, -91510)), scale=1000),
    doc("7af927ef", "Annual Report and Accounts 2022 containing the FY2022 consolidated FS (inventory class annual_report_with_statements; label 2022|FY = FY2022)", "2022-12-31", "FY",
        "text layer of a two-up annual-report spread; rows rebuilt from word coordinates (pdf p71 BS, p58 IS, p59 CF); printed page numbers not read", {"bs": 71, "is": 58, "cf": 59}, {},
        dict(cur=B(1340547, 1044796, 295751, 304560, 269844), prior=Dd21),
        dict(cur=I(2378547, -1148476, 1230071, 271698, -8743, 262955, 259226, 3729, 0.03077), prior=I(2051747, -970351, 1081396, 222140, -15732, 206408, 203917, 2491, 0.02421)),
        dict(cur=C(453928, -59947, -287088, 106893, 166923, 12152, 285968), prior=C(468849, -161568, -307867, -586, 171784, -4275, 166923)), scale=1000),
    doc("15db7206", "Q1 2023 interim (whole file scanned; label 2023|Q1 ok); 55ee8783 is a near-identical re-scan, e01e218e the Arabic twin", "2023-03-31", "Q1",
        VIS + " (pdf p6 BS printed 4, p7 IS printed 5, p11 CF printed 9)", {"bs": 6, "is": 7, "cf": 11}, {"bs": 4, "is": 5, "cf": 9},
        dict(cur=B(1377496, 1131337, 246159, 329483, 272658), prior=B(1340547, 1044796, 295751, 304560, 269844)),
        dict(cur=I(589424, -288889, 300535, 61662, -2871, 58791, 58129, 662, 0.0069), prior=I(577576, -268352, 309224, 77875, -4975, 72900, 71973, 927, 0.0085)),
        dict(cur=C(91042, -18368, -51557, 21117, 285968, 2186, 309271, -18845), prior=C(149288, -51599, -151498, -53809, 166923, 11753, 124867, -15645)), scale=1000),
    doc("341c2d0e", "H1 2022 condensed interim carve-out FS (label 2022|H1 ok); BS pdf p5 text layer is scrambled, all three statements read visually; six-month columns only", "2022-06-30", "H1",
        VIS + " (pdf p5 BS printed 3, p6 IS printed 4, p10 CF printed 8)", {"bs": 5, "is": 6, "cf": 10}, {"bs": 3, "is": 4, "cf": 8},
        dict(cur=B(1140218, 985472, 154746, 250039, 235988), prior=Dd21),
        dict(cur=I(1151929, -546122, 605807, 129330, -6119, 123211, 121266, 1945, 0.001), prior=I(968149, -458886, 509263, 99691, -6058, 93633, 93324, 309, 0.001)),
        dict(cur=C(241331, 18483, -197221, 62593, 166923, 6853, 236369, -44573), prior=C(208486, -84199, -168053, -43766, 171784, -94, 127924, -18840)), scale=1000),
]
for d in docs:
    if d.get("bs") is None:
        d.pop("bs", None)
(HERE / "manual_6015.json").write_text(json.dumps(docs, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
