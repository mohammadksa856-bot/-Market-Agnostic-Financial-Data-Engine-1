"""Builds raw-B018/1323.json from the page transcripts."""
import mkrecord

U = "Saudi riyals (SAR), full units as printed (not thousands)"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


T = "text layer (clean; identities pass)"
V = "visual (statement pages have no text layer)"
documents = [
    doc("f667bd74", "3M and 6M ended 2026-06-30 interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6}, T,
        "income columns: 3M 2026, 3M 2025, 6M 2026, 6M 2025; cash flow six-month only"),
    doc("426d2249", "3M ended 2026-03-31 interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6}, T),
    doc("4aa36e27", "FY ended 2025-12-31 audited consolidated FS (label 2026|FY = publication year; inventory class other_no_statements_found)", False, {"bs": 7, "is": 8, "cf": 10}, {"bs": 6, "is": 7, "cf": 9}, V,
        "pdf p7-10 (balance sheet, income statement, changes in equity, cash flow) are image-only while the notes (p11+) and audit report (p3-6) have a text layer; this is why the text scan found no statements"),
    doc("b2faa977", "3M and 9M ended 2025-09-30 interim (label 2025|9M correct)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 3, "is": 4, "cf": "6-7"}, V,
        "2024 comparatives marked restated (Note 19: bargain purchase gain 11,240,415 on the 2024 acquisition now in 9M 2024); cash flow continues on a second page"),
    doc("a1b78367", "3M and 6M ended 2025-06-30 interim (label 2025|H1 correct)", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6}, V,
        "assets held for sale 4,119,783 shown on the balance sheet at 30 June 2025"),
    doc("dd8d8c5b", "3M ended 2025-03-31 interim (label 2025|Q1 correct; entity still printed as a closed joint stock company)", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6}, V,
        "Q1 2025 cash flow shows fair value loss on financial assets as an operating adjustment (693,824) that the Q1 2026 comparative moves into trade receivables; operating cash flow identical (41,554,927)"),
    doc("53e7dfe1", "FY ended 2024-12-31 audited consolidated FS (label 2025|FY = publication year; three annual files share the 2025|FY label)", False, {"bs": 5, "is": 6, "cf": 8}, {"bs": 4, "is": 5, "cf": 7}, T),
    doc("eb5b3333", "FY ended 2023-12-31 audited consolidated FS with 2022 restated (label 2025|FY = publication year)", False, {"bs": 5, "is": 6, "cf": 8}, {"bs": 4, "is": 5, "cf": 7}, T,
        "2022 comparative restated (Note 31, pdf p50-53); EPS 2023 printed 7.83 here versus 3.92 in the FY2024 filing (share count doubled by the 2024 capitalisation issue)"),
    doc("3ad94137", "FY ended 2022-12-31 audited consolidated FS as issued (label 2025|FY = publication year; three annual files share the 2025|FY label)", False, {"bs": 5, "is": 6, "cf": 8}, {"bs": 4, "is": 5, "cf": 7}, T,
        "restated in the FY2023 filing: net profit 60,337,342 as issued versus 69,518,440 restated; total assets 881,475,624 versus 891,697,133; equity 418,170,597 versus 427,351,695; both declared, neither substituted"),
]
identified = {}
dimensions = {
    "value_correctness": {
        "status": "verified_for_all_9_files_in_the_collection_declared_restatement_noted",
        "summary": "Headline balance sheet, income and cash-flow values (full SAR as printed) read from clean text layers (FY2022, FY2023, FY2024, Q1 2026, H1 2026) or rendered image pages (FY2025, Q1/H1/9M 2025). All identities pass exactly: assets = liabilities + equity, revenue + cost = gross profit, profit before zakat and tax + zakat + income tax = net profit, CFO + CFI + CFF = net change, opening cash + net change (+ FX or acquired cash) = closing cash (one 3-riyal printed mismatch on acquired cash in the FY2022 as-issued cash flow is declared). FY2025: revenue 1,406,376,399, net profit 79,124,665 (EPS 1.98), total assets 1,077,838,734, equity 588,315,061, CFO 168,994,333, closing cash 85,159,556. FY2024 net profit 124,696,211; FY2023 156,697,764; FY2022 as issued 60,337,342 (restated 69,518,440). H1 2026 net profit 52,937,355 (Q2 28,784,590, Q1 24,152,765). Q1 + Q2 = H1 (2026 and 2025) and H1 + Q3 = 9M (2025) pass for revenue, profit before tax, zakat plus income tax and net profit. Every comparative column equals the earlier filing except the declared FY2022 restatement (Note 31) and the 2024 interim columns marked restated.",
        "not_read": ["notes in every file (other than the Note 31 restatement table pdf p53 and the audit-report date)", "statements of changes in equity and comprehensive-income pages beyond the printed lines", "audit reports (opinions, emphasis paragraphs, going-concern)", "Q2 cash flow by subtraction not validated", "legal-form change (closed to listed joint stock company) not traced to its date"],
    },
    "document_completeness": {
        "status": "all_nine_files_carry_the_primary_statements_but_FY2025_and_three_2025_interims_have_image_only_statement_pages",
        "summary": "FY2022, FY2023, FY2024, Q1 2026 and H1 2026 have clean text layers with all primary statements. FY2025 (4aa36e27) and Q1, H1, 9M 2025 have image-only statement pages with a text layer on the notes and report only; the inventory nevertheless records the FY2025 file as other_no_statements_found and the three 2025 interims as financial_statements/partial although all contain full balance sheet, income and cash flow (the 2025 Q1 and H1 files record only balance sheet and income by text scan). Three annual files (FY2022, FY2023, FY2024) carry the same collector label 2025|FY.",
        "defect_ids": ["B018-1323-1", "B018-1323-2", "B018-1323-3"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2025_Q1_to_2026_H1_present_by_page_derived_period_no_2022_to_2024_interims_no_pre_2022",
        "present_in_files_by_page_derived_period": ["FY2022", "FY2023", "FY2024", "FY2025", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued)", "FY2023", "FY2024", "FY2025", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (from the FY2022 filing)", "FY2022 restated (FY2023 filing)", "2024 Q1, H1, 9M (comparatives in the 2025 interims; 9M 2024 restated)", "Dec 2022 restated balance sheet (FY2023 filing)"],
        "values_not_read": [],
        "missing": ["all 2022, 2023 and 2024 interim filings (no files; consistent with the company having been unlisted before 2025, listing date not verified from the files)", "FY2021 and earlier own filings", "2026 9M (not yet due)"],
        "inventory_corrections": "Collector labels: the three files labelled 2025|FY are FY2022, FY2023 and FY2024 (distinguished by page-derived period and file hash); the file labelled 2026|FY is FY2025. Interim labels match page periods.",
    },
}
defects = [
    {"id": "B018-1323-1", "class": "image_only_or_scanned_statements_flagged_as_present_or_partial", "severity": "medium",
     "evidence": "4aa36e27 pdf p7-10 image-only (class other_no_statements_found); b2faa977 p4-8, a1b78367 p4-7, dd8d8c5b p4-7 image-only (classes record only some statements)."},
    {"id": "B018-1323-2", "class": "fiscal_year_label_mismatch", "severity": "high",
     "evidence": "3ad94137 (FY2022), eb5b3333 (FY2023) and 53e7dfe1 (FY2024) all labelled 2025|FY; 4aa36e27 (FY2025) labelled 2026|FY; the inventory sees one annual period with three files for 2025 and a duplicate-label conflict."},
    {"id": "B018-1323-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "FY2022: net profit 60,337,342 (3ad94137 pdf p6) as issued versus 69,518,440 restated (eb5b3333 pdf p6; Note 31 pdf p50-53); revenue 1,414,673,208 identical, cost of revenue 1,227,283,899 versus 1,260,961,312, total assets 881,475,624 versus 891,697,133, equity 418,170,597 versus 427,351,695, CFO 13,508,394 versus 13,630,946. FY2023 EPS 7.83 as issued versus 3.92 in the FY2024 filing (bonus shares). 9M 2024 and Q3 2024 comparatives restated in the 9M 2025 filing (net profit 99,489,598)."},
]
unread = ["notes in every file (except Note 31 restatement table)", "audit reports and opinions (going-concern not checked)", "statements of changes in equity", "Q2 / Q3 cash flow by subtraction not validated",
          "FY2021 and earlier (no file)", "2022 to 2024 interim filings (none in the collection)", "Arabic originals (none in collection)", "segment-note totals versus the primary statements"]
conclusion = ("NOT claimed complete. All nine collected filings value-verified from text layers or rendered image pages; the FY2022 restatement (Note 31) and the 2024 interim restatement are declared with both values; "
              "company coverage is FY2022-FY2025 and 2025 Q1 to 2026 H1 only (no 2022-2024 interims, no pre-2022 own filings); notes, audit reports and equity statements unread.")
mkrecord.build(dict(
    symbol="1323", name="UNITED CARTON INDUSTRIES COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statement pages read from text layers where clean and from rendered images otherwise (FY2025 and the 2025 interims). "
            "tools/check_transcripts.py over transcripts/1323.json checks balance-sheet identity, revenue + cost = gross profit, profit before tax + zakat + income tax = net profit, cash-flow sum and roll, "
            "cross-filing comparatives (declared differences only) and Q1 + Q2 = H1 and H1 + Q3 = 9M rolls; all pass.")))
