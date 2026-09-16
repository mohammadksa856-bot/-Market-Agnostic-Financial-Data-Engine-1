# Saudi banks — Riyad Bank (1010) and SAIB (1030), batch 1

Branch `claude/banks-riyad-saib-enrichment`, rebased on `origin/main` at `575afa7`
(after the SAB/SNB merge).
Scope is limited to Riyad Bank (`sa:1010`) and The Saudi Investment Bank
(`sa:1030`). No database, deployment, service or worker was changed. Every fact
below was produced by an engine reader from an archived official document and
verified before it was written; nothing was transcribed by hand and nothing was
estimated.

It builds on the generic Pillar 3 KM1 reader and vintage reconciliation merged
from `claude/banks-sab-snb-enrichment`; no commit from that branch is repeated here.

## What changed for the two banks

| | Before | After this batch |
|---|---|---|
| Riyad statements | FY2024–FY2025 (one audited filing) | 37 more reviewed/audited statement filings, Q1-2014 → Q2-2026: 10 fiscal years of flows (FY2014–FY2020, FY2022, FY2024, FY2025); 29 discrete quarters; 18 H1/9M YTD periods; 39 quarter-end balance sheets (gaps listed below) |
| Riyad regulatory capital | none | 37 quarter ends, Mar-2017 → Jun-2026 (only Mar-2023 missing): regulatory capital, RWA, CET1 ratio, Tier 1 ratio |
| SAIB statements | FY2024–FY2025 (one scanned audited filing) | 5 Data Supplement vintages: FY2018–FY2025 flows; 22 discrete quarters Q1-2021 → Q2-2026; 7 H1/9M YTD periods; 25 balance-sheet dates Dec-2018 → Jun-2026 |
| SAIB regulatory capital | none | 33 quarter ends: Jun-2017 → Dec-2019 and Mar-2021 → Jun-2026 (2020 missing) |
| New manifests | — | 90 — Riyad 66 (37 statements, 29 Pillar 3), SAIB 24 (19 Pillar 3, 5 Data Supplements); 132 candidate documents reviewed |

Whole-directory verification (`finengine verify --imports data/imports`) on the
rebased branch, including the merged SAB/SNB manifests: 966 checks passed,
14 warnings, 0 failures. The only new warning is the
SAIB Q4-2022 zakat reversal documented below.

## Source priority applied

1. **Issuer IR (primary).** Riyad Bank
   [financial results](https://www.riyadbank.com/en/investor-relations/financial-results)
   and [Basel III disclosures](https://www.riyadbank.com/investor-relations/basel-iii-disclosures);
   SAIB [financial reports](https://www.saib.com.sa/en/financial-reports-charts)
   year pages (`-2018` … `-2026`) and
   [financial presentations](https://www.saib.com.sa/en/financial-presentations)
   (Data Supplements). Both index pages were added to `config/companies.json`.
2. **Saudi Exchange.** Not used in this batch; it is the next route for the
   scanned statements listed under exceptions.
3. **Regulator.** Not needed; Pillar 3 is the SAMA-mandated disclosure itself.

## Reusable engine changes (read before merging)

Adapters and readers — Claude workstream, each with a regression test in
`tests/test_reading_pillar3.py`:

* `reading_pillar3.py`
  * units `SR 000`, `SR 000's` and `SAR (000)` recognised as thousands;
    `SR mn` as millions;
  * month-first headers (`December 31, 2025`) parsed before day-first ones;
  * a three-letter month followed by a space and a two-digit year (`Mar 20`,
    `T-1 Dec 17`) is a quarter end when nothing numeric follows; spelled-out
    months (`December 30`) never match;
  * the `1` of a `T-1` column tag is never read as a day;
  * rows 1–3 may carry the exact qualifier `(excluding IFRS 9 Adjustment)` /
    `(Exclusive of IFRS 9 adjustments)`, row 3 `(Tier I+Tier II)` and row 4
    `(RWA)-Pillar 1`. The row number still selects the row and the printed ratios
    must still reconcile.
* `config/supplements/1030.json` — SAIB Data Supplement map (SAR million, reported
  precision). `Other reserves` is deliberately not mapped (different definition
  from the audited statement); no total operating expenses line is derived.

No platform-owned file (`cli.py`, catalog, database) is changed on this branch.

## Vintage reconciliation

Pillar 3 filings repeat five quarter ends and Data Supplements repeat up to 22
quarters, so `reconcile_vintages` keeps one source of record per fact (assurance,
then latest period covered, then `filed_at`). Statements use `by_period=True` with
the existing reviewed FY2025 manifests fixed. Eight manifests were superseded in
full and are not written: Riyad `2023`, `2023-q2`, `2023-q3`, `2024-03`, `2024-q4x`
Pillar 3; SAIB `km1-2022-12` Pillar 3 and the `1Q-2025` / `1Q-2026` supplements.
Their sources are listed in the exceptions below for traceability.

Riyad re-posts three Pillar 3 files byte-for-byte under a second URL (`Q1.pdf`,
`Q3.pdf` for 2024; September 2025 `(1)`); each is archived once and the second URL
is recorded as `also_published_at` in `archive-index.json`.

## Exceptions

### Resolved in this batch

| Bank | Exception | Resolution |
|---|---|---|
| Riyad | KM1 2018–2022 rejected: `period_headers_unverifiable` (`Mar 20`, `T-1 Dec 17`) | generic header parsing; 20 filings now read, all columns reconcile |
| SAIB | KM1 2018–2023 rejected: `unit_not_declared` (`SAR (000)`), rows not found (IFRS 9 qualifiers) | generic unit and row-label handling; 10 filings now read |
| SAIB | KM1 Dec-2025 and Mar-2026 use a transposed layout (periods as rows, rotated dates) — `required_rows_missing` | every quarter end in both is published from the reconciled Sep-2025 and Jun-2026 filings; no layout-specific reader added |
| SAIB | "Pillar III Disclosures March 2025" link on the 2025 page points to the Mar-2024 workbook (issuer mislink) | Mar-2025 comes from the Sep-2025 filing's reconciled columns |
| SAIB | Q4-2022 zakat is +50.005 mn (verifier warning: effective tax outside range) | genuine reversal: Q1–Q4 (−63.003, −70.388, −120.724, +50.005) sum to the FY −204.110 and net income ties; published as reported |

### Remaining (not published; each needs the proposed action)

| Bank | Periods | Code | Evidence | Proposed action |
|---|---|---|---|---|
| Riyad | FY2021, Q3-2021, Q1–Q3 2022, FY2023, Q2–Q3 2023, FY2024, Q2-2024, Q2-2019 statements | `image_only_statements` | primary statement pages have no text layer; reader returns 0 facts and verification fails | OCR review (`enable_ocr`) or Saudi Exchange XBRL/filings; manual vision capture must follow the reviewed-manifest process |
| Riyad | Q1-2024 statements | `partial_text_layer` | only page 8 (cash flow / notes) has text; 5 out-of-context facts incl. a cash-flow `Dividend income` adjustment | same as above; partial read deliberately not published |
| Riyad | Mar-2023 capital | `unit_not_declared` + `reported_ratio_does_not_reconcile` | the March 2023 KM1 page prints no unit (`SR 000's` appears only on page 5); later filings print 2-decimal ratios that do not reproduce from their Mar-2023 amounts | confirm unit with the issuer or take Mar-2023 from the Saudi Exchange-filed Pillar 3 |
| Riyad | EPS from Q2-2026 onward | `eps_basis_change` | 1-for-3 bonus issue approved 5 April 2026; the Q2-2026 filing restates the comparative to 0.61 | earlier EPS stays on the pre-bonus basis as filed; adjusted history needs a corporate-action rule (Codex) |
| SAIB | Mar–Dec 2020 capital | `unit_not_declared` / `index_empty` | Dec-2019 and Dec-2020 Pillar III workbooks and the Mar/Sep 2019 KM1s print no unit; the 2020 and 2021 report pages list no documents | Saudi Exchange-filed Pillar 3 for 2020 |
| SAIB | Mar-2018, Sep-2018 KM1 files | `unit_not_declared` | page prints no unit | periods are covered by the Jun-2018 and Dec-2018 filings; no action |
| SAIB | Jun-2022 Pillar III workbook | `km1_table_not_found` | KM1 published as a separate file | covered by `KM1-June-2022.pdf`; no action |
| SAIB | all interim/annual statement PDFs 2024–2026 | `image_only_statements` | statement pages are scanned (text only on notes pages) | Data Supplement vintages publish the same lines; OCR or Saudi Exchange for notes-level detail |
| SAIB | Dec-2025 balance sheet | `restatement_disclosed` | the 2Q-2026 supplement restates Dec-2025 cash, due to banks, total assets and total liabilities by 104.7 mn (footnote: restated from 1Q-2024) | audited FY2025 remains the source of record for Dec-2025; restated values kept in `excluded_facts` with the winning source |
| SAIB | other reserves | `definition_mismatch` | supplement 2,206.472 mn vs audited −361,424 thousand for FY2025 | not mapped |
| Both | CET1 / Tier 1 amounts, leverage, LCR, NSFR | `catalog_field_missing` | values extracted and reconciled, kept in `excluded_facts` | catalog decision for Codex (same as SAB/SNB batch) |

## Documents and manifests

All archived under `data/raw/SA/<symbol>/documents/<sha256>.<ext>` and indexed in
`data/raw/archive-index.json`. `filed_at` is inferred from PDF creation or workbook
last-modified metadata (`filed_at_basis` in each manifest); ranking never relies on
it alone.

### Riyad Bank (sa:1010)

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| `riyad-2014-fy.json` | financial-statements | 31 | 2014-12-31 | `b0727e848ec1afa5` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2014%E2%80%93+Annual+consolidated+financial+statements-en_tcm8-5635.pdf/45222030-6a57-6dbf-16e2-855e0d494795?t=1755073748017) |
| `riyad-2014-q1.json` | interim-report | 33 | 2014-03-31 | `6f8d9435d5b18040` | [link](https://www.riyadbank.com/documents/20121/0/2014+Q1+-+RIYAD+BANK+-+FINANCIAL+STATEMENTS_tcm8-1336.pdf/1f091fdb-525e-e61e-0083-d9ca72416b02?t=1755073777970) |
| `riyad-2014-q2.json` | interim-report | 48 | 2014-06-30 | `c5805a1bfce2661a` | [link](https://www.riyadbank.com/documents/20121/0/2014-Q2-RiyadBank-financial-statements-en_tcm8-3332.pdf/7b71ea66-2c97-d579-6430-2c2dbf4c2d4c?t=1755073769338) |
| `riyad-2014-q3.json` | interim-report | 50 | 2014-09-30 | `3a4f0e40afa10e18` | [link](https://www.riyadbank.com/documents/20121/0/2014-Q3-RiyadBank-financial-statements-en_tcm8-4572.pdf/438ea81e-f7c4-ed0b-327d-4dcf3193baa7?t=1755073758202) |
| `riyad-2015-fy.json` | financial-statements | 32 | 2015-12-31 | `b86d2f96de8968be` | [link](https://www.riyadbank.com/documents/20121/0/Dec2015%E2%80%93Annual+consolidated+financial+statements_tcm8-7897.pdf/5c70ab6f-3294-e7dc-e846-0b51677e3f8a?t=1755073516122) |
| `riyad-2015-q1.json` | interim-report | 34 | 2015-03-31 | `43ec01680c294ebf` | [link](https://www.riyadbank.com/documents/20121/0/Mar-2015%E2%80%93interim-condensed-consolidated-statement-en_tcm8-5989.pdf/de3c083b-c759-eb66-e4db-c243aceb6721?t=1755073551099) |
| `riyad-2015-q2.json` | interim-report | 47 | 2015-06-30 | `06d6f99c903a2188` | [link](https://www.riyadbank.com/documents/20121/0/Jun+2015+%E2%80%93+Interim+condensed+consolidated+financial+statements+for+Financial_tcm8-6346_tcm8-6346.pdf/17941bd4-1c3f-d0f7-8166-c344d9a21668?t=1755073541837) |
| `riyad-2015-q3.json` | interim-report | 47 | 2015-09-30 | `51f50a385e6c2263` | [link](https://www.riyadbank.com/documents/20121/0/2015+Q3+-+Financial+Statements+-+English_tcm8-6559.pdf/a5b2cc44-9ab1-259e-d236-8d8918b93a71?t=1755073528061) |
| `riyad-2016-fy.json` | financial-statements | 32 | 2016-12-31 | `3acb4a0c197a44b6` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2016-Annual+Consolidated+Financial+Statements-EN_tcm8-10024.pdf/81c9bb22-9076-119f-fbcc-2b0f1678f501?t=1755072942734) |
| `riyad-2016-q1.json` | interim-report | 33 | 2016-03-31 | `1d5aaaff282fd51e` | [link](https://www.riyadbank.com/documents/20121/0/Mar+%E2%80%93+2016+Interim+Condensed+Consolidated+Statements_tcm8-8130.pdf/33f68e02-484d-b275-94b0-7e36ed9d0194?t=1755072975875) |
| `riyad-2016-q2.json` | interim-report | 47 | 2016-06-30 | `06ac748805b26568` | [link](https://www.riyadbank.com/documents/20121/0/Jun+%E2%80%93+2016+Interim+Condensed+Consolidated+Statements-_tcm8-8585.pdf/62c42b81-9282-c805-3bfb-d51c8099ac66?t=1755072965371) |
| `riyad-2016-q3.json` | interim-report | 48 | 2016-09-30 | `f0fe73fa4ecc4c67` | [link](https://www.riyadbank.com/documents/20121/0/Sep-2016+Interim+condensed+consolidated+statements-en_tcm8-8671.pdf/be2f273b-00d2-a243-53d1-13fa46621dc8?t=1755072953493) |
| `riyad-2017-fy.json` | financial-statements | 33 | 2017-12-31 | `6be41c308eb801ce` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2017+%E2%80%93+Annual+Consolidated+Financial+Statements_tcm8-14529.pdf/379312bf-f232-a031-9dea-f5693e35c7b2?t=1755069674611) |
| `riyad-2017-q1.json` | interim-report | 33 | 2017-03-31 | `6e5740b47f5b6b69` | [link](https://www.riyadbank.com/documents/20121/0/Mar202017-Interim+condensed+consolidated+statements_tcm8-10420.pdf/33bf12ed-3281-3acc-3683-747e90889071?t=1755069705884) |
| `riyad-2017-q2.json` | interim-report | 51 | 2017-06-30 | `5f9487a2789f3720` | [link](https://www.riyadbank.com/documents/20121/0/Jun-2017+Interim+condensed+consolidated+statements_tcm8-10603.pdf/c29f4a21-57a7-c20b-167f-89701047dcc9?t=1755069695453) |
| `riyad-2017-q3.json` | interim-report | 48 | 2017-09-30 | `148f952b855cb13b` | [link](https://www.riyadbank.com/documents/20121/0/Sep-2017+Interim+condensed+consolidated+statements-en_tcm8-11915.pdf/aa6161fd-01a5-9f63-cf21-d1f76e2bf4e7?t=1755069685209) |
| `riyad-2018-fy.json` | financial-statements | 36 | 2018-12-31 | `3584a14d3495e39d` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2018+Riyad+Bank+Consolidated+Financial+Statements+-+en_tcm8-16380.pdf/63bcf74a-0e9a-70a7-651e-1c808a774986?t=1755068433357) |
| `riyad-2018-q1-pillar3.json` | regulatory-disclosure | 4 | 2017-03-31 | `6a50eacbbf5c5fc2` | [link](https://www.riyadbank.com/documents/20121/0/Mar+2018+-+Disclosures+Under+Basel+III+Framework_tcm8-15344+Q1.pdf/b0e5a1be-714e-2d55-e84f-8a1ba631d5c5?t=1754643004070) |
| `riyad-2018-q1.json` | interim-report | 32 | 2018-03-31 | `18c70523ab424b50` | [link](https://www.riyadbank.com/documents/20121/0/Mar+2018+-+Interim+condensed+consolidated+statements-en_tcm8-15345.pdf/65c74a60-b0a5-75bc-30d9-f2b56edaac0f?t=1755068462822) |
| `riyad-2018-q2-pillar3.json` | regulatory-disclosure | 4 | 2017-06-30 | `1907b35c5d4917b5` | [link](https://www.riyadbank.com/documents/20121/0/Jun-2018+-Disclosures+Under+Basel+III+Framework_tcm8-15570+Q2+%281%29.pdf/6d010ee7-471c-f6e1-bcca-11bdab5de10f?t=1754642994994) |
| `riyad-2018-q2.json` | interim-report | 48 | 2018-06-30 | `4cc76e17a1836870` | [link](https://www.riyadbank.com/documents/20121/0/Jun-2018+-+Interim+condensed+consolidated+statements_tcm8-15569.pdf/d4cb1f01-0bfd-bfa0-e976-7e0e35e6c628?t=1755068452453) |
| `riyad-2018-q3-pillar3.json` | regulatory-disclosure | 4 | 2017-09-30 | `fbae35e74fbe7562` | [link](https://www.riyadbank.com/documents/20121/0/Quarter+3+-+Disclosures+Under+Basel+III+Framework_tcm8-15974+Q3.pdf/cee6a82a-0b4a-64ee-f6a3-7b25acf89a7d?t=1754642973841) |
| `riyad-2018-q3.json` | interim-report | 48 | 2018-09-30 | `0bf2b74010cb6b0e` | [link](https://www.riyadbank.com/documents/20121/0/Quarter+3+-+Interim+condensed+consolidated+statements-en_tcm8-15973.pdf/6d7fa83f-d1a6-0f89-5d1a-e038940aa8d9?t=1755068442495) |
| `riyad-2018-q4-pillar3.json` | regulatory-disclosure | 4 | 2017-12-31 | `28cd415d1432b26b` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2018+-Disclosures+Under+Basel+III+Framework_tcm8-16379+Q4.pdf/bfec9c10-71b2-bfa6-9818-27fda7930736?t=1754642955044) |
| `riyad-2019-fy.json` | financial-statements | 36 | 2019-12-31 | `6f026edbf873539a` | [link](https://www.riyadbank.com/documents/20121/0/quarter4-interim-condensed-consolidated-statements-en_tcm8-20994.pdf/7fcf1710-35d5-6e5d-ea87-e229690d19ab?t=1755068024497) |
| `riyad-2019-q1-pillar3.json` | regulatory-disclosure | 4 | 2018-03-31 | `e6600271cf61221f` | [link](https://www.riyadbank.com/documents/20121/0/Mar+2019+-+Disclosures+Under+Basel+III+Framework_tcm8-16692+Q1.pdf/7f134678-bcba-9125-9e35-fd0b8b409981?t=1754641700826) |
| `riyad-2019-q1.json` | interim-report | 33 | 2019-03-31 | `ea1fcf8cc8aabedf` | [link](https://www.riyadbank.com/documents/20121/0/Quarter-1+2019+-+Annual+Consolidated+Financial+Statements_tcm8-16691+%281%29.pdf/ab8bb64f-abd9-90ee-0f50-02065144d70f?t=1755068058104) |
| `riyad-2019-q2-pillar3.json` | regulatory-disclosure | 4 | 2018-06-30 | `8e44cae29047455c` | [link](https://www.riyadbank.com/documents/20121/0/Jun+2019+-+Disclosures+Under+Basel+III+Framework_tcm8-18133+Q2.pdf/3e6dcbe9-c725-be68-dcbc-93cbe83fabd8?t=1754641690390) |
| `riyad-2019-q3-pillar3.json` | regulatory-disclosure | 4 | 2018-09-30 | `db9d4bcaac577408` | [link](https://www.riyadbank.com/documents/20121/0/Sep-2019-Disclosures-Under-Basel-III-Framework_tcm8-20551+Q3.pdf/dd518ba8-bef3-918b-9331-707bc38d38bb?t=1754641673070) |
| `riyad-2019-q3.json` | interim-report | 52 | 2019-09-30 | `2549affd3fa822c3` | [link](https://www.riyadbank.com/documents/20121/0/Quarter-3-Interim-Condensed-Consolidated-Statements-en_tcm8-20545+%281%29.pdf/e1417115-7314-1148-755e-699da83aca87?t=1755068035627) |
| `riyad-2019-q4-pillar3.json` | regulatory-disclosure | 4 | 2018-12-31 | `9c6575841e6d7d03` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2019+-+Disclosures+Under+Basel+III+Framework_tcm8-21010.pdf/732ab94a-8491-4385-e34f-44976ba61b8a?t=1754641652708) |
| `riyad-2020-fy.json` | financial-statements | 36 | 2020-12-31 | `133ce33e4f4cbb22` | [link](https://www.riyadbank.com/documents/20121/0/rb-financial-statements-q4-2020-en_tcm8-26082.pdf/f03220ef-b6f6-7983-13a3-c69831bdb347?t=1755067565439) |
| `riyad-2020-q1-pillar3.json` | regulatory-disclosure | 4 | 2019-03-31 | `ea994123920ffb55` | [link](https://www.riyadbank.com/documents/20121/0/Mar+2020+-Disclosures+Under+Basel+III+Framework_tcm8-21556+Q1.pdf/5d212df4-86f4-3eba-ed5d-f111f16d5145?t=1754641395169) |
| `riyad-2020-q1.json` | interim-report | 34 | 2020-03-31 | `cf1eebc26ba5cffb` | [link](https://www.riyadbank.com/documents/20121/0/financial-statment-q1-en_tcm8-21539.pdf/065d96b3-f9f8-b885-a0b8-1e2d5ec7ff88?t=1755067595109) |
| `riyad-2020-q2-pillar3.json` | regulatory-disclosure | 4 | 2019-06-30 | `0a9904818a0f6c96` | [link](https://www.riyadbank.com/documents/20121/0/disclosures-under-basel-framework-_tcm8-24879+Q2.pdf/6501dc42-3237-062e-0a64-ddc980843332?t=1754641370277) |
| `riyad-2020-q2.json` | interim-report | 54 | 2020-06-30 | `0cac387d5da73233` | [link](https://www.riyadbank.com/documents/20121/0/rb-financial-2q-2020-en_tcm8-24852.pdf/79910a48-a609-fe19-e238-5a701d25e0a1?t=1755067585413) |
| `riyad-2020-q3-pillar3.json` | regulatory-disclosure | 4 | 2019-09-30 | `301840589f0a5e9e` | [link](https://www.riyadbank.com/documents/20121/0/Sep+2020+-+Disclosures+Under+Basel+III+Framework_tcm8-25469+Q3.pdf/e9570367-b553-fa5f-dfb5-12377c8fd1fc?t=1754641351144) |
| `riyad-2020-q3.json` | interim-report | 53 | 2020-09-30 | `ee11088b82e9c1b6` | [link](https://www.riyadbank.com/documents/20121/0/riyadbank-financials-review-report-q3-2020-en_tcm8-25466.pdf/a08f6d9c-e03a-7096-3bb4-392989294d98?t=1755067576391) |
| `riyad-2020-q4-pillar3.json` | regulatory-disclosure | 4 | 2019-12-31 | `91429acec749f63b` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2020+-Disclosures+Under+Basel+III+Framework_tcm8-26137+Q4.pdf/b7e90104-ba37-8d2a-552c-5d097abde3da?t=1754641335136) |
| `riyad-2021-q1-pillar3.json` | regulatory-disclosure | 4 | 2020-03-31 | `904e2334f2e51cb4` | [link](https://www.riyadbank.com/documents/20121/0/Mar+2021-Disclosures+Under+Basel+III+Framework_tcm8-26460+Q1.pdf/b3d6daa9-3770-cae4-834b-37dc18cb9df8?t=1754637297414) |
| `riyad-2021-q1.json` | interim-report | 36 | 2021-03-31 | `434cb0d8f59800d1` | [link](https://www.riyadbank.com/documents/20121/0/Riyad+Bank+Financial+Statements+-+Q1+2021-en_tcm8-26461.pdf/44641b54-45ce-b5a4-8414-be3e84d47a97?t=1755066764765) |
| `riyad-2021-q2-pillar3.json` | regulatory-disclosure | 4 | 2020-06-30 | `5182304fd219bbfc` | [link](https://www.riyadbank.com/documents/20121/0/Jun+2021+-+Disclosures+Under+Basel+III+Framework_tcm8-26791+Q2.pdf/d70d8ca2-4dcd-4fb8-2f57-6d421c50bd07?t=1754637317352) |
| `riyad-2021-q2.json` | interim-report | 51 | 2021-06-30 | `715f0ecf6fcc0cc5` | [link](https://www.riyadbank.com/documents/20121/0/Riyad+Bank+-+Financial+Statements+-+Q2+2021+%28E%29_tcm8-26776.pdf/5c13a8d7-cda7-5338-bedd-8a409e88ad69?t=1755066754657) |
| `riyad-2021-q3-pillar3.json` | regulatory-disclosure | 4 | 2020-09-30 | `46ec0359611c58b1` | [link](https://www.riyadbank.com/documents/20121/0/Sep+2021+-+Disclosures+Under+Basel+III+Framework_tcm8-27380+Q3+%281%29.pdf/ad4d759d-6bb8-7b22-6b78-64a9cba73164?t=1754637354621) |
| `riyad-2021-q4-pillar3.json` | regulatory-disclosure | 4 | 2020-12-31 | `306e6b1747226780` | [link](https://www.riyadbank.com/documents/20121/0/Dec+2021+-+Disclosures+Under+Basel+III+Framework_tcm8-28312+q4.pdf/308fbd51-167c-0182-3cbe-0ad8dc7037ce?t=1754637372717) |
| `riyad-2022-fy.json` | financial-statements | 35 | 2022-12-31 | `f27cda3dc79b5c1d` | [link](https://www.riyadbank.com/documents/20121/0/Quarter+4-Annual+Consolidated+Financial+Statements+%281%29.pdf/edf2de58-498a-eac6-693a-a8772773a9a6?t=1755066425898) |
| `riyad-2022-q1-pillar3.json` | regulatory-disclosure | 4 | 2021-03-31 | `ce0dde6a22828d95` | [link](https://www.riyadbank.com/documents/20121/0/Mar+2022-Disclosures+Under+Basel+III+Framework_tcm8-28560+Q1.pdf/008332ca-0aac-0612-9b18-6c1c77133b1b?t=1754637030176) |
| `riyad-2022-q2-pillar3.json` | regulatory-disclosure | 4 | 2021-06-30 | `a90f6f821872b685` | [link](https://www.riyadbank.com/documents/20121/0/Quarter2-Disclosure-Under-Basel-Framework+2022_tcm8-28920+Q2.pdf/efc9a48b-5daa-319e-9f81-c50bd103d0ba?t=1754637017051) |
| `riyad-2022-q3-pillar3.json` | regulatory-disclosure | 4 | 2021-09-30 | `a8aef49ad0da45f9` | [link](https://www.riyadbank.com/documents/20121/0/Q3-Disclosure-Under-Basel-Framework+Q3.pdf/4521da7e-c7d4-38be-386a-e2d9b71966a6?t=1754636996226) |
| `riyad-2022-q4-pillar3.json` | regulatory-disclosure | 20 | 2021-12-31 → 2022-12-31 (5) | `c5a5f9f6d8cad7f7` | [link](https://www.riyadbank.com/documents/20121/0/Quarter+4-Disclosure+%281%29.pdf/3d1539a8-3d0c-8fc9-4169-023ca450fe99?t=1754636985959) |
| `riyad-2023-q1.json` | interim-report | 35 | 2023-03-31 | `6186fa96a38b8157` | [link](https://www.riyadbank.com/documents/20121/0/Quarter+1-+Interim+Condensed+Consolidated+Financial+Statements-en+%281%29.pdf/30199171-39e5-99fa-adcf-ded11bceec1e?t=1755065919310) |
| `riyad-2024-09-pillar3.json` | regulatory-disclosure | 4 | 2023-09-30 | `61983da089784a25` | [link](https://www.riyadbank.com/documents/20121/5676168/Pillar+3+Workbook++Sep+2024+-+Riyad+Bank.pdf/cb85f1d2-056e-36e4-f7c4-6338bf6cbd45?t=1730202173839) |
| `riyad-2024-12-pillar3.json` | regulatory-disclosure | 4 | 2023-12-31 | `2d2ea6c44366d869` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook+v2+-+Q4+-+2024+-+Final.pdf/0c122581-d646-6ab6-f597-425212bc3539?t=1762342993326) |
| `riyad-2024-q2x-pillar3.json` | regulatory-disclosure | 4 | 2023-06-30 | `94969731811ac933` | [link](https://www.riyadbank.com/documents/20121/0/q2.pdf/1c51bab7-9745-ca56-bf1c-83baef3b4ab0?t=1754636468071) |
| `riyad-2024-q3.json` | interim-report | 54 | 2024-09-30 | `39daece40672311a` | [link](https://www.riyadbank.com/documents/20121/0/FS+-+3Q+2024+En.pdf/edf2e845-4416-d2ec-925b-0ce7404c8c1e?t=1776325951941) |
| `riyad-2025-03-pillar3.json` | regulatory-disclosure | 4 | 2024-03-31 | `b2b8a6ed6ae945f8` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook+v2+-+Q1+2025+-Riyad+Bank.pdf/480ea2f8-8db7-912a-5680-8418775cd41d?t=1745934908339) |
| `riyad-2025-06-pillar3.json` | regulatory-disclosure | 4 | 2024-06-30 | `e8f56462080e6868` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook++June+2025+-+Riyad+Bank+(1).pdf/aebc40b7-7ebc-83eb-c68c-e0a4dc89e2d7?t=1754635138590) |
| `riyad-2025-09-pillar3.json` | regulatory-disclosure | 4 | 2024-09-30 | `aad7f9f8af224375` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook++September+2025+-+Riyad+Bank.pdf/8ee25e11-9eee-33d7-ff6b-0437d20fc5f4?t=1761750412704) |
| `riyad-2025-12-pillar3.json` | regulatory-disclosure | 4 | 2024-12-31 | `4e27607639690eed` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook++December+2025+-+Riyad+Bank+(1).pdf/cc2ef222-7b9c-cc0f-0452-c58a66420b6b?t=1770895281106) |
| `riyad-2025-q1.json` | interim-report | 34 | 2025-03-31 | `5fefe4eeeaa9e0c3` | [link](https://www.riyadbank.com/documents/20121/0/FS+-+1Q+2025+En+%281%29.pdf/aa755b4e-0949-3736-53cf-cd6b2cf711d5?t=1778067687942) |
| `riyad-2025-q2.json` | interim-report | 53 | 2025-06-30 | `6ca32c5be78e862d` | [link](https://www.riyadbank.com/documents/20121/0/FS+-+2Q+2025+En.pdf/0b45ac47-b390-0af6-59e0-47928fd1cb2f?t=1776325821279) |
| `riyad-2025-q3.json` | interim-report | 54 | 2025-09-30 | `a2170d5277bae8d8` | [link](https://www.riyadbank.com/documents/20121/0/FS+-+3Q+2025+En.pdf/9ed279c6-4fd3-b3bf-6a8d-12248b58f7b1?t=1776325559299) |
| `riyad-2026-03-pillar3.json` | regulatory-disclosure | 4 | 2025-03-31 | `2063eeb710ce7dc9` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook++March+2026+-+Riyad+Bank+%281%29.pdf/09eadd02-1821-26b8-af68-d09d36f8b7e8?t=1777910658094) |
| `riyad-2026-06-pillar3.json` | regulatory-disclosure | 20 | 2025-06-30 → 2026-06-30 (5) | `2085fe031abcd28c` | [link](https://www.riyadbank.com/documents/20121/0/Pillar+3+Workbook++June+2026+-+Riyad+Bank.pdf/413e6b2c-63ac-1ea6-93ca-3b050709c3a0?t=1785342047399) |
| `riyad-2026-q1.json` | interim-report | 35 | 2026-03-31 | `c085bd5ecd8382da` | [link](https://www.riyadbank.com/documents/20121/0/Financial+statements++%E2%80%93+English+Q1+2026.pdf/28990178-4cc5-217d-3873-a6079b48def2?t=1777466611337) |
| `riyad-2026-q2.json` | interim-report | 54 | 2026-06-30 | `dbc5409a174c9091` | [link](https://www.riyadbank.com/documents/20121/0/Financial+statements++%E2%80%93+English+Q2+2026.pdf/c983bf54-0d92-e43b-d69c-b319b2e07ec7?t=1785334613832) |

### SAIB (sa:1030)

| Manifest | Type | Facts | Periods | SHA-256 (first 16) | Official URL |
|---|---|---:|---|---|---|
| `saib-2023-q2-supplement.json` | data-supplement | 76 | 2018-12-31 → 2023-06-30 (4) | `95da1034ae92a30c` | [link](https://www.saib.com.sa/sites/default/files/2023-08/20230809-SAIB-Data-Supplement-1H-2023.xlsx) |
| `saib-2024-05-pillar-3-workbook-pillar3.json` | regulatory-disclosure | 4 | 2023-03-31 | `c10ad4105fab2f88` | [link](https://www.saib.com.sa/sites/default/files/2024-05/Pillar-3-Workbook.pdf) |
| `saib-2024-08-saib-pillar-3-q2-2024-pillar3.json` | regulatory-disclosure | 4 | 2023-06-30 | `a2f6188faabb06f5` | [link](https://www.saib.com.sa/sites/default/files/2024-08/SAIB-Pillar-3-Q2-2024.pdf) |
| `saib-2024-11-pillar-3-disclosure-q3-2024-pillar3.json` | regulatory-disclosure | 4 | 2023-09-30 | `b8f8336839bdf900` | [link](https://www.saib.com.sa/sites/default/files/2024-11/Pillar-3-Disclosure-Q3-2024.pdf) |
| `saib-2025-04-pillar-3-workbook-dec-31-2024-pillar3.json` | regulatory-disclosure | 8 | 2023-12-31 → 2024-03-31 (2) | `c5c8c5ce7d337a22` | [link](https://www.saib.com.sa/sites/default/files/2025-04/Pillar-3-Workbook-%28Dec-31-2024%29.pdf) |
| `saib-2025-07-pillar-iii-disclosures-q2-2025-pillar3.json` | regulatory-disclosure | 4 | 2024-06-30 | `d50c49bab7c80f88` | [link](https://www.saib.com.sa/sites/default/files/2025-07/Pillar-III-Disclosures-Q2-2025.pdf) |
| `saib-2025-10-web-pillar-3-workbook-sep-2025-pillar3.json` | regulatory-disclosure | 12 | 2024-09-30 → 2025-03-31 (3) | `dbbc0f0a97524447` | [link](https://www.saib.com.sa/sites/default/files/2025-10/Web-Pillar-3-Workbook-Sep-2025.pdf) |
| `saib-2025-q2-supplement.json` | data-supplement | 16 | 2024-06-30 | `2f41b5fa3d30e056` | [link](https://www.saib.com.sa/sites/default/files/2025-08/SAIB-Data-Supplement-2Q-2025.xlsx) |
| `saib-2025-q3-supplement.json` | data-supplement | 48 | 2020-12-31 → 2025-09-30 (3) | `b10835dc9004daa2` | [link](https://www.saib.com.sa/sites/default/files/2025-11/SAIB-Data-Supplement-3Q-2025.xlsx) |
| `saib-2025-q4-supplement.json` | data-supplement | 26 | 2019-12-31 → 2020-12-31 (2) | `57f0a05edf6942fe` | [link](https://www.saib.com.sa/sites/default/files/2026-02/saib-data-supplement-4q-2025.xlsx) |
| `saib-2026-07-pillar-3-workbook-june-2026-web-pillar3.json` | regulatory-disclosure | 20 | 2025-06-30 → 2026-06-30 (5) | `6efc8535ec934d3f` | [link](https://www.saib.com.sa/sites/default/files/2026-07/Pillar-3-Workbook-june-2026-web.pdf) |
| `saib-2026-q2-supplement.json` | data-supplement | 692 | 2021-03-31 → 2026-06-30 (22) | `98711497658b7b19` | [link](https://www.saib.com.sa/sites/default/files/2026-08/SAIB-Data-Supplement-2Q-2026_0.xlsx) |
| `saib-km1-2022-03-pillar3.json` | regulatory-disclosure | 4 | 2021-03-31 | `4d4265d44a080521` | [link](https://www.saib.com.sa/sites/default/files/2022-05/SAIB-KM1-Mar-2022.pdf) |
| `saib-km1-2022-06-pillar3.json` | regulatory-disclosure | 4 | 2021-06-30 | `f84c566169eab6df` | [link](https://www.saib.com.sa/sites/default/files/2022-08/KM1-June-2022.pdf) |
| `saib-km1-2022-09-pillar3.json` | regulatory-disclosure | 4 | 2021-09-30 | `fe42982d67606910` | [link](https://www.saib.com.sa/sites/default/files/2023-03/SAIB%20KM1-Sep-2022.pdf) |
| `saib-km1-2023-03-pillar3.json` | regulatory-disclosure | 4 | 2022-03-31 | `c9a2b8ffcfcc6233` | [link](https://www.saib.com.sa/sites/default/files/2023-05/SAIB-KM1-Mar%202023.pdf) |
| `saib-km1-dec-2019-pillar3.json` | regulatory-disclosure | 20 | 2018-12-31 → 2019-12-31 (5) | `8853385498f92738` | [link](https://www.saib.com.sa/sites/default/files/2024-03/KM1-Dec-2019.pdf) |
| `saib-p3-2018-06-pillar3.json` | regulatory-disclosure | 8 | 2017-06-30 → 2017-09-30 (2) | `c4d3153084a93d79` | [link](https://www.saib.com.sa/sites/default/files/2024-03/Pillar%203%20-%20June%2030%2C%202018.pdf) |
| `saib-p3-2018-12-pillar3.json` | regulatory-disclosure | 8 | 2017-12-31 → 2018-03-31 (2) | `3df760876ae39337` | [link](https://www.saib.com.sa/sites/default/files/2024-03/December%202018%20Pillar%20III%20Web%20Disclosures-(F).pdf) |
| `saib-p3-2019-06-pillar3.json` | regulatory-disclosure | 8 | 2018-06-30 → 2018-09-30 (2) | `7c38ca3bd222e340` | [link](https://www.saib.com.sa/sites/default/files/2024-03/30-June-2019-PillarIII-Web-Disclosures.pdf) |
| `saib-p3-2022-12-pillar3.json` | regulatory-disclosure | 4 | 2021-12-31 | `b0b850e3f71b627f` | [link](https://www.saib.com.sa/sites/default/files/2023-03/SAIB-PIII-Dec-2022%20.pdf) |
| `saib-p3-2023-06-pillar3.json` | regulatory-disclosure | 4 | 2022-06-30 | `5011b997ef58cc9f` | [link](https://www.saib.com.sa/sites/default/files/2023-08/SAIB-Pillar-3%20-June-30-2023.pdf) |
| `saib-p3-2023-09-pillar3.json` | regulatory-disclosure | 4 | 2022-09-30 | `dc8746d426dce3f8` | [link](https://www.saib.com.sa/sites/default/files/2023-11/Web_Pillar-3-sep-2023.pdf) |
| `saib-p3-2023-12-pillar3.json` | regulatory-disclosure | 4 | 2022-12-31 | `2aed1d35e6e58138` | [link](https://www.saib.com.sa/sites/default/files/2024-02/Pillar-3-Dec-2023.pdf) |
