import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = "notes to the financial statements in every file; statements of changes in equity; auditor reports; biological-asset and segment notes"
spec = {
    "method": ("SHA-256 recomputed for every audited file (tools/rec.py). All 18 inventory files were opened and identified from the first pages (tools/survey.py). Ten statement files with a text layer were read with tools/auto.py "
               "(rows rebuilt from word coordinates); seven interim files whose statement pages are image-only (textless pdf p3-7) were rendered and read by eye (tools/pg.py); the FY2025 filing's text layer drops parentheses and splits numbers, so its balance sheet "
               "and cash flow (the cash flow page is image-only) were read from the rendered pages, and the H1 2024 cash flow was re-read from the render. tools/check_transcripts.py over transcripts/6070.json checks balance sheet identity, cash-flow sum and roll, gross profit, "
               "profit before zakat to net profit, Q1+Q2=H1 and H1+Q3=9M rolls and agreement of every comparative column with the original filing of the same period; the differences found are declared restatements."),
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_18_filings_with_4_declared_cash_flow_representations_and_1_ppe_reclassification",
            "summary": ("Headline values in full Saudi riyals (SAR). FY2025: sales 712,226,774, net profit 81,263,378, total assets 1,299,524,036, equity 798,978,519, cash from operations 75,924,479; FY2024: sales 582,788,144, net profit 75,300,454, cash from operations 121,337,652 as filed "
                        "(125,498,486 in the FY2025 comparative); FY2023: sales 426,435,301, net profit 61,968,851; FY2022: sales 341,996,642, net profit 51,065,262; H1 2026: sales 323,259,854, net profit 11,533,358, total assets 1,449,246,861; Q1 2026 profit 2,054,827 "
                        "against 34,657,037 in Q1 2025. All identities hold with zero difference. Declared re-presentations (both versions recorded, none substituted): cash flows of 9M 2022 (operating +174,543 / investing +77,535 / financing -252,078), FY2022 (investing and financing 2,114,159), "
                        "Q1 2024 (727,471), 9M 2024 (2,077,498), FY2024 (4,160,834); December 2023 PPE 595,976,357 became 760,482,059 when projects under construction 164,505,702 were merged; December 2021 PPE 489,100,879 + work under progress 17,932,422 = 507,033,301."),
            "not_read": [NOTES, "FY2021 and earlier originals (absent)", "annual/other documents: none in the file set"]},
        "document_completeness": {
            "status": "primary_statements_present_in_all_18_files_seven_files_image_only_and_five_misclassified_as_no_statements",
            "summary": ("All 18 files carry the three primary statements plus changes in equity. Five interim files (2022|Q1, 2024|Q1, 2025|H1, 2025|9M, 2026|Q1) are classed other_no_statements_found by the inventory because pdf p3-7 are image-only, yet hold complete statements; two more "
                        "(2022|9M, 2022|H1) are classed financial_statements but are also image-only. The FY2025 filing e03814b8 has an image-only cash flow page (pdf p9) and a text layer that loses parentheses; H1 2024 1350aa90 splits numbers in its cash flow page. "
                        "No duplicates or Arabic twins in this file set."),
            "defect_ids": ["B012-6070-1", "B012-6070-2", "B012-6070-3", "B012-6070-4"]},
        "company_coverage": {
            "status": "annual_FY2022_to_FY2025_and_every_interim_2022Q1_to_2026H1",
            "present_in_files_by_page_derived_period": ["FY2022", "FY2023", "FY2024", "FY2025", "2022 Q1", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            "values_known_only_as_comparatives": ["FY2021 balance sheet (Dec 2021 columns), FY2021 Q1/H1/9M income and cash flow (2022 filings)", "FY2021 annual income statement and cash flow: not read anywhere"],
            "missing": ["FY2021 and earlier standalone filings (inventory expects 55 periods back to 2011 but only 2022 onward was collected)"],
            "inventory_corrections": "annual labels are publication-year (2023|FY = FY2022 ... 2026|FY = FY2025); interim labels equal the interim year."}},
    "defects": [
        {"id": "B012-6070-1", "class": "annual_label_is_publication_year", "severity": "medium",
         "evidence": "d0639dfe (2023|FY) is the year ended 31 December 2022 (pdf p9-13), 0ec0360d (2024|FY) FY2023, 7be75050 (2025|FY) FY2024, e03814b8 (2026|FY) FY2025."},
        {"id": "B012-6070-2", "class": "image_only_statement_pages_flagged_no_statements", "severity": "high",
         "evidence": "42c7f999 (2022|Q1), 749a7b61 (2024|Q1), 86afc4e9 (2025|H1), 68065002 (2025|9M), 035209e7 (2026|Q1): class other_no_statements_found but pdf p4 (BS), p5 (IS), p7 (CF) are complete rendered statements; 87041a34 (2022|9M) and ec79b9c8 (2022|H1) classed financial_statements are image-only likewise."},
        {"id": "B012-6070-3", "class": "text_layer_loses_parentheses_and_splits_numbers", "severity": "high",
         "evidence": "e03814b8 text layer: total liabilities extracted as 84 and 4, prior cost of sales 406,064,506 and prior zakat 5,000,000 unsigned; 1350aa90 cash flow shows '41,919,12' '7' and unsigned 88,855,317 (investing is an outflow). Text-only extraction yields wrong signs or values; the rendered pages are correct (e03814b8 pdf p6, p7, p9; 1350aa90 pdf p7)."},
        {"id": "B012-6070-4", "class": "restated_or_represented_comparatives", "severity": "medium",
         "evidence": "Cash flow re-presentations: 9M 2022 (87041a34 -> ee2719d5), FY2022 (d0639dfe -> 0ec0360d, 2,114,159 between investing and financing), Q1 2024 (749a7b61 -> 54e4ecb1, 727,471), 9M 2024 (e6f8f4d8 -> 68065002, 2,077,498), FY2024 (7be75050 -> e03814b8, 4,160,834 between operating and financing); PPE presentation: Dec 2023 595,976,357 -> 760,482,059 and Dec 2021 489,100,879 vs 507,033,301."},
        {"id": "B012-6070-5", "class": "cash_flow_sign_of_operating_cash_in_q1_2026", "severity": "low",
         "evidence": "035209e7 pdf p7: Q1 2026 cash from operations is negative (8,531,713) after a working-capital outflow (inventory (55,162,222), biological assets (60,395,741)); not an extraction error."}],
    "unread_items": [NOTES, "equity statements", "FY2021 and earlier standalone filings: absent from the file set", "FY2021 annual income statement and cash flow"],
    "conclusion": ("NOT claimed complete. All 18 collected files value-verified from pages (FY2022 to FY2025 annual, every interim 2022 Q1 to 2026 H1); "
                   "5 cash-flow re-presentations and a PPE reclassification declared; seven files are image-only and five are misclassified as having no statements; "
                   "notes and equity statements unread; FY2021 and earlier absent."),
    "identified": {},
}
(HERE / "spec_6070.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
