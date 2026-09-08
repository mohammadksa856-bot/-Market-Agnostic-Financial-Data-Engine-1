# Saudi materials / petrochemicals sector — FY2025 batch 2

Batch branch: `claude/data-materials-2`. Source-faithful manifests transcribed by
hand from each issuer's official FY2025 audited consolidated financial statements
(the full audited PDFs linked on the Saudi Exchange company-profile "Financial
Statements" tab). No third-party data vendors. All PwC-audited.

## Companies

| Symbol | Company | Manifest | Status | Primary source |
|---|---|---|---|---|
| 2020 | SABIC Agri-Nutrients Company | `data/imports/sabic-agri-nutrients-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |
| 2310 | Sahara International Petrochemical Company (SIPCHEM) | `data/imports/sipchem-2025-fy.json` | enabled, published | Saudi Exchange company-profile "Financial Statements" tab → full audited consolidated FS PDF (PwC) |

## Source and archive

| Symbol | URL | SHA-256 | Local archive |
|---|---|---|---|
| 2020 | `https://www.saudiexchange.sa/Resources/fsPdf/382_0_2026-03-03_15-09-07_En.pdf` | `2697df89a62c351da1017fc8d1bd5fb876af856614cf810bce590f8380001bd1` | `data/raw/SA/2020/documents/2697df89…pdf` |
| 2310 | `https://www.saudiexchange.sa/Resources/fsPdf/411_0_2026-03-27_01-07-03_En.pdf` | `88430efa5a9b99617452aa32a899a5401f2a41339470cb3902841903998caa50` | `data/raw/SA/2310/documents/88430efa…pdf` |

Registered in `data/raw/archive-index.json` (SABIC AN 2,353,825 bytes; SIPCHEM
1,198,198 bytes; both `application/pdf`, digital text).

* **SABIC Agri-Nutrients (2020):** thousands of SAR. Board authorised issue
  **26 February 2026** (09 Ramadan 1447H). 50.1%-owned by SABIC (2010). The
  primary statements and notes are digital text, but the SoFP, income statement
  and cash-flow statement were cross-read from page images because the
  two-column PwC layout mis-aligns on plain text extraction. `income_taxes_and_zakat`
  sums the reported "Zakat expense", "Income tax expense" and "Deferred tax
  (expense) credit" (also carried split). `additional_paid_in_capital` = "Share
  premium". `other_noncurrent_liabilities` = the non-current "Derivative
  financial instrument" (a put/call option over Al-Bayroni NCI). No bank debt —
  only IFRS 16 leases. FY2025 net income +29.8% to SAR 4.47bn (EPS 9.08).

* **SIPCHEM (2310):** thousands of SAR. Board authorised issue **16 March 2026**
  (27 Ramadan 1447H). Digital text throughout (single-column layout). **FY2025
  was a loss year** — net loss SAR 772.4m (2024: +466.2m profit) as petrochemical
  margins compressed (gross profit SAR 256.7m vs SAR 1,439.5m) plus a SAR 300m
  PP&E impairment; `net_income`, `net_income_parent`, `comprehensive_income` and
  FY2025 EPS (−1.17 diluted) are all negative and retained earnings fell to
  SAR 2.7bn. `income_taxes_and_zakat` sums "Zakat (expense) / credit", "Income
  tax expense" and "Deferred tax credit / (expense)"; in FY2024 the net figure is
  a **+SAR 18.2m credit**. `impairment_charges` = the "Impairment of property,
  plant and equipment" add-back. `current_debt` sums the current portion of
  long-term borrowings and short-term borrowings. `provisions` = "Provision for
  decommissioning costs".

## Engine change (for integration review)

`src/finengine/bootstrap.py::_manifest_company` — when a legacy manifest with no
`company_id`/`cik` header (e.g. `aramco-2020-fy-historical.json`) matches more
than one registry company by filename, a distinctive **name-token** match (e.g.
"aramco") now wins over a bare **symbol substring** match (an issuer whose ticker
happens to equal a year in the filename — here SABIC Agri-Nutrients, ticker 2020).
Without this, adding ticker 2020 to the registry makes bootstrap fail to resolve
the Aramco 2020 historical manifest. Committed separately and flagged.

## Verification

`finengine verify sabic-agri-nutrients` → 24 pass / 0 warn / 0 fail;
`finengine verify sipchem` → 22 pass / 2 warn / 0 fail (the warns are the
effective-tax plausibility bound firing on a zakat charge/credit that is not a
function of pre-tax profit — SIPCHEM's FY2024 net zakat credit and its FY2025
zakat charge against a pre-tax loss). Bootstrap publishes 215 (SABIC AN) + 237
(SIPCHEM) data points with no pipeline errors. All balance-sheet identities, the
P&L bridge, gross-profit identity and the cash-flow reconciliation hold exactly.

Tests: `tests/test_materials_sector_batch2.py`.

## Unresolved fields

* **Saudi Kayan (2350), Petro Rabigh (2380), Tasnee / National Industrialization
  (2060)** — audited FS PDFs already archived; their primary statements are
  scanned images and need the vision transcription pass (follow-up in this batch
  or batch 3).
* **Product / plant-level volumes, capacity utilisation and realised prices** are
  in the board reports, not the audited FS.
* **EBITDA / net debt** — not presented as statement lines.
