"""Page transcription for 6012 RAYDAN (Raydan Food Company; full SAR). Writes transcripts/6012.json."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "6012.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, capex, cfi, cff, net, b, e, fx=None, **k):
    d = dict(cfo=cfo, capex=capex, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)
    if fx:
        d["fx"] = fx
    return d


def inc(rev, cost, gp, op, pbt, tax, ni, par=None, nci=None, disc=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, **k)
    if disc is not None:
        d["discontinued"] = disc
    if par is not None:
        d["ni_parent"] = par
        d["ni_nci"] = nci
    return d


def fix(d):
    d = dict(d)
    if "is_" in d:
        d["is"] = d.pop("is_")
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
    return d


R = True
VIS = "visual: statement pages textless, rendered and read"
FY24 = bs(196437930, 115459673, 80978257, 1199555, 95501944)
D = []
D.append(dict(sha256_prefix="c08a825b", label="FY2025 FS of Ridan Company Food (Raydan; statement pages image-only; inventory class financial_statements; label 2026|FY = publication year)",
  period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading=VIS + " (pdf p8-13); p9 BS (printed 7), p10 IS (8), p12-13 CF (10-11)", pages=dict(bs=9, is_=10, cf=12),
  bs=dict(cur=bs(136549435, 119403004, 17146431, 1353666, 71356176), prior=dict(FY24)),
  is_=dict(cur=inc(114080252, -125517628, -11437376, -40813975, -64652905, -76218, -64729123, eps_basic=-4.2),
           prior=inc(155367760, -154150349, 1217411, -66046611, -72805202, -300218, -73105420, eps_basic=-4.62, restated=R)),
  cf=dict(cur=cf(1153775, -1088839, 8599309, -9598973, 154111, 1199555, 1353666),
          prior=cf(16160533, -6236726, -6425692, -14116637, -4381796, 6476639, 1199555, fx=-895288))))
D.append(dict(sha256_prefix="80898466", label="FY2024 consolidated FS as issued (statement pages image-only; inventory class partial_statements; label 2025|FY = publication year)",
  period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
  reading=VIS + " (pdf p8-13); p9 BS (printed 7), p10 IS (8), p12 CF (10)", pages=dict(bs=9, is_=10, cf=12),
  bs=dict(cur=dict(FY24), prior=bs(266262198, 112204253, 154057945, 6476639, 131679951, restated=R)),
  is_=dict(cur=inc(155367760, -154150349, 1217411, -67170616, -72805202, -300218, -73105420, -73105420, 0, eps_basic=-4.62),
           prior=inc(177373734, -167718282, 9655452, -23497442, -30619800, -269366, -30889166, -30889166, 0, eps_basic=-1.95)),
  cf=dict(cur=cf(16160533, -6236726, -6425692, -14116637, -4381796, 6476639, 1199555, fx=-895288),
          prior=cf(4973444, -13158499, -11411834, -14550125, -20988515, 27465154, 6476639, restated=R))))
D.append(dict(sha256_prefix="dc9b7753", label="FY2023 consolidated FS as issued (statement pages image-only; label 2024|FY = publication year)",
  period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
  reading=VIS + " (pdf p8-13); p9 BS (printed 7), p10 IS (8), p12 CF (10)", pages=dict(bs=9, is_=10, cf=12),
  bs=dict(cur=bs(266262198, 112204253, 154057945, 6585363, 131679951), prior=bs(280958453, 95964506, 184993947, 27465154, 131278056)),
  is_=dict(cur=inc(177373734, -167718282, 9655452, -23497442, -30619800, -269366, -30889166, -30889166, 0, eps_basic=-1.95),
           prior=inc(159177603, -152694949, 6482654, -14243321, -23689912, -931627, -24621539, -24621384, -155, eps_basic=-0.83)),
  cf=dict(cur=cf(5082168, -13158499, -11411834, -14550125, -20879791, 27465154, 6585363),
          prior=cf(-24650997, -29296830, -11248567, -12823666, -48723230, 76188384, 27465154, restated=R))))
D.append(dict(sha256_prefix="94f34098", label="FY2022 consolidated FS as issued (statement pages image-only; inventory class partial_statements; label 2023|FY = publication year)",
  period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
  reading=VIS + " (pdf p9-13); p9 BS (printed 7), p10 IS (8), p12 CF (10)", pages=dict(bs=9, is_=10, cf=12),
  bs=dict(cur=bs(280958453, 95964506, 184993947, 27465154, 131278056), prior=bs(324839614, 116919297, 207920317, 76188384, 127779212)),
  is_=dict(cur=inc(159177603, -152694949, 6482654, -14243321, -23689912, -931627, -24621539, -24621384, -155, eps_basic=-0.83),
           prior=inc(131168043, -137374571, -6206528, -24228790, -34343839, -470971, -42223505, -42207449, -16056, disc=-7408695, eps_basic=-1.60)),
  cf=dict(cur=cf(-18586904, -29296830, -19609853, -10437566, -48634323, 76188384, 27465154, fx=-88907),
          prior=cf(-23996389, -3926950, -1054617, 95858947, 70807941, 5382116, 76188384, fx=-1673))))
D.append(dict(sha256_prefix="6f8cb490", label="Interim condensed FS 3M and 6M ended 2025-06-30 as issued (statement pages image-only; subsidiary in Egypt under liquidation shown as discontinued)",
  period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
  reading=VIS + " (pdf p4-9); p5 BS (printed 3), p6 IS (4), p7 equity (5), p8 CF (6)", pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(185927249, 123338424, 62588825, 994815, 87761068), prior=dict(FY24)),
  is_=dict(cur=inc(68876490, -79808500, -10932010, -21336147, -18385760, 0, -18389432, -18389432, 0, disc=-3672, eps_basic=-1.16),
           prior=inc(90033832, -83199830, 6834002, -7315940, -4349826, 0, -4909227, -4909227, 0, disc=-559401, eps_basic=-0.28)),
  is_q=dict(cur=inc(24663806, -34869262, -10205456, -14774574, -10544262, 0, -10547196, -10547196, 0, disc=-2934, eps_basic=-0.67),
            prior=inc(47462356, -44704936, 2757420, -5412914, -1233005, 0, -1565959, -1565959, 0, disc=-332954, eps_basic=-0.08)),
  cf=dict(cur=cf(4717031, -862813, 3561778, -8483549, -204740, 1199555, 994815),
          prior=cf(11371521, -4105150, -4298150, -9804562, -2731191, 6585363, 3854172))))
D.append(dict(sha256_prefix="8937ac21", label="Interim condensed FS 3M ended 2025-03-31 as issued (statement pages image-only)",
  period_end="2025-03-31", prior_end="2024-03-31", bs_prior_end="2024-12-31", period_type="Q1",
  reading=VIS + " (pdf p5-9); p5 BS (printed 3), p6 IS (4), p8 CF (6)", pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(197486128, 124350107, 73136021, 5246738, 89944786), prior=dict(FY24)),
  is_=dict(cur=inc(44212684, -44939238, -726554, -5983823, -7841498, 0, -7842236, -7842236, 0, disc=-738, eps_basic=-0.5),
           prior=inc(42571476, -38494894, 4076582, -1130662, -3116821, 0, -3252439, -3252439, 0, disc=-135618, eps_basic=-0.2)),
  cf=dict(cur=cf(6253920, -1303576, 3524730, -5731467, 4047183, 1199555, 5246738),
          prior=cf(4583756, -1666819, -1531201, -5625544, -2572989, 6585363, 4012374))))
D.append(dict(sha256_prefix="87839b51", label="Interim condensed FS 3M ended 2026-03-31 of Ridan Company Food (statement pages image-only; inventory class partial_statements)",
  period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
  reading=VIS + " (pdf p4-9); p5 BS, p6 IS (printed 4), p8 CF; pdf p7 equity statement not read", pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(127713099, 116678255, 11034844, 811232, 59510901), prior=bs(136549435, 119403004, 17146431, 1353666, 71356176)),
  is_=dict(cur=inc(19522387, -20912518, -1390131, -3525365, -6103532, 0, -6111587, -6111587, 0, disc=-8055, eps_basic=-0.8),
           prior=inc(44212684, -44939238, -726554, -6516573, -7841498, 0, -7842236, -7842236, 0, disc=-738, eps_basic=-0.5,
                     _declared_diff={"operating_income": "Q1 2025 operating loss -5,983,823 as issued versus -6,516,573 here: other income 577,750 moved from operating to below operating; pbt and net loss identical"})),
  cf=dict(cur=cf(-4579736, -121095, 8098695, -4061393, -542434, 1353666, 811232),
          prior=cf(6253920, -1303576, 3524730, -5731467, 4047183, 1199555, 5246738))))
D.append(dict(sha256_prefix="10e0e51c", label="Interim condensed FS 3M and 6M ended 2026-06-30; FY2025 balance sheet and H1/Q2 2025 income RE-PRESENTED for discontinued operations (text layer present)",
  period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
  reading="text layer: pdf p4 BS, p5 IS, p7-8 CF", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(105610921, 110795437, -5184516, 1304294, 45532684),
          prior=bs(136806587, 119660156, 17146431, 1353666, 71356176, restated=R)),
  is_=dict(cur=inc(20660235, -25969123, -5308888, -13547932, -15631648, 0, -22330947, disc=-6699299, eps_basic=-3.05),
           prior=inc(53143977, -65188708, -12044731, -17355739, -14312213, 0, -18389432, disc=-4077219, eps_basic=-1.16, restated=R)),
  is_q=dict(cur=inc(3483621, -8484938, -5001317, -11336790, -11286515, 0, -16219360, disc=-4932845, eps_basic=-2.20),
            prior=inc(18332713, -26049381, -7716668, -12298293, -7954728, 0, -10547196, disc=-2592468, eps_basic=-0.67, restated=R)),
  cf=dict(cur=cf(-5700167, -140204, 9748613, -4097818, -49372, 1353666, 1304294),
          prior=cf(4717031, -862813, 3561778, -8483549, -204740, 1199555, 994815))))

P = lambda pre, blk, col, key: [pre, blk, col, key]
roll = [
    dict(name="Q1 2025 + Q2 2025 = H1 2025 revenue (as issued)", total=P("6f8cb490", "is", "cur", "revenue"), parts=[P("8937ac21", "is", "cur", "revenue"), P("6f8cb490", "is_q", "cur", "revenue")]),
    dict(name="Q1 2025 + Q2 2025 = H1 2025 cost of revenue (as issued)", total=P("6f8cb490", "is", "cur", "cost_of_revenue"), parts=[P("8937ac21", "is", "cur", "cost_of_revenue"), P("6f8cb490", "is_q", "cur", "cost_of_revenue")]),
    dict(name="Q1 2025 + Q2 2025 = H1 2025 profit before zakat (as issued)", total=P("6f8cb490", "is", "cur", "pbt"), parts=[P("8937ac21", "is", "cur", "pbt"), P("6f8cb490", "is_q", "cur", "pbt")]),
    dict(name="Q1 2025 + Q2 2025 = H1 2025 net loss (as issued)", total=P("6f8cb490", "is", "cur", "net_income"), parts=[P("8937ac21", "is", "cur", "net_income"), P("6f8cb490", "is_q", "cur", "net_income")]),
    dict(name="Q1 2026 + Q2 2026 = H1 2026 net loss", total=P("10e0e51c", "is", "cur", "net_income"), parts=[P("87839b51", "is", "cur", "net_income"), P("10e0e51c", "is_q", "cur", "net_income")]),
]
t = dict(symbol="6012", name="RAYDAN (Raydan Food Company; styled Ridan Company Food from the FY2025 filing)", currency="SAR", unit="full SAR (no scaling) in every filing read",
         docs=[fix(d) for d in D], roll_checks=roll)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("docs", len(D))
