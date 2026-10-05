"""Builds raw-B020/2288.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


TXT = "text layer (clean) tied by arithmetic"
SCAN = "visual (whole-file Arabic scan, Arabic-Indic digits) tied by arithmetic"
documents = [
    doc("e0dc6e6f", "FY ended 2025-12-31 audited FS, label 2026|FY = publication year", False, {"bs": 6, "is": 7, "cf": "9-10"}, {"bs": 4, "is": 5, "cf": "7-8"}, TXT, "pdf p3-5 textless (not opened); equity statement p8 and notes not read"),
    doc("c0a96163", "FY ended 2024-12-31 audited FS as issued, label 2025|FY = publication year", False, {"bs": 6, "is": 7, "cf": 9}, {"bs": 4, "is": 5, "cf": 7}, "text layer for BS and CF totals tied by arithmetic; income statement page rendered and read",
        "the text layer splits some digits across lines; no value was used unless it ties"),
    doc("9d036ce5", "FY ended 2023-12-31 audited FS as issued, Arabic scan (33 pages); label 2024|FY = publication year; income statement page only", False, {"is": 7}, {"is": 5}, SCAN,
        "BS, equity, CF and notes pages not read; FY2023 balance sheet and cash flow are known from the FY2024 filing's comparatives"),
    doc("4f4be7af", "FY ended 2022-12-31 audited FS as issued, Arabic scan (28 pages); label 2023|FY = publication year; BS and IS pages", False, {"bs": 6, "is": 7}, {"bs": 3, "is": 4}, SCAN,
        "CF page (pdf p9, printed 6) was rendered and read but its digits do not tie (CFO 56,348,938, CFI -22,359,904, CFF -12,992,118 read, net change 20,992,816 read, ending cash 28,346,642) so no cash-flow value is transcribed; BS totals taken from clean comparatives that match the scan to within one ambiguous digit"),
    doc("35e63450", "six-month period ended 2026-06-30 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, TXT),
    doc("47c2d415", "three-month period ended 2026-03-31 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, TXT),
    doc("04ac1de0", "six-month period ended 2025-06-30 interim as issued (unaudited)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, TXT + " (selected lines; CFI, CFF and ending cash lines scrambled in the text and not transcribed)"),
    doc("5ee1f67a", "nine-month period ended 2025-09-30 interim (unaudited)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, TXT + " (selected lines; CFI, CFF and ending cash not transcribed)"),
    doc("58588e3a", "three-month period ended 2025-03-31 interim as issued (unaudited)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, TXT + " (selected lines)"),
    doc("2ead71ac", "six-month period ended 2024-06-30 interim as issued (unaudited)", True, {"bs": 4, "is": 5, "cf": "7-8"}, {"bs": 2, "is": 3, "cf": "5-6"}, TXT),
    doc("192af7ac", "six-month period ended 2023-06-30 interim as issued (unaudited)", True, {"bs": 4, "is": 5}, {"bs": 2, "is": 3}, TXT, "cash-flow page not read (the inventory finds no cash flow statement in the file)"),
]
identified = {}

spec = dict(
    symbol="2288", name="NOFOTH (Nofoth Food Products Company)",
    method=("SHA-256 recomputed for every file (all 11 inventory files were opened). Nine filings have clean text layers on the statement pages and were tied by arithmetic; the FY2022 and FY2023 annual files are whole-file Arabic scans (classed scanned_unreadable) "
            "and their statement pages were rendered and read by eye in Arabic-Indic digits. tools/check_transcripts.py over transcripts/2288.json (11 documents) checks BS identity, cash-flow sum and roll, gross profit, profit before zakat to net profit, "
            "cross-filing agreement of every comparative column (each larger difference carries a written reason) and Q1 + Q2 = H1, H1 + Q3 = 9M rolls for 2025 and 2024 and the 2026 Q1 + Q2 roll; all pass."),
    documents=documents, identified=identified,
    dimensions=dict(
        value_correctness=dict(
            status="verified_for_11_filings_with_cash_flow_reclassifications_and_bonus_issue_eps_restatements_declared",
            summary=("Full SAR. FY2025: sales 429,604,219, gross profit 267,005,912, profit from operations 55,996,572, profit before zakat 58,206,587, net profit 56,742,175, EPS 0.60; total assets 275,802,474, equity 185,333,019, liabilities 90,469,455, cash 6,409,575; "
                     "CFO 60,386,005, CFI -24,911,390, CFF -32,840,087, net change 2,634,528. FY2024 as issued: sales 365,059,686, net profit 51,636,185, total assets 235,756,759, CFO 93,728,021, EPS 1.08. FY2023: sales 308,189,985, net profit 42,670,755, total assets 162,867,287, CFO 69,062,490, EPS 1.78 as issued. "
                     "FY2022 (Arabic scan): sales 268,819,480, net profit 31,486,711, total assets 123,397,680. H1 2026: sales 215,508,401, net profit 24,598,220, total assets 289,405,944, CFO 32,462,575; Q1 2026 sales 109,358,396, net 14,318,465; Q2 2026 sales 106,150,005, net 10,279,755. "
                     "Declared differences, never substituted: (1) FY2024 cash flow re-presented in the FY2025 filing (CFO 90,360,701 versus 93,728,021 as issued, CFI -62,014,634 versus -65,381,954, the 3,367,320 murabaha income receipt moved; net change -6,575,375 unchanged); "
                     "(2) the same reclassification in the interims: Q1 2025 CFO 20,118,128 as issued versus 18,237,862 in the Q1 2026 filing (1,880,266), H1 2025 CFO 35,233,995 versus 33,520,325; "
                     "(3) EPS restated for bonus issues: FY2024 1.08 as issued versus 0.54, FY2023 1.78 versus 0.89, Q1 2025 0.42 as issued versus 0.21 in the Q1 2026 filing (share capital 24,000,000 to 48,000,000 to 96,000,000); "
                     "(4) FY2022 sales 268,819,480 in the FY2022 scan versus 270,199,270 in the FY2023 scan (gross profit 146,378,240 versus 147,758,030; profit before zakat 32,374,634 and net profit 31,486,711 identical); "
                     "(5) FY2023 as issued shows main operating profit 42,728,293 before the expected-credit-loss line (39,159), 42,689,134 in the FY2024 filing. Interim cost reclassification: Q1 2026 cost of sales 41,162,228 plus Q2 2026 39,879,725 is 54,798 below the H1 2026 figure 81,096,751 (moved from G&A), "
                     "so Q2 by subtraction from the Q1 file is wrong for cost and gross profit; sales, operating profit, profit before zakat and net profit roll exactly. All 2025 and 2024 quarter rolls hold for every line transcribed. "
                     "Cash flow Q2 by subtraction is NOT validated (the cash-flow presentation changed between Q1 2025 and Q1 2026 filings). Q4 documents do not exist. "
                     "Notes not read, so going concern and discontinued operations were not assessed; none visible on the statement faces."),
            not_read=["notes in every file", "statements of changes in equity", "auditor's reports", "FY2022 cash flow (scan digits do not tie)", "FY2023 scan balance sheet and cash flow", "cash and CFI/CFF lines of H1 2025, 9M 2025, Q1 2025 (scrambled in the text layer)",
                      "H1 2023 cash flow", "Q1 2023, 9M 2023, Q1 2024, 9M 2024 own filings", "FY2021 own filing"]),
        document_completeness=dict(
            status="statements_present_in_all_11_files_two_annual_files_are_arabic_scans",
            summary=("The two annual files 4f4be7af (28 pages, label 2023|FY) and 9d036ce5 (33 pages, label 2024|FY) are Arabic whole-file scans classed scanned_unreadable but contain full statements (FY2022 and FY2023; RSM audit reports); "
                     "the FY2022 cash flow page is legible only partially. The English text-layer filings are complete in the statement pages, some with scrambled column order (H1 2025, 9M 2025, Q1 2025). "
                     "FY labels are publication years (2023|FY = FY2022, 2024|FY = FY2023, 2025|FY = FY2024, 2026|FY = FY2025). Interim labels match the covers. No duplicates or English twins of the scans exist in the folder."),
            defect_ids=["B020-2288-1", "B020-2288-2"]),
        company_coverage=dict(
            status="annual_FY2022_to_FY2025_interims_H1_2023_H1_2024_Q1_H1_9M_2025_Q1_H1_2026_by_page_derived_period",
            present_in_files_by_page_derived_period=["FY2022", "FY2023", "FY2024", "FY2025", "H1 2023", "H1 2024", "Q1 2025", "H1 2025", "9M 2025", "Q1 2026", "H1 2026"],
            values_verified_from_own_pages=["FY2022 (BS, IS)", "FY2023 (IS)", "FY2024", "FY2025", "H1 2023 (BS, IS)", "H1 2024", "Q1 2025", "H1 2025", "9M 2025", "Q1 2026", "H1 2026"],
            values_known_only_as_comparatives=["FY2023 BS and CF (FY2024 filing)", "FY2021 balance sheet totals (FY2022 scan, one line)", "H1 2022 (H1 2023 filing)", "Q1 2024, 9M 2024 and Q3 2024 (2025 filings)", "H1 2023 CF (H1 2024 filing)"],
            values_not_read=["FY2022 cash flow", "equity statements and notes"],
            missing=["FY2021 own filing", "Q1 2023, 9M 2023, Q1 2024, 9M 2024 own filings", "Q4 documents", "annual reports"],
            inventory_corrections=("The inventory counts 7 of 11 expected periods complete, 2 scanned only and 1 absent (2022|FY, expected window starts at 2022|FY). By page-derived period the two scans are FY2022 and FY2023 with readable statements, "
                                   "so the 'scanned only' periods are in fact readable; the absent 2022|FY slot is FY2021, never collected (the FY labelled 2023|FY holds FY2022). Interim gaps (Q1 2023, 9M 2023, Q1 2024, 9M 2024 and the 2022 interims) are real.")),
    ),
    defects=[
        dict(id="B020-2288-1", **{"class": "whole_file_scans_with_full_statements"}, severity="high",
             evidence="4f4be7af (28 pages) and 9d036ce5 (33 pages) are 100% textless Arabic scans classed scanned_unreadable; they hold the FY2022 and FY2023 statements; the visual-reading queue lists them."),
        dict(id="B020-2288-2", **{"class": "restated_or_represented_comparatives"}, severity="high",
             evidence="FY2024 CFO 93,728,021 vs 90,360,701 and CFI -65,381,954 vs -62,014,634; Q1 2025 CFO 20,118,128 vs 18,237,862; H1 2025 CFO 35,233,995 vs 33,520,325; FY2022 sales 268,819,480 vs 270,199,270; FY2023 main operating profit 42,728,293 vs 42,689,134; EPS halved by the 1:1 bonus issues; Q1 2026 + Q2 2026 cost differs from H1 2026 by 54,798."),
        dict(id="B020-2288-3", **{"class": "fiscal_year_label_is_publication_year"}, severity="medium",
             evidence="2023|FY = FY2022, 2024|FY = FY2023, 2025|FY = FY2024, 2026|FY = FY2025; the inventory's period_mismatch queue flags two of the four."),
        dict(id="B020-2288-4", **{"class": "scrambled_text_layer_column_order"}, severity="low",
             evidence="H1 2025, 9M 2025 and Q1 2025 interleave current and comparative columns and split parenthesised numbers; values were identified by arithmetic and only unambiguous lines transcribed."),
    ],
    unread_items=["notes in all files", "statements of changes in equity", "auditor's reports", "FY2022 cash flow", "FY2023 scan BS and CF", "Q1 2023, 9M 2023, Q1 2024, 9M 2024 filings", "FY2021 filing", "Q4 documents (none exist)"],
    conclusion=("NOT claimed complete. 11 filings value-verified (two annual scans partially) with exact identities, cross-filing comparison and quarter rolls; cash-flow reclassifications, bonus-issue EPS restatements and a 2022 sales re-presentation recorded without substitution; "
                "the FY2022 cash flow, notes, equity statements and four interim periods are unread or absent."),
)
mkrecord.build(spec)
