"""Builds raw-B018/1322.json from the page transcripts."""
import mkrecord

U = "Saudi riyals (SAR), full units as printed (not thousands)"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


V = "visual (rendered image read)"
documents = [
    doc("65d75123", "3M and 6M ended 2026-06-30 interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, V + " plus text layer",
        "byte-different duplicate 9b555f86 (issuer-site copy versus Saudi Exchange copy): text of all 26 pages is identical; 2025 comparative cash flow prints operating 112,313,176 versus 112,313,177 in the H1 2025 original and its column sum is off by 1"),
    doc("1bc66fa2", "3M ended 2026-03-31 interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, V),
    doc("6646c89e", "FY ended 2025-12-31 audited FS (label 2026|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 10}, {"bs": 5, "is": 6, "cf": 8}, "text layer (clean; identities pass)"),
    doc("2a555f18", "3M and 9M ended 2025-09-30 interim (label 2025|9M correct)", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, V + " (pdf p4-7 no text layer)",
        "2024 comparatives marked restated (Note 18); dividends payable 110,700,703 on the balance sheet"),
    doc("27bb4851", "3M and 6M ended 2025-06-30 interim (label 2025|H1 correct)", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 2, "is": 3, "cf": 5}, V, "2024 comparatives marked restated (Note 18)"),
    doc("8070bf28", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year); 2023 comparative restated (Note 35)", False, {"bs": 7, "is": 8, "cf": 10}, {"bs": 5, "is": 6, "cf": 8}, V + " (pdf p3, 5-10 no text layer)",
        "first filing with severance fees as a separate line; FY2023 profit before zakat and income tax restated 68,001,062 versus 60,456,930 as issued"),
    doc("3ca65fbb", "FY ended 2023-12-31 audited FS as issued (label 2024|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 10}, {"bs": 5, "is": 6, "cf": 8}, V + " (pdf p3, 5-10 no text layer)",
        "severance fees inside direct costs as issued; restated in the FY2024 filing; both values declared"),
    doc("36790b12", "FY ended 2022-12-31 audited FS as issued (label 2023|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 10}, {"bs": 5, "is": 6, "cf": 8}, V + " (pdf p6-10 no text layer)",
        "also carries FY2021 comparatives (revenue 586,653,318, net profit 197,264,769)"),
]
cv = "(cover/title or first-page text only)"
identified = {
    "9b555f86": ("3M and 6M ended 2026-06-30 interim, duplicate of 65d75123", "text of all 26 pages identical to 65d75123 (programmatic comparison); different bytes and source URL (Saudi Exchange copy versus issuer site)"),
    "1c884e92": ("3M ended 2025-03-31 interim " + cv, "inventory class other_no_statements_found; not value-read; Q1 2025 comparatives read in 1bc66fa2"),
    "d00f138e": ("3M and 6M ended 2024-06-30 interim " + cv, "inventory class other_no_statements_found; not value-read; H1 2024 restated comparatives seen in 27bb4851"),
    "bb1f5bbf": ("3M ended 2024-03-31 interim " + cv, "not value-read"),
    "944a6c75": ("3M and 9M ended 2024-09-30 interim " + cv, "not value-read; restated 9M 2024 comparatives seen in 2a555f18"),
    "5142393c": ("3M ended 2023-03-31 interim " + cv, "not value-read"),
    "9c4a7cab": ("3M and 6M ended 2023-06-30 interim " + cv, "not value-read"),
    "fa1ec55e": ("3M and 9M ended 2023-09-30 interim " + cv, "not value-read"),
    "d92b95dc": ("3M ended 2022-03-31 interim " + cv, "not value-read"),
    "118422c9": ("3M and 6M ended 2022-06-30 interim " + cv, "inventory class other_no_statements_found; not value-read"),
    "b0f1cf1f": ("3M and 9M ended 2022-09-30 interim " + cv, "not value-read"),
    "b6218a12": ("Annual report (80 pages, English; year not verified; inventory label 2023|FY)", "contents page only read; inventory class financial_statements from summary tables; audited statements are in 36790b12 and 3ca65fbb"),
    "9e5fc45a": ("2024 annual report (123 pages, English)", "cover only; not read"),
    "dd7a773d": ("Financial and production summary year-to-date Q2 2026 (8 pages)", "first page only; not a statements file"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_8_filings_declared_restatements_and_printed_roundings_noted",
        "summary": "Headline balance sheet, income and cash-flow values (full SAR as printed) read from rendered pages (FY2022, FY2023, FY2024, Q1, H1 and 9M 2025, Q1 and H1 2026) and the clean text layer (FY2025). All identities pass exactly: assets = liabilities + equity, revenue + direct costs = gross profit, profit before zakat, income tax and severance fees less zakat, income tax and severance fees = net profit, cash-flow sum and cash roll, with printed one-riyal differences declared (H1 2026 comparative cash flow). FY2025: revenue 1,026,083,423, net profit 280,597,983 (EPS 3.17), total assets 1,548,195,235, equity 1,325,631,464, CFO 469,947,428, closing cash 14,547,517. FY2024 net profit 177,898,746; FY2023 54,582,956; FY2022 126,331,146. H1 2026 net profit 94,761,836 (Q2 34,657,788; Q1 60,104,048). Rolls pass: Q1 + Q2 = H1 2026 exactly; 2025 comparative Q1 + Q2 = H1 within 1-2 riyal printed rounding; H1 + Q3 = 9M 2025 exactly. Declared, never substituted: severance fees moved from direct costs to a separate line (FY2023 as issued versus restated in the FY2024 filing; 2024 interim comparatives restated in the 2025 interim filings, Note 18); H1 2026 comparative cash-flow one-riyal differences.",
        "not_read": ["notes in every file (including Notes 18 and 35 restatement tables)", "statements of changes in equity", "audit reports and review reports", "Q2 and Q3 cash flow by subtraction not validated", "eleven older interim files 2022 to 2025 Q1 not value-read", "annual reports 2023 and 2024"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_eight_files_five_have_image_only_statement_pages_inventory_flags_unreliable",
        "summary": "FY2022, FY2023, FY2024 annual files and the 9M 2025 interim have image-only statement pages (empty text layer on pdf p3-10 or p4-7) although the inventory counts statements in them from note pages; the H1 2025 file has partial text. The inventory classes the Q1 2025, H1 2024 and H1 2022 interim files as no statements found and most other 2022-2025 interims as partial_statements; the covers of those files were seen but their statements were not opened, so completeness of those files is unverified. 65d75123 and 9b555f86 are the same document from two sources.",
        "defect_ids": ["B018-1322-1", "B018-1322-2", "B018-1322-3", "B018-1322-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_Q1_to_2026_H1_present_by_page_derived_period_pre_2022_absent",
        "present_in_files_by_page_derived_period": ["FY2022", "FY2023", "FY2024", "FY2025", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022", "FY2023", "FY2024", "FY2025", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "FY2023 restated (FY2024 filing)", "2025 Q1 (2026 Q1 filing) and Q2 (2026 H1 filing)", "2024 H1 and 9M restated (2025 filings)"],
        "values_not_read": ["2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M originals", "2025 Q1 original"],
        "missing": ["FY2021 and earlier own filings (oldest file is the 2022 Q1 interim)", "2026 9M (not yet due)"],
        "inventory_corrections": "Annual labels equal the publication year (FY2022 labelled 2023|FY, FY2023 labelled 2024|FY, FY2024 labelled 2025|FY, FY2025 labelled 2026|FY); interim labels match page periods; the inventory's 2023|FY second file b6218a12 is an annual report, not a separate period. Two H1 2026 files are one document.",
    },
}
defects = [
    {"id": "B018-1322-1", "class": "image_only_or_scanned_statements_flagged_as_present_or_partial", "severity": "medium",
     "evidence": "36790b12 pdf p6-10, 3ca65fbb p3 and 5-10, 8070bf28 p3 and 5-10, 2a555f18 p4-7 are image-only; 1c884e92, 118422c9, d00f138e are classed other_no_statements_found and nine interims partial_statements; those files were not opened for statements, so the class is unverified rather than wrong."},
    {"id": "B018-1322-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "36790b12 FY2022 labelled 2023|FY, 3ca65fbb FY2023 labelled 2024|FY, 8070bf28 FY2024 labelled 2025|FY, 6646c89e FY2025 labelled 2026|FY; the annual report b6218a12 also labelled 2023|FY."},
    {"id": "B018-1322-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "FY2023: direct costs 371,999,011 and profit before zakat and income tax 60,456,930 as issued (3ca65fbb pdf p8) versus 364,454,879 and 68,001,062 with a separate severance fees line 7,544,132 restated (8070bf28 pdf p8); net profit 54,582,956 unchanged. 2024 H1 and 9M comparatives marked restated in 27bb4851 pdf p5 and 2a555f18 pdf p5. All recorded with both values."},
    {"id": "B018-1322-4", "class": "duplicate_files_and_printed_roundings", "severity": "low",
     "evidence": "65d75123 and 9b555f86 hold identical text on all 26 pages; one-riyal differences: H1 2025 original CFO 112,313,177 (27bb4851 pdf p7) versus 112,313,176 comparative (65d75123 pdf p7); Q1 2025 + Q2 2025 net profit 128,287,272 versus six-month 128,287,270."},
]
unread = ["notes in every file (including Notes 18 and 35)", "statements of changes in equity", "audit and review reports", "eleven interim files 2022 Q1 to 2025 Q1 and 2024 H1/9M (covers only)", "annual reports b6218a12 and 9e5fc45a",
          "FY2021 and earlier (no file)", "Arabic originals (none in collection)", "Q2 / Q3 cash flow by subtraction not validated"]
conclusion = ("NOT claimed complete. Eight filings value-verified (FY2022-FY2025; Q1, H1, 9M 2025; Q1, H1 2026) from rendered image pages and text; the severance-fee restatement is declared with both values; "
              "eleven older interims identified but not value-read; notes, audit reports and equity statements unread; no pre-2022 own filings.")
mkrecord.build(dict(
    symbol="1322", name="AL MASANE AL KOBRA MINING COMPANY (AMAK)", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statements read from rendered images (and clean text where available). The two H1 2026 files were compared page by page by text layer. "
            "tools/check_transcripts.py over transcripts/1322.json checks balance-sheet identity, revenue + direct costs = gross profit, profit before tax less zakat, income tax and severance fees = net profit, cash-flow sum and roll, "
            "cross-filing comparatives (declared differences only) and Q1 + Q2 = H1 (2026; 2025 comparatives within a written 2-riyal tolerance) and H1 + Q3 = 9M (2025) rolls; all pass.")))
