# Batch B007 raw-document statement audit: 1830 Leejam, 8200 Saudi Re, 2083 Marafiq, 2060 Tasnee, 2310 SIPCHEM

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Statement pages without a text layer were rendered and read by eye; born-digital pages were read from the text layer with visual spot checks. Page transcripts under `transcripts/`, identity and cross-filing checks in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll, NI split, comparatives versus the filing that reports the period with explicit restated flags, Q1+Q2=H1 and H1+Q3=9M rolls; all pass), guard test `tests/test_audit_raw_b007.py`. Per-company `documents[]` carry the full SHA-256 (verified against the raw file), PDF page and printed page.

Three dimensions are kept separate. No company is claimed complete: every record lists unread items.

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 2310 SIPCHEM (SAR thousand) | 9 filings: FY2022 to FY2025, 9M 2024, 9M 2025, H1 2025, Q1 2026, H1 2026 | all 18 English period files 2022 Q1 to 2026 H1 hold full statements; 7 flagged partial are image-only; 2 scans and 2 "no statements" files are statements; 4 Arabic duplicates | 18 periods 2022 Q1 to 2026 H1 have a file, 9 value-read; nothing before 2022 Q1 |
| 2060 TASNEE (SAR thousand) | 10 filings: FY2017, FY2022 to FY2025, Q1/H1/9M 2025, Q1/H1 2026 | every English standalone FS file complete on image pages; two classed "no statements"; 4 Arabic twins, annual reports unread | 20 periods have a file (2017 FY, 2020 9M scans, 2022 Q1 to 2026 H1); 9 of 18 recent not value-read; 2013-2016, 2018-2021 absent |
| 2083 MARAFIQ (SAR thousand) | 7 filings: FY2022 to FY2025, Q1 2026, H1 2026, H1 2025 | FY2025, Q1 2026 scans classed unreadable are complete; many slots hold Arabic twins or misdated announcements | 2022 9M to 2026 H1 present as files, 9 not value-read; no 2022 Q1/H1; nothing before 2022 |
| 8200 Saudi Re (full SAR) | 5 filings: FY2023, FY2024, FY2025, Q1 2026, H1 2026 | FY2022 to FY2025 standalone FS present; 2009-2016 files not opened; Arabic twins everywhere | only 2023 to 2026 H1 verified; 2009-2022 and interims 2022-2025 unread |
| 1830 Leejam (full SAR) | 8 filings: FY2022 (as filed), FY2023 to FY2025, Q1/H1 2026, headline-only Q1/H1 2025 | FY2022 to FY2025 complete; 5 scans identified by covers; results releases are not statements | FY2022 to FY2025 plus 2025 and 2026 H1 verified; 2018 to 2021 and 2022-2024 interims unread |

## Defects (general)

1. **Annual label = publication year** in all five companies. The standalone FS for FY(n) is labelled FY(n+1). Language twins and annual reports of the same year often carry different labels, so two fiscal years can share a slot (2060, 2083, 1830, 2310, 8200). Inventory "internal gap" and "unexpected 2026|FY" findings follow from this.
2. **Image-only statement pages inside text PDFs** are classified partial, "no statements found" or "scanned_unreadable" (2310, 2060, 2083, 8200, 1830). Rendered pages show complete BS, IS and cash flows. Whole-file scans (2083 FY2025 and Q1 2026, 1830 FY2023) render legibly.
3. **Restated and re-presented comparatives** change the value of one period by filing: 2060 FY2024 (net loss -27,632 as filed, -277,632 re-presented; total assets -250,000), 2083 FY2023 (net profit 525,798 vs 587,002; total assets 23,052,555 vs 24,026,706) and FY2024 CFO (2,380,846 vs 1,758,151), 8200 FY2023 total assets and Dec-2025 balance sheet, 1830 FY2022 (257,259,132 vs 254,758,323), 2310 FY2021/FY2022 tax and cash-flow reclassification. Both versions are in the transcripts.
4. **Unit scale**: 2310, 2060, 2083 report SAR thousand; 8200 and 1830 report full SAR in annual and interim files alike. No annual versus interim scale difference was found.
5. **Cash definitions**: BS cash differs from cash-flow ending cash for 8200 (FY2023, FY2024) and 1830 (FY2024, FY2025, Q1 2026, held-for-sale cash); 2060 H1 2026 includes held-for-sale cash.
6. **Misdated announcements** (2083: Arabic results releases dated "30 June 2023" in four slots) and duplicate or language-twin files counted as separate period files.

## Unread (explicit)

Notes in every file; most equity statements; all annual reports; Arabic files; per-company lists of unread interims and pre-2022 history in each JSON `unread_items` and `files_not_audited_for_values`.
