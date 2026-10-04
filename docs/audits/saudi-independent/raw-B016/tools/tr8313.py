"""Page transcript for 8313 Rasan Information Technology (SAR, full riyals as printed). Values read from text-layer pages."""
from trlib import bs, write


def isx(rev, cost, gp, op, pbt, tax, ni, eps=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni)
    if eps is not None:
        d["eps_basic"] = eps
    d.update(k)
    return d


def cf(cfo, cfi, cff, net, begin=None, fx=None, end=None, **k):
    d = dict(cfo=cfo, cfi=cfi, cff=cff, net_change=net)
    if begin is not None:
        d.update(cash_begin=begin, fx=fx, cash_end=end)
    d.update(k)
    return d


def D(sha, label, pe, pr, typ, reading, pages, BS, IS, CF, ISQ=None, bs_prior_end=None, restatements=None):
    d = dict(sha256_prefix=sha, label=label, period_end=pe, prior_end=pr, period_type=typ, reading=reading, pages=pages, bs=BS, cf=CF)
    d["is"] = IS
    if ISQ:
        d["is_q"] = ISQ
    if bs_prior_end:
        d["bs_prior_end"] = bs_prior_end
    if restatements:
        d["restatements"] = restatements
    return d


docs = [
    D("bb6fc163", "FY2025 audited FS (collector label 2026|FY = publication year)", "2025-12-31", "2024-12-31", "FY",
      "text layer: pdf p8 BS (printed 6), p9 IS (7), p11 CF (9)", dict(bs=8, is_=9, cf=11),
      dict(cur=bs(1347885386, 642446486, 705438900, cash=740964123, ppe=15823856), prior=bs(931842991, 516947356, 414895635, cash=451030258, ppe=16047347)),
      dict(cur=isx(653252233, -188345532, 464906701, 251412351, 269088727, -22282314, 246806413, 3.26), prior=isx(358329900, -120187679, 238142221, 98847850, 110389741, -15661944, 94727797, 1.29)),
      dict(cur=cf(333422120, -40884562, -1715144, 290822414, 451030258, -888549, 740964123), prior=cf(165115476, -26428195, 191882311, 330569592, 116490434, 3970232, 451030258))),
    D("2f31a99e", "FY2024 audited FS (label 2025|FY = publication year)", "2024-12-31", "2023-12-31", "FY",
      "text layer: pdf p9 BS (printed 7), p10 IS (8), p12 CF (10)", dict(bs=9, is_=10, cf=12),
      dict(cur=bs(931842991, 516947356, 414895635, cash=451030258), prior=bs(317187685, 196194033, 120993652, cash=116490434)),
      dict(cur=isx(358329900, -120187679, 238142221, 98847850, 110389741, -15661944, 94727797, 1.29), prior=isx(256234155, -107837762, 148396393, 50532155, 51245042, -5292716, 45952326, 0.65)),
      dict(cur=cf(165115476, -26428195, 191882311, 330569592, 116490434, 3970232, 451030258), prior=cf(71761792, -30562798, -2904610, 38294384, 77397342, 798708, 116490434))),
    D("9ca661d8", "FY2023 audited FS (label 2024|FY = publication year; collides with 2 other files in that slot)", "2023-12-31", "2022-12-31", "FY",
      "text layer: pdf p6 BS (printed 4), p7 IS (5), p9 CF (7)", dict(bs=6, is_=7, cf=9),
      dict(cur=bs(317187685, 196194033, 120993652, cash=116490434, ppe=16736036), prior=bs(133674054, 59203213, 74470841, cash=77397342, ppe=8522466)),
      dict(cur=isx(256234155, -107837762, 148396393, 50532155, 51245042, -5292716, 45952326, 0.65), prior=isx(162491088, -60595752, 101895336, 41768547, 37714527, -3305091, 34409436, 0.49)),
      dict(cur=cf(71761792, -30562798, -2904610, 38294384, 77397342, 798708, 116490434), prior=cf(65657977, -21558307, -1747817, 42351853, 35278462, -232973, 77397342))),
    D("4a453924", "FY2022 audited FS, English (label 2024|FY, wrong slot: holds FY2022)", "2022-12-31", "2021-12-31", "FY",
      "text layer: pdf p6 BS (printed 4), p7 IS (5), p9 CF (7)", dict(bs=6, is_=7, cf=9),
      dict(cur=bs(133674054, 59203213, 74470841, cash=77397342, ppe=8522466), prior=bs(86500558, 46206180, 40294378, cash=35278462, ppe=4627610)),
      dict(cur=isx(162491088, -60595752, 101895336, 41768547, 37714527, -3305091, 34409436, 13.494), prior=isx(86898916, -26049073, 60849843, 33044177, 36785824, -1505938, 35279886, 19.437)),
      dict(cur=cf(65657979, -21558307, -1747817, 42351855, 35278462, -232975, 77397342,
                  _declared_diff={"cfo": "FY2023 filing prints the FY2022 comparative cfo as 65,657,977 (2 lower; rounding in the comparative)",
                                  "net_change": "FY2023 filing prints 42,351,853 (2 lower; same rounding)"}),
           prior=cf(25169603, -14348348, 22024707, 32845962, 2413651, 18849, 35278462))),
    D("0ad38a49", "FY2021 audited FS, English (label 2021|FY)", "2021-12-31", "2020-12-31", "FY",
      "text layer: pdf p6 BS (printed 4), p7 IS (5), p9 CF (7)", dict(bs=6, is_=7, cf=9),
      dict(cur=bs(86500558, 46206180, 40294378, cash=35278462, ppe=4627610), prior=bs(24148530, 41651227, -17502697, cash=2413651, ppe=2343260)),
      dict(cur=isx(86898916, -26049073, 60849843, 33044177, 36785824, -1505938, 35279886, 19.437), prior=isx(43368799, -21101650, 22267149, 566922, 881968, -310023, 571945, 571.945)),
      dict(cur=cf(25169603, -14348348, 22024707, 32845962, 2413651, 18849, 35278462), prior=cf(4896885, -5452036, -380550, -935701, 3361436, -12084, 2413651))),
    D("9f58f106", "H1 2026 reviewed interim, English (label 2026|H1); 'is' = six months, 'is_q' = three months; 2025 comparatives restated", "2026-06-30", "2025-06-30", "H1",
      "text layer: pdf p4 BS (printed 2), p5 IS (3), p7 CF (5); note 20 restatements pdf p23-29", dict(bs=4, is_=5, cf=7, note20="23-29"),
      dict(cur=bs(1256772289, 291709430, 965062859, cash=607756425, ppe=17373521), prior=bs(988752885, 270052598, 718700287, cash=756175300, ppe=15823856, restated=True)),
      dict(cur=isx(517475435, -159302326, 358173109, 179828727, 187567549, -13438946, 174128603, 2.27), prior=isx(284935975, -108764075, 176171900, 64908883, 73041464, -8135883, 64905581, 0.86, restated=True)),
      dict(cur=cf(203146989, -348027955, -3607180, -148488146, 756175300, 69271, 607756425), prior=cf(76940584, -11751087, -1192946, 63996551, 473500112, 23778, 537520441, restated=True)),
      ISQ=dict(cur=isx(256469921, -84241628, 172228293, 85801554, 90146297, -4982970, 85163327, 1.11), prior=isx(146316030, -55904539, 90411491, 39730008, 43528535, -4007368, 39521167, 0.52, restated=True)),
      bs_prior_end="2025-12-31",
      restatements=["31 Dec 2025 balance sheet: total assets 1,347,885,386 as issued -> 988,752,885 (derecognition of gross premium receivable and payable, restatement 2: -365,950,570 assets, -372,393,888 liabilities; staged-vesting share-based payment, restatement 1: +6,818,069 assets and equity); total equity 705,438,900 -> 718,700,287; cash 740,964,123 -> 756,175,300 (restricted cash reclassified into cash, restatement 6)",
                    "H1 2025: net income 75,017,564 -> 64,905,581 (restatement 1, -10,111,983); revenue 244,735,828 -> 284,935,975 (restatements 8, 9, 10 reclassify rebates and gross commission, no profit effect); Q2 2025: net income 45,016,311 -> 39,521,167, revenue 124,224,821 -> 146,316,030; H1 2025 cash flow: net change 83,372,866 -> 63,996,551, cfo 102,044,410 -> 76,940,584, opening cash 451,030,258 -> 473,500,112 (restricted cash 22,469,854 reclassified)"]),
    D("9b0ee4a0", "Q1 2026 interim, English (label 2026|Q1); as originally issued", "2026-03-31", "2025-03-31", "Q1",
      "text layer: pdf p4 BS (printed 2), p5 IS (3), p7 CF (5)", dict(bs=4, is_=5, cf=7),
      dict(cur=bs(1864895499, 1043141592, 821753907, cash=756528958), prior=bs(1347885386, 642446486, 705438900, cash=740964123)),
      dict(cur=isx(261005514, -75060698, 185944816, 93346627, 96740705, -8455976, 88284729, 1.16), prior=isx(120511007, -34750598, 85760409, 29795714, 34129768, -4128515, 30001253, 0.39)),
      dict(cur=cf(26916482, -10009695, -3519814, 13386973), prior=cf(84119932, -6806483, -703838, 76609611)),
      bs_prior_end="2025-12-31"),
    D("7a2bc186", "9M 2025 interim, English (label 2025|9M); 'is' = nine months, 'is_q' = three months; as originally issued", "2025-09-30", "2024-09-30", "9M",
      "text layer: pdf p4 BS (printed 2), p5 IS (3), p7 CF (5)", dict(bs=4, is_=5, cf=7),
      dict(cur=bs(1299192041, 698046348, 601145693, cash=574481117), prior=bs(931842991, 516947356, 414895635, cash=451030258)),
      dict(cur=isx(439553374, -127884030, 311669344, 158131138, 171015152, -13675978, 157339174, 2.04), prior=isx(240458626, -95612678, 144845948, 56994313, 64208159, -9269079, 54939080, 0.75)),
      dict(cur=cf(151522511, -25131087, -2087794, 124303630, 451030258, -852771, 574481117), prior=cf(94774859, -19099478, 188830855, 264506236, 116490434, 3615204, 384611874)),
      ISQ=dict(cur=isx(194817546, -59320102, 135497444, 83110272, 87861705, -5540095, 82321610, 1.06), prior=isx(109999634, -42629573, 67370061, 35298738, 40016520, -3369702, 36646818, 0.48)),
      bs_prior_end="2024-12-31"),
    D("0ae692ef", "H1 2025 interim, English (label 2025|H1); 'is' = six months, 'is_q' = three months; as originally issued", "2025-06-30", "2024-06-30", "H1",
      "text layer: pdf p4 BS (printed 2), p5 IS (3), p7 CF (5)", dict(bs=4, is_=5, cf=7),
      dict(cur=bs(986550913, 479235311, 507315602, cash=534426902), prior=bs(931842991, 516947356, 414895635, cash=451030258)),
      dict(cur=isx(244735828, -68563928, 176171900, 75020866, 83153447, -8135883, 75017564), prior=isx(130458992, -52983105, 77475887, 21695575, 24191639, -5899377, 18292262)),
      dict(cur=cf(102044410, -17478598, -1192946, 83372866, 451030258, 23778, 534426902), prior=cf(74479008, -13034357, 189095817, 250540468, 116490434, 3986865, 371017767)),
      ISQ=dict(cur=isx(124224821, -33813330, 90411491, 45225152, 49023679, -4007368, 45016311), prior=isx(63525256, -26091600, 37433656, 11758359, 13055841, -4236795, 8819046)),
      bs_prior_end="2024-12-31"),
]
for d in docs:
    d["pages"] = {("is" if k == "is_" else k): v for k, v in d["pages"].items()}

rolls = [
    dict(name="2025 H1 net income = Q1 2025 (Q1 2026 filing prior column) + Q2 2025", total=["0ae692ef", "is", "cur", "net_income"], parts=[["9b0ee4a0", "is", "prior", "net_income"], ["0ae692ef", "is_q", "cur", "net_income"]]),
    dict(name="2025 H1 revenue = Q1 2025 + Q2 2025", total=["0ae692ef", "is", "cur", "revenue"], parts=[["9b0ee4a0", "is", "prior", "revenue"], ["0ae692ef", "is_q", "cur", "revenue"]]),
    dict(name="2025 9M net income = H1 + Q3", total=["7a2bc186", "is", "cur", "net_income"], parts=[["0ae692ef", "is", "cur", "net_income"], ["7a2bc186", "is_q", "cur", "net_income"]]),
    dict(name="2025 9M revenue = H1 + Q3", total=["7a2bc186", "is", "cur", "revenue"], parts=[["0ae692ef", "is", "cur", "revenue"], ["7a2bc186", "is_q", "cur", "revenue"]]),
    dict(name="2024 9M net income = H1 2024 + Q3 2024", total=["7a2bc186", "is", "prior", "net_income"], parts=[["0ae692ef", "is", "prior", "net_income"], ["7a2bc186", "is_q", "prior", "net_income"]]),
    dict(name="2026 H1 revenue = Q1 2026 + Q2 2026", total=["9f58f106", "is", "cur", "revenue"], parts=[["9b0ee4a0", "is", "cur", "revenue"], ["9f58f106", "is_q", "cur", "revenue"]]),
    dict(name="2026 H1 cost of revenue = Q1 + Q2", total=["9f58f106", "is", "cur", "cost_of_revenue"], parts=[["9b0ee4a0", "is", "cur", "cost_of_revenue"], ["9f58f106", "is_q", "cur", "cost_of_revenue"]]),
    dict(name="2026 H1 net income vs Q1 2026 (as issued) + Q2 2026: DOES NOT CLOSE", total=["9f58f106", "is", "cur", "net_income"], parts=[["9b0ee4a0", "is", "cur", "net_income"], ["9f58f106", "is_q", "cur", "net_income"]],
         declared_break=680547,
         reason="H1 2026 six-month net income 174,128,603 exceeds Q1 2026 as issued (88,284,729) plus Q2 2026 (85,163,327) by 680,547; about the same amount (680,546) sits in operating expenses (Q1 G&A as issued 44,394,649 against 43,714,103 implied by H1 G&A 89,504,345 plus impairment 2,376,856 less Q2 G&A 47,679,409 and impairment 487,689). Note 20 lists restatements of 2025 comparatives and the 31 March 2026 time-deposit classification but no restatement of Q1 2026 profit; unexplained, Q1 2026 is not substituted."),
]
write("8313", "RASAN INFORMATION TECHNOLOGY COMPANY", "SAR", "SAR full riyals as printed", docs, rolls)
