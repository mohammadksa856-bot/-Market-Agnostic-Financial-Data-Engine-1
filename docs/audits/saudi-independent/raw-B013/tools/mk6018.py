"""Page transcription for 6018 SPORT CLUBS (full SAR). Writes transcripts/6018.json."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "6018.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, capex, cfi, cff, net, b, e):
    d = dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e)
    if capex is not None:
        d["capex"] = capex
    return d


def inc(rev, cost, gp, op, pbt, tax, ni, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, **k)
    return d


def fix(d):
    d = dict(d)
    if "is_" in d:
        d["is"] = d.pop("is_")
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    return d


D = []
D.append(dict(sha256_prefix="95156e7d", label="FY2022 STANDALONE financial statements as originally issued (collector label 2025|FY)",
  period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
  reading="text layer: pdf p5 BS (printed 4), p6 IS (5), p8 CF (7); pdf p3-4 textless (auditor's review report)", pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(673178718, 538706328, 134472390, 15895356, 382306270), prior=bs(673679752, 558263330, 115416422, 16135878, 379515958)),
  is_=dict(cur=inc(268043244, -197190499, 70852745, 46571111, 24946299, -684793, 24261506, eps_basic=2.33),
           prior=inc(204358263, -164631924, 39726339, 24140589, 11625889, -450000, 11175889, eps_basic=1.07)),
  cf=dict(cur=cf(107040193, -37723893, -36851780, -70428935, -240522, 16135878, 15895356),
          prior=cf(72466478, -69862075, -70332822, 5261607, 7395263, 8740615, 16135878))))
D.append(dict(sha256_prefix="a34966d0", label="FY2023 consolidated financial statements with FY2022 and FY2021 comparatives RESTATED (Note 33); collector label 2025|FY",
  period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
  reading="text layer: pdf p5 BS (printed 4), p6 IS (5), p8 CF (7); Note 33 pdf p46-47; third column is 1 Jan 2022 / FY2021 restated",
  pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(757092838, 613682374, 143410464, 8641035, 408073520),
          prior=bs(665941152, 540035724, 125905428, 17297313, 373739309, restated=True)),
  bs_third_column_1jan2022_restated=bs(666984724, 558556584, 108428140, 16511632, 372527676),
  is_=dict(cur=inc(270620715, -198235704, 72385011, 50046585, 25896646, -808231, 25088415, eps_basic=2.41),
           prior=inc(268043244, -198769179, 69274065, 44992431, 23377557, -694731, 22682826, eps_basic=2.18, restated=True)),
  is_third_column_2021_restated=inc(204358263, -167841507, 36516756, 20931006, 8418806, -452500, 7966306, eps_basic=0.77),
  cf=dict(cur=cf(134176688, -66040164, -67304721, -75528245, -8656278, 17297313, 8641035),
          prior=cf(105484804, -32639060, -31266920, -73432203, 785681, 16511632, 17297313, ) | {"restated": True})))
D.append(dict(sha256_prefix="0f9cafac", label="FY2024 consolidated financial statements as originally issued (collector label 2025|FY)",
  period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
  reading="text layer: pdf p5 BS (printed 4), p6 IS (5), p8 CF (7); pdf p3-4 textless", pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(798406606, 629597736, 168808870, 5026406, 465149962), prior=bs(757092838, 613682374, 143410464, 8641035, 408073520)),
  is_=dict(cur=inc(327425956, -228880727, 98545229, 69216266, 39003873, -934132, 38069741, eps_basic=0.37),
           prior=inc(270620715, -198235704, 72385011, 50046585, 25896646, -808231, 25088415, eps_basic=0.24,
                     _declared_diff={"eps_basic": "2023 EPS 0.24 here versus 2.41 in the FY2023 filing (share count 104,000,000 after a 10-for-1 change versus 10,400,000; basis not read from the notes)"})),
  cf=dict(cur=cf(103143540, None, -89994914, -16763255, -3614629, 8641035, 5026406),
          prior=cf(134176688, -66040164, -67304721, -75528245, -8656278, 17297313, 8641035))))
D.append(dict(sha256_prefix="5fc6d9e9", label="FY2025 consolidated financial statements with FY2024 and 1 Jan 2024 comparatives RESTATED (Note 34, IAS 8); collector label 2026|FY",
  period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading="text layer: pdf p6 BS (printed 5), p7 IS (6), p9 CF (8); restatement Note 34 pdf p44-45; pdf p3-5 textless",
  pages=dict(bs=6, is_=7, cf=9),
  bs=dict(cur=bs(944706742, 674195901, 270510841, 46676425, 539778851),
          prior=bs(794329395, 629597737, 164731658, 5026406, 463355727, restated=True)),
  bs_third_column_1jan2024_restated=bs(754980998, 613682374, 141298624, 8641035, 407306143),
  is_=dict(cur=inc(376239000, -263766303, 112472697, 74361622, 42228233, -1061368, 41166865, eps_basic=0.38),
           prior=inc(327425956, -230737456, 96688500, 64399279, 37038501, -934132, 36104369, eps_basic=0.35, restated=True)),
  cf=dict(cur=cf(159440308, -113590101, -116710183, -1080106, 41650019, 5026406, 46676425),
          prior=cf(104170083, -91437508, -89994917, -17789795, -3614629, 8641035, 5026406) | {"restated": True})))
D.append(dict(sha256_prefix="0032c8f3", label="Interim condensed consolidated FS 3M and 6M ended 2025-06-30 (statement pages image-only; inventory finds only index pages)",
  period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
  reading="visual: pdf p3-7 textless; p4 BS (printed 3), p5 IS (4), p7 CF (6) rendered and read", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(844557154, 667757089, 176800065, 5652880, 481629302), prior=bs(798406606, 629597736, 168808870, 5026406, 465149962)),
  is_=dict(cur=inc(166849415, -127438391, 39411024, 25552739, 10539458, -266668, 10272790, eps_basic=0.099),
           prior=inc(140502730, -105618017, 34884713, 21142401, 9641065, -268179, 9372886, eps_basic=0.090)),
  is_q=dict(cur=inc(84409730, -62209784, 22199946, 15389781, 7019146, -152167, 6866979),
            prior=inc(70868520, -53339103, 17529417, 11250701, 5532656, -161028, 5371628)),
  cf=dict(cur=cf(50700042, -35806092, -37199068, -12874500, 626474, 5026406, 5652880),
          prior=cf(7963215, -32471720, -32763857, 24856754, 56112, 8641035, 8697147))))
D.append(dict(sha256_prefix="7e6a815f", label="Condensed consolidated interim FS 3M and 6M ended 2026-06-30",
  period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
  reading="text layer: pdf p4 BS (printed 3), p5 IS (4), p7 CF (6)", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(990233199, 704521475, 285711724, 44535360, 591542019), prior=bs(944706742, 674195901, 270510841, 46676425, 539778851)),
  is_=dict(cur=inc(192494098, -136716994, 55777104, 34236170, 18587037, -390924, 18196113, eps_basic=0.159),
           prior=inc(166849415, -127438391, 39411024, 25552739, 10539458, -266668, 10272790, eps_basic=0.099)),
  is_q=dict(cur=inc(106378475, -72415050, 33963425, 22533294, 14069396, -274474, 13794922),
            prior=inc(84409730, -62209784, 22199946, 15389781, 7019146, -152167, 6866979)),
  cf=dict(cur=cf(78402835, -71699627, -71690660, -8853240, -2141065, 46676425, 44535360),
          prior=cf(50700042, None, -37199068, -12874500, 626474, 5026406, 5652880))))
D.append(dict(sha256_prefix="275c9f02", label="Condensed consolidated interim FS 3M ended 2026-03-31",
  period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
  reading="text layer: pdf p4 BS (printed 3), p5 IS (4), p7 CF (6); negative figures in the prior column are text-extracted with the bracket after the number", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(951529348, 679871730, 271657618, 33737652, 560560939), prior=bs(944706742, 674195901, 270510841, 46676425, 539778851)),
  is_=dict(cur=inc(86115623, -64301944, 21813679, 11702876, 4517641, -116450, 4401191, eps_basic=0.038),
           prior=inc(82439685, -65228607, 17211078, 10162958, 3520312, -114501, 3405811, eps_basic=0.033)),
  cf=dict(cur=cf(29202500, -30043263, -29941418, -12199855, -12938773, 46676425, 33737652),
          prior=cf(12367430, -17810577, -18077784, 4232829, -1477525, 5026406, 3548881))))

P = lambda pre, blk, col, key: [pre, blk, col, key]
roll = [
    dict(name="Q1 2026 + Q2 2026 = H1 2026 revenue", total=P("7e6a815f", "is", "cur", "revenue"), parts=[P("275c9f02", "is", "cur", "revenue"), P("7e6a815f", "is_q", "cur", "revenue")]),
    dict(name="Q1 2026 + Q2 2026 = H1 2026 net income", total=P("7e6a815f", "is", "cur", "net_income"), parts=[P("275c9f02", "is", "cur", "net_income"), P("7e6a815f", "is_q", "cur", "net_income")]),
    dict(name="Q1 2025 (comparative in Q1 2026) + Q2 2025 = H1 2025 revenue", total=P("0032c8f3", "is", "cur", "revenue"), parts=[P("275c9f02", "is", "prior", "revenue"), P("0032c8f3", "is_q", "cur", "revenue")]),
    dict(name="Q1 2025 + Q2 2025 = H1 2025 net income", total=P("0032c8f3", "is", "cur", "net_income"), parts=[P("275c9f02", "is", "prior", "net_income"), P("0032c8f3", "is_q", "cur", "net_income")]),
    dict(name="Q1 2025 + Q2 2025 = H1 2025 operating income", total=P("0032c8f3", "is", "cur", "operating_income"), parts=[P("275c9f02", "is", "prior", "operating_income"), P("0032c8f3", "is_q", "cur", "operating_income")]),
]
t = dict(symbol="6018", name="SPORT CLUBS", currency="SAR", unit="full SAR (no scaling) in every filing read", docs=[fix(d) for d in D], roll_checks=roll)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("docs", len(D))
