"""Builds raw-B020/2250.json (audit record) from the page transcripts."""
import mkrecord

U = "SAR thousands"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


VIS = "visual (statement pages textless, rendered and read)"
TXT = "text layer (clean) tied by arithmetic"
documents = [
    doc("8af24f13", "FY ended 2025-12-31 audited consolidated FS (PwC), label 2026|FY = publication year", False, {"bs": 8, "is": 9, "cf": 12}, {"bs": 7, "is": 8, "cf": 11}, VIS,
        "equity statement pdf p10-11 not read; the extra transcribed lines are headline only"),
    doc("71e433f7", "FY ended 2024-12-31 audited FS, label 2025|FY = publication year", False, {"bs": 8, "is": 9, "cf": 11}, {"bs": 7, "is": 8, "cf": 10}, VIS),
    doc("874ddc6d", "FY ended 2023-12-31 audited FS, label 2024|FY = publication year", False, {"bs": 9, "is": 10, "cf": 12}, {"bs": 8, "is": 9, "cf": 11}, VIS,
        "the page printed 11 is the cash flow statement although headed 'statement of changes in equity' in the file"),
    doc("c2ddeaca", "FY ended 2022-12-31 audited FS, label 2023|FY = publication year", False, {"bs": 9, "is": 10, "cf": 12}, {"bs": 8, "is": 9, "cf": 11}, VIS,
        "the cash flow page is headed 'profit or loss and other comprehensive income' in the file"),
    doc("989c9047", "three-month period and year ended 2025-12-31 (Q4 2025 interim, unaudited); collector label 2025|Q1 is wrong", False, {"is": 5}, {"is": 4}, VIS,
        "only the income statement page was read; BS, equity and CF pages (pdf p4, 6-9) not read"),
    doc("d59eef41", "three-month period and year ended 2022-12-31 (Q4 2022 interim, unaudited); whole-file scan with no collector period (None|None), classed other_no_statements_found",
        False, {"is": 5}, {"is": 4}, "visual (whole-file scan, income statement page rendered and read)", "BS, equity and CF pages not read"),
    doc("e0ce5fe2", "nine-month period ended 2025-09-30 interim", True, {"is": 5}, {"is": 4}, VIS, "BS and CF pages (pdf p4, 6-8) textless, not read"),
    doc("dacda519", "six-month period ended 2025-06-30 interim", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6}, TXT, "equity statement pdf p6 textless, not read"),
    doc("83284b75", "three-month period ended 2025-03-31 interim", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 6}, TXT + " (headline lines only)"),
    doc("d9ac88b0", "three-month period ended 2026-03-31 interim", True, {"bs": 4, "is": 5, "cf": 7}, {"bs": 3, "is": 4, "cf": 7}, TXT, "equity statement pdf p6 textless, not read"),
    doc("b81f30d6", "six-month period ended 2026-06-30 interim (review report 29 July 2026)", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 3, "is": 4, "cf": 7},
        "visual (text layer is scrambled; BS, IS and CF rendered and read)", "equity statement pdf p6-7 text garbled, not transcribed"),
]

identified = {
    "f77fab93": ("3M ended 2022-03-31 (cover text)", "statements text-extractable per inventory; not transcribed"),
    "700d01f1": ("6M ended 2022-06-30 (cover text)", "pdf p4-7 textless; not transcribed"),
    "3d1cdf9c": ("9M ended 2022-09-30 (cover text)", "pdf p4-7 textless; not transcribed"),
    "d0f79f7b": ("3M ended 2023-03-31 (cover text)", "pdf p4-7 textless; not transcribed"),
    "cced33ab": ("6M ended 2023-06-30 (cover text)", "pdf p6 textless; not transcribed"),
    "735d94c8": ("9M ended 2023-09-30 (cover text)", "pdf p4-7 textless; not transcribed"),
    "2a5697cd": ("three-month period and year ended 2023-12-31 (Q4 2023 interim, cover text); collector label 2023|Q1 is wrong", "pdf p4-8 textless; not transcribed; FY2023 and Q4 2023 not separately read"),
    "d4e0d5d4": ("3M ended 2024-03-31 (cover text)", "pdf p4-7 textless; not transcribed; Q1 2024 known as comparative (27,532 net) from the Q1 2025 filing"),
    "8cea463d": ("6M ended 2024-06-30 (cover text)", "pdf p4-7 textless; not transcribed; H1 2024 known as comparatives from the H1 2025 filing"),
    "24e6c59b": ("9M ended 2024-09-30 (cover text)", "pdf p4-7 textless; not transcribed; 9M 2024 known as comparatives from the 9M 2025 filing"),
    "353b12bd": ("three-month period and year ended 2024-12-31 (Q4 2024 interim, cover text); collector label 2024|Q1 is wrong", "pdf p4-7 textless; not transcribed; Q4 2024 known as comparatives from the Q4 2025 filing"),
}

spec = dict(
    symbol="2250", name="SIIG (Saudi Industrial Investment Group Company)",
    method=("SHA-256 recomputed for every audited file. Annual FY2022 to FY2025, the Q4 2025 and Q4 2022 interims (income statement), the 9M 2025 interim and the H1 2026 interim have image-only statement pages (or a scrambled text layer) and were rendered and read by eye; "
            "the H1 2025, Q1 2025 and Q1 2026 filings have clean text layers on the statement pages and were tied by arithmetic. tools/check_transcripts.py over transcripts/2250.json checks BS identity (assets = liabilities + equity), "
            "cash-flow sum and roll, profit before zakat to net profit, owners + NCI, cross-filing agreement of every comparative column against the earlier filing of the same period, and rolls Q1 + Q2 = H1, H1 + Q3 = 9M, 9M + Q4 = FY "
            "for 2025 and 2024 (net profit, profit before zakat, operating profit, equity-method income); all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_11_filings_no_restatement_found_comparatives_agree",
            summary=("SAR thousands. SIIG is a holding company with no revenue line: the operating line is the share of net profit of investments accounted for using the equity method less G&A. "
                     "FY2025: share of equity-method result -84,365, operating loss -156,472, loss before zakat -133,846, zakat credit 29,743, net loss -104,103 (owners -103,672, NCI -431), EPS -0.15; total assets 8,822,747, equity 8,621,855 (owners 8,597,761, NCI 24,094), "
                     "liabilities 200,892, cash 399,645; CFO 275,644, CFI 301,974, CFF -1,097,041 (capital reduction -754,800, treasury shares -200,117, dividends -166,649), net change -519,423. "
                     "FY2024: net profit 201,243, total assets 10,101,448, CFO 779,813 (dividends from joint ventures 877,500), CFF -754,296. FY2023: net 112,201, total assets 10,772,372, CFO 43,621. FY2022: net 393,683 (owners 277,440, NCI 116,243), total assets 11,054,211, CFO 473,458; "
                     "FY2021: net 1,817,773 (owners 1,136,272, NCI 681,501), total assets 12,311,449, EPS 2.53 (from the FY2022 filing). Every comparative column agrees with the earlier filing of the same period; no restatement of net profit, equity or cash was found. "
                     "Presentation differences recorded, not substituted: the FY2022 cash flow shows placements in short-term deposits net (-748,030) while the FY2023 filing shows maturities 497,000 and placements -1,245,030 gross (CFI -392,403 identical); the FY2023 filing folds finance costs into finance income - net. "
                     "Quarter rolls (all exact): Q1 2026 251,796 + Q2 2026 -59,049 = H1 2026 192,747; Q1 2025 18,233 + Q2 2025 19,627 = H1 2025 37,860; + Q3 8,333 = 9M 46,193; + Q4 2025 -150,296 = FY2025 -104,103; 2024: 27,532 + 64,367 = 91,899; + 98,086 = 189,985; + Q4 11,258 = FY2024 201,243. "
                     "Q4 2022 net -296,436 (year 393,683, so 9M 2022 = 690,119 by subtraction only, 9M 2022 filing not read). 2026 events: H1 2026 net profit 192,747 (owners 193,809, NCI -1,062), total assets 8,996,297; Q1 2026 net 251,796. Bioprotein subsidiary (80%) formed in Q3 2025 explains NCI from 2025. "
                     "Interim cash flow: Q1 2026 CFO -13,800 versus H1 2026 CFO -46,795 (Q2 by subtraction -32,995); Q1 2025 CFO 36,479 versus H1 2025 91,495. Line labels are not stable between interim and annual statements: the 97,500 received in H1 2024 is 'proceeds from a related party' in the H1 2025 filing's comparative column but 'reduction in share capital of joint ventures' (97,500) in the FY2024 cash flow, so interim investing lines must not be mapped by label. "
                     "Going concern: none noted in the pages read. No discontinued operations."),
            not_read=["notes in every file", "statements of changes in equity (all files)", "auditor's report text beyond cover/opinion pages", "BS and CF pages of the Q4 2025, Q4 2022 and 9M 2025 interims",
                      "2022 Q1, H1, 9M, 2023 Q1, H1, 9M, Q4, 2024 Q1, H1, 9M, Q4 own filings (known only partly as comparatives)", "FY2021 own filing (known only as FY2022 comparatives)"]),
        document_completeness=dict(
            status="statements_present_in_all_22_files_but_most_statement_pages_image_only_and_four_files_mislabelled",
            summary=("The four annual files, the Q4 and 9M interims and the older interims have textless statement pages (annual pdf p8-12; interims p4-8) although the inventory classes them financial_statements with text-extractable pages (statement_pages point at note pages); "
                     "H1 2026 has textless BS and IS pages (p4-5) and a scrambled text layer on the cash flow and equity pages; H1 2025, Q1 2025 and Q1 2026 have clean statement text with only the equity page textless; one file (d59eef41) is a whole-file scan (23 pages, Xerox) with no period label and class other_no_statements_found although it is the Q4 2022 interim with an income statement. "
                     "Four Q4 interims (three-month period and year ended 31 December) are labelled Q1 by the collector: d59eef41 (None|None), 2a5697cd (2023|Q1), 353b12bd (2024|Q1), 989c9047 (2025|Q1); each shares its label with a true Q1 file. "
                     "Annual FY files are labelled with the publication year (2023|FY holds FY2022 etc.). Statement page headings in the FY2022 and FY2023 files are wrong in the files themselves (cash flow page headed OCI / changes in equity)."),
            defect_ids=["B020-2250-1", "B020-2250-2", "B020-2250-3"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_all_four_quarters_2022_to_2025_interims_2026Q1_H1_by_page_derived_periods",
            present_in_files_by_page_derived_period=["FY2022", "FY2023", "FY2024", "FY2025", "Q4 2022", "Q4 2023", "Q4 2024", "Q4 2025", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M",
                                                    "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            values_verified_from_own_pages=["FY2022", "FY2023", "FY2024", "FY2025", "Q4 2022 (income statement)", "Q4 2025 (income statement)", "2025 9M (income statement)", "2025 H1", "2025 Q1", "2026 Q1", "2026 H1"],
            values_known_only_as_comparatives=["FY2021 (FY2022 filing)", "Q4 2021 (Q4 2022 filing)", "2024 Q1, H1, 9M, Q4 (2025 filings)", "Q3 2024 and Q3 2025 (9M 2025 filing)"],
            values_not_read=["2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "Q4 2023 own filing", "2024 Q1", "2024 H1", "2024 9M", "Q4 2024 own filing"],
            missing=["FY2021 standalone and everything before FY2021 (collector horizon; inventory lists 2010 to 2021 as leading gaps, none of those files were collected)", "annual reports"],
            inventory_corrections=("The inventory counts 8 of 60 expected periods complete and 43 absent because the expected window starts at 2010|FY; by page-derived period the 2022 to 2026 H1 span is fully covered (22 files for 22 interim and annual blocks) and the 'internal gap 2022|FY' is the FY2021 filing, "
                                   "not collected but known as comparatives. FY labels are publication years (2023|FY = FY2022 ... 2026|FY = FY2025); four Q4 interims carry Q1 labels.")),
    ),
    defects=[
        dict(id="B020-2250-1", **{"class": "image_only_statement_pages_not_detected"}, severity="high",
             evidence="c2ddeaca, 874ddc6d, 71e433f7, 8af24f13 (pdf p8-12), 989c9047, e0ce5fe2 and earlier interims (pdf p4-8) have textless statement pages; d59eef41 is a whole-file scan classed other_no_statements_found; b81f30d6 text layer scrambled."),
        dict(id="B020-2250-2", **{"class": "q4_interim_labelled_q1"}, severity="high",
             evidence="d59eef41 (None|None, Q4 2022), 2a5697cd (2023|Q1, Q4 2023), 353b12bd (2024|Q1, Q4 2024), 989c9047 (2025|Q1, Q4 2025): covers read 'three-month period and year ended 31 December'. The inventory's period_mismatch queue flags three of them; d59eef41 has no period at all."),
        dict(id="B020-2250-3", **{"class": "fiscal_year_label_is_publication_year"}, severity="medium",
             evidence="2023|FY is FY2022, 2024|FY is FY2023, 2025|FY is FY2024, 2026|FY is FY2025 (cover and statement headings)."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "auditor's reports", "2022 to 2024 interim filings (11 files) not value-read", "BS and CF pages of Q4 2025, Q4 2022, 9M 2025", "FY2021 standalone and pre-2021 history"],
    conclusion=("NOT claimed complete. 11 filings value-verified from pages or clean text with exact identities, cross-filing agreement and quarter rolls; 11 further files identified by cover only and not value-read; "
                "no pre-2021 history in the raw archive; statement-level notes and equity statements unread."),
)
mkrecord.build(spec)
