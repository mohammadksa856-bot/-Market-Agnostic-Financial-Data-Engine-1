"""Transcripts/1324.json: Saleh Abdulaziz Al Rashed and Sons Company page transcriptions. Amounts are full Saudi riyals as printed."""
from tcommon import bs, cf, write


def isx(rev, cost, gp, op, pbt, tax, ni, par, nci, eps=None, **k):
    d = dict(revenue=rev, cost_of_revenue=cost, gross_profit=gp, operating_income=op, pbt=pbt, tax=tax, net_income=ni, ni_parent=par, ni_nci=nci, **k)
    if eps is not None:
        d["eps_basic"] = eps
    return d


REP = "re-presentation of the FY2024 comparative in the FY2025 filing (operating and investing cash flow lines and current asset classification moved; net change in cash and closing cash identical)"
REP23 = "re-presentation of the 2023 comparative in the FY2024 filing (operating 56,982,967 as issued versus 56,765,462; investing -97,972,448 versus -97,754,943; total assets 428,694,195 versus 428,590,605; net change identical)"
SP = "FY2022 special purpose financial statements of a limited liability company (3a9efe83) versus the 2022 comparative column of the FY2023 consolidated financial statements (6d210026): different basis and measurement (cost of revenue, G&A, receivables, accrued expenses, retained earnings); both recorded, neither substituted"

docs = [
    dict(sha256_prefix="35231b87", label="3M and 6M ended 2026-06-30 interim (label 2026|H1 correct); latest period; whole file is a scan with garbled OCR text", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3; 3M and 6M), p7-8 CF (5-6, six months)", pages=dict(bs=4, is_=5, cf="7-8"),
         bs=dict(cur=bs(614252301, 199195922, 415056379, 27791612, 261152804), prior=bs(630305544, 191605797, 438699747, 60344504, 275722297)),
         **{"is": dict(cur=isx(315782024, -272501960, 43280064, 17799489, 15522683, -2131032, 13391651, 15652966, -2261315, 0.84),
                       prior=isx(360882083, -285991165, 74890918, 43207442, 43173870, -2026376, 41147494, 41154499, -7005, 2.21)),
            "is_q": dict(cur=isx(160614487, -140531883, 20082604, 7477128, 6177999, -964636, 5213363, 6400985, -1187622, 0.34),
                         prior=isx(190180875, -155030007, 35150868, 21222154, 19033780, -1039202, 17994578, 17997768, -3190, 0.97))},
         cf=dict(cur=cf(16885587, -26112019, -23326460, -32552892, 60344504, 27791612), prior=cf(47561238, -50833429, 2516294, -755897, 25914252, 25158355))),
    dict(sha256_prefix="2e8fae42", label="3M ended 2026-03-31 interim (label 2026|Q1 correct); whole file is a scan with garbled OCR text", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p4 BS (printed 2), p5 IS (3), p7-8 CF (5-6)", pages=dict(bs=4, is_=5, cf="7-8"),
         bs=dict(cur=bs(625424316, 178401300, 447023016, 27782144, 265811769), prior=bs(630305544, 191605797, 438699747, 60344504, 275722297)),
         **{"is": dict(cur=isx(155167537, -131970077, 23197460, 10322361, 9344684, -1166396, 8178288, 9251981, -1073693, 0.50),
                       prior=isx(170701208, -130734498, 39966710, 21985288, 24140090, -987174, 23152916, 23156731, -3815, 1.24))},
         cf=dict(cur=cf(-17483838, -10460260, -4618262, -32562360, 60344504, 27782144), prior=cf(-3314678, -13452062, 11469442, -5297298, 25914252, 20616954))),
    dict(sha256_prefix="b8514899", label="FY2025 audited consolidated FS, signed copy with audit-trail page (label 2026|FY = publication year; twin 866e75f2 lacks the audit-trail page)", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="text layer: pdf p7 BS (printed 5), p8 IS (6), p10-11 CF (8-9)", pages=dict(bs=7, is_=8, cf="10-11"),
         bs=dict(cur=bs(630305544, 191605797, 438699747, 60344504, 275722297), prior=bs(506679299, 150065565, 356613734, 25914252, 205741535)),
         **{"is": dict(cur=isx(739521228, -575558749, 163962479, 104216501, 95849746, -4284669, 91565077, 91656884, -91807, 4.93),
                       prior=isx(599584163, -492890316, 106693847, 63204686, 63987625, -4300062, 59687563, 59688293, -730, 3.21))},
         cf=dict(cur=cf(177386171, -139661022, -3294897, 34430252, 25914252, 60344504), prior=cf(86122981, -68528335, -3230424, 14364222, 11550030, 25914252))),
    dict(sha256_prefix="730be357", label="FY2024 audited consolidated FS (label 2026|FY = publication year; entity printed as closed joint stock company)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="text layer: pdf p6 BS (printed 4), p7 IS (5), p9 CF (7)", pages=dict(bs=6, is_=7, cf=9),
         bs=dict(cur=bs(506679299, 150065565, 356613734, 25914252, 205741535), prior=bs(428590605, 120700045, 307890560, 11550030, 193200130)),
         **{"is": dict(cur=isx(599584163, -492890316, 106693847, 63204686, 63987625, -4300062, 59687563, 59688293, -730, 3.21),
                       prior=isx(498692692, -401343696, 97348996, 54376082, 51148560, -4090314, 47058246, 47058246, 0, 2.53))},
         cf=dict(cur=cf(87856238, -70241592, -3250424, 14364222, 11550030, 25914252, _declared_diff={"cfo": REP, "cfi": REP, "cff": REP}),
                 prior=cf(56765462, -97754943, 34200371, -6789110, 18339140, 11550030))),
    dict(sha256_prefix="6d210026", label="FY2023 audited consolidated FS as issued (label 2026|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="text layer: pdf p5 BS (printed 3), p6 IS (4), p8-9 CF (6-7)", pages=dict(bs=5, is_=6, cf="8-9"),
         bs=dict(cur=bs(428694195, 120803635, 307890560, 11550030, 193425779, _declared_diff={"total_assets": REP23, "total_liabilities": REP23, "ppe": REP23}),
                 prior=bs(348555300, 89380643, 259174657, 18339140, 128498469)),
         **{"is": dict(cur=isx(498692692, -401343696, 97348996, 54376082, 51148560, -4090314, 47058246, 47058246, 0),
                       prior=isx(429460881, -310045582, 119415299, 71390884, 71952220, -1964926, 69987294, 69987294, 0))},
         cf=dict(cur=cf(56982967, -97972448, 34200371, -6789110, 18339140, 11550030, _declared_diff={"cfo": REP23, "cfi": REP23}),
                 prior=cf(57926765, -82018703, -6500000, -30591938, 48931078, 18339140))),
    dict(sha256_prefix="3a9efe83", label="FY2022 special purpose FS of a limited liability company (label 2026|FY; PDF metadata names another company, text names Saleh Abdulaziz Al Rashed and Sons)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="text layer: pdf p3 BS (printed 4), p4 IS (5), p6 CF (7)", pages=dict(bs=3, is_=4, cf=6),
         bs=dict(cur=bs(341824434, 87072123, 254752311, 18339139, 128498469, _declared_diff={"total_assets": SP, "total_liabilities": SP, "total_equity": SP}),
                 prior=bs(269433612, 160329612, 109104000, 48931087, 75736166, restated=True)),
         **{"is": dict(cur=isx(429460879, -308286020, 121174859, 72192916, 72754252, -1964926, 70789326, 70789326, 0, 1.416,
                               _declared_diff={k: SP for k in ("revenue", "cost_of_revenue", "gross_profit", "operating_income", "pbt", "net_income", "ni_parent")}),
                       prior=isx(349769400, -236065533, 113703867, 71027019, 72317684, -2035250, 70282434, 70282434, 0, 1.406, restated=True))},
         cf=dict(cur=cf(62419962, -81776188, -11235722, -30591948, 48931087, 18339139, _declared_diff={k: SP for k in ("cfo", "cfi", "cff", "net_change", "cash_end")}),
                 prior=cf(53008751, -34150137, 1500000, 20358614, 28572473, 48931087, restated=True))),
]
S = lambda p, blk, col, k: [p, blk, col, k]
rolls = []
for k, nm in (("revenue", "revenue"), ("pbt", "profit before zakat"), ("tax", "zakat"), ("net_income", "net profit"), ("ni_parent", "profit to shareholders"), ("ni_nci", "non-controlling interests")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {nm}", total=S("35231b87", "is", "cur", k), parts=[S("2e8fae42", "is", "cur", k), S("35231b87", "is_q", "cur", k)]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {nm} (comparatives)", total=S("35231b87", "is", "prior", k), parts=[S("2e8fae42", "is", "prior", k), S("35231b87", "is_q", "prior", k)]))
write("1324", "SALEH ABDULAZIZ AL RASHED AND SONS COMPANY", docs, rolls, unit="Saudi riyals (SAR), full units as printed (not thousands)")
