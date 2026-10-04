"""Builds raw-B017/8300.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SAR 000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("b8fd2d1c", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 12}, {"bs": 7, "is": 8, "cf": 12}, "visual (pdf p7-12 textless)"),
    doc("b23739e4", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 12}, {"bs": 7, "is": 8, "cf": 12}, "visual (pdf p7-12 textless)",
        "2024 investing cash flow split differs by 240 between commission income and net gains lines versus the FY2025 comparative (totals identical)"),
    doc("5d5ba5ed", "FY ended 2023-12-31 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 13}, {"bs": 8, "is": 9, "cf": 13}, "visual (pdf p8-13 textless)"),
    doc("c0492e7e", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", False, {"bs": 7, "is": 8, "cf": "11-12"}, {"bs": 7, "is": 8, "cf": "11-12"}, "visual (pdf p7-12 textless)",
        "IFRS 4 presentation (gross premiums written); restated in the FY2023 filing: net result -18,344 to -27,662, loss before zakat -11,853 to -21,171, total assets 1,916,140 to 1,333,966, equity 380,459 to 400,038, CFO 62,175 to 57,318, CFI -221,855 to -216,998. Both declared; neither substituted."),
    doc("b538bac9", "3M and 6M ended 2026-06-30 reviewed interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 4, "is": 5, "cf": 8}, "visual (pdf p4-8 textless)",
        "income columns: 3M 2026, 3M 2025, 6M 2026, 6M 2025; cash flow is six-month only"),
    doc("3c17b8d5", "3M ended 2026-03-31 reviewed interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 4, "is": 5, "cf": 8}, "visual (pdf p4-8 textless)"),
]
cover = "(cover text only)"
identified = {
    "051eb54d": ("3M and 9M ended 2022-09-30 interim " + cover, "not transcribed; pdf p4-10 textless"),
    "2b54711b": ("3M and 6M ended 2022-06-30 interim " + cover, "not transcribed; pdf p4-10 textless"),
    "1015a2ff": ("3M ended 2022-03-31 interim " + cover, "not transcribed; pdf p3-10 textless"),
    "1bdf0d8e": ("3M and 9M ended 2023-09-30 interim " + cover, "not transcribed"),
    "8364f8d8": ("3M and 6M ended 2023-06-30 interim " + cover, "not transcribed"),
    "505ac217": ("3M ended 2023-03-31 interim " + cover, "not transcribed"),
    "67a49f47": ("3M and 9M ended 2024-09-30 interim " + cover, "not transcribed"),
    "de4eae89": ("3M and 6M ended 2024-06-30 interim " + cover, "not transcribed"),
    "a4b9cdff": ("3M ended 2024-03-31 interim " + cover, "not transcribed"),
    "65f802eb": ("3M and 9M ended 2025-09-30 interim " + cover, "not transcribed; inventory class partial_statements but pdf p4-8 are image pages"),
    "3a8d597c": ("3M and 6M ended 2025-06-30 interim " + cover, "not transcribed; H1 2025 comparatives read in the H1 2026 filing"),
    "5238b3e9": ("3M ended 2025-03-31 interim " + cover, "not transcribed; Q1 2025 comparatives read in the Q1 2026 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatement_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read from rendered image-only pages for FY2025, FY2024, FY2023 (2022 restated), FY2022 as issued under IFRS 4, H1 2026 and Q1 2026. All identities pass exactly. FY2025: insurance revenue 1,837,593, profit before zakat and tax 49,490, net profit 37,090 (EPS 0.93), total assets 2,043,961, equity 657,987, CFO -65,851, closing cash 102,074. FY2024 net profit 103,050; FY2023 84,581; FY2022 restated -27,662 (as issued IFRS 4 -18,344). H1 2026: revenue 1,342,569, net profit 9,126 (Q2 19,334, Q1 -10,208); Q1 + Q2 = H1 for revenue, pre-tax result, zakat plus tax and net result in 2026 and 2025 (pass). Cross-filing: every comparative in a later filing equals the earlier filing except the declared IFRS 4 to IFRS 17 FY2022 restatement (total assets 1,916,140 as issued versus 1,333,966 restated; the as-issued balance sheet is grossed up on a different basis). The FY2024 filing and the FY2025 comparative split investing commission income and gains differently (240) with identical totals. Insurance service expenses are printed in brackets (negative) in the income statement.",
        "not_read": ["notes in every file", "statements of changes in equity (only the FY2024 comparative page in FY2025 seen)", "FY2022 other comprehensive income page", "Q2 cash flow by subtraction not validated", "all other 12 interim filings", "segment-note totals versus the primary balance sheet"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_opened_all_statement_pages_are_image_only",
        "summary": "All six audited files carry balance sheet, income statement and cash flow as image-only pages (empty text layer on pdf p4-12 or p7-13), although the inventory classes eleven of eighteen files as partial (statement pages taken from notes) and b538bac9, 3c17b8d5, 65f802eb as partial_statements. Wataniya presents a single set of IFRS 17 statements in the primary pages; Insurance Authority supplementary statements appear in the annual file note pages (FY2025 pdf p87 to 92) and were not read. No FY2021 own FS exists in the collection.",
        "defect_ids": ["B017-8300-1", "B017-8300-2", "B017-8300-3"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_to_2026_H1_with_gaps_by_page_derived_period",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)",
                                                    "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "2025 Q1 and H1 (2026 filings)", "1 Jan 2022 restated balance sheet (FY2023 filing)"],
        "values_not_read": ["2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M", "2025 Q1/H1/9M originals"],
        "missing": ["FY2021 and earlier own filings (no file; the oldest file is the 2022 Q1 interim)", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in all four FS files (2023|FY holds FY2022 ... 2026|FY holds FY2025); interim labels match page periods. The inventory first_observed_period 2011|Q1 comes from announcements; the oldest file is the 2022 Q1 interim.",
    },
}
defects = [
    {"id": "B017-8300-1", "class": "image_only_or_scanned_statements_flagged_as_present_or_partial", "severity": "high",
     "evidence": "b8fd2d1c pdf p7-12, b23739e4 p7-12, 5d5ba5ed p8-13, c0492e7e p7-12, b538bac9 p4-8, 3c17b8d5 p4-8 are image-only; inventory classes b538bac9, 3c17b8d5, 65f802eb as partial_statements although full statements are present as images."},
    {"id": "B017-8300-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "c0492e7e FY2022 labelled 2023|FY, 5d5ba5ed FY2023 labelled 2024|FY, b23739e4 FY2024 labelled 2025|FY, b8fd2d1c FY2025 labelled 2026|FY."},
    {"id": "B017-8300-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17 transition: FY2022 net loss -18,344 as issued (c0492e7e pdf p8) versus -27,662 restated (5d5ba5ed pdf p9); total assets 1,916,140 versus 1,333,966; equity 380,459 versus 400,038; CFO 62,175 versus 57,318; opening cash 42,130 versus 42,126. Both recorded, none substituted."},
]
unread = ["notes in every file", "statements of changes in equity (except the FY2024 comparative page in FY2025)", "Insurance Authority supplementary statements (FY2025 pdf p87-92 etc.)", "12 interim filings 2022 Q1 to 2025 9M (identified by cover only)",
          "FY2021 and earlier (no file)", "Arabic originals (none in collection)", "segment-note totals versus the primary balance sheet"]
conclusion = ("NOT claimed complete. Six filings value-verified from rendered image-only pages (FY2022 as issued, FY2023, FY2024, FY2025, Q1 2026, H1 2026); the IFRS 17 FY2022 restatement is declared with both values; "
              "12 interim filings identified by cover but not value-read; FY2021 and earlier absent.")
mkrecord.build(dict(
    symbol="8300", name="WATANIYA INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All statement pages of the six audited filings are image-only and were rendered and read by eye. "
            "tools/check_transcripts.py over transcripts/8300.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat and tax to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, pre-tax result, zakat plus tax and net result (2026 and 2025); all pass.")))
