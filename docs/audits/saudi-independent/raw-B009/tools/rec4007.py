import mkrecord


def D(sha, period, ok, bs, is_, cf, pbs, pis, pcf, reading, units="SAR (full riyals)"):
    return {"sha256": sha, "actual_period": period, "label_ok": ok, "pdf_pages": {"bs": bs, "is": is_, "cf": cf},
            "printed_pages": {"bs": pbs, "is": pis, "cf": pcf}, "units": units, "reading": reading}


VIS = "visual (statement pages image-only inside a text PDF, rendered and read)"
TXT = "text layer, totals and cross-filing comparatives tied by arithmetic"
spec = {
    "symbol": "4007",
    "name": "ALHAMMADI (Al Hammadi Holding Company)",
    "method": ("SHA-256 recomputed for every audited file (tools/mkrecord.py). Statement pages of the standalone annual files FY2022, FY2023, FY2025 "
               "(pdf p3-14) and of Q1 2026 (pdf p3-9) are image-only, so they were rendered and read by eye; FY2024, Q1/H1/9M 2025 and H1 2026 have "
               "a text layer for the statements, read through tools/rows.py and tied by arithmetic. The Q1 2025 income statement was also rendered "
               "because its text layer omits the shaded current-period column. tools/check_transcripts.py over transcripts/4007.json checks BS "
               "identity, cash-flow sum and roll, gross profit, profit before zakat to net profit, cross-filing agreement of comparatives with "
               "explicit restated flags, and Q1+Q2=H1 / H1+Q3=9M rolls; all pass."),
    "documents": [
        D("b97990d3", "FY ended 2025-12-31 audited (collector label 2026|FY)", False, 11, 9, 13, 10, 8, 12, VIS),
        D("507b9a1e", "FY ended 2024-12-31 audited, as originally filed (collector label 2025|FY)", False, 11, 9, 13, 10, 8, 12, TXT),
        D("964e652f", "FY ended 2023-12-31 audited, as originally filed (collector label 2024|FY)", False, 11, 9, 13, 10, 8, 12, VIS),
        D("eb3719c7", "FY ended 2022-12-31 audited, as originally filed (collector label 2023|FY)", False, 11, 9, 13, 10, 8, 12, VIS),
        D("030791ca", "3M ended 2025-03-31 reviewed", True, 6, 4, 8, 5, 3, 7, "income statement visual, BS and CF text layer tied by arithmetic"),
        D("9b85d9ca", "3M and 6M ended 2025-06-30 reviewed", True, 6, 4, 8, 5, 3, 7, TXT),
        D("f79e7223", "3M and 9M ended 2025-09-30 reviewed", True, 6, 4, 8, 5, 3, 7, TXT),
        D("cbbdf048", "3M ended 2026-03-31 reviewed", True, 6, 4, 8, 5, 3, 7, VIS),
        D("9121564d", "3M and 6M ended 2026-06-30 reviewed", True, 6, 4, 8, 5, 3, 7, TXT),
    ],
    "identified": {
        "6be0d936": ("Arabic 9M ended 2021-09-30 (cover read)", "scan, textless; not transcribed; Arabic"),
        "a0ef43db": ("Arabic 3M and 6M ended 2021-06-30 (cover read)", "scan, textless; not transcribed; Arabic"),
        "283abd43": ("Arabic 3M ended 2021-03-31 (cover read)", "scan, textless; not transcribed; Arabic"),
        "a7f68f3c": ("English 3M ended 2022-03-31 (cover read)", "scan, textless pdf p1-7; not transcribed"),
        "f3219ce3": ("Arabic 3M ended 2022-03-31 (cover read)", "scan, language twin of a7f68f3c; not transcribed"),
        "fcda052e": ("English 3M and 6M ended 2022-06-30 (cover read)", "scan, all 18 pages textless; not transcribed"),
        "c9662492": ("Arabic 3M and 6M ended 2022-06-30 (first-page text)", "Arabic twin; not transcribed"),
        "9c7e8e4f": ("English 3M and 9M ended 2022-09-30 (first-page text)", "statements image-only (textless pdf p3-9); not transcribed"),
        "a3d42f36": ("Arabic 3M and 9M ended 2022-09-30 (first-page text)", "Arabic twin; not transcribed"),
        "e90507c4": ("Arabic FY ended 2022-12-31 audited FS (first-page text; collector slot None|None)", "language twin of eb3719c7; no fiscal year or slot in the inventory; not transcribed"),
        "af6bda93": ("Arabic annual report 2022", "annual report; not read"),
        "cb0ed072": ("English 3M ended 2023-03-31 (first-page text)", "statements image-only (textless pdf p3-9); not transcribed"),
        "902fb527": ("Arabic 3M ended 2023-03-31 (cover read; collector slot 2023|None)", "scan, all 25 pages textless; language twin of cb0ed072; not transcribed"),
        "3b9d999d": ("English 3M and 6M ended 2023-06-30 (index page p2)", "classed other_no_statements_found, but index lists the statements and pdf p3-20 are image-only; not transcribed"),
        "d328e786": ("Arabic 3M and 6M ended 2023-06-30 (first-page text)", "Arabic twin; not transcribed"),
        "fd2d4621": ("English 3M and 9M ended 2023-09-30 (first-page text)", "born-digital statements present on pdf p4-9; not transcribed"),
        "73fbf1d1": ("Arabic 3M and 9M ended 2023-09-30 (first-page text)", "Arabic twin; not transcribed"),
        "b126e985": ("Arabic FY ended 2023-12-31 audited FS (first-page text)", "language twin of 964e652f; not transcribed"),
        "e1d005f0": ("Arabic annual report 2023", "annual report; not read"),
        "17e59ef2": ("English 3M ended 2024-03-31 (first-page text)", "born-digital statements present (pdf p4-9); not transcribed; Q1 2024 IS and CF known from the Q1 2025 comparatives"),
        "fe8cb108": ("English 3M and 6M ended 2024-06-30 (first-page text)", "born-digital statements present; not transcribed; 6M and Q2 2024 IS and 6M CF known from the H1 2025 comparatives"),
        "bf2e82bd": ("Arabic 3M and 6M ended 2024-06-30 (cover read; collector slot 2024|None)", "garbled font text layer, cover rendered; language twin of fe8cb108; not transcribed"),
        "aeeafc0f": ("English 3M and 9M ended 2024-09-30 (first-page text)", "born-digital statements present; not transcribed; 9M and Q3 2024 known from the 9M 2025 comparatives"),
        "af512f78": ("Arabic 3M and 9M ended 2025-09-30 (first-page text)", "Arabic twin of f79e7223; not transcribed"),
    },
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_9_filings_with_re_presentations_recorded",
            "summary": ("Headline BS, income and cash-flow values (full SAR) transcribed from pages for FY2022, FY2023, FY2024, FY2025, Q1 2025, H1 2025, 9M 2025, "
                        "Q1 2026 and H1 2026 including comparative columns and Q2/Q3 quarter columns. All identities hold with zero difference: total assets = "
                        "liabilities + equity; CFO+CFI+CFF = net change; opening cash + net change = closing cash (and closing cash equals balance-sheet cash in all nine); "
                        "revenue + cost = gross profit; profit before zakat less zakat = net profit; Q1+Q2=H1 and H1+Q3=9M for revenue, gross profit and net profit "
                        "in 2025 and Q1+Q2=H1 for 2026. No non-controlling interest: net profit equals profit attributable to shareholders. Selected: FY2025 revenue "
                        "1,234,531,248, net profit 241,859,844, total assets 2,735,020,822, CFO 213,920,041; H1 2026 revenue 640,839,143, net profit 128,126,265, "
                        "total assets 2,886,260,665. Same-period values differ between filings in presentation only (defect B009-4007-4): net profit, totals and cash "
                        "flows agree everywhere; both versions are in the transcript with restated flags."),
            "not_read": [
                "notes in every file (including the notes behind the FY2025 goodwill impairment, contingent consideration and land expropriation items)",
                "statements of changes in equity and OCI (only H1 2026 OCI page text seen)",
                "2021 Q1/H1/9M, 2022 Q1/H1/9M, 2023 Q1/H1/9M and 2024 Q1/H1/9M standalone interim filings (their IS and part of CF are known only as comparatives from the 2025 filings)",
                "all Arabic files and the two annual reports",
            ],
        },
        "document_completeness": {
            "status": "primary_statements_present_in_every_english_standalone_file_inventory_classification_wrong_for_image_only_pages",
            "summary": ("Every English standalone FS file opened carries a statement of profit or loss, OCI, financial position, equity and cash flows (index on pdf p2). "
                        "FY2022, FY2023, FY2025 statements are image-only in pdf p3-14 (printed 1-13), which hides them from the inventory; Q1 2026 (cbbdf048) has image-only "
                        "pdf p3-9 although the inventory lists statement_pages 22 and 20 (notes pages); the FY2024 file and 2025 interims and H1 2026 have born-digital statement "
                        "pages with the shaded current-period column sometimes missing from the text layer (Q1 2025 p4). Whole-file scans: 2021 Q1/H1/9M (Arabic), 2022 Q1 "
                        "(English and Arabic) and H1 (English), 2023 Q1 (Arabic). Language twins (Arabic) exist for most interims and FY2022/FY2023; two annual reports are "
                        "unread. Three files carry no usable slot (None|None e90507c4, 2023|None 902fb527, 2024|None bf2e82bd)."),
            "defect_ids": ["B009-4007-1", "B009-4007-2", "B009-4007-3", "B009-4007-5"],
        },
        "company_coverage": {
            "status": "contiguous_2021Q1_to_2026H1_files_english_from_2022",
            "present_in_files_by_page_derived_period": [
                "2021|Q1 (Arabic scan)", "2021|H1 (Arabic scan)", "2021|9M (Arabic scan)",
                "2022|Q1", "2022|H1", "2022|9M", "2022|FY",
                "2023|Q1", "2023|H1", "2023|9M", "2023|FY",
                "2024|Q1", "2024|H1", "2024|9M", "2024|FY",
                "2025|Q1", "2025|H1", "2025|9M", "2025|FY",
                "2026|Q1", "2026|H1",
            ],
            "values_verified_from_own_pages": ["2022|FY", "2023|FY", "2024|FY", "2025|FY", "2025|Q1", "2025|H1", "2025|9M", "2026|Q1", "2026|H1"],
            "values_known_only_as_comparatives": [
                "2021|FY (FY2022 filing: IS, BS, CF)", "2024|Q1 IS and CF (Q1 2025 filing)", "2024|H1 and Q2 2024 IS, 6M CF (H1 2025 filing)",
                "2024|9M and Q3 2024 IS, 9M CF (9M 2025 filing)", "2025|Q4 only by subtraction FY2025 minus 9M 2025 (not a source value)",
            ],
            "values_not_read": ["2021|Q1", "2021|H1", "2021|9M", "2022|Q1", "2022|H1", "2022|9M", "2023|Q1", "2023|H1", "2023|9M", "2024|Q1 original", "2024|H1 original", "2024|9M original"],
            "missing": ["everything before 2021 Q1; 2021|FY standalone statements (only as comparative in the FY2022 filing)"],
            "inventory_corrections": ("annual FS files carry the publication year: 2023|FY is FY2022 (eb3719c7), 2024|FY is FY2023 (964e652f), 2025|FY is FY2024 "
                                      "(507b9a1e), 2026|FY is FY2025 (b97990d3), so the inventory reports no FY2021 and an unexpected 2026|FY. Page-derived: 21 distinct periods 2021 Q1 "
                                      "to 2026 H1 have a file; 2022 Q1 to 2026 H1 are gap-free in English."),
        },
    },
    "defects": [
        {"id": "B009-4007-1", "class": "period_label_publication_year", "severity": "medium",
         "evidence": "Standalone annual FS eb3719c7 (FY2022), 964e652f (FY2023), 507b9a1e (FY2024), b97990d3 (FY2025) are labelled 2023|FY, 2024|FY, 2025|FY, 2026|FY (cover pages 'FOR THE YEAR ENDED 31 DECEMBER ...'). Annual reports e1d005f0 and af6bda93 carry the fiscal year label instead."},
        {"id": "B009-4007-2", "class": "image_only_statement_pages_flagged_partial_or_missing", "severity": "medium",
         "evidence": "Statement pages are images in eb3719c7, 964e652f, b97990d3 (pdf p3-14), cbbdf048 (pdf p3-9, inventory points at note pages 22 and 20), 9c7e8e4f and cb0ed072 (p3-9) and 3b9d999d (p3-20, classed other_no_statements_found). Rendered pages show complete statements."},
        {"id": "B009-4007-3", "class": "text_layer_drops_current_period_column", "severity": "high",
         "evidence": "Q1 2025 (030791ca) pdf p4: the text layer gives revenue 277,040,344 (the 2024 comparative); the rendered page shows 301,880,733 for 2025, cost 205,374,358, gross profit 96,506,375. Reading text-layer rows without a visual check would take the wrong column. The 9M 2025 and H1 2025 pages were tied by roll checks, not by eye."},
        {"id": "B009-4007-4", "class": "re_presented_comparatives", "severity": "medium",
         "evidence": ("(a) FY2022 in the FY2023 filing: cost of revenue 706,378,359 -> 702,725,852, gross profit 416,018,666 -> 419,671,173, selling and marketing 6,172,580 -> 10,225,270, "
                      "G&A 92,699,058 -> 92,298,875; operating profit 291,784,961 and net profit 257,336,168 unchanged. "
                      "(b) FY2023 in the FY2024 filing: loss on disposal (1,481,702) split out of other operating income 29,413,468 -> 30,895,170; long-term loans 163,826,053 -> 173,847,770 and "
                      "current portion 28,735,957 -> 18,714,240 (non-current liabilities 465,939,926 -> 475,325,401, current 283,584,124 -> 274,198,649, total liabilities 749,524,050 unchanged). "
                      "(c) FY2024 cash flow in the FY2025 filing: net changes in related parties (4,003,421) -> (3,860,655) and trade payables (4,755,888) -> (4,898,654), sum unchanged. "
                      "Both versions are in the transcripts and the page-level values; no filing was substituted for another.")},
        {"id": "B009-4007-5", "class": "duplicates_language_twins_and_no_slot_files", "severity": "low",
         "evidence": "Arabic twins for 2022-2025 interims and FY2022/FY2023 FS are separate inventory files in the same slots; e90507c4 (Arabic FY2022 FS) has no year or slot, 902fb527 is the Arabic Q1 2023 scan labelled 2023|None, bf2e82bd the Arabic H1 2024 file labelled 2024|None."},
        {"id": "B009-4007-6", "class": "interim_cash_flow_not_decomposed", "severity": "low",
         "evidence": "Q1 and H1 cash flows were transcribed separately and never subtracted: Q1 2026 shows 'Repayment of government borrowings (9,879,750)' where H1 2026 shows proceeds 90,000,000 and 'Repayment of long and short-term loans (107,337,000)', so a Q2 cash-flow derived by subtraction needs the line mapping checked first."},
    ],
    "unread_items": [
        "notes in all files",
        "equity statements and OCI statements",
        "2021 Q1/H1/9M, 2022 Q1/H1/9M, 2023 Q1/H1/9M, 2024 Q1/H1/9M standalone interim filings (see files_not_audited_for_values)",
        "Arabic files, annual reports 2022 and 2023",
        "everything before 2021 Q1 (no files)",
    ],
    "conclusion": ("NOT claimed complete. Nine filings value-verified from pages (FY2022 to FY2025, Q1/H1/9M 2025, Q1/H1 2026) with all arithmetic identities passing; "
                   "21 page-derived periods 2021 Q1 to 2026 H1 have a file but 12 are not value-read in their own filing and nothing before 2021 is present."),
}
mkrecord.build(spec)
