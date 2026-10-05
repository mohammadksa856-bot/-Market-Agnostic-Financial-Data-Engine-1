"""Builds raw-B019/1320.json (audit record) from the page transcripts."""
import mkrecord

U = "full SAR"
IS = "is"


def doc(sha, period, ok, pdf, printed, reading, note=None):
    d = dict(sha256=sha, actual_period=period, label_ok=ok, pdf_pages=pdf, printed_pages=printed, units=U, reading=reading)
    if note:
        d["note"] = note
    return d


VIS = "visual (statement pages textless, rendered and read)"
TXT = "text layer (clean)"
P3 = {"bs": 7, IS: 8, "cf": 10}
PR3 = {"bs": 6, IS: 7, "cf": 9}
P2 = {"bs": 4, IS: 5, "cf": 7}
PR2 = {"bs": 3, IS: 4, "cf": 6}
documents = [
    doc("9212474e", "FY ended 2025-12-31 consolidated FS, label 2026|FY = publication year", False, P3, PR3, VIS),
    doc("2ab11293", "FY ended 2024-12-31 consolidated FS as issued, label 2025|FY = publication year; inventory class partial_statements", False, P3, PR3, VIS),
    doc("2b713687", "FY ended 2023-12-31 consolidated FS as issued, label 2024|FY = publication year", False, P3, PR3, VIS),
    doc("c2f44602", "FY ended 2022-12-31 consolidated FS as issued, label 2023|FY = publication year", False, P3, PR3, VIS),
    doc("172e57b9", "3M and 6M ended 2026-06-30; inventory class partial_statements", True, P2, {"bs": 3, IS: 4, "cf": 6}, VIS, "equity statement and review report not read"),
    doc("6e69c9ed", "3M ended 2026-03-31", True, P2, PR2, TXT, "pdf p3 (review report) and p6 (equity) textless, not viewed"),
    doc("46818338", "3M and 9M ended 2025-09-30", True, P2, PR2, TXT, "pdf p3 and p6 textless, not viewed"),
    doc("0d449916", "3M and 6M ended 2025-06-30", True, P2, PR2, TXT, "pdf p3 textless (review report), not viewed"),
    doc("0f77c38c", "3M ended 2025-03-31", True, P2, PR2, TXT, "pdf p3 and p6 textless, not viewed"),
]

AR = "Arabic file, cover image viewed; period from cover; statements not read"
T = "cover text; not transcribed"
PR = "earnings press release (about 3-4 pages); no statements; not transcribed"
identified = {
    # files without a collector fiscal year, periods from cover images
    "17aa6e8f": ("9M ended 2022-09-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "5dbc4496": ("9M ended 2020-09-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "71498607": ("9M ended 2018-09-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "9dc61859": ("9M ended 2025-09-30 (Arabic twin of 46818338, cover image)", AR + "; label fiscal_year None"),
    "e08bd278": ("9M ended 2019-09-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "e54bbb8b": ("9M ended 2021-09-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "f2486ecd": ("9M ended 2023-09-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "1c9b90ec": ("FY ended 2015-12-31 consolidated FS (Arabic, cover image)", AR + "; label fiscal_year None, slot FY"),
    "20e54ea8": ("6M ended 2023-06-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "28c09114": ("6M ended 2019-06-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "28edc4ab": ("6M ended 2018-06-30 (Arabic, cover image; whole file image-only)", AR + "; label fiscal_year None"),
    "8b0c0410": ("6M ended 2022-06-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "9c099506": ("6M ended 2021-06-30 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "a04e6466": ("6M ended 2020-06-30 (Arabic, cover image; whole-file scan)", AR + "; label fiscal_year None"),
    "cfec7bf8": ("6M ended 2025-06-30 (Arabic twin of 0d449916, cover image)", AR + "; label fiscal_year None"),
    "1050205d": ("3M ended 2019-03-31 (Arabic, cover image; whole-file image-only)", AR + "; label fiscal_year None"),
    "14b5e4b7": ("FY ended 2023-12-31 consolidated FS (Arabic twin of 2b713687, 54 pages, cover image)", AR + "; labelled Q1 with fiscal_year None although it is an annual file"),
    "299a3e32": ("3M ended 2023-03-31 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "3dd36023": ("3M ended 2018-03-31 (Arabic, cover image; whole-file scan)", AR + "; label fiscal_year None"),
    "517a46e3": ("FY ended 2024-12-31 consolidated FS (Arabic twin of 2ab11293, 51 pages, cover image)", AR + "; labelled Q1 with fiscal_year None although it is an annual file"),
    "878cc4a9": ("3M ended 2020-03-31 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "bf9eb02d": ("3M and year ended 2018-12-31 (Arabic cover image: three months and the year)", AR + "; labelled Q1 with fiscal_year None although the period is Q4/FY2018"),
    "d86b768c": ("3M ended 2025-03-31 (Arabic twin of 0f77c38c, cover image)", AR + "; label fiscal_year None"),
    "ddf44d1a": ("3M ended 2021-03-31 (Arabic, cover image)", AR + "; label fiscal_year None"),
    "b543c81b": ("FY ended 2025-12-31 consolidated FS (Arabic twin of 9212474e, 50 pages, cover image)", AR + "; label 2025|FY is the publication year of FY2024 elsewhere but this file is FY2025"),
    # 2015-2017 files with a collector year
    "0114753a": ("9M 2015 (Arabic cover text)", T), "650d5591": ("H1 2015 (label only; text layer garbled)", "period unverified"),
    "0c66b726": ("Q1 2015 (Arabic cover text)", T), "88d5e588": ("Q1 2015 label; whole-file scan", "period unverified"),
    "821ce3af": ("9M 2016 label; text layer garbled", "period unverified"), "4d5c7ebe": ("FY2016 label; textless 30 pages", "period unverified"),
    "5898bcd5": ("H1 2016 label; textless", "period unverified"), "669149d8": ("Q1 2016 (Arabic cover text)", T),
    "85972ce0": ("Q1 2016 label; textless", "period unverified"), "82239b4f": ("9M 2017 (Arabic cover text)", T),
    "1f0ec15c": ("H1 2017 (Arabic cover text; whole file image-only)", T), "4fff2b09": ("Q1 2017 (Arabic cover text)", T),
    # press releases
    "bf30f633": ("3Q 2021 results highlights (cover text)", PR), "5229043e": ("4Q/FY2021 results highlights (cover text)", PR),
    "248e9631": ("2Q 2021 results highlights (cover text)", PR), "81954d82": ("1Q 2021 results (cover text)", PR),
    "061cecb0": ("3Q 2022 results highlights (cover text)", PR),
    "8acac6e9": ("FY2022 results highlights (cover text)", PR + "; label 2022|FY is the fiscal year, unlike FS files where FY labels are publication years"),
    "7492e0dc": ("2Q 2022 results highlights (title 2Q2022; text dateline says 2Q 2021)", PR + "; internal date inconsistency"),
    "b96d8b17": ("1Q 2022 results highlights (cover text)", PR),
    "fbeeacfc": ("3Q 2023 results highlights (cover text)", PR),
    "0fa49c79": ("FY2023 results highlights (cover text)", PR + "; label 2023|FY is the fiscal year"),
    "0dc0ba6f": ("2Q 2023 results highlights (cover text)", PR), "b61f2969": ("1Q 2023 results highlights (cover text)", PR),
    "bf53ce32": ("3Q 2024 results highlights (title 3Q 2024; dateline says Q3 2023)", PR + "; internal date inconsistency"),
    "1cea0bf1": ("FY2024 results highlights (cover text)", PR + "; label 2024|FY is the fiscal year"),
    "3aa4f9d5": ("2Q 2024 results highlights (cover text)", PR), "920a3c73": ("1Q 2024 results highlights (cover text)", PR),
    "17de48b9": ("3Q 2025 results highlights (cover text)", PR),
    "3db0bccd": ("FY2025 results highlights (cover text)", PR + "; label 2025|FY is the fiscal year"),
    "2b78f983": ("2Q 2025 results highlights (cover text)", PR), "4115181a": ("1Q 2025 results highlights (cover text)", PR),
    "825b3965": ("2Q 2026 results highlights (cover text)", PR), "37e7acd1": ("1Q 2026 results highlights (cover text)", PR),
    # English interim FS not read
    "3fa5fcbe": ("3M and 9M ended 2022-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "cf4b96b4": ("3M and 6M ended 2022-06-30 (cover text)", "statement pages pdf p3-7 textless; not transcribed"),
    "5f2817f0": ("3M ended 2022-03-31 (Arabic cover text)", "Arabic twin of a4f17b2c; not transcribed"),
    "a4f17b2c": ("3M ended 2022-03-31 (cover text)", "statement pages pdf p4-7 textless; not transcribed"),
    "794897dd": ("3M and 9M ended 2023-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "e595bb4d": ("3M and 6M ended 2023-06-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "6c48d2f7": ("3M ended 2023-03-31 (cover text)", "classed other_no_statements_found; not transcribed"),
    "d41d86ee": ("3M and 9M ended 2024-09-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "30d6743d": ("3M and 6M ended 2024-06-30 (cover text)", "classed other_no_statements_found; not transcribed"),
    "d5d179db": ("3M ended 2024-03-31 (cover text)", "classed other_no_statements_found; not transcribed; Q1 2024 known as comparatives in the Q1 2025 filing"),
}

method = ("SHA-256 recomputed for every audited file. The four annual statements and the H1 2026 interim have image-only statement pages (pdf p3-10) and were rendered and read by eye; the other four interims have clean text layers. "
          "Cover images of 25 files with no collector fiscal year (mostly Arabic, scrambled fonts or image-only) were viewed to derive their periods. "
          "tools/check_transcripts.py over transcripts/1320.json checks BS identity, cash-flow sum and roll, gross profit, profit before zakat less zakat plus discontinued to net profit, owners plus NCI, cross-filing agreement of comparatives and Q1+Q2=H1 / H1+Q3=9M rolls (revenue, cost of revenue, net profit); all pass.")

dimensions = {
    "value_correctness": {
        "status": "verified_for_9_filings_with_declared_reclassifications",
        "summary": ("Headline BS, income and cash-flow values (full SAR) read from pages for FY2022-FY2025, 3M 2025, 6M 2025, 9M 2025, 3M 2026 and 6M 2026; identities hold with zero difference. "
                    "FY2025: revenue 1,412,253,836, net profit 263,103,171 (shareholders 191,533,818, NCI 71,569,353), total assets 1,729,374,069, equity 1,164,542,645, CFO 357,224,921, cash 234,242,912; profit before zakat includes a one-off lands settlement compensation of 53,632,986 and CFI includes lands settlement proceeds 211,482,986; dividends paid 199,642,128. "
                    "FY2024: revenue 1,630,189,005, net profit 250,305,230, CFO 36,550,739. FY2023: revenue 1,334,708,124, net profit 217,261,410, CFO 315,357,590 (consolidation of a subsidiary with NCI from 2023; gain on bargain purchase 40,330,649). FY2022: revenue 747,622,847, net profit 54,205,644; FY2021 revenue 373,484,610 and net profit 931,645 (with discontinued operations 18,920,315) known from the FY2022 filing. "
                    "H1 2026: revenue 691,565,046, net profit 115,883,178 (Q1 77,860,939 + Q2 38,022,239 rolls exactly). "
                    "Declared differences, never substituted: (1) FY2024 re-presented in the FY2025 filing: cost of revenue -1,230,602,002 vs -1,231,354,078 as issued, gross profit 399,587,003 vs 398,834,927, operating income 309,193,318 vs 307,269,318 (finance charges and administrative expenses moved; profit before zakat 265,514,899 and net profit unchanged). "
                    "(2) 2025 interim comparatives re-presented in the 2026 filings in the same way: Q1 2025 cost -344,959,737 as issued vs -344,757,500; 6M 2025 cost -602,030,259 vs -601,625,785, gross profit 188,293,171 vs 188,697,645, operating income 131,691,665 vs 132,724,329; Q2 2025 cost -257,070,522 vs -256,868,285. Pre-tax and net profit unchanged. "
                    "(3) Interim cash flow: 9M 2025 CFO 161,219,962 is lower than 6M 2025 CFO 227,135,917 (and zakat paid 9,404,300 for 9M vs 10,553,397 for 6M), so a Q3 CFO by subtraction (-65,915,955) is NOT validated; Q1 2026 CFO 20,028,338 vs 6M 2026 CFO 235,741,141 also not validated by subtraction. "
                    "Income-statement quarters do roll: Q1 + Q2 = 6M and 6M + Q3 = 9M for revenue, cost of revenue and net profit as issued."),
        "not_read": [
            "notes in every file (going concern, restatement, related-party, borrowings, lands settlement note 16/30)",
            "statements of changes in equity",
            "auditor and review report pages (pdf p3-6)",
            "all 2022-2024 interim filings (English and Arabic), 2015-2021 interims and annual FS, FY2015 FS",
            "Arabic twins of FY2023, FY2024, FY2025 and the 2025 interims (income, balance sheet and cash flow)",
            "all earnings press releases",
        ],
    },
    "document_completeness": {
        "status": "annual_FY2022_to_FY2025_and_interims_2025Q1_to_2026H1_read; remaining files identified by cover only",
        "summary": ("The inventory understates content and mis-dates files. 24 of the 78 files carry no collector fiscal year (period_slot only); their covers show they are 2018-2025 Arabic FS of mixed periods, and three annual-period files are labelled Q1 (14b5e4b7 FY2023, 517a46e3 FY2024, bf9eb02d three months and year to 2018-12-31); 1c9b90ec is FY2015 with no year. "
                    "The FY2022-FY2025 English annual FS (classed financial_statements/partial_statements) have image-only statement pages and carry complete BS, income and cash-flow statements. FS FY labels are publication years (2023|FY = FY2022, 2024|FY = FY2023, 2025|FY = FY2024, 2026|FY = FY2025) whereas the press-release FY labels (2022|FY, 2023|FY, 2024|FY, 2025|FY) are fiscal years, so the same label denotes different years. "
                    "Several files exist as English and Arabic twins (FY2023-FY2025, Q1/H1/9M 2025, Q1 2022, 2023 interims). Unit is full SAR; the currency symbol is the new riyal glyph in 2025-2026 files. Two press releases carry inconsistent internal dates (7492e0dc, bf53ce32)."),
        "defect_ids": ["B019-1320-1", "B019-1320-2", "B019-1320-3"],
    },
    "company_coverage": {
        "status": "annual_FY2022_to_FY2025_present_with_statements; interims by cover; earlier years partial",
        "present_in_files_by_page_derived_period": [
            "FY2015 (Arabic FS), FY2018 incl. Q4 (Arabic, cover only), FY2022, FY2023 (English and Arabic), FY2024 (English and Arabic), FY2025 (English and Arabic)",
            "3M: 2015, 2016, 2017 (cover text), 2018-2023 and 2025 (cover), 2024 (English cover), 2026",
            "6M: 2017-2025 (covers), 2026; 2015 and 2016 H1 files exist by label only (period unverified)",
            "9M: 2015, 2017-2025 (covers); 2016 9M by label only (unverified)",
            "press releases 2021 to 2026 (all quarters/FY where present)",
        ],
        "values_verified_from_own_pages": ["FY2022", "FY2023", "FY2024", "FY2025", "2025 Q1", "2025 H1", "2025 9M", "2026 Q1", "2026 H1"],
        "values_known_only_as_comparatives": ["FY2021 (FY2022 filing)", "2024 Q1, 6M, Q2, 9M, Q3 (2025 filings)"],
        "values_not_read": ["FY2015 to FY2021 own FS", "all 2015-2024 interim filings", "FY2018 file", "press releases"],
        "missing": ["FY2016, FY2017, FY2019, FY2020, FY2021 annual FS files (only FY2015 and FY2018-labelled files exist)", "2016 and 2017 9M/H1 identification unverified (garbled labels)", "2024 Q1/H1/9M English files present but not read"],
        "inventory_corrections": "Collector labels are unreliable for this company (25 files without year, annual files labelled Q1, FS FY = publication year, press-release FY = fiscal year); coverage must be taken from page-derived periods.",
    },
}

defects = [
    {"id": "B019-1320-1", "kind": "label_missing_or_wrong", "detail": "24 files have fiscal_year None; four annual FS carry slot Q1 (14b5e4b7, 517a46e3, bf9eb02d) or FY with ambiguous year (b543c81b). Periods recovered from cover images are listed per file."},
    {"id": "B019-1320-2", "kind": "label_semantics", "detail": "FS FY labels are publication years; press-release FY labels are fiscal years. Two press releases (7492e0dc, bf53ce32) have internally inconsistent dates."},
    {"id": "B019-1320-3", "kind": "reclassifications", "detail": "FY2024 and 2025 interim comparatives re-presented in later filings (cost of revenue, gross profit, operating income); declared in the transcript; no value substituted. Interim cash-flow quarter by subtraction not validated (9M CFO below 6M CFO)."},
]

unread = [
    "notes to the financial statements in every file",
    "statements of changes in equity; auditor and review reports",
    "2022, 2023, 2024 English and Arabic interim filings (Q1, H1, 9M each year); 2015-2021 interims and FS",
    "Arabic twins of FY2023, FY2024, FY2025 and 2025 interims: statements not compared",
    "files with unverified periods: 650d5591, 88d5e588, 821ce3af, 4d5c7ebe, 5898bcd5, 85972ce0",
    "all 22 earnings press releases",
]

spec = dict(
    symbol="1320",
    name="SSP (Saudi Steel Pipes Company)",
    method=method,
    documents=documents,
    identified=identified,
    dimensions=dimensions,
    defects=defects,
    unread_items=unread,
    conclusion="Company is NOT claimed complete: annual FY2022-FY2025 and five interims were read; 2015-2024 interims, FY2015-FY2021 FS, Arabic twins, notes and press releases are unread, and several collector labels are wrong.",
)
if __name__ == "__main__":
    mkrecord.build(spec)
