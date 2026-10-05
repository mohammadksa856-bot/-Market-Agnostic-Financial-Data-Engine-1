"""Transcripts/8060.json: Walaa Cooperative Insurance Company page transcriptions (SAR thousands as printed)."""
from tcommon import bs, cf, inc, write

R23 = "FY2023 operating cash flow as first issued (a57b1123 pdf p17: 422,928; investing -440,574) versus re-presented in the FY2024 filing (041b9f6a pdf p13-14: 423,386; -441,032): 458 amortisation-of-investments line moved from operating to investing; net change and cash unchanged"


def i(rev, pbt, tax, ni, parent, nci, **k):
    return dict(revenue=rev, pbt=pbt, tax=tax, net_income=ni, ni_parent=parent, ni_nci=nci, **k)


docs = [
    dict(sha256_prefix="0ea15501", label="FY2025 audited consolidated FS (label 2026|FY = publication year; inventory annual_report_no_statements but pdf p8-14 carry full statements as images); business combination in 2025 (goodwill)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 6), p9 IS (7), p13-14 CF (11-12); pdf p3-14 textless",
         pages=dict(bs=8, is_=9, cf="13-14"),
         bs=dict(cur=bs(5456783, 3784149, 1672634, 407070, 56455), prior=bs(4765913, 2941895, 1824018, 962268, 50960)),
         **{"is": dict(cur=i(3104295, -155084, -20000, -175084, -175816, 732, eps_basic=-1.38), prior=i(3344580, 83053, -18750, 64303, 64303, 0, eps_basic=0.62))},
         cf=dict(cur=cf(-545897, -1151, -8150, -555198, 962268, 407070), prior=cf(65575, -24798, 409080, 449857, 512411, 962268))),
    dict(sha256_prefix="041b9f6a", label="FY2024 audited FS (label 2025|FY = publication year; inventory annual_report_with_statements, pdf p3-14 textless)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p8 BS, p9 IS, p13-14 CF",
         pages=dict(bs=8, is_=9, cf="13-14"),
         bs=dict(cur=bs(4765913, 2941895, 1824018, 962268, 50960), prior=bs(4107249, 2838794, 1268455, 512411)),
         **{"is": dict(cur=i(3344580, 83053, -18750, 64303, 64303, 0, eps_basic=0.62), prior=i(2887642, 162977, -15000, 147977, 147977, 0, eps_basic=1.45, _declared_diff={"eps_basic": "FY2023 EPS 1.74 as first issued (a57b1123) versus 1.45 labelled Restated in the FY2024 filing (weighted shares 85,058 versus 101,722 thousand)"}))},
         cf=dict(cur=cf(65575, -24798, 409080, 449857, 512411, 962268), prior=cf(423386, -441032, -4153, -21799, 534210, 512411, _declared_diff={"cfo": R23, "cfi": R23}))),
    dict(sha256_prefix="a57b1123", label="FY2023 audited FS as first issued, first IFRS 17 year, 2022 and 2021 restated (label 2024|FY = publication year; pdf p3-18 textless)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p12 BS (printed 10), p13 IS (11), p17-18 CF (15-16)",
         pages=dict(bs=12, is_=13, cf="17-18"),
         bs=dict(cur=bs(4107249, 2838794, 1268455, 512411), prior=bs(3587872, 2471436, 1116436, 534210, restated=True)),
         **{"is": dict(cur=i(2887642, 162977, -15000, 147977, 147977, 0, eps_basic=1.74), prior=i(2572335, -56441, -11639, -68080, -68080, 0, eps_basic=-0.99, restated=True))},
         cf=dict(cur=cf(422928, -440574, -4153, -21799, 534210, 512411), prior=cf(59365, 139479, 10318, 209162, 325048, 534210, restated=True))),
    dict(sha256_prefix="a8eaa7a2", label="3M and 6M ended 2026-06-30 unaudited consolidated interim (inventory partial_statements; label 2026|H1 correct); latest period in the collection; 31 Dec 2025 comparative marked Restated", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3; columns 3M 2026, 3M 2025, 6M 2026, 6M 2025), p9-10 CF (7-8; six-month only); pdf p3-10 textless",
         pages=dict(bs=4, is_=5, cf="9-10"),
         bs=dict(cur=bs(5142443, 3427439, 1715004, 446762, 53887), prior=bs(5456783, 3784149, 1672634, 407070, 56455)),
         **{"is": dict(cur=i(1308958, 53413, -9918, 43495, 43166, 329, eps_basic=0.34), prior=i(1475032, -107127, -10000, -117127, -117304, 177, eps_basic=-0.92)),
            "is_q": dict(cur=i(675781, 32245, -4987, 27258, 26986, 272, eps_basic=0.21), prior=i(686813, -44177, -5000, -49177, -49354, 177, eps_basic=-0.39))},
         cf=dict(cur=cf(-23367, 69370, -6311, 39692, 407070, 446762), prior=cf(-424033, -15606, -5756, -445395, 962268, 516873))),
    dict(sha256_prefix="531e3feb", label="3M ended 2026-03-31 unaudited consolidated interim (inventory partial_statements; label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3), p9-10 CF (7-8); pdf p3, p5-10 textless",
         pages=dict(bs=4, is_=5, cf="9-10"),
         bs=dict(cur=bs(5273050, 3584179, 1688871, 514966, 55012), prior=bs(5456783, 3784149, 1672634, 407070, 56455)),
         **{"is": dict(cur=i(633177, 21168, -4931, 16237, 16180, 57, eps_basic=0.13), prior=i(788219, -62950, -5000, -67950, -67950, 0, eps_basic=-0.53))},
         cf=dict(cur=cf(-2553, 115534, -5085, 107896, 407070, 514966), prior=cf(-357496, -35649, -5160, -398305, 962268, 563963))),
]
H, Q = "a8eaa7a2", "531e3feb"
rolls = []
for k, name in (("revenue", "insurance revenue"), ("pbt", "result before zakat and tax"), ("tax", "zakat and tax"), ("net_income", "net result"), ("ni_parent", "result attributable to owners")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {name}", total=[H, "is", "cur", k], parts=[[Q, "is", "cur", k], [H, "is_q", "cur", k]]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {name}", total=[H, "is", "prior", k], parts=[[Q, "is", "prior", k], [H, "is_q", "prior", k]]))
write("8060", "WALAA COOPERATIVE INSURANCE COMPANY", docs, rolls)
