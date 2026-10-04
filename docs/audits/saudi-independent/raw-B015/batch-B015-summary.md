# Batch B015 raw-document statement audit (insurers): 8240 Chubb Arabia, 8130 Alahli Takaful (ATC), 8190 UCA, 8270 Buruj, 8050 Salama

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Statement pages were scans or image-only in almost every audited filing and were rendered and read by eye; born-digital pages (UCA FY2025, FY2023, H1/Q1 2026) were read from the text layer and tied by arithmetic. Transcripts in `transcripts/`, checks in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll, pre-zakat result plus zakat/tax to net result, cross-filing comparatives that fail on any undeclared difference, Q1 + Q2 = H1 rolls; all pass), guard test `tests/test_audit_raw_b015.py`. Per-company `documents[]` carry the full SHA-256 verified against the raw file; `files_not_audited_for_values[]` lists every other inventory file.

Three dimensions are kept separate. No company is claimed complete.

| Symbol (units) | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 8240 CHUBB ARABIA (full SAR) | 6 filings: FY2022 (IFRS 4), FY2023, FY2024, FY2025, Q1 2026, H1 2026; IFRS 17 restatement of FY2022 and FY2024 EPS declared | all 6 have scanned statement pages (FY2025 OCR garbled); 2 Chubb Limited files wrongly filed under 8240 | FY2022 to FY2025, interims 2022 Q1 to 2026 H1 present; 12 not value-read; no FY2021 |
| 8130 ATC = Alahli Takaful (SAR '000) | 4 filings: FY2018 as issued, FY2019, FY2020, 9M 2021; FY2018 restatement and FY2019 re-presentation declared | all 4 textless scans; H1 2018 whole-file scan unopened | FY2018 to FY2020 plus interims to 9M 2021; series ends because entity merged into Arabian Shield; 11 not value-read |
| 8190 UCA (SAR '000) | 6 filings: FY2022 (IFRS 4), FY2023, FY2024, FY2025, Q1 2026, H1 2026; IFRS 17 restatement and FY2023 re-presentation declared; going-concern uncertainty FY2025 | FY2024 and FY2022 statements image-only; others born digital | FY2022 to FY2025, interims 2022 Q1 to 2026 H1; 12 not value-read |
| 8270 BURUJ (full SAR) | 5 filings: FY2022 (IFRS 4), FY2023, FY2024, Q1 2025, H1 2025; IFRS 17 restatement declared | all image-only; two 2023 interims mis-classed no statements | FY2021 to FY2024, interims to 2025 H1; no 9M 2025, FY2025 or 2026 in collection (reason unestablished); 13 not value-read |
| 8050 SALAMA (SAR '000) | 6 filings: FY2022 (IFRS 4), FY2023, FY2024, FY2025, Q1 2026, H1 2026; IFRS 17, FY2024 cash-flow and EPS restatements declared | all image-only (H1 2026 only a stamp text) | FY2022 to FY2025, interims 2022 Q1 to 2026 H1; 12 not value-read |

## Defects (general)

1. Image-only or scanned statement pages classed financial_statements / annual_report_with_state (all five), or classed other_no_statements_found / partial_statements (8270 two 2023 interims, 8050 9M 2023).
2. Annual FY label equals publication year for every FS file in all five (2023|FY holds FY2022, etc.); inventory period_mismatch flags are correct detections.
3. IFRS 4 to IFRS 17 transition: FY2022 (and 1 Jan 2022) restated in the FY2023 filing for 8240, 8190, 8270, 8050; both values declared. Further re-presentations: 8240 FY2024 EPS, 8190 FY2023 BS/CF, 8130 FY2018 and FY2019, 8050 FY2024 CF and FY2023 EPS, Q1 2025 CF.
4. Wrong-entity files: 8240 holds two Chubb Limited documents (Swiss statutory FS, Q2 2026 profile).
5. Merged entity: 8130 ATC (Alahli Takaful) merged into Arabian Shield after 9M 2021; the symbol's series is final.
6. Going concern: 8190 FY2025 (net loss -256,220k, equity 24,579k, auditor material uncertainty).
7. Interim cash-flow Q2 by subtraction not valid (8240, 8190, 8050; classification and line items differ between Q1 and H1 statements).
8. Series ends without established reason: 8270 stops at H1 2025.
9. No duplicate-hash entries in the inventory anomaly queues for these five symbols.

## Unread (explicit)

Notes in every file (except specific passages named in records), most equity statements, interims identified by cover only, supplementary insurance-operations/shareholders statements (8240 appendix), Arabic originals (none in collection), the long lists in each JSON `unread_items` and `files_not_audited_for_values`.
