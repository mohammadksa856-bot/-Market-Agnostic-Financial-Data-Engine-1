"""Writes transcripts/8130.json (page transcriptions, SAR thousands as printed) for Alahli Takaful (symbol 8130 ATC)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "transcripts" / "8130.json"


def bs(ta, tl, te, cash, ppe, **k):
    return dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash, ppe=ppe, **k)


def cf(cfo, cfi, cff, net, b, e, **k):
    return dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net, cash_begin=b, cash_end=e, **k)


def inc(rev, pbt, tax, ni, **k):
    return dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni, ni_parent=ni, ni_nci=0, **k)


PRES = "re-presentation in the FY2020 filing: reinsurers' share of IBNR 17,838 shown gross as an asset and gross IBNR 22,891 as a liability (FY2019 filing netted: IBNR 5,053)"
REVP = "FY2020 filing presents total revenues with investible contributions in revenue (202,165); FY2019 filing nets them (52,538); net underwriting income 32,338 is identical"
Z18 = "FY2018 as issued showed net income attributable to shareholders 10,421 with no zakat/tax line (EPS 0.63); the FY2019 filing restates 2018 after zakat 5,669 and income tax recovery 706 to 5,458 (EPS 0.33)"
C18 = "FY2018 as issued: CFO -36,500 (zakat paid -4,895), CFF -10,466 (dividends -12,499, tax recovered 663 and 1,370); FY2019 filing restates 2018: CFO -35,130 (zakat net -3,525), CFF -11,836; net change -7,800 unchanged"

docs = [
    dict(sha256_prefix="41855727", label="FY2020 audited FS, SAR thousands (scan, textless; collector label 2021|FY = publication year)", period_end="2020-12-31", prior_end="2019-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 6), p9-10 IS (7-8), p14-15 CF (12-13)", pages=dict(bs=8, is_="9-10", cf="14-15"),
         bs=dict(cur=bs(1088807, 838861, 249946, 33713, 3487), prior=bs(1092355, 850592, 241763, 19619, 2703)),
         **{"is": dict(cur=inc(191091, 14056, -6037, 8019, eps_basic=0.48, net_underwriting_income=38418),
                       prior=inc(202165, 13746, -6408, 7338, eps_basic=0.44, net_underwriting_income=32338))},
         cf=dict(cur=cf(-18848, 32942, 0, 14094, 19619, 33713), prior=cf(20093, -19345, 0, 748, 18871, 19619))),
    dict(sha256_prefix="c95c3409", label="FY2019 audited FS, SAR thousands (scan, textless; collector label 2020|FY = publication year)", period_end="2019-12-31", prior_end="2018-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 7), p9-10 IS (8-9), p14-15 CF (13-14)", pages=dict(bs=8, is_="9-10", cf="14-15"),
         bs=dict(cur=bs(1074517, 832754, 241763, 19619, 2703, _extra_keys=["total_liabilities"],
                        _declared_diff={"total_assets": PRES, "total_liabilities": PRES}),
                 prior=bs(1098621, 863884, 234737, 18871, 1712)),
         **{"is": dict(cur=inc(52538, 13746, -6408, 7338, eps_basic=0.44, net_underwriting_income=32338, _declared_diff={"revenue": REVP}),
                       prior=inc(76300, 10421, -4963, 5458, eps_basic=0.33, net_underwriting_income=39938,
                                 _declared_diff={"net_income": Z18, "ni_parent": Z18}))},
         cf=dict(cur=cf(20093, -19345, 0, 748, 18871, 19619),
                 prior=cf(-35130, 39166, -11836, -7800, 26671, 18871, _declared_diff={"cfo": C18, "cff": C18}))),
    dict(sha256_prefix="16466467", label="FY2018 audited FS as issued, SAR thousands (scan, textless; collector label 2019|FY = publication year)", period_end="2018-12-31", prior_end="2017-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 6), p8 IS (7), p12-13 CF (11-12)", pages=dict(bs=7, is_=8, cf="12-13"),
         bs=dict(cur=bs(1098621, 863884, 234737, 18871, 1712), prior=bs(1109509, 868417, 241092, 26671, 2000)),
         **{"is": dict(cur=dict(revenue=76300, net_income=10421, ni_parent=10421, ni_nci=0, eps_basic=0.63, net_underwriting_income=39938,
                                _declared_diff={"net_income": Z18, "ni_parent": Z18}))},
         cf=dict(cur=cf(-36500, 39166, -10466, -7800, 26671, 18871, _declared_diff={"cfo": C18, "cff": C18}),
                 prior=cf(26512, -11348, -7526, 7638, 19033, 26671))),
    dict(sha256_prefix="ae851486", label="3M and 9M ended 2021-09-30 reviewed interim, SAR thousands (scan; label 2021|9M correct) - latest period in the collection", period_end="2021-09-30", prior_end="2020-09-30", bs_prior_end="2020-12-31", period_type="9M",
         reading="visual: pdf p4 BS (printed 2), p5-6 IS (3-4), p10-11 CF (8-9); income columns three-month 2021, three-month 2020, nine-month 2021, nine-month 2020",
         pages=dict(bs=4, is_="5-6", cf="10-11"),
         bs=dict(cur=bs(1126660, 877695, 248965, 48507, 3559), prior=bs(1088807, 838861, 249946, 33713, 3487)),
         **{"is": dict(cur=inc(153368, 3881, -4739, -858), prior=inc(149655, 6962, -4471, 2491)),
            "is_q": dict(cur=inc(51096, -3212, -1488, -4700), prior=inc(50368, 202, -1281, -1079))},
         cf=dict(cur=cf(790, 14004, 0, 14794, 33713, 48507), prior=cf(-12682, 14687, 0, 2005, 19619, 21624))),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}
t = dict(symbol="8130", name="ALAHLI TAKAFUL COMPANY (ATC)", currency="SAR", unit="SAR thousands as printed (SR'000)", docs=docs, roll_checks=[])
OUT.write_text(json.dumps(t, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("ok")
