import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = "notes to the financial statements in every file; statements of changes in equity; auditor reports; segment, related-party and note-level data"
spec = {
    "method": ("SHA-256 recomputed for every audited file (tools/rec.py). All 34 inventory files were opened (cover pages read; Arabic twins identified from cover text; duplicates tested by page text hash or rendered-pixel difference). "
               "Income statement and cash flow pages of 14 English filings were read from the text layer (tools/auto.py, rows rebuilt from word coordinates). Because the balance sheet page is an image in nearly every English file, "
               "the balance sheet of each of those filings was rendered and read by eye (tools/pg.py), as were all statements of the whole-file scans (FY2021 carve-out, FY2022 income statement and cash flow, Q1 2023) and the H1 2022 file whose "
               "balance sheet text layer is scrambled. tools/check_transcripts.py over transcripts/6015.json checks balance sheet identity, cash-flow sum and roll (opening + net change + translation = closing), gross profit, "
               "profit before tax to net profit incl. zakat/KFAS, owners + non-controlling interests, Q1+Q2=H1 and H1+Q3=9M rolls and agreement of every comparative column with the original filing of the same period; all pass with no restatement found."),
    "dimensions": {
        "value_correctness": {
            "status": "verified_for_19_documents_no_restatement_found_currency_USD_thousand",
            "summary": ("Headline values are in US dollars thousand (USD, not SAR): FY2025 revenue 2,508,821, net profit 218,450 (shareholders 219,123, non-controlling interests (673)), total assets 1,734,126, equity 489,974, "
                        "cash from operations 588,997; H1 2026 revenue 1,364,520, net profit 146,983, total assets 1,695,711, cash from operations 360,541; FY2024 revenue 2,196,751, net profit 151,404; FY2023 revenue 2,413,134, net profit 262,331; "
                        "FY2022 revenue 2,378,547, net profit 262,955. All identities hold with zero difference; every comparative agrees with the original filing. Entity and currency verified from the pages: Americana Restaurants International PLC "
                        "(ADGM, auditor PwC then Deloitte), reporting currency USD thousand; FY2021, H1 2022 and 9M 2022 are special-purpose carve-out statements of the restaurant business of Kuwait Food Company (Americana) "
                        "(net parent investment, not share capital; per-share figures not comparable). Cash in the cash flow equals balance sheet cash less bank facilities until Q3 2024 (e.g. Q1 2023 329,483 - 20,212 = 309,271) and equals it from FY2024."),
            "not_read": [NOTES, "BS of the scan bf00d061 (values taken from the annual report 7af927ef text layer instead)", "Arabic twins (not value-read)", "annual report 2023 72104919 (statements not located)"]},
        "document_completeness": {
            "status": "primary_statements_present_in_19_documents_balance_sheet_page_is_an_image_in_most_files",
            "summary": ("English statement files carry all three primary statements, but the balance sheet page is an image-only page (textless) in every filing from H1 2022 to H1 2026 except the FY2022/FY2021 scans, so text-layer extraction of the balance sheet fails "
                        "for 16 English statement files (two of them duplicates) and the inventory's complete/partial counts understate content. Whole-file scans bf00d061, d8c7a726 (FY2022), 16a1bd4e (FY2021 carve-out), 15db7206, 55ee8783 (Q1 2023) hold full statements. "
                        "H1 2022 file 341c2d0e has a scrambled text layer on the BS page. Duplicates and twins: d8c7a726 is a pixel-identical copy of bf00d061 labelled 2023|FY; 9e93f4df is a text-identical copy of 0aa9236f; a115e4b0 near-identical to 9d10f8bf; 55ee8783 a re-scan of 15db7206; "
                        "Arabic twins exist for FY2021, FY2023, 9M/H1 2022, 9M/H1 2023, Q1 2023, Q1 2024, Q1 2025."),
            "defect_ids": ["B012-6015-1", "B012-6015-2", "B012-6015-3", "B012-6015-4", "B012-6015-5"]},
        "company_coverage": {
            "status": "annual_FY2021_to_FY2025_and_interims_2022H1_to_2026H1_except_Q1_2022",
            "present_in_files_by_page_derived_period": ["FY2021 (carve-out)", "FY2022", "FY2023", "FY2024", "FY2025", "2022 H1", "2022 9M", "2023 Q1", "2023 H1", "2023 9M", "2024 Q1", "2024 H1", "2024 9M", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
            "values_known_only_as_comparatives": ["FY2020 (FY2021 carve-out)", "Q1 2022 (Q1 2023 filing)", "H1 2021 and 9M 2021 (2022 filings)"],
            "missing": ["Q1 2022 standalone filing (company IPO in 2022)", "any pre-2019 history (carve-out starts 2019)"],
            "inventory_corrections": ("annual labels are mixed: 2022|FY holds FY2022 and 2023|FY holds FY2023 (d8c7a726 a duplicate of FY2022), but 2025|FY holds FY2024 (publication-year) and 2026|FY holds FY2025; no file is labelled 2024|FY. "
                                      "Files labelled 2021|None and 2022|None have no period in the inventory (Arabic FY2021 and 9M 2022).")}},
    "defects": [
        {"id": "B012-6015-1", "class": "image_only_statement_page_inside_text_files", "severity": "high",
         "evidence": "Balance sheet pdf page is textless in bff40b85 (p5), 3645bab3 (p6), 0aa9236f (p6), 9e93f4df, 7d3cf132 (p11), 9d10f8bf, a115e4b0, 0d1be98d, 94583f06 (p5), e07a74a7 (p11), 8360cdb3, 78139441, 6b7ac28c (p5), 1d753c47 (p9), 926c4878, dd33ea23 (p5); income and cash flow pages are text. An extractor that only reads text finds no balance sheet."},
        {"id": "B012-6015-2", "class": "scrambled_text_layer", "severity": "medium",
         "evidence": "341c2d0e (2022|H1) pdf p5 balance sheet has a garbled text layer (characters unrelated to the page); the rendered page gives total assets 1,140,218."},
        {"id": "B012-6015-3", "class": "duplicates_and_mislabelled_copies", "severity": "medium",
         "evidence": "d8c7a726 (2023|FY) pdf p9, p10, p13 are pixel-identical to bf00d061 (2022|FY): both are the FY2022 statements, so slot 2023|FY has no FY2023 scan content; 9e93f4df text-identical to 0aa9236f (35 of 35 pages); a115e4b0 identical text to 9d10f8bf on 28 of 33 pages; 55ee8783 a re-scan of 15db7206."},
        {"id": "B012-6015-4", "class": "currency_and_reporting_basis", "severity": "high",
         "evidence": "All filings report in US dollars thousand (not SAR). Pre-IPO FY2021, H1 2022 and 9M 2022 are special-purpose carve-out statements of Kuwait Food Company's restaurant business (16a1bd4e pdf p6-10; bff40b85 'condensed interim carve-out'), EPS 0.001 and net parent investment; not comparable with the PLC consolidated statements."},
        {"id": "B012-6015-5", "class": "annual_label_mixed", "severity": "medium",
         "evidence": "e07a74a7 (2025|FY) cover and statements are year ended 31 December 2024; 1d753c47 (2026|FY) is year ended 31 December 2025; 7d3cf132 (2023|FY) is FY2023 and bf00d061 (2022|FY) FY2022 (no publication-year shift in those two); 2024|FY has no file."},
        {"id": "B012-6015-6", "class": "cash_flow_cash_definition", "severity": "low",
         "evidence": "Cash and cash equivalents in the cash flow equals balance sheet cash minus bank facilities: Q1 2023 329,483 - 20,212 = 309,271 (15db7206 pdf p6, p11); FY2023 87,608 - 4,375 = 83,233; equal from FY2024 when bank facilities are nil."},
        {"id": "B012-6015-7", "class": "annual_report_two_up_layout", "severity": "low",
         "evidence": "7af927ef (Annual Report 2022, class annual_report_with_statements) prints statements as two-up spreads (pdf p58 income and OCI side by side); labels in the text layer are merged, so only manual row selection is reliable; values agree with the scan bf00d061."}],
    "unread_items": [NOTES, "equity statements", "Arabic twins (b82eafb7, 753a2058, 8338cb49, 6298092b, 3981ee52, c07247cc, 55cd18c9, 4cf9220c, e01e218e) identified from covers only",
                     "annual report 2023 (72104919) statements", "earnings release e4dad39b", "BS of bf00d061 and d8c7a726 (FY2022 scan) not read", "standalone Q1 2022 filing: absent"],
    "conclusion": ("NOT claimed complete. Nineteen documents value-verified from pages in USD thousand (FY2021 carve-out, FY2022 x2 sources, FY2023, FY2024, FY2025, H1/9M 2022, Q1/H1/9M 2023 to 2025 where present, Q1/H1 2026); "
                   "no restatement found; balance sheets of 14 filings only readable as images; duplicates, Arabic twins and mislabelled copies listed; notes, equity statements and the Q1 2022 standalone filing unread or absent."),
    "identified": {
        "b82eafb7": ["Arabic special-purpose carve-out FS for the years 2021, 2020, 2019 (cover read)", "Arabic twin of 16a1bd4e; not value-read"],
        "753a2058": ["Arabic condensed interim carve-out FS, nine months ended 30 September 2022 (cover read)", "Arabic twin of bff40b85; no period in the inventory"],
        "8338cb49": ["Arabic condensed interim carve-out FS, six months ended 30 June 2022 (cover read)", "Arabic twin of 341c2d0e"],
        "6298092b": ["Arabic interim FS, nine months ended 30 September 2023 (cover read)", "Arabic twin of 3645bab3"],
        "3981ee52": ["Arabic consolidated FS, year ended 31 December 2023 (cover read, digits reversed in text layer)", "Arabic twin of 7d3cf132"],
        "72104919": ["Annual Report 2023 (cover read)", "inventory says annual_report_with_statements; statement pages not located by the row search; not value-read"],
        "d8c7a726": ["FY2022 consolidated FS, whole-file scan (cover thumbnails and pdf p9, p10, p13 pixel-identical to bf00d061)", "duplicate of bf00d061 labelled 2023|FY"],
        "55ee8783": ["Q1 2023 interim, whole-file scan (thumbnails; pdf p6, p7, p11 near-identical to 15db7206)", "re-scan of 15db7206; not separately read"],
        "e01e218e": ["Arabic Q1 2023 interim, whole-file scan (thumbnails)", "Arabic twin of 15db7206"],
        "9e93f4df": ["H1 2023 interim (cover and page text identical to 0aa9236f, 35 of 35 pages)", "duplicate copy, smaller file"],
        "a115e4b0": ["Q1 2024 interim (page text identical to 9d10f8bf on 28 of 33 pages)", "near-duplicate; BS image page not separately read"],
        "55cd18c9": ["Arabic Q1 2024 interim (cover read)", "Arabic twin of 9d10f8bf"],
        "4cf9220c": ["Arabic Q1 2025 interim (cover read)", "Arabic twin of 8360cdb3; class partial_statements because of the Arabic text layer"],
        "e4dad39b": ["H1 2026 earnings release, 4 pages (cover read)", "results announcement; not a statements file"],
    },
}
(HERE / "spec_6015.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf8")
