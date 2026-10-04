"""Builds raw-B013/6004.json (audit record) from the page transcripts."""
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
    doc("20bface3", "FY ended 2022-12-31 audited consolidated FS of Saudi Airlines Catering Company (collector label 2023|FY = publication year)", False,
        {"bs": 7, IS: 8, "cf": 10}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("66999970", "FY ended 2023-12-31 audited consolidated FS of Catrion Catering Holding (formerly Saudi Airlines Catering); label 2024|FY = publication year; inventory class partial_statements", False,
        {"bs": 7, IS: 8, "cf": 10}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("954d5faa", "FY ended 2024-12-31 audited consolidated FS (label 2025|FY = publication year)", False, {"bs": 7, IS: 8, "cf": 10}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("f53011f6", "FY ended 2025-12-31 audited consolidated FS (label 2026|FY = publication year)", False, {"bs": 7, IS: 8, "cf": 10}, {"bs": 5, IS: 6, "cf": 8}, VIS),
    doc("d7dea47a", "3M and 6M ended 2025-06-30 unaudited (text layer with missing lines; headline totals only)", True, {"bs": 5, IS: 4, "cf": 7}, {"bs": 3, IS: 2, "cf": 5},
        "text layer (incomplete); cost of revenue not transcribed", "H1 2025 values agree with the comparative columns in the H1 2026 filing"),
    doc("9b85d057", "3M and 6M ended 2026-06-30 unaudited", True, {"bs": 6, IS: 4, "cf": 8}, {"bs": 4, IS: 2, "cf": 6},
        "visual for IS and CF (text layer scrambles lines and drops values), text layer for BS tied by identity",
        "extracted text drops cost of revenue, general and administrative expenses for 2026 and the financing lines"),
    doc("9af63009", "3M ended 2026-03-31 unaudited (statement pages image-only)", True, {"bs": 5, IS: 4, "cf": 7}, {"bs": 3, IS: 2, "cf": 5}, VIS),
]

identified = {
    "18f6ddc9": ("3M and 9M ended 2022-09-30, Saudi Airlines Catering Company (cover text)", "classed other_no_statements_found; pdf p3-7 textless; not transcribed"),
    "57729b29": ("3M and 6M ended 2022-06-30 (cover text)", "classed other_no_statements_found; pdf p3-7 textless; not transcribed"),
    "0c42652a": ("3M ended 2022-03-31 (cover text)", "classed other_no_statements_found; not transcribed"),
    "5f19d5f7": ("3M and 9M ended 2023-09-30, Catrion (cover text)", "classed other_no_statements_found; not transcribed"),
    "2c98e474": ("3M and 6M ended 2023-06-30 (cover text)", "classed other_no_statements_found; pdf p3-7 textless; not transcribed"),
    "e4d31808": ("3M ended 2023-03-31 (cover text)", "classed other_no_statements_found; pdf p3-7 textless; not transcribed"),
    "a61b1e5a": ("3M and 9M ended 2024-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "baf7e0ad": ("3M and 6M ended 2024-06-30 (cover read, whole-file scan 25 pages)", "classed scanned_unreadable; statements not transcribed; 6M 2024 known from the H1 2025 comparatives (partial)"),
    "101391e4": ("3M ended 2024-03-31 (cover text)", "pdf p4-7 textless; not transcribed"),
    "0d864404": ("3M and 9M ended 2025-09-30 (cover text)", "pdf p4-7 textless; not transcribed"),
    "a66c7a08": ("3M ended 2025-03-31 (cover text)", "pdf p4-7 textless; not transcribed; Q1 2025 known from the Q1 2026 comparatives"),
}

spec = dict(
    symbol="6004", name="CATRION (Catrion Catering Holding Co, formerly Saudi Airlines Catering Company)",
    method=("SHA-256 recomputed for every audited file. All four annual filings and the Q1 2026 interim have image-only statement pages and were rendered and read by eye; the H1 2026 income statement and cash flow were rendered "
            "because the text layer scrambles lines and drops values; the H1 2025 text layer is incomplete and only arithmetic-tied headline lines were transcribed. tools/check_transcripts.py over transcripts/6004.json "
            "checks BS identity, cash-flow sum and roll, gross profit, profit before zakat to net profit, owners + NCI, cross-filing agreement of comparatives and Q1 + Q2 = H1 rolls for 2026 and 2025; all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_7_filings_no_restatement_found",
            summary=("Headline BS, income and cash-flow values (full SAR) transcribed for FY2022 (with FY2021), FY2023, FY2024, FY2025, H1 2025 (headline lines), H1 2026 (with Q2) and Q1 2026 (with Q1 2025). "
                     "All identities hold with zero difference and every comparative column agrees with the earlier filing of the same period; no restatement was found. FY2025: revenue 2,441,044,531, net profit 313,621,296, "
                     "total assets 3,451,579,427, CFO 320,222,095, cash 398,453,391. FY2024: revenue 2,299,259,701, net 352,770,108. FY2023: revenue 2,133,762,298, net 282,657,704. FY2022: revenue 1,818,006,368, net 257,103,138; "
                     "FY2021 net 14,055,459. H1 2026: revenue 1,352,198,759, net 127,223,568 (owners 127,972,658, NCI -749,090 after a 2026 subsidiary acquisition with goodwill 367,527,145); Q1 2026 + Q2 2026 = H1 2026 for revenue, cost, "
                     "operating profit, profit before zakat, net profit and owners' profit, and Q1 2025 + Q2 2025 = H1 2025 for revenue, gross profit, operating profit, profit before zakat and net profit. "
                     "Presentation notes: the FY2022 file shows 'cash generated from operating activities' 377,368,494 and the FY2023 file 384,843,240 for FY2022 (long-term bonus paid shown separately), CFO identical 346,200,353; "
                     "the FY2025 filing renames the statutory reserve (246,000,000) to Reserve; FY2021 EPS 0.17. Interim cash flow: Q1 2026 CFO 223,926,355 versus H1 2026 CFO 364,694,057; the acquisition payment is 309,878,023 in the Q1 "
                     "statement and 309,875,862 in the H1 statement, so a Q2 cash flow by subtraction is NOT validated."),
            not_read=["notes in every file", "statements of changes in equity (H1 2026 equity text only partially extracted; Q1 2026 equity statement not read)", "H1 2025 cost of revenue and several lines (text layer incomplete)",
                      "2022 Q1/H1/9M, 2023 Q1/H1/9M, 2024 Q1/H1/9M, 2025 Q1/9M filings", "annual reports: none in the collection for this symbol"]),
        document_completeness=dict(
            status="annual_FY2022_to_FY2025_and_interims_2022Q1_to_2026H1_with_statements_image_only_in_most_files",
            summary=("All annual FS and the Q1 2026 interim carry image-only statement pages (pdf p6-10 or p4-7 textless), so the text-layer inventory classes seven interim files other_no_statements_found and one whole-file scan scanned_unreadable "
                     "although they contain full statements (checked for those opened). The H1 2026 file has a scrambled text layer that omits values; the H1 2025 text layer omits lines. FY files carry the publication-year label. "
                     "2022 and early-2023 files belong to Saudi Airlines Catering Company; the company was renamed Catrion Catering Holding Co in 2023 and is also styled Catrion for Catering Holding Company."),
            defect_ids=["B013-6004-1", "B013-6004-2", "B013-6004-3"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_interims_2022Q1_to_2026H1_complete_by_label",
            present_in_files_by_page_derived_period=["FY2022", "FY2023", "FY2024", "FY2025", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1 (scan)", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            values_verified_from_own_pages=["FY2022", "FY2023", "FY2024", "FY2025", "2025 H1 (headline lines)", "2026 Q1", "2026 H1"],
            values_known_only_as_comparatives=["FY2021 (FY2022 filing)", "2024 H1 and Q2 headline lines (H1 2025 filing)", "2025 Q1 (Q1 2026 filing)", "2025 Q2 and H1 (H1 2026 filing)"],
            values_not_read=["2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1 original", "2025 9M"],
            missing=["FY2021 standalone", "everything before FY2021", "annual reports"],
            inventory_corrections=("FY labels are publication years (2023|FY holds FY2022, 2024|FY holds FY2023, 2025|FY holds FY2024, 2026|FY holds FY2025). Interim labels match the periods on the covers.")),
    ),
    defects=[
        dict(id="B013-6004-1", **{"class": "image_only_statement_pages_not_detected"}, severity="high",
             evidence="Annual FS 20bface3, 66999970, 954d5faa, f53011f6 have textless statement pages (pdf p6-10 or p7-10); interims 18f6ddc9, 57729b29, 0c42652a, 5f19d5f7, 2c98e474, e4d31808, a61b1e5a classed other_no_statements_found; 101391e4, 0d864404, a66c7a08, 9af63009 have textless statement pages; baf7e0ad is a whole-file scan."),
        dict(id="B013-6004-2", **{"class": "scrambled_or_incomplete_text_layer"}, severity="high",
             evidence="9b85d057 (H1 2026): extracted text interleaves cost of revenue with gross profit and drops 2026 G&A, hedging, lease and financing values; d7dea47a (H1 2025): cost of revenue and many lines missing. Text-layer parsing would give wrong or missing values; rendered pages were used."),
        dict(id="B013-6004-3", **{"class": "fiscal_year_label_is_publication_year"}, severity="medium",
             evidence="2023|FY is FY2022 (Saudi Airlines Catering), 2024|FY is FY2023, 2025|FY is FY2024, 2026|FY is FY2025."),
        dict(id="B013-6004-4", **{"class": "company_rename"}, severity="low",
             evidence="Files for 2022 to Q2 2023 are titled Saudi Airlines Catering Company; later files Catrion Catering Holding Company (formerly known as Saudi Airlines Catering Company). Same registry symbol 6004, same company on the pages."),
        dict(id="B013-6004-5", **{"class": "interim_cash_flow_not_comparable_for_subtraction"}, severity="low",
             evidence="Q1 2026 payment for acquisition of subsidiary 309,878,023 versus H1 2026 309,875,862; line items differ, so Q2 by subtraction is not validated."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "2022 to 2024 interims and Q1/9M 2025 financial statements", "H1 2025 cost of revenue and missing lines",
                  "annual reports (not in collection)"],
    conclusion=("NOT claimed complete. Seven filings value-verified from pages (four with image-only statements); no restatement found; 11 further files are not value-read; "
                "nothing before FY2021."),
)
mkrecord.build(spec)
