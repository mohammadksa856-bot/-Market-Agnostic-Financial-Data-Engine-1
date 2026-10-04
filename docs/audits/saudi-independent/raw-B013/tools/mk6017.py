"""Page transcription for 6017 JAHEZ (full SAR). Writes transcripts/6017.json. Values read from the cited pdf pages."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "6017.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, capex, cfi, cff, net, b, e):
    return dict(cfo=cfo, capex=capex, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e)


def inc(rev, cost, gp, op, pbt, tax, ni, par, nci, **k):
    return dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, ni_parent=par, ni_nci=nci, **k)


D = []
D.append(dict(sha256_prefix="b9421e85", label="FY2025 audited consolidated FS (standalone, whole-file scan; collector label 2026|FY)",
  period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading="visual: whole-file scan, 64 textless pages; pdf p8 BS (printed 6), p9 IS+OCI (7), p11 CF (9) rendered and read",
  pages=dict(bs=8, is_=9, cf=11),
  bs=dict(cur=bs(2452458554, 1038244196, 1414214358, 428423257, 287540467, equity_parent=1341661269, equity_nci=72553089),
          prior=bs(1770075646, 520635218, 1249440428, 1054080837, 210753570, equity_parent=1240431729, equity_nci=9008699)),
  is_=dict(cur=inc(2323639572, -1793551030, 530088542, 49401786, 61532995, -3587455, 57945540, 72974832, -15029292, eps_basic=0.36),
           prior=inc(2218662735, -1677500170, 541162565, 168863674, 204594638, -20376493, 184218145, 187979245, -3761100, eps_basic=0.92)),
  cf=dict(cur=cf(99834675, -37989622, -809444938, 83952683, -625657580, 1054080837, 428423257),
          prior=cf(202791779, -175399885, -137582020, -120188443, -54978684, 1109059521, 1054080837))))
D.append(dict(sha256_prefix="d9587e85", label="Annual Report 2025 (English, text layer) copy of FY2025 audited FS; label 2025|FY is correct",
  period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading="text layer: pdf p95 BS+IS spread (printed 188-189), p96-97 CF (printed 192-193); tied to the standalone scan",
  pages=dict(bs=95, is_=95, cf=97),
  bs=dict(cur=bs(2452458554, 1038244196, 1414214358, 428423257, 287540467), prior=bs(1770075646, 520635218, 1249440428, 1054080837, 210753570)),
  is_=dict(cur=inc(2323639572, -1793551030, 530088542, 49401784, 61532995, -3587455, 57945540, 72974832, -15029292,
                   _declared_diff={"operating_income": "annual-report copy shows other income 220,059 and operating profit 49,401,784, standalone FS 220,061 and 49,401,786 (SAR 2 rounding difference; finance costs 8,878,605 vs 8,878,607; totals below identical)"}),
           prior=inc(2218662735, -1677500170, 541162565, 168863674, 204594638, -20376493, 184218145, 187979245, -3761100)),
  cf=dict(cur=cf(99834675, -37989622, -809444938, 83952683, -625657580, 1054080837, 428423257),
          prior=cf(202791779, -175399885, -137582020, -120188443, -54978684, 1109059521, 1054080837))))
D.append(dict(sha256_prefix="20131ae2", label="FY2024 audited consolidated FS (standalone, text layer; collector label 2025|FY = publication year)",
  period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
  reading="text layer: pdf p7 BS (printed 5), p8 IS (6), p10 CF (8)", pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(1770075646, 520635218, 1249440428, 1054080837, 210753570), prior=bs(1650795840, 505316896, 1145478944, 1109059521, 53839230)),
  is_=dict(cur=inc(2218662735, -1677500170, 541162565, 168863674, 204594638, -20376493, 184218145, 187979245, -3761100, eps_basic=0.92),
           prior=inc(1784755283, -1378877760, 405877523, 101895079, 145833239, -27065630, 118767609, 125336967, -6569358, eps_basic=0.61)),
  cf=dict(cur=cf(202791779, -175399885, -137582020, -120188443, -54978684, 1109059521, 1054080837),
          prior=cf(256867520, -23343175, -16068703, -34425038, 206373779, 902685742, 1109059521))))
D.append(dict(sha256_prefix="cbe8b249", label="FY2023 audited consolidated FS (standalone; statement pages image-only inside a file classed financial_statements; collector label 2024|FY = publication year)",
  period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
  reading="visual: pdf p7-10 textless (images); p7 BS (printed 5), p8 IS (6), p10 CF (8) rendered and read",
  pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(1650795840, 505316896, 1145478944, 1109059521, 53839230), prior=bs(1410885160, 406919485, 1003965675, 902685742, 40355671)),
  is_=dict(cur=inc(1784755283, -1378877760, 405877523, 101895079, 145833239, -27065630, 118767609, 125336967, -6569358, eps_basic=0.61),
           prior=inc(1602476839, -1243297002, 359179837, 64020022, 84827732, -28304442, 56523290, 58977006, -2453716,
                     eps_basic=0.29, _declared_diff={"eps_basic": "FY2022 EPS 0.29 here versus 5.7 in the FY2022 annual report (re-presented; cause not verified from pages)"})),
  cf=dict(cur=cf(256867520, -23343175, -16068703, -34425038, 206373779, 902685742, 1109059521),
          prior=cf(7197709, -37165475, -219056066, 722856097, 510997740, 391688002, 902685742))))
D.append(dict(sha256_prefix="115c111e", label="Annual Report 2022 (English, text) with audited FY2022 FS; collector label 2022|FY",
  period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
  reading="text layer: pdf p124 BS (printed 122), p125 IS (123), p128 CF (126)", pages=dict(bs=124, is_=125, cf=128),
  bs=dict(cur=bs(1410885160, 406919485, 1003965675, 902685742, 40355671), prior=bs(494016310, 305700009, 188316301, 391688002, 7783014)),
  is_=dict(cur=inc(1602476839, -1243297002, 359179837, 64020022, 84827732, -28304442, 56523290, 58977006, -2453716, eps_basic=5.7),
           prior=inc(1159567962, -914043363, 245524599, 119776508, 121197798, -4487725, 116710073, 117068284, -358211, eps_basic=19.6)),
  cf=dict(cur=cf(7197709, -37165475, -219056066, 722856097, 510997740, 391688002, 902685742),
          prior=cf(206178367, -3878688, -16920150, -3294171, 185964046, 205723956, 391688002))))
D.append(dict(sha256_prefix="401e9014", label="Interim condensed consolidated FS 3M and 6M ended 30 June 2025 (English; inventory class partial_statements but BS, IS, CF are present)",
  period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
  reading="text layer: pdf p4 BS (printed 1), p5 IS (2), p7 CF (4)", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(1903377545, 596737336, 1306640209, 1073619018, 210818990), prior=bs(1770075646, 520635218, 1249440428, 1054080837, 210753570)),
  is_=dict(cur=inc(1093034293, -847781572, 245252721, 49065058, 62770836, -9775336, 52995500, 58914800, -5919300),
           prior=inc(1021894232, -804976568, 216917664, 32518467, 53507289, -10476493, 43030796, 42692632, 338164)),
  is_q=dict(cur=inc(567077409, -447800116, 119277293, 14810569, 24177932, -4500336, 19677596, 23595391, -3917795),
            prior=inc(540962580, -419683827, 121278753, 27318410, 37779933, -6450000, 31329933, 30244298, 1085635)),
  cf=dict(cur=cf(37855777, -7264469, -1956844, -16360752, 19538181, 1054080837, 1073619018),
          prior=cf(9232348, -158053820, -240107541, -59019479, -289894672, 1109059521, 819164849))))
D.append(dict(sha256_prefix="1e407fc6", label="Interim condensed consolidated FS 3M and 6M ended 30 June 2026 (English; inventory class partial_statements but BS, IS, CF are present)",
  period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
  reading="text layer: pdf p4 BS (printed 2), p5 IS (3), p7 CF (5); pdf p36-37 textless, not read", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(2603501045, 1218664946, 1384836099, 436054084, 314270350), prior=bs(2452458554, 1038244196, 1414214358, 428423257, 287540467)),
  is_=dict(cur=inc(1488075881, -1181715699, 306360182, -31519362, -37240462, 3380006, -33860456, -26579097, -7281359),
           prior=inc(1093034293, -847781572, 245252721, 49065058, 62770836, -9775336, 52995500, 58914800, -5919300)),
  is_q=dict(cur=inc(762963286, -625750003, 137213283, -22209863, -25693511, 3501969, -22191542, -17396148, -4795394),
            prior=inc(567077409, -447800116, 119277293, 14810569, 24177932, -4500336, 19677596, 23595391, -3917795)),
  cf=dict(cur=cf(140165038, -39430655, -86568506, -45965705, 7630827, 428423257, 436054084),
          prior=cf(37855777, -7264469, -1956844, -16360752, 19538181, 1054080837, 1073619018))))
D.append(dict(sha256_prefix="707a731f", label="Interim condensed consolidated FS 3M ended 31 March 2026 (English; inventory class partial_statements but BS, IS, CF are present)",
  period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
  reading="text layer: pdf p4 BS, p5 IS, p7 CF (printed 5)", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(2608255044, 1203269911, 1404985133, 510685237, 305156058), prior=bs(2452458554, 1038244196, 1414214358, 428423257, 287540467)),
  is_=dict(cur=inc(725112595, -555965696, 169146899, None, -11546951, -121963, -11668914, -9182949, -2485965),
           prior=inc(525956884, -399981456, 125975428, None, 38592904, -5275000, 33317904, 35319409, -2001505)),
  cf=dict(cur=cf(157126724, -25483602, -49033260, -25831484, 82261980, 428423257, 510685237),
          prior=cf(-47951803, -1439176, 4979982, -8371987, -51343808, 1054080837, 1002737029))))


def fix(d):
    d = dict(d)
    if "is_" in d:
        d["is"] = d.pop("is_")
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    for blk in ("is", "is_q"):
        if blk in d:
            for col in d[blk].values():
                for k in [k for k, v in col.items() if v is None]:
                    del col[k]
    return d


roll = [
    dict(name="Q1 2026 + Q2 2026 = H1 2026 revenue", total=["1e407fc6", "is", "cur", "revenue"], parts=[["707a731f", "is", "cur", "revenue"], ["1e407fc6", "is_q", "cur", "revenue"]]),
    dict(name="Q1 2026 + Q2 2026 = H1 2026 net income", total=["1e407fc6", "is", "cur", "net_income"], parts=[["707a731f", "is", "cur", "net_income"], ["1e407fc6", "is_q", "cur", "net_income"]]),
    dict(name="Q1 2026 + Q2 2026 = H1 2026 parent income", total=["1e407fc6", "is", "cur", "ni_parent"], parts=[["707a731f", "is", "cur", "ni_parent"], ["1e407fc6", "is_q", "cur", "ni_parent"]]),
    dict(name="Q1 2025 (comparative in Q1 2026) + Q2 2025 = H1 2025 revenue", total=["401e9014", "is", "cur", "revenue"], parts=[["707a731f", "is", "prior", "revenue"], ["401e9014", "is_q", "cur", "revenue"]]),
    dict(name="Q1 2025 + Q2 2025 = H1 2025 net income", total=["401e9014", "is", "cur", "net_income"], parts=[["707a731f", "is", "prior", "net_income"], ["401e9014", "is_q", "cur", "net_income"]]),
]
t = dict(symbol="6017", name="JAHEZ", currency="SAR", unit="full SAR (no scaling) in every filing read", docs=[fix(d) for d in D], roll_checks=roll)
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("docs", len(D))
