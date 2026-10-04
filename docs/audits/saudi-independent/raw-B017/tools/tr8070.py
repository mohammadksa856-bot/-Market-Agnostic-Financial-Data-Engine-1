"""Transcripts/8070.json: Arabian Shield Cooperative Insurance Company page transcriptions (SAR thousands as printed)."""
from tcommon import bs, cf, inc, write

R22 = "IFRS 4 as issued (842ec46a) versus IFRS 17 restated 2022 comparative in the FY2023 filing (efb18e0c): premium-based to insurance-revenue-based presentation, new technical accounts; net result 27,920 versus -18,225"
R23 = "FY2023 as first issued (efb18e0c) versus restated in the FY2024 filing (441d0b94, note 31): net result 44,188 versus 66,940, total assets 3,531,551 versus 3,355,638, equity 1,528,991 versus 1,544,237; cash flow reclassified (investments measured at FVTPL moved from investing to operating: CFO 48,420 versus 228,409, CFI -34,190 versus -214,179)"
docs = [
    dict(sha256_prefix="f37574d3", label="FY2025 audited FS (label 2026|FY = publication year); text layer present and agrees with the rendered pages", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="visual and text: pdf p10 BS, p11 IS, p14 CF (balance-sheet cash 259,168 includes restricted cash 9,549 per note 9 at pdf p73; cash-flow closing cash 249,619 excludes it)",
         pages=dict(bs=10, is_=11, cf=14),
         bs=dict(cur=bs(4894739, 3262431, 1632308, 259168, 20808), prior=bs(3613538, 1961443, 1652095, 82018, 5477)),
         **{"is": dict(cur=inc(1881892, -31270, -12483, -43753, eps_basic=-0.55), prior=inc(1566804, 93725, -22730, 70995, eps_basic=0.89))},
         cf=dict(cur=cf(50076, 127683, -10158, 167601, 82018, 249619), prior=cf(-31693, -46684, -576, -78953, 160971, 82018))),
    dict(sha256_prefix="441d0b94", label="FY2024 audited FS with 2023 and 1 Jan 2023 restated (label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p10 BS, p11 IS, p15 CF (pdf p10-15 textless)",
         pages=dict(bs=10, is_=11, cf=15),
         bs=dict(cur=bs(3613538, 1961443, 1652095, 82018, 5477), prior=bs(3355638, 1811401, 1544237, 160971, 5999, restated=True)),
         **{"is": dict(cur=inc(1566804, 93725, -22730, 70995, eps_basic=0.89), prior=inc(1127888, 87888, -20948, 66940, eps_basic=1.01, restated=True))},
         cf=dict(cur=cf(-31693, -46684, -576, -78953, 160971, 82018), prior=cf(228409, -214179, 8, 14238, 146733, 160971, restated=True))),
    dict(sha256_prefix="efb18e0c", label="FY2023 audited FS as first issued, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="text layer rows at pdf p12 BS, p13 IS, p17 CF; BS p12 also read as an image (column headers: 2023 as issued, 2022 and 1 Jan 2022 Restated)",
         pages=dict(bs=12, is_=13, cf=17),
         bs=dict(cur=bs(3531551, 2002560, 1528991, 160971, 5999, _declared_diff={"total_assets": R23, "total_liabilities": R23, "total_equity": R23}), prior=bs(2520772, 1335600, 1185172, 146733, 5978, restated=True)),
         **{"is": dict(cur=inc(1145711, 65136, -20948, 44188, eps_basic=0.67, _declared_diff={"revenue": R23, "pbt": R23, "net_income": R23, "ni_parent": R23}), prior=inc(918720, 406, -18631, -18225, eps_basic=-0.29, restated=True))},
         cf=dict(cur=cf(48420, -34190, 8, 14238, 146733, 160971, _declared_diff={"cfo": R23, "cfi": R23}), prior=cf(85390, -304411, 0, -219021, 365754, 146733, restated=True))),
    dict(sha256_prefix="842ec46a", label="FY2022 audited FS as issued under IFRS 4 (label 2023|FY = publication year; pdf p4-17 textless)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p11 BS, p12 IS, p16-17 CF",
         pages=dict(bs=11, is_=12, cf="16-17"),
         bs=dict(cur=bs(2678635, 1565749, 1112886, 146094, 5978, _declared_diff={"total_assets": R22, "total_liabilities": R22, "total_equity": R22, "cash": R22}),
                 prior=bs(1148622, 659909, 488713, 365555, 2713)),
         **{"is": dict(cur=dict(pbt=46551, tax=-18631, net_income=27920, ni_parent=27920, ni_nci=0, eps_basic=0.44, total_revenues_ifrs4=743375, _declared_diff={"pbt": R22, "tax": R22, "net_income": R22, "ni_parent": R22}),
                       prior=dict(pbt=36607, tax=-10454, net_income=26153, ni_parent=26153, ni_nci=0, eps_basic=0.65, total_revenues_ifrs4=411721))},
         cf=dict(cur=cf(101493, -320954, 0, -219461, 365555, 146094, _declared_diff={"cfo": R22, "cfi": R22, "net_change": R22, "cash_end": R22}), prior=cf(-74995, -77195, 0, -152190, 517745, 365555))),
    dict(sha256_prefix="604d6cc8", label="3M and 6M ended 2026-06-30 unaudited interim (inventory class scanned_unreadable; label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: whole file is image pages (no text layer); pdf p5 BS, p6 IS (3M 2026, 3M 2025, YTD 2026, YTD 2025), p9 CF (six months). Balance-sheet cash 801,315 versus cash-flow closing 789,306 (difference 12,009, restricted cash in note 9 not read)",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(7109123, 5466684, 1642439, 801315, 20814), prior=bs(4894739, 3262431, 1632308, 259168, 20808)),
         **{"is": dict(cur=inc(801665, 12305, -4580, 7725, eps_basic=0.10), prior=inc(912031, -17484, -5976, -23460, eps_basic=-0.29)),
            "is_q": dict(cur=inc(403269, 5099, -2272, 2827, eps_basic=0.04), prior=inc(460991, -27394, -2519, -29913, eps_basic=-0.37))},
         cf=dict(cur=cf(463298, 86682, -10293, 539687, 249619, 789306), prior=cf(103672, -20706, 0, 82966, 82018, 164984))),
    dict(sha256_prefix="86813dab", label="3M ended 2026-03-31 unaudited interim (inventory class partial_statements; label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p5 BS, p6 IS, p9 CF (pdf p4-9 textless). Balance-sheet cash 536,920 versus cash-flow closing 526,470 (difference 10,450, restricted cash in note 9 not read)",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(5948778, 4313424, 1635354, 536920, 20044), prior=bs(4894739, 3262431, 1632308, 259168, 20808)),
         **{"is": dict(cur=inc(398396, 7206, -2308, 4898, eps_basic=0.06), prior=inc(451040, 9910, -3457, 6453, eps_basic=0.08))},
         cf=dict(cur=cf(282897, -5253, -793, 276851, 249619, 526470), prior=cf(87771, -28973, 0, 58798, 82018, 140816))),
]
H, Q = "604d6cc8", "86813dab"
rolls = []
for k, name in (("revenue", "insurance revenue"), ("pbt", "result before zakat and tax"), ("tax", "zakat and tax"), ("net_income", "net result")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {name}", total=[H, "is", "cur", k], parts=[[Q, "is", "cur", k], [H, "is_q", "cur", k]]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {name}", total=[H, "is", "prior", k], parts=[[Q, "is", "prior", k], [H, "is_q", "prior", k]]))
write("8070", "ARABIAN SHIELD COOPERATIVE INSURANCE COMPANY", docs, rolls)
