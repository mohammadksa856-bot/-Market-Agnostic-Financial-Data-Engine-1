"""Layouts behind the known data regressions this branch closes.

Each fixture reproduces the shape of a real filing:

* Riyad Bank prints gross fee income, fee expense and the net subtotal as three
  separate lines, all beginning "Fee and commission income"; the net subtotal
  must not be published as gross fee income.
* SABIC prints its consolidated statement of cash flows across two pages, the
  second headed "(continued)", so neither page carries the whole signature.
* SABIC's consolidated statement of income puts the profit-attribution rows in
  a second panel that carries no heading of its own.
"""
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False

_X = (430, 520)


def _put_rows(page, rows, start=150, step=18, label_x=40):
    y = start
    for label, values in rows:
        page.insert_text((label_x, y), label, fontsize=9)
        for x, value in zip(_X, values):
            page.insert_text((x, y), value, fontsize=9)
        y += step
    return y


def _bank_fee_pdf(path):
    """A bank income statement carrying gross, expense and net fee lines."""
    document = pymupdf.open()
    page = document.new_page(width=640, height=842)
    page.insert_text((40, 50), "Consolidated statement of income", fontsize=12)
    page.insert_text((350, 90), "For the three months ended", fontsize=7)
    for x, year in zip(_X, ("2020", "2019")):
        page.insert_text((x, 110), year, fontsize=9)
    _put_rows(page, [
        ("Special commission income", ("2,000,000", "1,900,000")),
        ("Net special commission income", ("1,200,000", "1,150,000")),
        ("Fee and commission income", ("481,519", "455,000")),
        ("Fee and commission expense", ("(158,779)", "(150,000)")),
        ("Fee and commission income, net", ("322,740", "305,000")),
        ("Total operating income", ("1,800,000", "1,700,000")),
        ("Net income for the period", ("900,000", "850,000")),
    ])
    document.save(path)
    document.close()


def _split_cash_flow_pdf(path, second_heading="Consolidated statement of cash flows (continued)"):
    """A cash-flow statement whose sections are split over two pages."""
    document = pymupdf.open()
    first = document.new_page(width=640, height=842)
    first.insert_text((40, 50), "Consolidated statement of cash flows", fontsize=12)
    for x, year in zip(_X, ("2025", "2024")):
        first.insert_text((x, 110), year, fontsize=9)
    _put_rows(first, [
        ("Operating activities", ("", "")),
        ("Income before zakat and income tax", ("3,000,000", "2,800,000")),
        ("Depreciation and amortisation", ("500,000", "480,000")),
        ("Zakat and income tax paid", ("(2,043,686)", "(1,900,000)")),
        ("Net cash from operating activities", ("15,958,999", "14,000,000")),
    ])
    second = document.new_page(width=640, height=842)
    second.insert_text((40, 50), second_heading, fontsize=12)
    for x, year in zip(_X, ("2025", "2024")):
        second.insert_text((x, 110), year, fontsize=9)
    # The continuation page carries a full column of its own, as the issuer's
    # does; a page with only a line or two is not a statement page.
    _put_rows(second, [
        ("Investing activities", ("", "")),
        ("Purchase of property, plant and equipment", ("(8,750,028)", "(8,000,000)")),
        ("Proceeds from sale of property, plant and equipment", ("82,308", "75,000")),
        ("Purchase of investments", ("(1,200,000)", "(1,100,000)")),
        ("Net cash used in investing activities", ("(7,717,198)", "(7,000,000)")),
        ("Financing activities", ("", "")),
        ("Proceeds from debt", ("18,495,107", "17,000,000")),
        ("Repayment of debt", ("(15,288,056)", "(14,000,000)")),
        ("Dividends paid to shareholders", ("(9,625,654)", "(9,000,000)")),
        ("Lease payments", ("(1,102,688)", "(1,000,000)")),
        ("Net cash used in financing activities", ("(10,873,712)", "(10,000,000)")),
        ("Cash and cash equivalents at the beginning of the year",
         ("30,536,409", "33,000,000")),
        ("Cash and cash equivalents at the end of the year", ("27,950,605", "30,536,409")),
    ])
    document.save(path)
    document.close()


def _two_panel_income_pdf(path, right_panel_heading=None):
    """One income statement heading printed across two panels."""
    document = pymupdf.open()
    page = document.new_page(width=960, height=842)
    page.insert_text((40, 50), "Consolidated statement of income", fontsize=12)
    for x, year in zip((330, 392), ("2025", "2024")):
        page.insert_text((x, 110), year, fontsize=9)
    for x, year in zip((731, 793), ("2025", "2024")):
        page.insert_text((x, 110), year, fontsize=9)
    y = 150
    for label, values in [("Revenue", ("100,000", "90,000")),
                          ("Gross profit", ("40,000", "36,000")),
                          ("Net income", ("20,000", "18,000"))]:
        page.insert_text((40, y), label, fontsize=9)
        for x, value in zip((330, 392), values):
            page.insert_text((x, y), value, fontsize=9)
        y += 18
    if right_panel_heading:
        page.insert_text((520, 70), right_panel_heading, fontsize=10)
    y = 150
    for label, values in [("Net income attributable to:", ("", "")),
                          ("Equity holders of the Parent", ("19,000", "17,000")),
                          ("Non-controlling interests", ("1,000", "1,000"))]:
        page.insert_text((520, y), label, fontsize=9)
        for x, value in zip((731, 793), values):
            page.insert_text((x, y), value, fontsize=9)
        y += 18
    document.save(path)
    document.close()


def _read(pdf, **kwargs):
    from finengine.reading import StatementReader

    options = {"market": "SA", "symbol": "1010", "currency": "SAR",
               "source_url": "https://issuer.example/fs.pdf", "filed_at": "2026-01-31",
               "period_end": "2020-06-30", "fiscal_year": 2020,
               "filing_type": "interim-report", "profile": "bank"}
    options.update(kwargs)
    return StatementReader(pdf, enable_ocr=False).read(**options)


@unittest.skipUnless(HAVE_PYMUPDF, "the reader needs the optional pymupdf extra")
class BankFeeLineTests(unittest.TestCase):
    def test_net_fee_subtotal_is_not_published_as_gross_fee_income(self):
        # Riyad Bank's own Q2-2020 figures: gross 481,519, expense 158,779,
        # net 322,740. The three lines share the same opening words.
        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "bank.pdf"
            _bank_fee_pdf(pdf)
            manifest = _read(pdf)
        values = {f["metric"]: f["value"] for f in manifest["facts"]}
        self.assertEqual(values.get("fee_income"), "481519")
        self.assertEqual(values.get("net_fee_income"), "322740")
        self.assertEqual(values.get("fee_expense"), "-158779")
        self.assertNotEqual(values.get("fee_income"), "322740",
                            "the net subtotal must never be published as gross fee income")


@unittest.skipUnless(HAVE_PYMUPDF, "the reader needs the optional pymupdf extra")
class SplitCashFlowStatementTests(unittest.TestCase):
    def test_cash_flow_split_over_two_pages_is_read(self):
        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "split.pdf"
            _split_cash_flow_pdf(pdf)
            manifest = _read(pdf, profile="corporate", filing_type="financial-statements",
                             period_end="2025-12-31", fiscal_year=2025)
        values = {f["metric"]: f["value"] for f in manifest["facts"]}
        self.assertEqual(values.get("operating_cash_flow"), "15958999")
        self.assertEqual(values.get("investing_cash_flow"), "-7717198")
        self.assertEqual(values.get("financing_cash_flow"), "-10873712")

    def test_pages_are_not_pooled_without_a_repeated_statement_heading(self):
        # The second page must name the same statement; a different table that
        # merely follows one is never absorbed into it.
        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "unrelated.pdf"
            _split_cash_flow_pdf(pdf, second_heading="Notes to the financial statements")
            manifest = _read(pdf, profile="corporate", filing_type="financial-statements",
                             period_end="2025-12-31", fiscal_year=2025)
        values = {f["metric"] for f in manifest["facts"]}
        self.assertNotIn("financing_cash_flow", values)


@unittest.skipUnless(HAVE_PYMUPDF, "the reader needs the optional pymupdf extra")
class TwoPanelStatementTests(unittest.TestCase):
    def test_attribution_panel_without_its_own_heading_is_read(self):
        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "panels.pdf"
            _two_panel_income_pdf(pdf)
            manifest = _read(pdf, profile="corporate", filing_type="financial-statements",
                             period_end="2025-12-31", fiscal_year=2025)
        values = {f["metric"]: f["value"] for f in manifest["facts"]}
        self.assertEqual(values.get("net_income"), "20000")
        self.assertEqual(values.get("net_income_parent"), "19000")
        self.assertEqual(values.get("net_income_noncontrolling"), "1000")

    def test_panel_claiming_a_different_statement_is_not_absorbed(self):
        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "other.pdf"
            _two_panel_income_pdf(pdf, right_panel_heading="Statement of financial position")
            manifest = _read(pdf, profile="corporate", filing_type="financial-statements",
                             period_end="2025-12-31", fiscal_year=2025)
        metrics = {f["metric"] for f in manifest["facts"]}
        self.assertNotIn("net_income_parent", metrics)
