"""Writes transcripts/8190.json (page transcriptions, SAR thousands as printed) for United Cooperative Assurance (UCA)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "8190.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, cfi, cff, net, b, e, **k):
    return dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)


def inc(rev, pbt, tax, ni, **k):
    return dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni, ni_parent=ni, ni_nci=0, **k)


NET23 = "FY2023 filing nets insurance contracts per portfolio (no insurance contract assets, reinsurance contract assets nil, net liability 285,885); the FY2024 filing re-presents 2023 gross: insurance contract assets 101,129, reinsurance contract assets 66,787, insurance contract liabilities 387,014, reinsurance contract liabilities 94,496 (equity 265,155 unchanged)"
CF23 = "FY2023 filing cash flow shows CFO 28,546 and CFI 12,679; the FY2024 filing re-presents 2023 as CFO 21,071 and CFI 20,154 (term deposits 101,041 now in investing); net change 38,315 and financing -2,910 unchanged"
IFRS17 = "IFRS 4 to IFRS 17 and IFRS 9 transition: FY2022 as issued (this filing) versus restated comparative in the FY2023 filing (cc813d13)"
CASH22 = "cash 83,980 as issued versus 83,964 restated (16 difference at IFRS 9 transition); opening 87,769 versus 87,753"

docs = [
    dict(sha256_prefix="edae80ae", label="FY2025 audited FS, SAR thousands (born digital; label 2026|FY = publication year)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="text layer pdf p9 BS (printed 7), p10 IS (8), p14-15 CF (12-13); going-concern uncertainty read at pdf p16-17",
         pages=dict(bs=9, is_=10, cf="14-15"),
         bs=dict(cur=bs(788744, 764165, 24579, 23743, 7476), prior=bs(920603, 652289, 268314, 73030, 12419)),
         **{"is": dict(cur=inc(858313, -259224, 3004, -256220, eps_basic=-6.41), prior=inc(1049578, -11055, -4000, -15055, eps_basic=-0.38))},
         cf=dict(cur=cf(-183275, 135411, -1423, -49287, 73030, 23743), prior=cf(-10790, -34991, -3468, -49249, 122279, 73030))),
    dict(sha256_prefix="47b9867c", label="FY2024 audited FS, SAR thousands (statement pages image-only; label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p10 BS (printed 8), p11 IS (9), p15-16 CF (13-14); pdf p9-16 textless",
         pages=dict(bs=10, is_=11, cf="15-16"),
         bs=dict(cur=bs(920603, 652289, 268314, 73030, 12419), prior=bs(797762, 532607, 265155, 122279, 7343)),
         **{"is": dict(cur=inc(1049578, -11055, -4000, -15055, eps_basic=-0.38), prior=inc(1061771, 9562, -4270, 5292, eps_basic=0.13))},
         cf=dict(cur=cf(-10790, -34991, -3468, -49249, 122279, 73030), prior=cf(21071, 20154, -2910, 38315, 83964, 122279))),
    dict(sha256_prefix="cc813d13", label="FY2023 audited FS, first IFRS 17 year, with 2022 restated comparatives (text layer; label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="text layer pdf p12 BS (printed 11), p13 IS (12), p16 equity (15), p17-18 CF (16-17); pdf p3-11 textless (auditor report)",
         pages=dict(bs=12, is_=13, cf="17-18"),
         bs=dict(cur=bs(629846, 364691, 265155, 122279, 7343, _extra_keys=["total_liabilities"], _declared_diff={"total_assets": NET23, "total_liabilities": NET23}),
                 prior=bs(747546, 491395, 256151, 83964, 10482, restated=True)),
         **{"is": dict(cur=inc(1061771, 9562, -4270, 5292, eps_basic=0.13), prior=inc(634333, -52482, -3000, -55482, eps_basic=-1.39, restated=True))},
         cf=dict(cur=cf(28546, 12679, -2910, 38315, 83964, 122279, _declared_diff={"cfo": CF23, "cfi": CF23}),
                 prior=cf(7204, -8424, -2569, -3789, 87753, 83964, restated=True))),
    dict(sha256_prefix="f933d77c", label="FY2022 audited FS as issued under IFRS 4, SAR thousands (statement pages image-only; label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p9-10 BS (printed 7-8), p11-12 IS (9-10), p15-16 CF (13-14)", pages=dict(bs="9-10", is_="11-12", cf="15-16"),
         bs=dict(cur=bs(1060892, 855259, 205633, 83980, 10482, _declared_diff={"total_assets": IFRS17, "total_liabilities": IFRS17, "total_equity": IFRS17, "cash": CASH22}),
                 prior=bs(978405, 725356, 253049, 87769, 9122)),
         **{"is": dict(cur=dict(pbt=-39861, tax=-3000, net_income=-42861, ni_parent=-42861, ni_nci=0, gross_premiums_written=821844, total_revenues_ifrs4=310905, eps_basic=-1.07,
                                _declared_diff={"pbt": IFRS17, "net_income": IFRS17, "ni_parent": IFRS17}),
                       prior=dict(pbt=-65671, tax=-8000, net_income=-73671, ni_parent=-73671, ni_nci=0, gross_premiums_written=409756, total_revenues_ifrs4=218875, eps_basic=-1.84))},
         cf=dict(cur=cf(7204, -8424, -2569, -3789, 87769, 83980, _declared_diff={"cash_end": CASH22}),
                 prior=cf(-5928, 35251, -3289, 26034, 61735, 87769))),
    dict(sha256_prefix="fae9bdf6", label="3M and 6M ended 2026-06-30 reviewed interim, SAR thousands (text layer; label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="text layer pdf p5 BS (printed 3), p6 IS (4), p8 equity (6), p9 CF (7, also rendered); income columns three-month 2026, three-month 2025, six-month 2026, six-month 2025",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(833693, 816851, 16842, 80267, 6463), prior=bs(788744, 764165, 24579, 23743, 7476)),
         **{"is": dict(cur=inc(188973, -7237, -500, -7737), prior=inc(430431, -108835, 3974, -104861)),
            "is_q": dict(cur=inc(88288, -372, -500, -872), prior=inc(211278, -81541, 0, -81541))},
         cf=dict(cur=cf(-14389, 11373, 59540, 56524, 23743, 80267), prior=cf(-61480, 26653, -656, -35483, 73030, 37547))),
    dict(sha256_prefix="695faccd", label="3M ended 2026-03-31 reviewed interim, SAR thousands (text layer; label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="text layer pdf p5 BS (printed 4), p6 IS (5), p9 CF (8)", pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(756220, 738506, 17714, 3632, 6794), prior=bs(788744, 764165, 24579, 23743, 7476)),
         **{"is": dict(cur=inc(100685, -6865, 0, -6865), prior=inc(219153, -27294, 3974, -23320))},
         cf=dict(cur=cf(-17342, -2125, -644, -20111, 23743, 3632), prior=cf(-820, 22567, -656, 21091, 73030, 94121))),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
rolls = []
for key in ("revenue", "pbt", "net_income"):
    rolls.append(dict(name=f"Q1 2026 + Q2 2026 = H1 2026 {key}", total=["fae9bdf6", "is", "cur", key], parts=[["695faccd", "is", "cur", key], ["fae9bdf6", "is_q", "cur", key]]))
    rolls.append(dict(name=f"Q1 2025 + Q2 2025 = H1 2025 {key}", total=["fae9bdf6", "is", "prior", key], parts=[["695faccd", "is", "prior", key], ["fae9bdf6", "is_q", "prior", key]]))
t = dict(symbol="8190", name="UNITED COOPERATIVE ASSURANCE COMPANY", currency="SAR", unit="SAR thousands as printed (SR'000)", docs=docs, roll_checks=rolls)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("ok")
