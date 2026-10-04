"""Writes transcripts/8240.json (page transcriptions, SAR full units) for Chubb Arabia."""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "transcripts" / "8240.json"

def bs(ta, tl, te, cash, ppe, **k): return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)
def cf(cfo, cfi, cff, net, b, e, **k): return dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)
def inc(rev, pbt, tax, ni, **k): return dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni, ni_parent=ni, ni_nci=0, **k)

IFRS17 = "IFRS 4 to IFRS 17 transition restatement: this value is the restated comparative in the FY2023 filing (7e9a7064); the original filing (403fab90) value is declared in the other document"
docs = [
 dict(sha256_prefix="170333be", label="FY2025 audited FS (scan with poor OCR; read as images); collector label 2026|FY = publication year", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
  reading="visual: pdf p8 BS (printed 7), p9 IS (8), p12-13 CF (11-12); text layer is garbled OCR so it was not used",
  pages=dict(bs=8, is_=9, cf="12-13"),
  bs=dict(cur=bs(790215871, 313279092, 476936779, 20896722, 2350271), prior=bs(687820272, 233405672, 454414600, 38781683, 3009239)),
  **{"is": dict(cur=inc(392965748, 17202029, -6585158, 10616871, eps_basic=0.27), prior=inc(383410199, 21655747, -5363096, 16292651, eps_basic=0.41))},
  cf=dict(cur=cf(29126656, -44960366, -2051251, -17884961, 38781683, 20896722), prior=cf(14505516, -14203662, 0, 301854, 38479829, 38781683))),
 dict(sha256_prefix="a323e350", label="FY2024 audited FS (scan; collector label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
  reading="visual: pdf p8 BS (printed 7), p9 IS (8), p12-13 CF (11-12)", pages=dict(bs=8, is_=9, cf="12-13"),
  bs=dict(cur=bs(687820272, 233405672, 454414600, 38781683, 3009239), prior=bs(758402678, 334562365, 423840313, 38479829, 2215348)),
  **{"is": dict(cur=inc(383410199, 21655747, -5363096, 16292651, eps_basic=0.54, _declared_diff={"eps_basic": "EPS 0.54 on 30,000,000 shares here; restated to 0.41 in FY2025 filing after the 100,000,000 bonus issue (40,000,000 shares)"}), prior=inc(329438071, 32302258, -7484702, 24817556, eps_basic=0.83))},
  cf=dict(cur=cf(14505516, -14203662, 0, 301854, 38479829, 38781683), prior=cf(36166094, -22606079, 0, 13560015, 24919814, 38479829))),
 dict(sha256_prefix="7e9a7064", label="FY2023 audited FS, first IFRS 17 year (scan; collector label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
  reading="visual: pdf p10 BS (printed 10), p11 IS (11), p14-15 CF (14-15)", pages=dict(bs=10, is_=11, cf="14-15"),
  bs=dict(cur=bs(758402678, 334562365, 423840313, 38479829, 2215348),
          prior=bs(700191701, 305389223, 394802478, 24919814, 2704838, restated=True)),
  **{"is": dict(cur=inc(329438071, 32302258, -7484702, 24817556, eps_basic=0.83),
               prior=inc(299355899, 19692047, -7154463, 12537584, eps_basic=0.42, restated=True, _extra_keys=[]))},
  cf=dict(cur=cf(36166094, -22606079, 0, 13560015, 24919814, 38479829),
          prior=cf(25027676, -186151747, 0, -161124071, 186043885, 24919814, restated=True))),
 dict(sha256_prefix="403fab90", label="FY2022 audited FS as originally issued under IFRS 4 (scan; collector label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
  reading="visual: pdf p7-8 BS (printed 1-2), p9-10 IS (3-4), p13-14 CF (7-8)", pages=dict(bs="7-8", is_="9-10", cf="13-14"),
  bs=dict(cur=bs(894348594, 533161539, 361187055, 24919814, 2704838, _declared_diff={"total_assets": IFRS17, "total_liabilities": IFRS17, "total_equity": IFRS17}),
          prior=bs(809216980, 452515346, 356701634, 186043885, 2323765)),
  **{"is": dict(cur=dict(pbt=11851571, tax=-7154463, net_income=4697108, ni_parent=4697108, ni_nci=0, gross_premiums_written=303677133, income_before_surplus_zakat_tax=13396057, eps_basic=0.16,
                         _declared_diff={"pbt": IFRS17, "net_income": IFRS17, "ni_parent": IFRS17}),
               prior=dict(pbt=13535628, tax=-6373365, net_income=7162263, ni_parent=7162263, ni_nci=0, gross_premiums_written=290581787, income_before_surplus_zakat_tax=15316994, eps_basic=0.24))},
  cf=dict(cur=cf(25709217, -186833288, 0, -161124071, 186043885, 24919814, _declared_diff={"cfo": IFRS17, "cfi": IFRS17}),
          prior=cf(976593, 60395877, -11122227, 50250243, 135793642, 186043885))),
 dict(sha256_prefix="1a8ef8d7", label="3M and 6M ended 2026-06-30 reviewed interim (scan statements; label 2026|H1 correct)", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
  reading="visual: pdf p4 BS (printed 3), p5 IS (4), p8-9 CF (7-8); columns: three-month 2026, three-month 2025, six-month 2026, six-month 2025",
  pages=dict(bs=4, is_=5, cf="8-9"),
  bs=dict(cur=bs(763650919, 283824643, 479826276, 47398021, 2009862), prior=bs(790215871, 313279092, 476936779, 20896722, 2350271)),
  **{"is": dict(cur=inc(199366392, 7447062, -3541476, 3905586), prior=inc(191059250, 7490286, -3518263, 3972023)),
     "is_q": dict(cur=inc(102822668, 2481284, -1570578, 910706), prior=inc(100467258, 2213134, -1201163, 1011971))},
  cf=dict(cur=cf(11461157, 16756368, -1716226, 26501299, 20896722, 47398021), prior=cf(57422451, 56916873, -1804652, 112534672, 38781683, 151316355))),
 dict(sha256_prefix="a73e4e47", label="3M ended 2026-03-31 reviewed interim (scan statements; label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", period_type="Q1",
  reading="visual: pdf p5 IS (printed 4), p7 changes in equity (6), p8 CF (7)", pages=dict(is_=5, cf=8),
  **{"is": dict(cur=inc(96543724, 4965778, -1970898, 2994880), prior=inc(90591992, 5277152, -2317100, 2960052))},
  cf=dict(cur=cf(10086764, 6446281, -1716226, 14816819, 20896722, 35713541), prior=cf(25643239, 50620491, -1604652, 74659078, 38781683, 113440761))),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
rolls = []
def roll(name, tot, parts):
    rolls.append(dict(name=name, total=tot, parts=parts))
for key in ("revenue", "net_income", "pbt"):
    roll(f"Q1 2026 + Q2 2026 = H1 2026 {key}", ["1a8ef8d7", "is", "cur", key], [["a73e4e47", "is", "cur", key], ["1a8ef8d7", "is_q", "cur", key]])
    roll(f"Q1 2025 + Q2 2025 = H1 2025 {key}", ["1a8ef8d7", "is", "prior", key], [["a73e4e47", "is", "prior", key], ["1a8ef8d7", "is_q", "prior", key]])
t = dict(symbol="8240", name="CHUBB ARABIA COOPERATIVE INSURANCE COMPANY", currency="SAR", unit="full SAR (no scaling) in every filing read", docs=docs, roll_checks=rolls)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("ok")
