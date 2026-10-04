"""Builds raw-B015/8190.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SR'000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("edae80ae", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 9, "is": 10, "cf": "14-15"}, {"bs": 7, "is": 8, "cf": "12-13"},
        "text layer (pdf p3-8 auditor report textless; statements born digital)",
        "net loss 256,220; equity 24,579; auditor and note 1 carry a material uncertainty related to going concern (pdf p4-8 report, p16-17 note)"),
    doc("47b9867c", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 10, "is": 11, "cf": "15-16"}, {"bs": 8, "is": 9, "cf": "13-14"},
        "visual (statement pages pdf p9-16 are image-only inside an annual_report_with_state file; text layer is the annual report only)"),
    doc("cc813d13", "FY ended 2023-12-31 audited FS, first IFRS 17 year, with 2022 restated comparatives (label 2024|FY = publication year)", False, {"bs": 12, "is": 13, "cf": "17-18"}, {"bs": 11, "is": 12, "cf": "16-17"},
        "text layer", "2023 balance sheet and cash flow are re-presented in the FY2024 filing; see defect B015-8190-3"),
    doc("f933d77c", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", False, {"bs": "9-10", "is": "11-12", "cf": "15-16"}, {"bs": "7-8", "is": "9-10", "cf": "13-14"},
        "visual (statement pages textless)", "IFRS 4 presentation (gross premiums written, net underwriting result); restated to IFRS 17 in the FY2023 filing: net loss -42,861 to -55,482, total assets 1,060,892 to 747,546, equity 205,633 to 256,151"),
    doc("fae9bdf6", "3M and 6M ended 2026-06-30 reviewed (label 2026|H1 correct); latest period in the collection", True, {"bs": 5, "is": 6, "cf": 9}, {"bs": 3, "is": 4, "cf": 7},
        "text layer; cash flow page also rendered and read", "net loss 7,737 (3M 872); statutory deposit 59,989 released in financing (60,000); cash 80,267; auditor going-concern paragraph at pdf p4"),
    doc("695faccd", "3M ended 2026-03-31 reviewed (label 2026|Q1 correct)", True, {"bs": 5, "is": 6, "cf": 9}, {"bs": 4, "is": 5, "cf": 8}, "text layer"),
]
identified = {
    "8d0689d1": ("3M and 9M ended 2022-09-30 IFRS 4 interim (cover text; pdf p5-12 textless)", "not transcribed"),
    "29361462": ("3M and 6M ended 2022-06-30 IFRS 4 interim (cover text; pdf p5-12 textless)", "not transcribed"),
    "8227c800": ("3M ended 2022-03-31 IFRS 4 interim (cover text; pdf p4-11 textless)", "not transcribed"),
    "3b09a3f9": ("3M and 9M ended 2023-09-30 interim (cover text)", "not transcribed"),
    "c92f9bed": ("3M and 6M ended 2023-06-30 interim (cover text)", "not transcribed"),
    "ebf3da95": ("3M ended 2023-03-31 interim (cover text; company name misspelled UNITED COOPERATIVE ASSURACE on the cover)", "not transcribed"),
    "5e99b01e": ("3M and 9M ended 2024-09-30 interim (cover text)", "not transcribed"),
    "89a049b0": ("3M and 6M ended 2024-06-30 interim (cover text)", "not transcribed"),
    "2f21e3e3": ("3M ended 2024-03-31 interim (cover text)", "not transcribed"),
    "2c3e3e82": ("3M and 9M ended 2025-09-30 interim (cover text)", "not transcribed"),
    "9eac335a": ("3M and 6M ended 2025-06-30 interim (cover text)", "not transcribed; H1 2025 comparatives read in the H1 2026 filing"),
    "dc6893ef": ("3M ended 2025-03-31 interim (cover text)", "not transcribed; Q1 2025 comparatives read in the Q1 2026 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatements_and_representations_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) from FY2025, FY2024, FY2023 (with 2022 restated), FY2022 as issued under IFRS 4, H1 2026 (with 3M columns) and Q1 2026. All identities hold exactly; comparatives agree across filings except declared items. FY2025: insurance revenue 858,313, loss before zakat -259,224, net loss -256,220 (EPS -6.41), total assets 788,744, equity 24,579 (after accumulated losses of 451,837 against 400,000 capital), CFO -183,275, closing cash 23,743; the auditor reports a material uncertainty related to going concern. FY2024 net loss -15,055; FY2023 net profit 5,292; FY2022 restated net loss -55,482. H1 2026: net loss -7,737 (Q2 -872), equity 16,842; Q1 2026 + Q2 2026 = H1 2026 and Q1 2025 + Q2 2025 = H1 2025 for revenue, loss before zakat and net loss (all pass). Declared differences: (1) IFRS 17/9 transition: FY2022 as issued (net loss -42,861, total assets 1,060,892, total liabilities 855,259, equity 205,633, cash 83,980) versus restated (net loss -55,482, total assets 747,546, liabilities 491,395, equity 256,151, cash 83,964). (2) FY2023 balance sheet and cash flow re-presented in the FY2024 filing: total assets 629,846 versus 797,762, total liabilities 364,691 versus 532,607 (gross versus netted insurance contracts), CFO 28,546 versus 21,071, CFI 12,679 versus 20,154; equity, revenue, net profit unchanged. Interim cash flow: Q1 2026 CFO -17,342 versus H1 2026 CFO -14,389 (Q2 by subtraction +2,953) and Q1 2025 CFO -820 versus H1 2025 -61,480, with different line items (term deposits, commission received, statutory deposit release classified in financing), so a Q2 cash flow by subtraction is NOT validated. H1 2026 prints payments for purchases of property and equipment as +361 (sign as printed, confirmed on the rendered page).",
        "not_read": ["notes in every file (except going-concern passages)", "statements of changes in equity (FY2025 pdf p13 and H1 2026 p8 text seen, not transcribed)", "all other interims", "auditor reports in full"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_opened_two_are_image_only",
        "summary": "All six audited files carry balance sheet, income statement and cash-flow statement. FY2024 (pdf p9-16) and FY2022 (pdf p3-16) statement pages are image-only inside files classed annual_report_with_state and financial_statements; the FY2025, FY2023, H1 2026 and Q1 2026 statements are born digital. Interims 2022 Q1/H1/9M have textless statement pages. FY2025 has two Saudi Exchange results announcements (ids 94682 and 94062 in the inventory state) but a single file.",
        "defect_ids": ["B015-8190-1", "B015-8190-2", "B015-8190-3", "B015-8190-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_to_2026_H1_with_gaps_by_page_derived_period",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)",
                                                    "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "2025 Q1, Q2, H1 (2026 filings)"],
        "values_not_read": ["2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M", "2025 Q1/H1/9M originals"],
        "missing": ["FY2021 and earlier (no file)", "2021 and earlier interims", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in all four FS files (2023|FY holds FY2022, 2024|FY FY2023, 2025|FY FY2024, 2026|FY FY2025); the inventory period_mismatch flags for these files are therefore correct detections, not data errors. Interim labels match page periods.",
    },
}
defects = [
    {"id": "B015-8190-1", "class": "image_only_or_scanned_statements_flagged_as_present", "severity": "medium",
     "evidence": "47b9867c pdf p9-16 and f933d77c pdf p3-16 are image-only (inventory classes annual_report_with_state and financial_statements with statement_pages taken from notes); 2022 interims 8d0689d1, 29361462, 8227c800 have textless pages 4-12."},
    {"id": "B015-8190-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "f933d77c FY2022 labelled 2023|FY, cc813d13 FY2023 labelled 2024|FY, 47b9867c FY2024 labelled 2025|FY, edae80ae FY2025 labelled 2026|FY. A label reader would shift every annual value by one year."},
    {"id": "B015-8190-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17/9 transition: FY2022 net loss -42,861 as issued (f933d77c pdf p12) versus -55,482 (cc813d13 pdf p13); total assets 1,060,892 versus 747,546; equity 205,633 versus 256,151. FY2023 balance sheet re-presented in FY2024: total assets 629,846 (cc813d13 pdf p12) versus 797,762 (47b9867c pdf p10); CFO 28,546 versus 21,071. Both recorded, none substituted."},
    {"id": "B015-8190-4", "class": "going_concern_and_capital_deterioration", "severity": "medium",
     "evidence": "FY2025 net loss -256,220 and equity 24,579 (edae80ae pdf p9-10) with a material uncertainty related to going concern (pdf p16-17); H1 2026 equity 16,842 and a 60,000 statutory deposit release classified in financing (fae9bdf6 pdf p9). Values are as printed; downstream consumers should not treat the series as ordinary earnings history."},
]
unread = ["notes (except going-concern passages)", "statements of changes in equity", "12 interim filings 2022 Q1 to 2025 9M (identified by cover only)", "FY2021 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Six filings value-verified from pages (FY2022 as issued, FY2023, FY2024, FY2025, Q1 2026, H1 2026); IFRS 17 restatement and FY2023 re-presentation declared with both values; "
              "12 interim filings identified by cover but not value-read; FY2021 and earlier absent.")
mkrecord.build(dict(
    symbol="8190", name="UNITED COOPERATIVE ASSURANCE COMPANY (UCA)", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. FY2024 and FY2022 statement pages (image-only) were rendered and read by eye; FY2025, FY2023, H1 2026 and Q1 2026 were read from the text layer and the H1 2026 cash flow also by eye. "
            "tools/check_transcripts.py over transcripts/8190.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat/tax to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, loss before zakat and net loss (2026 and 2025); all pass.")))
