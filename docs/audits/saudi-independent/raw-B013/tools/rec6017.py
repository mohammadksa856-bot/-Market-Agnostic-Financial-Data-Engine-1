"""Builds raw-B013/6017.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("b9421e85", "FY ended 2025-12-31 audited consolidated FS, standalone whole-file scan (collector label 2026|FY = publication year)", False,
        dict(bs=8, is_=9, cf=11), dict(bs=6, is_=7, cf=9), "visual (64 textless pages, rendered and read)"),
    doc("d9587e85", "Annual Report 2025 (English) carrying the FY2025 audited FS (label 2025|FY correct)", True,
        dict(bs=95, is_=95, cf="96-97"), dict(bs="188-189", is_="188-189", cf="192-193"), "text layer",
        "ties to the standalone scan except SAR 1-2 rounding differences on other income, operating profit, finance costs, proceeds due to customers and accrued expenses"),
    doc("20131ae2", "FY ended 2024-12-31 audited consolidated FS, standalone text (collector label 2025|FY = publication year)", False,
        dict(bs=7, is_=8, cf=10), dict(bs=5, is_=6, cf=8), "text layer"),
    doc("cbe8b249", "FY ended 2023-12-31 audited consolidated FS, standalone; statement pages image-only (collector label 2024|FY = publication year)", False,
        dict(bs=7, is_=8, cf=10), dict(bs=5, is_=6, cf=8), "visual (pdf p7-10 textless although inventory class is financial_statements)"),
    doc("115c111e", "Annual Report 2022 (English) carrying the FY2022 audited FS (label 2022|FY correct)", True,
        dict(bs=124, is_=125, cf=128), dict(bs=122, is_=123, cf=126), "text layer"),
    doc("401e9014", "3M and 6M ended 2025-06-30 reviewed (inventory class partial_statements; BS p4, IS p5, CF p7 are present)", True,
        dict(bs=4, is_=5, cf=7), dict(bs=1, is_=2, cf=4), "text layer"),
    doc("1e407fc6", "3M and 6M ended 2026-06-30 reviewed (inventory class partial_statements; BS p4, IS p5, CF p7 are present)", True,
        dict(bs=4, is_=5, cf=7), dict(bs=2, is_=3, cf=5), "text layer"),
    doc("707a731f", "3M ended 2026-03-31 reviewed (inventory class partial_statements; BS p4, IS p5, CF p7 are present)", True,
        dict(bs=4, is_=5, cf=7), dict(bs=2, is_=3, cf=5), "text layer"),
]
for d in documents:
    d["pdf_pages"] = {("is" if k == "is_" else k): v for k, v in d["pdf_pages"].items()}
    d["printed_pages"] = {("is" if k == "is_" else k): v for k, v in d["printed_pages"].items()}

identified = {
    "9671e9d0": ("FY ended 2021-12-31 Arabic audited FS (cover read; label has no period slot)", "Arabic twin of the FY2021 FS; not transcribed"),
    "3c4a0470": ("FY ended 2021-12-31 audited FS, English, whole-file scan (cover read)", "scan, 43 pages textless; not transcribed; FY2021 values known only as the comparative column in the FY2022 annual report"),
    "1c5f2657": ("Annual Report 2021 (1442H), English (cover text)", "contains FS; not transcribed"),
    "a50fda5a": ("Annual Report 2021, Arabic twin (cover text)", "not transcribed"),
    "a5f55fee": ("3M and 9M ended 2021-09-30 (cover read, English scan)", "whole-file scan; not transcribed"),
    "f1bf9a70": ("3M and 9M ended 2021-09-30, Arabic twin (cover read)", "scan/other; not transcribed"),
    "20340c2d": ("3M ended 2021-03-31 (cover read, English scan)", "whole-file scan; not transcribed"),
    "173b86c8": ("3M ended 2021-03-31, Arabic twin (cover read)", "not transcribed"),
    "6a873d51": ("Annual Report 2022, Arabic twin", "not transcribed"),
    "dd39d396": ("3M and 6M ended 2022-06-30 (cover text)", "text FS present; not transcribed"),
    "45e8750a": ("Annual Report 2023, English (label 2023|FY correct)", "contains FS; not transcribed (FY2023 values taken from the standalone FS cbe8b249)"),
    "cf05c4f6": ("Annual Report 2023, Arabic twin", "not transcribed"),
    "a1c9b64e": ("FY ended 2022-12-31 audited FS, English, whole-file scan (cover read); collector label 2023|FY is one year late", "scan 48 pages textless; not transcribed; FY2022 values are read from the FY2022 annual report and agree with the FY2023 comparatives"),
    "5765e521": ("3M and 6M ended 2023-06-30 (cover text)", "text FS present; not transcribed"),
    "5c9f4d81": ("H1 2023 results announcement (8 pages)", "announcement, not statements"),
    "f09b1e06": ("H1 2023 earnings-call presentation (cover image)", "presentation, not statements"),
    "08d6f0e3": ("Q3 2024 consolidated interim results announcement, Arabic (cover text)", "announcement, not statements; label has no period slot"),
    "ac541842": ("Jahez Group presentation, period not identified (cover is a logo)", "presentation; period unverified; label has no period slot"),
    "40714a01": ("3M and 9M ended 2024-09-30, English (cover text)", "not transcribed"),
    "8ecf9ead": ("3M and 9M ended 2024-09 Arabic twin (cover text, font-encoded Arabic)", "not transcribed"),
    "aa9f730f": ("3M and 6M ended 2024-06-30, English (cover text)", "not transcribed; 6M 2024 and Q2 2024 known from the H1 2025 comparatives"),
    "3520c1fa": ("9M 2025 investor presentation", "presentation"),
    "8875c683": ("3M and 9M ended 2025-09-30, Arabic (cover text)", "not transcribed"),
    "a01f2b20": ("3M and 9M ended 2025-09-30, English (cover text)", "not transcribed"),
    "1df358ca": ("Results presentation labelled 2025|FY (15 pages)", "presentation; not statements"),
    "4b45d999": ("Annual Report 2024, English; collector label 2025|FY = publication year", "contains FS for FY2024; not transcribed (FY2024 values read from standalone FS 20131ae2)"),
    "67d08e3a": ("Annual Report 2024, Arabic twin; label 2025|FY", "not transcribed"),
    "8eab568d": ("Annual Report 2025, Arabic twin of d9587e85 (cover text)", "classed annual_report_no_statements by the inventory though its sibling carries FS; not transcribed"),
    "c6efe6fc": ("FY2025 results announcement, Arabic (cover text)", "announcement; not statements"),
    "3fdcd6b4": ("H1 2025 presentation", "presentation"),
    "8cbc7cce": ("3M and 6M ended 2025-06-30, Arabic twin", "not transcribed"),
    "61a37bda": ("Q1 2025 presentation", "presentation"),
    "8e04397e": ("3M ended 2025-03-31, Arabic", "not transcribed; Q1 2025 income and cash flow are known from the Q1 2026 comparatives"),
    "c2b379c0": ("3M ended 2025-03-31, English (cover text)", "not transcribed"),
    "84626d33": ("H1 2026 results announcement", "announcement"),
    "e23ee07f": ("3M and 6M ended 2026-06-30, Arabic twin (font-encoded)", "not transcribed"),
    "fedb8d5c": ("H1 2026 presentation", "presentation"),
    "482cce52": ("Q1 2026 presentation", "presentation"),
    "4ae12a55": ("3M ended 2026-03-31, Arabic twin", "not transcribed"),
}

spec = dict(
    symbol="6017", name="JAHEZ (Jahez International Company for Information Systems Technology)",
    method=("SHA-256 recomputed for every audited file. FY2025 standalone FS (whole-file scan, 64 textless pages) and the FY2023 FS (image-only statement pages) were rendered and read by eye; "
            "FY2024, FY2022 annual report, H1 2025, H1 2026, Q1 2026 and the FY2025 annual-report copy were read from the text layer. tools/check_transcripts.py over transcripts/6017.json checks "
            "balance-sheet identity, cash-flow sum and roll, gross profit, profit before zakat to net profit, owners + non-controlling interests, cross-filing agreement of comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls; all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_8_filings_declared_differences_noted",
            summary=("Headline BS, income and cash-flow values (full SAR) transcribed from pages for FY2025 (scan and annual-report copy), FY2024, FY2023, FY2022 (with FY2021 comparatives), H1 2025 (with H1/Q2 2024), "
                     "H1 2026 (with Q2) and Q1 2026 (with Q1 2025). All identities hold with zero difference and every comparative column agrees with the earlier filing of the same period except declared items. "
                     "FY2025: revenue 2,323,639,572, net profit 57,945,540 (owners 72,974,832, NCI -15,029,292), total assets 2,452,458,554, CFO 99,834,675, closing cash 428,423,257 (after a 725,894,842 subsidiary acquisition; "
                     "goodwill and intangibles rose from 102.2m to 1,062.7m). FY2024: revenue 2,218,662,735, net profit 184,218,145. FY2023: revenue 1,784,755,283, net 118,767,609. FY2022: revenue 1,602,476,839, net 56,523,290. "
                     "H1 2026: revenue 1,488,075,881, net loss 33,860,456, Q2 2026 net loss 22,191,542; Q1 2026 + Q2 2026 = H1 2026 for revenue, net income and parent income, and Q1 2025 + Q2 2025 = H1 2025 for revenue and net income. "
                     "Declared differences: FY2022 EPS 5.7 (FY2022 annual report) versus 0.29 (FY2023 filing comparative), cause not verified; FY2025 annual-report copy differs from the standalone FS by SAR 1-2 rounding on "
                     "other income, operating profit and finance costs. Interim cash flow: Q1 2026 CFO 157,126,724 versus H1 2026 CFO 140,165,038 (Q2 by subtraction would be -16,961,686) and the H1 statement carries different "
                     "line items (disposal of intangible assets presented in investing, no 'loss from intangible assets' add-back), so a Q2 cash flow by subtraction is NOT validated."),
            not_read=["notes in every file", "statements of changes in equity (except FY2025 spread glimpsed)", "all annual reports other than the FY2025 and FY2022 statement pages",
                      "every Arabic twin", "FY2021 own FS (scan and Arabic), FY2022 standalone scan", "Q1/9M 2021, H1 2022, H1/9M 2023, H1/9M 2024, Q1 and 9M 2025 filings",
                      "H1 2026 pdf p36-37 textless"]),
        document_completeness=dict(
            status="primary_statements_present_for_FY2021_to_FY2025_and_interims_2021_to_2026_H1_some_image_only_or_scanned",
            summary=("Statement-level pages opened: FY2025 standalone FS is a whole-file scan (inventory: scanned_unreadable, label 2026|FY); FY2023 FS statements are image-only pages inside a file the inventory "
                     "calls financial_statements (statement_pages not detected); the FY2022 standalone FS (a1c9b64e) is a scan labelled 2023|FY; FY2021 standalone FS is a scan; H1 2026, H1 2025 and Q1 2026 English files are "
                     "classed partial_statements although BS, IS and CF are present. No missing statement was found in the files opened."),
            defect_ids=["B013-6017-1", "B013-6017-2", "B013-6017-3", "B013-6017-4"]),
        company_coverage=dict(
            status="annual_FY2021_to_FY2025_and_interims_with_gaps_by_page_derived_period",
            present_in_files_by_page_derived_period=[
                "FY2021 (scan, Arabic, annual report)", "FY2022 (annual report, scan labelled 2023|FY)", "FY2023 (FS, annual reports)", "FY2024 (FS, annual reports)", "FY2025 (scan FS, annual report)",
                "2021 Q1 (scan, Arabic)", "2021 9M (scan, Arabic)", "2022 H1", "2023 H1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            values_verified_from_own_pages=["FY2022 (annual report)", "FY2023", "FY2024", "FY2025", "2025 H1", "2026 Q1", "2026 H1"],
            values_known_only_as_comparatives=["FY2021 (FY2022 annual report)", "2024 H1 and Q2 (H1 2025 filing)", "2025 Q1 and Q2 (Q1 2026 and H1 2026 filings)"],
            values_not_read=["FY2021 own FS", "2021 Q1", "2021 9M", "2022 H1", "2023 H1", "2024 H1 original", "2024 9M", "2025 Q1 original", "2025 9M"],
            missing=["2021 H1", "2022 Q1", "2022 9M", "2023 Q1", "2023 9M", "2024 Q1", "everything before FY2021 (listed on Nomu in 2021, moved to the main market later)"],
            inventory_corrections=("Fiscal-year labels mix conventions: FS files carry the publication year (FY2023 FS 2024|FY, FY2024 FS 2025|FY, FY2025 FS 2026|FY, FY2022 FS 2023|FY) while annual reports carry the "
                                   "fiscal year (AR2022 2022|FY, AR2023 2023|FY, AR2025 2025|FY) except AR2024 labelled 2025|FY. The 2025|FY slot therefore holds FY2024 FS, FY2024 annual reports (en, ar) "
                                   "and FY2025 annual reports (en, ar) at once. Two files have no period slot (2024|None)."))),
    defects=[
        dict(id="B013-6017-1", **{"class": "image_only_or_scanned_statements_flagged_partial_or_unreadable"}, severity="high",
             evidence="b9421e85 (FY2025 FS) is a 64-page whole-file scan classed scanned_unreadable with label 2026|FY; cbe8b249 (FY2023 FS) pdf p7-10 are image-only inside a file classed financial_statements; "
                      "a1c9b64e (FY2022 FS) and 3c4a0470 (FY2021 FS) are scans; 401e9014, 1e407fc6, 707a731f are classed partial_statements though BS, IS and CF are on pdf p4, p5, p7."),
        dict(id="B013-6017-2", **{"class": "fiscal_year_label_mismatch"}, severity="medium",
             evidence="FS files labelled with the publication year (2024|FY holds FY2023, 2025|FY holds FY2024, 2026|FY holds FY2025, 2023|FY scan holds FY2022) while annual reports use the fiscal year; the 2025|FY slot holds four different annual documents."),
        dict(id="B013-6017-3", **{"class": "restated_or_represented_comparatives"}, severity="low",
             evidence="FY2022 EPS 5.7 (FY2022 annual report) versus 0.29 (FY2023 filing comparative); both recorded. All other FY2022 to FY2025 comparatives agree between filings."),
        dict(id="B013-6017-4", **{"class": "duplicate_registry_symbol_and_arabic_twins"}, severity="medium",
             evidence="36 of the 47 files in archive/SA/6017 are byte-identical (same SHA-256 file names) to all 36 files in archive/SA/9526, which has no raw-coverage inventory record and is absent from live_tadawul_list.json; "
                      "the 6017 annual report 2022 states Jahez was listed on Nomu (parallel market), so 9526 is consistent with a former Nomu registry symbol (inferred, not verified). The 11 files only under 6017 are b9421e85 (FY2025 FS), "
                      "5765e521 (H1 2023), dd39d396 (H1 2022), aa9f730f (H1 2024), 5c9f4d81 and six presentations; entity verified as Jahez from the statement pages. Arabic twins and English/Arabic pairs are counted as separate period files by the inventory (duplicate_candidates flags 6 files)."),
        dict(id="B013-6017-5", **{"class": "interim_cash_flow_not_comparable_for_subtraction"}, severity="low",
             evidence="Q1 2026 CFO 157,126,724 versus H1 2026 CFO 140,165,038; line items differ between the Q1 and H1 cash-flow statements, so Q2 by subtraction is not validated."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "Arabic twins", "FY2021 own FS", "interims 2021 to 2024 and Q1/9M 2025 filings (see files_not_audited_for_values)",
                  "FY2021 and FY2022 standalone scans", "annual reports other than statement pages cited", "H1 2026 pdf p36-37", "period of ac541842 (presentation, logo cover)"],
    conclusion=("NOT claimed complete. Eight filings value-verified from pages (FY2022 to FY2025, H1 2025, Q1 and H1 2026, plus the FY2025 annual-report copy); FY2021 known only as comparatives; "
                "gaps 2022 Q1/9M, 2023 Q1/9M, 2024 Q1 have no file; 39 further files are not value-read; 36 files are shared byte-for-byte with registry symbol 9526."),
)
mkrecord.build(spec)
