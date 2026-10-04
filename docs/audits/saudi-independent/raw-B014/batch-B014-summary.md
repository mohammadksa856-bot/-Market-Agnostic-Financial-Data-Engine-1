# Batch B014 (insurers) - statement-level audit of raw collected documents

Companies: 8311 ENAYA, 8040 MUTAKAMELA, 8020 MALATH INSURANCE, 8012 JAZIRA TAKAFUL, 8160 AICC. Raw files read only from `C:/Users/Mohammed856/finengine-raw-odd`; no network, no `data/**`, no AWS or Supabase writes. Method follows B009 and B011: page transcription (text layer where clean, rendered images read by eye where image-only or OCR-corrupted), SHA-256 recomputed for every file, arithmetic identities and a restatement detector in `tools/check_transcripts.py`, offline guard in `tests/test_audit_raw_b014.py`.

Three dimensions are kept separate: value correctness, document completeness, company coverage (page-derived periods, never collector labels). No company is claimed complete as a company history.

## Per-company status

| Symbol | Files | Statement sets transcribed | Value correctness | Document completeness | Company coverage (page-derived) |
|---|---|---|---|---|---|
| 8311 ENAYA | 26 | 18 (FY2020-FY2025, 9M 2021 scan, all 2023-H1 2026 interims) | verified from pages, identities pass, 50 declared restatement differences | all 26 are single-period statement sets; FY2020 primary pages and the whole 9M 2021 file are image-only and read by eye | Q1 2020 to H1 2026 present once each; 8 interim sets 2020-2022 plus Q1 2021 not transcribed |
| 8040 MUTAKAMELA | 33 | 14 (FY2022-FY2025, Q1/H1 2023, Q1/H1/9M 2024, Q1/H1/9M 2025, Q1/H1 2026) | verified from pages (almost all image or OCR), 108 declared differences incl. FY2025 note 33 prior-period error | English files complete but image-only or OCR-corrupted; 15 Arabic files unread | interims 2020-2026 present (2020-2021 Arabic only), annuals FY2022-FY2025 only; restated 2023 income statement not in any file |
| 8020 MALATH | 18 | 9 (FY2022-FY2025, Q1/H1/9M 2025, Q1/H1 2026) | verified from pages, 17 declared differences | 18 single-period statement sets, 6 with image-only or OCR primary statements | Q1 2022 to H1 2026 present once each; nine 2022-2024 interim sets not transcribed |
| 8012 JAZIRA TAKAFUL | 18 | 12 (FY2022-FY2025, Q1/H1/9M 2024, Q1/H1/9M 2025, Q1/H1 2026) | verified from pages, 16 declared differences | 18 single-period statement sets, Q1 2025 image-only read by eye | Q1 2022 to H1 2026 present once each; six 2022-2023 interim sets not transcribed |
| 8160 AICC | 18 | 10 (FY2022-FY2025, Q1 2023 scan, Q1/H1/9M 2025, Q1/H1 2026) | verified from pages (all images), 41 declared differences | 18 single-period statement sets, nearly all primary statements image-only | Q1 2022 to H1 2026 present once each; eight 2022-2024 interim sets not transcribed |

## Cross-cutting findings

1. Annual period label is the publication year for FY2022-FY2025 in all five companies (2023|FY = FY2022 and so on). ENAYA also carries true-year labels for FY2020 and FY2021, and the collector counts its FY2022 file under both 2022|FY and 2023|FY. The inventory 2022|FY gaps for Jazira and AICC are label artefacts (the file is present as 2023|FY).
2. IFRS 17 transition restated 2022 at every company that has both filings; both values are declared with the source filings, never substituted. Several companies also show 31 Dec 2022 or 1 Jan 2022 opening balance sheets that differ between the first 2023 interim and the FY2023 annual.
3. MUTAKAMELA (formerly Allianz Saudi Fransi) restated the 31 Dec 2023 and 31 Dec 2024 balance sheets for a material prior-year error (equity 800,684,313 -> 689,885,283 and 813,091,361 -> 702,292,331); the restated 2023 income statement is not in the collected pages. Entity renamed from Allianz Saudi Fransi to Mutakamela with the FY2024 annual.
4. ENAYA: the 31 Dec 2023 total assets are printed four different ways (339,800 / 343,127 / 335,309 / 325,127) with equity unchanged; the FY2025 audit report has a going-concern material uncertainty after the Salama merger was not approved on 1 Feb 2026.
5. AICC: the 9M 2025 income statement prints insurance service expenses as positive amounts; only insurance service result is comparable with FY2025. Amounts are whole SAR for MUTAKAMELA and AICC and SAR thousand for the other three.
6. Image-only primary statements dominate: inventory statement_pages and missing-cash-flow flags are unreliable for MUTAKAMELA, MALATH, JAZIRA (Q1 2025) and AICC; two whole-file scans (ENAYA 9M 2021, AICC Q1 2023) are complete interim sets.

## Unread items (explicit)

Notes to the statements in all files (except MUTAKAMELA FY2025 note 33 and ENAYA going-concern text); equity statements and OCI; the 15 Arabic files of MUTAKAMELA; every interim set listed above as not transcribed (ENAYA 2020-2022 and Q1 2021; MUTAKAMELA 9M 2023 and the 2022 IFRS 4 interims; MALATH, JAZIRA and AICC 2022-2024 or 2022-2023 interims); history before the earliest file for every company.

Per-company JSON: `<symbol>.json`; page transcriptions: `transcripts/<symbol>.json`; spec scripts that built them: `tools/specs/`; renders are not committed.
