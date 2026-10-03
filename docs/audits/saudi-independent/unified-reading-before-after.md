# Unified reading.py: before / after re-read of reader-produced manifests

Variants re-read (read-only, OCR off, identical arguments): (a) base ec610f3, (b) A-only 83a70f7, (c) B-only ae11b2d, (d) unified (this branch). Tools: tools/unified_reread.py, unified_compare.py, unified_verify.py, unified_columns.py, unified_page.py, unified_report.py. Nothing under data/ was written.

## Counts

- reader_manifests_finengine_reading_1: 175
- manifests_re_read: 172
- changed_unified: 105
- changed_A_only: 96
- changed_B_only: 9
- unchanged: 67
- regressions: 0
- borderline: 1
- new_wrong_facts: 6
- facts (unified vs base): 156 value changes, 6 disappeared, 297 added
- Not re-readable (source PDF absent from data/raw): acwa-2026-q2.json, stc-2026-q2.json, tawuniya-2025-fy.json
- Scope: 175 finengine.reading/1 manifests. The other 322 files in data/imports come from other producers (pillar3 reader, xlsx reader, manual/vision, reviewed tables) that do not call reading.py and are untouched.
- Facts whose value is printed in the caption row of the cited page: added 296 of 297; changed 156 of 156. Period-column choice was checked by position heuristics (unified_columns.py) and hand inspection.

## How the two header approaches were reconciled

They act at different stages and are kept side by side. A (_header_row_hits, called from _column_blocks) chooses which period tokens define the amount columns by discarding title-line years above the real header row. B (_header_limit, used in _period_column_groups) chooses how far down the heading band extends when the text above each column is read to decide three-month vs year-to-date, replacing the fixed y < 155. Neither filters the other's input; git merged the two edits with no textual conflict in reading.py. On all 175 manifests the unified output equals A's output where A changed something and B's where B changed something, and no manifest is touched by both (A hits ANB/Riyad/Albilad/AlJazira/BSF/Al Rajhi, B hits Alinma only), so no interaction was observed. The only add/add conflict was the audit helper tools/build_records.py: B's copy kept, A's saved as build_records_batch1A.py.

## Regressions

**None.** No fact that was correct under the base reader is wrong or missing under the unified reader. Checked: all 6 disappeared facts, every changed fact (value printed in the cited row), 4-column period layouts by position, and page inspection of Alinma Q2-2018, ANB Q3-2021, Al Jazira Q2-2008, ANB 2017/2023/2025.

### Borderline (counted as 0 regressions, flagged)

- alinma-2020-q1.json net_income|ytd|2020-03-31: 370265 -> (gone). Page 5 (statement of comprehensive income, three-month column only) used to be labelled ytd because the THREE MONTHS subtitle sat below the fixed y=155 cut. It is now labelled quarter and de-duplicated with the identical page-4 net_income quarter fact (370265, unchanged). Q1 year-to-date equals the quarter figure; the value is retained, only the redundant ytd duplicate is gone.

### Removed facts that were wrong (improvements)

- alrajhi-2024-q2.json dividend_income|ytd|2024-06-30||{} = -74037 ("Dividend income", p9): cash-flow add-back row, not the income statement.
- anb-2020-q1.json dividend_income|ytd|2020-03-31||{} = -13223 ("Dividend income", p7): cash-flow add-back row, not the income statement.
- anb-2020-q1.json financing_expense|ytd|2020-03-31||{} = 18944 ("Special commission expense on Sukuk", p7): cash-flow add-back row, not the income statement.
- anb-2021-q1.json dividend_income|ytd|2021-03-31||{} = -16162 ("Dividend income", p7): cash-flow add-back row, not the income statement.
- anb-2021-q1.json financing_expense|ytd|2021-03-31||{} = 23386 ("Special commission expense on Sukuk", p7): cash-flow add-back row, not the income statement.

## New wrong facts (previously absent, now emitted incorrectly; unresolved)

- aljazira-2008-q2.json (from A): exchange_income|ytd 7273 (page prints 9037); trading_income|ytd 11841 (page prints 1784); dividend_income|ytd 6602 (page prints 6330); other_income|ytd 3787 (page prints 2717); eps_diluted|ytd 1.70 (page prints 0.84). Page 4, columns Q2-08 | Q2-07 | 6M-08 | 6M-07. Narrow right-aligned numbers in the 3rd column fall outside the 45pt column window so the 4th (prior-year) number is picked. Base emitted none of these facts (the income statement was not parsed), so this is a latent column-window defect exposed by A, not a regression; the other facts spot-checked on the page are correct.
- anb-2019-annual-report.json (from A): eps_diluted|fy 202 (page prints 2.02). Page 9 prints EPS with a decimal comma (2,02); A's distant-note-column rule now lets the row parse and _parse_number treats the comma as a thousands separator. Base emitted no EPS fact.

## Wrong before and still wrong (not regressions)

- aljazira-2013-q3.json provision_expense|ytd|2013-09-30: -1283152 -> 1283152. Both values are wrong-source: page 15 is a restatement note table, not the income statement. A's cash-flow add-back sign rule fires because the page mentions a cash-flow statement; the sign flipped but the fact was wrong before and after.
- alrajhi-2024-q2.json dividend_income|ytd|2024-06-30: -74037 -> (absent). Base value came from the cash-flow statement add-back (p9), not the income statement; removal is correct. No income-statement dividend_income fact exists in either version (pre-existing gap).

## Change patterns

- A: bank other_expense printed as a positive deduction is now stored negative like every other bank expense (74 facts, sign only); cash-flow add-back depreciation/provision stored with expense sign (25); cash-flow rows such as dividend income and sukuk commission no longer populate income-statement metrics; ANB 2015-2023 annual reports and ANB/Riyad/Al Jazira interims gain income-statement and balance-sheet facts previously mis-paired or taken from notes (e.g. anb-2023-fy customer_deposits 158,681 note extract -> 165,861,338 balance sheet; ANB 2017 financing_expense fy 71,460 sukuk line -> 1,370,441 total).
- B: Alinma three/six/nine-month filings now classify the three-month column as quarter and the cumulative column as ytd (Q2-2018 financing_income ytd 1,185,931 -> 2,299,017; Q3-2018 net_income ytd 653,266 -> 1,856,403); gross financing_income no longer takes the net line (FY2018 3,797,832 -> 4,893,617) and gains financing_expense and net_financing_income.

## Every change, per source file

Format: field (period kind): old -> new. added = absent under base. Labels and pages are in the .json.

### albilad-2011-fy.json (changed by A; pdf data/raw/SA/1140/documents/303d30810d3fe133bbcc99cfeb6e63c066c6d201d4685b7cb8cc24e4ddd58f8b.pdf)
- depreciation_amortization (fy): 88689 -> -88689  [Depreciation and amortization p25 -> Depreciation and amortization p25]
- added bank_investments (instant): 951458  [Investments, net p21]
- added cash_and_balances_with_central_bank (instant): 5834702  [Cash and balances with SAMA p21]
- added customer_deposits (instant): 23037934  [Customer deposits p21]
- added due_from_banks (instant): 6454366  [Due from banks and other financial institutions, net p21]
- added due_to_banks (instant): 421837  [Due to banks and other financial institutions p21]
- added net_loans (instant): 13779746  [Financing, net p21]
- added share_capital (instant): 3000000  [Share capital p21]
- added statutory_reserve (instant): 134653  [Statutory reserve p21]

### albilad-2012-fy.json (changed by A; pdf data/raw/SA/1140/documents/0f388c858dd97f0423cea05f398f86041df5fccc66e94ad1465d35e7221e2d8b.pdf)
- depreciation_amortization (fy): 88020 -> -88020  [Depreciation and amortization p52 -> Depreciation and amortization p52]

### albilad-2018-fy.json (changed by A; pdf data/raw/SA/1140/documents/cba48e96aa0a3a5597fd8c2eb873104b936a7debadbe0f9f288b9abab7bf443e.pdf)
- added cash_end (fy): 9574966  [Cash and cash equivalents at the end of the year p46]

### albilad-2019-fy.json (changed by A; pdf data/raw/SA/1140/documents/ec46ea3ca369f1d246a6bc5c823528622ac327943ce40464b4f3e202f47d7c56.pdf)
- depreciation_amortization (fy): 248924 -> -248924  [Depreciation and amortization p12 -> Depreciation and amortization p12]
- provision_expense (fy): 535623 -> -535623  [Impairment charge for expected credit losses, net p12 -> Impairment charge for expected credit losses, net p12]

### albilad-2020-fy.json (changed by A; pdf data/raw/SA/1140/documents/46353fb92a63fb2ed72de8bc20af55f1e6bdd7625eafded0f4b8e2a5e1271871.pdf)
- depreciation_amortization (fy): 260425 -> -260425  [Depreciation and amortization p14 -> Depreciation and amortization p14]

### albilad-2020-q1.json (changed by A; pdf data/raw/SA/1140/documents/f9dca6151a9584f2576993d61449598b9d62a717a25505ed29c0848d27dd540d.pdf)
- depreciation_amortization (ytd): 62420 -> -62420  [Depreciation and amortization p9 -> Depreciation and amortization p9]
- provision_expense (ytd): 203433 -> -203433  [Impairment charge for expected credit losses, net p9 -> Impairment charge for expected credit losses, net p9]

### albilad-2021-q3.json (changed by A; pdf data/raw/SA/1140/documents/00d11cbf298a77be037f0e6dfafe5533b443289b0a8c1cd1997ed6350a178305.pdf)
- provision_expense (ytd): 448344 -> -448344  [Impairment charge for expected credit losses, net p8 -> Impairment charge for expected credit losses, net p8]

### albilad-2022-q1.json (changed by A; pdf data/raw/SA/1140/documents/925432fe57224148a38d48c5cc347d70cee92bce06f25178c4295945c7acf902.pdf)
- depreciation_amortization (ytd): 69217 -> -69217  [Depreciation and amortization p8 -> Depreciation and amortization p8]
- provision_expense (ytd): 159529 -> -159529  [Impairment charge for expected credit losses, net p8 -> Impairment charge for expected credit losses, net p8]

### albilad-2023-q1.json (changed by A; pdf data/raw/SA/1140/documents/fd4d19cf2a4c7e90f49313d8421c71c675fbfa7635aec97942b1142f14ea909d.pdf)
- depreciation_amortization (ytd): 73726 -> -73726  [Depreciation and amortization p8 -> Depreciation and amortization p8]
- provision_expense (ytd): 128851 -> -128851  [Impairment charge for expected credit losses, net p8 -> Impairment charge for expected credit losses, net p8]

### albilad-2024-q1.json (changed by A; pdf data/raw/SA/1140/documents/5e5d58ebed40e6a706bda1793847c36579a951b3fcbc027aa6ce61bb5fe2be17.pdf)
- depreciation_amortization (ytd): 65979 -> -65979  [Depreciation and amortization p8 -> Depreciation and amortization p8]
- provision_expense (ytd): 51547 -> -51547  [Impairment charge for expected credit losses, net p8 -> Impairment charge for expected credit losses, net p8]

### alinma-2018-fy.json (changed by B; pdf data/raw/SA/1150/documents/fe2c8548cb0621b272f4c9b1b018a7d147e01b0d36fcd4bce5aa1584b2799988.pdf)
- financing_income (fy): 3797832 -> 4893617  [Income from investments and financing, net p9 -> Income from investments and financing p9]
- added financing_expense (fy): -1095785  [Return on time investments p9]
- added net_financing_income (fy): 3797832  [Income from investments and financing, net p9]

### alinma-2018-q2.json (changed by B; pdf data/raw/SA/1150/documents/a6f2b183dd7b9b30e9c1035c1aef133b37743653bc678726c1904063e525921b.pdf)
- depreciation_amortization (ytd): -46098 -> -92060  [Depreciation and amortization p4 -> Depreciation and amortization p4]
- dividend_income (ytd): 22649 -> 32443  [Dividend income p4 -> Dividend income p4]
- exchange_income (ytd): 45868 -> 85403  [Exchange income, net p4 -> Exchange income, net p4]
- financing_income (ytd): 1185931 -> 2299017  [Income from investments and financing p4 -> Income from investments and financing p4]
- general_and_administrative_expense (ytd): -140503 -> -272830  [Other general and administrative expenses p4 -> Other general and administrative expenses p4]
- net_income (ytd): 621325 -> 1203137  [Net income for the period p4 -> Net income for the period p4]
- operating_income (ytd): 624745 -> 1201845  [Net operating income p4 -> Net operating income p4]
- other_income (ytd): 1017 -> 1018  [Other operating income p4 -> Other operating income p4]
- salaries_and_employee_expenses (ytd): -216567 -> -443577  [Salaries and employee related expenses p4 -> Salaries and employee related expenses p4]
- total_operating_expenses (ytd): -606259 -> -1138919  [Total operating expenses p4 -> Total operating expenses p4]
- total_operating_income (ytd): 1231004 -> 2340764  [Total operating income p4 -> Total operating income p4]
- added depreciation_amortization (quarter): -46098  [Depreciation and amortization p4]
- added dividend_income (quarter): 22649  [Dividend income p4]
- added exchange_income (quarter): 45868  [Exchange income, net p4]
- added financing_expense (quarter): -243541  [Return on time investments p4]
- added financing_expense (ytd): -460350  [Return on time investments p4]
- added financing_income (quarter): 1185931  [Income from investments and financing p4]
- added general_and_administrative_expense (quarter): -140503  [Other general and administrative expenses p4]
- added net_financing_income (quarter): 942390  [Income from investments and financing, net p4]
- added net_financing_income (ytd): 1838667  [Income from investments and financing, net p4]
- added net_income (quarter): 621325  [Net income for the period p4]
- added operating_income (quarter): 624745  [Net operating income p4]
- added other_income (quarter): 1017  [Other operating income p4]
- added salaries_and_employee_expenses (quarter): -216567  [Salaries and employee related expenses p4]
- added total_operating_expenses (quarter): -606259  [Total operating expenses p4]
- added total_operating_income (quarter): 1231004  [Total operating income p4]

### alinma-2018-q3.json (changed by B; pdf data/raw/SA/1150/documents/8eae5c4221d8d630cf02132020d89b659a654e2448c9a7ed7a40703e45b48306.pdf)
- depreciation_amortization (ytd): -46067 -> -138127  [Depreciation and amortization p4 -> Depreciation and amortization p4]
- dividend_income (ytd): 753 -> 33196  [Dividend income p4 -> Dividend income p4]
- eps_diluted (ytd): 0.44 -> 1.25  [Basic and diluted earnings per share (SAR) p4 -> Basic and diluted earnings per share (SAR) p4]
- exchange_income (ytd): 43362 -> 128765  [Exchange income, net p4 -> Exchange income, net p4]
- financing_income (ytd): 987214 -> 3588810  [Income from investments and financing, net p4 -> Income from investments and financing p4]
- general_and_administrative_expense (ytd): -136229 -> -408659  [Other general and administrative expenses p4 -> Other general and administrative expenses p4]
- net_income (ytd): 653266 -> 1856403  [Net income for the period p4 -> Net income for the period p4]
- operating_income (ytd): 659319 -> 1861164  [Net operating income p4 -> Net operating income p4]
- other_income (ytd): 194 -> 1212  [Other operating income p4 -> Other operating income p4]
- salaries_and_employee_expenses (ytd): -227470 -> -671047  [Salaries and employee related expenses p4 -> Salaries and employee related expenses p4]
- total_operating_expenses (ytd): -552379 -> -1691298  [Total operating expenses p4 -> Total operating expenses p4]
- total_operating_income (ytd): 1211698 -> 3552462  [Total operating income p4 -> Total operating income p4]
- added depreciation_amortization (quarter): -46067  [Depreciation and amortization p4]
- added dividend_income (quarter): 753  [Dividend income p4]
- added eps_diluted (quarter): 0.44  [Basic and diluted earnings per share (SAR) p4]
- added exchange_income (quarter): 43362  [Exchange income, net p4]
- added financing_expense (quarter): -302579  [Return on time investments p4]
- added financing_expense (ytd): -762929  [Return on time investments p4]
- added financing_income (quarter): 1289793  [Income from investments and financing p4]
- added general_and_administrative_expense (quarter): -136229  [Other general and administrative expenses p4]
- added net_financing_income (quarter): 987214  [Income from investments and financing, net p4]
- added net_financing_income (ytd): 2825881  [Income from investments and financing, net p4]
- added net_income (quarter): 653266  [Net income for the period p4]
- added operating_income (quarter): 659319  [Net operating income p4]
- added salaries_and_employee_expenses (quarter): -227470  [Salaries and employee related expenses p4]
- added total_operating_expenses (quarter): -552379  [Total operating expenses p4]
- added total_operating_income (quarter): 1211698  [Total operating income p4]

### alinma-2019-fy.json (changed by B; pdf data/raw/SA/1150/documents/13a6ea5f65a40a19de042300a7eccea6d2c83c4eb14b0c61955685258ed1fef3.pdf)
- financing_income (fy): 4394459 -> 5608762  [Income from investments and financing, net p9 -> Income from investments and financing p9]
- added financing_expense (fy): -1214303  [Return on time investments p9]
- added net_financing_income (fy): 4394459  [Income from investments and financing, net p9]

### alinma-2019-q2.json (changed by B; pdf data/raw/SA/1150/documents/ae1cabb24272054a057459ed9bd8e383204a6b9036bb762cd7a5881aa2a95c11.pdf)
- added financing_expense (quarter): -298936  [Return on time investments p4]
- added financing_expense (ytd): -612950  [Return on time investments p4]
- added net_financing_income (quarter): 1079559  [Income from investments and financing, net p4]
- added net_financing_income (ytd): 2072658  [Income from investments and financing, net p4]

### alinma-2020-fy.json (changed by B; pdf data/raw/SA/1150/documents/116d48bf0a7fb01542195649ca41e7f76afb46667ee4bc74fa24018777a53e1f.pdf)
- financing_income (fy): 4647823 -> 5470006  [Income from investments and financing, net p11 -> Income from investments and financing p11]
- added financing_expense (fy): -822183  [Return on time investments p11]
- added net_financing_income (fy): 4647823  [Income from investments and financing, net p11]

### alinma-2020-q1.json (changed by B; pdf data/raw/SA/1150/documents/89d71c740db890b509c6750dd9c8bda3ae33ddfd813ce35ffab00de93739b299.pdf)
- financing_income (quarter): 1121155 -> 1395092  [Income from investments and financing, net p4 -> Income from investments and financing p4]
- DISAPPEARED net_income (ytd): 370265  [Net income for the period after zakat p5]
- added financing_expense (quarter): -273937  [Return on time investments p4]
- added net_financing_income (quarter): 1121155  [Income from investments and financing, net p4]

### alinma-2020-q2.json (changed by B; pdf data/raw/SA/1150/documents/bdf81ec9b72d82ada659362996917cc785dd3f37c5d43db5930068b849d70640.pdf)
- added financing_expense (quarter): -215393  [Return on time investments p4]
- added financing_expense (ytd): -489330  [Return on time investments p4]

### alinma-2020-q3.json (changed by B; pdf data/raw/SA/1150/documents/ebac72dd938ce0735d85c22a56f9544ccd5f51384b42218f434f1a4f081439a1.pdf)
- financing_income (quarter): 1167441 -> 1337217  [Income from investments and financing, net p4 -> Income from investments and financing p4]
- financing_income (ytd): 3410857 -> 4069963  [Income from investments and financing, net p4 -> Income from investments and financing p4]
- added financing_expense (quarter): -169776  [Return on time investments p4]
- added financing_expense (ytd): -659106  [Return on time investments p4]
- added net_financing_income (quarter): 1167441  [Income from investments and financing, net p4]
- added net_financing_income (ytd): 3410857  [Income from investments and financing, net p4]

### aljazira-2008-q2.json (changed by A; pdf data/raw/SA/1020/documents/a78ffb4406599076425915e7b33b085ea1c0185d10903894138c989b2dfcc38c.pdf)
- other_expense (ytd): 289 -> -1273  [Other operating expenses p4 -> Other operating expenses p4]
- added cash_beginning (ytd): 3891962  [Cash and cash equivalents at the beginning of the period p7]
- added cash_change (ytd): -1038020  [Net decrease in cash and cash equivalents p7]
- added cash_end (ytd): 2853942  [Cash and cash equivalents at the end of the period (Note p7]
- added dividend_income (quarter): 1994  [Dividend income p4]
- added dividend_income (ytd): 6602  [Dividend income p4]
- added eps_diluted (quarter): 0.33  [Basic and diluted earnings per share (expressed in SR) p4]
- added eps_diluted (ytd): 1.70  [Basic and diluted earnings per share (expressed in SR) p4]
- added exchange_income (quarter): 5204  [Exchange income, net p4]
- added exchange_income (ytd): 7273  [Exchange income, net p4]
- added financing_cash_flow (ytd): -112927  [Net cash used in financing activities p7]
- added financing_expense (quarter): -86676  [Special commission expense p4]
- added financing_expense (ytd): -189068  [Special commission expense p4]
- added financing_income (quarter): 254450  [Special commission income p4]
- added financing_income (ytd): 523754  [Special commission income p4]
- added net_financing_income (quarter): 167774  [Net special commission income p4]
- added net_financing_income (ytd): 334686  [Net special commission income p4]
- added net_income_parent (quarter): 99890  [Net income for the period attributable to equity holders of the parent p4]
- added net_income_parent (ytd): 253239  [Net income for the period attributable to equity holders of the parent p4]
- added net_income (ytd): 253239  [Net income for the period p7]
- added other_expense (quarter): -289  [Other operating expenses p4]
- added other_income (quarter): 2676  [Other operating income p4]
- added other_income (ytd): 3787  [Other operating income p4]
- added provision_expense (quarter): -23484  [Charge for / (reversal of) provision for credit losses, net p4]
- added provision_expense (ytd): -25203  [Charge for / (reversal of) provision for credit losses, net p4]
- added salaries_and_employee_expenses (quarter): -119870  [Salaries and employee-related expenses p4]
- added salaries_and_employee_expenses (ytd): -221879  [Salaries and employee-related expenses p4]
- added total_operating_expenses (quarter): -231255  [Total operating expenses p4]
- added total_operating_expenses (ytd): -419914  [Total operating expenses p4]
- added total_operating_income (quarter): 331317  [Total operating income p4]
- added total_operating_income (ytd): 673071  [Total operating income p4]
- added trading_income (quarter): 6489  [Trading income, net p4]
- added trading_income (ytd): 11841  [Trading income, net p4]

### aljazira-2008-q3.json (changed by A; pdf data/raw/SA/1020/documents/60e460bef3499143e2f4e7fabc14eab5826208f519d7f4ecf1ea8dd9132a016c.pdf)
- other_expense (quarter): 82 -> -82  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 449 -> -449  [Other operating expenses p4 -> Other operating expenses p4]
- added cash_beginning (ytd): 3891962  [Cash and cash equivalents at the beginning of the period p6]
- added cash_change (ytd): -1710385  [Net decrease in cash and cash equivalents p6]
- added financing_cash_flow (ytd): -135411  [Net cash used in financing activities p6]
- added provision_expense (ytd): -33673  [Provision for credit losses, net p6]
- added share_capital (instant): 3000000  [Share capital p3]

### aljazira-2013-q3.json (changed by A; pdf data/raw/SA/1020/documents/7045ec72af6b3c4dc0ee3d9c6110e1f20e8d46b37c0429c4d992ecdf589ed4c9.pdf)
- other_expense (quarter): 995 -> -995  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 4381 -> -4381  [Other operating expenses p4 -> Other operating expenses p4]
- provision_expense (ytd): -1283152 -> 1283152  [Provision for credit losses p15 -> Provision for credit losses p15]

### aljazira-2014-q3.json (changed by A; pdf data/raw/SA/1020/documents/bb90a4c79285afe5e528f71d16bdf1a15b9a341857644ea801a8ea17723be1dc.pdf)
- other_expense (quarter): 876 -> -876  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 3040 -> -3040  [Other operating expenses p4 -> Other operating expenses p4]

### aljazira-2015-q1.json (changed by A; pdf data/raw/SA/1020/documents/bd6b51db25cd972d79ee4634b0e2386177f0be84f5ad3f264a4a624bf1f4f9b0.pdf)
- other_expense (quarter): 862 -> -862  [Other operating expenses p4 -> Other operating expenses p4]
- added eps_diluted (quarter): 0.57  [Basic and diluted earnings per share for the period p4]

### aljazira-2015-q3.json (changed by A; pdf data/raw/SA/1020/documents/db8653ef306a147a30c8ebe95a12829950cefedc23b015120acebcf221502784.pdf)
- other_expense (quarter): 236 -> -236  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 2012 -> -2012  [Other operating expenses p4 -> Other operating expenses p4]

### alrajhi-2024-q2.json (changed by A; pdf data/raw/SA/1120/documents/76558c1f4730d8e186f4929500a4b53f03546c7c5ecc5be6af5c07612818c795.pdf)
- DISAPPEARED dividend_income (ytd): -74037  [Dividend income p9]

### anb-2004-q1.json (changed by A; pdf data/raw/SA/1080/documents/dd647cf992a4bb227c16a557abbe2bc04ee39a2c1d0f7088db772e5374dd85c6.pdf)
- depreciation_amortization (ytd): 15831 -> -15831  [Depreciation and amortization p5 -> Depreciation and amortization p5]
- other_expense (quarter): 9250 -> -9250  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2004-q2.json (changed by A; pdf data/raw/SA/1080/documents/eb3df59a5c589266fe59643a3e6d2b9d7aa7da32ec75c61cf6113ac14be4a7c5.pdf)
- other_expense (ytd): 9252 -> -9252  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2004-q3.json (changed by A; pdf data/raw/SA/1080/documents/117d2f58c7e0c0bf997a295fc18db9be821aad47be271b83505ed49b41a19ea1.pdf)
- other_expense (quarter): 115 -> -115  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 9367 -> -9367  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2005-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/93ed25e002f45f6b187aab121cc13a2de3c82e2342cdbd8bd81bac0b9575563c.pdf)
- other_expense (fy): 202 -> -202  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2005-q1.json (changed by A; pdf data/raw/SA/1080/documents/30b8b108c7c755408d7b82a9a4fb1617ce864529f7ffffee86f4bc3e01451957.pdf)
- depreciation_amortization (ytd): 15548 -> -15548  [Depreciation and amortization p5 -> Depreciation and amortization p5]
- other_expense (ytd): 68 -> -68  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2005-q2.json (changed by A; pdf data/raw/SA/1080/documents/909c8031a519a50e767d93d0b7628b970ee77c09d5e951c1057d3f0628780b0d.pdf)
- other_expense (quarter): 118 -> -118  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 186 -> -186  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2005-q3.json (changed by A; pdf data/raw/SA/1080/documents/e1767eb4b0e8c3eda37c16c896bbf13fe0187e1b3d7a8dc7d0cc29cc155667cc.pdf)
- other_expense (ytd): 186 -> -186  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2006-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/e44f05576c61b41976fa4911b598b581b29d756aa5790e6803cd6a7c22359e9c.pdf)
- other_expense (fy): 643 -> -643  [Other operating expenses p3 -> Other operating expenses p3]

### anb-2010-q1.json (changed by A; pdf data/raw/SA/1080/documents/949eebee47066fe45ba087f2874fbe887d6f63e9ed3d5282d0c688fca4779a41.pdf)
- added bank_investments (instant): 28103476  [Investments, net p2]

### anb-2011-q1.json (changed by A; pdf data/raw/SA/1080/documents/36befbaa5e23ae0ecc7cc7b7877b8dcb93927b0f0912fe80198b3f6c6a970824.pdf)
- added bank_investments (instant): 30757397  [Investments, net p1]
- added share_capital (instant): 8500000  [Share capital p1]

### anb-2011-q2.json (changed by A; pdf data/raw/SA/1080/documents/9720f20354b86366ee11411c5e29e33cb002c0fb1a1e99f7418620e58ce77ee9.pdf)
- added cash_end (ytd): 8564838  [Cash and cash equivalents at the end of the period p6]

### anb-2012-q2.json (changed by A; pdf data/raw/SA/1080/documents/e0349769e10c27062d3506d9ffcbbe441ca6f56d45a96635ae7eca4fdf36e478.pdf)
- added cash_end (ytd): 7040107  [Cash and cash equivalents at the end of the period p6]

### anb-2014-q1.json (changed by A; pdf data/raw/SA/1080/documents/591e1d444c038d7ea03c2d48713d3b8993c7ec317c4c2141dfde1ef0a892609d.pdf)
- added bank_investments (instant): 36260772  [Investments, net p2]
- added cash_end (ytd): 16587453  [Cash and cash equivalents at the end of the period p6]
- added customer_deposits (instant): 117541233  [Customers’ deposits p2]
- added net_loans (instant): 87418944  [Loans and advances, net p2]
- added share_capital (instant): 10000000  [Share capital p2]

### anb-2014-q2.json (changed by A; pdf data/raw/SA/1080/documents/1c61d5b0a4b38b4a7aebe9de875225c5319bd9021eabfbe656a37c74b390f35f.pdf)
- added cash_end (ytd): 7577423  [Cash and cash equivalents at the end of the period p6]

### anb-2014-q3.json (changed by A; pdf data/raw/SA/1080/documents/ca409e34711ee834d216180864bdec4d4ba835d9edecdc2b722f15e4c47f2df0.pdf)
- added cash_end (ytd): 8362491  [Cash and cash equivalents at the end of the period p6]

### anb-2015-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/0482608a38c0f746b5230f227529a19ac59b24973df11d5d1b1b3a0e088d4ca3.pdf)
- depreciation_amortization (fy): 199323 -> -199323  [Depreciation and amortization of property and equipment p8 -> Depreciation and amortization p5]
- dividend_income (fy): -46277 -> 46277  [Dividend income p8 -> Dividend income p5]
- added bank_investments (instant): 33239175  [Investments, net p4]
- added cash_and_balances_with_central_bank (instant): 10428291  [Cash and balances with SAMA p4]
- added due_from_banks (instant): 5575020  [Due from banks and other financial institutions p4]
- added due_to_banks (instant): 5672883  [Due to banks and other financial institutions p4]
- added exchange_income (fy): 513272  [Exchange income, net p5]
- added financing_expense (fy): -593942  [Special commission expense p5]
- added financing_income (fy): 4438779  [Special commission income p5]
- added general_and_administrative_expense (fy): -502434  [Other general and administrative expenses p5]
- added net_fee_income (fy): 1285924  [Fees and commission income, net p5]
- added net_financing_income (fy): 3844837  [Net special commission income p5]
- added net_income_noncontrolling (fy): -7941  [Non-controlling interest p5]
- added net_income_parent (fy): 2964417  [Equity holders of the Bank p5]
- added net_loans (instant): 115144322  [Loans and advances, net p4]
- added operating_income (fy): 2918976  [Net operating income p5]
- added other_income (fy): 156983  [Other operating income, net p5]
- added salaries_and_employee_expenses (fy): -1375471  [Salaries and employee related expenses p5]
- added share_capital (instant): 10000000  [Share capital p4]
- added statutory_reserve (instant): 8732000  [Statutory reserve p4]
- added total_operating_expenses (fy): -2943553  [Total operating expenses p5]
- added total_operating_income (fy): 5862529  [Total operating income p5]

### anb-2015-q1.json (changed by A; pdf data/raw/SA/1080/documents/07454afef684364819978ce0e50aec512ac5aa3657cd7e7c5c5ec92a60abeb23.pdf)
- added bank_investments (instant): 33642535  [Investments, net p2]
- added cash_end (ytd): 11191847  [Cash and cash equivalents at the end of the period p6]
- added customer_deposits (instant): 131110207  [Customers’ deposits p2]
- added net_loans (instant): 108344757  [Loans and advances, net p2]
- added share_capital (instant): 10000000  [Share capital p2]

### anb-2015-q2.json (changed by A; pdf data/raw/SA/1080/documents/15db9b137ac02a94d1db92e1254bfaafac6169947ab7809aad4146bb615e4b9b.pdf)
- added bank_investments (instant): 33810707  [Investments, net p2]
- added cash_end (ytd): 9732547  [Cash and cash equivalents at the end of the period p6]
- added customer_deposits (instant): 132306424  [Customers’ deposits p2]
- added net_loans (instant): 110971312  [Loans and advances, net p2]
- added share_capital (instant): 10000000  [Share capital p2]

### anb-2015-q3.json (changed by A; pdf data/raw/SA/1080/documents/6461ea14020bac265a08ac5399f6a09c04e0bdbf52d2fa0ac37abec84afb2611.pdf)
- added bank_investments (instant): 30716573  [Investments, net p2]
- added cash_end (ytd): 9364856  [Cash and cash equivalents at the end of the period p6]
- added customer_deposits (instant): 132521561  [Customers’ deposits p2]
- added debt_securities_issued (instant): 1687500  [Debt securities in issue p2]
- added net_loans (instant): 112746929  [Loans and advances, net p2]
- added share_capital (instant): 10000000  [Share capital p2]

### anb-2016-q1.json (changed by A; pdf data/raw/SA/1080/documents/5c0118722160e449d8d24ab8606637dc32fa7f13e8e5e27b9106189f52c97585.pdf)
- added cash_end (ytd): 13737096  [Cash and cash equivalents at the end of the period p7]

### anb-2016-q2.json (changed by A; pdf data/raw/SA/1080/documents/7817401bbff0abd38db4757fd08fbe450a5faea7018ab81f1821ee79a172c149.pdf)
- added cash_end (ytd): 12449535  [Cash and cash equivalents at the end of the period p7]

### anb-2016-q3.json (changed by A; pdf data/raw/SA/1080/documents/4a8cc39d6504277a96e6dbfbdf7e328d45adf2a675e219036af2a2c8936d2182.pdf)
- added cash_end (ytd): 13484276  [Cash and cash equivalents at the end of the period p7]

### anb-2017-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/91b1d6217433c1e42c32ceaa9a7744237f95dc0adafdcba21521bc11edc1ed79.pdf)
- depreciation_amortization (fy): 221379 -> -221379  [Depreciation and amortization of property and equipment p16 -> Depreciation and amortization p13]
- dividend_income (fy): -53203 -> 53203  [Dividend income p16 -> Dividend income p13]
- financing_expense (fy): 71460 -> -1370441  [Special commission expense on sukuk p16 -> Special commission expense p13]
- added bank_investments (instant): 32320816  [Investments, net p12]
- added cash_and_balances_with_central_bank (instant): 17251379  [Cash and balances with SAMA p12]
- added customer_deposits (instant): 136048089  [Customers’ deposits p12]
- added due_from_banks (instant): 1710123  [Due from banks and other financial institutions p12]
- added due_to_banks (instant): 2691549  [Due to banks and other financial institutions p12]
- added exchange_income (fy): 415112  [Exchange income, net p13]
- added financing_income (fy): 6035194  [Special commission income p13]
- added general_and_administrative_expense (fy): -577741  [Other general and administrative expenses p13]
- added net_fee_income (fy): 840398  [Fees and commission income, net p13]
- added net_financing_income (fy): 4664753  [Net special commission income p13]
- added net_income_noncontrolling (fy): 7086  [Non-controlling interest p13]
- added net_income_parent (fy): 3026972  [Equity holders of the Bank p13]
- added net_loans (instant): 114542929  [Loans and advances, net p12]
- added operating_income (fy): 3003399  [Net operating income p13]
- added other_income (fy): 204437  [Other operating income, net p13]
- added salaries_and_employee_expenses (fy): -1247129  [Salaries and employee related expenses p13]
- added share_capital (instant): 10000000  [Share capital p12]
- added statutory_reserve (instant): 10000000  [Statutory reserve p12]
- added total_operating_expenses (fy): -3374544  [Total operating expenses p13]
- added total_operating_income (fy): 6377943  [Total operating income p13]
- added trading_income (fy): 22832  [Trading income, net p13]

### anb-2017-q1.json (changed by A; pdf data/raw/SA/1080/documents/226f79a8a1dca369ab69b1050c4c7c5539161683e071f5a15f5841a1769d1774.pdf)
- added cash_end (ytd): 14721559  [Cash and cash equivalents at the end of the period p7]

### anb-2017-q3.json (changed by A; pdf data/raw/SA/1080/documents/88ec8352b154a1eed2fefe3352c5e6dc1be18a0ac0697aa74e864e4d0e919beb.pdf)
- added bank_investments (instant): 25759420  [Investments, net p3]
- added cash_end (ytd): 8492156  [Cash and cash equivalents at the end of the period p7]
- added customer_deposits (instant): 128546906  [Customers’ deposits p3]
- added net_loans (instant): 115931970  [Loans and advances, net p3]
- added share_capital (instant): 10000000  [Share capital p3]

### anb-2018-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/b5759f230bdce83493db6f4bbfd42425ab612a17807cc9db15b5538b3ef944e3.pdf)
- added bank_investments (instant): 27857183  [Investments, net p10]
- added cash_and_balances_with_central_bank (instant): 22980266  [Cash and balances with SAMA p10]
- added cash_end (fy): 17094956  [Cash and cash equivalents at the end of the year p15]
- added customer_deposits (instant): 140909422  [Customers’ deposits p10]
- added depreciation_amortization (fy): -204990  [Depreciation and amortization p11]
- added dividend_income (fy): 63376  [Dividend income p11]
- added due_from_banks (instant): 1134048  [Due from banks and other financial institutions p10]
- added eps_diluted (fy): 3.31  [Basic and diluted earnings per share (expressed in SAR) p11]
- added fee_expense (fy): -684071  [Fee and commission expense p11]
- added fee_income (fy): 1335185  [Fee and commission income p11]
- added financing_expense (fy): -1680971  [Special commission expense p11]
- added financing_income (fy): 6832413  [Special commission income p11]
- added net_loans (instant): 121038239  [Loans and advances, net p10]
- added other_income (fy): 189594  [Other operating income, net p11]
- added other_reserves (instant): -7263  [Other reserves p10]
- added salaries_and_employee_expenses (fy): -1265985  [Salaries and employee related expenses p11]
- added share_capital (instant): 10000000  [Share capital p10]
- added statutory_reserve (instant): 10000000  [Statutory reserve p10]
- added trading_income (fy): 21155  [Trading income, net p11]

### anb-2018-q1.json (changed by A; pdf data/raw/SA/1080/documents/edf97f841f31f37ad9e1d4ba8190e5a209d3742faeb2d2b39791e2656a70598a.pdf)
- added cash_end (ytd): 10619400  [Cash and cash equivalents at the end of the period p7]

### anb-2018-q2.json (changed by A; pdf data/raw/SA/1080/documents/4e20a938adcf9b84b8446e2cf0c2cf8b4d56097192e86fd99cfef025a0cbe4f3.pdf)
- added cash_end (ytd): 9549547  [Cash and cash equivalents at the end of the period p7]

### anb-2018-q3.json (changed by A; pdf data/raw/SA/1080/documents/f6362a4175af0719951b6a3a3f6cbfcc5c1a6757333cf3573c4bad71e266f4da.pdf)
- added bank_investments (instant): 27486440  [Investments, net p3]
- added cash_end (ytd): 7837577  [Cash and cash equivalents at the end of the period p7]
- added customer_deposits (instant): 130830470  [Customers’ deposits p3]
- added net_loans (instant): 120489435  [Loans and advances, net p3]
- added share_capital (instant): 10000000  [Share capital p3]

### anb-2019-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/f05ee3e34dc7d21ff7024272382f4ee0c13af8fefbb36f6f186ed369ca0d395d.pdf)
- depreciation_amortization (fy): 253207 -> -253207  [Depreciation and amortization of property and equipment, net p13 -> Depreciation and amortization p9]
- dividend_income (fy): -84531 -> 84531  [Dividend income p13 -> Dividend income p9]
- financing_expense (fy): 85129 -> -2079685  [Special commission expense on sukuk p13 -> Special commission expense p9]
- added bank_investments (instant): 38038140  [Investments, net p8]
- added cash_and_balances_with_central_bank (instant): 17167044  [Cash and balances with SAMA p8]
- added customer_deposits (instant): 142128897  [Customers’ deposits p8]
- added due_from_banks (instant): 2067992  [Due from banks and other financial institutions, net p8]
- added due_to_banks (instant): 3082181  [Due to banks and other financial institutions p8]
- added eps_diluted (fy): 202  [Basic and diluted earnings per share (expressed in SAR) p9]
- added fee_expense (fy): -632920  [Fee and commission expense p9]
- added fee_income (fy): 1290651  [Fee and commission income p9]
- added financing_income (fy): 7632624  [Special commission income p9]
- added net_income_noncontrolling (fy): -1423  [Non-controlling interest p9]
- added net_loans (instant): 118837121  [Loans and advances, net p8]
- added other_income (fy): 74698  [Other operating income, net p9]
- added salaries_and_employee_expenses (fy): -1281170  [Salaries and employee related expenses p9]
- added share_capital (instant): 15000000  [Share capital p8]
- added statutory_reserve (instant): 7756000  [Statutory reserve p8]

### anb-2019-q1.json (changed by A; pdf data/raw/SA/1080/documents/6247964e37e68f2bd6d42969e4ebb2ac0002e97ec30bcf602d12d9f0bffd93b1.pdf)
- added cash_end (ytd): 4188977  [Cash and cash equivalents at the end of the period p7]
- added eps_diluted (ytd): 0.61  [Basic and diluted earnings per share (in SAR) p4]

### anb-2020-fy.json (changed by A; pdf data/raw/SA/1080/documents/1755779113404f486568503930e76903b04ddfa6daf26f0cee47c968ebb54987.pdf)
- added bank_investments (instant): 43774875  [Investments, net p10]
- added cash_and_balances_with_central_bank (instant): 12633339  [Cash and balances with SAMA p10]
- added customer_deposits (instant): 129352176  [Customers' deposits p10]
- added due_from_banks (instant): 1081984  [Due from banks and other financial institutions, net p10]
- added due_to_banks (instant): 9797744  [Due to banks, SAMA and other financial institutions p10]
- added net_loans (instant): 113362613  [Loans and advances, net p10]
- added share_capital (instant): 15000000  [Share capital p10]
- added statutory_reserve (instant): 8317000  [Statutory reserve p10]

### anb-2020-q1.json (changed by A; pdf data/raw/SA/1080/documents/bb7acd369c118165c3e1a141710b282807541c74a8278e50e13b96727f300087.pdf)
- depreciation_amortization (ytd): 58149 -> -58149  [Depreciation and amortization of property and equipment p7 -> Depreciation and amortization of property and equipment p7]
- DISAPPEARED dividend_income (ytd): -13223  [Dividend income p7]
- DISAPPEARED financing_expense (ytd): 18944  [Special commission expense on Sukuk p7]

### anb-2021-q1.json (changed by A; pdf data/raw/SA/1080/documents/34a845e4794654c46add4d0de50b1738722fbb585b12de26f6910ac38683b5d5.pdf)
- depreciation_amortization (ytd): 53034 -> -53034  [Depreciation and amortization p7 -> Depreciation and amortization p7]
- DISAPPEARED dividend_income (ytd): -16162  [Dividend income p7]
- DISAPPEARED financing_expense (ytd): 23386  [Special commission expense on Sukuk p7]

### anb-2021-q3.json (changed by A; pdf data/raw/SA/1080/documents/043f5ec235f1968668b5c31b4703466dadee1405296b84a089090a214c3d30d0.pdf)
- dividend_income (ytd): 22626 -> 65136  [Dividend income p4 -> Dividend income p4]
- exchange_income (ytd): 56146 -> 158241  [Exchange income, net p4 -> Exchange income, net p4]
- financing_expense (ytd): -131498 -> -322861  [Special commission expense p4 -> Special commission expense p4]
- financing_income (ytd): 1383847 -> 3884940  [Special commission income p4 -> Special commission income p4]
- general_and_administrative_expense (ytd): -173643 -> -503194  [Other general and administrative expenses p4 -> Other general and administrative expenses p4]
- income_before_income_taxes_and_zakat (ytd): 764406 -> 2049708  [Net income before zakat and income tax p4 -> Net income before zakat and income tax p4]
- net_fee_income (ytd): 126445 -> 377260  [Fees and commission income, net p4 -> Fees and commission income, net p4]
- net_financing_income (ytd): 1252349 -> 3562079  [Net special commission income p4 -> Net special commission income p4]
- net_income_noncontrolling (ytd): -797 -> -4758  [Non-controlling interests p4 -> Non-controlling interests p4]
- net_income_parent (ytd): 665354 -> 1720246  [Equity holders of the Bank p4 -> Equity holders of the Bank p4]
- net_income (ytd): 664557 -> 1715488  [Net income for the period p4 -> Net income for the period p4]
- operating_income (ytd): 740828 -> 1977297  [Net operating income p4 -> Net operating income p4]
- other_income (ytd): 2030 -> 29645  [Other operating income, net p4 -> Other operating income, net p4]
- salaries_and_employee_expenses (ytd): -312217 -> -921731  [Salaries and employee related expenses p4 -> Salaries and employee related expenses p4]
- total_operating_expenses (ytd): -738399 -> -2439500  [Total operating expenses p4 -> Total operating expenses p4]
- total_operating_income (ytd): 1479227 -> 4416797  [Total operating income p4 -> Total operating income p4]
- trading_income (ytd): 976 -> 10102  [Trading income, net p4 -> Trading income, net p4]
- added dividend_income (quarter): 22626  [Dividend income p4]
- added exchange_income (quarter): 56146  [Exchange income, net p4]
- added financing_expense (quarter): -131498  [Special commission expense p4]
- added financing_income (quarter): 1383847  [Special commission income p4]
- added general_and_administrative_expense (quarter): -173643  [Other general and administrative expenses p4]
- added income_before_income_taxes_and_zakat (quarter): 764406  [Net income before zakat and income tax p4]
- added net_fee_income (quarter): 126445  [Fees and commission income, net p4]
- added net_financing_income (quarter): 1252349  [Net special commission income p4]
- added net_income_noncontrolling (quarter): -797  [Non-controlling interests p4]
- added net_income_parent (quarter): 665354  [Equity holders of the Bank p4]
- added net_income (quarter): 664557  [Net income for the period p4]
- added operating_income (quarter): 740828  [Net operating income p4]
- added other_income (quarter): 2030  [Other operating income, net p4]
- added salaries_and_employee_expenses (quarter): -312217  [Salaries and employee related expenses p4]
- added total_operating_expenses (quarter): -738399  [Total operating expenses p4]
- added total_operating_income (quarter): 1479227  [Total operating income p4]
- added trading_income (quarter): 976  [Trading income, net p4]

### anb-2023-fy.json (changed by A; pdf data/raw/SA/1080/documents/a74d0df3a826a1c7dd74e7b42454da6a51304b42259a9f72649234c1a1427aa6.pdf)
- customer_deposits (instant): 158681 -> 165861338  [Customers’ deposits p93 -> Customers’ deposits p10]
- due_from_banks (instant): 43491 -> 2477949  [Due from banks and other financial institutions p93 -> Due from banks and other financial institutions, net p10]
- due_to_banks (instant): 442133 -> 8429750  [Due to banks and other financial institutions p93 -> Due to banks, Saudi Central Bank and other financial institutions p10]
- net_loans (instant): 2861700 -> 152235109  [Loans and advances, net p39 -> Loans and advances, net p10]
- added bank_investments (instant): 46675830  [Investments, net p10]
- added cash_and_balances_with_central_bank (instant): 10892182  [Cash and balances with Saudi Central Bank p10]
- added cash_end (fy): 4549290  [Cash and cash equivalents at the end of the year p15]
- added dividend_income (fy): 143139  [Dividend income p11]
- added eps_diluted (fy): 2.71  [Basic and diluted earnings per share (expressed in SAR) p11]
- added fee_expense (fy): -1058185  [Fee and commission expense p11]
- added fee_income (fy): 1694719  [Fee and commission income p11]
- added financing_expense (fy): -5340355  [Special commission expense p11]
- added financing_income (fy): 12477349  [Special commission income p11]
- added noncontrolling_interests (instant): 28422  [Non-controlling interest p10]
- added other_income (fy): 105570  [Other operating income p11]
- added salaries_and_employee_expenses (fy): -1547002  [Salaries and employee related expenses p11]
- added share_capital (instant): 15000000  [Share capital p10]
- added statutory_reserve (instant): 10648000  [Statutory reserve p10]
- added trading_income (fy): 26939  [Trading income, net p11]

### anb-2024-q1.json (changed by A; pdf data/raw/SA/1080/documents/71a524c250b02aa613887085c31a49b5aa9f15bd4164546bdd698d89083ab45f.pdf)
- added cash_end (ytd): 8735531  [Cash and cash equivalents at the end of the period p8]
- added eps_diluted (ytd): 0.82  [Basic and diluted earnings per share (expressed in SAR) p4]

### anb-2024-q2.json (changed by A; pdf data/raw/SA/1080/documents/f5f810a988c9d268480a40cb87a4ccb830cdaf997c1325ca14f49418821f720c.pdf)
- added cash_end (ytd): 5735844  [Cash and cash equivalents at the end of the period p8]
- added eps_diluted (quarter): 0.62  [Basic and diluted earnings per share (expressed in SAR) p4]
- added eps_diluted (ytd): 1.23  [Basic and diluted earnings per share (expressed in SAR) p4]
- added share_capital (instant): 20000000  [Share capital p3]

### anb-2024-q3.json (changed by A; pdf data/raw/SA/1080/documents/1ada2b04851817a1bd1b04c5f661d16044779c948dbfe46968676110fd3a3b49.pdf)
- added cash_end (ytd): 5754932  [Cash and cash equivalents at the end of the period p8]
- added eps_diluted (quarter): 0.62  [Basic and diluted earnings per share (expressed in SAR) p4]
- added eps_diluted (ytd): 1.86  [Basic and diluted earnings per share (expressed in SAR) p4]
- added share_capital (instant): 20000000  [Share capital p3]

### anb-2025-annual-report.json (changed by A; pdf data/raw/SA/1080/documents/b32c41d05bb4b2800383174f7c43ddefd5aa62c858eafb78e72c17540340df88.pdf)
- added debt_securities_issued (instant): 451962  [Debt securities in issue p7]
- added share_capital (instant): 20000000  [Share capital p7]

### anb-2025-q3.json (changed by A; pdf data/raw/SA/1080/documents/69dc53ff9f4881014e5bf97a85f6d368883e3c3ba598627473b0df267f117caa.pdf)
- due_from_banks (instant): 7764252 -> 7760172  [Due from banks and other financial institutions maturing within ninety days of acquisition p17 -> Due from banks and other financial institutions, net p3]
- added cash_and_balances_with_central_bank (instant): 12931865  [Cash and balances with Saudi Central Bank p3]
- added cash_end (ytd): 9855445  [Cash and cash equivalents at the end of the period p8]
- added customer_deposits (instant): 210696811  [Customers’ deposits p3]
- added due_to_banks (instant): 9672685  [Due to banks, Saudi Central Bank and other financial institutions p3]
- added eps_diluted (quarter): 0.64  [Basic and diluted earnings per share (expressed in SAR) p4]
- added eps_diluted (ytd): 1.94  [Basic and diluted earnings per share (expressed in SAR) p4]
- added net_loans (instant): 191355875  [Loans and advances, net p3]
- added retained_earnings (instant): 7729177  [Retained earnings p3]
- added share_capital (instant): 20000000  [Share capital p3]

### bsf-2025-q3.json (changed by A; pdf data/raw/SA/1050/documents/b1b9212ba22bc92e17e734eb801a09b2d3f38b1a8c99fbebe3249b40f36983e6.pdf)
- provision_expense (ytd): 1033575 -> -1033575  [Impairment charge for expected credit losses, net p7 -> Impairment charge for expected credit losses, net p7]

### riyad-2014-fy.json (changed by A; pdf data/raw/SA/1010/documents/b0727e848ec1afa5e37f9121f20993e238cb6cf6260aa79e37410b783dd5debf.pdf)
- other_expense (fy): 46163 -> -46163  [Other operating expenses p4 -> Other operating expenses p4]

### riyad-2014-q1.json (changed by A; pdf data/raw/SA/1010/documents/6f8d9435d5b18040050cd7b9cd5ad34aee5a62a55c3e8c022d6fe94a9ad6b18f.pdf)
- other_expense (quarter): 13280 -> -13280  [Other operating expenses p2 -> Other operating expenses p2]
- added eps_diluted (quarter): 0.72  [Basic and diluted earnings per share for the period (in SAR)-Note p2]

### riyad-2014-q2.json (changed by A; pdf data/raw/SA/1010/documents/c5805a1bfce2661adeb8a3d0b5356d7a4e37cba9a5d4d98ad0ce0ccf6887e17a.pdf)
- other_expense (quarter): 9029 -> -9029  [Other operating expenses p2 -> Other operating expenses p2]
- other_expense (ytd): 22309 -> -22309  [Other operating expenses p2 -> Other operating expenses p2]

### riyad-2014-q3.json (changed by A; pdf data/raw/SA/1010/documents/3a4f0e40afa10e1841085ea79a7bbf864d711f990da2a2f4055d9c5399110322.pdf)
- other_expense (quarter): 10572 -> -10572  [Other operating expenses p2 -> Other operating expenses p2]
- other_expense (ytd): 32881 -> -32881  [Other operating expenses p2 -> Other operating expenses p2]

### riyad-2015-fy.json (changed by A; pdf data/raw/SA/1010/documents/b86d2f96de8968be24f7248961437f335d4a54c263c5b0607d3a4326fbb01e8d.pdf)
- other_expense (fy): 87525 -> -87525  [Other operating expenses p4 -> Other operating expenses p4]

### riyad-2015-q1.json (changed by A; pdf data/raw/SA/1010/documents/43ec01680c294ebf6b32104edc273459e0eda87eca85c5d619383b664a1c6e43.pdf)
- other_expense (quarter): 24904 -> -24904  [Other operating expenses p4 -> Other operating expenses p4]

### riyad-2015-q2.json (changed by A; pdf data/raw/SA/1010/documents/06d6f99c903a2188d7690ecf80bac71494b90fca6580baac078a7c711ee12dd4.pdf)
- other_expense (quarter): 18073 -> -18073  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 42977 -> -42977  [Other operating expenses p4 -> Other operating expenses p4]
- added other_income (quarter): 296126  [Other operating income-Note p4]
- added other_income (ytd): 321164  [Other operating income-Note p4]

### riyad-2015-q3.json (changed by A; pdf data/raw/SA/1010/documents/51f50a385e6c2263e749f38599e5cf15a170a5007f45dd72e45e6eaf3fde03e8.pdf)
- other_expense (quarter): 14990 -> -14990  [Other operating expenses p2 -> Other operating expenses p2]
- other_expense (ytd): 57967 -> -57967  [Other operating expenses p2 -> Other operating expenses p2]
- added other_income (quarter): 7790  [Other operating income-Note p2]
- added other_income (ytd): 328954  [Other operating income-Note p2]

### riyad-2016-fy.json (changed by A; pdf data/raw/SA/1010/documents/3acb4a0c197a44b6e6871b5957ca86c7828dd9b9a9ef67403744a20f25fca903.pdf)
- other_expense (fy): 39330 -> -39330  [Other operating expenses p11 -> Other operating expenses p11]

### riyad-2016-q1.json (changed by A; pdf data/raw/SA/1010/documents/1d5aaaff282fd51ecbc8e5f31d1cbf01db67a84aa991559b038e89bf3b5aa17b.pdf)
- other_expense (quarter): 11169 -> -11169  [Other operating expenses p4 -> Other operating expenses p4]

### riyad-2016-q2.json (changed by A; pdf data/raw/SA/1010/documents/06ac748805b265688ea61aed1481ff46c5ab99b61dc7132308d3ad2d30f587e7.pdf)
- other_expense (quarter): 17578 -> -17578  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 28747 -> -28747  [Other operating expenses p4 -> Other operating expenses p4]

### riyad-2016-q3.json (changed by A; pdf data/raw/SA/1010/documents/f0fe73fa4ecc4c67ceda992ffc937698490dbf1306782686ac7b482d7404cac6.pdf)
- other_expense (quarter): 10005 -> -10005  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 38752 -> -38752  [Other operating expenses p4 -> Other operating expenses p4]

### riyad-2017-fy.json (changed by A; pdf data/raw/SA/1010/documents/6be41c308eb801ce8d2904312a47301bb1bb225af1ea1a23cdc3267cfc1dee84.pdf)
- other_expense (fy): 23833 -> -23833  [Other operating expenses p11 -> Other operating expenses p11]

### riyad-2017-q1.json (changed by A; pdf data/raw/SA/1010/documents/6e5740b47f5b6b69c0c83f3e2fb476bf90f69f1fa4d3f8cc80714942aa8aebfd.pdf)
- other_expense (quarter): 11009 -> -11009  [Other operating expenses p3 -> Other operating expenses p3]

### riyad-2017-q2.json (changed by A; pdf data/raw/SA/1010/documents/5f9487a2789f3720f74f7cac984522f7fb64ae67c936aa33706987559009420d.pdf)
- other_expense (quarter): 6738 -> -6738  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 17747 -> -17747  [Other operating expenses p3 -> Other operating expenses p3]

### riyad-2017-q3.json (changed by A; pdf data/raw/SA/1010/documents/148f952b855cb13b0044e08a38c010149c7e193114d7dcf8c0fd4ed994258955.pdf)
- other_expense (quarter): 4422 -> -4422  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 22169 -> -22169  [Other operating expenses p3 -> Other operating expenses p3]
- added bank_investments (instant): 46883547  [Investments, net p2]
- added customer_deposits (instant): 156050942  [Customer deposits p2]
- added net_loans (instant): 142067876  [Loans and advances, net p2]

### riyad-2018-fy.json (changed by A; pdf data/raw/SA/1010/documents/3584a14d3495e39d720b3442a8b0bb3a8fcd30caf662bbb4a975c41426b7dd42.pdf)
- other_expense (fy): 31392 -> -31392  [Other operating expenses p9 -> Other operating expenses p9]

### riyad-2018-q1.json (changed by A; pdf data/raw/SA/1010/documents/18c70523ab424b507ee2de3909b0be58b26959568271605caaccd7b018d4da1e.pdf)
- other_expense (quarter): 6074 -> -6074  [Other operating expenses p3 -> Other operating expenses p3]

### riyad-2018-q2.json (changed by A; pdf data/raw/SA/1010/documents/4cc76e17a1836870dc1eb2a6e677e3003ebc6eb3276593d2fc6fc666ef349dd9.pdf)
- other_expense (quarter): 7628 -> -7628  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 13702 -> -13702  [Other operating expenses p3 -> Other operating expenses p3]
- provision_expense (ytd): 477652 -> -477652  [Impairment charge for credit losses and other provisions, net p6 -> Impairment charge for credit losses and other provisions, net p6]

### riyad-2018-q3.json (changed by A; pdf data/raw/SA/1010/documents/0bf2b74010cb6b0ed67bb7bcade8bc5255750aeafe0501bff89574e28e9464c8.pdf)
- other_expense (quarter): 5274 -> -5274  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 18976 -> -18976  [Other operating expenses p3 -> Other operating expenses p3]
- provision_expense (ytd): 785918 -> -785918  [Impairment charge for credit losses and other provisions, net p6 -> Impairment charge for credit losses and other provisions, net p6]

### riyad-2019-fy.json (changed by A; pdf data/raw/SA/1010/documents/6f026edbf873539a2504ac673ed98fdd92a1cd28fe7d3477e78cd9fa8a2a17bd.pdf)
- other_expense (fy): 120207 -> -120207  [Other operating expenses p8 -> Other operating expenses p8]

### riyad-2019-q1.json (changed by A; pdf data/raw/SA/1010/documents/ea1fcf8cc8aabedfadfcf76a1c66b60e25d7fd73be153e64ddfab0cf6736c231.pdf)
- other_expense (quarter): 8591 -> -8591  [Other operating expenses p3 -> Other operating expenses p3]
- added provision_expense (quarter): -211439  [Impairment charge for credit losses and other financial assets, net p3]

### riyad-2019-q3.json (changed by A; pdf data/raw/SA/1010/documents/2549affd3fa822c3b582d7bd3e869586977dc550a5907f31f8e3ff3cc138c3f8.pdf)
- other_expense (quarter): 21975 -> -21975  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 33406 -> -33406  [Other operating expenses p3 -> Other operating expenses p3]
- added provision_expense (quarter): -201495  [Impairment charge for credit losses and other financial assets, net p3]
- added provision_expense (ytd): -641392  [Impairment charge for credit losses and other financial assets, net p3]

### riyad-2020-fy.json (changed by A; pdf data/raw/SA/1010/documents/133ce33e4f4cbb225db17970423cadee1e8f73607c3d6bb97e731e8782b003f4.pdf)
- other_expense (fy): 54100 -> -54100  [Other operating expenses p12 -> Other operating expenses p12]

### riyad-2020-q1.json (changed by A; pdf data/raw/SA/1010/documents/cf1eebc26ba5cffbe09ba301de82cb64a71b6041b78bf57acb004ba929c02c4b.pdf)
- other_expense (quarter): 15841 -> -15841  [Other operating expenses p3 -> Other operating expenses p3]
- added provision_expense (quarter): -308129  [Impairment charge for credit losses and other financial assets, net p3]

### riyad-2020-q2.json (changed by A; pdf data/raw/SA/1010/documents/0cac387d5da7323316a0ae1126a429326c625f979251afe0f2f988412f8e9c5a.pdf)
- other_expense (quarter): 13322 -> -13322  [Other operating expenses p3 -> Other operating expenses p3]
- other_expense (ytd): 29163 -> -29163  [Other operating expenses p3 -> Other operating expenses p3]
- added provision_expense (quarter): -612085  [Impairment charge for credit losses and other financial assets, net p3]
- added provision_expense (ytd): -920214  [Impairment charge for credit losses and other financial assets, net p3]

### riyad-2020-q3.json (changed by A; pdf data/raw/SA/1010/documents/ee11088b82e9c1b6124a9ecd6679e2df809a578253d09899a57f9bdd0bb7086b.pdf)
- other_expense (quarter): 14102 -> -14102  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 43265 -> -43265  [Other operating expenses p4 -> Other operating expenses p4]
- added provision_expense (quarter): -490102  [Impairment charge for credit losses and other financial assets, net p4]
- added provision_expense (ytd): -1410316  [Impairment charge for credit losses and other financial assets, net p4]

### riyad-2021-q1.json (changed by A; pdf data/raw/SA/1010/documents/434cb0d8f59800d1b7c33cb6b7d4f8dda95c733e272a4a7dec2a1c3ea65199ba.pdf)
- other_expense (quarter): 40678 -> -40678  [Other operating expenses p4 -> Other operating expenses p4]
- added provision_expense (quarter): -246782  [Impairment charge for credit losses and other financial assets, net p4]

### riyad-2021-q2.json (changed by A; pdf data/raw/SA/1010/documents/715f0ecf6fcc0cc562456f2b35ac1ad31686297976ef9a49db844241737a8e22.pdf)
- other_expense (quarter): 12345 -> -12345  [Other operating expenses p4 -> Other operating expenses p4]
- other_expense (ytd): 53023 -> -53023  [Other operating expenses p4 -> Other operating expenses p4]
- added provision_expense (quarter): -237626  [Impairment charge for credit losses and other financial assets, net p4]
- added provision_expense (ytd): -484408  [Impairment charge for credit losses and other financial assets, net p4]

### riyad-2022-fy.json (changed by A; pdf data/raw/SA/1010/documents/f27cda3dc79b5c1dd4a2976808a3e753f8e7ea74f6663c2514733aed2c110e9c.pdf)
- other_expense (fy): 80423 -> -80423  [Other operating expenses p10 -> Other operating expenses p10]

### riyad-2023-q1.json (changed by A; pdf data/raw/SA/1010/documents/6186fa96a38b8157a52ba865daa48469d234dfc11f03ddc3201460bfbf7fa46c.pdf)
- other_expense (quarter): 8309 -> -8309  [Other operating expenses p4 -> Other operating expenses p4]
- added provision_expense (quarter): -603776  [Impairment charge for credit losses and other financial assets, net p4]

### riyad-2024-q3.json (changed by A; pdf data/raw/SA/1010/documents/39daece40672311a366be739e113dacc41ec89cb771627366a0c6ed778ff852d.pdf)
- other_expense (quarter): 27820 -> -27820  [Other operating expenses p5 -> Other operating expenses p5]
- other_expense (ytd): 59693 -> -59693  [Other operating expenses p5 -> Other operating expenses p5]

### riyad-2025-q1.json (changed by A; pdf data/raw/SA/1010/documents/5fefe4eeeaa9e0c3210936df6289640258ad96d6e27c50f7a87b063de59fd0be.pdf)
- other_expense (quarter): 22582 -> -22582  [Other operating expenses p5 -> Other operating expenses p5]

### riyad-2025-q2.json (changed by A; pdf data/raw/SA/1010/documents/6ca32c5be78e862d9bff773a2f5d2a15007bcc61bd8eb9f047eb74bef3fb09c8.pdf)
- other_expense (quarter): 29210 -> -29210  [Other operating expenses p5 -> Other operating expenses p5]
- other_expense (ytd): 51792 -> -51792  [Other operating expenses p5 -> Other operating expenses p5]

### riyad-2025-q3.json (changed by A; pdf data/raw/SA/1010/documents/a2170d5277bae8d8dca82891f7e9387f0e34c05aa98e81266068e740c3e1a4bd.pdf)
- other_expense (quarter): 37039 -> -37039  [Other operating expenses p5 -> Other operating expenses p5]
- other_expense (ytd): 88831 -> -88831  [Other operating expenses p5 -> Other operating expenses p5]

### riyad-2026-q1.json (changed by A; pdf data/raw/SA/1010/documents/c085bd5ecd8382da053c609ed00bdb2af060502d6be7ddab1dd70d1a8bdebf73.pdf)
- other_expense (quarter): 8440 -> -8440  [Other operating expenses p5 -> Other operating expenses p5]

### riyad-2026-q2.json (changed by A; pdf data/raw/SA/1010/documents/dbc5409a174c9091b38e8d9d14fc1a2b1dd6298f65b90ab6e5536acd22d9c32d.pdf)
- other_expense (quarter): 21304 -> -21304  [Other operating expenses p5 -> Other operating expenses p5]
- other_expense (ytd): 29744 -> -29744  [Other operating expenses p5 -> Other operating expenses p5]

## Full test suite (python -m pytest -q, whole repo)

- Base ec610f3: 1 failed, 527 passed, 1 skipped, 42 errors (571 tests, 32m34s).
- Unified: 1 failed, 538 passed, 1 skipped, 42 errors (582 tests, 32m30s). The +11 passes are the two audit test files (A: test_reading_saudi_audit_batch1a.py, B: test_audit_alinma_interim_columns.py).
- The set of failing/erroring test ids is identical on both (diff empty): 0 failures attributable to this change. Pre-existing: tests/test_monitoring.py::MonitoringTests::test_interim_pdf_is_held_until_period_semantics_are_proven (pdf_extraction_failed vs interim_period_semantics_required) and 42 setup errors in tests/test_factory_18_category_contract.py.
