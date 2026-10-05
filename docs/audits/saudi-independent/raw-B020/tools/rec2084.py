"""Builds raw-B020/2084.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


TXT = "text layer (clean) tied by arithmetic"
IMG = "visual (scanned statement pages rendered and read) tied by arithmetic"
documents = [
    doc("f0476a54", "FY ended 2025-12-31 audited consolidated FS (EY report 16 March 2026), label 2026|FY = publication year", False, {"bs": 8, "is": "9-10", "cf": "12-13"}, {"bs": 7, "is": "8-9", "cf": "11-12"}, TXT,
        "pdf p7 is an image-only auditor-report page, viewed; equity statement pdf p11 and notes not read; FY2024 comparatives re-presented (declared)"),
    doc("f455db46", "FY ended 2024-12-31 audited FS as issued, label 2025|FY = publication year", False, {"bs": 7, "is": "8-9", "cf": "11-12"}, {"bs": 7, "is": "8-9", "cf": "11-12"}, TXT, "FY2023 comparatives re-presented (declared)"),
    doc("a3f066cc", "FY ended 2023-12-31 audited FS as issued (Saudi Joint Stock Company - Closed), label 2024|FY = publication year", False, {"bs": "7-8", "is": 9, "cf": "12-13"}, {"bs": "7-8", "is": 9, "cf": "12-13"}, TXT),
    doc("05646437", "FY ended 2022-12-31 FS of Miahona Company Limited (LLC), signed 29 June 2023; whole-file scan; label 2024|FY is wrong (inventory period check detects 2022-12-31)", False, {"bs": 5, "is": 6, "cf": 9}, {"bs": 3, "is": 4, "cf": 7}, IMG,
        "BS liabilities totals (622,931,493 and 965,436,918 as read at 3x zoom) disagree with the component sums (622,931,487 and 965,436,912) and the 2021 column (643,776,167 read versus 643,766,167 by components); unresolved legibility, so no liabilities total is transcribed"),
    doc("413e7003", "six-month period ended 2026-06-30 interim (unaudited)", True, {"bs": 4, "is": "5-6", "cf": "8-9"}, {"bs": 3, "is": "4-5", "cf": "7-8"}, TXT),
    doc("98300ac7", "three-month period ended 2026-03-31 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, TXT),
    doc("3af14a6b", "six-month period ended 2025-06-30 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, TXT),
    doc("ef50f362", "nine-month period ended 2025-09-30 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, TXT),
    doc("7e883d6a", "three-month period ended 2025-03-31 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, TXT, "the investing-activities total line is absent from the text layer; Q1 2025 CFI -9,616,500 is known from the Q1 2026 comparatives"),
    doc("8c4b7564", "nine-month period ended 2024-09-30 interim as issued (unaudited); statement pages scanned (pdf p4-9 textless)", True, {"bs": 4, "is": 5, "oci": 6, "cf": "8-9"}, {"bs": 2, "is": 3, "oci": 4, "cf": "6-7"}, IMG,
        "9M cost of revenue digits ambiguous in the scan; value derived from revenue minus printed gross profit and from H1 + Q3 (both 167,944,649)"),
    doc("1b2ace76", "six-month period ended 2024-06-30 interim as issued (unaudited)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"}, TXT),
]

identified = {
    "43f85e2e": ("one-page scanned table headed 'Corrections' with SAR-million figures for Q3 and 9M 2024 (revenue 88.48 / 248.08, net profit 16.72 / 44.81, total comprehensive income -6.23 / 26.10), viewed",
                 "consistent with 8c4b7564 p5-6 (net profit 16,724,661 and 44,807,404; total comprehensive income -6,225,799 and 26,100,073); not a statement filing; classed scanned_unreadable but legible"),
}

spec = dict(
    symbol="2084", name="MIAHONA (Miahona Company)",
    method=("SHA-256 recomputed for every audited file. Nine of eleven statement filings have clean text layers on the statement pages (tied by arithmetic); the FY2022 LLC filing (46 of 48 pages textless) and the 9M 2024 interim (statement pages textless) were rendered and read by eye, "
            "and every line used ties to its totals, with one exception recorded in the document note (liabilities totals of the FY2022 balance sheet not transcribed). tools/check_transcripts.py over transcripts/2084.json (11 documents) checks BS identity, cash-flow sum and roll, "
            "gross profit, profit before zakat to net profit, owners + NCI, cross-filing agreement of every comparative column against the earlier filing of the same period (each larger difference carries a written reason in _declared_diff), and 51 roll checks "
            "(Q1 + Q2 = H1 and H1 + Q3 = 9M for 2026, 2025, 2024 and 2023); all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_11_filings_with_four_chains_of_re_presented_comparatives_declared",
            summary=("Full SAR. FY2025: revenue 699,654,359, gross profit 113,659,205, operating profit 83,951,077, profit before zakat 82,377,370, zakat -6,615,737, net profit 75,761,633 (owners 72,414,951, NCI 3,346,682), EPS 0.45; total assets 1,684,649,081, equity 479,016,277, liabilities 1,205,632,804, cash 305,710,999; "
                     "CFO 158,917,989, CFI -238,414,192, CFF 241,004,029, net change 161,507,826. FY2024 as issued: revenue 385,089,058, net profit 41,007,078, total assets 1,150,284,034, CFO 138,205,461. FY2023 as issued: revenue 324,462,898, net profit 56,922,114, total assets 989,339,885, CFO 132,579,327. "
                     "FY2022 as originally issued (LLC): revenue 276,023,072, net profit 50,110,047, total assets 965,436,912, equity 342,505,425, CFO 39,850,677; FY2021 net profit 25,331,852. H1 2026: revenue 233,761,394, net profit 6,467,473, total assets 1,624,441,396, CFO 2,424,038, cash 64,849,287; Q1 2026 revenue 117,712,275, net 3,108,582; Q2 2026 (own column) revenue 116,049,119, net 3,358,891. "
                     "Declared differences, never substituted: (1) FY2024 re-presented in the FY2025 filing: cost of revenue -298,631,518 versus -292,324,966, gross profit 86,457,540 versus 92,764,092, other income 6,885,469 versus 578,917 (operating profit 54,703,178, net profit and every cash-flow total unchanged); "
                     "(2) FY2023 re-presented in the FY2024 filing: cost -233,514,801 versus -215,055,671, gross profit 90,948,097 versus 109,407,227, CFO 113,207,840 versus 132,579,327, CFI -21,770,484 versus -41,608,343, CFF -23,092,528 versus -22,626,156 (operating profit 70,255,592, net profit, cash 136,166,214 unchanged); "
                     "(3) FY2022: the FY2023 filing shows total assets 963,013,736 (originally 965,436,912), cash 67,821,386 (originally 103,177,386, term deposits 35,356,000 no longer cash), CFO 60,009,671 (39,850,677), CFI -51,861,522 (-11,384,973), CFF -36,205,864 (-36,523,419), net change -28,057,715 (-8,057,715); revenue, operating profit and net profit identical; "
                     "(4) 2024 interims: H1 2025 and 9M 2025 comparatives move cost between cost of revenue and G&A (H1 2024 cost -115,729,479 versus -104,032,573 as issued; 9M 2024 -183,615,346 versus -167,944,649), the 9M 2024 comparatives differ by 2 SAR from the 9M 2024 filing in operating profit, profit before zakat and net profit (Q3 2024 revenue 88,501,460 versus 88,483,460). "
                     "Quarter rolls hold for 2026, 2025 and 2023; for 2024 own filings the nine-month revenue 248,079,325 is 7,751,170 above H1 151,844,695 plus Q3 88,483,460 because the nine-month column moves 7,751,170 from other income to revenue (revenue plus other income ties exactly; cost, G&A, profit before zakat, net profit tie), so Q3 2024 by subtraction (96,234,630) is wrong. "
                     "The Dec 2024 and Dec 2023 balance sheets agree across all filings. Cash flow Q2 by subtraction is NOT validated (Q1 2026 CFO 2,463,144 versus H1 2026 CFO 2,424,038 implies a negative Q2 of -39,106 and line layouts differ between the two statements). Q4 documents do not exist; Q4 by subtraction is NOT validated. "
                     "Notes not read, so going concern and discontinued operations were not assessed; none visible on the statement faces. The entity filed as Miahona Company Limited (LLC) for FY2022, a closed JSC for FY2023 and a Saudi Joint Stock Company in the 2024 interim titles."),
            not_read=["notes in every file", "statements of changes in equity (all files)", "auditor's reports beyond the FY2025 continuation page", "FY2022 liabilities totals (illegible digits, see document note)",
                      "Q1 2024 own filing (known only as Q1 2025 comparatives)", "FY2021 own filing", "2022 and 2023 interim filings"]),
        document_completeness=dict(
            status="statements_present_in_all_12_files_two_scans_and_labels_mixed",
            summary=("The FY2022 filing (05646437, 48 pages) is a whole-file scan with only one text-layer statement page found by the inventory (partial_statements) although it contains the balance sheet, income statement, OCI, equity and cash flow statements (pdf p5-9). "
                     "The 9M 2024 interim (8c4b7564) has textless statement pages (p4-9) although classed financial_statements. 43f85e2e (one page, scanned_unreadable) is a legible results-corrections table, not a filing. "
                     "Labels: 2024|FY holds both the FY2023 filing and the FY2022 LLC filing, 2025|FY is FY2024 and 2026|FY is FY2025 (publication-year convention), confirming the inventory period_mismatch queue for 2084. "
                     "No duplicate hashes or Arabic twins were found in this folder."),
            defect_ids=["B020-2084-1", "B020-2084-2", "B020-2084-3"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_interims_H1_2024_to_H1_2026_without_Q1_2024_by_page_derived_period",
            present_in_files_by_page_derived_period=["FY2022 (LLC, as originally issued)", "FY2023", "FY2024", "FY2025", "H1 2024", "9M 2024", "Q1 2025", "H1 2025", "9M 2025", "Q1 2026", "H1 2026"],
            values_verified_from_own_pages=["FY2022", "FY2023", "FY2024", "FY2025", "H1 2024", "9M 2024", "Q1 2025", "H1 2025", "9M 2025", "Q1 2026", "H1 2026"],
            values_known_only_as_comparatives=["FY2021 and Dec 2021 balance sheet (FY2022 filing)", "Q1 2024 (Q1 2025 filing)", "H1, Q2, 9M and Q3 2023 (2024 interims)", "Q1 2023 by subtraction only", "Q4 2024 and Q4 2025 only by subtraction"],
            values_not_read=["equity statements and notes in all filings"],
            missing=["Q1 2024 own filing", "all 2022 and 2023 interim filings", "FY2021 and earlier", "Q4 documents (none exist)", "annual reports"],
            inventory_corrections=("The inventory counts 8 of 9 periods complete; by page-derived period the 2024 to 2026 H1 interim set is complete apart from Q1 2024 (the expected window starts at 2024|H1, so Q1 2024 is not counted) and annual FY2022 to FY2025 are all present, "
                                   "FY2022 under the label 2024|FY. The partial period is 2024|9M (scan plus a corrections table). Listing date is not verified from the files.")),
    ),
    defects=[
        dict(id="B020-2084-1", **{"class": "restated_or_represented_comparatives"}, severity="high",
             evidence=("FY2024 cost/gross profit/other income re-presented in FY2025; FY2023 cost/gross profit and cash-flow totals re-presented in FY2024; FY2022 cash (103,177,386 versus 67,821,386), total assets and cash-flow totals re-presented in FY2023; "
                       "2024 interim cost versus G&A re-presented in 2025 comparatives; 9M 2024 YTD revenue includes 7,751,170 moved from other income while Q3 does not; 2 SAR differences between 9M 2024 as issued and its comparatives. Both values are kept in the transcripts.")),
        dict(id="B020-2084-2", **{"class": "image_only_statement_pages_and_scans_misclassified"}, severity="high",
             evidence="05646437 (48 pages, partial_statements, labelled 2024|FY but FY2022) and 8c4b7564 (9M 2024, textless p4-9) hold full statements as images; 43f85e2e is a scanned corrections table."),
        dict(id="B020-2084-3", **{"class": "fiscal_year_label_is_publication_year"}, severity="medium",
             evidence="2024|FY holds FY2023 (a3f066cc) and FY2022 (05646437); 2025|FY is FY2024 (f455db46); 2026|FY is FY2025 (f0476a54)."),
        dict(id="B020-2084-4", **{"class": "source_total_not_legible_or_inconsistent"}, severity="low",
             evidence="FY2022 LLC balance sheet: printed liabilities and equity-and-liabilities totals read 622,931,493 / 965,436,918 (2021: 643,776,167) at 3x zoom, versus component sums 622,931,487 / 965,436,912 (643,766,167); asset side and equity tie exactly. Could be scan digit confusion or a source imbalance of 6 SAR; unresolved."),
        dict(id="B020-2084-5", **{"class": "interim_flow_not_comparable_for_subtraction"}, severity="medium",
             evidence="9M 2024 revenue minus H1 2024 revenue (96,234,630) differs from the reported Q3 2024 revenue 88,483,460; cash-flow Q2 by subtraction not validated for 2026."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "auditor's reports", "Q1 2024 own filing", "2022 and 2023 interim filings", "FY2022 liabilities totals", "pre-2022 history"],
    conclusion=("NOT claimed complete. 11 filings value-verified (two from scans) with exact identities, cross-filing comparison and quarter rolls; four chains of re-presented comparatives and a year-to-date reclassification recorded without substitution; "
                "notes and equity statements unread; no Q1 2024, 2022-2023 interim or Q4 documents."),
)
mkrecord.build(spec)
