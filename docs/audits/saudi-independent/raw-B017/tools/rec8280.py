"""Builds raw-B017/8280.json from the page transcripts."""
import mkrecord

U = "SAR thousands (SAR 000) as printed"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("0d5ddad6", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 9, "is": 10, "cf": 13}, {"bs": 8, "is": 9, "cf": 12}, "visual (whole file image-only; inventory class scanned_unreadable although it holds full statements)",
        "Balance-sheet cash 59,395 versus cash-flow closing 58,672 (difference 723; 2024 85,512 versus 84,839, difference 673); cause not read (notes). Auditors PwC and Crowe, report dated 19 Feb 2026."),
    doc("b374e6d4", "FY ended 2024-12-31 audited FS with 2023 and 1 Jan 2023 restated (label 2025|FY = publication year)", False, {"bs": 9, "is": 10, "cf": 13}, {"bs": 8, "is": 9, "cf": 12}, "text layer (clean, identities tie) plus image of the income page",
        "1 Jan 2023 column (note 25 restated) shows total equity 375,157 versus 333,423 for 31 Dec 2022 in the FY2023 filing: a second restatement of the opening position, not transcribed to the cross-check."),
    doc("c79efac6", "FY ended 2023-12-31 audited FS as first issued, first IFRS 17 year, 2022 and 1 Jan 2022 restated; issuer already renamed Liva (formerly Al Alamiya) (label 2024|FY = publication year)", False, {"bs": 7, "is": 8, "cf": 11}, {"bs": 5, "is": 6, "cf": 9}, "visual (pdf p3-6 textless; statement pages read as images)",
        "FY2023 cash flow re-presented in the FY2024 filing (CFO 12,930 to 1,003, CFI 54,781 to 66,708). FY2023 income statement shows other income 19,394 separately; FY2024 comparative nets it (net result 11,258 identical)."),
    doc("8e205eda", "FY ended 2022-12-31 audited FS as issued under IFRS 4, issuer name Al Alamiya for Cooperative Insurance Company (label 2023|FY = publication year)", False, {"bs": "8-9", "is": "10-11", "cf": 13}, {"bs": "8-9", "is": "10-11", "cf": 13}, "text layer rows (identities tie); detail lines not transcribed",
        "IFRS 4 presentation (gross premiums written 455,162, total revenues 227,043); restated to IFRS 17 in the FY2023 filing. Both declared; neither substituted. Balance-sheet cash 37,443 versus cash-flow closing 36,743."),
    doc("f998e711", "3M and 6M ended 2026-06-30 unaudited interim (label 2026|H1 correct); latest period in the collection", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 2, "is": 3, "cf": 6}, "visual (whole file image-only; scanned_unreadable class)",
        "income columns 3M 2026, 3M 2025, 6M 2026, 6M 2025; cash flow six-month only; balance-sheet cash 40,596 versus cash-flow closing 39,867"),
    doc("8b8d8e7a", "3M ended 2026-03-31 unaudited interim (label 2026|Q1 correct)", True, {"bs": 4, "is": 5, "cf": 8}, {"bs": 2, "is": 3, "cf": 6}, "text layer rows (clean; cash-flow line order scrambled but values tie by identity)",
        "balance-sheet cash 61,963 versus cash-flow closing 61,245"),
]
nt = "not transcribed"
identified = {
    "2360156c": ("one-page monthly Statement of Comprehensive Income (unreviewed) for the month ended 2014-10-31, Al Alamiya", "monthly, not an annual or quarterly statement; label 2014|None"),
    "5db9da66": ("one-page monthly statement for the month ended 2014-08-31, Al Alamiya", "monthly page; label 2014|None"),
    "ca6e2f7c": ("one-page monthly statement for the month ended 2014-11-30, Al Alamiya", "monthly page; label 2014|None"),
    "8d50dac6": ("one-page monthly statement for the month ended 2014-09-30, Al Alamiya", "monthly page; collector labels it 2014|9M but it is not a nine-month statement set"),
    "74f71a5f": ("one-page monthly statement for the month ended 2014-12-31, Al Alamiya", "monthly page; collector labels it 2014|FY but it is not an annual statement set"),
    "199bffb2": ("one-page monthly statement for the month ended 2015-01-31, Al Alamiya", "monthly page; label 2015|None"),
    "a1dff86d": ("not identified from text (whole file image-only, scanned_unreadable); label 2022|9M", "not opened as images for this audit"),
    "456de333": ("not identified from text (whole file image-only, scanned_unreadable); label 2022|H1", "not opened as images for this audit"),
    "dfd3791d": ("not identified from text (whole file image-only, scanned_unreadable); label 2022|Q1", "not opened as images for this audit"),
    "2f35a727": ("2-page results announcement (Al Alamiya), label 2023|9M", "announcement, not statements"),
    "cb208e83": ("2-page results announcement (Al Alamiya), label 2023|H1", "announcement, not statements"),
    "654af658": ("1-page results announcement (Al Alamiya), label 2023|Q1", "announcement, not statements"),
    "b7fc3ef6": ("3M and 9M ended 2023-09-30 interim (cover text; issuer Liva formerly Al Alamiya)", nt),
    "eb5436e2": ("3M and 6M ended 2023-06-30 interim (cover text; Al Alamiya name)", nt),
    "e3ad35f1": ("3M ended 2023-03-31 interim (cover text; Al Alamiya name)", nt),
    "dd0a46e9": ("3M and 9M ended 2024-09-30 interim (cover text)", nt),
    "d52580df": ("3M and 6M ended 2024-06-30 interim (cover text)", nt),
    "923527ed": ("not identified from text (whole file image-only, scanned_unreadable); label 2024|Q1", "not opened as images for this audit"),
    "3c056c71": ("3M and 9M ended 2025-09-30 interim (cover text)", nt),
    "671d9cf4": ("3M and 6M ended 2025-06-30 interim (cover text)", nt + "; H1 2025 comparatives read in the H1 2026 filing"),
    "53f6446d": ("3M ended 2025-03-31 interim (cover text)", nt + "; Q1 2025 comparatives read in the Q1 2026 filing"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatements_noted",
        "summary": "Headline BS, income and cash-flow values (SAR thousands as printed) read for FY2025 (image-only file), FY2024 (clean text layer plus image of the income page), FY2023 as first issued (2022 restated), FY2022 as issued under IFRS 4 (text layer), H1 2026 (image-only file) and Q1 2026 (text layer). All identities pass exactly. FY2025: insurance revenue 575,028, profit before zakat 30,732, net profit 26,640 (EPS 0.67), total assets 1,056,991, equity 478,678, CFO 66,247, closing cash per cash flow 58,672 (balance-sheet cash 59,395). FY2024 net profit 32,761; FY2023 11,258; FY2022 IFRS 4 -48,775 versus IFRS 17 restated -42,945. H1 2026 net profit 16,487 (Q1 7,231, Q2 9,256); Q1 + Q2 = H1 for revenue, profit before zakat, zakat and net profit in 2026 and 2025 (pass). Declared: IFRS 4 to IFRS 17 FY2022 restatement; FY2023 cash flow re-presented in the FY2024 filing (CFO 12,930 versus 1,003); second restatement of the 1 Jan 2023 opening equity (375,157 versus 333,423). Insurance service expense is printed in brackets (negative). Entity: Liva Insurance Company is the former Al Alamiya for Cooperative Insurance Company; the FY2022 filing and earlier interims carry the Al Alamiya name and FY2023 onward carry Liva (formerly Al Alamiya); the symbol 8280 is the same company throughout.",
        "not_read": ["notes (name-change note, note 25 restatement)", "statements of changes in equity", "supplementary insurance-operations / shareholders statements (FY2025 pdf p67-68 index)", "cause of balance-sheet cash versus cash-flow cash differences", "Q2 cash flow by subtraction not validated", "all other 21 files", "segment-note totals versus the primary balance sheet"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_six_files_opened_two_whole_file_scans_read_as_images",
        "summary": "Six files carry balance sheet, income statement and cash flow. 0d5ddad6 (FY2025) and f998e711 (H1 2026) are entirely image pages and are classed scanned_unreadable by the inventory although they hold full statements; four 2022 and 2024 interims (a1dff86d, 456de333, dfd3791d, 923527ed) are also scanned and unopened. Six 2014 to 2015 files are single monthly statement pages (partial_statements) that the collector labels 2014|9M, 2014|FY and 2014|None; they are not annual or quarterly statement sets. Three results announcements (2023 Q1, H1, 9M) are not statements. No FY2021 or earlier own annual statements exist in the collection, and none for FY2015 to FY2021.",
        "defect_ids": ["B017-8280-1", "B017-8280-2", "B017-8280-3", "B017-8280-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_verified_interims_2022_to_2026_H1_present_pre_2022_history_absent",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)", "2022 Q1/H1/9M (scanned, unopened)", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1 (scanned, unopened)", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1",
                                                    "2014-08 to 2015-01 monthly pages (six one-page files)"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing)", "FY2022 IFRS 17 restated (FY2023 filing)", "FY2023 re-presented (FY2024 filing)", "2025 Q1 and H1 (2026 filings)"],
        "values_not_read": ["2022 to 2025 interim originals", "six 2014/2015 monthly pages"],
        "missing": ["FY2015 to FY2021 own filings (no file)", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in the four FS files read. 2014|9M and 2014|FY labels on one-page monthly statements are wrong in kind (monthly pages).",
    },
}
defects = [
    {"id": "B017-8280-1", "class": "scanned_unreadable_files_that_hold_full_statements", "severity": "high",
     "evidence": "0d5ddad6 (FY2025) pdf p9, p10, p13 and f998e711 (H1 2026) pdf p4, p5, p8 are full primary statements on image pages yet classed scanned_unreadable; a1dff86d, 456de333, dfd3791d, 923527ed remain scanned and unopened."},
    {"id": "B017-8280-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "8e205eda FY2022 labelled 2023|FY, c79efac6 FY2023 labelled 2024|FY, b374e6d4 FY2024 labelled 2025|FY, 0d5ddad6 FY2025 labelled 2026|FY."},
    {"id": "B017-8280-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17 transition: FY2022 net loss -48,775 as issued (8e205eda pdf p10) versus -42,945 restated (c79efac6 pdf p8); total assets 913,730 versus 790,444; CFO 37,459 versus 41,993. FY2023 CFO 12,930 (c79efac6 pdf p11) versus 1,003 (b374e6d4 pdf p13); 1 Jan 2023 equity 375,157 (b374e6d4 pdf p9) versus 333,423 (c79efac6 pdf p7). Both recorded, none substituted."},
    {"id": "B017-8280-4", "class": "renamed_entity_and_mislabelled_monthly_files", "severity": "medium",
     "evidence": "Al Alamiya for Cooperative Insurance Company renamed Liva Insurance Company (cover of c79efac6 and b7fc3ef6: formerly known as Al Alamiya). Files 2360156c, 5db9da66, ca6e2f7c, 8d50dac6, 74f71a5f, 199bffb2 are single monthly statement pages mislabelled 2014|9M, 2014|FY or None."},
]
unread = ["notes (name-change and restatement notes)", "statements of changes in equity", "supplementary insurance-operations / shareholders statements", "21 files not value-read (four scanned interims unopened)",
          "balance-sheet cash versus cash-flow cash differences (cause)", "FY2015 to FY2021 (no file)", "Arabic originals (none in collection)", "segment-note totals versus the primary balance sheet"]
conclusion = ("NOT claimed complete. Six filings value-verified (FY2022 as issued, FY2023, FY2024, FY2025, Q1 2026, H1 2026); IFRS 4 to IFRS 17 and FY2023 cash-flow re-presentation declared with both values; "
              "remaining interims identified by cover only, four scanned interims unopened, FY2021 and earlier absent.")
mkrecord.build(dict(
    symbol="8280", name="LIVA INSURANCE COMPANY (formerly AL ALAMIYA FOR COOPERATIVE INSURANCE COMPANY)", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. Image-only statement pages rendered and read by eye; clean text layers used where identities tie. "
            "tools/check_transcripts.py over transcripts/8280.json checks balance-sheet identity, cash-flow sum and roll, pre-zakat result plus zakat to net result, cross-filing comparatives "
            "(declared differences only) and Q1 + Q2 = H1 rolls for revenue, profit before zakat, zakat and net profit (2026 and 2025); all pass.")))
