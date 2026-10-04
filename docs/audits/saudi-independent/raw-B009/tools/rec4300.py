import mkrecord

U = "SAR thousand (SR 000)"
VIS = "visual (whole-file scan, statement pages rendered and read)"
TXT = "text layer (born digital with OCR-style text), tied by arithmetic; page images not rendered"


def D(sha, period, ok, bs, is_, cf, pbs, pis, pcf, reading=VIS):
    return {"sha256": sha, "actual_period": period, "label_ok": ok, "pdf_pages": {"bs": bs, "is": is_, "cf": cf},
            "printed_pages": {"bs": pbs, "is": pis, "cf": pcf}, "units": U, "reading": reading}


def cv(period, extra=""):
    return (f"{period} (cover read)", "whole-file scan; collector label agrees with the cover; not transcribed" + extra)


spec = {
    "symbol": "4300",
    "name": "DAR ALARKAN (Dar Al Arkan Real Estate Development Company)",
    "method": ("SHA-256 recomputed for every audited file (tools/mkrecord.py). Of 65 files, 54 are whole-file scans (no text layer) classed scanned_unreadable. "
               "The FY2022 to FY2025 audited statements and the Q1 and H1 2026 interims were rendered and read by eye; FY2020 and FY2021 are born-digital PDFs read from the text layer "
               "(rows.py) and tied by arithmetic without page images. Covers of the other files were rendered as montages (tools/covers.py) but only some are legible, so many periods are unverified. "
               "tools/check_transcripts.py over transcripts/4300.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat plus discontinued operations to net profit, "
               "owners + NCI = profit, cross-filing agreement of comparatives with explicit restated flags and Q1+Q2=H1 rolls for 2026 and the 2025 comparatives; all pass."),
    "documents": [
        D("545ed36b", "FY ended 2025-12-31 audited (collector label 2026|FY)", False, 9, 10, 12, 7, 8, 10),
        D("28fb9881", "FY ended 2024-12-31 audited, as filed (collector label 2025|FY)", False, 9, 10, 12, 7, 8, 10),
        D("36ceb1c7", "FY ended 2023-12-31 audited, as filed (collector label 2024|FY)", False, 9, 10, 12, 7, 8, 10),
        D("7b2fd6da", "FY ended 2022-12-31 audited, as originally filed (collector label 2023|FY)", False, 9, 10, 12, 7, 8, 10),
        D("103976f8", "FY ended 2021-12-31 audited (label 2021|FY correct)", True, 8, 9, 11, 6, 7, 9, TXT),
        D("2a5adf57", "FY ended 2020-12-31 audited (label 2020|FY correct)", True, 8, 9, 11, 6, 7, 9, TXT),
        D("c322f053", "3M and 6M ended 2026-06-30 reviewed (English)", True, 4, 5, 7, 2, 3, 5),
        D("89995ef7", "3M ended 2026-03-31 reviewed (English)", True, 5, 4, 7, 2, 3, 5),
    ],
    "identified": {
        "b86029b7": ("Arabic-language file: FY ended 2005-12-31 audited FS (cover read)", "scan; not transcribed"),
        "eb108b26": ("Financial Update as of 31 December 2010 (investor presentation, cover read)", "8-page results slide deck (revenue 4,142 SAR million for 2010 in the text layer); not a statement set; not read further"),
        "1c12d095": ("9M ended 2014-09-30 (cover text)", "born digital, notes text only per inventory; not transcribed"),
        "4cc2f921": ("3M ended 2014-03-31 (cover text)", "not transcribed"),
        "62118711": ("FY ended 2014-12-31 (cover text)", "born digital with five textless pages; not transcribed"),
        "524b0f07": ("6M ended 2014-06-30 (cover read)", "scan; not transcribed"),
        "a717ddc0": ("9M ended 2015-09-30 (cover read)", "scan; not transcribed"), "7961743d": ("FY ended 2015-12-31 (cover read)", "scan; not transcribed"),
        "5a123605": ("6M ended 2015-06-30 (cover read)", "scan; not transcribed"), "ef032dab": ("3M ended 2015-03-31 (cover read)", "scan; not transcribed"),
        "92059827": ("9M ended 2016-09-30 (cover read)", "scan; not transcribed"), "4b8ff231": ("FY ended 2016-12-31 (cover read)", "scan; not transcribed"),
        "ef27e535": ("9M ended 2020-09-30 (cover read)", "scan; not transcribed"), "cdd2ad90": ("6M ended 2020-06-30 (cover read)", "scan; not transcribed"),
        "b92c0bb6": ("6M ended 2021-06-30 (cover read)", "scan; not transcribed"), "18526192": ("3M ended 2021-03-31 (cover read)", "scan; not transcribed"),
        "511e32ba": ("3M and 9M ended 2022 (cover text partly legible)", "scan; not transcribed"),
        "2cd4939b": ("3M and 6M ended 2022 (cover text partly legible)", "scan; not transcribed"),
        "18edc8f0": ("3M ended 2022-03-31 (cover text)", "born digital with full text layer (inventory statement pages 3-7); not transcribed in this batch"),
        "c6d33655": ("Annual report 2022 (cover)", "annual report, 93 pages; not read"),
        "0a48a10f": ("Annual report 2023 (cover)", "annual report, 97 pages; not read"),
        "d308f972": ("Annual report 2024 (cover)", "annual report, 127 pages; not read"),
        "b9710436": ("Annual report 2025 (cover)", "annual report, 172 pages; not read; contains consolidated financial statements per its table of contents"),
        "a74326f8": ("FY ended 2023-12-31 (cover read; collector label 2023|FY)", "scan; second FY2023 copy besides 36ceb1c7; the 2023|FY slot therefore holds FY2022 (7b2fd6da) and FY2023 (a74326f8)"),
        "b131b816": ("FY (cover partly legible; label 2024|FY)", "scan; Arabic twin per inventory; not transcribed"),
        "82a56369": ("9M 2023 interim (cover)", "scan; not transcribed"), "ee5a5a51": ("9M 2023 interim (cover)", "scan; not transcribed"),
        "7ac0cbfe": ("H1 2023 interim (cover)", "scan; not transcribed"), "3c0a874e": ("Q1 2023 interim (cover)", "scan; not transcribed"),
        "a628ed18": ("Q1 2023 interim (cover)", "scan; not transcribed"), "a9a8462d": ("9M 2024 interim (cover)", "scan; not transcribed"),
        "1e823ad6": ("3M and 6M ended 2024-06-30 (cover read)", "scan; not transcribed"),
    },
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_8_filings_with_cash_flow_re_presentation_recorded",
            "summary": ("Headline BS, income and cash-flow values (SAR thousand) transcribed for FY2020 and FY2021 (text layer), FY2022 to FY2025 (rendered pages), Q1 2026 and H1 2026 with comparatives and Q2 columns. "
                        "Identities hold with zero difference: total assets = liabilities + equity; CFO+CFI+CFF = net change; opening + net change = closing cash (equal to balance-sheet cash); revenue - cost = gross profit; "
                        "profit before zakat less zakat plus discontinued operations = net profit; owners + NCI = net profit; Q1+Q2=H1 for revenue, gross profit, operating profit, profit before zakat and net profit in 2026 and in the 2025 comparatives. "
                        "Selected: FY2025 revenue 3,899,802, net profit 1,133,920 (owners 1,134,182), total assets 41,612,961, CFO -3,319,216 (negative: development properties build 4,100,037); H1 2026 revenue 2,343,274, net profit 498,972, total assets 43,684,907, CFO 4,245. "
                        "The FY2022 cash flow as originally filed (CFO 454,129, CFF 1,335,559) was re-presented in the FY2023 filing (CFO 460,062, CFF 1,329,626, lease principal 5,933 moved into financing); "
                        "FY2023 CFO 1,416,433 as filed became 1,426,335 and CFI -1,163,882 became -1,173,784 in the FY2024 filing (defect B009-4300-4). Income statements and balance sheets agree between filings."),
            "not_read": [
                "notes in every file", "equity statements (H1 2026 equity page is rotated)",
                "FY2005, FY2014 to FY2019 files, 2014-2021 interims, 2022-2025 interims (see files_not_audited_for_values)",
                "annual reports 2022 to 2025 and the 2010 results deck",
                "page images of the FY2020 and FY2021 files (text layer only)",
                "capex in the FY2024-filing 2023 comparative column (clipped by the scan edge); CFO 1,426,335 there is derived from the cash-flow identity (visible digits 1,426,3)",
            ],
        },
        "document_completeness": {
            "status": "primary_statements_present_in_every_file_opened_inventory_classification_wrong_for_54_scans",
            "summary": ("Every audited-FS file opened holds BS, profit or loss and OCI, equity and cash flows (FY2025 index: BS 7, P&L 8, equity 9, cash flows 10; interims 2-5). 54 of 65 files are whole-file scans classed "
                        "scanned_unreadable, among them every FY2022 to FY2025 statement file and the 2026 interims, while the FY2020 and FY2021 statements are born digital but flagged only by partly matching pages. "
                        "The right-hand column of the 2023 cash flow in the FY2024 file is cut off by the scan edge. Annual-report files (2022 to 2025) are classed annual_report_with_statements or no_statements though the 2025 report lists the consolidated statements. "
                        "A fiscal-year slot can hold two files for different fiscal years (2023|FY holds FY2022 and FY2023)."),
            "defect_ids": ["B009-4300-1", "B009-4300-2", "B009-4300-3", "B009-4300-5"],
        },
        "company_coverage": {
            "status": "files_for_2014_to_2026H1_every_period_FY2005_and_2010_isolated",
            "present_in_files_by_page_derived_period": [
                "2005|FY (scan)", "2010|results deck only", "2014|Q1", "2014|H1", "2014|9M", "2014|FY", "2015|Q1", "2015|H1", "2015|9M", "2015|FY",
                "2016|Q1", "2016|H1", "2016|9M", "2016|FY", "2017|Q1..FY", "2018|Q1..FY", "2019|Q1..FY (collector labels; covers not all legible)",
                "2020|Q1", "2020|H1", "2020|9M", "2020|FY", "2021|Q1", "2021|H1", "2021|9M", "2021|FY", "2022|Q1", "2022|H1", "2022|9M", "2022|FY",
                "2023|Q1", "2023|H1", "2023|9M", "2023|FY", "2024|Q1", "2024|H1", "2024|9M", "2024|FY", "2025|Q1", "2025|H1", "2025|9M", "2025|FY", "2026|Q1", "2026|H1",
            ],
            "values_verified_from_own_pages": ["2020|FY", "2021|FY", "2022|FY", "2023|FY", "2024|FY", "2025|FY", "2026|Q1", "2026|H1"],
            "values_known_only_as_comparatives": ["2019|FY balance sheet totals (FY2020 filing)", "2025|Q1 and 2025|H1 six months and Q2 (2026 filings)", "2020|FY cash flow (FY2021 filing)"],
            "values_not_read": ["2005|FY", "2014 to 2019 all periods", "2020|Q1", "2020|H1", "2020|9M", "2021|Q1", "2021|H1", "2021|9M", "2022|Q1", "2022|H1", "2022|9M",
                                "2023|Q1", "2023|H1", "2023|9M", "2024|Q1", "2024|H1", "2024|9M", "2025|Q1 original", "2025|H1 original", "2025|9M"],
            "missing": ["2006 to 2013 (no files except the 2010 deck)", "standalone 2025 interim values only as comparatives"],
            "inventory_corrections": ("annual files are labelled by publication year from 2022: 2023|FY holds FY2022 (7b2fd6da) and FY2023 (a74326f8), 2024|FY holds FY2023 (36ceb1c7) and an Arabic/other copy (b131b816), "
                                      "2025|FY holds FY2024 (28fb9881) and an Arabic twin (03e4c638), 2026|FY holds FY2025 (545ed36b); FY2020 and FY2021 are labelled by their fiscal year. "
                                      "Interim labels follow the period reported where the cover is legible; the cover of many 2017 to 2021 scans is blank at page 1 so the period was not independently verified."),
        },
    },
    "defects": [
        {"id": "B009-4300-1", "class": "period_label_publication_year_and_slot_collision", "severity": "medium",
         "evidence": "Covers read: 545ed36b (2026|FY) is FY2025, 28fb9881 (2025|FY) FY2024, 36ceb1c7 (2024|FY) FY2023, 7b2fd6da (2023|FY) FY2022; FY2020 and FY2021 files keep their own year. a74326f8 (cover: year ended 31 December 2023) and 7b2fd6da both sit in 2023|FY."},
        {"id": "B009-4300-2", "class": "whole_file_scans_classed_unreadable", "severity": "high",
         "evidence": "54 of 65 files are classed scanned_unreadable (no text layer) and the inventory lists no statement pages; rendered pages are legible. Includes every FY2022 to FY2025 statement file and 2026 interims. 2014 files and 18edc8f0 are text PDFs but 2014 files have five textless pages."},
        {"id": "B009-4300-3", "class": "clipped_scan_column", "severity": "medium",
         "evidence": "28fb9881 pdf p12 (cash flows FY2024): the right-hand 2023 comparative column is cut by the page edge (values end with a truncated last digit, e.g. 1,426,3 and 5,928,85); the same 2023 values are complete in 36ceb1c7 only as originally filed and differ (see B009-4300-4)."},
        {"id": "B009-4300-4", "class": "restated_or_represented_cash_flow_comparatives", "severity": "high",
         "evidence": ("(a) FY2022 cash flow: as filed (7b2fd6da) CFO 454,129, CFF 1,335,559 (borrowings only); re-presented in the FY2023 filing CFO 460,062, CFF 1,329,626 after lease principal (5,933) was added to financing; net change 1,775,431 and CFI -14,257 unchanged. "
                      "(b) FY2023 cash flow: as filed CFO 1,416,433, CFI -1,163,882; in the FY2024 filing CFO 1,426,335 (derived), CFI -1,173,784 (9,902 moved from investing to operating); CFF -731,575 and net change -479,024 unchanged. "
                      "(c) FY2024 and FY2025 income statements show the 2024 comparative with discontinued operations split (profit from discontinued operations 18,902) as filed, no change between the two filings. Income statements and balance sheets show no restatement across filings.")},
        {"id": "B009-4300-5", "class": "negative_operating_cash_flow_and_non_cash_definition", "severity": "low",
         "evidence": "FY2025 CFO -3,319,216 is driven by development properties (4,100,037) classed in working capital; H1 2026 CFO 4,245 and Q1 2026 CFO 223,079 are on the same presentation, so Q2 2026 CFO is -218,834 by subtraction. Interim and annual cash flows use the same cash definition (cash and cash equivalents equal balance sheet cash in all eight filings)."},
    ],
    "unread_items": [
        "notes in all files", "equity statements",
        "all 2014 to 2021 interim and annual files except FY2020 and FY2021; 2022 to 2025 interims (see files_not_audited_for_values)",
        "annual reports 2022 to 2025; 2010 results deck; FY2005",
        "page images of the FY2020 and FY2021 files",
        "2006 to 2013: no files",
    ],
    "conclusion": ("NOT claimed complete. Eight filings value-verified (six from rendered pages, two from the text layer) with cash-flow re-presentations recorded; files exist for 2014 to 2026 H1 by label "
                   "but 57 are not value-read and many covers are not legible; 2006 to 2013 and the 2010 deck are not statements."),
}
mkrecord.build(spec)
