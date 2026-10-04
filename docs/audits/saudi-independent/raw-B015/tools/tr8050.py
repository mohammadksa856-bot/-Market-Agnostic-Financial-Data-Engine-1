"""Writes transcripts/8050.json (page transcriptions, SAR thousands as printed) for Salama Cooperative Insurance Company."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "8050.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, cfi, cff, net, b, e, **k):
    return dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)


def inc(rev, pbt, tax, ni, **k):
    return dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni, ni_parent=ni, ni_nci=0, **k)


R22 = "IFRS 4 to IFRS 17 transition: FY2022 as issued (16733245) versus restated comparative in the FY2023 filing (44f0c863)"
CF24 = "IAS 7 reclassification of commission income (note 31 of the FY2025 filing): FY2024 as issued CFO -155,575 and CFI -21,810 versus restated -153,278 and -24,107; net change and closing cash unchanged"

docs = [
    dict(sha256_prefix="28ce63c0", label="FY2025 audited FS, SAR thousands (statement pages image-only; label 2026|FY = publication year)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 7), p9 IS (8), p13-14 CF (12-13); pdf p8-14 textless; note 31 text read at pdf p111",
         pages=dict(bs=8, is_=9, cf="13-14"),
         bs=dict(cur=bs(808775, 538879, 269896, 282383, 6064), prior=bs(745506, 491180, 254326, 232803, 6334)),
         **{"is": dict(cur=inc(558377, -90044, -1520, -91564, eps_basic=-3.05), prior=inc(678479, 28620, 1503, 30123, eps_basic=1.23))},
         cf=dict(cur=cf(-1627, -39864, 91071, 49580, 232803, 282383), prior=cf(-153278, -24107, -4897, -182282, 415085, 232803, restated=True))),
    dict(sha256_prefix="ded8b2a2", label="FY2024 audited FS, SAR thousands (statement pages image-only; label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 7), p9 IS (8), p13 CF (12); pdf p3-14 textless",
         pages=dict(bs=8, is_=9, cf=13),
         bs=dict(cur=bs(745506, 491180, 254326, 232803, 6334), prior=bs(806249, 601270, 204979, 415085, 5471)),
         **{"is": dict(cur=inc(678479, 28620, 1503, 30123, eps_basic=1.23), prior=inc(802288, 55302, -4000, 51302, eps_basic=2.68, _declared_diff={"eps_basic": "FY2023 EPS 3.25 as first issued versus 2.68 labelled restated in the FY2024 filing (cause not verified from the pages read)"}))},
         cf=dict(cur=cf(-155575, -21810, -4897, -182282, 415085, 232803, _declared_diff={"cfo": CF24, "cfi": CF24}), prior=cf(53763, 141464, 85093, 280320, 134765, 415085))),
    dict(sha256_prefix="44f0c863", label="FY2023 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (statement pages image-only; label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p10 BS (printed 9), p11 IS (10), p15-16 CF (14-15); pdf p9-16 textless",
         pages=dict(bs=10, is_=11, cf="15-16"),
         bs=dict(cur=bs(806249, 601270, 204979, 415085, 5471), prior=bs(666810, 605954, 60856, 134765, 5154, restated=True)),
         **{"is": dict(cur=inc(802288, 55302, -4000, 51302, eps_basic=3.25, _declared_diff={"eps_basic": "FY2023 EPS 3.25 as first issued versus 2.68 labelled restated in the FY2024 filing (cause not verified)"}),
                       prior=inc(598351, -35866, -3000, -38866, eps_basic=-2.55, restated=True))},
         cf=dict(cur=cf(53763, 141464, 85093, 280320, 134765, 415085), prior=cf(69463, -53679, -5035, 10749, 124016, 134765, restated=True))),
    dict(sha256_prefix="16733245", label="FY2022 audited FS as issued under IFRS 4 (statement pages image-only; label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 6), p9-10 IS (7-8; p9 revenue/underwriting page not transcribed), p13 CF (11); pdf p3-13 textless",
         pages=dict(bs=8, is_="9-10", cf=13),
         bs=dict(cur=bs(765970, 728202, 37768, 134765, 5154, _declared_diff={"total_assets": R22, "total_liabilities": R22, "total_equity": R22}),
                 prior=bs(614541, 518057, 96484, 124016, 4107)),
         **{"is": dict(cur=dict(pbt=-55327, tax=-3000, net_income=-58327, ni_parent=-58327, ni_nci=0, eps_basic=-5.83, _declared_diff={"pbt": R22, "net_income": R22, "ni_parent": R22}),
                       prior=dict(pbt=-106410, tax=-6000, net_income=-112410, ni_parent=-112410, ni_nci=0, eps_basic=-11.24))},
         cf=dict(cur=cf(77841, -62057, -5035, 10749, 124016, 134765, _declared_diff={"cfo": R22, "cfi": R22}), prior=cf(-94346, 60193, -1077, -35230, 159246, 124016))),
    dict(sha256_prefix="c1bacc8f", label="3M and 6M ended 2026-06-30 reviewed interim, SAR thousands (statement pages carry only a signing stamp as text; read as images; label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3), p8 CF (6); income columns three-month 2026, three-month 2025, six-month 2026, six-month 2025",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(807788, 558234, 249554, 133969, 6102), prior=bs(808775, 538879, 269896, 282383, 6064)),
         **{"is": dict(cur=inc(333800, -18842, -1500, -20342), prior=inc(272614, -38849, -283, -39132)),
            "is_q": dict(cur=inc(172423, -16018, -1000, -17018), prior=inc(140731, -3211, -500, -3711))},
         cf=dict(cur=cf(-13554, -130652, -4208, -148414, 282383, 133969), prior=cf(-71025, -42125, 91660, -21490, 232803, 211313))),
    dict(sha256_prefix="fdad4f76", label="3M ended 2026-03-31 reviewed interim, SAR thousands (image-only statement pages; label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", period_type="Q1",
         reading="visual: pdf p5 IS (printed 4), p8 CF (7); pdf p4-8 textless; balance sheet (pdf p4) not transcribed",
         pages=dict(is_=5, cf=8),
         **{"is": dict(cur=inc(161377, -2824, -500, -3324), prior=inc(131883, -35638, 217, -35421))},
         cf=dict(cur=cf(-18958, -130733, -4065, -153756, 282383, 128627), prior=cf(-5370, -59069, 95637, 31198, 232803, 264001, restated=True))),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
rolls = []
for key in ("revenue", "pbt", "tax", "net_income"):
    rolls.append(dict(name=f"Q1 2026 + Q2 2026 = H1 2026 {key}", total=["c1bacc8f", "is", "cur", key], parts=[["fdad4f76", "is", "cur", key], ["c1bacc8f", "is_q", "cur", key]]))
    rolls.append(dict(name=f"Q1 2025 + Q2 2025 = H1 2025 {key}", total=["c1bacc8f", "is", "prior", key], parts=[["fdad4f76", "is", "prior", key], ["c1bacc8f", "is_q", "prior", key]]))
t = dict(symbol="8050", name="SALAMA COOPERATIVE INSURANCE COMPANY", currency="SAR", unit="SAR thousands as printed (SAR '000)", docs=docs, roll_checks=rolls)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("ok")
