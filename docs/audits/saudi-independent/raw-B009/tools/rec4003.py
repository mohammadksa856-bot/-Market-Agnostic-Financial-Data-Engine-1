import mkrecord

U = "SAR thousand"
V = "visual (statement pages image-only or garbled text layer, rendered and read)"


def D(sha, period, ok, bs, is_, cf, pbs, pis, pcf, reading=V):
    return {"sha256": sha, "actual_period": period, "label_ok": ok, "pdf_pages": {"bs": bs, "is": is_, "cf": cf},
            "printed_pages": {"bs": pbs, "is": pis, "cf": pcf}, "units": U, "reading": reading}


spec = {
    "symbol": "4003",
    "name": "EXTRA (United Electronics Company)",
    "method": ("SHA-256 recomputed for every audited file (tools/mkrecord.py). Statement pages of FY2025, FY2024 (garbled OCR text layer), FY2022 and FY2021 "
               "(whole-file scans) and of H1 2025 and H1 2026 (textless pdf p4-10) were rendered and read by eye. tools/check_transcripts.py over "
               "transcripts/4003.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat and tax to net profit, NI split between owners and "
               "non-controlling interests, and cross-filing agreement of comparatives with explicit restated flags; all pass."),
    "documents": [
        D("99fc4459", "FY ended 2025-12-31 audited (file classed annual_report_with_statements; it contains the full FS and label 2025|FY is correct)", True, 9, 8, 12, 8, 7, 11),
        D("1e5b9192", "FY ended 2024-12-31 audited, as filed", True, 9, 8, 12, 8, 7, 11),
        D("7a0da397", "FY ended 2022-12-31 audited, as filed (whole-file scan)", True, 9, 8, 12, 8, 7, 11),
        D("574c22dc", "FY ended 2021-12-31 audited, as originally filed (whole-file scan)", True, 9, 8, 12, 8, 7, 11),
        D("80c111ff", "3M and 6M ended 2025-06-30 reviewed", True, 6, 4, 9, 5, 3, 8),
        D("c9b0e8d1", "3M and 6M ended 2026-06-30 reviewed", True, 6, 4, 9, 5, 3, 8),
    ],
    "identified": {
        "8b063e2d": ("FY ended 2018-12-31 (cover read)", "whole-file scan, 49 pages textless; not transcribed"),
        "40ec2b52": ("FY ended 2019-12-31 (cover text)", "born-digital FS present (statement pages 7, 10-14 per inventory); not transcribed"),
        "f10d557b": ("FY ended 2020-12-31 (cover text)", "statement pages p3-12 textless (images); not transcribed; FY2020 IS, CF and BS totals known from the FY2021 comparatives"),
        "c14f646f": ("3M and 9M ended 2022-09-30 (cover read)", "whole-file scan, 22 pages textless; not transcribed"),
        "e07fe370": ("3M and 6M ended 2022-06-30 (cover read)", "whole-file scan, 22 pages textless; not transcribed"),
        "bd68c42b": ("3M ended 2022-03-31 (cover text)", "statements textless pdf p4-9; not transcribed"),
        "d771e723": ("3M and 9M ended 2023-09-30 (cover read)", "whole-file scan, 38 pages; not transcribed"),
        "89a0c42f": ("Annual report 2023 (cover text)", "classed partial_statements: highlights tables only (total assets on p6, p20), no full financial statements; the standalone FY2023 FS file is absent from the collection"),
        "996ec4b6": ("3M and 6M ended 2023-06-30 (cover text)", "statements textless pdf p4-9; not transcribed"),
        "7167dd62": ("3M ended 2023-03-31 (cover read)", "scan, 34 pages (only p8 has text); not transcribed"),
        "d40279b2": ("3M ended 2024-03-31 (cover text)", "statements textless pdf p4-9; not transcribed"),
        "4e5b7092": ("3M and 6M ended 2024-06-30 (cover text)", "statements textless pdf p4-9; not transcribed; 6M 2024 IS and CF known from the H1 2025 comparatives"),
        "71d1531b": ("3M and 9M ended 2024-09-30 (cover text)", "born-digital pages (no textless pages); not transcribed"),
        "289ea4dc": ("3M ended 2025-03-31 (cover text)", "statements textless pdf p4-9; not transcribed"),
        "ffef72ec": ("3M and 9M ended 2025-09-30 (cover text)", "statements textless pdf p4-10; not transcribed"),
        "801be1b4": ("3M ended 2026-03-31 (cover text)", "statements textless pdf p4-9; not transcribed"),
    },
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_6_filings_with_restated_eps_and_cash_definition_notes",
            "summary": ("Headline BS, income and cash-flow values (SAR thousand) transcribed from pages for FY2021 (as originally filed), FY2022, FY2024, FY2025, H1 2025 and "
                        "H1 2026 with comparative columns and Q2 columns. Identities hold with zero difference: total assets = liabilities + equity (FY2021 total liabilities not read); "
                        "CFO+CFI+CFF = net change; opening + net change = closing cash; revenue - cost = gross profit; profit before zakat and tax less zakat and income tax = net profit; "
                        "owners + non-controlling interests = net profit. Selected: FY2025 revenue 7,446,115, net profit 575,989 (owners 497,002), total assets 5,924,092, CFO 92,230; "
                        "H1 2026 revenue 4,069,063, net profit 231,331, total assets 6,320,326, CFO 21,712. FY2022 CFO is negative (-68,259). The FY2021 income statement and balance sheet "
                        "agree between the FY2021 and FY2022 filings except earnings per share, which the FY2022 filing marks Restated - Note 32 (basic 6.90 -> 5.37, diluted 6.61 -> 4.96); "
                        "H1 2025 EPS differs between the H1 2025 filing (2.99 basic, 2.85 diluted; Q2 1.63 and 1.56) and the H1 2026 comparatives (2.52, 2.41; Q2 1.40 and 1.34) per note 12."),
            "not_read": [
                "notes in every file", "statements of changes in equity",
                "Q1 and 9M 2025, Q1 2026 filings; all 2022 to 2024 interims; FY2019 and FY2020 originals; FY2018 scan",
                "total liabilities of FY2021 and FY2020 (BS continuation page not read in the FY2021 file)",
            ],
        },
        "document_completeness": {
            "status": "primary_statements_present_in_fy2021_fy2022_fy2024_fy2025_h1_2025_h1_2026_standalone_FY2023_file_absent",
            "summary": ("Opened files carry full statements; statement pages are images for FY2025 (pdf p8-13, inside a file the inventory calls annual_report_with_statements and which actually "
                        "is the audited FS file), FY2022 and FY2021 (whole-file scans classed scanned_unreadable), H1 2025, H1 2026 and the other 2022-2026 interims (textless pdf p4-10; "
                        "inventory finds only index pages), and FY2024 has an OCR-garbled text layer that must not be parsed. No standalone FY2023 financial "
                        "statement file exists: the FY2023 slot holds the annual report (highlights only); FY2023 is known only as the comparative column of the FY2024 filing."),
            "defect_ids": ["B009-4003-1", "B009-4003-2", "B009-4003-3"],
        },
        "company_coverage": {
            "status": "annual_2018_to_2025_except_FY2023_standalone_interims_2022Q1_to_2026H1",
            "present_in_files_by_page_derived_period": [
                "2018|FY (scan)", "2019|FY", "2020|FY", "2021|FY (scan)", "2022|FY (scan)", "2023|FY (annual report, highlights only)", "2024|FY", "2025|FY",
                "2022|Q1", "2022|H1 (scan)", "2022|9M (scan)", "2023|Q1 (scan)", "2023|H1", "2023|9M (scan)", "2024|Q1", "2024|H1", "2024|9M",
                "2025|Q1", "2025|H1", "2025|9M", "2026|Q1", "2026|H1",
            ],
            "values_verified_from_own_pages": ["2021|FY", "2022|FY", "2024|FY", "2025|FY", "2025|H1", "2026|H1"],
            "values_known_only_as_comparatives": ["2020|FY (FY2021 filing)", "2023|FY (FY2024 filing)", "2024|H1 six months and Q2 (H1 2025 filing)", "2025|Q2 (H1 2025 filing, EPS re-presented in H1 2026)"],
            "values_not_read": ["2018|FY", "2019|FY", "2020|FY original", "2022|Q1", "2022|H1", "2022|9M", "2023|Q1", "2023|H1", "2023|9M", "2024|Q1", "2024|H1 original", "2024|9M", "2025|Q1", "2025|9M", "2026|Q1"],
            "missing": ["standalone FY2023 financial statements", "everything before FY2018"],
            "inventory_corrections": ("annual labels equal the fiscal year here (2024|FY is FY2024, 2025|FY is FY2025), unlike the publication-year pattern elsewhere in the batch; "
                                      "2025|FY is classed annual_report_with_statements and is the FS file. 2023|FY is an annual report, not statements."),
        },
    },
    "defects": [
        {"id": "B009-4003-1", "class": "image_only_or_scanned_statements_flagged_partial_or_unreadable", "severity": "medium",
         "evidence": "FY2025 (99fc4459) statements are textless pdf p8-13 and the file is classed annual_report_with_statements; FY2022 7a0da397 and FY2021 574c22dc are whole-file scans classed scanned_unreadable; 2022-2023 interim scans c14f646f, e07fe370, d771e723, 7167dd62; H1 2025/H1 2026 and other interims have textless pdf p4-10."},
        {"id": "B009-4003-2", "class": "garbled_ocr_text_layer", "severity": "high",
         "evidence": "FY2024 (1e5b9192) pdf p8, p10, p13 have an OCR text layer with corrupted digits (e.g. 6,156,63:3 and 3,:358,172); the rendered pages give the correct values. Text-layer parsing of this file would produce wrong numbers."},
        {"id": "B009-4003-3", "class": "missing_fiscal_year_file", "severity": "medium",
         "evidence": "No financial statements file for FY2023; 89a0c42f (annual report 2023, 56 pages) has only highlights. FY2023 values come from the FY2024 filing's comparative column, whose total assets 4,441,511 include assets held for sale 7,069."},
        {"id": "B009-4003-4", "class": "restated_or_represented_comparatives", "severity": "medium",
         "evidence": "FY2021 EPS restated in the FY2022 filing (6.90 -> 5.37 basic, 6.61 -> 4.96 diluted; income, balance sheet and CFO unchanged) and cash-from-operations sub-lines re-presented (cash generated 49,368 -> 60,585, trade payables 142,882 -> 142,618; CFO -17,041 unchanged). H1 2025 EPS re-presented in H1 2026 (2.99 -> 2.52 basic, 2.85 -> 2.41 diluted). Both versions recorded; no value substituted."},
        {"id": "B009-4003-5", "class": "cash_definition_differs", "severity": "low",
         "evidence": "Dec 2023 balance-sheet cash 151,272 versus cash-flow closing cash 152,604 in the FY2024 filing (held-for-sale cash); in FY2022, FY2024, FY2025, H1 2025 and H1 2026 the two agree. Equity includes non-controlling interests from 2024 (333,794 at Dec 2024), none before."},
    ],
    "unread_items": [
        "notes in all files", "equity statements",
        "Q1/9M 2025, Q1 2026, and all 2022-2024 interims (see files_not_audited_for_values)",
        "FY2018, FY2019, FY2020 standalone files", "total liabilities for FY2021/FY2020",
        "standalone FY2023 FS: no file",
    ],
    "conclusion": ("NOT claimed complete. Six filings value-verified from pages; FY2023 has no standalone FS file; 16 further files are not value-read "
                   "(see values_not_read); nothing before FY2018."),
}
mkrecord.build(spec)
