"""Builds raw-B016/8100.json from the page transcripts."""
import mkrecord

K = "SAR thousands as printed"
V = "visual (rendered and read by eye)"


def doc(sha, period, ok, pdf, printed, reading, note=None, units=K):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=units, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("c3fdea9b", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": 13}, {"bs": 8, "is": 9, "cf": 13}, V,
        "PARTLY READ: only the cash-flow page (pdf p13) was viewed as an image. Balance-sheet values come from the 31 Dec 2025 column of the H1 2026 filing and income-statement values from the garbled OCR text layer corroborated by pdf p13 (pre-zakat 28,431) and the equity statement text (22,177); pdf p8-9 images were not viewed. Net income 22,177 after 28,431 pre-zakat; no financing cash flows"),
    doc("3751df76", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 12}, {"bs": 7, "is": 8, "cf": 12}, V,
        "PARTLY READ: only the cash-flow page (pdf p12) was viewed; balance-sheet and income-statement values come from comparative columns in the FY2025 text layer and the H1 2025 filing, pdf p7-8 images were not viewed"),
    doc("6120d98d", "FY ended 2023-12-31 audited FS (label 2024|FY = publication year); 2022 and 1 Jan 2022 restated for IFRS 17 and IFRS 9", False, {"bs": 10, "is": 11, "cf": 15, "equity": 13}, {"bs": 8, "is": 9, "cf": 13, "equity": 11}, V,
        "printed page numbers are pdf page minus 2; auditors' report heading reads 'Arabia Insurance Cooperative Company' (pdf p8-9)"),
    doc("1601d15b", "FY ended 2022-12-31 audited FS as issued under IFRS 4 (label 2023|FY = publication year); FULL SAR, not thousands", False, {"bs": 8, "is": 9, "cf": 13}, {"bs": 6, "is": 7, "cf": 11}, V,
        "income statement revenue/underwriting lines not transcribed", units="SAR full riyals as printed"),
    doc("01c03433", "H1 2026 reviewed interim (label 2026|H1 correct); six and three months", True, {"bs": 4, "is": 5, "cf": 9}, {"bs": 3, "is": 4, "cf": 8}, V),
    doc("f37d8748", "Q1 2026 interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": 9}, {"bs": 3, "is": 4, "cf": 8}, V,
        "note 4 (text, pdf p12) splits cash into insurance operations 287,924 and shareholders' operations 430"),
    doc("ccb6adbe", "9M 2025 interim (label 2025|9M correct); nine and three months", True, {"bs": 4, "is": 5, "cf": 9}, {"bs": 3, "is": 4, "cf": 8}, V),
    doc("e17189e9", "H1 2025 interim (label 2025|H1 correct); six and three months", True, {"bs": 4, "is": 5, "cf": 9}, {"bs": 4, "is": 5, "cf": 9}, V),
]
identified = {
    "f2fbd21b": ("Q1 2022 interim, whole-file 41-page scan classed scanned_unreadable (cover rendered: three-month period ended 31 March 2022)", "statements not opened; not transcribed"),
    "e4fadf26": ("H1 2022 interim, whole-file 47-page scan classed scanned_unreadable (cover rendered: three and six months ended 30 June 2022)", "statements not opened; not transcribed"),
    "2b18c242": ("9M 2022 interim (cover text: ended 30 September 2022); pdf p3-8 textless", "not transcribed"),
    "4b7a67f9": ("Q1 2023 interim (cover: ended 31 March 2023); pdf p3-4 textless", "not transcribed"),
    "1c970f28": ("H1 2023 interim (cover: ended 30 June 2023); pdf p3-9 textless", "not transcribed"),
    "572a6d53": ("9M 2023 interim (cover: ended 30 September 2023); pdf p3-9 textless", "not transcribed"),
    "635586a1": ("Q1 2024 interim (cover: ended 31 March 2024); pdf p3-9 textless", "not transcribed"),
    "81937341": ("H1 2024 interim (cover: ended 30 June 2024); pdf p3-9 textless", "not transcribed; H1 2024 values known only as comparatives in e17189e9"),
    "f0761cd9": ("9M 2024 interim (cover: ended 30 September 2024); pdf p4-9 textless", "not transcribed; 9M 2024 values known only as comparatives in ccb6adbe"),
    "8a0bae91": ("Q1 2025 interim (cover: ended 31 March 2025); pdf p3-9 textless", "not transcribed; Q1 2025 values known only as comparatives in f37d8748"),
    "7fbc75b1": ("28-page provider-network list (bilingual table: provider name, region, city), labelled 2025|Q1, classed other_no_statements_found", "not a financial document"),
    "57646c58": ("Annual Report of the Audit Committee for the year ended 31 December 2025, dated 4 February 2026 (cover rendered), 5 pages, labelled 2024|FY", "not a statement; mislabelled (FY2025 report in the 2024|FY slot)"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_8_filings_IFRS17_restatement_and_unit_change_declared",
        "summary": ("Headline balance sheet, income and cash-flow values read from rendered pages for FY2025, FY2024, FY2023, FY2022 as issued, H1 2026, Q1 2026, 9M 2025 and H1 2025. Balance-sheet identity, cash-flow sum and roll, and pre-zakat income less zakat to net income hold exactly in every column read; "
                    "nine Q1+Q2=H1 / H1+Q3=9M roll checks (net income and insurance revenue, 2024, 2025, 2026) close exactly. SAR thousands: FY2025 insurance revenue 1,156,884, net income 22,177 (EPS 0.74), total assets 2,224,346, equity 415,217, CFO 16,647, closing cash 180,006. FY2024: 1,080,637 and 49,318 (EPS 1.64). FY2023: 1,044,519 and 71,098. "
                    "FY2022 as issued under IFRS 4 in FULL SAR: net loss -37,204,718, total assets 1,461,610,325, equity 257,924,099, cash 36,736,221. H1 2026: insurance revenue 743,740, net income 15,951, total assets 2,180,071. "
                    "Declared differences: (1) IFRS 17/IFRS 9 restatement of FY2022 in the FY2023 filing: total assets 1,461,610 thousand as issued versus 1,150,965, equity 257,924 versus 235,438, net loss -37,205 versus -61,647, cash 36,736 versus 43,072, CFO 10,943 versus 18,145; opening 1 Jan 2022 equity 292,735 -> 292,021. "
                    "(2) unit scale changes from full SAR (FY2022 filing) to SAR thousands (FY2023 onwards). "
                    "Interim cash flows are cumulative: H1 2026 CFO 129,693 versus Q1 2026 157,041; 6M 2025 CFO -56,256 versus Q1 2025 114,543, so a Q2 CFO by subtraction (-27,348 in 2026, -170,799 in 2025) is NOT validated and not used. "
                    "Statements are single-company (insurance and shareholders' operations are not presented separately; only the cash note splits them)."),
        "not_read": ["notes in every file (except Q1 2026 note 4 cash split)", "statements of changes in equity (read for the FY2023 opening restatement only)", "FY2022 revenue and underwriting lines", "auditor reports (headings only)",
                     "own filings of Q1/H1/9M 2022, 2023, 2024 and Q1 2025", "note 4 restatement detail", "FY2021 and earlier (comparatives only)"],
    },
    "document_completeness": {
        "status": "statements_present_for_every_period_2022Q1_to_2026H1_nearly_all_image_only_or_garbled_OCR",
        "summary": ("Every annual FS and every interim from Q1 2022 to H1 2026 has a statement set, but the statement pages are images or garbled OCR in all of them: the FY2025 text layer misreads digits and punctuation so values cannot be extracted as text; FY2022, FY2023 and FY2024 statement pages are textless; "
                    "Q1 2022 and H1 2022 are whole-file scans classed scanned_unreadable; every interim file read has textless statement pages (pdf p3-9). Two non-statement files are mislabelled: a provider-network list (2025|Q1) and the FY2025 Audit Committee report (2024|FY). No Arabic twins."),
        "defect_ids": ["B016-8100-1", "B016-8100-2", "B016-8100-3", "B016-8100-4", "B016-8100-5"],
    },
    "company_coverage": {
        "status": "contiguous_quarterly_and_annual_coverage_2022Q1_to_2026H1_nothing_earlier_than_2022",
        "present_in_files_by_page_derived_period": ["2022 Q1", "2022 H1", "2022 9M", "FY2022 (label 2023|FY)", "2023 Q1", "2023 H1", "2023 9M", "FY2023 (label 2024|FY)", "2024 Q1", "2024 H1", "2024 9M", "FY2024 (label 2025|FY)",
                                                    "2025 Q1", "2025 H1", "2025 9M", "FY2025 (label 2026|FY)", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued)", "FY2023", "FY2024", "FY2025", "2025 H1 and Q2", "2025 9M and Q3", "2026 Q1", "2026 H1 and Q2"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "FY2022 restated, 1 Jan 2022 restated (FY2023 filing)", "2024 H1/Q2, 9M/Q3 (2025 filings)", "2025 Q1 (Q1 2026 filing)"],
        "values_not_read": ["2022 Q1, H1, 9M", "2023 Q1, H1, 9M", "2024 Q1, H1, 9M own filings", "2025 Q1 own filing"],
        "missing": ["FY2021 and earlier (no file; the inventory window opening at 2011 precedes the collection)"],
        "inventory_corrections": ("Annual labels equal publication year (2023|FY = FY2022 ... 2026|FY = FY2025); no 2022|FY label. The 2024|FY slot also holds the FY2025 Audit Committee report, and 2025|Q1 holds a provider-network list. "
                                  "Q4 2025 by subtraction: net income 22,177 less 9M 35,251 = -13,074 and insurance revenue 1,156,884 less 848,517 = 308,367; both annual and 9M statements carry no declared restatement, but quarterly Q4 values are derived, not printed."),
    },
}
defects = [
    {"id": "B016-8100-1", "class": "fiscal_year_label_mismatch_and_wrong_file_in_slot", "severity": "medium",
     "evidence": "1601d15b (FY2022) is 2023|FY, 6120d98d (FY2023) 2024|FY, 3751df76 (FY2024) 2025|FY, c3fdea9b (FY2025) 2026|FY; 57646c58 (Audit Committee report dated 4 February 2026) sits in 2024|FY; 7fbc75b1 (provider list) in 2025|Q1."},
    {"id": "B016-8100-2", "class": "image_only_or_scanned_or_garbled_statements_flagged_as_present_or_unreadable", "severity": "high",
     "evidence": "c3fdea9b pdf p8-12 carry garbled OCR (the text layer reads the note column as 'l\'otc' and prints figures such as '{689,218l'; values taken from the images); 1601d15b, 6120d98d, 3751df76, 01c03433, f37d8748, ccb6adbe, e17189e9 statement pages are textless images; e4fadf26 and f2fbd21b are whole-file scans classed scanned_unreadable (covers rendered)."},
    {"id": "B016-8100-3", "class": "restated_or_represented_comparatives_ifrs17", "severity": "high",
     "evidence": "FY2022 as issued (1601d15b pdf p8-9): net loss -37,204,718, equity 257,924,099; FY2023 filing (6120d98d pdf p10-11): net loss -61,647 thousand, equity 235,438 thousand; equity statement (pdf p13): IFRS 17 adjustment -25,851, IFRS 9 adjustment +25,137. Both values recorded, none substituted."},
    {"id": "B016-8100-4", "class": "unit_scale_change", "severity": "high",
     "evidence": "1601d15b states 'All amounts in Saudi Riyals' (e.g. total assets 1,461,610,325); 6120d98d and later state 'Thousands Saudi Riyals' (2022 restated total assets 1,150,965). A series spanning FY2022 and FY2023 must rescale; the two FY2022 values are not comparable even after rescaling (restatement)."},
    {"id": "B016-8100-5", "class": "interim_cash_flow_quarter_by_subtraction_invalid", "severity": "medium",
     "evidence": "H1 2026 CFO 129,693 (01c03433 pdf p9) versus Q1 2026 CFO 157,041 (f37d8748 pdf p9); H1 2025 CFO -56,256 (e17189e9 pdf p9) versus Q1 2025 CFO 114,543 (f37d8748 prior column). Subtraction yields -27,348 and -170,799; classification of statutory deposit and murabaha movements differs and the Q1 2025 column was not checked against its own filing."},
]
unread = ["notes in every file", "statements of changes in equity (except FY2023 opening)", "FY2022 revenue/underwriting lines", "auditor reports", "own filings of Q1/H1/9M 2022, 2023, 2024 and Q1 2025 (identified by cover only)",
          "Q1 2022 and H1 2022 whole-file scans", "FY2021 and earlier (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Eight filings value-verified from rendered pages (FY2022 as issued, FY2023, FY2024, FY2025, 9M 2025, H1 2025, Q1 2026, H1 2026); IFRS 17 restatement of FY2022 and a unit-scale change are declared. "
              "A statement file exists for every period Q1 2022 to H1 2026, but ten interim files are identified by cover only and unread; no pre-2022 filing exists.")
mkrecord.build(dict(
    symbol="8100", name="SAUDI ARABIAN COOPERATIVE INSURANCE COMPANY (SAICO)", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All audited statement pages are images or garbled OCR and were rendered at 1.7-2x and read by eye; two whole-file scan covers and one 5-page file were rendered to identify them. "
            "tools/check_transcripts.py over transcripts/8100.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat income plus zakat to net income, cross-filing comparatives (restated FY2022 columns flagged) and nine Q1+Q2=H1 / H1+Q3=9M roll checks; all pass.")))
