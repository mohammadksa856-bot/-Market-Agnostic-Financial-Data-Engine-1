"""Transcripts/1323.json: United Carton Industries Company (UCIC) page transcriptions. Amounts are full Saudi riyals as printed (not thousands)."""
from tcommon import bs, cf, inc, write


def isx(rev, cost, gp, op, pbt, zk, tx, ni, eps, **k):
    # tax = zakat + income tax (both printed as separate lines; combined here so pbt + tax = net profit)
    return dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=zk + tx, zakat=zk, income_tax=tx,
                net_income=ni, ni_parent=ni, ni_nci=0, eps_basic=eps, **k)


R22 = ("FY2022 as issued (3ad94137) versus FY2022 restated in the FY2023 filing (eb5b3333, Note 31, pdf p50-53): measurement-period adjustments on the "
       "acquisition, correction of prior period errors and a change in accounting policy; cost of sales, selling expenses, bargain purchase gain, finance costs and other income re-presented")
CFR22 = "operating cash flow 13,508,394 as issued versus 13,630,946 restated and financing 37,900,623 versus 37,778,071 (same Note 31 restatement); investing and net change identical"

docs = [
    dict(sha256_prefix="f667bd74", label="3M and 6M ended 2026-06-30 interim (label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="text layer: pdf p4 BS (printed 3), p5 IS (4; 3M and 6M), p7 CF (6, six months)", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1064738839, 439195902, 625542937, 53507804, 403275932), prior=bs(1077838734, 489523673, 588315061, 85159556, 397852759)),
         **{"is": dict(cur=isx(737579853, -614788613, 122791240, 59492015, 58161619, -2645778, -2578486, 52937355, 1.32),
                       prior=isx(684824364, -592088699, 92735665, 33580141, 32743681, -1976441, -4067964, 26699276, 0.67)),
            "is_q": dict(cur=isx(384090465, -318948864, 65141601, 32302999, 31587064, -1634020, -1168454, 28784590, 0.72),
                         prior=isx(334994542, -293613623, 41380919, 11044955, 11715341, -1062450, -2606838, 8046053, 0.20))},
         cf=dict(cur=cf(49214750, -32660030, -48206472, -31651752, 85159556, 53507804), prior=cf(90536023, -27123467, -49948411, 13464145, 38005164, 51469309))),
    dict(sha256_prefix="426d2249", label="3M ended 2026-03-31 interim (label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="text layer: pdf p4 BS (printed 3), p5 IS (4), p7 CF (6)", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1044783838, 432316012, 612467826, 51952972, 399495880), prior=bs(1077838734, 489523673, 588315061, 85159556, 397852759)),
         **{"is": dict(cur=isx(353489388, -295839749, 57649639, 27189016, 26574555, -1011758, -1410032, 24152765, 0.60),
                       prior=isx(349829822, -298475076, 51354746, 22535186, 21028340, -913991, -1461126, 18653223, 0.47))},
         cf=dict(cur=cf(7230787, -13115548, -27321823, -33206584, 85159556, 51952972), prior=cf(41554927, -6999904, -12552722, 22002301, 38005164, 60007465))),
    dict(sha256_prefix="4aa36e27", label="FY2025 audited consolidated FS (label 2026|FY = publication year; inventory class other_no_statements_found although full statements are present)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual: pdf p7 BS (printed 6), p8 IS (7), p10 CF (9); pdf p7-10 have no text layer", pages=dict(bs=7, is_=8, cf=10),
         bs=dict(cur=bs(1077838734, 489523673, 588315061, 85159556, 397852759), prior=bs(997679841, 452155382, 545524459, 38005164, 393497885)),
         **{"is": dict(cur=isx(1406376399, -1208666311, 197710088, 88955585, 86668833, -3208097, -4336071, 79124665, 1.98),
                       prior=isx(1344476419, -1104413687, 240062732, 145869754, 139910066, -3330081, -11883774, 124696211, 3.12))},
         cf=dict(cur=cf(168994333, -58057158, -63782783, 47154392, 38005164, 85159556), prior=cf(166140732, -104882059, -53842763, 7415910, 30586197, 38005164, fx=3057))),
    dict(sha256_prefix="b2faa977", label="3M and 9M ended 2025-09-30 interim (label 2025|9M correct)", period_end="2025-09-30", prior_end="2024-09-30", bs_prior_end="2024-12-31", period_type="9M",
         reading="visual: pdf p4 BS (printed 3), p5 IS (4; 3M and 9M), p7-8 CF (6-7, nine months); pdf p4-8 have no text layer", pages=dict(bs=4, is_=5, cf="7-8"),
         bs=dict(cur=bs(1026040300, 425846044, 600194256, 42217320, 384789760), prior=bs(997679841, 452155382, 545524459, 38005164, 393497885)),
         **{"is": dict(cur=isx(1056290497, -908762818, 147527679, 57406312, 56048084, -3115043, -5633372, 47299669, 1.18),
                       prior=isx(1021740471, -826752945, 194987526, 116025951, 112041997, -4073189, -8479210, 99489598, 2.49, restated=True)),
            "is_q": dict(cur=isx(371466133, -316674119, 54792014, 23826171, 23304403, -1138602, -1565408, 20600393, 0.52),
                         prior=isx(351059445, -289899569, 61159876, 41946336, 39795484, -1988971, -1050560, 36755953, 0.92, restated=True))},
         cf=dict(cur=cf(89165927, -33385644, -51568127, 4212156, 38005164, 42217320), prior=cf(92137412, -94869118, -11460449, -14192155, 30586197, 16389545, fx=-4497, restated=True))),
    dict(sha256_prefix="a1b78367", label="3M and 6M ended 2025-06-30 interim (label 2025|H1 correct)", period_end="2025-06-30", prior_end="2024-06-30", bs_prior_end="2024-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 3), p5 IS (4; 3M and 6M), p7 CF (6, six months); pdf p4-7 have no text layer", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1022353528, 442759665, 579593863, 51469309, 390151581), prior=bs(997679841, 452155382, 545524459, 38005164, 393497885)),
         **{"is": dict(cur=isx(684824364, -592088699, 92735665, 33580141, 32743681, -1976441, -4067964, 26699276, 0.67),
                       prior=isx(670681026, -536853376, 133827650, 74079615, 72246513, -2084218, -7428650, 62733645, 1.57)),
            "is_q": dict(cur=isx(334994542, -293613623, 41380919, 11044955, 11715341, -1062450, -2606838, 8046053, 0.20),
                         prior=isx(315168385, -254914784, 60253601, 31744359, 31106695, -368331, -2650460, 28087904, 0.70))},
         cf=dict(cur=cf(90536023, -27123467, -49948411, 13464145, 38005164, 51469309), prior=cf(81049507, -48044668, -34055477, -1050638, 30586197, 29527005, fx=-8554))),
    dict(sha256_prefix="dd8d8c5b", label="3M ended 2025-03-31 interim (label 2025|Q1 correct; entity printed as a closed joint stock company)", period_end="2025-03-31", prior_end="2024-03-31", bs_prior_end="2024-12-31", period_type="Q1",
         reading="visual: pdf p4 BS (printed 3), p5 IS (4), p7 CF (6); pdf p4-7 have no text layer", pages=dict(bs=4, is_=5, cf=7),
         bs=dict(cur=bs(1021874939, 457697257, 564177682, 60007465, 391109531), prior=bs(997679841, 452155382, 545524459, 38005164, 393497885)),
         **{"is": dict(cur=isx(349829822, -298475076, 51354746, 22535186, 21028340, -913991, -1461126, 18653223, 0.47),
                       prior=isx(355512641, -281938592, 73574049, 42335256, 41139818, -1715887, -4778190, 34645741, 0.87))},
         cf=dict(cur=cf(41554927, -6999904, -12552722, 22002301, 38005164, 60007465), prior=cf(78766724, -36382341, -31549665, 10834718, 30586197, 41416400, fx=-4515))),
    dict(sha256_prefix="53e7dfe1", label="FY2024 audited consolidated FS (label 2025|FY = publication year; three annual files share the 2025|FY label)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="text layer: pdf p5 BS (printed 4), p6 IS (5), p8 CF (7)", pages=dict(bs=5, is_=6, cf=8),
         bs=dict(cur=bs(997679841, 452155382, 545524459, 38005164, 393497885), prior=bs(925754457, 443684577, 482069880, 30586197, 378805743)),
         **{"is": dict(cur=isx(1344476419, -1104413687, 240062732, 145869754, 139910066, -3330081, -11883774, 124696211, 3.12),
                       prior=isx(1361796751, -1077458925, 284337826, 174666764, 166930711, -3833795, -6399152, 156697764, 3.92))},
         cf=dict(cur=cf(166140732, -104882059, -53842763, 7415910, 30586197, 38005164, fx=3057), prior=cf(323765564, -84346016, -218801046, 20618502, 10075518, 30586197, fx=-107823))),
    dict(sha256_prefix="eb5b3333", label="FY2023 audited consolidated FS with 2022 restated (label 2025|FY = publication year; three annual files share the 2025|FY label)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="text layer: pdf p5 BS (printed 4), p6 IS (5), p8 CF (7); restatement table Note 31 pdf p50-53", pages=dict(bs=5, is_=6, cf=8),
         bs=dict(cur=bs(925754457, 443684577, 482069880, 30586197, 378805743), prior=bs(891697133, 464345438, 427351695, 10075518, 347682938, restated=True)),
         **{"is": dict(cur=isx(1361796751, -1077458925, 284337826, 174666764, 166930711, -3833795, -6399152, 156697764, 7.83,
                               _note="EPS 7.83 as issued (200 million shares); restated to 3.92 in the FY2024 filing after the 2024 capitalisation to 400 million shares"),
                       prior=isx(1414673208, -1260961312, 153711896, 77980000, 74415332, -2259111, -2637781, 69518440, 3.48, restated=True))},
         cf=dict(cur=cf(323765564, -84346016, -218801046, 20618502, 10075518, 30586197, fx=-107823),
                 prior=cf(13630946, -54774104, 37778071, -3365087, 12801519, 10075518, fx=639086, fx_note="cash of an acquired subsidiary, printed as a separate line", restated=True))),
    dict(sha256_prefix="3ad94137", label="FY2022 audited consolidated FS as issued (label 2025|FY = publication year; three annual files share the 2025|FY label; entity a closed joint stock company)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="text layer: pdf p5 BS (printed 4), p6 IS (5), p8 CF (7)", pages=dict(bs=5, is_=6, cf=8),
         bs=dict(cur=bs(881475624, 463305027, 418170597, 10075518, 337381414), prior=bs(774989974, 398534305, 376455669, 12801519, 318427733)),
         **{"is": dict(cur=isx(1414673208, -1227283899, 187389309, 66743589, 65234234, -2259111, -2637781, 60337342, None),
                       prior=isx(1049571818, -941602973, 107968845, 4590122, 6570362, -1588506, 2065848, 7047704, None))},
         cf=dict(cur=cf(13508394, -54774104, 37900623, -3365087, 12801519, 10075518, fx=639089, fx_note="cash of an acquired subsidiary",
                        rounding=-3, rounding_reason="printed 12,801,519 - 3,365,087 + 639,089 = 10,075,521 but the filing prints closing cash 10,075,518 (equal to the balance sheet); the restated comparative prints the acquired cash as 639,086",
                        _declared_diff={"cfo": CFR22, "cff": CFR22}),
                 prior=cf(17949481, -27510211, 11608849, 2048119, 10753400, 12801519))),
]
for d in docs:  # drop the free-text note key where None eps was passed
    for blk in ("is", "is_q"):
        for col in ("cur", "prior"):
            c = d.get(blk, {}).get(col)
            if c is not None and c.get("eps_basic") is None:
                c.pop("eps_basic", None)

S = lambda p, blk, col, k: [p, blk, col, k]
rolls = []
for k, nm in (("revenue", "revenue"), ("pbt", "profit before zakat and tax"), ("tax", "zakat plus income tax"), ("net_income", "net profit")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {nm}", total=S("f667bd74", "is", "cur", k), parts=[S("426d2249", "is", "cur", k), S("f667bd74", "is_q", "cur", k)]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {nm}", total=S("a1b78367", "is", "cur", k), parts=[S("dd8d8c5b", "is", "cur", k), S("a1b78367", "is_q", "cur", k)]))
    rolls.append(dict(name=f"2025 H1 + Q3 = 9M {nm}", total=S("b2faa977", "is", "cur", k), parts=[S("a1b78367", "is", "cur", k), S("b2faa977", "is_q", "cur", k)]))
write("1323", "UNITED CARTON INDUSTRIES COMPANY", docs, rolls, unit="Saudi riyals (SAR), full units as printed (not thousands)")
