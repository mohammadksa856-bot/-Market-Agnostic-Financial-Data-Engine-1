"""Builds raw-B015/8270.json from the page transcripts."""
import mkrecord

U = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("e0d99bd9", "FY ended 2024-12-31 audited FS (collector label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 12}, {"bs": 3, "is": 4, "cf": 7},
        "visual (statement pages image-only, pdf p3-12 textless)"),
    doc("bc6d203e", "FY ended 2023-12-31 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", False, {"bs": 12, "is": 13, "cf": 16}, {"bs": 3, "is": 4, "cf": 7},
        "visual (image-only, pdf p3-16 textless)"),
    doc("5da7b83a", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 11}, {"bs": 6, "is": 7, "cf": 10},
        "visual (image-only, pdf p3-11 textless)",
        "restated to IFRS 17 in the FY2023 filing: net loss -39,293,106 to -29,000,327, total assets 793,814,537 to 752,056,846, equity 394,779,424 to 420,484,271, CFO -129,942,452 to -150,647,857, CFI 147,961,867 to 170,331,457, closing cash 254,910,052 to 255,969,579. Both declared; neither substituted."),
    doc("c04bbe5e", "3M and 6M ended 2025-06-30 reviewed interim (label 2025|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 3, "is": 4, "cf": 7},
        "visual (image-only, pdf p3-8 textless)", "income columns are three-month 2025, three-month 2024, six-month 2025, six-month 2024; cash flow is six-month only"),
    doc("31885374", "3M ended 2025-03-31 reviewed interim (label 2025|Q1 correct)", True, {"bs": 4, "is": 5, "equity": 7}, {"bs": 3, "is": 4, "equity": 6},
        "visual (image-only, pdf p3-8 textless); cash flow page not read"),
]
identified = {
    "6f6383be": ("3M and 9M ended 2021-09-30 interim (cover text; pdf p3-8 textless)", "not transcribed"),
    "4d101c8c": ("3M and 6M ended 2021-06-30 interim (cover image read; zero text on pdf p1-8)", "not transcribed"),
    "f9a872aa": ("3M ended 2021-03-31 interim (cover text)", "not transcribed"),
    "3840ce4c": ("3M and 9M ended 2022-09-30 interim (cover text)", "not transcribed"),
    "5f6542c5": ("FY ended 2021-12-31 audited FS under IFRS 4 (cover image read; label 2022|FY = publication year)", "not transcribed; FY2021 values known only as the comparative column in the FY2022 filing"),
    "edde7b96": ("3M and 6M ended 2022-06-30 interim (cover text)", "not transcribed"),
    "6359b493": ("3M ended 2022-03-31 interim (cover text)", "not transcribed"),
    "7d8f4a7e": ("3M and 9M ended 2023-09-30 interim (cover image read; pdf p1-7 textless)", "not transcribed"),
    "53e21da9": ("3M and 6M ended 2023-06-30 interim (cover text); inventory class other_no_statements_found is wrong (pdf p3-8 image-only)", "not transcribed"),
    "a3b17f11": ("3M ended 2023-03-31 interim (cover text); inventory class other_no_statements_found is wrong (pdf p3-8 image-only)", "not transcribed"),
    "c10f9e10": ("3M and 9M ended 2024-09-30 interim (cover text)", "not transcribed"),
    "573a04ae": ("3M and 6M ended 2024-06-30 interim (cover text)", "not transcribed; 6M and Q2 2024 read as comparatives in the H1 2025 filing"),
    "ea764f26": ("3M ended 2024-03-31 interim (cover text)", "not transcribed; Q1 2024 read as comparative in the Q1 2025 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_5_filings_declared_restatement_noted",
        "summary": "Headline BS, income and cash-flow values (full SAR) read from rendered image-only pages for FY2024, FY2023 (with 2022 restated), FY2022 as issued under IFRS 4, H1 2025 (with 3M and prior-year columns) and Q1 2025. All identities hold exactly; every comparative agrees with the earlier filing except the declared IFRS 17 items. FY2024: insurance revenue 372,730,192, profit before zakat 19,191,600, net profit 9,385,565 (EPS 0.31 on 30,000,000 shares), total assets 769,087,328, equity 474,372,502, CFO -80,113,398, closing cash 173,678,154. FY2023 net profit 20,083,440; FY2022 restated net loss -29,000,327 (as issued under IFRS 4 -39,293,106). H1 2025: revenue 215,080,562, net profit 2,838,232 (Q2 1,539,833), equity 479,719,957; Q1 + Q2 = H1 for 2025 and 2024 for revenue, profit before zakat and net profit (pass). Declared differences: IFRS 17 transition for FY2022 (as issued versus restated: net result, total assets, equity, CFO, CFI, net change, closing cash 254,910,052 versus 255,969,579). FY2022 as issued has no insurance-revenue line (premiums and underwriting presentation), so gross written premiums and total revenues are recorded under their own keys. Only the six-month cash flow was read for 2025, so Q2 cash flow by subtraction was not tested and is NOT validated.",
        "not_read": ["notes in every file", "statements of changes in equity (except Q1 2025 p6 glimpsed)", "Q1 2025 cash flow", "FY2021 own statements", "all other interims"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_five_files_opened_all_statement_pages_are_image_only",
        "summary": "All five audited files carry balance sheet, income statement and cash-flow statement (Q1 2025 cash flow not read) as image-only pages with no text layer, although the inventory classes them financial_statements; two 2023 interims are classed other_no_statements_found and two interims (H1 2021, 9M 2023) have no extractable text on the first pages. The collection ends at H1 2025: no 9M 2025, FY2025 or 2026 file, and the collector announcement state lists no results slot after 2025|H1 (reason not established from pages).",
        "defect_ids": ["B015-8270-1", "B015-8270-2", "B015-8270-3", "B015-8270-4"],
    },
    "company_coverage": {
        "status": "annual_FY2021_to_FY2024_and_interims_2021_to_2025_H1_with_gaps_by_page_derived_period",
        "present_in_files_by_page_derived_period": ["FY2021 (label 2022|FY)", "FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)",
                                                    "2021 Q1", "2021 H1", "2021 9M", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "2025 Q1 (income and balance sheet)", "2025 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "2024 Q1, H1 and Q2 (2025 filings)"],
        "values_not_read": ["2021 Q1/H1/9M", "2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M originals", "FY2021 own statements"],
        "missing": ["2025 9M", "FY2025", "2026 and later", "FY2020 and earlier (no file)"],
        "inventory_corrections": "FY labels equal the publication year in all four FS files (2022|FY holds FY2021, 2023|FY FY2022, 2024|FY FY2023, 2025|FY FY2024); the inventory period_mismatch flags are correct detections. The inventory class other_no_statements_found for 53e21da9 and a3b17f11 is wrong (image-only statements).",
    },
}
defects = [
    {"id": "B015-8270-1", "class": "image_only_or_scanned_statements_flagged_as_present_or_absent", "severity": "high",
     "evidence": "Statement pages image-only in every audited file (e0d99bd9 pdf p3-12, bc6d203e p3-16, 5da7b83a p3-11, c04bbe5e p3-8, 31885374 p3-8); 53e21da9 and a3b17f11 classed other_no_statements_found; 4d101c8c and 7d8f4a7e have no extractable text on pdf p1-8 and p1-7."},
    {"id": "B015-8270-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "5f6542c5 FY2021 labelled 2022|FY, 5da7b83a FY2022 labelled 2023|FY, bc6d203e FY2023 labelled 2024|FY, e0d99bd9 FY2024 labelled 2025|FY. A label reader would shift every annual value by one year."},
    {"id": "B015-8270-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17 transition: FY2022 net loss -39,293,106 as issued (5da7b83a pdf p8) versus -29,000,327 restated (bc6d203e pdf p13); total assets 793,814,537 versus 752,056,846; equity 394,779,424 versus 420,484,271; CFO -129,942,452 versus -150,647,857. Both recorded, none substituted; revenue is not comparable across the transition."},
    {"id": "B015-8270-4", "class": "series_ends_without_stated_reason", "severity": "medium",
     "evidence": "No 9M 2025, FY2025 or 2026 file exists and the collector announcement state lists no results slot after 2025|H1. Notes were not read, so whether the series ended or the collection stopped is not established."},
]
unread = ["notes in every file", "statements of changes in equity", "Q1 2025 cash flow", "13 other filings (identified by cover only), including FY2021 own FS", "FY2020 and earlier (no file)", "reason the series stops at H1 2025", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Five filings value-verified from rendered image-only pages (FY2022 as issued, FY2023, FY2024, Q1 2025, H1 2025); IFRS 17 restatement of FY2022 declared with both values; "
              "13 further filings identified by cover but not value-read; no FY2025, 9M 2025 or 2026 documents in the collection.")
mkrecord.build(dict(
    symbol="8270", name="BURUJ COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All statement pages of the five audited filings are image-only and were rendered and read by eye. "
            "tools/check_transcripts.py over transcripts/8270.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat profit plus zakat to net profit, cross-filing comparatives "
            "(declared differences only: FY2022 IFRS 17 restatement keys) and Q1 + Q2 = H1 rolls for revenue, profit before zakat and net profit (2025 and 2024); all pass.")))
