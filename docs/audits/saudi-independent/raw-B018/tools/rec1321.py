"""Builds raw-B018/1321.json from the page transcripts."""
import mkrecord

U = "Saudi riyals (SAR), full units as printed (not thousands); fiscal year ends 31 March"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


T = "text layer (clean; identities pass)"
V = "visual (rendered image read)"
documents = [
    doc("881ec696", "3M ended 2026-06-30 interim = fiscal Q1 of FY ending 2027-03-31 (label 2026|Q1 is a calendar-style label)", True, {"is": 4, "bs": 5, "cf": 7}, {"is": 2, "bs": 3, "cf": 5}, V + " plus text layer",
        "latest period in the collection; Q1 FY26 comparative re-presented (finance income split out of other operating income)"),
    doc("c032fedd", "FY ended 2026-03-31 audited FS (label 2026|FY; inventory class partial_statements although all three statements are present)", True, {"is": 8, "bs": 9, "cf": 11}, {"is": 6, "bs": 7, "cf": 9}, T,
        "31 March 2025 comparative balance sheet re-presented (total assets 1,638,543,651 versus 1,632,108,105 as audited); statement of changes in equity pdf p10 seen in text, not transcribed; auditor report p7 image page not read"),
    doc("6366e4d4", "3M and 9M ended 2025-12-31 interim = fiscal Q3 of FY ending 2026-03-31 (label 2025|9M)", True, {"is": 4, "bs": 5, "cf": 7}, {"is": 2, "bs": 3, "cf": 5}, V + " (text layer garbled)",
        "net change in cash printed 388,542,754 against a column sum of 388,542,756 (2 riyal source rounding, verified on zoomed render)"),
    doc("8a30cf4b", "3M and 6M ended 2025-09-30 interim = fiscal Q2 of FY ending 2026-03-31 (label 2025|H1)", True, {"is": 4, "bs": 5, "cf": 7}, {"is": 2, "bs": 3, "cf": 5}, V),
    doc("a97bb7a6", "3M ended 2025-06-30 interim = fiscal Q1 of FY ending 2026-03-31 (label 2025|Q1; inventory partial_statements)", True, {"is": 4, "bs": 5, "cf": 7}, {"is": 2, "bs": 3, "cf": 5}, V + " (pdf p3-7 have no text layer)"),
    doc("285c64ee", "FY ended 2025-03-31 audited FS (label 2025|FY)", True, {"is": 8, "bs": 9, "cf": "11-12"}, {"is": 6, "bs": 7, "cf": "9-10"}, T),
    doc("038edf7d", "FY ended 2024-03-31 audited FS (label 2024|FY)", True, {"is": 7, "bs": 8, "cf": 10}, {"is": 5, "bs": 6, "cf": 8}, T,
        "auditor report pdf p3-6 image-only (not read); inventory flags no cash flow statement though it is on pdf p10"),
    doc("8f5b16dd", "FY ended 2023-03-31 audited FS, whole-file scan (label 2023|FY; inventory class scanned_unreadable)", True, {"is": 7, "bs": 8, "cf": 10}, {"is": 5, "bs": 6, "cf": 8}, V + " (no text layer on any page)",
        "also carries the FY ended 2022-03-31 comparatives (revenue 597,465,405, net loss -3,245,320); the standalone FY2022 financial statements are not in the collection"),
]
cv = "(cover/title or first-page text only)"
identified = {
    "d2121e91": ("3M ended 2023-06-30 interim = fiscal Q1 of FY2024 " + cv, "not value-read; text layer present except pdf p3"),
    "519dabc9": ("3M and 6M ended 2023-09-30 interim = fiscal Q2 of FY2024 " + cv, "not value-read"),
    "b5fbd5f1": ("3M and 9M ended 2023-12-31 interim = fiscal Q3 of FY2024 " + cv, "not value-read"),
    "71f87d3a": ("3M ended 2024-06-30 interim = fiscal Q1 of FY2025 " + cv, "not value-read; Q1 FY25 comparatives read in a97bb7a6"),
    "6a104890": ("3M and 6M ended 2024-09-30 interim = fiscal Q2 of FY2025 " + cv, "not value-read; H1 FY25 comparatives read in 8a30cf4b"),
    "42f3f9dd": ("3M and 9M ended 2024-12-31 interim = fiscal Q3 of FY2025 " + cv, "not value-read; 9M FY25 comparatives read in 6366e4d4"),
    "7298b0d6": ("3M ended 2022-06-30 interim = fiscal Q1 of FY2023 " + cv, "inventory class other_no_statements_found; not value-read"),
    "f9cc430d": ("3M and 6M ended 2022-09-30 interim = fiscal Q2 of FY2023 (cover viewed)", "inventory class other_no_statements_found; not value-read"),
    "64865887": ("3M and 9M ended 2022-12-31 interim = fiscal Q3 of FY2023 (cover viewed)", "whole-file scan (20 pages, no text); not value-read"),
    "b02410d6": ("3M and 9M ended 2025-12-31 interim, Arabic (cover viewed)", "Arabic twin of 6366e4d4; not value-read"),
    "83a50e6b": ("Annual report 2021-2022 (FY ended 2022-03-31), English, 61 pages", "p53 five-year financial summary in SAR thousands read from text (FY2022 sales 597,465, net income -3,245) only; no audited statements in the file; summary cost of sales 562,965 differs in presentation from the audited comparative 569,720,077"),
    "b479f1fe": ("Annual report 2021-2022, Arabic twin of 83a50e6b", "not read"),
    "84724b08": ("Annual report FY2023 (year ended 2023-03-31), English, 50 pages (inventory class financial_statements)", "pdf p41-42 read: five-year summary tables (garbled text), not audited statements; other pages unread; the audited FY2023 statements are in 8f5b16dd"),
    "592bf05e": ("Annual report FY2024 (1444-1445 H), Arabic, 69 pages", "not read"),
    "fb7fd69f": ("Annual report FY2024 (1444-1445 H), English, 69 pages", "not read"),
    "8063ef32": ("Annual report FY2025, Arabic, 71 pages", "not read"),
    "d8006bc1": ("Results announcement FY2022 (year ended 2022-03-31), 4 pages", "not read; announcement, not statements"),
    "4efe52a0": ("Results announcement Q1 FY2023, 4 pages", "not read; announcement"),
    "aa7fc2a7": ("Results announcement Q2 FY2023, 4 pages", "not read; announcement"),
    "0877f27e": ("Results announcement FY2025, 5 pages", "not read; announcement"),
    "00fe9261": ("Results announcement Q1 FY2026, 3 pages", "not read; announcement"),
    "12893dfe": ("Results announcement Q2 FY2026, 3 pages", "not read; announcement"),
    "053cf144": ("Results announcement 9M FY2026, 3 pages", "not read; announcement"),
    "dc6242ae": ("Results announcement FY2026, 3 pages", "not read; announcement"),
    "d608129f": ("Results announcement Q1 FY2027, 3 pages", "not read; announcement"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_8_filings_declared_representations_noted",
        "summary": "Headline balance sheet, income and cash-flow values (full SAR as printed) read from clean text layers (FY2024, FY2025, FY2026) and rendered images (FY2023 scan, Q1 FY26 to Q1 FY27). All identities pass exactly: assets = liabilities + equity, revenue + cost = gross profit, profit before zakat and tax + zakat + income tax = net profit, cash-flow sum and cash roll (one 2-riyal printed rounding in the 9M FY26 cash flow declared). FY2026 (year to 31 Mar 2026): revenue 2,297,739,980, net profit 573,262,283 (EPS 18.20), total assets 1,969,890,077, equity 1,563,827,299, CFO 973,110,362, closing cash 680,946,579. FY2025 net profit 382,123,608; FY2024 267,507,881; FY2023 99,920,835; FY2022 (comparative) net loss -3,245,320. Q1 FY27 net profit 122,917,040. Rolls pass: Q1 + Q2 = H1 and H1 + Q3 = 9M for revenue, profit before tax, zakat plus income tax and net profit in FY26 and for the FY25 comparatives. Cross-filing comparatives agree except two declared re-presentations: the 31 March 2025 balance sheet (total assets 1,638,543,651 in the FY2026 filing versus 1,632,108,105 audited) and Q1 FY26 operating profit (98,651,233 re-presented versus 104,581,273 first reported; finance income split out). Fiscal year ends 31 March, so annual and interim labels are shifted against calendar years.",
        "not_read": ["notes in every file", "statements of changes in equity (seen as text in FY2024 and FY2026, not transcribed)", "audit reports (pdf p3-6 of FY2024 and FY2023, p7 of FY2026 are image pages)", "Q2 and Q3 cash flow by subtraction not validated", "nine older interim files FY23-FY25 not value-read", "Arabic twins and annual reports"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_eight_files_one_whole_file_scan_and_several_image_only_statement_pages",
        "summary": "FY2023 file (8f5b16dd) is a whole-file scan holding full audited statements although the inventory classes it scanned_unreadable. The Q1 FY26 file has image-only statement pages; the 9M and H1 FY26 files have partial text layers. Inventory classes FY2026 as partial_statements and FY2024 as lacking cash flows though both contain all three statements. The standalone audited statements for FY ended 31 March 2022 are absent: FY2022 appears only as the comparative column in the FY2023 filing and in the annual report five-year table. The annual-report files read (84724b08 p41-42, 83a50e6b p53) show only summary tables; their other pages are unread.",
        "defect_ids": ["B018-1321-1", "B018-1321-2", "B018-1321-3"],
    },
    "company_coverage": {
        "status": "annual_FY2023_to_FY2026_and_all_interim_quarters_FY2023_to_Q1_FY2027_present_by_page_derived_period_FY2022_only_as_comparative",
        "present_in_files_by_page_derived_period": ["FY2023 (year to 2023-03-31)", "FY2024", "FY2025", "FY2026", "Q1 FY23 (2022-06-30)", "Q2 FY23 (2022-09-30)", "Q3 FY23 (2022-12-31)", "Q1 FY24", "Q2 FY24", "Q3 FY24",
                                                    "Q1 FY25", "Q2 FY25", "Q3 FY25", "Q1 FY26", "Q2 FY26", "Q3 FY26", "Q1 FY27 (2026-06-30)"],
        "values_verified_from_own_pages": ["FY2023", "FY2024", "FY2025", "FY2026", "Q1 FY26", "Q2 FY26", "Q3 FY26", "Q1 FY27"],
        "values_known_only_as_comparatives": ["FY2022 (year to 2022-03-31) from the FY2023 filing", "Q1, Q2, Q3 FY25 (FY26 filings)", "Q1 FY26 re-presented (Q1 FY27 filing)", "31 March 2025 balance sheet re-presented (FY2026 filing)"],
        "values_not_read": ["Q1-Q3 FY23 originals", "Q1-Q3 FY24 originals", "Q1-Q3 FY25 originals"],
        "missing": ["standalone audited statements for FY ended 2022-03-31 and earlier (the file labelled 2021|FY is the 2021-2022 annual report without statements)", "FY2027 full year and Q2 FY27 (not yet due)"],
        "inventory_corrections": "Collector labels are calendar-style: a period to 30 June is labelled Q1 of the calendar year of its end date, 30 September H1, 31 December 9M, and the 31 March year end FY of the year in which it ends; the fiscal Q1 FY27 file is labelled 2026|Q1 and a results announcement for it 2027|Q1; the 9M label 2025|9M holds period ended 2025-12-31 and 2024|9M holds period ended 2024-12-31. The file labelled 2021|FY is the 2021-2022 annual report (year to 2022-03-31).",
    },
}
defects = [
    {"id": "B018-1321-1", "class": "image_only_or_scanned_statements_flagged_as_present_or_partial", "severity": "high",
     "evidence": "8f5b16dd 46-page scan (no text on any page) holds balance sheet pdf p8, income pdf p7 and cash flow pdf p10, classed scanned_unreadable; a97bb7a6 pdf p3-7 image-only; 64865887 20-page scan not opened; c032fedd classed partial_statements and 038edf7d flagged missing cash flows although complete."},
    {"id": "B018-1321-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "March year end: interim labels are calendar-style (2025|H1 = period to 2025-09-30; 2024|9M = period to 2024-12-31; 2026|Q1 = period to 2026-06-30 while its announcement is labelled 2027|Q1); the 2021|FY file is the annual report for the year to 2022-03-31 and the 2025|9M file pair (6366e4d4 English, b02410d6 Arabic) both cover period to 2025-12-31."},
    {"id": "B018-1321-3", "class": "restated_or_represented_comparatives", "severity": "medium",
     "evidence": "31 March 2025 balance sheet: total assets 1,632,108,105 (285c64ee pdf p9) versus 1,638,543,651 (c032fedd pdf p9); Q1 FY26 operating profit 104,581,273 (a97bb7a6 pdf p4) versus 98,651,233 (881ec696 pdf p4). Both recorded; none substituted. FY2022 cost of revenue 569,720,077 in the audited comparative versus 562,965 thousand in the annual report summary (different grouping, depreciation shown separately)."},
]
unread = ["notes in every file", "statements of changes in equity", "audit reports and opinions (image pages)", "nine interim files FY2023 to FY2025 (covers/first-page text only)", "Arabic twins (b479f1fe, 592bf05e, 8063ef32, b02410d6)",
          "annual reports 83a50e6b, 84724b08, fb7fd69f beyond summary tables", "results announcements (9 files)", "standalone FY2022 statements (absent)", "Q2 / Q3 cash flow by subtraction not validated"]
conclusion = ("NOT claimed complete. Eight filings value-verified (FY2023-FY2026 audited; Q1-Q3 FY26; Q1 FY27); two re-presentations declared with both values; "
              "nine older interim files identified but not value-read; standalone FY2022 audited statements absent (comparative only); notes, audit reports and equity statements unread.")
mkrecord.build(dict(
    symbol="1321", name="EAST PIPES INTEGRATED COMPANY FOR INDUSTRY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statements read from text layers where clean and from rendered images for the FY2023 scan and the FY26 and FY27 interims. "
            "tools/check_transcripts.py over transcripts/1321.json checks balance-sheet identity, revenue + cost = gross profit, profit before tax + zakat + income tax = net profit, cash-flow sum and roll, "
            "cross-filing comparatives (declared differences only) and Q1 + Q2 = H1, H1 + Q3 = 9M rolls for FY26 and FY25 comparatives; all pass.")))
