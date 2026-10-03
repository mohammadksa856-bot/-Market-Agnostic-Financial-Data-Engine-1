"""Regression tests from the independent Saudi audit (batch1-B, Alinma 1150).

Proven from the archived source PDFs:
* a subtitle ("FOR THE NINE MONTHS PERIOD ENDED ...") pushes the period headings below
  the old fixed y=155 band, so the three-month column was published as year-to-date;
* "Income from investments and financing, net" (the NET line) was mapped to the gross
  ``financing_income`` metric, and a caption wrapped over two rows read the gross line.
"""
from pathlib import Path

import pytest

from finengine.reading import StatementReader

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data" / "raw" / "SA" / "1150" / "documents"
Q3_2018 = DOCS / "8eae5c4221d8d630cf02132020d89b659a654e2448c9a7ed7a40703e45b48306.pdf"
Q2_2019 = DOCS / "ae1cabb24272054a057459ed9bd8e383204a6b9036bb762cd7a5881aa2a95c11.pdf"
FY_2019 = DOCS / "13a6ea5f65a40a19de042300a7eccea6d2c83c4eb14b0c61955685258ed1fef3.pdf"


def _read(pdf, period_end, year, filing_type):
    if not pdf.is_file():
        pytest.skip("archived source document not present")
    manifest = StatementReader(pdf, enable_ocr=False).read(
        "SA", "1150", "SAR", "https://example.invalid/x.pdf", "2026-01-01",
        period_end=period_end, fiscal_year=year, filing_type=filing_type, profile="bank")
    return {(f["metric"], f["period_kind"]): f["value"] for f in manifest["facts"]}


def test_nine_month_subtitle_does_not_turn_quarter_into_ytd():
    facts = _read(Q3_2018, "2018-09-30", 2018, "interim-report")
    # page 4: three months 1,211,698 / nine months 3,552,462; net income 653,266 / 1,856,403
    assert facts[("total_operating_income", "quarter")] == "1211698"
    assert facts[("total_operating_income", "ytd")] == "3552462"
    assert facts[("net_income", "quarter")] == "653266"
    assert facts[("net_income", "ytd")] == "1856403"


def test_net_special_income_is_not_published_as_gross_and_wrapped_caption_is_joined():
    q2 = _read(Q2_2019, "2019-06-30", 2019, "interim-report")
    # page 4: gross 1,378,495 / 2,685,608; net (caption wrapped over two rows) 1,079,559 / 2,072,658
    assert q2[("financing_income", "quarter")] == "1378495"
    assert q2[("net_financing_income", "quarter")] == "1079559"
    assert q2[("net_financing_income", "ytd")] == "2072658"
    fy = _read(FY_2019, "2019-12-31", 2019, "financial-statements")
    # page 9: gross 5,608,762; return on time investments (1,214,303); net 4,394,459
    assert fy[("financing_income", "fy")] == "5608762"
    assert fy[("financing_expense", "fy")] == "-1214303"
    assert fy[("net_financing_income", "fy")] == "4394459"
