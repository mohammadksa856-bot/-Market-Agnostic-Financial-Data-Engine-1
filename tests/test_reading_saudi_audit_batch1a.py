"""Offline regression tests for reader defects proven by the independent Saudi
bank audit (batch 1-A: ANB, Riyad, Albilad, Aljazira, Al Rajhi).

Each test builds a tiny synthetic PDF reproducing the layout that failed on the
real archived document (named in the docstring) and asserts the reader now reads
it as the printed page says.
"""
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False


def _facts(pdf, *, filing_type="financial-statements", period_end="2024-06-30",
           fiscal_year=2024):
    from finengine.reading import StatementReader

    manifest = StatementReader(pdf, enable_ocr=False).read(
        "SA", "9999", "SAR", "https://example.invalid/x.pdf", "2024-08-01",
        period_end=period_end, fiscal_year=fiscal_year,
        filing_type=filing_type, profile="bank")
    return manifest["facts"]


def _by(facts, metric, kind=None):
    return [f for f in facts if f["metric"] == metric and (kind is None or f["period_kind"] == kind)]


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class NoteColumnFarLeftOfValuesTests(unittest.TestCase):
    """anb-2017/2018/2019 annual reports: the note column sits ~140pt left of the
    first amount column, so every row carrying a note number was dropped and the
    note-table rows of the 'commission rate sensitivity' disclosure were published
    as the balance sheet instead."""

    def _pdf(self, path):
        doc = pymupdf.open()
        page = doc.new_page(width=612, height=792)
        page.insert_text((50, 60), "Consolidated Statement of Financial Position", fontsize=12)
        page.insert_text((50, 76), "As at December 31, 2017 and 2016", fontsize=9)
        page.insert_text((470, 100), "2017", fontsize=9)
        page.insert_text((560, 100), "2016", fontsize=9)
        rows = [
            ("Cash and balances with SAMA", "4", "17,251,379", "19,503,973"),
            ("Due from banks and other financial institutions", "5", "1,710,123", "4,030,850"),
            ("Investments, net", "6", "32,320,816", "25,548,399"),
            ("Loans and advances, net", "7", "114,542,929", "115,511,521"),
            ("Total assets", None, "171,701,699", "170,008,722"),
            ("Customers' deposits", "14", "136,048,089", "135,907,457"),
            ("Total liabilities", None, "146,635,734", "146,084,169"),
            ("Share capital", "17", "10,000,000", "10,000,000"),
            ("Total equity", None, "25,065,965", "23,924,553"),
            ("Total liabilities and equity", None, "171,701,699", "170,008,722"),
        ]
        for i, (label, note, cur, prior) in enumerate(rows):
            y = 130 + i * 16
            page.insert_text((50, y), label, fontsize=9)
            if note:
                page.insert_text((318, y), note, fontsize=9)  # far left of the 2017 column
            page.insert_text((430, y), cur, fontsize=9)
            page.insert_text((520, y), prior, fontsize=9)
        doc.save(path)
        doc.close()

    def test_rows_with_a_distant_note_column_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "bs.pdf"
            self._pdf(pdf)
            facts = _facts(pdf, period_end="2017-12-31", fiscal_year=2017)
        values = {f["metric"]: f["value"] for f in facts if f["period_kind"] == "instant"}
        self.assertEqual(values["cash_and_balances_with_central_bank"], "17251379")
        self.assertEqual(values["due_from_banks"], "1710123")
        self.assertEqual(values["bank_investments"], "32320816")
        self.assertEqual(values["net_loans"], "114542929")
        self.assertEqual(values["customer_deposits"], "136048089")
        self.assertEqual(values["share_capital"], "10000000")
        self.assertEqual(values["total_assets"], "171701699")

    def test_label_numbers_are_not_mistaken_for_note_references(self):
        """'Tier 1' keeps its number: only a token to the right of every caption
        word counts as a note reference."""
        from finengine.reading import _NOTE_REFERENCE

        self.assertTrue(_NOTE_REFERENCE.match("16.1"))
        self.assertTrue(_NOTE_REFERENCE.match("6-41"))
        self.assertTrue(_NOTE_REFERENCE.match("12"))
        self.assertFalse(_NOTE_REFERENCE.match("17,251,379"))


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class TitleYearsDoNotShiftPeriodColumnsTests(unittest.TestCase):
    """anb-2021-q3 (and the same layout in other ANB interims): the title line
    'FOR THE NINE MONTHS ENDED SEPTEMBER 30, 2021 AND 2020' repeats the years
    above the real header. The two stray year centres shifted the column pairing
    so the three-month column was published as nine-month ('ytd') and the
    discrete quarter was lost."""

    def _pdf(self, path):
        doc = pymupdf.open()
        page = doc.new_page(width=612, height=792)
        page.insert_text((50, 60), "INTERIM CONSOLIDATED STATEMENT OF INCOME", fontsize=12)
        page.insert_text((50, 76), "FOR THE NINE MONTHS ENDED SEPTEMBER 30, 2021 AND 2020", fontsize=9)
        # Title years repeated as separate tokens above the header, offset from the
        # real columns exactly as on the archived page (centres 303 and 349 against
        # real period columns at 344 / 413 / 480 / 550).
        page.insert_text((294, 92), "2021", fontsize=9)
        page.insert_text((340, 92), "2020", fontsize=9)
        page.insert_text((300, 120), "For the three months ended", fontsize=8)
        page.insert_text((450, 120), "For the nine months ended", fontsize=8)
        for x, year in ((335, "2021"), (404, "2020"), (471, "2021"), (541, "2020")):
            page.insert_text((x, 138), year, fontsize=9)
        rows = [
            ("Special commission income", "1,383,847", "1,405,650", "3,884,940", "4,665,714"),
            ("Special commission expense", "131,498", "195,012", "322,861", "965,268"),
            ("Total operating income", "1,479,227", "1,463,829", "4,416,797", "4,423,168"),
            ("Total operating expenses", "738,399", "701,594", "2,439,500", "2,314,951"),
            ("Net income for the period", "664,557", "667,936", "1,715,488", "1,795,837"),
        ]
        for i, row in enumerate(rows):
            y = 170 + i * 16
            page.insert_text((50, y), row[0], fontsize=9)
            # right-aligned amounts: their centres sit left of the header years, so
            # the stray title year at x~303 still "aligns" with them
            for x, value in zip((305, 375, 442, 510), row[1:]):
                page.insert_text((x, y), value, fontsize=9)
        doc.save(path)
        doc.close()

    def test_three_month_and_nine_month_columns_are_not_confused(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "is.pdf"
            self._pdf(pdf)
            facts = _facts(pdf, filing_type="interim-report",
                           period_end="2021-09-30", fiscal_year=2021)
        quarter = _by(facts, "total_operating_income", "quarter")
        ytd = _by(facts, "total_operating_income", "ytd")
        self.assertEqual([f["value"] for f in quarter], ["1479227"])
        self.assertEqual([f["value"] for f in ytd], ["4416797"])
        self.assertEqual([f["value"] for f in _by(facts, "net_income", "ytd")], ["1715488"])
        self.assertEqual([f["value"] for f in _by(facts, "net_income", "quarter")], ["664557"])

    def test_header_row_selection_keeps_single_line_pages_unchanged(self):
        from finengine.reading import StatementReader

        one_line = [(350.0, 120.0), (420.0, 120.0), (490.0, 119.5), (560.0, 120.2)]
        self.assertEqual(StatementReader._header_row_hits(one_line), one_line)
        with_title = [(300.0, 76.0), (345.0, 76.0)] + one_line
        self.assertEqual(sorted(StatementReader._header_row_hits(with_title)), sorted(one_line))


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class CashFlowRowsDoNotPopulateIncomeStatementMetricsTests(unittest.TestCase):
    """anb-2015/2017/2019 annual reports and anb-2020/2021 Q1, alrajhi-2024-q2:
    cash-flow reconciliation rows ('Dividend income' shown as a deduction,
    'Special commission expense on Sukuk') were published as dividend_income and
    financing_expense; the depreciation / impairment add-backs kept the
    add-back's positive sign instead of the expense sign used everywhere else."""

    def _pdf(self, path):
        doc = pymupdf.open()
        page = doc.new_page(width=612, height=792)
        page.insert_text((50, 60), "Consolidated Statement of Cash Flows", fontsize=12)
        page.insert_text((400, 100), "2017", fontsize=9)
        page.insert_text((500, 100), "2016", fontsize=9)
        rows = [
            ("Net income for the year", "3,034,058", "2,861,877"),
            ("Dividend income", "(53,203)", "(45,484)"),
            ("Special commission expense on Sukuk", "71,460", "64,498"),
            ("Depreciation and amortization", "221,379", "202,300"),
            ("Provision for credit losses, net", "1,148,790", "1,200,000"),
            ("Net cash from operating activities", "3,665,645", "4,000,000"),
            ("Net cash used in financing activities", "(1,347,952)", "(900,000)"),
        ]
        for i, (label, cur, prior) in enumerate(rows):
            y = 140 + i * 18
            page.insert_text((50, y), label, fontsize=9)
            page.insert_text((400, y), cur, fontsize=9)
            page.insert_text((500, y), prior, fontsize=9)
        doc.save(path)
        doc.close()

    def test_income_statement_metrics_are_not_read_from_cash_flow_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "cf.pdf"
            self._pdf(pdf)
            facts = _facts(pdf, period_end="2017-12-31", fiscal_year=2017)
        metrics = {f["metric"] for f in facts}
        self.assertNotIn("dividend_income", metrics)
        self.assertNotIn("financing_expense", metrics)
        self.assertEqual({f["metric"]: f["value"] for f in facts}["operating_cash_flow"], "3665645")

    def test_cash_flow_addbacks_take_the_expense_sign(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "cf.pdf"
            self._pdf(pdf)
            facts = _facts(pdf, period_end="2017-12-31", fiscal_year=2017)
        values = {f["metric"]: f["value"] for f in facts}
        self.assertEqual(values["depreciation_amortization"], "-221379")
        self.assertEqual(values["provision_expense"], "-1148790")


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class PluralStatementHeadingTests(unittest.TestCase):
    """aljazira-2008-q2: 'CONSOLIDATED STATEMENTS OF INCOME' (plural) was not a
    recognised heading, so the whole income statement was missing from the
    manifest while a bogus 'bank_investments' fact was lifted from a row of it."""

    def test_plural_headings_are_recognised(self):
        from finengine.reading import ANCHORS

        self.assertIn("statements of income", ANCHORS["income_statement"])
        self.assertIn("statements of financial position", ANCHORS["balance_sheet"])
        self.assertIn("statements of cash flows", ANCHORS["cash_flow"])

    def test_plural_income_statement_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "is.pdf"
            doc = pymupdf.open()
            page = doc.new_page(width=612, height=792)
            page.insert_text((50, 60), "CONSOLIDATED STATEMENTS OF INCOME", fontsize=12)
            page.insert_text((300, 100), "Three Months Ended", fontsize=8)
            page.insert_text((450, 100), "Six Months Ended", fontsize=8)
            for x, year in ((340, "2008"), (400, "2007"), (470, "2008"), (535, "2007")):
                page.insert_text((x, 118), year, fontsize=9)
            rows = [
                ("Special commission income", "254,450", "227,177", "523,754", "432,350"),
                ("Total operating income", "331,317", "363,328", "673,071", "778,495"),
                ("Net income for the period", "100,062", "206,677", "253,157", "508,994"),
            ]
            for i, row in enumerate(rows):
                y = 150 + i * 16
                page.insert_text((50, y), row[0], fontsize=9)
                for x, value in zip((340, 400, 470, 535), row[1:]):
                    page.insert_text((x, y), value, fontsize=9)
            doc.save(pdf)
            doc.close()
            facts = _facts(pdf, filing_type="interim-report",
                           period_end="2008-06-30", fiscal_year=2008)
        self.assertEqual([f["value"] for f in _by(facts, "total_operating_income", "quarter")], ["331317"])
        self.assertEqual([f["value"] for f in _by(facts, "total_operating_income", "ytd")], ["673071"])


@unittest.skipUnless(HAVE_PYMUPDF, "requires pymupdf")
class OtherExpenseSignTests(unittest.TestCase):
    """riyad/aljazira/anb interims: 'Other operating expenses' is printed as an
    unsigned expense; unlike every other expense metric it was published
    positive (72 facts), so a signed sum of expense lines was wrong."""

    def test_other_operating_expenses_are_natural_negative(self):
        from finengine.reading import _BANK_NATURAL_NEGATIVE_METRICS

        self.assertIn("other_expense", _BANK_NATURAL_NEGATIVE_METRICS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
