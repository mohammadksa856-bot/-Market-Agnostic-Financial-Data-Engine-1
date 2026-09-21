# Closing the known data regressions

Branch `claude/known-data-regressions-cleanup`, cut from `origin/main` at `5026292`.
Four known problems are closed here. No company is added, no data set is widened, and
every changed value is reproducible from a document already archived in this repository.

## What changed, in one view

| Manifests changed | Net facts added | Companies touched | Companies proven unchanged |
| --- | --- | --- | --- |
| 49 | +56 | Riyad Bank, BSF, ANB, Al Rajhi, Alinma | 25 of 30 |

## 1. Riyad Bank: the net fee subtotal was stored as gross fee income

**Cause.** Riyad Bank prints three lines that all begin with the same words:
`Fee and commission income`, `Fee and commission expense` and the subtotal
`Fee and commission income, net`. The manifests built before the caption for the net
subtotal existed stored that subtotal under `fee_income`, so the gross line was lost and
`net_fee_income` was absent. The reader on `main` already resolves the three captions
correctly - only the stored data was stale.

**Fix.** Each affected manifest was re-read from its own archived PDF; only its facts
were replaced, and every provenance field (source URL, filed-at basis and note, index
page, notes) was carried across untouched. Vintages were then reconciled with the
engine's own `reconcile_vintages`, and nothing was written that the accounting verifier
did not accept.

- Manifests re-read and verified: **37** (0 rejected)
- `fee_income` values replaced by the gross line: **26**
- Net-subtotal entries removed from `fee_income`: **29**
- `net_fee_income` facts added: **55**
- Facts in those manifests: 1,550 -> 1,577; facts removed other than the relabelled subtotal: **0**

The documented Q2-2020 example, before and after:

| Metric | Period | Before | After | Source label (page 3) |
| --- | --- | --- | --- | --- |
| `fee_income` | quarter 2020-06-30 | 322,740 | **481,519** | Fee and commission income |
| `fee_income` | ytd 2020-06-30 | 894,698 | **1,266,616** | Fee and commission income |
| `net_fee_income` | quarter 2020-06-30 | absent | **322,740** | Fee and commission income, net |
| `net_fee_income` | ytd 2020-06-30 | absent | **894,698** | Fee and commission income, net |
| `fee_expense` | quarter 2020-06-30 | -158,779 | -158,779 | Fee and commission expense |

Regression test: `tests/test_known_data_regressions.py::BankFeeLineTests`, built on that
three-line layout with Riyad Bank's own figures.

## 2. Pre-zakat facts the merged fix revealed

**Cause.** The cash-flow statement opens on a pre-zakat figure whose caption contains
the words "net income for the period". Until the mapping merged in `5026292`, that
caption resolved to the shorter net-income entry, so the line was either mis-mapped or
dropped. With the mapping in place those lines are real facts that were never published.

**Fix.** Only the manifests whose own archived document yields facts the stored file
lacks were rewritten. The rebuild refuses to run if any existing value would change or
any fact would disappear.

- Manifests rewritten: **12** (BSF 7, ANB 1, Al Rajhi 2, Alinma 2)
- Facts added: **29**; values changed across the whole branch: **26** (all of them the Riyad `fee_income` correction above); facts removed: **0**

Added across the branch, by metric: `cash_beginning` 2, `cash_end` 1, `dividend_income` 1, `financing_cash_flow` 2, `income_before_income_taxes_and_zakat` 18, `investing_cash_flow` 2, `net_fee_income` 55, `operating_cash_flow` 3, `taxes_paid` 1

The 18 pre-zakat facts are spread over four banks, not three: 17 are added here and the
eighteenth belongs to `riyad-2019-fy.json`, which was rebuilt with the Riyad correction
above.

| Bank | Manifest | Period | Kind | Value | Page |
| --- | --- | --- | --- | --- | --- |
| Alinma | `alinma-2019-fy.json` | 2019-12-31 | fy | 2,816,456 | 9 |
| Alinma | `alinma-2020-fy.json` | 2020-12-31 | fy | 2,201,760 | 11 |
| AlRajhi | `alrajhi-2023-q3.json` | 2023-09-30 | quarter | 4,632,996 | 4 |
| AlRajhi | `alrajhi-2023-q3.json` | 2023-09-30 | ytd | 13,881,858 | 4 |
| AlRajhi | `alrajhi-2024-q2.json` | 2024-06-30 | quarter | 5,225,744 | 5 |
| AlRajhi | `alrajhi-2024-q2.json` | 2024-06-30 | ytd | 10,139,903 | 5 |
| BSF | `bsf-2023-fy.json` | 2023-12-31 | fy | 4,707,833 | 11 |
| BSF | `bsf-2023-q1.json` | 2023-03-31 | quarter | 1,200,004 | 4 |
| BSF | `bsf-2023-q2.json` | 2023-06-30 | quarter | 1,193,077 | 4 |
| BSF | `bsf-2023-q2.json` | 2023-06-30 | ytd | 2,393,081 | 4 |
| BSF | `bsf-2023-q3.json` | 2023-09-30 | quarter | 1,382,969 | 4 |
| BSF | `bsf-2023-q3.json` | 2023-09-30 | ytd | 3,776,050 | 4 |
| BSF | `bsf-2024-q1.json` | 2024-03-31 | quarter | 1,282,450 | 4 |
| BSF | `bsf-2024-q2.json` | 2024-06-30 | quarter | 1,259,323 | 4 |
| BSF | `bsf-2024-q2.json` | 2024-06-30 | ytd | 2,541,773 | 4 |
| BSF | `bsf-2025-q3.json` | 2025-09-30 | quarter | 1,508,448 | 4 |
| BSF | `bsf-2025-q3.json` | 2025-09-30 | ytd | 4,569,562 | 4 |
| Riyad | `riyad-2019-fy.json` | 2019-12-31 | fy | 6,232,066 | 8 |

## 3. SABIC 2025 reproduced only 41 of its 59 facts

**Cause.** Two reader gaps, both general and both proven against the archived annual
report:

1. **A statement split across two pages.** SABIC prints its consolidated statement of
   cash flows on pages 136 and 137, the second headed "(continued)". The cash-flow
   signature demands "operating activities" *and* "financing activities" on one page,
   and neither page carries both, so the statement was never recognised. 16 facts lost.
2. **A second panel with no heading of its own.** The profit-attribution rows sit in a
   right-hand panel of the income statement on page 133. A page split into panels kept
   only the panels whose own heading matched, and the rule that generalises one heading
   across both panels applied to the balance sheet alone. 2 facts lost.

**Fix.** A page is now pooled with the page that follows it only when the issuer repeats
the same statement heading there, and one heading is generalised across both panels of
any statement only when the other panel names no statement of its own. Neither rule
loosens what counts as a statement: a following page that names something else, or a
panel that claims a different statement, is still refused - both cases are tested.

**Result.** `sabic-2025-fy.json` now reproduces from its archived PDF exactly: 59 stored,
59 read, 0 conflicting, 0 missing, 0 reader-only. No fact was deleted, and none had to be
moved to `excluded_facts`. The manifest file itself is unchanged - it was already right;
it simply could not be rebuilt before.

Regression tests: `SplitCashFlowStatementTests` and `TwoPanelStatementTests`, each with
a negative case.

## 4. The missing Aramco document

**Cause.** `data/raw/SA/2222/*` is excluded by `.gitignore:25`, so the annual report the
two quote-grounding tests read was never committed and is absent from every fresh clone.
Seven of the eight Aramco artifacts in the index were missing for the same reason.

**Fix.** The file was taken from the issuer's own page - the same URL the manifest and
the archive index already record - and verified before use:

- Source: https://www.aramco.com/-/media/publications/corporate-reports/reports-and-presentations/2025/fy/saudi-aramco-ara-2025-english.pdf
- Index page: https://www.aramco.com/en/investors/reports-and-presentations
- Size: 17,683,967 bytes, matching `byte_size` in `archive-index.json`, and inside
  GitHub's 100 MB per-file limit
- SHA-256: `78bb678e8e45f5c58fa1b2402ab5a29c5ad10adfda8ba5e7ee5f4d1ad76cd227` - identical to the `content_hash` recorded in the index
- Added with `git add -f`, since the path is gitignored

Neither test was modified, skipped or relaxed; both now pass on their own assertions.
Note that `aramco.com` refuses connections from the build shell (DNS resolves and TCP
connects, but every HTTP read is reset or times out, sandboxed or not), so the document
was retrieved through the browser instead. The remaining six Aramco binaries are still
absent; no test depends on them today.

## Production points, before and after

Measured by a CI-parity bootstrap into a scratch database, counting `data_points` rows
with `is_current = 1`.

| Company | Before | After | Delta | Metrics after |
| --- | --- | --- | --- | --- |
| Riyad | 2,255 | 2,282 | +27 | 90 |
| SAIB | 1,418 | 1,418 | +0 | 83 |
| BSF | 2,573 | 2,584 | +11 | 98 |
| SAB | 231 | 231 | +0 | 77 |
| ANB | 3,937 | 3,946 | +9 | 88 |
| AlRajhi | 2,286 | 2,296 | +10 | 104 |
| Alinma | 1,470 | 1,480 | +10 | 90 |
| SNB | 838 | 838 | +0 | 88 |
| AlJazira | 1,264 | 1,264 | +0 | 93 |
| Albilad | 1,959 | 1,959 | +0 | 98 |
| Aramco | 1,095 | 1,095 | +0 | 374 |
| SABIC | 768 | 768 | +0 | 325 |

## Companies proven unchanged

Every manifest was fingerprinted before the first edit and again afterwards. 25 of 30 companies are byte-identical, and no manifest outside the five banks named above changed at all:

`sa:1020`, `sa:1030`, `sa:1060`, `sa:1140`, `sa:1180`, `sa:2010`, `sa:2082`, `sa:2222`, `sa:3002`, `sa:3003`, `sa:3005`, `sa:3010`, `sa:3020`, `sa:3030`, `sa:3040`, `sa:3050`, `sa:3060`, `sa:7010`, `sa:7030`, `sa:7202`, `sa:7203`, `sa:8010`, `us:MSFT`, `us:NVDA`

## Checks

| Check | Baseline | After |
| --- | --- | --- |
| `verify --imports data/imports` | ok, 0 failures, 14 warnings | ok, 0 failures, 14 warnings (identical set) |
| Pipeline publication of every changed manifest | - | 49 published, 0 exceptions |
| `bootstrap` into a scratch database | exit 0 | exit 0 |
| `audit --project-root . --strict-warnings` | ready, 23,127 facts, 1 warning | ready, 23,194 facts, 1 warning |
| Full test suite | 340 tests, 2 errors (both Aramco quote-grounding) | **345 tests, 0 failures, 0 errors, 1 skipped** |

The two Aramco errors are gone because the document they read is now archived, not
because either test was changed. The count rises from 340 to 345 with the five
regression tests added in `tests/test_known_data_regressions.py`, three of which assert
the new reader behaviour and two of which assert what it still refuses to do.

The single audit warning is `enabled_company_coverage` for `us:COP`, `us:CVX`, `us:EOG`,
`us:OXY` and `us:XOM`, which unmodified `origin/main` reports too; it is why
`--strict-warnings` exits 1. The 14 verify warnings are unchanged from the baseline, both
in count and in content.

