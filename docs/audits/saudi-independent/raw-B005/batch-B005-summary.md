# Batch B005 raw-document statement audit: 4250, 4164, 4321, 4009, 4013

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Statement pages were rendered and read by eye (image-only and scanned pages) or read from the text layer (born-digital); transcripts in `transcripts/`, identities in `tools/check_transcripts.py` (BS identity, cash-flow sum and roll including FX, NI split, tolerance 1 only for rounded board-report tables), guard test `tests/test_audit_raw_b005_transcripts.py`.

Three dimensions are kept separate. No company is claimed complete: every JSON lists unread items (notes everywhere, equity statements mostly, many interim filings never opened).

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 4250 Jabal Omar | 10 filings verified (FY2022-FY2025, H1 2026, Q1 2026, 9M 2025, H1 2025 partial, Q1 2025, H1 2024), SAR thousand | all read files complete; 8 flagged partial/no-statements wrongly; 4 annual labels = publication year | 10 verified + 8 present unread; 2017-2021 absent |
| 4164 Nahdi | 7 filings verified (FY2022-FY2025, 9M 2025, Q1 2026, H1 2026), whole SAR | full audited FS flagged no-statements/unreadable; 4 English annual labels shifted | 7 verified + 11 interims present unread |
| 4321 Cenomi Centers | 5 filings verified (9M transition to 2022-12-31, FY2023-FY2025, H1 2026), whole SAR | fiscal year changed March to December in 2022; scanned FS misclassified; 4 annual labels shifted | 5 verified, about 13 more unread; pre-2022 statements absent |
| 4009 Saudi German Health | no statement values: only board-report summary tables (SAR million, rounded) | no primary statements in any of 3 files; "FY2025" report carries FY2024 numbers | none (0 of 41 periods) |
| 4013 Sulaiman Alhabib | 5 filings verified (FY2022-FY2025, H1 2026), whole SAR | scanned FS flagged unreadable; garbled cash-flow OCR text layer in FY2025; 4 annual labels shifted | 5 verified + 13 interims present unread |

(4250 row: verified = FY2022, FY2023, FY2024, FY2025, Q1 2026, H1 2026, 9M 2025, H1 2025 partial, Q1 2025, H1 2024.)

## Defects (general)

1. Annual FS labelled with the publication year (4250, 4164 English, 4321, 4013). 4321 additionally has a 9-month transition period (fiscal year change) labelled as a full year.
2. Image-only or scanned statement pages classified as partial / no statements / unreadable (all four companies with statements).
3. 4009: board-report summary pages classified as statements; the FY2025 annual report contains stale FY2024 financial tables under shifted year headers.
4. Re-presented comparatives and cash-flow basis changes (interest paid, restricted cash, loan gross-up, development property) change CFO/CFI/gross profit for the same period depending on filing; both versions transcribed. 4250 H1 2026 vs Q1 2026 cash flows are on different bases.
5. 4321 inventory expected-period grid keeps a March year end.

## Incomplete / unread (explicit)

Notes; equity statements (mostly); all interims not listed as verified (4250: 8, 4164: 11, 4321: about 13, 4013: 13); Arabic statement numbers; annual reports, factsheets, press releases. See each JSON `unread_items`.
