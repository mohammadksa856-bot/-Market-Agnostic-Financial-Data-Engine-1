# Independent audit, Saudi batch 1-A (1080 ANB, 1010 Riyad, 1140 Albilad, 1020 AlJazira, 1120 Al Rajhi)

Audited: `origin/codex/telecom-95pct` (authoritative manifests, `data/imports/*.json`). Other branches read-only:
`claude/data-banking-notes-1` / `-profiles-1` hold older copies of the 2025 FY manifests (not authoritative);
`claude/aramco-alrajhi-gap-closure` adds three Al Rajhi manifests (annual-notes, company-profile, q4-supplement), audited via `git show`.
No data/**, AWS or Supabase changes. Per-company records: `1080.json`, `1010.json`, `1140.json`, `1020.json`, `1120.json`
(every manifest listed, status `done`). Tools: `tools/` (pagecheck, p3check, xlsxcheck, build_records, defects_curated).

Method: independent PyMuPDF row/column reconstruction (not the finengine reader). Every published fact with a page was located on the
cited page and checked for printed number, label, column-header date/period and sign; Pillar 3 cells and XLSX cells checked
against the printed table / workbook; the five FY2025 manually transcribed manifests (two from scanned images) read from the page images.
"verified_correct" in the records means value + label + period header all matched on the cited page; facts whose header date is not
machine-readable are counted separately, not as verified.

## Per company: three dimensions kept separate

| Symbol | 1 Numeric correctness | 2 Document completeness | 3 Company coverage |
|---|---|---|---|
| 1080 ANB | **defective**: 2,980/3,206 text-PDF facts verified; defects D1 (20 note-table BS facts), D3 (anb-2021-q3 3M labelled ytd), D4, D6 | defective: operating cash flow missing in 55 docs with the line present, fee/provision/share capital gaps (D9) | incomplete: 2003-Q1/FY, 2004 FY, 2013 Q1-Q2, 2021 Q2, 2022-2023 interims, 2025 Q1-Q2, 2026 |
| 1010 Riyad | **defective (basis)**: 1,611/1,665 verified; Pillar 3 2,030/2,030; D6 pre-zakat net income, D4 | defective: cash_end 31, D&A 37, pre-zakat 15 docs | incomplete: 2019 Q2, 2021 Q3/FY, 2022, 2023 Q2-FY, 2024 Q1-Q2 |
| 1140 Albilad | **defective (basis)**: 1,137/1,158 verified; Pillar 3 1,840/1,840; D6, D4 | defective: financing_income ~28 docs, net_financing_income 25, due_to_banks 21 (D9) | incomplete: only 2011, 2012, 2018+; 2018-2019 interims absent |
| 1020 AlJazira | **defective**: D5 (aljazira-2008-q2 wrong row) ; FY2025 (84 facts, scanned) verified visually; 6 supplements match workbook (EPS rounding only); Pillar 3 1,702/1,747 (45 unlocatable cells) | defective: 2008 interims lack income statement | incomplete severely: no statements 2009-2012, 2016-2020 |
| 1120 Al Rajhi | **no numeric defect found**: FY2025 45/45 visually verified; supplement values match; Pillar 3 1,997/1,997; DPS FY2023 workbook internally inconsistent (1.15 vs 2.3) - unverified | defective: FY2024 comparatives, net fee income, equity sukuk unpublished (D11) | incomplete: primary statements only 2023-Q3, 2024-Q2, FY2025 |

No company is claimed complete.

## Proven defects (page evidence in the JSON records)
- **D1** ANB annual reports 2015/2017/2018/2019: BS metrics read from the commission-rate-sensitivity note (e.g. 2017 deposits 39,939,760 vs printed 136,048,089, p62 vs p12).
- **D3** anb-2021-q3: all 17 IS facts are the three-month column labelled ytd (p4: 1,383,847 vs 9M 3,884,940).
- **D4** cash-flow adjustment rows published as dividend_income / financing_expense; add-backs with wrong sign (anb, alrajhi-2024-q2, albilad, riyad).
- **D5** aljazira-2008-q2 bank_investments 13,312 is an income-statement comparative (real 4,431,820); IS missing.
- **D6** net_income <=2018 is pre-zakat; restated after-zakat figures exist in FY2019 filings (Riyad 4,716,085 -> 3,092,277; ANB 3,311,817 -> 3,970,659; Albilad 1,110,510 -> 612,693, EPS 1.85 -> 0.82).
- **D7/D8/D9/D10/D11/D12** mapping/sign/completeness/duplicate items (see records).

## Shared root causes (reader, `src/finengine/reading.py`)
1. Fixed note-column zone (ANB annual reports). 2. Title-line years pollute column detection (nine-month vs three-month). 3. Cash-flow rows allowed to fill income-statement metrics, no add-back sign handling. 4. Plural statement headings not anchors. 5. `other_expense` outside natural-negative set. 6. Published manifests are stale relative to the current reader (re-running it changes/adds many facts). 7. Label gaps in `BANK_LINE_MAP` (Albilad wording) - planned, not applied.

## Fixes prepared (commit on this branch; no data republished)
`tests/test_reading_saudi_audit_batch1a.py` (9 tests; 8+ fail on HEAD reader, pass now). Existing suites run: test_reading, test_reading_pillar3, test_reading_xlsx, test_bank_albilad_cash_flow, test_bank_aljazira_layouts, test_verification, test_known_data_regressions - 100 passed.
A/B re-read of all 150 reader-produced manifests (HEAD reader vs fixed reader) was used as a regression harness; result: the only facts the fixed reader no longer produces are the 5 cash-flow-row facts of D4 (alrajhi-2024-q2, anb-2020-q1, anb-2021-q1); all other differences are additions or sign/column corrections.

## Unverified / not done
- Quarter docs: header-date machine check covers ~96%; the rest only value-on-page. Visual page rendering was done for the representative documents listed in `manual_visual_checks`, not every page.
- Restated comparative values were detected (D6 and cross-document comparison) but not enumerated for every FY pair beyond the evidence listed.
- Pillar 3 non-KM1 templates not audited. Al Rajhi supplement duplicate-column values unresolved.
