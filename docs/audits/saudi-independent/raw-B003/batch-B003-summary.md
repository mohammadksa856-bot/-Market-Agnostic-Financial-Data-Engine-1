# Batch B003 raw-document statement audit: 2050, 2080, 2020, 2280, 2330

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Statement pages were rendered and read by eye (image-only pages) or read from the text layer with a visual spot check (born-digital); transcripts under `transcripts/`, identity checks in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll including FX, NI split; all pass), guard test `tests/test_audit_raw_b003_transcripts.py`.

Three dimensions are kept separate. Nothing is claimed complete: every company has unread items, listed per company JSON.

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 2050 Savola | FY2022, FY2023, FY2024, FY2025 and H1 2026 verified from pages (SAR thousand), originals and re-presented versions both transcribed | 4 FY files mislabelled (publication year); image-only statements wrongly flagged; 2004/2005 files are board reports | FY2022-25 + H1 2026 verified, 14 more interims likely present but unread; 2008, 2017-2021 absent |
| 2080 GASCO | 9 filings verified (FY2022-FY2025, Q1/H1/9M 2025, Q1/H1 2026), whole SAR | 4 FY files mislabelled; image-only statements flagged "missing cash flow"; Arabic bulletins classified as statements | FY2022-25 and 2025-26 interims verified; 2022-24 interims present as images, unread; 2018-2021 gap confirmed |
| 2020 SABIC Agri-Nutrients | 9 filings verified (FY2023, FY2024, Q1-9M 2024, Q1-9M 2025, 9M 2023), SAR thousand | 4 files flagged partial are complete (image-only statements); FY labels correct | 9 periods complete, FY2025 and 2026 absent, 2023 Q1/H1 only announcements |
| 2280 Almarai | FY2022-FY2025 and H1 2026 verified | 4 FY files mislabelled; 5 "scanned_unreadable" files are scanned results announcements, not statements | FY2022-25 + H1 2026 verified; 2018-2021 announcements only; 2025 Q1 and 2026 Q1 statements absent |
| 2330 Advanced | Only 5 headline H1 2026 figures (SAR millions) verified, from a press release | The single file is not a statement | None: 1 of 40 periods, non-statement |

## Defects (general)

1. **Period label = publication year for annual statements** (2050, 2080, 2280; not 2020, which was labelled correctly). Fourteen annual FS PDFs in this batch carry the label of the year after the fiscal year; the inventory flag `period_mismatch_candidate` is a true positive and could drive an automatic relabel (cover text "for the year ended 31 December YYYY").
2. **Image-only statement pages are classified as partial / no statements.** Pages of the statements have no text layer; the inventory saw only note text. All files spot-read this way contained complete statements (2020: FY2023, FY2024, Q1 2025, H1 2024; 2050; 2080; 2280).
3. **Restated comparatives** change the value of the same fiscal period depending on the filing used: Savola FY2022-FY2024 (revenue, operating profit, CFO), GASCO FY2022 and FY2024 (CFO/CFI reclass), Almarai FY2022 (CFO 300). Both versions are in the transcripts.
4. Scanned announcement files are labelled `scanned_unreadable` and could be reclassified as `results_announcement` after reading the first page (2280).

## Unread (explicit)

Notes in every file; equity statements (mostly); text-layer interims not individually rendered; Arabic annual reports and bulletins (2050, 2080); all image interims not listed as verified. See each JSON `unread_items`.
