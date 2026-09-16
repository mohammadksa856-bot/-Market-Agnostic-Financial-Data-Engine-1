# Saudi banks — BSF (1050) and ANB (1080), batch 1

Branch `claude/banks-bsf-anb-enrichment`, cut from `origin/main` at `4d9a0e1`.
Scope is limited to Banque Saudi Fransi (`sa:1050`) and Arab National Bank
(`sa:1080`). No database, deployment, service or worker was changed. Every fact
below was produced by an engine reader from an archived official document and
verified before it was written; nothing was transcribed by hand and nothing was
estimated.

<!-- SUMMARY_TABLE -->

## Source priority applied

1. **Issuer IR (primary).**
   * BSF — [quarterly results / investor presentations](https://bsf.sa/english/top-menu/investorrelation/quarterly-results):
     the quarterly Data Supplement workbooks (FY2015 onward) and the consolidated
     financial statements PDFs.
   * ANB — [financial reports](https://anb.com.sa/en/web/anb/financial-reports)
     (quarterly statements back to 2003) and
     [annual reports](https://anb.com.sa/en/web/anb/annual-reports)
     (Part 2 — Financial Statements).
2. **Saudi Exchange.** Attempted as the fallback for the Pillar 3 gap below; the
   portal answers `403` to this network, so it could not fill it.
3. **Regulator.** Not applicable — neither bank publishes a KM1 disclosure that
   could be reached.

## Regulatory capital: where it comes from for these two banks

Unlike the six banks merged before this batch, **neither BSF nor ANB publishes a
Basel III Pillar 3 KM1 disclosure on a reachable page**:

* BSF's investor site exposes 152 documents, all under one
  `Investor_Presentations` folder — statements, Data Supplements, earnings
  releases, presentations, transcripts and factsheets. There is no Basel or
  Pillar 3 document in either the English or the Arabic library, and no annual
  report either.
* ANB's Basel III disclosures page renders empty (no document links in the DOM),
  its investor-relations landing page carries only product menus, its sitemap
  lists no Basel or Pillar 3 entry, and the Euroland-hosted IR site used by the
  existing FY2025 manifest (`financial.eurolandir.com`) does not answer from this
  network.

BSF's own Data Supplement carries the regulatory lines, so for BSF they are read
from there: Tier 1 capital, total capital, risk-weighted assets, the liquidity
coverage ratio and the Basel III leverage ratio are now mapped, while the capital
adequacy, Tier 1 and NPL ratios stay unmapped because the engine recomputes them
from the published amounts. ANB has no reachable source for capital or liquidity
at all; that is recorded as an open gap rather than filled from a secondary site.

## Reusable engine changes

All three are generic, each with a regression test, and each was checked against
every manifest in `data/imports` that an engine reader produced (53 of them) by
re-reading its archived PDF before and after the change.

* `reading.py` — period columns headed by **pre-2010 years** were not detected:
  column detection accepted year headings from 2010 onward only, so a bank's
  older filings produced no value columns at all and read as empty. ANB
  publishes quarterly statements from 2003; lowering the floor to 2000 makes 33
  more of its archived documents readable (every quarter from 2003-Q2 to
  2010-Q4, plus the 2005–2008 and 2010 annual reports), 28–52 facts each. The
  floor still excludes 19xx, note-reference columns are still discarded, and the
  page must already be a confirmed statement.
  Test: `test_period_columns_headed_by_pre_2010_years_are_detected`.
* `reading.py` — the **trailing ", net" fee caption** had no entry, so it fell
  back to the gross caption: ANB's 2025 annual report published the net subtotal
  (878,412) as `fee_income` instead of the gross 2,283,365. Now
  `fee and commission income, net` maps to `net_fee_income`, matching the
  existing `fee income from banking services, net` precedent.
  Test: `test_trailing_net_fee_caption_is_not_gross_fee_income`.
* `reading.py` — the cash-flow statement heading list required the plural
  ("statement of cash flows"). ANB titles the page **"Consolidated statement of
  cash flow"**, so the entire page was skipped and every figure on it was lost:
  ANB's 2024 annual statements read 16 facts instead of 21, with no operating,
  investing or financing cash flow. The singular form is now recognised.
  Regression test: `tests/test_reading.py::test_cash_flow_statement_titled_in_the_singular_is_read`,
  which builds a statement page titled in the singular and asserts the three
  cash-flow subtotals are read. The change only adds a heading variant, so it
  cannot remove an existing match; the 2015-2023 ANB layouts and every BSF
  statement read identically before and after.
* `config/supplements/1050.json` — the BSF map now rounds to the issuer's
  reported precision (its formula cells carry binary float noise), carries
  `SAR/share` scale and unit on the per-share rows, integer share counts, and
  maps the capital and liquidity rows described above.

No catalog field was added: the Basel III amounts and ratios these banks report
(`tier1_capital`, `liquidity_coverage_ratio`, `leverage_ratio`,
`regulatory_capital`, `risk_weighted_assets`) already exist in the `banking_v1`
pack from the previous batch.

### Two findings for review (not changed by this batch)

* **Riyad Bank (`sa:1010`) carries the same fee mistake.** Its merged manifests
  print all three fee lines for many periods, and their stored `fee_income` is
  actually the net subtotal — for 2020-Q2, `fee_income` is 322,740 (quarter) and
  894,698 (YTD), which are the net figures; the gross lines are 481,519 and
  1,266,616. Rebuilding `sa:1010` with the corrected mapping would fix
  `fee_income` and add `net_fee_income` for 37 manifests. This batch does not
  rewrite another bank's merged data; it is left for Codex to schedule.
* **`sabic-2025-fy.json` no longer reproduces from its archived PDF.** It holds
  59 facts; both this branch *and* untouched `origin/main` read 41 from the same
  document (the cash-flow pages are no longer picked up). The manifest predates
  reader changes already merged into `main`, so this is pre-existing drift on an
  out-of-scope company, reported here rather than fixed.

## Vintage reconciliation

Each BSF Data Supplement repeats every prior quarter back to FY2015, so
`reconcile_vintages` keeps one source of record per fact — assurance first, then
the latest period covered, then `filed_at` — and the reviewed statements outrank
the workbooks for the periods they both cover. Superseded workbook vintages are
kept in the archive and recorded as superseded rather than deleted.

## Exceptions

<!-- EXCEPTIONS_TABLE -->

<!-- MANIFEST_TABLE -->
