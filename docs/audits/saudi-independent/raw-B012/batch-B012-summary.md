# Batch B012 raw-document statement audit: 6014 Alamar, 6015 Americana, 6070 Al-Jouf, 6090 Jazadco, 6002 Herfy

Source: `C:\Users\Mohammed856\finengine-raw-odd` (read-only), inventory `origin/claude/audit-saudi-raw-coverage`. No network, no data/**, AWS or Supabase. Born-digital statement pages were read from the text layer (rows rebuilt from word coordinates, `tools/auto.py`) and tied by arithmetic; every image-only page, whole-file scan and text layer that loses signs was rendered and read by eye. Transcripts in `transcripts/`, checks in `tools/check_transcripts.py` (balance sheet identity, cash-flow sum and roll, gross profit, pre-tax to net result incl. discontinued operations, owners + NCI, Q1+Q2=H1 and H1+Q3=9M rolls, cross-filing comparatives with explicit restated flags; all pass), guard test `tests/test_audit_raw_b012.py`. Per-company `documents[]` carry the full SHA-256 recomputed from the raw file; `files_not_audited_for_values[]` lists every other inventory file.

Three dimensions are kept separate. No company is claimed complete.

| Symbol | Value correctness | Document completeness | Company coverage |
|---|---|---|---|
| 6014 ALAMAR (SAR, full riyals) | 20 filings FY2021 to FY2025, H1 2021, Q1 to 9M 2022 to 2025, Q1/H1 2026; 3 cash-flow re-presentations declared | 20 of 25 files hold statements; 5 whole-file scans classed unreadable; FY2023 BS page image-only inside a text file; 3 annual reports without statements | FY2021 to FY2025 and interims 2021 H1, 2022 Q1 to 2026 H1; collector label 2022\|H1 233a32b3 is H1 2021 |
| 6015 AMERICANA (USD thousand, not SAR) | 19 documents; no restatement; pre-IPO FY2021 to 9M 2022 are carve-out statements of Kuwait Food Co's restaurant business | balance sheet page image-only in 14 filings; scrambled text layer in H1 2022; duplicates and Arabic twins | FY2021 to FY2025 and interims 2022 H1 to 2026 H1 except Q1 2022; 15 files not value-read |
| 6070 ALJOUF (SAR) | 18 filings FY2022 to FY2025 and every interim 2022 Q1 to 2026 H1; 5 cash-flow and one PPE re-presentation declared | seven image-only files, five misclassified as no-statements; FY2025 text layer loses parentheses and splits numbers | FY2022 to FY2025, all interims; FY2021 and earlier absent |
| 6090 JAZADCO (SAR) | 18 filings FY2022 to FY2025 and every interim; heavy restatements (FY2023 net profit 1.52m becomes loss (32.3m)) declared with both values; one printed transposition | six scans, image-only IS/CF in Q1 2024, text layers drop signs and columns; 2025\|9M slot holds the board report | FY2022 to FY2025, all interims; FY2021 and earlier absent |
| 6002 HERFY (SAR) | 6 filings (FY2023, FY2024, FY2025, H1 2025, Q1 2026, H1 2026); no restatement | every statement page in all 19 files is an image; inventory classes unreliable | FY2022 to FY2025 and interims present; 13 of 19 files not value-read; 2023\|Q1 a6891af2 is a Q4/FY2023 filing |

## Defects (general)

1. Annual FY label = publication year (FY n+1) for 6014, 6070, 6090, 6002 and mostly 6015 (6015 mixes: 2022\|FY and 2023\|FY hold FY2022 and FY2023, 2025\|FY holds FY2024).
2. Image-only statement pages and whole-file scans classed partial, unreadable or no-statements (all five); 6015 balance sheets and 6002 all statements are images.
3. Text layers that drop parentheses, split numbers or add a third column (6070 FY2025 and H1 2024, 6090 2023 to 2025, 6015 H1 2022): text-only extraction yields wrong signs or columns.
4. Restated or re-presented comparatives: 6014 cash flows; 6070 cash flows and PPE; 6090 FY2022, FY2023, 2024 interims, 2023 interims and 2025 cost-of-revenue grossing; none found for 6015 and 6002.
5. Mislabelled collector periods: 6014 233a32b3 (2022\|H1 is H1 2021), 6002 a6891af2 (2023\|Q1 is Q4/FY2023), 6090 38696e57 (2025\|9M is the annual report), 6015 d8c7a726 (2023\|FY is a duplicate of FY2022).
6. 6015 reports in USD thousand (not SAR) and is a PLC with carve-out pre-IPO statements.

## Unread (explicit)

Notes in every file; all equity statements; Arabic twins; auditor reports; annual reports; pre-2021/2022 history (absent from the file sets); 6002: 13 of 19 files; 6015: Arabic files, the 2023 annual report and the FY2022 scan balance sheet. Per-company `unread_items` and `files_not_audited_for_values` give the exact lists.
