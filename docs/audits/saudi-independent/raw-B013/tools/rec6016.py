"""Builds raw-B013/6016.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"
IS = "is"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


VIS = "visual (statement pages textless, rendered and read)"
documents = [
    doc("c85e4452", "FY ended 2022-12-31 FS as issued (collector label 2023|FY = publication year; inventory class other_no_statements_found)", False,
        {"bs": 6, IS: 7, "cf": 9}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("b38de818", "FY ended 2023-12-31 FS as issued (label 2024|FY = publication year)", False, {"bs": 6, IS: 7, "cf": 9}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("38566848", "FY ended 2024-12-31 FS as originally issued (label 2025|FY = publication year; inventory class partial_statements)", False,
        {"bs": 6, IS: 7, "cf": 9}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("dd1c4fa1", "FY ended 2025-12-31 consolidated FS with FY2024 and 1 Jan 2024 RESTATED (label 2026|FY; inventory class partial_statements)", False,
        {"bs": 7, IS: 8, "cf": 10}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("a61dd916", "3M and 6M ended 2025-06-30 as originally issued (inventory class partial_statements)", True, {"bs": 4, IS: 5, "cf": 7}, {"bs": 3, IS: 4, "cf": 6}, VIS),
    doc("0fda6794", "3M and 6M ended 2026-06-30, 2025 comparatives RESTATED (inventory class results_announcement)", True, {"bs": 5, IS: 6, "cf": 8}, {"bs": 3, IS: 4, "cf": 6}, VIS),
    doc("ef72a63d", "3M ended 2026-03-31, Q1 2025 comparative RESTATED (inventory class other_no_statements_found)", True, {"bs": 4, IS: 5, "cf": 7}, {"bs": 3, IS: 4, "cf": 6}, VIS),
]

identified = {
    "42587378": ("3M and 6M ended 2022-06-30 (cover text); company then named Bait Alshateera Fast Food Restaurants, a Saudi closed joint stock company", "text FS present; not transcribed"),
    "44256adb": ("3M and 9M ended 2023-09-30 (cover read, whole-file scan)", "scan 15 pages; not transcribed"),
    "e7a01bb5": ("3M and 6M ended 2023-06-30 (cover text)", "classed other_no_statements_found; statement pages not located; not transcribed"),
    "f0b1f55a": ("3M and 9M ended 2024-09-30 (cover text)", "statement pages pdf p3-7 textless; not transcribed"),
    "e2284416": ("Annual Report 2024, English (cover text)", "not transcribed; FY2024 values read from the FS file"),
    "e743b6d8": ("3M and 6M ended 2024-06-30 (cover text)", "text FS present; not transcribed"),
    "6bd85931": ("3M ended 2024-03-31 (cover read, whole-file scan)", "scan 15 pages; not transcribed"),
    "6cc8dff7": ("3M and 9M ended 2025-09-30 (cover text)", "statement pages pdf p3-7 textless; not transcribed"),
    "7ee80da6": ("Annual Report 2024, Arabic twin (cover text); label 2025|FY", "byte-identical file also stored under archive/SA/9520; not transcribed"),
    "ecb6d3bf": ("3M ended 2025-03-31 (cover read; 13 of 14 pages textless)", "scan; not transcribed; Q1 2025 restated values are known from the Q1 2026 comparatives"),
}

spec = dict(
    symbol="6016", name="BURGERIZZR (Bait Alshateera Fast Food Restaurants Co.)",
    method=("SHA-256 recomputed for every audited file. All seven filings have image-only statement pages (pdf p3-10 textless) and were rendered and read by eye; restatement notes (FY2025 Note 30, H1 2026 Note 14) were read from the text layer. "
            "tools/check_transcripts.py over transcripts/6016.json checks BS identity, cash-flow sum and roll (including cash acquired with a subsidiary as fx), gross profit, profit before zakat to net profit, owners + NCI, "
            "cross-filing agreement of comparatives (restated columns flagged and written up) and Q1 + Q2 = H1 rolls for 2026 and restated 2025; all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_7_filings_with_one_restatement_chain",
            summary=("Headline BS, income and cash-flow values (full SAR) from rendered pages for FY2022, FY2023, FY2024 (as issued), FY2025, H1 2025 (as issued), H1 2026 and Q1 2026; all identities hold with zero difference "
                     "and FY2022/FY2023/FY2024 comparatives agree between filings except declared EPS scale and a financing sub-line split. FY2025: revenue 366,481,879, net profit 11,138,948 (owners 10,914,889, NCI 224,059), total assets 223,350,412, "
                     "CFO 57,825,404, cash 21,114,749 after 482,881 acquired cash (goodwill 7,993,001 from a 2025 subsidiary acquisition). H1 2026: revenue 218,932,295, net profit 12,927,994; Q1 2026 + Q2 2026 = H1 2026 for revenue, cost, operating profit, "
                     "profit before zakat, net profit and owners' profit. RESTATED, never substituted: Note 30 (FY2025 filing) corrects prepaid government (Iqama/work-permit) fees as an IAS 8 error: FY2024 net profit 8,445,501 -> 8,186,709, cost of revenue "
                     "208,624,984 -> 208,883,776, total assets 151,245,092 -> 149,442,492, equity 72,059,455 -> 70,256,855, EPS 0.24 -> 0.23, and CFO 35,988,610 -> 34,875,418 with financing -17,473,552 -> -16,360,360 (finance cost paid moved from financing "
                     "to operating, 1,113,192) although the note says only profit before zakat and working capital are affected; 1 Jan 2024 equity 68,867,186 -> 67,323,378. Note 14 (H1 2026 filing) restates 6M 2025 net profit 3,273,403 -> 3,066,241 "
                     "(Q2 2025 1,073,621 -> 1,170,233, Q1 2025 restated 1,896,008) and EPS 0.09 -> 0.05 (also reflects 21,000,000 bonus shares, capital 35,000,000 -> 56,000,000). Share-count scale: FY2022 EPS 0.77 vs 0.077 in the FY2023 filing. "
                     "Interim cash flow: Q1 2026 CFO 10,238,265 vs H1 2026 CFO 23,375,389 and the Q1 statement has no zakat-paid line, so a Q2 cash flow by subtraction is NOT validated."),
            not_read=["notes in all files except restatement notes", "statements of changes in equity (FY2025 Q1 2026 equity statement glimpsed only)", "H1 2022, H1 2023, 9M 2023, Q1 2024, H1 2024, 9M 2024, Q1 2025, 9M 2025 filings",
                      "annual reports 2024 (English and Arabic)", "FY2021 and earlier: no standalone file (FY2021 known only as FY2022 comparatives)"]),
        document_completeness=dict(
            status="annual_FY2022_to_FY2025_and_interims_with_statements_every_opened_file_all_image_only",
            summary=("Every one of the seven opened filings carries all four statements, but the statement pages are textless images (auditor's reports too in the FY files), so the text-layer-based inventory finds none (FY2022 file classed "
                     "other_no_statements_found, H1 2026 file results_announcement, Q1 2026 file other_no_statements_found, FY2024, FY2025 and H1 2025 files partial_statements). 2023|9M and 2024|Q1 are whole-file scans classed scanned_unreadable "
                     "with cover pages for 3M/9M 2023 and Q1 2024."),
            defect_ids=["B013-6016-1", "B013-6016-2", "B013-6016-3"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_interims_2022H1_to_2026H1_with_gaps",
            present_in_files_by_page_derived_period=["FY2022", "FY2023", "FY2024", "FY2025", "2022 H1", "2023 H1", "2023 9M (scan)", "2024 Q1 (scan)", "2024 H1", "2024 9M", "2025 Q1 (scan)", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            values_verified_from_own_pages=["FY2022", "FY2023", "FY2024 (as issued)", "FY2025", "2025 H1 (as issued)", "2026 Q1", "2026 H1"],
            values_known_only_as_comparatives=["FY2021 (FY2022 filing)", "FY2024 restated and 1 Jan 2024 restated (FY2025 filing)", "H1 and Q2 2024 (H1 2025 filing)", "2025 Q1, H1, Q2 restated (Q1 2026 and H1 2026 filings)"],
            values_not_read=["2022 H1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1 original", "2024 9M", "2025 Q1 original", "2025 9M"],
            missing=["2022 Q1", "2022 9M", "2023 Q1", "FY2021 standalone", "everything before FY2021"],
            inventory_corrections=("Annual FS labels are the publication year (2023|FY holds FY2022, 2024|FY holds FY2023, 2025|FY holds FY2024, 2026|FY holds FY2025); annual reports are 2024|FY and 2025|FY for the same FY2024 report. "
                                   "Collector name BURGERIZZR corresponds to Bait Alshateera Fast Food Restaurants (also styled Shatirah House Restaurants Co. in the annual report cover)")),
    ),
    defects=[
        dict(id="B013-6016-1", **{"class": "image_only_statement_pages_not_detected"}, severity="high",
             evidence="All seven value-read filings have textless statement pages: c85e4452 and ef72a63d are classed other_no_statements_found, 0fda6794 results_announcement, 38566848, dd1c4fa1, a61dd916 partial_statements; the inventory statement_pages point to notes, not statements."),
        dict(id="B013-6016-2", **{"class": "restated_or_represented_comparatives"}, severity="high",
             evidence="FY2024 profit 8,445,501 as issued vs 8,186,709 restated (Note 30), CFO/CFF reclassification of 1,113,192; 1H 2025 profit 3,273,403 vs 3,066,241 restated (Note 14); EPS rebased for 56,000,000 shares. Both versions recorded; no value substituted."),
        dict(id="B013-6016-3", **{"class": "fiscal_year_label_is_publication_year"}, severity="medium",
             evidence="2023|FY is FY2022, 2024|FY is FY2023, 2025|FY is FY2024 (FS) and FY2024 annual report, 2026|FY is FY2025."),
        dict(id="B013-6016-4", **{"class": "duplicate_registry_symbol"}, severity="low",
             evidence="Two files (e2284416 annual report 2024 English and 7ee80da6 Arabic) are byte-identical to files in archive/SA/9520, which has 2 files and no raw-coverage record; entity verified as the same company from the report covers (Burgerizzr / Shatirah House Restaurants Co.). 9520 is absent from live_tadawul_list.json."),
        dict(id="B013-6016-5", **{"class": "share_count_rebasing"}, severity="low",
             evidence="FY2022 EPS 0.77 in the FY2022 filing versus 0.077 (35,000,000 weighted shares) in the FY2023 filing (share count of the FY2022 filing not read); 2026 filings use 56,000,000 shares after a 21,000,000 bonus issue."),
    ],
    unread_items=["notes in all files except restatement notes", "statements of changes in equity", "interims 2022 to 2024 and Q1/9M 2025 filings", "annual reports 2024", "reason for the FY2022 EPS 0.77 vs 0.077 scaling"],
    conclusion=("NOT claimed complete. Seven filings value-verified from rendered pages; one restatement chain recorded without substitution; 10 further files not value-read; "
                "no files for 2022 Q1/9M, 2023 Q1 and nothing before FY2021."),
)
mkrecord.build(spec)
