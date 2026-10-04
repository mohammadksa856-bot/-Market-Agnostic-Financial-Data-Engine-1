import mkrecord

U = "SAR thousand"
VIS = "visual (statement pages are images, rendered and read)"


def D(sha, period, ok, bs, is_, cf, pbs, pis, pcf, reading=VIS):
    return {"sha256": sha, "actual_period": period, "label_ok": ok, "pdf_pages": {"bs": bs, "is": is_, "cf": cf},
            "printed_pages": {"bs": pbs, "is": pis, "cf": pcf}, "units": U, "reading": reading}


def ar(period, extra=""):
    return (f"Arabic {period} (cover read)", "whole-file scan, textless, Arabic language twin of an English file; not transcribed" + extra)


def en(period, extra=""):
    return (f"English {period} (cover read)", "whole-file scan, textless; not transcribed" + extra)


spec = {
    "symbol": "4280",
    "name": "KINGDOM (Kingdom Holding Company)",
    "method": ("SHA-256 recomputed for every audited file (tools/mkrecord.py). all 45 files are whole-file scans or have image-only statement pages (only a review-report or note page carries text in six files); "
               "the inventory classes 37 of them scanned_unreadable and finds no usable statement pages in the rest. Every file was identified by rendering its cover "
               "(tools/covers.py montages), and the primary statements of FY2023, FY2024, FY2025, Q1 2026 and H1 2026 were rendered and read by eye. tools/check_transcripts.py "
               "over transcripts/4280.json checks BS identity, cash-flow sum and roll, profit before tax less withholding tax and zakat equals profit, owners + NCI = profit, "
               "cross-filing agreement of comparatives and Q1+Q2=H1 rolls for 2026 and for the 2025 comparatives; all pass."),
    "documents": [
        D("373b1daa", "FY ended 2025-12-31 audited (collector label 2026|FY, classed other_no_statements_found)", False, 8, 9, 12, 6, 7, 10),
        D("f9757968", "FY ended 2024-12-31 audited, as filed (whole-file scan, collector label 2025|FY)", False, 7, 8, 11, 5, 6, 9),
        D("f15698c2", "FY ended 2023-12-31 audited, as filed (whole-file scan, collector label 2024|FY)", False, 7, 8, 11, 5, 6, 9),
        D("4901b251", "3M ended 2026-03-31 reviewed (English)", True, 4, 5, 8, 3, 4, 7),
        D("00754ef7", "3M and 6M ended 2026-06-30 reviewed (English)", True, 4, 5, 8, 3, 4, 7),
    ],
    "identified": {
        "5e95516f": ("English FY ended 2021-12-31 (cover read; slot None|None)", "whole-file scan; not transcribed; FY2021 not available as a comparative here (FY2022 original not opened)"),
        "f4f65197": ar("FY ended 2021-12-31 (slot None|None)"),
        "bf92976f": ar("FY ended 2022-12-31 (slot None|None)"),
        "ee97b5d6": ar("FY ended 2023-12-31 (slot None|None)"),
        "08260242": ar("FY ended 2024-12-31 (slot None|None)"),
        "c27fa8ee": ("Arabic FY ended 2025-12-31 (cover read; slot None|None)", "classed partial_statements (text on income and cash-flow note pages, not primary statements); language twin of 373b1daa; not transcribed"),
        "27cdfda0": ("English FY ended 2023-12-31 (cover read; slot None|None)", "whole-file scan, 54 pages; second copy of the FY2023 file (f15698c2 is labelled 2024|FY); not compared page by page"),
        "b63e3443": ("English FY ended 2022-12-31 (cover read; label 2023|FY)", "whole-file scan, 50 pages; FY2022 own file not transcribed (FY2022 values taken from the comparative column of the FY2023 filing only)"),
        "df64f71d": ("English 3M and 9M ended 2021-09-30 (cover read; collector label 2029|9M)", "whole-file scan; not transcribed; the fiscal-year label 2029 is wrong"),
        "3b8f71b6": ("Arabic 3M and 6M ended 2023-06-30 (cover read; collector label 2006|H1)", "whole-file scan; not transcribed; the fiscal-year label 2006 is wrong; language twin of 6d9450b1"),
        "ffe5b079": en("3M ended 2021-03-31 (slot None|Q1)"), "83bbcc38": en("3M and 6M ended 2021-06-30 (slot None|H1)"),
        "9a54d1c4": ar("3M ended 2021-03-31"), "3dc09c6e": ar("3M and 6M ended 2021-06-30"), "a72b20b8": ar("3M and 9M ended 2021-09-30"),
        "919dcf1e": ar("3M ended 2022-03-31"), "b3d21c4b": ar("3M and 6M ended 2022-06-30"), "2c04ae93": ar("3M and 9M ended 2022-09-30"),
        "a5cb6c8d": ar("3M ended 2023-03-31"), "3dcb1c7c": ar("3M and 9M ended 2023-09-30"),
        "7d7e5772": ar("3M ended 2024-03-31"), "af10774e": ar("3M and 6M ended 2024-06-30"), "1aa0617a": ar("3M and 9M ended 2024-09-30", "; inventory marks financial_statements from a text p3 review report only"),
        "d3768b34": ar("3M ended 2025-03-31"), "e99651c2": ar("3M and 6M ended 2025-06-30"), "0dfea526": ar("3M and 9M ended 2025-09-30"),
        "72bc81c9": ar("3M ended 2026-03-31", "; inventory marks it financial_statements on a text page only"), "9a972666": ar("3M and 6M ended 2026-06-30", "; inventory marks financial_statements on a text page only"),
        "f11c4a85": en("3M ended 2022-03-31"), "c99fcdfd": en("3M and 6M ended 2022-06-30"), "1bcb4bd7": en("3M and 9M ended 2022-09-30"),
        "42a87a99": en("3M ended 2023-03-31"), "6d9450b1": en("3M and 6M ended 2023-06-30"), "c159ca05": en("3M and 9M ended 2023-09-30"),
        "b47a6f95": en("3M ended 2024-03-31"), "ce1dbeb9": en("3M and 6M ended 2024-06-30"), "1b968d87": en("3M and 9M ended 2024-09-30", "; inventory marks financial_statements on a text p3 review report only"),
        "5377f128": en("3M ended 2025-03-31"), "f7ae06d3": en("3M and 6M ended 2025-06-30"), "011b4e21": en("3M and 9M ended 2025-09-30"),
    },
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_5_filings_comparatives_consistent_no_restatement_found",
            "summary": ("Headline BS, income and cash-flow values (SAR thousand) transcribed from rendered pages for FY2023, FY2024, FY2025, Q1 2026 and H1 2026 with comparative columns "
                        "(FY2022, Q1 2025, H1 2025, Q2 2025) and Q2 2026. Identities hold with zero difference: total assets = liabilities + equity; CFO+CFI+CFF = net change; opening + net change = closing "
                        "cash and cash equivalents; profit before zakat, withholding and income tax less those taxes = profit; owners + non-controlling interests = profit; Q1+Q2=H1 2026 for revenue, "
                        "profit from operations, profit before tax and profit; the 2025 Q1 (from the Q1 2026 filing) plus Q2 (from the H1 2026 filing) equal H1 2025 within 1 thousand (rounding). "
                        "Values for one fiscal period agree between filings (FY2023 original = FY2024 comparative; FY2024 original = FY2025 comparative), so no restatement was found. "
                        "Kingdom has no single revenue line: 'revenue' in the transcript is Hotels and other operating revenues, with dividend income (948,289 in FY2025) and equity-accounted results "
                        "(1,039,004) reported separately. Selected: FY2025 hotel revenue 1,677,547, profit 2,112,899 (shareholders 2,143,294), total assets 74,934,321, CFO 986,212; "
                        "H1 2026 profit 588,598, total assets 85,462,792, CFO 538,664."),
            "not_read": [
                "notes in every file (including the FVOCI investment note 10 that drives the large fair-value reserve swings and the 2025 sale of an equity-accounted investee)",
                "statements of changes in equity (none opened) and OCI beyond FY2024 p9",
                "FY2022 and FY2021 own files, all 2021 to 2025 interim filings (English and Arabic scans); FY2022 is known only as the FY2023 comparative column",
            ],
        },
        "document_completeness": {
            "status": "primary_statements_present_in_every_file_opened_inventory_classification_wrong_because_files_are_images",
            "summary": ("Every file opened holds BS, income, comprehensive income, equity and cash flows (FY2025 index on pdf p2: BS 6, income 7, OCI 8, equity 9, cash flows 10; interims 3-7). "
                        "Statement pages are images in all 45 files (whole-file scans classed scanned_unreadable, or text PDFs where only the review-report page has text: 4901b251, 00754ef7, "
                        "1b968d87, 1aa0617a, 9a972666, 72bc81c9), so the inventory finds none, or points at the review report as 'statement pages'. FY2025 373b1daa is classed other_no_statements_found "
                        "although its pdf p8-12 are the full statements. Twenty-four files (7 annual, 17 interim) carry no fiscal year and Arabic twins exist for every period."),
            "defect_ids": ["B009-4280-1", "B009-4280-2", "B009-4280-3", "B009-4280-5"],
        },
        "company_coverage": {
            "status": "contiguous_2021Q1_to_2026H1_files_all_periods_present",
            "present_in_files_by_page_derived_period": [
                "2021|Q1", "2021|H1", "2021|9M", "2021|FY", "2022|Q1", "2022|H1", "2022|9M", "2022|FY", "2023|Q1", "2023|H1", "2023|9M", "2023|FY",
                "2024|Q1", "2024|H1", "2024|9M", "2024|FY", "2025|Q1", "2025|H1", "2025|9M", "2025|FY", "2026|Q1", "2026|H1",
            ],
            "values_verified_from_own_pages": ["2023|FY", "2024|FY", "2025|FY", "2026|Q1", "2026|H1"],
            "values_known_only_as_comparatives": [
                "2022|FY (FY2023 filing: BS, IS, CF)", "2025|Q1 (Q1 2026 filing: IS, CF)", "2025|H1 six months and Q2 (H1 2026 filing: IS, CF)",
                "2025|Q1 BS is not shown (no comparative BS for March 2025)",
            ],
            "values_not_read": ["2021|Q1", "2021|H1", "2021|9M", "2021|FY", "2022|Q1", "2022|H1", "2022|9M", "2022|FY own file", "2023|Q1", "2023|H1", "2023|9M",
                                "2024|Q1", "2024|H1", "2024|9M", "2025|Q1 own file", "2025|H1 own file", "2025|9M"],
            "missing": ["everything before 2021 Q1 (no files)"],
            "inventory_corrections": ("annual FS are labelled by publication year: 2023|FY (b63e3443) is FY2022, 2024|FY (f15698c2) is FY2023, 2025|FY (f9757968) is FY2024, 2026|FY (373b1daa) is FY2025; "
                                      "seven files labelled None|None are Arabic or English annual files for FY2021 to FY2025; interim labels follow the period reported except df64f71d (2029|9M, really 9M 2021) "
                                      "and 3b8f71b6 (2006|H1, really H1 2023). The inventory therefore shows no FY2021, no 2021 interims and a bogus 2029 and 2006 year."),
        },
    },
    "defects": [
        {"id": "B009-4280-1", "class": "period_label_publication_year_and_missing_labels", "severity": "medium",
         "evidence": "Covers read: b63e3443 (2023|FY) is FY2022, f15698c2 (2024|FY) FY2023, f9757968 (2025|FY) FY2024, 373b1daa (2026|FY) FY2025; seven annual files (5e95516f, f4f65197, bf92976f, ee97b5d6, 08260242, 27cdfda0, c27fa8ee) have fiscal year None."},
        {"id": "B009-4280-2", "class": "whole_file_scans_and_image_only_statements_flagged_unreadable_or_no_statements", "severity": "high",
         "evidence": "37 files classed scanned_unreadable; 373b1daa classed other_no_statements_found; 4901b251, 00754ef7, 1b968d87, 1aa0617a, 9a972666, 72bc81c9 list the p3 auditor review report as statement pages while the statements (p4-8) are images."},
        {"id": "B009-4280-3", "class": "wrong_fiscal_year_values_in_inventory", "severity": "medium",
         "evidence": "df64f71d carries fiscal year 2029 (cover: 9M ended 30 September 2021); 3b8f71b6 carries 2006 (cover: 6M ended 30 June 2023, Arabic). Both would create impossible years in a period index."},
        {"id": "B009-4280-4", "class": "cash_definition_differs_between_annual_and_interim", "severity": "high",
         "evidence": "FY2025 cash flow closes at 1,331,554 (cash excluding restricted cash) while the balance sheet shows 1,524,563; the H1 2026 and Q1 2026 cash flows open at 1,524,563 (the balance-sheet figure) and H1 2025 opens at 1,689,658 = Dec 2024 balance sheet (FY2024 cash flow closed at 1,495,903). Annual and interim cash flows are therefore on different cash definitions; interim opening cash does not equal the prior annual cash-flow closing cash."},
        {"id": "B009-4280-5", "class": "interim_cash_flow_line_presentation_differs_q1_vs_h1", "severity": "medium",
         "evidence": "Q1 2026 cash flow shows Finance income (3,007) and Financial charges 206,413 as separate adjustments while the H1 2026 cash flow shows one line Financial charges, net 408,750; Q1 2026 also lists Additions to investment properties (69,993) where H1 shows (87,385) and a different line order. Subtracting Q1 from H1 line by line to get Q2 would mix classifications; only the three section totals roll (CFO 157,567 -> 538,664, CFI 990,256 -> 581,870)."},
        {"id": "B009-4280-6", "class": "no_single_revenue_line", "severity": "low",
         "evidence": "Income statement has no total revenue: hotels and other operating revenues, hotel costs, dividend income, gain on FVTPL, equity-accounted results and gains on sales are separate lines; a revenue field must be defined explicitly (here hotel revenue 1,677,547 in FY2025 against dividend income 948,289)."},
    ],
    "unread_items": [
        "notes in all files",
        "equity statements and the Q1 and H1 2026 comprehensive income pages",
        "FY2021 and FY2022 own files and all 2021-2025 interim filings, English and Arabic (see files_not_audited_for_values)",
        "second FY2023 copy 27cdfda0 and Arabic FY2025 file c27fa8ee not compared with their English twins",
        "2025 Q1/H1/9M originals; March 2025 balance sheet",
        "nothing before 2021 Q1: no files",
    ],
    "conclusion": ("NOT claimed complete. Five filings value-verified from rendered pages with no restatement found; 22 periods 2021 Q1 to 2026 H1 have a file but 17 are not value-read in their own filing; "
                   "all statement pages are images so the inventory classification is unreliable; fiscal-year labels 2029 and 2006 are wrong."),
}
mkrecord.build(spec)
