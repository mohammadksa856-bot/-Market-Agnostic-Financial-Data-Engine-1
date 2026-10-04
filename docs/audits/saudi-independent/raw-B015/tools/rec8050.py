"""Builds raw-B015/8050.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SAR 000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("28ce63c0", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "13-14"}, {"bs": 7, "is": 8, "cf": "12-13"},
        "visual (statement pages image-only, pdf p8-14 textless); note 31 comparative restatement read from text at pdf p111",
        "FY2024 cash flow restated for IAS 7 commission-income presentation (note 31)"),
    doc("ded8b2a2", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 13}, {"bs": 7, "is": 8, "cf": 12}, "visual (image-only, pdf p3-14 textless)"),
    doc("44f0c863", "FY ended 2023-12-31 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated (label 2024|FY = publication year)", False, {"bs": 10, "is": 11, "cf": "15-16"}, {"bs": 9, "is": 10, "cf": "14-15"},
        "visual (image-only, pdf p9-16 textless)"),
    doc("16733245", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year)", False, {"bs": 8, "is": "9-10", "cf": 13}, {"bs": 6, "is": "7-8", "cf": 11}, "visual (image-only, pdf p3-13 textless)",
        "IFRS 4 presentation; restated to IFRS 17 in the FY2023 filing: net loss -58,327 to -38,866, total assets 765,970 to 666,810, equity 37,768 to 60,856, CFO 77,841 to 69,463, CFI -62,057 to -53,679. Both declared; neither substituted. pdf p9 (premiums/underwriting page) not transcribed."),
    doc("c1bacc8f", "3M and 6M ended 2026-06-30 reviewed interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 2, "is": 3, "cf": 6},
        "visual (pages carry only an e-signature stamp as text)", "income columns are three-month 2026, three-month 2025, six-month 2026, six-month 2025"),
    doc("fdad4f76", "3M ended 2026-03-31 reviewed interim (label 2026|Q1 correct)", True, {"is": 5, "cf": 8}, {"is": 4, "cf": 7}, "visual (image-only, pdf p4-8 textless); balance sheet not transcribed",
        "2025 comparative cash flow marked Restated - Note 24"),
]
identified = {
    "529ec98f": ("3M and 9M ended 2022-09-30 IFRS 4 interim (cover text)", "not transcribed"),
    "4ea34e59": ("3M and 6M ended 2022-06-30 IFRS 4 interim (cover text)", "not transcribed"),
    "f6490302": ("3M ended 2022-03-31 IFRS 4 interim (cover text)", "not transcribed"),
    "03f680b6": ("3M and 9M ended 2023-09-30 interim (cover text); inventory class partial_statements, pdf p3-9 textless", "not transcribed"),
    "88946dfb": ("3M and 6M ended 2023-06-30 interim (cover text)", "not transcribed"),
    "0247f3c6": ("3M ended 2023-03-31 interim (cover text; 57 pages)", "not transcribed"),
    "abe5824f": ("3M and 9M ended 2024-09-30 interim (cover text)", "not transcribed"),
    "770e2bf9": ("3M and 6M ended 2024-06-30 interim (cover text)", "not transcribed"),
    "4a8556cd": ("3M ended 2024-03-31 interim (cover text)", "not transcribed"),
    "b43be1db": ("3M and 9M ended 2025-09-30 interim (cover text)", "not transcribed"),
    "2e1768d4": ("3M and 6M ended 2025-06-30 interim (cover text)", "not transcribed; H1 2025 comparatives read in the H1 2026 filing"),
    "bcf888b2": ("3M ended 2025-03-31 interim (cover text)", "not transcribed; Q1 2025 comparatives read in the Q1 2026 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatements_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read from rendered image-only pages for FY2025, FY2024, FY2023 (with 2022 restated), FY2022 as issued under IFRS 4, H1 2026 (with 3M and prior-year columns) and Q1 2026. All identities hold exactly; comparatives agree across filings except declared items. FY2025: insurance revenue 558,377, loss before zakat -90,044, net loss -91,564 (EPS -3.05), total assets 808,775, equity 269,896 after a 100,000 share-capital issue (capital 200,000 to 300,000, transaction costs 4,054), CFO -1,627, closing cash 282,383. FY2024 net profit 30,123; FY2023 net profit 51,302; FY2022 restated net loss -38,866 (as issued -58,327). H1 2026: revenue 333,800, net loss -20,342 (Q2 -17,018), equity 249,554; Q1 + Q2 = H1 for revenue, loss before zakat, zakat and net loss in 2026 and 2025 (pass). Declared differences: (1) IFRS 17 transition for FY2022 (as issued versus restated: net result, total assets, equity, CFO, CFI). (2) FY2024 cash flow restated in the FY2025 filing (note 31): CFO -155,575 to -153,278 and CFI -21,810 to -24,107 (commission income received reclassified to operating), net change and cash unchanged. (3) FY2023 EPS 3.25 as first issued versus 2.68 labelled restated in the FY2024 filing (cause not verified). (4) Q1 2025 cash flow is marked Restated - Note 24 in the Q1 2026 filing (CFO -5,370 there). Interim cash flow: Q1 2026 CFO -18,958 versus H1 2026 CFO -13,554 (Q2 by subtraction +5,404) with different zakat and financing line detail, so a Q2 cash flow by subtraction is NOT validated.",
        "not_read": ["notes in every file (except note 31 of FY2025)", "statements of changes in equity", "Q1 2026 balance sheet", "FY2022 as-issued income page pdf p9 (premiums and underwriting)", "H1 2025 original cash flow (comparative in H1 2026 only)", "all other interims"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_opened_all_statement_pages_are_image_only",
        "summary": "All six audited files carry balance sheet, income statement and cash-flow statement (Q1 2026 balance sheet not transcribed) as image-only pages with no usable text layer, although the inventory classes them financial_statements or annual_report_with_state with statement_pages taken from notes; 03f680b6 (9M 2023) is classed partial_statements. H1 2026 text layer contains only an e-signature stamp line on each statement page. No FY2021 own FS and no 2021 interims exist in the collection.",
        "defect_ids": ["B015-8050-1", "B015-8050-2", "B015-8050-3"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_to_2026_H1_with_gaps_by_page_derived_period",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)",
                                                    "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "2025 Q1, Q2, H1 (2026 filings)"],
        "values_not_read": ["2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M", "2025 Q1/H1/9M originals"],
        "missing": ["FY2021 and earlier (no file)", "2021 and earlier interims", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in all four FS files (2023|FY holds FY2022, 2024|FY FY2023, 2025|FY FY2024, 2026|FY FY2025); the inventory period_mismatch flags are correct detections. Interim labels match page periods.",
    },
}
defects = [
    {"id": "B015-8050-1", "class": "image_only_or_scanned_statements_flagged_as_present", "severity": "high",
     "evidence": "28ce63c0 pdf p8-14, ded8b2a2 p3-14, 44f0c863 p9-16, 16733245 p3-13, fdad4f76 p4-8 are image-only; c1bacc8f statement pages hold only a signing stamp as text; 03f680b6 classed partial_statements with p3-9 textless."},
    {"id": "B015-8050-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "16733245 FY2022 labelled 2023|FY, 44f0c863 FY2023 labelled 2024|FY, ded8b2a2 FY2024 labelled 2025|FY, 28ce63c0 FY2025 labelled 2026|FY. A label reader would shift every annual value by one year."},
    {"id": "B015-8050-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17 transition: FY2022 net loss -58,327 as issued (16733245 pdf p10) versus -38,866 restated (44f0c863 pdf p11); total assets 765,970 versus 666,810; equity 37,768 versus 60,856; CFO 77,841 versus 69,463. FY2024 CFO -155,575 (ded8b2a2 pdf p13) versus -153,278 restated (28ce63c0 pdf p13, note 31). FY2023 EPS 3.25 versus 2.68. Q1 2025 cash flow restated (fdad4f76 pdf p8). Both values recorded, none substituted."},
]
unread = ["notes in every file (except note 31 of FY2025)", "statements of changes in equity", "Q1 2026 balance sheet", "12 interim filings 2022 Q1 to 2025 9M (identified by cover only)", "FY2021 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Six filings value-verified from rendered image-only pages (FY2022 as issued, FY2023, FY2024, FY2025, Q1 2026, H1 2026); IFRS 17 restatement, FY2024 cash-flow restatement and EPS restatement declared with both values; "
              "12 interim filings identified by cover but not value-read; FY2021 and earlier absent.")
mkrecord.build(dict(
    symbol="8050", name="SALAMA COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All statement pages of the six audited filings are image-only and were rendered and read by eye. "
            "tools/check_transcripts.py over transcripts/8050.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, loss before zakat, zakat and net loss (2026 and 2025); all pass.")))
