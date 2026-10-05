"""Builds raw-B016/8170.json from the page transcripts."""
import mkrecord

V = "visual (rendered and read by eye)"


def doc(sha, period, ok, pdf, printed, reading, note=None, units="SAR thousands as printed"):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=units, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("32269f80", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 7, "is": 8, "cf": "11-12"}, {"bs": 5, "is": 6, "cf": "9-10"}, V,
        "net loss -244,444; accumulated losses -162,072; going-concern assessment note (pdf p13) cites net loss, operating cash outflow and solvency; 2024 comparatives reclassified (note 35, pdf p91-92)"),
    doc("7a886b41", "FY ended 2024-12-31 audited FS as issued (label 2025|FY = publication year)", False, {"bs": 9, "is": 10, "cf": 13}, {"bs": 7, "is": 8, "cf": 11}, V,
        "FY2024 balance sheet and cash flow later reclassified in the FY2025 filing; both values declared"),
    doc("c7fd5fda", "FY ended 2023-12-31 audited FS (label 2024|FY = publication year); 2022 and 1 Jan 2022 restated to IFRS 17 and labelled unaudited", False, {"bs": 11, "is": 12, "cf": 15}, {"bs": 9, "is": 10, "cf": 13}, V),
    doc("108aea03", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year); FULL SAR", False, {"bs": "8-9", "is": "10-11", "cf": 14}, {"bs": "6-7", "is": "8-9", "cf": 12}, V,
        "statements are combined (insurance operations and shareholders together, surplus attribution shown); the separate split is in note 33 (not read); transcript total_equity adds accumulated surplus and reserves 1,642,868 to shareholders equity 565,258,467",
        units="SAR full riyals as printed"),
    doc("e663a175", "H1 2026 reviewed interim (label 2026|H1 correct); whole-file 51-page scan classed scanned_unreadable but holds review report and full statements", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 2, "is": 3, "cf": "6-7"}, V,
        "review report (pdf p3) carries a MATERIAL UNCERTAINTY RELATED TO GOING CONCERN: net loss 92.2m, operating outflow 92.8m, accumulated loss 212.9m, solvency margin below the minimum; statutory reserve 41,362 transferred to accumulated losses"),
    doc("39ad317e", "Q1 2026 interim (label 2026|Q1 correct); image-only", True, {"bs": 4, "is": 5, "cf": 9}, {"bs": 2, "is": 3, "cf": 7}, V,
        "cash-flow operating and investing sections (pdf p8) not read; only net change 15,151 and closing cash 110,139 seen"),
]
identified = {
    "7c7b408a": ("Q1 2022 interim (cover: ended March 31, 2022); pdf p3-10 textless", "not transcribed"),
    "8b248946": ("H1 2022 interim (cover: ended June 30, 2022); pdf p3-10 textless", "not transcribed"),
    "ad366c0b": ("9M 2022 interim (cover: ended September 30, 2022); pdf p3-10 textless", "not transcribed"),
    "d61e3e8a": ("Q1 2023 interim (cover: ended March 31, 2023); pdf p3-8 textless", "not transcribed"),
    "dc508913": ("H1 2023 interim (cover: ended June 30, 2023); pdf p3-8 textless", "not transcribed"),
    "9e135e59": ("9M 2023 interim (cover: ended September 30, 2023); pdf p3-8 textless", "not transcribed"),
    "f50f68f1": ("Q1 2024 interim (cover: ended March 31, 2024); classed partial_statements; pdf p3-8 textless", "not transcribed"),
    "c80dd749": ("H1 2024 interim (cover: ended June 30, 2024); classed partial_statements", "not transcribed"),
    "1019f1f2": ("9M 2024 interim (cover: ended September 30, 2024); classed partial_statements", "not transcribed"),
    "2f7ed244": ("Q1 2025 interim (cover: ended March 31, 2025); classed partial_statements; pdf p3-8 textless", "not transcribed; Q1 2025 values known only as comparatives in 39ad317e"),
    "e34771bb": ("H1 2025 interim (cover: ended June 30, 2025); pdf p3-9 textless", "not transcribed; H1 and Q2 2025 values known only as comparatives in e663a175"),
    "c707d6a1": ("9M 2025 interim (cover: ended September 30, 2025); pdf p3-9 textless", "not transcribed"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_IFRS17_restatement_reclassification_and_going_concern_declared",
        "summary": ("Headline balance sheet, income and cash-flow values read from rendered pages for FY2025, FY2024 as issued, FY2023, FY2022 as issued (full SAR), H1 2026 (six and three months) and Q1 2026 (cash flow only net change). Balance-sheet identity, cash-flow sum and roll, and pre-zakat result plus zakat to net result hold exactly; "
                    "five Q1+Q2=H1 roll checks (2026 and 2025: net result, insurance revenue, pre-zakat result) close exactly. SAR thousands: FY2025 insurance revenue 1,254,553, net loss -244,444 (EPS -4.89), total assets 1,201,190, equity 449,585, CFO -236,436, closing cash 94,988. FY2024 as issued: 1,489,646 and net income 49,134 (EPS 0.98), total assets 1,550,782. "
                    "FY2023: 1,202,169 and 93,896 (EPS 2.09). FY2022 as issued under IFRS 4 in full SAR: total revenues 1,037,956,465, income attributable to shareholders 32,290,996, total assets 1,810,631,516. H1 2026: insurance revenue 603,164, net loss -92,194 (Q2 -52,629), total assets 1,053,867, equity 357,391. "
                    "Declared differences: (1) FY2022 restated to IFRS 17 in the FY2023 filing and labelled unaudited: total assets 1,810,631,516 -> 1,515,459 thousand, shareholders equity 565,258,467 -> 536,614, net income 32,290,996 -> 12,702 thousand, revenue 1,037,956,465 (IFRS 4 total revenues) -> 1,072,869 (IFRS 17 insurance revenue), CFO 89,391,163 -> 89,392 thousand. "
                    "(2) FY2024 reclassified in the FY2025 filing (note 35, pdf p91-92): total assets 1,550,782 -> 1,509,526, total liabilities 839,125 -> 797,869, CFO -338,081 -> -320,454, CFI 393,774 -> 380,422, CFF -27,000 -> -31,275; net income 49,134 and equity 711,657 unchanged. "
                    "(3) EPS: 2023 EPS 2.09 as issued versus 1.88 in the FY2024 filing (bonus shares); 2022 EPS 0.72 as issued versus 0.28 restated. (4) unit scale changes from full SAR (FY2022) to SAR thousands (FY2023 onward). "
                    "(5) the FY2023 income statement was re-presented in the FY2024 filing (insurance service expenses 1,088,617 versus 1,089,714, other income 189 versus 26,244; pre-zakat income 103,896 and net income 93,896 unchanged). "
                    "Interim cash flows are cumulative; a Q2 2026 CFO by subtraction is impossible because the Q1 2026 operating section was not read."),
        "not_read": ["notes in every file (except note 35, the going-concern note and note 1 headings)", "statements of changes in equity", "insurance operations / shareholders split (note 33 of FY2022 and similar)", "Q1 2026 operating and investing cash flows (pdf p8)",
                     "own filings of 12 interims 2022 to 2025", "FY2021 and earlier (comparatives only)"],
    },
    "document_completeness": {
        "status": "statements_present_for_every_period_2022Q1_to_2026H1_all_statement_pages_image_only",
        "summary": ("Eighteen files cover every period from Q1 2022 to H1 2026; four annuals are annual-report-style FS files. Every statement page examined is an image: the whole-file 51-page H1 2026 scan (e663a175) is classed scanned_unreadable but holds a review report and full statements; "
                    "all other files have textless statement pages (pdf p3-14 in annuals, p3-10 in interims). Four 2024-2025 Q1/H1/9M files are classed partial_statements (inventory found only income pages) although the covers show full condensed statements. No Arabic twins."),
        "defect_ids": ["B016-8170-1", "B016-8170-2", "B016-8170-3", "B016-8170-4", "B016-8170-5"],
    },
    "company_coverage": {
        "status": "contiguous_quarterly_and_annual_coverage_2022Q1_to_2026H1_nothing_earlier_than_2022",
        "present_in_files_by_page_derived_period": ["2022 Q1", "2022 H1", "2022 9M", "FY2022 (label 2023|FY)", "2023 Q1", "2023 H1", "2023 9M", "FY2023 (label 2024|FY)", "2024 Q1", "2024 H1", "2024 9M", "FY2024 (label 2025|FY)",
                                                    "2025 Q1", "2025 H1", "2025 9M", "FY2025 (label 2026|FY)", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued)", "FY2023", "FY2024 (as issued)", "FY2025", "2026 Q1 (BS, IS)", "2026 H1 and Q2"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "FY2022 restated (FY2023 filing)", "FY2024 reclassified (FY2025 filing)", "2025 Q1 (Q1 2026 filing)", "2025 H1 and Q2 (H1 2026 filing)"],
        "values_not_read": ["2022 Q1, H1, 9M", "2023 Q1, H1, 9M", "2024 Q1, H1, 9M", "2025 Q1, H1, 9M own filings", "2026 Q1 cash-flow detail"],
        "missing": ["FY2021 and earlier (no file; the inventory window opening at 2011 precedes the collection)"],
        "inventory_corrections": ("Annual labels equal publication year (2023|FY = FY2022 ... 2026|FY = FY2025); no 2022|FY label. Entity is Al-Etihad Cooperative Insurance Company, same name in every file (Khobar head office, commercial registration 2051036304 per FY2022 note 1); no merger or rename appears in the pages read. "
                                  "The four period_mismatch flags the inventory raised for 8170 are correct (publication-year labels)."),
    },
}
defects = [
    {"id": "B016-8170-1", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "108aea03 (FY2022) is 2023|FY, c7fd5fda (FY2023) 2024|FY, 7a886b41 (FY2024) 2025|FY, 32269f80 (FY2025) 2026|FY; the inventory period_mismatch_candidate flags for 8170 are correct."},
    {"id": "B016-8170-2", "class": "image_only_or_scanned_statements_flagged_as_present_or_unreadable", "severity": "high",
     "evidence": "e663a175 (51 pages, zero text) is classed scanned_unreadable but pdf p3 is the review report and pdf p4-9 are the full interim statements; all other files read have textless statement pages; four Q1/H1/9M 2024-2025 files are classed partial_statements."},
    {"id": "B016-8170-3", "class": "restated_or_represented_comparatives_ifrs17_and_reclassification", "severity": "high",
     "evidence": "FY2022 as issued (108aea03 pdf p8-11) versus restated unaudited column (c7fd5fda pdf p11-12): equity 565,258,467 vs 536,614 thousand, net income 32,290,996 vs 12,702 thousand. FY2024 as issued (7a886b41 pdf p9, p13) versus FY2025 restated (32269f80 pdf p7, p11): total assets 1,550,782 vs 1,509,526, CFO -338,081 vs -320,454; note 35 (pdf p91-92) lists salvage recoveries, murabaha receivables and intangibles reclassifications. Both values recorded, none substituted."},
    {"id": "B016-8170-4", "class": "unit_scale_change", "severity": "high",
     "evidence": "108aea03 prints SR full riyals (total assets 1,810,631,516); c7fd5fda and later print SR'000 thousands. Restated FY2022 values appear in thousands in the FY2023 filing."},
    {"id": "B016-8170-5", "class": "going_concern_material_uncertainty", "severity": "high",
     "evidence": "H1 2026 review report (e663a175 pdf p3): MATERIAL UNCERTAINTY RELATED TO GOING CONCERN citing net loss 92.2m, operating cash outflow 92.8m, accumulated loss 212.9m and solvency margin below the Insurance Authority minimum. FY2025 audited note (32269f80 pdf p13): net loss 244.4m, accumulated loss 162.1m, solvency continues to be in compliance. Equity fell from 711,657 (Dec 2024) to 357,391 (Jun 2026) thousand."},
]
unread = ["notes in every file", "statements of changes in equity", "insurance operations / shareholders operations split", "Q1 2026 operating and investing cash flows", "own filings of 12 interims 2022-2025 (identified by cover only)",
          "going-concern wording of the FY2025 auditor report beyond the note", "FY2021 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Six filings value-verified from rendered pages (FY2022 as issued, FY2023, FY2024 as issued, FY2025, Q1 2026 partly, H1 2026); IFRS 17 restatement of FY2022, FY2024 reclassification and a unit-scale change are declared; the H1 2026 review report carries a going-concern material uncertainty. "
              "A statement file exists for every period Q1 2022 to H1 2026, but twelve interim files are identified by cover only and unread; no pre-2022 filing exists.")
mkrecord.build(dict(
    symbol="8170", name="AL-ETIHAD COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Every audited statement page is an image and was rendered at 1.6-1.8x and read by eye (the 51-page H1 2026 whole-file scan included). "
            "tools/check_transcripts.py over transcripts/8170.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat to net result, cross-filing comparatives (restated columns flagged) and five Q1+Q2=H1 roll checks; all pass.")))
