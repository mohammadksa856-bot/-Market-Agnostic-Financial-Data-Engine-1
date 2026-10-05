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
    doc("78343af2", "Q1 2026 interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, T),
]
identified = {
    "a20d60af": ("FY2022 audited FS as issued under IFRS 4 in annual report (label 2023|FY); statement pages carry a garbled OCR layer (e.g. TOTALASSETS, 4o9,426,j49). NOT READ in this audit (page images were not viewable); FY2022 as issued is therefore UNVERIFIED, only the IFRS 17 restated FY2022 column in d50bb975 is verified", "statements not read"),
    "a737083d": ("H1 2026 interim (label 2026|H1), pdf p3-9 textless image pages. NOT READ in this audit (page images were not viewable); H1 2026 values unverified", "statements not read"),
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
        "status": "verified_for_4_filings_FY2022_as_issued_and_H1_2026_unread",
        "summary": ("Headline balance sheet, income and cash-flow values (SAR full riyals as printed) read from text layers and tied by arithmetic for FY2025, FY2024, FY2023 (with restated FY2022 and 1 Jan 2022 columns) and Q1 2026. Balance-sheet identity, cash-flow sum and roll, and pre-zakat result plus zakat to net result hold exactly. "
                    "FY2025: insurance revenue 604,414,187, net loss -70,317,330 (EPS -2.34), total assets 651,837,105, equity 342,143,409, CFO -93,014,777. FY2024: 503,656,077 and 31,858,208 (EPS 1.26). FY2023: 486,224,565 and 42,299,859 (EPS 3.02 as issued, 1.99 restated in the FY2024 filing). Restated FY2022 (IFRS 17, in the FY2023 filing): total assets 567,895,461, equity 153,458,074, net loss -53,459,717. Q1 2026: revenue 146,130,776, net profit 1,006,186. "
                    "FY2022 as issued under IFRS 4 (a20d60af, garbled OCR layer, image pages) and H1 2026 (a737083d, image pages) were NOT read because the page images were not viewable; their values are unverified and not recorded, and the size of the IFRS 17 restatement of FY2022 cannot be stated. "
                    "The Q1 2026 revenue of 146,130,776 is the as-printed three-month figure."),
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
        "values_verified_from_own_pages": ["FY2023", "FY2024", "FY2025", "2026 Q1", "FY2022 restated (as comparative in the FY2023 filing)"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "FY2022 restated, 1 Jan 2022 restated (FY2023 filing)", "2025 Q1 (Q1 2026 filing)", "(2025 H1 and Q2 and 2026 H1 unread: H1 2026 filing not read)"],
        "values_not_read": ["FY2022 as issued", "2026 H1", "2022 Q1, H1, 9M", "2023 Q1, H1, 9M", "2024 Q1, H1, 9M", "2025 Q1, H1, 9M own filings"],
        "missing": ["FY2021 and earlier (no file; inventory window opening at 2010 precedes the collection)"],
        "inventory_corrections": ("Annual labels equal publication year (2023|FY = FY2022 ... 2026|FY = FY2025); no 2022|FY label although FY2022 is present. The inventory's 46 'absent' periods are overwhelmingly pre-2022 window years. "
                                  "Share capital: 400,000,000 (2021) -> 140,000,000 (2022, accumulated losses 197m eliminated) -> 300,000,000 (2024 rights issue); EPS before 2024 is not comparable with later EPS (14,000,000 shares versus 30,000,000)."),
    },
}
defects = [
    {"id": "B016-8180-1", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "a20d60af (FY2022) is labelled 2023|FY, d50bb975 (FY2023) 2024|FY, ec20ffab (FY2024) 2025|FY, e2b38e66 (FY2025) 2026|FY; the 2022|FY label is empty although FY2022 is present."},
    {"id": "B016-8180-2", "class": "image_only_or_scanned_statements_flagged_as_present_or_unreadable", "severity": "high",
     "evidence": "d0be96a1 (62 pages) and 3023af6a (75 pages) are whole-file scans classed scanned_unreadable; covers rendered read as nine-month interim statements for 30 Sept 2022 and 2023, contents otherwise not viewed. a737083d (H1 2026) pdf p3-9 and a20d60af statement pages (garbled OCR layer) are image pages that were not read here."},
    {"id": "B016-8180-3", "class": "restated_or_represented_comparatives_ifrs17", "severity": "high",
     "evidence": "FY2022 was restated for IFRS 17 in the FY2023 filing (d50bb975 pdf p10-12, notes 3 and 5): restated total assets 567,895,461, equity 153,458,074, net loss -53,459,717 are read from text. The FY2022 as-issued values (a20d60af) were NOT read, so the size of the restatement is unverified. 2023 EPS 3.02 (d50bb975 pdf p11) versus 1.99 restated (ec20ffab pdf p9) is verified."},
    {"id": "B016-8180-4", "class": "net_loss_year_going_concern_wording_unread", "severity": "low",
     "evidence": "FY2025 net loss -70,317,330; accumulated losses -41,476,996 at 31 Dec 2025 against equity 342,143,409. The H1 2026 filing (image pages) was not read, so any going-concern or regulatory-capital wording is unverified. No material uncertainty was seen in pages read."},
]
unread = ["notes in every file", "statements of changes in equity", "going-concern and capital wording (H1 2026 pdf p10, FY2025 notes, auditor reports)", "FY2022 as issued statements (a20d60af)", "H1 2026 statements (a737083d)",
          "own filings of the other 12 interims (identified by cover only)", "whole-file scans d0be96a1 and 3023af6a statements", "FY2021 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Four filings value-verified (FY2023, FY2024, FY2025, Q1 2026); FY2022 as issued and H1 2026 were not read. "
              "A statement file exists for every period Q1 2022 to H1 2026 by page-derived period, but thirteen interim files were identified by cover only or not read; no filing before 2022 exists.")
mkrecord.build(dict(
    symbol="8180", name="AL SAGR COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Born-digital pages read from the text layer with tools/rows.py; FY2022-as-issued (a20d60af) and H1 2026 (a737083d) statements are image pages that were NOT read; four whole-file or textless cover pages were rendered to identify periods. "
            "tools/check_transcripts.py over transcripts/8180.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat to net result, cross-filing comparatives (restated FY2022 columns flagged) (no roll checks remain because H1 2026 is unread); all pass.")))
