"""Curated, evidence-backed defect list for batch 1-A; merged into defects.json (see build_records.py)."""
import json, os

p = os.path.join(os.path.dirname(__file__), "defects.json")
d = json.load(open(p, encoding="utf8"))
d["defects"] = []


def A(**k):
    k["defect_class"] = k.pop("cls")
    d["defects"].append(k)


A(id="D1", symbols=["1080"], cls="wrong_table_and_column", severity="high",
  documents=["anb-2015-annual-report.json", "anb-2017-annual-report.json", "anb-2018-annual-report.json", "anb-2019-annual-report.json"],
  summary="Balance-sheet facts (cash, due from/to banks, bank_investments, customer_deposits, net_loans) taken from the Note 'commission rate sensitivity' table (first bucket / comparative column) instead of the primary statement of financial position. 20 published facts.",
  evidence=[
      {"doc": "anb-2017-annual-report", "pdf_page": 62, "line": "Cash and balances with SAMA 8,002,667 (Within-3-months bucket) ... Total 17,251,379",
       "published": {"cash": "8002667", "deposits": "39939760", "due_from": "1010113", "due_to": "2529120", "bank_investments": "12358717 (3-month bucket of Other investments held at amortised cost)"},
       "correct_page": 12, "correct": {"cash": "17,251,379", "due_from": "1,710,123", "bank_investments": "32,320,816", "deposits": "136,048,089", "due_to": "2,691,549", "net_loans (missing)": "114,542,929"}},
      {"doc": "anb-2018-annual-report", "pdf_pages": [90, 91], "published": {"cash": "14312000", "deposits": "48176822", "bank_investments": "12358717 (2017 comparative bucket)"},
       "correct_page": 10, "correct": {"cash": "22,980,266", "due_from": "1,134,048", "investments": "27,857,183", "deposits": "140,909,422", "due_to": "1,536,602", "net_loans": "121,038,239"}},
      {"doc": "anb-2019-annual-report", "pdf_pages": [82, 83], "published": {"cash": "8363000", "deposits": "40627864"},
       "correct_page": 8, "correct": {"cash": "17,167,044", "due_from": "2,067,992", "investments": "38,038,140", "deposits": "142,128,897", "due_to": "3,082,181", "net_loans": "118,837,121"}},
      {"doc": "anb-2015-annual-report", "pdf_pages": [53, 54], "published": {"cash": "12089917", "net_loans": "58748903", "bank_investments": "18078127", "due_from": "3708706", "due_to": "5487544"},
       "correct_page": 4, "correct": {"cash": "10,428,291", "due_from": "5,575,020", "investments": "33,239,175", "net_loans": "115,144,322", "due_to": "5,672,883"}}],
  root_cause="Older reader version published rows from notes pages (current reader stops at the notes section, so manifests are stale) AND the primary-statement rows were never read because the note column sits ~140pt left of the amounts (D2).",
  fix="Republish after the D2 reader fix; test NoteColumnFarLeftOfValuesTests.")
A(id="D2", symbols=["1080"], cls="reader_bug_note_column", severity="high", documents=["*anb"],
  summary="Statement rows that carry a note number are dropped when the note column is >90pt left of the amount columns (ANB annual reports 2015-2019). Re-running the current reader on anb-2017 annual report returns only 9 BS facts (no cash, due from, investments, loans, deposits, due to).",
  evidence=[{"doc": "anb-2017-annual-report", "pdf_page": 12, "note": "note refs at x~318-324, first amount column x~465"}],
  fix="note-reference detection accepts a note token right of every caption word and left of the value columns; pattern widened (16.1, 6-41).")
A(id="D3", symbols=["1080"], cls="quarter_vs_cumulative_confusion", severity="high", documents=["anb-2021-q3.json"],
  summary="All 17 income-statement facts of anb-2021-q3 are the THREE-month column labelled period_kind=ytd; no discrete-quarter facts and no nine-month values.",
  evidence=[{"pdf_page": 4, "line": "Special commission income 1,383,847 (3M 2021) | 1,405,650 | 3,884,940 (9M 2021) | 4,665,714", "published": "financing_income ytd 1383847", "correct_ytd": "3,884,940", "correct_quarter": "1,383,847"},
            {"pdf_page": 4, "line": "Net income for the period 664,557 (3M) / 1,715,488 (9M)", "published": "net_income ytd 664557"}],
  root_cause="Title line 'FOR THE NINE MONTHS ENDED SEPTEMBER 30, 2021 AND 2020' repeats years above the header; stray year centres shift period pairing (reading._column_blocks).",
  fix="_header_row_hits keeps only the header row; test TitleYearsDoNotShiftPeriodColumnsTests.")
A(id="D4", symbols=["1080", "1120", "1140", "1010"], cls="cash_flow_adjustment_row_mapped_to_income_metric", severity="medium",
  documents=["anb-2015-annual-report.json", "anb-2017-annual-report.json", "anb-2019-annual-report.json", "anb-2020-q1.json", "anb-2021-q1.json", "alrajhi-2024-q2.json",
             "albilad-2019-fy.json", "albilad-2020-fy.json", "albilad-2020-q1.json", "albilad-2021-q3.json", "albilad-2022-q1.json", "albilad-2023-q1.json", "albilad-2024-q1.json", "riyad-2018-q2.json", "riyad-2018-q3.json"],
  summary="Cash-flow reconciliation rows published as income-statement facts: dividend_income negative in 6 docs (-46,277, -53,203, -84,531, -13,223, -16,162, alrajhi-2024-q2 -74,037); financing_expense = 'Special commission expense on Sukuk' (+71,460, +85,129, +18,944, +23,386: partial amount, wrong sign); depreciation/provision add-backs published positive (13 + 8 facts) while IS-sourced expenses are negative.",
  evidence=[{"doc": "anb-2017-annual-report", "pdf_page": 16, "line": "Dividend income (53,203); Special commission expense on sukuk 71,460", "correct": "FY2017 special commission expense 1,370,441 (anb-2018 AR p11 comparative); dividend income 53,203 positive"},
            {"doc": "anb-2019-annual-report", "pdf_page": 9, "correct": "Special commission expense 2,079,685; Dividend income 84,531"}],
  fix="_CASH_FLOW_REJECTED_METRICS + add-back sign flip; test CashFlowRowsDoNotPopulateIncomeStatementMetricsTests.")
A(id="D5", symbols=["1020"], cls="wrong_row_wrong_column_and_missing_statement", severity="high", documents=["aljazira-2008-q2.json", "aljazira-2008-q3.json"],
  summary="aljazira-2008-q2: bank_investments=13,312 is the income-statement row 'Gain on non-trading investments, net' (3M June-2007 comparative); real Investments = 4,431,820 (p3). The whole income statement (p4) is missing from both 2008 interims; due_from/due_to missing in Q2.",
  evidence=[{"pdf_page": 4, "line": "Gain on non-trading investments, net - 13,312 4,003 22,501 (3M08, 3M07, 6M08, 6M07)"},
            {"pdf_page": 3, "line": "Investments 4 4,431,820; Due from banks 2,758,879; Due to banks 1,643,829"}],
  root_cause="Plural heading 'STATEMENTS OF INCOME' was not an ANCHORS entry; substring label match 'investments'.", fix="plural anchors; test PluralStatementHeadingTests.")
A(id="D6", symbols=["1080", "1010", "1140"], cls="restated_comparative_and_zakat_basis_discontinuity", severity="high",
  documents=["anb-2018-annual-report.json", "riyad-2018-fy.json", "albilad-2018-fy.json"],
  summary="Until FY2018 these banks charged zakat/tax to equity, so published net_income for periods <=2018 is PRE-zakat; FY2019 filings restate 2018 after zakat. Published history mixes bases and the restated comparative is not published.",
  evidence=[{"doc": "riyad-2018-fy", "published": "net_income 4,716,085; EPS 1.57", "later_restated": "3,092,277; EPS 1.03 (riyad-2019-fy pdf p2, 2018 Restated; also net special commission income 6,685,764->6,628,460, exchange 337,043->292,581, trading 2,717->104,560)"},
            {"doc": "anb-2018-annual-report", "published": "net_income 3,311,817 (equals Net income before zakat and tax)", "later_restated": "3,970,659 (anb-2019 AR p9; zakat reversal 1,113,261)"},
            {"doc": "albilad-2018-fy", "published": "net_income 1,110,510; EPS 1.85", "later_restated": "after zakat 612,693; EPS 0.82 (albilad-2019-fy p8; zakat 497,817)"}],
  fix="Ingest comparative columns as restated vintages (manifest_vintages) and tag net_income basis; no hand edits.")
A(id="D7", symbols=["1080", "1120"], cls="wrong_metric_mapping_and_semantics", severity="medium", documents=["anb-2025-annual-report.json", "alrajhi-2025-fy.json"],
  summary="anb-2025-annual-report assets_held_for_sale=11,358 is 'Liabilities associated with assets held for sale'; real assets held for sale 250,085 not extracted. equity_parent in ANB/Al Rajhi FY2025 includes Tier-1/equity sukuk (49,482,510 / 142,762,048) whereas shareholders-only equity is 41,715,010 / 114,854,169 - not comparable with banks that publish shareholders-only.",
  evidence=[{"doc": "anb-2025-annual-report", "pdf_page": 7, "line": "Liabilities associated with assets held for sale 39 11,358; Assets held for sale 39 250,085"}])
A(id="D8", symbols=["1080", "1010", "1020"], cls="sign_convention", severity="medium", documents=["*anb", "*riyad", "*aljazira"],
  summary="other_expense (unsigned expense line) is published positive in 72 facts while every other expense metric is negative.",
  evidence=[{"doc": "aljazira-2008-q2", "pdf_page": 4, "line": "Other operating expenses 21 289 367 1,273"}], fix="other_expense added to _BANK_NATURAL_NEGATIVE_METRICS; test OtherExpenseSignTests.")
A(id="D9", symbols=["1140", "1010", "1080", "1020"], cls="document_completeness_label_gaps", severity="medium", documents=["*albilad", "*riyad", "*anb", "*aljazira"],
  summary="Lines present on the statement pages but not published (list per document in documents[]): Albilad 'Income from investing and financing assets' (financing_income) and '..., net'; 'Fee and commission, net'; 'Impairment charge for credit and other financial assets, net'; cash-flow subtotals missing in many interims (ANB operating CF 55 docs, Riyad cash_end 31 / D&A 37, Albilad); Riyad pre-zakat income (15).",
  evidence=[{"doc": "albilad-2019-fy", "pdf_page": 8, "line": "Income from investing and financing assets 20 3,355,200 2,723,748"}],
  fix="Add labels to BANK_LINE_MAP (planned, not applied: changes protected data on republish).")
A(id="D10", symbols=["1120", "1020", "1010", "1140"], cls="pillar3_and_supplement_notes", severity="low", documents=["*alrajhi", "*aljazira", "*riyad", "*albilad"],
  summary="Pillar 3: all 7,569 published+rejected KM1 values match the printed cell, month and unit (45 aljazira leverage cells not locatable by row id). Only the oldest column per doc is published (vintage rule); rows 8-12, 'a' variants, LCR/NSFR for old Riyad docs and all non-KM1 templates are not extracted. Supplements: values match workbooks; EPS published at 2dp vs unrounded; Al Rajhi workbook has duplicate FY/quarter columns with different values (FY2023 DPS 1.15 col T vs 2.3 col BF; FY2021 total assets 623,126.517 vs 623,644.628) - original column published, restated column unverified.",
  evidence=[{"xlsx": "alrajhi 2Q2026 sheet '1. Income Statement' row 29 cols T and BF"}])
A(id="D11", symbols=["1120"], cls="coverage_and_completeness", severity="medium", documents=["alrajhi-2025-fy.json"],
  summary="All 45 FY2025 values verified visually (pdf pp 9,10,14,15) but FY2024 comparatives on the same pages, net_fee_income 5,869,207, equity sukuk 27,907,879 and shareholders equity 114,854,169 are not published. Branch-only alrajhi-2025-annual-notes cites printed page numbers (pdf page = cited + 8).",
  evidence=[{"pdf_page": 9, "line": "Total assets 1,043,268,297 | 972,444,354"}])
A(id="D12", symbols=["1080"], cls="duplicate_manifests", severity="low", documents=["anb-2025-annual-report.json", "anb-2025-fy.json"],
  summary="Two published manifests for ANB FY2025 with identical values; no conflict.", evidence=[])
d["visual"] = {
    "1020": [{"doc": "aljazira-2025-fy", "pages": [7, 8, 11, 12], "result": "all 84 published values (2025 + restated 2024) match the scanned statements; combos: provision_2024 274,889 = 317,460 - 42,571; zakat+tax 280,289 = 267,145 + 13,144 and 173,665 = 165,281 + 8,384"}],
    "1120": [{"doc": "alrajhi-2025-fy", "pages": [9, 10, 14, 15], "result": "all 45 values match; unit SAR '000"}],
    "1080": [{"doc": "anb-2024-q2", "pages": [3, 4], "result": "BS/IS values match the rendered page; quarter/ytd columns correct; share capital and other lines not published"},
             {"doc": "anb-2025-fy / anb-2025-annual-report", "pages": [9, 7], "result": "values match; combos documented"}],
    "1010": [{"doc": "riyad-2018-fy / riyad-2019-fy", "pages": [2], "result": "IS rows read from text layer; restatement evidence D6; riyad-2022-fy total_liabilities_equity 359,652,857 correct (label noise only)"}],
    "1140": [{"doc": "albilad-2018-fy / albilad-2019-fy", "pages": [43, 8], "result": "published values match; zakat restatement D6"}]}
json.dump(d, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=1)
