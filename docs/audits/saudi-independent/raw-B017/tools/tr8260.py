"""Transcripts/8260.json: Gulf General Cooperative Insurance Company page transcriptions (SAR thousands as printed)."""
from tcommon import bs, cf, inc, write

R22 = "IFRS 4 as issued (618d4f55) versus IFRS 17 restated 2022 comparative in the FY2023 filing (9062d8a2): total assets 602,511 versus 481,552, equity 267,616 versus 293,654, net result -104,190 versus -106,017, CFO -97,589 versus -100,898, CFI -152,175 versus -148,866"
docs = [
    dict(sha256_prefix="05cbd6dd", label="FY2025 audited FS, going-concern material uncertainty (label 2026|FY = publication year); text layer present and agrees with rendered income page", period_end="2025-12-31", prior_end="2024-12-31", period_type="FY",
         reading="text rows plus image read of income statement: pdf p8 BS, p9 IS, p12 CF",
         pages=dict(bs=8, is_=9, cf=12),
         bs=dict(cur=bs(349043, 183929, 165114, 8179, 10051), prior=bs(433186, 209280, 223906, 6559, 11088)),
         **{"is": dict(cur=inc(321752, -116988, -3500, -120488, eps_basic=-4.02), prior=inc(414352, -88592, -5615, -94207, eps_basic=-3.14))},
         cf=dict(cur=cf(-124385, 77275, 48730, 1620, 6559, 8179), prior=cf(-19209, 12600, -1294, -7903, 14462, 6559))),
    dict(sha256_prefix="951540a4", label="FY2024 audited FS (label 2025|FY = publication year)", period_end="2024-12-31", prior_end="2023-12-31", period_type="FY",
         reading="visual: pdf p8 BS, p9 IS, p12 CF (pdf p8-12 textless)",
         pages=dict(bs=8, is_=9, cf=12),
         bs=dict(cur=bs(433186, 209280, 223906, 6559, 11088), prior=bs(490197, 189804, 300393, 14462, 13532)),
         **{"is": dict(cur=inc(414352, -88592, -5615, -94207, eps_basic=-3.14), prior=inc(315646, 6319, -2787, 3532, eps_basic=0.12))},
         cf=dict(cur=cf(-19209, 12600, -1294, -7903, 14462, 6559), prior=cf(16742, -5917, -1514, 9311, 5151, 14462))),
    dict(sha256_prefix="9062d8a2", label="FY2023 audited FS, first IFRS 17 year, 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", period_end="2023-12-31", prior_end="2022-12-31", period_type="FY",
         reading="visual: pdf p8 BS, p9 IS, p13 CF",
         pages=dict(bs=8, is_=9, cf=13),
         bs=dict(cur=bs(490197, 189804, 300393, 14462, 13532), prior=bs(481552, 187898, 293654, 5151, 15499, restated=True)),
         **{"is": dict(cur=inc(315646, 6319, -2787, 3532, eps_basic=0.07), prior=inc(315686, -101999, -4018, -106017, eps_basic=-2.12, restated=True))},
         cf=dict(cur=cf(16742, -5917, -1514, 9311, 5151, 14462), prior=cf(-100898, -148866, -1197, -250961, 256112, 5151, restated=True))),
    dict(sha256_prefix="618d4f55", label="FY2022 audited FS as issued under IFRS 4 (label 2023|FY = publication year; image-only statements)", period_end="2022-12-31", prior_end="2021-12-31", period_type="FY",
         reading="visual: pdf p8 BS (printed 6), p9 IS (7), p12-13 CF (10-11)",
         pages=dict(bs=8, is_=9, cf="12-13"),
         bs=dict(cur=bs(602511, 334895, 267616, 5151, 15499, _declared_diff={"total_assets": R22, "total_liabilities": R22, "total_equity": R22}), prior=bs(639050, 268177, 370873, 256112, 13120)),
         **{"is": dict(cur=dict(pbt=-100172, tax=-4018, net_income=-104190, ni_parent=-104190, ni_nci=0, eps_basic=-2.08, total_revenues_ifrs4=258702, _declared_diff={"pbt": R22, "net_income": R22, "ni_parent": R22}),
                       prior=dict(pbt=-84075, tax=-2701, net_income=-86776, ni_parent=-86776, ni_nci=0, eps_basic=-3.16, total_revenues_ifrs4=251165))},
         cf=dict(cur=cf(-97589, -152175, -1197, -250961, 256112, 5151, _declared_diff={"cfo": R22, "cfi": R22}), prior=cf(-133800, -10977, 239495, 94718, 161394, 256112))),
    dict(sha256_prefix="08af868a", label="3M and 6M ended 2026-06-30 unaudited interim, review report with solvency non-compliance emphasis (label 2026|H1 correct); latest period in the collection", period_end="2026-06-30", prior_end="2025-06-30", bs_prior_end="2025-12-31", period_type="H1",
         reading="visual: pdf p5 BS (printed 3), p6 IS (4; columns 3M 2026, 3M 2025, 6M 2026, 6M 2025), p9 CF (7); pdf p4-9 textless",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(356654, 221028, 135626, 14704, 8750), prior=bs(349043, 183929, 165114, 8179, 10051)),
         **{"is": dict(cur=inc(174903, -27088, -2400, -29488, eps_basic=-0.98), prior=inc(173453, -50461, -2400, -52861, eps_basic=-1.76)),
            "is_q": dict(cur=inc(93847, -14269, -1200, -15469, eps_basic=-0.52), prior=inc(79344, -27879, -1200, -29079, eps_basic=-0.97))},
         cf=dict(cur=cf(4238, 2706, -419, 6525, 8179, 14704), prior=cf(-86150, 89914, -494, 3270, 6559, 9829))),
    dict(sha256_prefix="4cfca767", label="3M ended 2026-03-31 unaudited interim with going-concern material uncertainty in the review report (label 2026|Q1 correct)", period_end="2026-03-31", prior_end="2025-03-31", bs_prior_end="2025-12-31", period_type="Q1",
         reading="visual: pdf p5 BS, p6 IS, p9 CF (pdf p3-9 textless)",
         pages=dict(bs=5, is_=6, cf=9),
         bs=dict(cur=bs(354976, 203881, 151095, 12743, 9262), prior=bs(349043, 183929, 165114, 8179, 10051)),
         **{"is": dict(cur=inc(81056, -12819, -1200, -14019, eps_basic=-0.47), prior=inc(94109, -22582, -1200, -23782, eps_basic=-0.79))},
         cf=dict(cur=cf(3577, 1406, -419, 4564, 8179, 12743), prior=cf(-68157, 180109, -398, 111554, 6559, 118113))),
]
H, Q = "08af868a", "4cfca767"
rolls = []
for k, name in (("revenue", "insurance revenue"), ("pbt", "loss before zakat"), ("tax", "zakat"), ("net_income", "net loss")):
    rolls.append(dict(name=f"2026 Q1 + Q2 = H1 {name}", total=[H, "is", "cur", k], parts=[[Q, "is", "cur", k], [H, "is_q", "cur", k]]))
    rolls.append(dict(name=f"2025 Q1 + Q2 = H1 {name}", total=[H, "is", "prior", k], parts=[[Q, "is", "prior", k], [H, "is_q", "prior", k]]))
write("8260", "GULF GENERAL COOPERATIVE INSURANCE COMPANY", docs, rolls)
