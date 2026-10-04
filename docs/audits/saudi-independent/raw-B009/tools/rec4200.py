import mkrecord

U = "SAR (full riyals)"
VIS = "visual (whole-file scan, statement pages rendered and read)"


def D(sha, period, ok, bs, is_, cf, pbs, pis, pcf, reading=VIS):
    return {"sha256": sha, "actual_period": period, "label_ok": ok, "pdf_pages": {"bs": bs, "is": is_, "cf": cf},
            "printed_pages": {"bs": pbs, "is": pis, "cf": pcf}, "units": U, "reading": reading}


def ar(period):
    return (f"Arabic {period} (cover read)", "whole-file scan, all pages textless, language twin of the English file for the same period (collector fiscal year None); not transcribed")


def en(period, extra=""):
    return (f"English {period} (cover read)", "whole-file scan, all pages textless; not transcribed" + extra)


spec = {
    "symbol": "4200",
    "name": "ALDREES (Aldrees Petroleum and Transport Services Company)",
    "method": ("SHA-256 recomputed for every audited file (tools/mkrecord.py). Of 39 files, 37 are whole-file scans (all pages textless) classed scanned_unreadable; "
               "every scan was identified by rendering its cover (tools/covers.py montages) and the primary-statement pages of FY2022, FY2023, FY2024 (as originally filed), "
               "Q1 2026 and H1 2026 were rendered and read by eye. FY2025 (b98957d5) is born digital and was read from the text layer with the income statement page also rendered. "
               "tools/check_transcripts.py over transcripts/4200.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat to net income, cross-filing agreement of "
               "comparatives with explicit restated flags and Q1+Q2=H1 rolls; all pass."),
    "documents": [
        D("b98957d5", "FY ended 2025-12-31 audited (label 2025|FY correct for this file; the 2025|FY slot also holds the FY2024 scan 1ae33a08)", True, 8, 9, 11, 6, 7, 9,
          "text layer, income statement page rendered"),
        D("1ae33a08", "FY ended 2024-12-31 audited, as originally filed (collector label 2025|FY)", False, 8, 9, 11, 6, 7, 9),
        D("97801f99", "FY ended 2023-12-31 audited, as originally filed (collector label 2024|FY)", False, 8, 9, 11, 6, 7, 9),
        D("b19fb27e", "FY ended 2022-12-31 audited, as originally filed (label 2022|FY correct)", True, 9, 10, 12, 7, 8, 10),
        D("5c2e8a91", "3M ended 2026-03-31 reviewed", True, 4, 5, 7, 2, 3, 5, "visual (statement pages textless images inside a PDF whose p3 review report is text)"),
        D("3c77bb99", "3M and 6M ended 2026-06-30 reviewed", True, 4, 5, 7, 2, 3, 5),
    ],
    "identified": {
        "fa59d193": ("FY ended 2021-12-31 (cover read; label 2021|FY correct)", "whole-file scan, 44 pages; not transcribed; FY2021 IS, BS and CF are known from the FY2022 filing's comparative column"),
        "c239b2bf": ("FY ended 2022-12-31 (cover read and BS page p9 compared visually with b19fb27e)", "copy of the FY2022 file mislabelled 2023|FY: BS page identical; FY2023 is in 97801f99 (labelled 2024|FY)"),
        "fb80ac00": ("FY ended 2025-12-31 (cover read; label 2026|FY)", "whole-file scan twin of the born-digital FY2025 file b98957d5; not compared page by page"),
        "126ad981": ar("9M ended 2021-09-30"), "176d442c": ar("9M ended 2022-09-30"), "60407be6": ar("9M ended 2023-09-30"),
        "edc07db1": ar("9M ended 2024-09-30"), "7fee7dc1": ar("9M ended 2025-09-30"),
        "5d2e3277": ar("6M ended 2021-06-30"), "327b0a86": ar("6M ended 2022-06-30"), "08b8b480": ar("6M ended 2023-06-30"),
        "85f9a3b4": ar("6M ended 2024-06-30"), "51f02a8e": ar("6M ended 2025-06-30"),
        "fb36a34b": ar("3M ended 2021-03-31"), "03179729": ar("3M ended 2022-03-31"), "00e5d306": ar("3M ended 2023-03-31"),
        "f9aca4f4": ar("3M ended 2024-03-31"), "6b30918c": ar("3M ended 2025-03-31"),
        "6fe356f5": en("3M and 9M ended 2021-09-30"), "58b5adfc": en("3M and 6M ended 2021-06-30"), "b6039442": en("3M ended 2021-03-31"),
        "4df22aa9": en("3M and 9M ended 2022-09-30"), "075fa07c": en("3M and 6M ended 2022-06-30"), "f2d2a9a4": en("3M ended 2022-03-31"),
        "e44b8555": en("3M and 9M ended 2023-09-30"), "e85337e9": en("3M and 6M ended 2023-06-30"), "b250a200": en("3M ended 2023-03-31"),
        "28471bd0": en("3M and 9M ended 2024-09-30"), "18eefb13": en("3M and 6M ended 2024-06-30"), "ac56e053": en("3M ended 2024-03-31"),
        "11816cf8": en("3M and 9M ended 2025-09-30"), "ef679b1b": en("3M and 6M ended 2025-06-30", "; the 2025 restated comparative is in the H1 2026 filing"),
        "034089b9": en("3M ended 2025-03-31", "; the restated Q1 2025 comparative is in the Q1 2026 filing"),
    },
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_6_filings_with_material_restatements_recorded",
            "summary": ("Headline BS, income and cash-flow values (full SAR) transcribed from pages for FY2022, FY2023, FY2024 (original), FY2025, Q1 2026 and H1 2026 with their comparative "
                        "columns and the Q2 columns. Identities hold with zero difference: total assets = liabilities + equity; CFO+CFI+CFF = net change; opening + net change = "
                        "closing bank balances (equal to balance-sheet bank balances throughout); revenue - cost = gross profit; profit before zakat less zakat = net income; "
                        "Q1+Q2=H1 for revenue, gross profit and net income in 2026 and in the restated 2025 comparatives. No non-controlling interest. Selected: FY2025 revenue 25,760,827,915, "
                        "net income 421,845,770, total assets 9,453,976,563, CFO 1,096,504,986; H1 2026 revenue 14,158,762,289, net income 234,059,661, total assets 10,067,331,024. "
                        "FY2024 was RESTATED (note 37): as originally filed net income 338,047,048, total assets 8,443,323,301, equity 1,479,487,425, CFO 1,397,899,452, EPS 3.38; as restated in the FY2025 "
                        "filing 344,650,993, 8,380,633,196, 1,416,797,320, 1,379,150,772 and 3.44 (see defect B009-4200-4). Both versions are in the transcript with a restated flag; none substituted."),
            "not_read": [
                "notes in every file (note 37 and note 25 restatement notes in particular)",
                "equity statements except Q1 2026 p6",
                "FY2021 own file fa59d193 and the FY2025 scan fb80ac00 (FY2021 known only from the FY2022 filing's comparative column)",
                "all 2021-2025 interim filings (English and Arabic scans); Q1 2025 and H1 2025 are known only as restated comparatives in the 2026 filings",
            ],
        },
        "document_completeness": {
            "status": "primary_statements_present_in_every_file_opened_inventory_classification_wrong_for_38_whole_file_scans",
            "summary": ("Every file opened (annual FY2022 to FY2025, Q1 and H1 2026) holds a statement of financial position, comprehensive income, changes in equity and cash flows. 37 of 39 files "
                        "are whole-file scans with no text layer and the inventory classes them scanned_unreadable with no statement pages; only b98957d5 (FY2025) is born digital. "
                        "Fifteen Arabic twin interims have no fiscal year in the inventory. A duplicate of the FY2022 file (c239b2bf) occupies the 2023|FY slot, so the FY2023 file sits in 2024|FY."),
            "defect_ids": ["B009-4200-1", "B009-4200-2", "B009-4200-3", "B009-4200-5"],
        },
        "company_coverage": {
            "status": "contiguous_2021Q1_to_2026H1_files_all_periods_present",
            "present_in_files_by_page_derived_period": [
                "2021|Q1", "2021|H1", "2021|9M", "2021|FY", "2022|Q1", "2022|H1", "2022|9M", "2022|FY", "2023|Q1", "2023|H1", "2023|9M", "2023|FY",
                "2024|Q1", "2024|H1", "2024|9M", "2024|FY", "2025|Q1", "2025|H1", "2025|9M", "2025|FY", "2026|Q1", "2026|H1",
            ],
            "values_verified_from_own_pages": ["2022|FY", "2023|FY", "2024|FY (original)", "2025|FY", "2026|Q1", "2026|H1"],
            "values_known_only_as_comparatives": [
                "2021|FY (FY2022 filing)", "2025|Q1 restated (Q1 2026 filing)", "2025|H1 six months and Q2 restated (H1 2026 filing)",
                "2024|FY restated (FY2025 filing)",
            ],
            "values_not_read": ["2021|Q1", "2021|H1", "2021|9M", "2021|FY own file", "2022|Q1", "2022|H1", "2022|9M", "2023|Q1", "2023|H1", "2023|9M",
                                "2024|Q1", "2024|H1", "2024|9M", "2025|Q1 original", "2025|H1 original", "2025|9M"],
            "missing": ["everything before 2021 Q1 (no files)"],
            "inventory_corrections": ("annual FS are labelled by publication year except FY2022 and FY2021: 2024|FY is FY2023, 2025|FY holds both FY2024 (scan 1ae33a08) and FY2025 (b98957d5), "
                                      "2026|FY is the FY2025 scan fb80ac00, and 2023|FY (c239b2bf) is a copy of FY2022. 15 files with fiscal year None are Arabic interims for 2021 to 2025. "
                                      "Interim files are labelled by the period they report. Page-derived: 22 distinct periods 2021 Q1 to 2026 H1 each have at least one file."),
        },
    },
    "defects": [
        {"id": "B009-4200-1", "class": "period_label_annual_mixed_and_duplicate", "severity": "medium",
         "evidence": "Covers read: 97801f99 (2024|FY) is 31 December 2023; 1ae33a08 and b98957d5 (both 2025|FY) are 31 December 2024 and 31 December 2025; fb80ac00 (2026|FY) is 31 December 2025; c239b2bf (2023|FY) has the FY2022 cover and a BS page identical to b19fb27e (2022|FY). No file in the 2023|FY slot reports FY2023."},
        {"id": "B009-4200-2", "class": "whole_file_scans_classed_unreadable", "severity": "high",
         "evidence": "37 of 39 files have no text layer on any page; the inventory lists no statement pages for them. Rendered pages are legible and contain all four primary statements. Q1 2026 5c2e8a91 is a text PDF whose statement pages p4-9 are images."},
        {"id": "B009-4200-3", "class": "language_twins_without_fiscal_year", "severity": "low",
         "evidence": "15 Arabic interim files (126ad981, 176d442c, 60407be6, edc07db1, 7fee7dc1, 5d2e3277, 327b0a86, 08b8b480, 85f9a3b4, 51f02a8e, fb36a34b, 03179729, 00e5d306, f9aca4f4, 6b30918c) carry fiscal_year None; covers give periods 2021 to 2025 Q1/H1/9M."},
        {"id": "B009-4200-4", "class": "restated_or_represented_comparatives", "severity": "high",
         "evidence": ("(a) FY2024 restated (note 37) in the FY2025 filing: cost of revenue 18,477,334,023 -> 18,470,730,078, gross profit 811,218,990 -> 817,822,935, income before zakat 346,386,115 -> 352,990,060, "
                      "net income 338,047,048 -> 344,650,993, EPS 3.38 -> 3.44; total assets 8,443,323,301 -> 8,380,633,196, equity 1,479,487,425 -> 1,416,797,320; opening Jan 2024 retained earnings reduced by 69,294,050 "
                      "(total assets 7,506,130,159 -> 7,436,836,109, equity 1,235,919,779 -> 1,166,625,729); CFO 1,397,899,452 -> 1,379,150,772 and CFI -653,203,691 -> -634,455,011 (finance income received 18,748,680 moved to investing; capex and CFF unchanged). "
                      "(b) FY2022 re-presented in the FY2023 filing: total assets 6,315,582,096 -> 6,358,693,699, total liabilities 5,206,237,770 -> 5,249,349,373, CFO 716,541,761 -> 772,759,064, CFF -325,155,162 -> -382,302,262, income from operations 370,841,922 -> 363,021,749; net income 241,826,918 and equity unchanged. "
                      "(c) 2023 EPS 3.74 -> 2.81 in the FY2024 filing after the 1-for-3 bonus issue (share capital 750m -> 1,000m). "
                      "(d) Q1 2025 and H1 2025 marked restated (note 25) in the 2026 filings (Q1 2025 net income 101,063,763; 6M 197,731,713); the originals were not read. Every version is in the transcript or listed as unread.")},
        {"id": "B009-4200-5", "class": "page_header_mismatch", "severity": "low",
         "evidence": "FY2025 b98957d5 pdf p9 (printed 7) is the statement of profit or loss and comprehensive income but its running header reads STATEMENT OF CHANGES IN EQUITY; the equity statement is pdf p10. A parser keyed on headers would misfile it."},
    ],
    "unread_items": [
        "notes in all files, including notes 25 and 37 (restatement)",
        "equity statements (except Q1 2026)",
        "2021 to 2025 interim filings in English and Arabic (see files_not_audited_for_values)",
        "FY2021 own file and FY2025 scan twin",
        "Q1 2025 and H1 2025 originals (before restatement)",
        "nothing before 2021 Q1: no files",
    ],
    "conclusion": ("NOT claimed complete. Six filings value-verified from rendered pages with material restatements recorded (FY2024 note 37); all 22 periods 2021 Q1 to 2026 H1 "
                   "have a file but 16 are not value-read in their own filing; 37 scans are misclassified as unreadable; no FY2023-labelled file holds FY2023."),
}
mkrecord.build(spec)
