"""Builds raw-B018/1324.json from the page transcripts."""
import mkrecord

U = "Saudi riyals (SAR), full units as printed (not thousands)"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


T = "text layer (clean; identities pass)"
documents = [
    doc("35231b87", "3M and 6M ended 2026-06-30 interim (collector label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, "visual (whole file is a scan; OCR text layer garbled)",
        "inventory flags missing cash flow, but the cash flow is on pdf p7-8; income columns 3M 2026, 3M 2025, 6M 2026, 6M 2025"),
    doc("2e8fae42", "3M ended 2026-03-31 interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, "visual (scan; OCR text layer garbled)"),
    doc("b8514899", "FY ended 2025-12-31 audited consolidated FS, signed copy with Signit audit-trail page 47 (label 2026|FY = publication year; also labelled 2025|FY by the inventory because of twin 866e75f2)", False, {"bs": 7, "is": 8, "cf": "10-11"}, {"bs": 5, "is": 6, "cf": "8-9"}, T,
        "pdf p6 has no text (auditor-report continuation image page, not opened). Twin 866e75f2 (46 pages): every printed number of five or more digits (937) is identical in sequence; the only difference is the audit-trail page. Net profit includes non-controlling interests (loss -91,807)."),
    doc("730be357", "FY ended 2024-12-31 audited consolidated FS (label 2026|FY = publication year)", False, {"bs": 6, "is": 7, "cf": 9}, {"bs": 4, "is": 5, "cf": 7}, T,
        "FY2024 comparative is re-presented in the FY2025 filing: operating cash flow 87,856,238 versus 86,122,981, investing -70,241,592 versus -68,528,335, financing -3,250,424 versus -3,230,424; net change and closing cash identical; current assets re-classified (prepayments 23,239,889 versus 22,989,889)"),
    doc("6d210026", "FY ended 2023-12-31 audited consolidated FS as issued (label 2026|FY = publication year)", False, {"bs": 5, "is": 6, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "6-7"}, T,
        "2023 comparative re-presented in the FY2024 filing (total assets 428,694,195 versus 428,590,605; operating 56,982,967 versus 56,765,462); both declared"),
    doc("3a9efe83", "FY ended 2022-12-31 special purpose financial statements of a limited liability company (label 2026|FY = publication year)", False, {"bs": 3, "is": 4, "cf": 6}, {"bs": 4, "is": 5, "cf": 7}, T,
        "special purpose basis, not the consolidated statements: differs from the 2022 comparative in the FY2023 consolidated FS (net profit 70,789,326 versus 69,987,294; total assets 341,824,434 versus 348,555,300); 2021 comparative marked restated (Note 26). PDF metadata title/author name another entity (Gulf Training and Electronic Industries / Ernst & Young), a template carry-over; page text names Saleh Abdulaziz Al Rashed and Sons."),
]
cv = "(cover text only)"
identified = {
    "f7019852": ("FY ended 2022-12-31 special purpose FS, Arabic (limited liability company) " + cv, "whole-file scan (32 pages, no text); Arabic twin of 3a9efe83, not value-read"),
    "8bdc8742": ("FY ended 2023-12-31 consolidated FS, Arabic " + cv, "Arabic twin of 6d210026; text layer in presentation-form glyphs, not value-read"),
    "ff46f18d": ("FY ended 2024-12-31 consolidated FS, Arabic " + cv, "Arabic twin of 730be357; not value-read"),
    "c6a5750f": ("FY ended 2025-12-31 consolidated FS, Arabic (Saudi joint stock company) " + cv, "Arabic twin of b8514899; not value-read"),
    "866e75f2": ("FY ended 2025-12-31 consolidated FS, English, copy without audit-trail page", "twin of b8514899: all 937 printed numbers of 5+ digits identical in sequence (programmatic text comparison); statement pages not separately transcribed"),
    "1070877b": ("Independent auditor's report on the FY2025 consolidated FS (Maham, 23 pages, English)", "auditor report only; not read beyond the first page; opinion and key audit matters not transcribed"),
    "3c475a8d": ("Annual report 2025, English (110 pages) " + cv, "not opened beyond cover; not a primary-statement source"),
    "c35690fc": ("Annual report 2025 (file named BOD report), English (110 pages) " + cv, "not opened beyond cover; likely duplicate of 3c475a8d (different hash, not compared)"),
    "b824e816": ("Annual report 2025, Arabic (107 pages) " + cv, "not opened beyond cover"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_basis_and_representation_differences_noted",
        "summary": "Headline balance sheet, income and cash-flow values (full SAR as printed) read from clean text layers (FY2025, FY2024, FY2023, FY2022 special purpose) and rendered scan pages (Q1 and H1 2026, whose OCR text is garbled). All identities pass exactly: assets = liabilities + equity, revenue + cost = gross profit, profit before zakat + zakat = net profit, parent + non-controlling = net profit, cash-flow sum and cash roll. FY2025: revenue 739,521,228, net profit 91,565,077 (to shareholders 91,656,884; NCI -91,807; EPS 4.93), total assets 630,305,544, equity 438,699,747, CFO 177,386,171, closing cash 60,344,504. FY2024 net profit 59,687,563; FY2023 47,058,246. H1 2026 net profit 13,391,651 (Q2 5,213,363, Q1 8,178,288); Q1 + Q2 = H1 for 2026 and for the 2025 comparatives (pass). Declared, never substituted: FY2024 and FY2023 cash-flow/asset re-presentations in the following year's filing; FY2022 special purpose basis versus the 2022 column of the FY2023 consolidated FS.",
        "not_read": ["notes in every file", "statements of changes in equity and comprehensive-income pages beyond printed lines", "audit reports (opinion and key audit matters)", "Q2 cash flow by subtraction not validated", "Arabic files not value-read (twins)", "annual reports 2025 not read", "pdf p6 of b8514899 (image-only page)"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_Q1_and_H1_2026_are_scans_with_garbled_OCR_inventory_flags_unreliable",
        "summary": "Six English files hold full primary statements. The Q1 and H1 2026 files are whole-file scans with a garbled OCR text layer; the inventory classes them financial_statements and flags H1 missing cash flow although the cash flow is on pdf p7-8. The FY2022 file is special purpose (limited liability company) statements, not consolidated annual accounts. Five annual-statement files in the inventory carry labels 2025|FY or 2026|FY or none (Arabic files have no period label). The Arabic twins of FY2022-FY2025 exist but were not read; the FY2022 Arabic file is a pure scan.",
        "defect_ids": ["B018-1324-1", "B018-1324-2", "B018-1324-3", "B018-1324-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_Q1_H1_2026_only_by_page_derived_period_no_FY2021_no_2022_to_2025_interims",
        "present_in_files_by_page_derived_period": ["FY2022 (special purpose)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (special purpose)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (restated, from the FY2022 special purpose FS)", "FY2022 consolidated basis (FY2023 filing)", "Q1 2025, Q2 2025, H1 2025 (2026 interim comparatives)", "FY2024 cash-flow as re-presented (FY2025 filing)"],
        "values_not_read": ["Arabic twins FY2022-FY2025", "annual report 2025"],
        "missing": ["FY2021 and earlier own filings", "2022-2025 interim filings (none in the collection)", "2026 9M (not yet due)"],
        "inventory_corrections": "Collector labels are wrong for the annual files: FY2022, FY2023, FY2024 and FY2025 English statements (3a9efe83, 6d210026, 730be357, b8514899) are all labelled 2026|FY and b8514899 also 2025|FY; their page-derived periods are 2022-12-31 to 2025-12-31. Arabic statement files carry year labels 2022 to 2025 with no slot. The inventory duplicate flag for 2026|Q1 is a label conflict between the Q1 and H1 files (35231b87 is H1 2026).",
    },
}
defects = [
    {"id": "B018-1324-1", "class": "image_only_or_scanned_statements_flagged_as_present_or_partial", "severity": "medium",
     "evidence": "35231b87 and 2e8fae42 are scans with garbled OCR (pdf p4-8); inventory flags 35231b87 as missing cash flows although pdf p7-8 hold them; f7019852 (FY2022 Arabic) is a 32-page pure scan."},
    {"id": "B018-1324-2", "class": "fiscal_year_label_mismatch", "severity": "high",
     "evidence": "3a9efe83 (FY2022), 6d210026 (FY2023), 730be357 (FY2024) and b8514899 (FY2025) all labelled 2026|FY; b8514899 and 866e75f2 labelled 2025|FY; the 2026|Q1 label is attached to both the Q1 and H1 2026 files."},
    {"id": "B018-1324-3", "class": "restated_or_represented_comparatives", "severity": "medium",
     "evidence": "FY2024 CFO 87,856,238 (730be357 pdf p9) versus 86,122,981 (b8514899 pdf p10); FY2023 total assets 428,694,195 (6d210026 pdf p5) versus 428,590,605 (730be357 pdf p6); FY2022 special purpose net profit 70,789,326 (3a9efe83 pdf p4) versus 69,987,294 (6d210026 pdf p6). All recorded with both values."},
    {"id": "B018-1324-4", "class": "entity_or_metadata_anomaly", "severity": "low",
     "evidence": "3a9efe83 PDF metadata title and author name another company (Gulf Training and Electronic Industries Co. Ltd / Ernst & Young) while the statement pages name Saleh Abdulaziz Al Rashed and Sons; legal form changes across files: limited liability company (FY2022), printed as Saudi joint stock company on the FY2023 English cover, closed joint stock on the FY2024 English cover and on the FY2023 and FY2024 Arabic covers, Saudi joint stock from FY2025. The registry name SALEH ALRASHED corresponds to Saleh Abdulaziz Al Rashed and Sons Company."},
]
unread = ["notes in every file", "audit reports and opinions (1070877b not read)", "statements of changes in equity", "Q2 cash flow by subtraction not validated", "Arabic files 8bdc8742, ff46f18d, c6a5750f, f7019852 (twins)",
          "annual reports 3c475a8d, c35690fc, b824e816 (not opened beyond cover)", "FY2021 and earlier (no file)", "2022-2025 interim filings (none in the collection)", "pdf p6 of b8514899 and 866e75f2 (image-only page)"]
conclusion = ("NOT claimed complete. Six filings value-verified (FY2022 special purpose, FY2023, FY2024, FY2025, Q1 2026, H1 2026); the re-presentations and the special-purpose basis difference are declared with both values; "
              "Arabic twins, annual reports and the audit report unread; no pre-2022 own filings and no 2022-2025 interims in the collection.")
mkrecord.build(dict(
    symbol="1324", name="SALEH ABDULAZIZ AL RASHED AND SONS COMPANY (registry: SALEH ALRASHED)", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Statements read from text layers where clean and from rendered images for the two 2026 interim scans. The FY2025 twin was compared programmatically (all printed numbers). "
            "tools/check_transcripts.py over transcripts/1324.json checks balance-sheet identity, revenue + cost = gross profit, profit before zakat + zakat = net profit, parent + non-controlling = net profit, cash-flow sum and roll, "
            "cross-filing comparatives (declared differences only) and Q1 + Q2 = H1 rolls (2026 and 2025 comparatives); all pass.")))
