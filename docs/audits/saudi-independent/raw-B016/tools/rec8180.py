"""Builds raw-B016/8180.json from the page transcripts."""
import mkrecord

U = "SAR full riyals as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


T = "text layer, tied by arithmetic"
documents = [
    doc("e2b38e66", "FY ended 2025-12-31 audited FS in annual report (collector label 2026|FY = publication year)", False, {"bs": 7, "is": 8, "cf": "11-12"}, {"bs": 6, "is": 7, "cf": "10-11"}, T,
        "net loss -70,317,330 after a zakat reversal of 1,000,000 (pre-zakat loss -71,317,330); accumulated losses -41,476,996"),
    doc("ec20ffab", "FY ended 2024-12-31 audited FS in annual report (label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "12-13"}, {"bs": 7, "is": 8, "cf": "11-12"}, T,
        "2024 rights issue: share capital 140,000,000 -> 300,000,000, net proceeds 152,911,250; 2023 EPS restated 1.99 (3.02 as issued)"),
    doc("d50bb975", "FY ended 2023-12-31 audited FS in annual report (label 2024|FY = publication year); 2022 and 1 Jan 2022 restated for IFRS 17", False, {"bs": 10, "is": 11, "cf": "14-15"}, {"bs": 9, "is": 10, "cf": "13-14"}, T),
    doc("a20d60af", "FY ended 2022-12-31 audited FS as issued under IFRS 4 in annual report (label 2023|FY = publication year); statement pages carry a garbled OCR text layer", False, {"bs": 8, "is": "9-10", "cf": "13-14"}, {"bs": 7, "is": "8-9", "cf": "12-13"},
        "visual (rendered at 2x and read); the underwriting/revenue page (pdf p9) not transcribed", "OCR layer reads e.g. 'TOTALASSETS' and '4o9,426,j49'; text extraction is unusable for values"),
    doc("a737083d", "H1 2026 reviewed interim (label 2026|H1 correct); six and three months; statement pages image-only", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, "visual (rendered at 2x and read)"),
    doc("78343af2", "Q1 2026 interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, T),
]
identified = {
    "f3259e74": ("Q1 2022 interim (cover: ended March 31, 2022); pdf p3-11 textless", "not transcribed"),
    "1b6e6400": ("H1 2022 interim (cover: ended June 30, 2022); pdf p3-12 textless", "not transcribed"),
    "d0be96a1": ("9M 2022 interim (cover rendered: three and nine months ended September 30, 2022), whole-file 62-page scan classed scanned_unreadable", "statements not opened; not transcribed"),
    "b1283841": ("Q1 2023 interim (cover rendered: three months ended 31 March 2023); pdf p1-10 textless", "not transcribed"),
    "af8d1267": ("H1 2023 interim (cover rendered: three and six months ended 30 June 2023); pdf p1-10 textless", "not transcribed"),
    "3023af6a": ("9M 2023 interim (cover rendered: three and nine months ended 30 September 2023), whole-file 75-page scan classed scanned_unreadable", "statements not opened; not transcribed"),
    "f7cdacac": ("Q1 2024 interim (cover: ended 31 March 2024)", "not transcribed"),
    "419f6613": ("H1 2024 interim (cover: ended 30 June 2024)", "not transcribed"),
    "1dea40e5": ("9M 2024 interim (cover: ended 30 September 2024)", "not transcribed"),
    "d50bb975x": ("", ""),
    "d50bb975y": ("", ""),
    "daa455ca": ("Q1 2025 interim (cover: ended 31 March 2025); pdf p3-9 textless", "not transcribed; Q1 2025 values known only as comparatives in 78343af2"),
    "fd898f69": ("H1 2025 interim (cover: ended June 30, 2025); pdf p3-9 textless", "not transcribed; H1 and Q2 2025 values known only as comparatives in a737083d"),
    "574281ba": ("9M 2025 interim (cover: ended September 30, 2025); pdf p3-9 textless", "not transcribed"),
}
identified = {k: v for k, v in identified.items() if v[0]}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_IFRS17_restatement_of_FY2022_declared",
        "summary": ("Headline balance sheet, income and cash-flow values (SAR full riyals as printed) read and tied by arithmetic for FY2025, FY2024, FY2023 (text), FY2022 as issued (garbled OCR layer, read from images), H1 2026 (image-only pages read visually) and Q1 2026. "
                    "Balance-sheet identity, cash-flow sum and roll, and pre-zakat result plus zakat to net result hold exactly in every column. FY2025: insurance revenue 604,414,187, net loss -70,317,330 (EPS -2.34), total assets 651,837,105, equity 342,143,409, CFO -93,014,777. "
                    "FY2024: insurance revenue 503,656,077, net profit 31,858,208 (EPS 1.26). FY2023: 486,224,565 and 42,299,859. FY2022 as issued under IFRS 4: pre-zakat loss -68,896,262, net loss -73,496,262, total assets 666,141,428, equity 130,324,813. H1 2026: insurance revenue 303,818,880, net profit 2,110,782, total assets 637,240,897. "
                    "Declared differences: (1) IFRS 17 restatement of FY2022 in the FY2023 filing: total assets 666,141,428 -> 567,895,461, equity 130,324,813 -> 153,458,074, net loss -73,496,262 -> -53,459,717, and 1 Jan 2022 assets 753,782,100 -> 663,697,390; cash and cash-flow totals unchanged. "
                    "(2) 2023 EPS 3.02 as issued versus 1.99 restated in the FY2024 filing (rights issue). The Q1+Q2=H1 2026 and 2025 rolls (revenue, pre-zakat result, net income) close exactly (five roll checks). "
                    "Interim cash-flow Q2 by subtraction: H1 2026 CFO -6,610,713 less Q1 86,292 would give -6,697,005; the H1 statement is cumulative, subtraction not validated against any printed quarter."),
        "not_read": ["notes in every file (including note 1 going-concern and capital paragraph of the H1 2026 filing, pdf p10, image-only)", "statements of changes in equity", "FY2022 income statement revenue and underwriting page (pdf p9)",
                     "own filings of Q1/H1/9M 2022, 2023, 2024, 2025", "FY2021 and earlier (comparatives only)", "FY2025 auditor report"],
    },
    "document_completeness": {
        "status": "primary_statements_present_for_every_period_2022Q1_to_2026H1_many_statement_sets_image_only",
        "summary": ("Eighteen files provide a statement set for every period from Q1 2022 to H1 2026; the four annual items are annual reports with embedded audited FS. Image-only or scan problems: whole-file scans d0be96a1 (9M 2022, 62 pages) and 3023af6a (9M 2023, 75 pages) are classed scanned_unreadable but carry full interim statements (covers rendered); "
                    "FY2022 (a20d60af) has a garbled OCR layer on its statement pages; Q1 2022, H1 2022, Q1 2023, H1 2023, Q1/H1/9M 2025 and H1 2026 have textless statement pages. Q1/H1/9M 2024 and Q1 2026 are born digital. No Arabic twins."),
        "defect_ids": ["B016-8180-1", "B016-8180-2", "B016-8180-3", "B016-8180-4"],
    },
    "company_coverage": {
        "status": "contiguous_quarterly_and_annual_coverage_2022Q1_to_2026H1_nothing_earlier_than_2022",
        "present_in_files_by_page_derived_period": ["2022 Q1", "2022 H1", "2022 9M", "FY2022 (label 2023|FY)", "2023 Q1", "2023 H1", "2023 9M", "FY2023 (label 2024|FY)", "2024 Q1", "2024 H1", "2024 9M", "FY2024 (label 2025|FY)",
                                                    "2025 Q1", "2025 H1", "2025 9M", "FY2025 (label 2026|FY)", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1 and Q2"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "FY2022 restated, 1 Jan 2022 restated (FY2023 filing)", "2025 Q1 (Q1 2026 filing)", "2025 H1 and Q2 (H1 2026 filing)"],
        "values_not_read": ["2022 Q1, H1, 9M", "2023 Q1, H1, 9M", "2024 Q1, H1, 9M", "2025 Q1, H1, 9M own filings"],
        "missing": ["FY2021 and earlier (no file; inventory window opening at 2010 precedes the collection)"],
        "inventory_corrections": ("Annual labels equal publication year (2023|FY = FY2022 ... 2026|FY = FY2025); no 2022|FY label although FY2022 is present. The inventory's 46 'absent' periods are overwhelmingly pre-2022 window years. "
                                  "Share capital: 400,000,000 (2021) -> 140,000,000 (2022, accumulated losses 197m eliminated) -> 300,000,000 (2024 rights issue); EPS before 2024 is not comparable with later EPS (14,000,000 shares versus 30,000,000)."),
    },
}
defects = [
    {"id": "B016-8180-1", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "a20d60af (FY2022) is labelled 2023|FY, d50bb975 (FY2023) 2024|FY, ec20ffab (FY2024) 2025|FY, e2b38e66 (FY2025) 2026|FY; the 2022|FY label is empty although FY2022 is present."},
    {"id": "B016-8180-2", "class": "image_only_or_scanned_statements_flagged_as_present_or_unreadable", "severity": "high",
     "evidence": "d0be96a1 (62 pages) and 3023af6a (75 pages) are whole-file scans classed scanned_unreadable but the rendered covers read 'three-month and nine-month periods ended September 30, 2022' and '30 September 2023'; a737083d (H1 2026) pdf p3-9 textless although classed financial_statements with statement_pages from notes; a20d60af statement pages carry an OCR layer with corrupt digits ('4o9,426,j49')."},
    {"id": "B016-8180-3", "class": "restated_or_represented_comparatives_ifrs17", "severity": "high",
     "evidence": "FY2022 as issued (a20d60af pdf p8, p10): net loss -73,496,262, equity 130,324,813, total assets 666,141,428; restated in the FY2023 filing (d50bb975 pdf p10-11): net loss -53,459,717, equity 153,458,074, total assets 567,895,461 (restatement notes 3 and 5). 2023 EPS 3.02 (d50bb975 pdf p11) versus 1.99 restated (ec20ffab pdf p9). Both values recorded, none substituted."},
    {"id": "B016-8180-4", "class": "net_loss_year_going_concern_wording_unread", "severity": "low",
     "evidence": "FY2025 net loss -70,317,330 and 2025 H1 loss -33,258,058; accumulated losses -41,476,996 at 31 Dec 2025 against equity 342,143,409. The H1 2026 note 1/2 page (pdf p10) is an image and was not read, so any going-concern or regulatory-capital wording is unverified. No material uncertainty was seen in pages read."},
]
unread = ["notes in every file", "statements of changes in equity", "going-concern and capital wording (H1 2026 pdf p10, FY2025 notes, auditor reports)", "FY2022 revenue/underwriting page (pdf p9)",
          "own filings of the other 12 interims (identified by cover only)", "whole-file scans d0be96a1 and 3023af6a statements", "FY2021 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Six filings value-verified (FY2022 as issued, FY2023, FY2024, FY2025, Q1 2026, H1 2026); the IFRS 17 restatement of FY2022 is declared with both values. "
              "A statement file exists for every period Q1 2022 to H1 2026 by page-derived period, but twelve interim files were identified by cover only and are unread; no filing before 2022 exists.")
mkrecord.build(dict(
    symbol="8180", name="AL SAGR COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Born-digital pages read from the text layer with tools/rows.py; FY2022 (garbled OCR layer) and H1 2026 (image-only) statements were rendered at 2x and read by eye; four whole-file or textless cover pages were rendered to identify periods. "
            "tools/check_transcripts.py over transcripts/8180.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat to net result, cross-filing comparatives (restated FY2022 columns flagged) and five Q1+Q2=H1 roll checks; all pass.")))
