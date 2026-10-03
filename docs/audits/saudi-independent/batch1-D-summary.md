# Batch 1-D independent audit: 2010, 2082, 3010, 3030, 3050

Audited published branch: `origin/codex/telecom-95pct` @ `ec610f3`. ACWA FY2025 manifest exists only on `origin/claude/data-utilities-1` @ `ce167a8` (audited from there, read-only). 1050/1060 not touched. No data/**, AWS or Supabase changes.
Per-company evidence (page + line item) is in `<symbol>.json`. Rejected facts: none found in repo; AWS DB not reviewed (unverified).

## Status (three dimensions kept separate)

| Symbol | Numeric correctness | Document completeness | Company coverage |
|---|---|---|---|
| 3010 Arabian Cement | verified_correct (all 118 facts) | defective (pre-tax, OCI, EPS basic, many CF lines missing) | unverified (FY2025+FY2024 only) |
| 3030 Saudi Cement | verified_correct (all 104) | defective (OCI, debt/lease CF, equity stmt) | unverified (FY2025+FY2024 only) |
| 3050 Southern Province | verified_correct (all 103) | defective (31 Dec 2023 balance column, debt CF, OCI) | unverified (FY2025+FY2024 only) |
| 2010 SABIC | defective (10 defects; face statements correct) | defective | defective (no quarterly; FY2021-23 summary only) |
| 2082 ACWA | unverified for published Q2 (PDF missing); FY2025 branch manifest verified_correct (100 facts) | defective | defective (published: Q2 2026 only) |

## Defects proven
- SABIC: capex FY2025 PP&E-only vs FY2024 PP&E+intangibles (p137, p42); proceeds from asset sales FY2024 = 33,343+562,424 vs FY2025 82,308 only; D&A FY2025 12,762,575 vs cash-flow basis 12,897,679; FY2024 general reserve 110,889,032 not extracted; Murabaha 15,195,578 double counts 599 (p184); related-party payables +100 vs rows (p201); sales volumes 23.4/16.2 (incl. discontinued) conflict with 23.2/13.0 (continuing) (p47); "domestic_revenue_chemicals" is group revenue (p208); five-year "cash" is cash-flow cash; sign conventions mixed.
- Cement 3010/3030/3050: `filed_at` is the board-approval date, 5-9 days before the Saudi Exchange upload date in the URL (11 manifests repo-wide); capex definition differs between 3010 (with intangibles) and 3030/3050; 3050 omits the 31 Dec 2023 restated balance sheet shown on p6.
- ACWA: Q2 2026 PDF listed in archive-index but absent everywhere (blocked, not downloaded: needs approval); FY2025 audited manifest not on the published branch.

## Shared root causes
RC-FILED-AT, RC-CAPEX-DEFINITION (also seen for sa:3003 capex; sa:1080/1120 D&A labels, leads for other auditors), RC-PARTIAL-EXTRACTION, RC-COMPOSITE-LABEL-DOUBLE-COUNT, RC-OPERATING-BASIS, RC-SIGN-CONVENTION. Existing `ManifestVerifier` passes every manifest here (all identity checks), so none of the above is caught by identities. No reader/scale bug was found.

## Fix prepared
`src/finengine/audit_consistency.py` (report-only, offline): `definition_drift`, `dimension_reconciliation`, `filing_date_before_exchange_upload`; run with `python -m finengine.audit_consistency data/imports [prefix]`. Tests: `tests/test_audit_consistency.py` (11 pass); existing tests verification, cement batches 1-3, known_data_regressions, manifest_vintages: 49 pass. Repo-wide run also flags sa:7030 segment_revenue (sum exceeds revenue by 862,572k; lead for another auditor). Manifests are not edited.

## Unverified / blocked
ACWA Q2 2026 (PDF unavailable); SABIC unverified fact lists in `2010.json` (deep notes 36, gap-closure 25, ESG 7 cells located on page only); rejected facts / AWS DB; expected-period lists (none in repo).
