"""Writes transcripts/8270.json (page transcriptions, full SAR) for Buruj Cooperative Insurance Company."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "8270.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, cfi, cff, net, b, e, **k):
    return dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)


def inc(rev, pbt, tax, ni, **k):
    return dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni, ni_parent=ni, ni_nci=0, **k)


R22 = "IFRS 4 to IFRS 17 transition: FY2022 as issued (this filing, 5da7b83a) versus restated comparative in the FY2023 filing (bc6d203e)"

fy24_bs_cur = bs(769087328, 294714826, 474372502, 173678154, 6427722)
docs = [
    dict(sha256_prefix="e0d99bd9", label="FY2024 audited FS, full SAR (image-only statement pages; label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 3), p9 IS (4), p12 CF (7); pdf p3-12 textless",
         pages=dict(bs=8, is_=9, cf=12),
         bs=dict(cur=fy24_bs_cur, prior=bs(847638170, 402801715, 444836455, 98964335, 4167861)),
         **{"is": dict(cur=inc(372730192, 19191600, -9806035, 9385565, eps_basic=0.31), prior=inc(373444279, 25580143, -5496703, 20083440, eps_basic=0.67))},
         cf=dict(cur=cf(-80113398, 156092217, -1265000, 74713819, 98964335, 173678154), prior=cf(-7999045, -147906199, -1100000, -157005244, 255969579, 98964335))),
    dict(sha256_prefix="bc6d203e", label="FY2023 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (image-only statement pages; label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p12 BS (printed 3), p13 IS (4), p16 CF (7); pdf p3-16 textless",
         pages=dict(bs=12, is_=13, cf=16),
         bs=dict(cur=bs(847638170, 402801715, 444836455, 98964335, 4167861), prior=bs(752056846, 331572575, 420484271, 255969579, 3539910, restated=True)),
         **{"is": dict(cur=inc(373444279, 25580143, -5496703, 20083440, eps_basic=0.67), prior=inc(417102909, -23875905, -5124422, -29000327, eps_basic=-0.97, restated=True))},
         cf=dict(cur=cf(-7999045, -147906199, -1100000, -157005244, 255969579, 98964335), prior=cf(-150647857, 170331457, -996258, 18687342, 237282237, 255969579, restated=True))),
    dict(sha256_prefix="5da7b83a", label="FY2022 audited FS as issued under IFRS 4 (image-only statement pages; label 2023|FY = publication year)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 6), p8 IS (7), p11 CF (10); pdf p3-11 textless. total_liabilities = liabilities 399,816,088 plus insurance-operations reserve items (3,752,134 FV reserve deficit, 2,971,159 actuarial) = 399,035,113 as printed 'total liabilities and insurance operations surplus'",
         pages=dict(bs=7, is_=8, cf=11),
         bs=dict(cur=bs(793814537, 399035113, 394779424, 254910052, 3539910, _declared_diff={"total_assets": R22, "total_liabilities": R22, "total_equity": R22, "cash": R22}),
                 prior=bs(889952300, 447531086, 442421214, 237886895, 4129551)),
         **{"is": dict(cur=dict(pbt=-32642832, tax=-6650274, net_income=-39293106, ni_parent=-39293106, ni_nci=0, gross_written_premiums=368839351, total_revenues_ifrs4=398215100, eps_basic=-1.31,
                                _declared_diff={"pbt": R22, "net_income": R22, "ni_parent": R22}),
                       prior=dict(pbt=15770140, tax=-11456333, net_income=4313807, ni_parent=4313807, ni_nci=0, gross_written_premiums=290711903, total_revenues_ifrs4=171973021, eps_basic=0.14))},
         cf=dict(cur=cf(-129942452, 147961867, -996258, 17023157, 237886895, 254910052, _declared_diff={"cfo": R22, "cfi": R22, "net_change": R22, "cash_end": R22}),
                 prior=cf(46459719, 58925788, 609455, 105994962, 131891933, 237886895))),
    dict(sha256_prefix="c04bbe5e", label="3M and 6M ended 2025-06-30 reviewed interim (image-only statement pages; label 2025|H1 correct); latest period in the collection", period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 3), p5 IS (4), p8 CF (7); income columns three-month 2025, three-month 2024, six-month 2025, six-month 2024",
         pages=dict(bs=4, is_=5, cf=8),
         bs=dict(cur=bs(890931975, 411212018, 479719957, 291405199, 6088189), prior=fy24_bs_cur),
         **{"is": dict(cur=inc(215080562, 4838232, -2000000, 2838232), prior=inc(194289573, 10963221, -3800000, 7163221)),
            "is_q": dict(cur=inc(114139699, 3104951, -1565118, 1539833), prior=inc(88515428, 5640640, -2300000, 3340640))},
         cf=dict(cur=cf(99988889, 18370656, -632500, 117727045, 173678154, 291405199), prior=cf(-47256677, 150350071, -632500, 102460894, 98964335, 201425229))),
    dict(sha256_prefix="31885374", label="3M ended 2025-03-31 reviewed interim (image-only statement pages; label 2025|Q1 correct)", period_end="2025-03-31", prior_end="2024-03-31", bs_prior_end="2024-12-31", period_type="Q1",
         reading="visual: pdf p4 BS (printed 3), p5 IS (4), p7 equity (6); cash flow (pdf p8) not read",
         pages=dict(bs=4, is_=5),
         bs=dict(cur=bs(824132392, 345952268, 478180124, 229047183, 6414393), prior=fy24_bs_cur),
         **{"is": dict(cur=inc(100940863, 1733281, -434882, 1298399), prior=inc(105774145, 5322581, -1500000, 3822581))}),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
rolls = []
for key in ("revenue", "pbt", "net_income"):
    rolls.append(dict(name=f"Q1 2025 + Q2 2025 = H1 2025 {key}", total=["c04bbe5e", "is", "cur", key], parts=[["31885374", "is", "cur", key], ["c04bbe5e", "is_q", "cur", key]]))
    rolls.append(dict(name=f"Q1 2024 + Q2 2024 = H1 2024 {key}", total=["c04bbe5e", "is", "prior", key], parts=[["31885374", "is", "prior", key], ["c04bbe5e", "is_q", "prior", key]]))
t = dict(symbol="8270", name="BURUJ COOPERATIVE INSURANCE COMPANY", currency="SAR", unit="full SAR (no scaling) in every filing read", docs=docs, roll_checks=rolls)
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("ok")
