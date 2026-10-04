"""Builds transcripts/4007.json from page-read values (full SAR). Values were read from rendered or text-layer pages; see each doc's reading note."""
import json
import pathlib


def I(rev, cost, gp, op, pbt, tax, ni, eps, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax,
             net_income=ni, ni_parent=ni, ni_nci=0, eps=eps)
    d.update(k)
    return d


def B(ta, tl, te, cash, ppe=None, **k):
    d = dict(total_assets=ta, total_liabilities=tl, total_equity=te, cash=cash)
    if ppe is not None:
        d["ppe"] = ppe
    d.update(k)
    return d


def C(cfo, capex, cfi, cff, net, begin, end, **k):
    d = dict(cfo=cfo, capex=capex, cfi=cfi, cff=cff, net_change=net, cash_begin=begin, cash_end=end)
    d.update(k)
    return d


def doc(prefix, label, pe, pr, ptype, reading, pages, bs, is_, cf, bs_prior_end=None, is_q=None):
    d = dict(sha256_prefix=prefix, label=label, period_end=pe, prior_end=pr, period_type=ptype, reading=reading,
             pages=pages, bs=bs, cf=cf)
    d["is"] = is_
    if is_q:
        d["is_q"] = is_q
    if bs_prior_end:
        d["bs_prior_end"] = bs_prior_end
    return d


D24 = B(2650766197, 689512417, 1961253780, 245261942, 1709582028)
D25 = B(2735020822, 729856688, 2005164134, 127891184, 1715728192)
docs = [
    doc("b97990d3", "FY2025 audited (collector label 2026|FY)", "2025-12-31", "2024-12-31", "FY",
        "visual: IS/BS/CF pages are image-only inside a text PDF (textless pdf p3-14); pdf p9 IS (printed 8), p11 BS (10), p13-14 CF (12-13) rendered and read",
        {"bs": 11, "is": 9, "cf": 13},
        dict(cur=D25, prior=D24),
        dict(cur=I(1234531248, -871504822, 363026426, 254141219, 258335915, -16476071, 241859844, 1.51),
             prior=I(1153880931, -771426534, 382454397, 365634922, 354679786, -15878972, 338800814, 2.12)),
        dict(cur=C(213920041, -94585851, -94253278, -237037521, -117370758, 245261942, 127891184),
             prior=C(464072322, -209968983, -83012107, -261035714, 120024501, 125237441, 245261942))),
    doc("507b9a1e", "FY2024 audited as filed (collector label 2025|FY)", "2024-12-31", "2023-12-31", "FY",
        "text layer (pdf p9, p11, p13-14 born digital; p3-8 image-only); columns checked against the FY2025 comparatives",
        {"bs": 11, "is": 9, "cf": 13},
        dict(cur=D24, prior=B(2594447887, 749524050, 1844923837, 125237441, 1658600189)),
        dict(cur=I(1153880931, -771426534, 382454397, 365634922, 354679786, -15878972, 338800814, 2.12),
             prior=I(1176763617, -743619194, 433144423, 342574855, 320955285, -17624413, 303330872, 1.90)),
        dict(cur=C(464072322, -209968983, -83012107, -261035714, 120024501, 125237441, 245261942),
             prior=C(350953998, -53457129, -54782129, -231536913, 64634956, 60602485, 125237441))),
    doc("964e652f", "FY2023 audited as filed (collector label 2024|FY)", "2023-12-31", "2022-12-31", "FY",
        "visual: statement pages image-only (textless pdf p3-14); pdf p9 IS (printed 8), p11 BS (10), p13 CF (12) rendered and read; 2022 comparative cost of revenue, gross profit, selling and G&A differ from the FY2022 filing (re-presented)",
        {"bs": 11, "is": 9, "cf": 13},
        dict(cur=B(2594447887, 749524050, 1844923837, 125237441, 1658600189),
             prior=B(2481848065, 771285376, 1710562689, 60602485, 1606179197)),
        dict(cur=I(1176763617, -743619194, 433144423, 342574855, 320955285, -17624413, 303330872, 1.90),
             prior=I(1122397025, -702725852, 419671173, 291784961, 274150965, -16814797, 257336168, 1.61, restated=True)),
        dict(cur=C(350953998, -53457129, -54782129, -231536913, 64634956, 60602485, 125237441),
             prior=C(253309934, -16723020, -112609756, -200955202, -60255024, 120857509, 60602485))),
    doc("eb3719c7", "FY2022 audited as filed (collector label 2023|FY)", "2022-12-31", "2021-12-31", "FY",
        "visual: statement pages image-only (textless pdf p3-14); pdf p9 IS (printed 8), p11 BS (10), p13 CF (12) rendered and read",
        {"bs": 11, "is": 9, "cf": 13},
        dict(cur=B(2481848065, 771285376, 1710562689, 60602485, 1606179197),
             prior=B(2261714148, 602424911, 1659289237, 120857509, 1546936349)),
        dict(cur=I(1122397025, -706378359, 416018666, 291784961, 274150965, -16814797, 257336168, 1.61),
             prior=I(951887495, -587840128, 364047367, 131229212, 117560461, -18692335, 90087837, 0.56, discontinued=-8780289)),
        dict(cur=C(253309934, -16723020, -112609756, -200955202, -60255024, 120857509, 60602485),
             prior=C(434636025, -14601454, -133010438, -194418033, 107207554, 13649955, 120857509))),
    doc("030791ca", "Q1 2025 reviewed", "2025-03-31", "2024-03-31", "Q1",
        "visual for the income statement (the text layer omits the shaded current-period column on several lines: revenue 277,040,344 in the text layer is the 2024 column, the page shows 301,880,733 for 2025); BS and CF text layer tied by arithmetic",
        {"bs": 6, "is": 4, "cf": 8},
        dict(cur=B(2667467398, 686971170, 1980496228, 290920788), prior=D24),
        dict(cur=I(301880733, -205374358, 96506375, 76725796, 77926321, -4000000, 73926321, 0.46),
             prior=I(277040344, -185983367, 91056977, 74897319, 69041465, -5000000, 64041465, 0.40)),
        dict(cur=C(105220067, -3912042, -2815767, -56745454, 45658846, 245261942, 290920788),
             prior=C(142879380, -5898340, -5990490, -56110079, 80778811, 125237441, 206016252)),
        bs_prior_end="2024-12-31"),
    doc("9b85d9ca", "H1 2025 reviewed (3M and 6M)", "2025-06-30", "2024-06-30", "H1",
        "text layer (pdf p4 IS, p6 BS, p8-9 CF); totals tie by arithmetic; 'is' = six months, 'is_q' = Q2",
        {"bs": 6, "is": 4, "cf": 8},
        dict(cur=B(2646088752, 658647862, 1987440890, 193603968), prior=D24),
        dict(cur=I(600120163, -410620768, 189499395, 140616612, 143889889, -8000000, 135889889, 0.85),
             prior=I(540498525, -363701934, 176796591, 205063512, 192912821, -11000000, 181912821, 1.14)),
        dict(cur=C(110846597, -25699338, -23923062, -138581509, -51657974, 245261942, 193603968),
             prior=C(248828310, -10034230, 113463925, -137494771, 224797464, 125237441, 350034905)),
        bs_prior_end="2024-12-31",
        is_q=dict(cur=I(298239430, -205246410, 92993020, 63890816, 65963568, -4000000, 61963568, 0.39),
                  prior=I(263458181, -177718567, 85739614, 130166193, 123871356, -6000000, 117871356, 0.74))),
    doc("f79e7223", "9M 2025 reviewed (3M and 9M)", "2025-09-30", "2024-09-30", "9M",
        "text layer (pdf p4 IS, p6 BS, p8-9 CF); 'is' = nine months, 'is_q' = Q3",
        {"bs": 6, "is": 4, "cf": 8},
        dict(cur=B(2679907487, 695587331, 1984320156, 124084314), prior=D24),
        dict(cur=I(895029201, -622503132, 272526069, 194944686, 199782968, -12000000, 187782968, 1.17),
             prior=I(831091328, -558243275, 272848053, 286988405, 277038469, -16000000, 261038469, 1.63)),
        dict(cur=C(137860720, -64367765, -61435192, -197603156, -121177628, 245261942, 124084314),
             prior=C(391934870, -16106275, 108593084, -196504860, 304023094, 125237441, 429260535)),
        bs_prior_end="2024-12-31",
        is_q=dict(cur=I(294909038, -211882364, 83026674, 54328074, 55893079, -4000000, 51893079, 0.32),
                  prior=I(290592803, -194541341, 96051462, 81924893, 84125648, -5000000, 79125648, 0.49))),
    doc("cbbdf048", "Q1 2026 reviewed", "2026-03-31", "2025-03-31", "Q1",
        "visual: pdf p3-9 image-only; pdf p4 IS (printed 3), p6 BS (5), p8-9 CF (7-8) rendered and read",
        {"bs": 6, "is": 4, "cf": 8},
        dict(cur=B(2909326558, 883402661, 2025923897, 19198864), prior=D25),
        dict(cur=I(319093684, -218002552, 101091132, 52545199, 60238960, -4000000, 56238960, 0.35),
             prior=I(301880733, -205374358, 96506375, 76725796, 77926321, -4000000, 73926321, 0.46)),
        dict(cur=C(-45398490, -32691690, -52691690, -10602140, -108692320, 127891184, 19198864),
             prior=C(105220067, -3912042, -2815767, -56745454, 45658846, 245261942, 290920788)),
        bs_prior_end="2025-12-31"),
    doc("9121564d", "H1 2026 reviewed (3M and 6M)", "2026-06-30", "2025-06-30", "H1",
        "text layer (pdf p4 IS, p5 OCI, p6 BS, p8-9 CF; only pdf p3 textless); 'is' = six months, 'is_q' = Q2",
        {"bs": 6, "is": 4, "cf": 8},
        dict(cur=B(2886260665, 819644515, 2066616150, 39951367, 1680181528), prior=D25),
        dict(cur=I(640839143, -459813108, 181026035, 122087608, 136126265, -8000000, 128126265, 0.80),
             prior=I(600120163, -410620768, 189499395, 140616612, 143889889, -8000000, 135889889, 0.85)),
        dict(cur=C(98190222, -75034474, -94290465, -91839574, -87939817, 127891184, 39951367),
             prior=C(110846597, -25699338, -23923062, -138581509, -51657974, 245261942, 193603968)),
        bs_prior_end="2025-12-31",
        is_q=dict(cur=I(321745459, -241810556, 79934903, 69542409, 75887305, -4000000, 71887305, 0.45),
                  prior=I(298239430, -205246410, 92993020, 63890816, 65963568, -4000000, 61963568, 0.39))),
]


def ref(p, block, col, key):
    return [p, block, col, key]


rolls = []
for key in ("revenue", "gross_profit", "net_income"):
    rolls.append(dict(name=f"Q1+Q2=H1 2025 {key}", total=ref("9b85d9ca", "is", "cur", key),
                      parts=[ref("030791ca", "is", "cur", key), ref("9b85d9ca", "is_q", "cur", key)]))
    rolls.append(dict(name=f"H1+Q3=9M 2025 {key}", total=ref("f79e7223", "is", "cur", key),
                      parts=[ref("9b85d9ca", "is", "cur", key), ref("f79e7223", "is_q", "cur", key)]))
    rolls.append(dict(name=f"Q1+Q2=H1 2026 {key}", total=ref("9121564d", "is", "cur", key),
                      parts=[ref("cbbdf048", "is", "cur", key), ref("9121564d", "is_q", "cur", key)]))
out = dict(symbol="4007", name="ALHAMMADI (Al Hammadi Holding Company)", currency="SAR",
           unit="full SAR (riyals) in annual and interim filings alike; no NCI line (net income = parent)",
           docs=docs, roll_checks=rolls)
pathlib.Path(__file__).resolve().parent.parent.joinpath("transcripts", "4007.json").write_text(
    json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
print("written", len(docs))
