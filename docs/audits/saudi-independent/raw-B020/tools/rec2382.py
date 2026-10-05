"""Builds raw-B020/2382.json (audit record) from the page transcripts."""
import mkrecord

K = "SAR thousands"
F = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, units=K, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=units, reading=reading)
    if note:
        d["note"] = note
    return d


TXT = "text layer (clean) tied by arithmetic"
documents = [
    doc("18b45d3c", "FY ended 2025-12-31 audited consolidated FS (EY), label 2026|FY = publication year", False, {"bs": "8-9", "is": 10, "cf": "13-14"}, {"bs": "1-2", "is": 3, "cf": "6-7"}, TXT,
        note="equity statement pdf p11-12 and notes not read; FY2024 comparatives re-presented (declared)"),
    doc("d1d9ccba", "FY ended 2024-12-31 audited FS as issued (EY report 3 March 2025), label 2025|FY = publication year", False, {"is": 8, "bs": 9, "cf": "12-13"}, {"is": 2, "bs": 3, "cf": "6-7"}, TXT,
        note="pdf p7 (auditor report page, image-only) viewed; its statement pages have clean text; the prior column is the 28 Dec 2022 to 31 Dec 2023 period"),
    doc("dc1de08f", "period 28 Dec 2022 (incorporation) to 31 Dec 2023, audited consolidated FS as issued, label 2024|FY = publication year", False, {"is": 8, "bs": 9, "cf": 11}, {"is": 6, "bs": 7, "cf": 9}, TXT, F,
        note="no 2022 comparative column; first page textless auditor page not opened"),
    doc("73667c41", "special purpose consolidated FS 2022, 2021, 2020 of ADES Holding Company (Mixed Closed JSC), approved 12 March 2023; label 2024|FY is wrong", False, {"is": 5, "bs": 6, "cf": 10}, {"is": 1, "bs": 2, "cf": 6}, TXT, F,
        note="three-year pre-IPO special-purpose perimeter; pdf p2-4 textless auditor pages not opened; EPS cell reads 474,998 in the text layer and was not recorded"),
    doc("a111cf61", "six-month period ended 2026-06-30 interim (unaudited)", True, {"bs": "5-6", "is": 7, "cf": "10-11"}, {"bs": "1-2", "is": 3, "cf": "6-7"}, TXT, note="EPS caption reads In $ per share in the file"),
    doc("6a5c0453", "three-month period ended 2026-03-31 interim (unaudited)", True, {"bs": "5-6", "is": 7, "cf": "10-11"}, {"bs": "1-2", "is": 3, "cf": "6-7"}, TXT),
    doc("1152c9a9", "six-month period ended 2025-06-30 interim (unaudited)", True, {"bs": "5-6", "is": 7, "cf": 9}, {"bs": "1-2", "is": 3, "cf": 5}, TXT),
    doc("8be70142", "nine-month period ended 2025-09-30 interim (unaudited)", True, {"bs": "5-6", "is": 7, "cf": "9-10"}, {"bs": "1-2", "is": 3, "cf": "5-6"}, TXT),
    doc("bd69ad32", "three-month period ended 2025-03-31 interim (unaudited)", True, {"is": 3, "bs": 4, "cf": 7}, {"is": 2, "bs": 3, "cf": 6}, TXT),
    doc("cc3168a8", "nine-month period ended 2024-09-30 interim (unaudited)", True, {"is": 3, "bs": 4, "cf": 7}, {"is": 2, "bs": 3, "cf": 6}, TXT,
        note="BS cash 883,392 includes escrow 71,251 that is excluded from cash in the cash flow (note p14)"),
    doc("6bf7ba99", "six-month period ended 2024-06-30 interim (unaudited)", True, {"is": 3, "bs": 4, "cf": 7}, {"is": 2, "bs": 3, "cf": 6}, TXT),
    doc("15426fd5", "three-month period ended 2024-03-31 interim (unaudited); b9a77c0c is a text-identical copy", True, {"is": 3, "bs": 4, "cf": 7}, {"is": 2, "bs": 3, "cf": 6}, TXT + " (selected lines)"),
    doc("44b81bc8", "nine-month period ended 2023-09-30 interim (unaudited)", True, {"is": 3, "bs": 4, "cf": 7}, {"is": 2, "bs": 3, "cf": 6}, TXT, F,
        note="PBT, tax and Dec 2022 PPE later re-presented (declared)"),
    doc("b1e2a770", "Arabic twin of the 9M 2023 interim (revenue 3,059,554,355 matches); only that line read", True, {"is": 3}, {}, "text layer, revenue line only", F),
]

identified = {
    "dc832bb5": ("Arabic FS for the period 28 Dec 2022 to 31 Dec 2023 (cover text); revenue 4,331,902,893 appears on p7, p31, p32; label 2023|FY", "Arabic twin of dc1de08f by revenue match; statements not transcribed; pdf p6 textless"),
    "399bc59c": ("Arabic FS for the year ended 2024-12-31 (cover text); revenue 6,199,022 on p7 and CFO 2,998,780 on p11 match d1d9ccba; label 2024|None", "Arabic twin of d1d9ccba by two matched figures; not transcribed; pdf p6 textless"),
    "eb642eb8": ("Arabic 9M 2024 interim (cover text); revenue 4,629,953 matches cc3168a8", "Arabic twin; not transcribed; pdf p2 textless"),
    "8aff6575": ("Arabic Q1 2024 interim (cover text); revenue 1,532,070 matches 15426fd5", "Arabic twin; not transcribed; pdf p2 textless"),
    "b9a77c0c": ("Q1 2024 interim, English; all 33 pages text-identical to 15426fd5 (different source URLs: Saudi Exchange vs issuer site)", "byte-different duplicate; not separately transcribed"),
    "0934a610": ("9M 2023 trading update presentation (25 pages), not FS; text-identical to e7247ebe", "duplicate presentation, classed other_no_statements_found"),
    "e7247ebe": ("9M 2023 trading update presentation (25 pages), duplicate of 0934a610", "presentation, not FS"),
    "6e72b5c7": ("9M 2023 results announcement (6 pages, as at 30 September 2023)", "announcement text, not read for values"),
    "d0b52be4": ("FY 2024 earnings release (11 pages)", "announcement, not read for values"),
    "5f719c5c": ("1H 2024 earnings release (10 pages)", "announcement, not read for values"),
    "d1ff685c": ("FY 2025 earnings release (11 pages)", "announcement, not read for values"),
    "3c8d1101": ("1H 2026 earnings release (11 pages)", "announcement, not read for values"),
    "a2c10c6e": ("presentation slides (11 pages), collector label 2025|9M, period not verified", "other_no_statements_found; not opened beyond classification"),
}

spec = dict(
    symbol="2382", name="ADES (ADES Holding Company)",
    method=("SHA-256 recomputed for every audited file. Every statement filing opened has a clean text layer on its statement pages (the textless pages are auditor-report pages; pdf p7 of the FY2024 file was rendered and viewed), "
            "so values were read from the text layer and every filing was tied by arithmetic. tools/check_transcripts.py over transcripts/2382.json (14 documents) checks BS identity, cash-flow sum and roll, gross profit, profit before tax to net profit, owners + NCI, "
            "cross-filing agreement of every comparative column against the earlier filing of the same period (filings in full SAR versus SAR thousands compared with a 1.5 thousand rounding tolerance; every larger difference carries a written reason), "
            "and quarter rolls Q1 + Q2 = H1 and H1 + Q3 = 9M for 2025, 2024 and (with 1 thousand tolerance) 2023; all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_14_filings_with_three_declared_representations",
            summary=("FY2025 (SAR thousands): revenue 6,688,959, gross profit 2,533,091, profit before tax and zakat 1,044,928, income tax and zakat -212,067, net profit 832,861 (owners 818,016, NCI 14,845), EPS 0.74; total assets 31,411,709, equity 6,812,994, liabilities 24,598,715, "
                     "cash 2,458,449; CFO 2,980,723, CFI -2,732,219, CFF 1,465,758, net change 1,714,262, capex -1,837,878. FY2024 as issued: revenue 6,199,022, net profit 816,195, total assets 21,628,690, CFO 2,998,780. "
                     "Period 28 Dec 2022 to 31 Dec 2023 (full SAR): revenue 4,331,902,893, net profit 452,078,758, total assets 19,422,450,754, CFO 2,282,706,055. FY2022 special-purpose (full SAR): revenue 2,467,200,801, net profit 397,621,942, total assets 14,501,345,645, CFO 1,146,247,852; FY2021 net 114,428,590; FY2020 net 82,580,678. "
                     "H1 2026: revenue 4,544,065, net profit 374,121, total assets 31,677,705, CFO 1,497,493; Q1 2026: revenue 2,390,736, net 240,853; Q2 2026 (own column) revenue 2,153,329, net 133,268. "
                     "Declared differences, never substituted: (1) the FY2025 filing re-presents FY2024: cost of revenue -3,841,373 versus -3,839,972 as issued, gross profit 2,357,649 versus 2,359,050, CFO 2,995,912 versus 2,998,780 and CFI -3,182,435 versus -3,185,303 (profit before tax 970,846, net profit 816,195, cash 744,187 unchanged); "
                     "(2) the FY2024 filing's 2023 comparatives differ from the FY2023 filing in the cash flow only (CFO 2,282,704 versus 2,282,706 thousand, CFF 1,886,063 versus 1,886,061, loans proceeds and repayments shown gross, 3,447,680 and -3,650,568 versus 3,351,737 and -3,554,625); "
                     "(3) the 9M 2024 comparatives re-present 9M 2023 profit before tax 331,407 (originally 347,730,492) and tax -48,335 (originally -64,658,237) with net profit 283,072 identical, and Dec 2022 PPE is 12,066,091,416 in the 9M 2023 filing versus 12,188,121,186 in the special-purpose filing (difference 122,029,770, total assets identical). "
                     "H1 2024, 9M 2024, Q1 2025, H1 2025 and the 2024 comparatives in the 2025 and 2026 filings agree to the thousand with the 2024 own filings. Roll checks: Q1 + Q2 = H1 and H1 + Q3 = 9M hold for revenue, cost, gross profit, pbt, tax, net profit, owners and NCI in 2026, 2025, 2024 and 2023 (2023 pbt and tax within 1 thousand rounding). "
                     "Cash: the FY2023 filing starts cash at 0 (period from incorporation) while the 2023 interim and comparative cash flows start from 190,829 thousand (combined cash at Dec 2022, equal to the special-purpose FY2022 cash 190,828,971); the 9M 2024 balance sheet cash 883,392 includes an escrow 71,251 excluded from cash in the cash flow (812,141). "
                     "Q2 by subtraction: income statement lines are consistent (the H1 2026 file prints its own Q2 column and it equals H1 minus Q1); cash flow Q2 by subtraction is NOT validated (Q1 2026 adds back tax provisions 764 while H1 2026 shows a reversal of -67,510; Q1 2026 CFO 760,907 versus H1 2026 1,497,493). "
                     "Q4 2025 by subtraction (FY2025 minus 9M 2025: net profit 225,355, revenue 1,986,061) is NOT validated because the FY2025 statements re-present lines (gain on equity instruments 88,778 versus 85,744 in the 9M filing) and there is no Q4 document in the raw archive."),
            not_read=["notes in every file (going concern, discontinued operations, subsequent events not assessed)", "statements of changes in equity", "auditor's reports beyond the FY2024 continuation page", "Arabic twins (identified by matched figures only)",
                      "earnings releases and presentations", "Q1 2023 and H1 2023 own filings (known only as comparatives)", "2022 interim data (9M 2022 known only as comparatives)", "FY2022 special-purpose EPS and notes"]),
        document_completeness=dict(
            status="statement_pages_text_clean_in_all_value_read_filings_labels_and_perimeters_inconsistent",
            summary=("All statement filings have clean statement text; the inventory flags 8 files with no statements (announcements, presentations), correctly, and its period_mismatch queue is right: FY labels are publication years (2026|FY = FY2025, 2025|FY = FY2024, 2024|FY holds both FY2023 and the FY2022 special-purpose filing), "
                     "2023|FY holds the Arabic FY2023 file and 2024|None the Arabic FY2024 file. Five Arabic twins and one duplicate English pair (15426fd5/b9a77c0c, 33 pages identical) and one duplicate presentation pair exist; the inventory text-duplicate flags are confirmed. "
                     "The FY2023 filing covers 28 Dec 2022 to 31 Dec 2023 with no 2022 column; 2022 exists only in a pre-IPO special-purpose filing for the same group (Mixed Closed JSC), so FY2022 is a different report basis from FY2023 onward (opening equity 2,258,430,544 ties to the reorganisation line)."),
            defect_ids=["B020-2382-1", "B020-2382-2", "B020-2382-3"]),
        company_coverage=dict(
            status="annual_FY2022sp_FY2023_FY2024_FY2025_interims_9M2023_to_H12026_complete_by_page_derived_period",
            present_in_files_by_page_derived_period=["FY2022 (special purpose, with FY2021 and FY2020)", "FY2023 (period from 28 Dec 2022)", "FY2024", "FY2025", "9M 2023", "Q1 2024", "H1 2024", "9M 2024", "Q1 2025", "H1 2025", "9M 2025", "Q1 2026", "H1 2026"],
            values_verified_from_own_pages=["FY2022 special purpose", "FY2023", "FY2024", "FY2025", "9M 2023", "Q1 2024", "H1 2024", "9M 2024", "Q1 2025", "H1 2025", "9M 2025", "Q1 2026", "H1 2026"],
            values_known_only_as_comparatives=["Q1 2023", "H1 2023", "Q2 and Q3 2023", "9M 2022 and Q3 2022 (9M 2023 filing)", "FY2021 and FY2020 (inside the special-purpose filing)", "Q4 2023 and Q4 2024 and Q4 2025 only by subtraction, not as documents"],
            values_not_read=["Arabic twins of FY2023, FY2024, 9M 2023, 9M 2024, Q1 2024", "earnings releases and presentations"],
            missing=["2022 interim filings and anything before FY2020", "Q1 2023 and H1 2023 own filings", "FY2022 as a statutory-perimeter filing", "annual reports"],
            inventory_corrections=("The inventory counts 12 of 12 expected periods complete; by page-derived period that is right for 2023|9M to 2026|H1 as labelled, but 2024|FY holds FY2023 and the FY2022 special-purpose filing, 2025|FY holds FY2024, 2026|FY holds FY2025 and the true FY2025 slot "
                                   "is the 2026|FY file; the inventory 'periods complete' count therefore overstates distinct periods. No Q4 document exists for any year.")),
    ),
    defects=[
        dict(id="B020-2382-1", **{"class": "restated_or_represented_comparatives"}, severity="high",
             evidence=("FY2024 as issued versus FY2025 comparatives: cost of revenue -3,839,972 vs -3,841,373, gross profit 2,359,050 vs 2,357,649, CFO 2,998,780 vs 2,995,912, CFI -3,185,303 vs -3,182,435; "
                       "9M 2023 pbt 347,730,492 vs 331,407 thousand and tax -64,658,237 vs -48,335 thousand; Dec 2022 PPE 12,066,091,416 vs 12,188,121,186; FY2023 CFO and CFF differ by 2 thousand between the FY2023 and FY2024 filings. Both versions are kept in the transcript with declared differences.")),
        dict(id="B020-2382-2", **{"class": "fiscal_year_label_is_publication_year_and_mixed_labels"}, severity="medium",
             evidence="2026|FY is FY2025 (18b45d3c), 2025|FY is FY2024 (d1d9ccba), 2024|FY holds FY2023 (dc1de08f) and the FY2022 special-purpose filing (73667c41), 2023|FY holds the Arabic FY2023 (dc832bb5), 2024|None holds the Arabic FY2024 (399bc59c)."),
        dict(id="B020-2382-3", **{"class": "duplicates_and_arabic_twins"}, severity="low",
             evidence="15426fd5 and b9a77c0c text-identical on all 33 pages; 0934a610 and e7247ebe text-identical on all 25 pages; Arabic twins dc832bb5, 399bc59c, eb642eb8, 8aff6575, b1e2a770 share figures with their English files."),
        dict(id="B020-2382-4", **{"class": "perimeter_and_cash_definition_changes"}, severity="medium",
             evidence="FY2023 covers a period from 28 Dec 2022 with opening cash 0 while 2023 interim cash flows open at 190,829 thousand; FY2022 exists only as a special-purpose pre-IPO filing; 9M 2024 BS cash 883,392 vs cash flow cash 812,141 (escrow 71,251)."),
        dict(id="B020-2382-5", **{"class": "interim_flow_not_comparable_for_subtraction"}, severity="medium",
             evidence="Cash-flow Q2 and Q4 by subtraction not validated (Q1 2026 tax provision +764 vs H1 2026 reversal -67,510); FY2025 re-presents lines relative to the 9M 2025 filing; EPS caption In $ per share in the H1 2026 file."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "auditor's reports", "Arabic twins", "earnings releases and presentations", "Q1 and H1 2023 own filings", "Q4 documents (none in raw archive)", "2022 interim filings (none in raw archive)"],
    conclusion=("NOT claimed complete. 14 filings value-verified from clean text with exact identities, cross-filing comparison and quarter rolls; three groups of re-presented comparatives and perimeter changes recorded without substitution; "
                "no Q4 documents, no 2022 interims, notes and equity statements unread."),
)
mkrecord.build(spec)
