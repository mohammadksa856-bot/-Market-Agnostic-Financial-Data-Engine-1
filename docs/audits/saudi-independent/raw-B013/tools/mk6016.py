"""Page transcription for 6016 BURGERIZZR (Bait Alshateera Fast Food Restaurants; full SAR). Writes transcripts/6016.json."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "6016.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, capex, cfi, cff, net, b, e, fx=None, **k):
    d = dict(cfo=cfo, capex=capex, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)
    if fx:
        d["fx"] = fx
    return d


def inc(rev, cost, gp, op, pbt, tax, ni, par=None, nci=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, **k)
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
D = []
D.append(dict(sha256_prefix="c85e4452", label="FY2022 FS as issued (statement pages image-only; inventory class other_no_statements_found; collector label 2023|FY = publication year)",
  period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
  reading="visual: pdf p3-9 textless; p6 BS (printed 5), p7 IS (6), p9 CF (8) rendered and read", pages=dict(bs=6, is_=7, cf=9),
  bs=dict(cur=bs(151239051, 94303046, 56936005, 6843214, 77846436), prior=bs(143674917, 88932939, 54741978, 7886360, 70136277)),
  is_=dict(cur=inc(250436084, -182125953, 68310131, 5735270, 3159417, -462445, 2696972, eps_basic=0.77),
           prior=inc(234782861, -164700593, 70082268, 17750704, 15877630, -509975, 15367655, eps_basic=4.39)),
  cf=dict(cur=cf(32756426, -6175349, -20488931, -13310641, -1043146, 7886360, 6843214),
          prior=cf(34009833, -8704078, -22332174, -10105790, 1571869, 6314491, 7886360))))
D.append(dict(sha256_prefix="b38de818", label="FY2023 FS as issued (statement pages image-only; collector label 2024|FY = publication year)",
  period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
  reading="visual: pdf p3-9 textless; p6 BS (printed 5), p7 IS (6), p9 CF (8) rendered and read", pages=dict(bs=6, is_=7, cf=9),
  bs=dict(cur=bs(145149233, 76282047, 68867186, 12650781, 76981033), prior=bs(151239051, 94303046, 56936005, 6843214, 77846436)),
  is_=dict(cur=inc(281053038, -196308401, 84744637, 15814450, 12683417, -398140, 12285277, eps_basic=0.351),
           prior=inc(250436084, -182125953, 68310131, 5735270, 3159417, -462445, 2696972, eps_basic=0.077,
                     _declared_diff={"eps_basic": "FY2022 EPS 0.077 (marked Restated, 35,000,000 shares) versus 0.77 in the FY2022 filing (10 times)"})),
  cf=dict(cur=cf(41035968, -9441811, -11140068, -24088333, 5807567, 6843214, 12650781),
          prior=cf(32756426, -6175349, -20488931, -13310641, -1043146, 7886360, 6843214,
                   _declared_diff={"cff": "total unchanged; inside financing, repayment of loans -8,755,055 in the FY2022 filing is split into -7,811,200 and finance cost paid -943,855 here"}))))
D.append(dict(sha256_prefix="38566848", label="FY2024 FS as originally issued (statement pages image-only; inventory class partial_statements; collector label 2025|FY = publication year)",
  period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
  reading="visual: pdf p3-9 textless; p6 BS (printed 5), p7 IS (6), p9 CF (8) rendered and read", pages=dict(bs=6, is_=7, cf=9),
  bs=dict(cur=bs(151245092, 79185637, 72059455, 12152895, 81899777), prior=bs(145149233, 76282047, 68867186, 12650781, 76981033)),
  is_=dict(cur=inc(299575519, -208624984, 90950535, 10970308, 8693599, -248098, 8445501, eps_basic=0.24),
           prior=inc(281053038, -196308401, 84744637, 15814450, 12683417, -398140, 12285277, eps_basic=0.35)),
  cf=dict(cur=cf(35988610, -12121641, -19012944, -17473552, -497886, 12650781, 12152895),
          prior=cf(41035968, -9441811, -11140068, -24088333, 5807567, 6843214, 12650781))))
D.append(dict(sha256_prefix="dd1c4fa1", label="FY2025 consolidated FS; FY2024 and 1 Jan 2024 columns RESTATED (Note 30, IAS 8); statement pages image-only (inventory class partial_statements; collector label 2026|FY)",
  period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading="visual: pdf p3-10 textless; p7 BS (printed 5), p8 IS (6), p10 CF (8) rendered and read; Note 30 pdf p35 text",
  pages=dict(bs=7, is_=8, cf=10),
  bs=dict(cur=bs(223350412, 141218036, 82132376, 21114749, 104439451, equity_parent=80359366, equity_nci=1773010),
          prior=bs(149442492, 79185637, 70256855, 12152895, 81899777, restated=R)),
  bs_third_column_1jan2024_restated=bs(143605425, 76282047, 67323378, 12650781, 76981033),
  is_=dict(cur=inc(366481879, -248217682, 118264197, 15141627, 11423034, -284086, 11138948, 10914889, 224059, eps_basic=0.31),
           prior=inc(299575519, -208883776, 90691743, 10711516, 8434807, -248098, 8186709, 8186709, 0, eps_basic=0.23, restated=R)),
  cf=dict(cur=cf(57825404, -15036255, -43470432, -5875999, 8478973, 12152895, 21114749, fx=482881),
          prior=cf(34875418, -12121641, -19012944, -16360360, -497886, 12650781, 12152895, restated=R))))
D.append(dict(sha256_prefix="a61dd916", label="Interim condensed FS 3M and 6M ended 2025-06-30 as originally issued (statement pages image-only; inventory class partial_statements)",
  period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
  reading="visual: pdf p3-7 textless; p4 BS (printed 3), p5 IS (4), p7 CF (6) rendered and read", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(158018077, 83175882, 74842195, 10908183, 85644821), prior=bs(151245092, 79185637, 72059455, 12152895, 81899777)),
  is_=dict(cur=inc(162245731, -113840437, 48405294, 4066156, 3355398, -81995, 3273403, eps_basic=0.09),
           prior=inc(146077780, -99069179, 47008601, 7844986, 6880251, -191322, 6688929, eps_basic=0.19)),
  is_q=dict(cur=inc(83812174, -59684445, 24127729, 1407423, 1099211, -25590, 1073621, eps_basic=0.03),
            prior=inc(70261367, -49122412, 21138955, 2009823, 1473878, -50722, 1423156, eps_basic=0.04)),
  cf=dict(cur=cf(19968340, -4538751, -13707243, -7505809, -1244712, 12152895, 10908183),
          prior=cf(19672256, -5059671, -8116377, -12265609, -709730, 12650781, 11941051))))
D.append(dict(sha256_prefix="0fda6794", label="Interim condensed consolidated FS 3M and 6M ended 2026-06-30; 2025 comparatives RESTATED (Note 14); statement pages image-only (inventory class results_announcement)",
  period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
  reading="visual: pdf p5-8 textless; p5 BS (printed 3), p6 IS (4), p8 CF (6) rendered and read; Note 14 pdf p17 text", pages=dict(bs=5, is_=6, cf=8),
  bs=dict(cur=bs(221454429, 132301004, 89153425, 16510198, 106359130, equity_nci=3491617), prior=bs(223350412, 141218036, 82132376, 21114749, 104439451)),
  is_=dict(cur=inc(218932295, -143684857, 75247438, 16129946, 13248885, -320891, 12927994, 11209387, 1718607, eps_basic=0.20),
           prior=inc(162245731, -114047599, 48198132, 3858994, 3148236, -81995, 3066241, 3066241, 0, eps_basic=0.05, restated=R)),
  is_q=dict(cur=inc(114216928, -75385081, 38831847, 8542539, 6820170, -160173, 6659997, 5487334, 1172663, eps_basic=0.10),
            prior=inc(83812174, -59587833, 24224341, 1504035, 1195823, -25590, 1170233, 1170233, 0, eps_basic=0.02, restated=R)),
  cf=dict(cur=cf(23375389, -8468434, -9272013, -18707927, -4604551, 21114749, 16510198),
          prior=cf(19968340, -4538751, -13707243, -7505809, -1244712, 12152895, 10908183))))
D.append(dict(sha256_prefix="ef72a63d", label="Condensed interim consolidated FS 3M ended 2026-03-31; Q1 2025 comparative RESTATED (Note 16); statement pages image-only (inventory class other_no_statements_found)",
  period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
  reading="visual: pdf p3-7 textless; p4 BS (printed 3), p5 IS (4), p6 equity (5), p7 CF (6) rendered and read", pages=dict(bs=4, is_=5, cf=7),
  bs=dict(cur=bs(225653369, 137252996, 88400373, 21506239, 104254456, equity_nci=2318954), prior=bs(223350412, 141218036, 82132376, 21114749, 104439451)),
  is_=dict(cur=inc(104715367, -68299776, 36415591, 7587407, 6428715, -160718, 6267997, 5722053, 545944, eps_basic=0.10),
           prior=inc(78433557, -54459766, 23973791, 2354959, 1952413, -56405, 1896008, 1896008, 0, eps_basic=0.03, restated=R)),
  cf=dict(cur=cf(10238265, -2146823, -3196180, -6650595, 391490, 21114749, 21506239),
          prior=cf(11411175, -2209038, -6493976, -4193550, 723649, 12152895, 12876544, restated=R))))

P = lambda pre, blk, col, key: [pre, blk, col, key]
roll = []
for key in ("revenue", "cost_of_revenue", "operating_income", "pbt", "net_income", "ni_parent"):
    roll.append(dict(name=f"Q1 2026 + Q2 2026 = H1 2026 {key}", total=P("0fda6794", "is", "cur", key), parts=[P("ef72a63d", "is", "cur", key), P("0fda6794", "is_q", "cur", key)]))
for key in ("revenue", "operating_income", "net_income"):
    roll.append(dict(name=f"Q1 2025 restated + Q2 2025 restated = H1 2025 restated {key}", total=P("0fda6794", "is", "prior", key), parts=[P("ef72a63d", "is", "prior", key), P("0fda6794", "is_q", "prior", key)]))
t = dict(symbol="6016", name="BURGERIZZR (Bait Alshateera Fast Food Restaurants; Shatirah House Restaurants Co.)", currency="SAR", unit="full SAR (no scaling) in every filing read", docs=[fix(d) for d in D], roll_checks=roll)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("docs", len(D))
