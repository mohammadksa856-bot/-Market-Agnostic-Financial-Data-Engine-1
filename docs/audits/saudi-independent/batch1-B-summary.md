# Independent audit, batch 1-B: 1150 Alinma, 1030 SAIB, 1180 SNB, 8010 Tawuniya, 2222 Aramco

Audited version: `origin/codex/telecom-95pct` @ `ec610f3` (data/imports identical to `origin/main` for these companies; the
`banks-*` branches are ancestors of it). Unmerged candidates audited read-only: Tawuniya manifests on
`origin/claude/insurance-tawuniya-bupa-enrichment` @ `2985be4`. 1050/1060 not touched. Per-company records:
`1150.json 1030.json 1180.json 8010.json 2222.json` (resumable: every source has `status` done/pending).

Three dimensions are kept separate everywhere: **(1) numeric correctness**, **(2) document completeness**, **(3) company coverage**.

## Status matrix

| Company | (1) numeric correctness | (2) document completeness | (3) coverage |
|---|---|---|---|
| 1150 Alinma | **defective**: 9 PDF manifests (ALN-1..3), 1 Pillar-3 conflict (ALN-4); 21 Pillar-3 docs (1,259 facts) and XLSX supplement (493) otherwise exact | low: 13 of ~26 BS lines, no interim cash flow | FS PDFs only 2018-2020 (+Q2-18, Q3-18, Q2-19, 2020 Q1-Q3); 2021-2025 only via issuer XLSX (quarters from 2023Q1) |
| 1030 SAIB | verified_correct (FY2025 page images, 19 Pillar-3, 5 XLSX) | FY2025 83 of ~200 lines; Pillar-3 CET1/T1/leverage/LCR/NSFR never published (P3-STALE) | FY2025 FS; XLSX 1Q21-2Q26; Pillar-3 gaps |
| 1180 SNB | verified_correct (FY2025, 4 interims, 10 XLSX, 10 Pillar-3) | FY2025 96 of ~120; P3-STALE | FY2025, 4 interims, supplements 2Q24-2Q26 |
| 8010 Tawuniya | published FY2025 verified_correct; unmerged candidate `tawuniya-2023-fy` **defective** (TAW-1) | 30 of ~75 lines | only FY2025 published; 7 more manifests unmerged; all 8 source PDFs absent from main |
| 2222 Aramco | 2025 income statement verified line by line; 160/176 page citations wrong (ARA-1); 11 manifests **unverified** (source PDFs not archived anywhere) | derived metric manifests only | FY2019-2025 annual metrics, 2026 Q1/Q2; no quarters before |

## Defects proven (page and line item)

* **ALN-1 quarter vs cumulative (Alinma 2018-Q2, 2018-Q3)**: income-statement facts hold the *three-month* column but are labelled `ytd`
  (pdf p4). Q3-2018: published net income 653,266 (3M) vs 9M 1,856,403; total operating income 1,211,698 vs 3,552,462. Q2-2018: 621,325 vs 1,203,137.
  Root cause `reading._period_column_groups`: heading band hard-coded `y < 155`; the "FOR THE NINE MONTHS PERIOD" subtitle pushes the headings lower.
* **ALN-2 net published as gross (Alinma 2018FY/Q3, 2019FY, 2020FY/Q1/Q2/Q3)**: "Income from investments and financing, net" published as `financing_income`
  (FY2019 p9: gross 5,608,762, net 4,394,459 published). Mixed series with the supplement (gross). Vintage reconciler mislabels it "restated".
* **ALN-3 wrapped caption (2018-Q2, 2019-Q2)**: caption split over two rows; gross line read, net line (942,390 / 1,079,559) never published.
* **ALN-4 Pillar-3 2021-09-30 (Alinma)**: CET1 30,887,221 / ratio 21.26% as originally printed (CET1 = Tier 1); three later disclosures print 25,887,221 / 17.35% which do not reconcile either. Unresolved issuer conflict.
* **P3-STALE (SAIB 19 docs, SNB 10 docs)**: CET1/T1/leverage/HQLA/LCR/NSFR rows excluded `catalog_field_missing`; current reader publishes them.
  Dry run: SAIB 132 -> 446 publishable facts (+314), SNB 72 -> 247 (+175), Alinma 400 -> 400 (method reproduces the published set exactly, zero value changes).
* **TAW-1 (candidate, unmerged) tawuniya-2023-fy `cash_change` = -106,248**: pdf p179 two-panel page; correct 422,514 (2022: 471,057); -106,248 is the 2022 comparative of "Reinsurance contract assets" in the other panel. 1,591,389-1,044,024-124,851 = 422,514.
* **ARA-1** wrong page citations in `aramco-2025-annual-metrics` (values correct).
* Provenance: 8 Tawuniya and 12 of 13 Aramco archived documents referenced in `archive-index.json` are not present in `main` or the audited branch.

Also recorded (not defects): equity lines including Tier-1 sukuk (SAIB `total_equity`, SNB `equity_parent`), SAIB "Term Loans" mapped to `debt_securities_issued`,
Alinma shares-count rounded to millions with currency SAR on a share count, SNB `dividends_paid` is a sum of two printed lines, restated comparatives vs original vintages.

## Shared root causes and fixes (this branch)

1. Heading band `y<155` (ALN-1) - `src/finengine/reading.py::_header_limit`.
2. Net/gross caption mapping and wrapped captions (ALN-2/3) - `BANK_LINE_MAP` + caption stitching in `_statement_facts`.
3. Stale Pillar-3 exclusions - regeneration with current reader (`tools/p3_regen_dryrun.py`, report `p3-regeneration-dryrun-batch1-B.json`); no data written.
4. Two-panel page mispairing (TAW-1) - **not fixed**, plan recorded.

Tests: new `tests/test_audit_alinma_interim_columns.py` (offline, archived PDFs); relevant suites run green
(`test_reading, test_reading_pillar3, test_reading_xlsx, test_bank_*, test_known_data_regressions, test_manifest_sync, test_manifest_vintages`: 105 passed).
Regression of all 172 re-readable published manifests vs baseline reader: only the 9 Alinma manifests change; the other 16 pre-existing drifts (albilad, aljazira, anb, mobily, sabic) are identical with and without the fix.

## Not verified / blocked

Aramco FY2019-FY2024 and 2026 interim sources (not archived); Aramco gap-fill/deep/full-notes row semantics; Alinma/SAIB/SNB notes-level facts; Tawuniya Q-series (anchored to pages only, no visual check).
Tools: `docs/audits/saudi-independent/tools/` (all offline, read-only).
