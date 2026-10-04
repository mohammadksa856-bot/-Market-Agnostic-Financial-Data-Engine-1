"""Builds raw-B015/8240.json from the page transcripts."""
import mkrecord

U = "full SAR"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


documents = [
    doc("170333be", "FY ended 2025-12-31 audited FS (collector label 2026|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "12-13"}, {"bs": 7, "is": 8, "cf": "11-12"},
        "visual (statement pages are scans with garbled OCR text; rendered and read)"),
    doc("a323e350", "FY ended 2024-12-31 audited FS (label 2025|FY = publication year)", False, {"bs": 8, "is": 9, "cf": "12-13"}, {"bs": 7, "is": 8, "cf": "11-12"},
        "visual (statement pages textless)",
        "FY2024 EPS 0.54 here becomes 0.41 in the FY2025 filing after the bonus issue (300m to 400m capital); both recorded"),
    doc("7e9a7064", "FY ended 2023-12-31 audited FS, first IFRS 17 year, with 2022 and 1 Jan 2022 restated comparatives (label 2024|FY = publication year)", False,
        {"bs": 10, "is": 11, "cf": "14-15"}, {"bs": 10, "is": 11, "cf": "14-15"}, "visual (statement pages textless)"),
    doc("403fab90", "FY ended 2022-12-31 audited FS as originally issued under IFRS 4 (label 2023|FY = publication year; inventory detected 2023-03-31, wrong)", False,
        {"bs": "7-8", "is": "9-10", "cf": "13-14"}, {"bs": "1-2", "is": "3-4", "cf": "7-8"}, "visual (statement pages textless)",
        "IFRS 4 presentation (gross premiums written, net underwriting income, insurance-operations surplus split); restated to IFRS 17 in the FY2023 filing: total assets 894,348,594 to 700,191,701, equity 361,187,055 to 394,802,478, net income attributable 4,697,108 to 12,537,584, CFO 25,709,217 to 25,027,676, CFI -186,833,288 to -186,151,747. Both are declared; neither is substituted."),
    doc("1a8ef8d7", "3M and 6M ended 2026-06-30 reviewed (label 2026|H1 correct)", True, {"bs": 4, "is": 5, "cf": "8-9"}, {"bs": 3, "is": 4, "cf": "7-8"},
        "visual (statement pages textless)",
        "income columns are three-month 2026, three-month 2025, six-month 2026, six-month 2025; cash flow is six-month only"),
    doc("a73e4e47", "3M ended 2026-03-31 reviewed (label 2026|Q1 correct)", True, {"is": 5, "equity": 7, "cf": 8}, {"is": 4, "equity": 6, "cf": 7},
        "visual (statement pages textless); balance sheet page not transcribed"),
]
identified = {
    "f369325d": ("3M and 9M ended 2022-09-30 IFRS 4 interim (cover text)", "not transcribed"),
    "fe5f6972": ("3M and 6M ended 2022-06-30 IFRS 4 interim (cover text)", "not transcribed"),
    "36f584b4": ("3M ended 2022-03-31 IFRS 4 interim (cover text)", "not transcribed"),
    "cb1525f6": ("3M and 9M ended 2023-09-30 interim, first IFRS 17 interim (cover text; class annual_report_with_state is wrong, 95 pages)", "not transcribed; 2022 comparatives in it are IFRS 17 restated"),
    "5f193135": ("3M and 6M ended 2023-06-30 interim (cover text; class annual_report_with_state)", "not transcribed"),
    "58d30ead": ("3M ended 2023-03-31 interim (cover text)", "not transcribed"),
    "ccdfe899": ("3M and 9M ended 2024-09-30 interim (cover text)", "not transcribed"),
    "4b16fb50": ("3M and 6M ended 2024-06-30 interim (cover text)", "not transcribed"),
    "53e7c16c": ("3M ended 2024-03-31 interim (cover text)", "not transcribed"),
    "e0d4bbac": ("3M and 9M ended 2025-09-30 interim (cover text)", "not transcribed"),
    "b0efe08b": ("3M and 6M ended 2025-06-30 interim (cover text)", "not transcribed; 2025 H1 comparatives read in the H1 2026 filing"),
    "1071b090": ("3M ended 2025-03-31 interim (cover text)", "not transcribed; 2025 Q1 comparatives read in the Q1 2026 filing"),
    "eab5328f": ("NOT Chubb Arabia: Chubb Limited (Swiss parent) Swiss statutory financial statements at 2025-12-31, 18 pages, parent-only", "wrong entity filed under 8240 with label 2025|FY; excluded from every Chubb Arabia value"),
    "690c1b57": ("NOT Chubb Arabia: Chubb Limited Company Profile, second quarter 2026, 2 pages", "wrong entity filed under 8240 with label 2026|H1; excluded"),
}
dimensions = {
    "value_correctness": {
        "status": "verified_for_6_filings_declared_restatements_noted",
        "summary": "Headline BS, income and cash-flow values (full SAR) read from rendered pages for FY2025, FY2024, FY2023, FY2022 as issued (IFRS 4), H1 2026 and Q1 2026. All identities hold with zero difference; comparatives agree across filings except declared items. FY2025: insurance revenue 392,965,748, profit before zakat and tax 17,202,029, net profit attributable to shareholders 10,616,871 (FY2024 16,292,651; FY2023 24,817,556), total assets 790,215,871, equity 476,936,779 after a 100,000,000 bonus issue (share capital 300m to 400m), CFO 29,126,656, closing cash 20,896,722. Statements are entity-level (single insurer statement of income with zakat and tax inside); supplementary insurance-operations and shareholders' statements exist in an appendix (FY2025 pdf p109-115) and were not read. Declared differences: (1) IFRS 17 transition: FY2022 original IFRS 4 (net income 4,697,108, total assets 894,348,594, equity 361,187,055, CFO 25,709,217, CFI -186,833,288) versus restated in the FY2023 filing (12,537,584, 700,191,701, 394,802,478, 25,027,676, -186,151,747); 1 Jan 2022 restated equity 385,784,777 versus FY2021 as issued 356,701,634. (2) FY2024 EPS 0.54 versus 0.41 restated. Interim: Q1 2026 + Q2 2026 = H1 2026 for revenue (96,543,724 + 102,822,668 = 199,366,392), profit before zakat and net profit (2,994,880 + 910,706 = 3,905,586); Q1 2025 + Q2 2025 = H1 2025 likewise. Interim cash flow: Q1 2026 CFO 10,086,764 (statement has an interest-on-term-deposit adjustment and no zakat line) versus H1 2026 CFO 11,461,157 (zakat paid -6,615,675 shown): presentations differ, so a Q2 cash flow by subtraction is NOT validated; H1 2026 financing -1,716,226 equals Q1 2026 financing exactly.",
        "not_read": ["notes in every file", "supplementary insurance-operations / shareholders statements (FY2025 pdf p109-115 and equivalents)", "statements of changes in equity (except Q1 2026 p7 glimpsed)", "Q1 2026 balance sheet", "all other interims (listed in files_not_audited_for_values)", "auditor reports"],
    },
    "document_completeness": {
        "status": "primary_statements_present_in_all_six_files_opened_statement_pages_are_scans",
        "summary": "The FY2025, FY2024, FY2023, FY2022, H1 2026 and Q1 2026 filings each carry balance sheet, income statement and cash-flow statement as scanned pages with no (or garbled) text layer although the inventory classes them financial_statements or annual_report_with_state with statement_pages detected from note text, not from the statements; FY2025 text-layer OCR is corrupted (net expense from reinsurance 2024 reads (188,672,162) in the text layer versus (188,679,169) on the page). Two files filed under 8240 are Chubb Limited documents. No FY2021 own FS and no 2021 interims exist in the collection.",
        "defect_ids": ["B015-8240-1", "B015-8240-2", "B015-8240-3", "B015-8240-4"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_and_interims_2022_to_2026_H1_with_gaps_by_page_derived_period",
        "present_in_files_by_page_derived_period": ["FY2022 (label 2023|FY)", "FY2023 (label 2024|FY)", "FY2024 (label 2025|FY)", "FY2025 (label 2026|FY)",
                                                    "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_verified_from_own_pages": ["FY2022 (as issued, IFRS 4)", "FY2023", "FY2024", "FY2025", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (IFRS 4, from FY2022 filing); 1 Jan 2022 restated balance sheet", "FY2022 IFRS 17 restated (FY2023 filing)", "2025 Q1, Q2, H1 (2026 filings)"],
        "values_not_read": ["2022 Q1/H1/9M", "2023 Q1/H1/9M", "2024 Q1/H1/9M", "2025 Q1/H1/9M originals"],
        "missing": ["FY2021 and every earlier year (no file)", "2021 and earlier interims", "2026 9M (not yet due)"],
        "inventory_corrections": "FY labels equal the publication year in all four FS files (2023|FY holds FY2022, 2024|FY FY2023, 2025|FY FY2024, 2026|FY FY2025); the inventory marked 403fab90 as detected 2023-03-31, but its pages are the FY2022 statements. Interim labels match page periods.",
    },
}
defects = [
    {"id": "B015-8240-1", "class": "image_only_or_scanned_statements_flagged_as_present", "severity": "high",
     "evidence": "170333be, a323e350, 7e9a7064, 403fab90, 1a8ef8d7 and a73e4e47: statement pages are scans (textless pages 3-7, 8-13, 10-15, 7-14, 4-9, 3-9); 170333be pages 8-13 carry corrupted OCR text. All were read as images."},
    {"id": "B015-8240-2", "class": "fiscal_year_label_mismatch", "severity": "medium",
     "evidence": "Four annual FS files are labelled with the publication year: 403fab90 FY2022 as 2023|FY, 7e9a7064 FY2023 as 2024|FY, a323e350 FY2024 as 2025|FY, 170333be FY2025 as 2026|FY. A collector reading the label would shift every annual value by one year. Inventory detected 2023-03-31 for 403fab90 (wrong)."},
    {"id": "B015-8240-3", "class": "restated_or_represented_comparatives", "severity": "high",
     "evidence": "IFRS 17 transition: FY2022 and 1 Jan 2022 restated in the FY2023 filing; net income FY2022 4,697,108 (IFRS 4, 403fab90 pdf p10) versus 12,537,584 (7e9a7064 pdf p11); total assets 894,348,594 versus 700,191,701; equity 361,187,055 versus 394,802,478. FY2024 EPS 0.54 versus 0.41 (bonus issue). Both values are declared, none substituted. Series that mix the two bases across 2022/2023 are not comparable."},
    {"id": "B015-8240-4", "class": "wrong_entity_files_in_symbol_bucket", "severity": "medium",
     "evidence": "eab5328f (Chubb Limited Swiss statutory FS, 18 pages, label 2025|FY) and 690c1b57 (Chubb Limited Company Profile Q2 2026, 2 pages, label 2026|H1) are not Chubb Arabia documents; each occupies a period slot that is a false completeness signal."},
]
unread = ["notes in every file", "supplementary insurance-operations and shareholders statements", "statements of changes in equity", "Q1 2026 balance sheet",
          "12 interim filings 2022 Q1 to 2025 9M (identified by cover only)", "FY2021 own statements (no file)", "Arabic originals (none in collection)"]
conclusion = ("NOT claimed complete. Six filings value-verified from rendered pages (FY2022 as issued under IFRS 4, FY2023, FY2024, FY2025, Q1 2026, H1 2026); IFRS 17 restatement of FY2022 declared with both values; "
              "12 interim filings identified by cover but not value-read; FY2021 and earlier absent; two Chubb Limited files wrongly filed under 8240.")
mkrecord.build(dict(
    symbol="8240", name="CHUBB ARABIA COOPERATIVE INSURANCE COMPANY", documents=documents, identified=identified, dimensions=dimensions, defects=defects,
    unread_items=unread, conclusion=conclusion,
    method=("SHA-256 recomputed for every audited file. All six audited filings have scanned statement pages and were rendered and read by eye (balance sheet, income statement, cash flow per filing). "
            "tools/check_transcripts.py over transcripts/8240.json checks balance-sheet identity, cash-flow sum and roll, profit before zakat plus tax to net income, cross-filing comparatives "
            "(declared differences only: IFRS 17 restatement keys, EPS) and Q1 + Q2 = H1 rolls for revenue, profit before zakat and net income (2026 and 2025); all pass.")))
