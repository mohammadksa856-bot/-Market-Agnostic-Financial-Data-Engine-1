"""The pre-zakat line that opens a bank's indirect cash-flow statement.

Bank Albilad's interim cash-flow statement starts on "Net income for the period
before zakat". That caption contains the words "net income for the period", so
without an entry of its own it resolves to the shorter net-income caption and a
pre-zakat amount is published as net income - which in a first-quarter filing,
where the year-to-date span is the quarter itself, the period roll-forward check
then rejects.
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


def _albilad_q1_pdf(path: Path, cash_flow_caption: str) -> None:
    document = pymupdf.open()

    income = document.new_page(width=640, height=842)
    income.insert_text((40, 50), "INTERIM CONSOLIDATED STATEMENT OF INCOME (UNAUDITED)",
                       fontsize=11)
    income.insert_text((360, 80), "For the three months period ended", fontsize=7)
    for x, year in zip(_X, ("2024", "2023")):
        income.insert_text((x, 100), f"March 31, {year}", fontsize=8)
    rows = [
        ("Income from investing and financing assets", ("1,341,350", "1,335,606")),
        ("Total operating income", ("1,341,350", "1,335,606")),
        ("Salaries and employee-related expenses", ("(410,000)", "(395,000)")),
        ("Total operating expenses", ("(624,460)", "(711,417)")),
        ("Zakat and income tax", ("(73,840)", "(64,291)")),
        ("Net income for the period after zakat", ("643,050", "559,898")),
    ]
    y = 140
    for label, values in rows:
        income.insert_text((40, y), label, fontsize=9)
        for x, value in zip(_X, values):
            income.insert_text((x, y), value, fontsize=9)
        y += 18

    flows = document.new_page(width=640, height=842)
    flows.insert_text((40, 50), "INTERIM CONSOLIDATED STATEMENT OF CASH FLOWS", fontsize=11)
    for x, year in zip(_X, ("2024", "2023")):
        flows.insert_text((x, 100), f"March 31, {year}", fontsize=8)
    flow_rows = [
        ("OPERATING ACTIVITIES", None),
        (cash_flow_caption, ("716,890", "624,189")),
        ("Depreciation and amortisation", ("120,000", "110,000")),
        ("Net cash from operating activities", ("1,500,000", "1,400,000")),
        ("INVESTING ACTIVITIES", None),
        ("Net cash used in investing activities", ("(900,000)", "(850,000)")),
        ("FINANCING ACTIVITIES", None),
        ("Net cash from financing activities", ("200,000", "180,000")),
        ("Net change in cash and cash equivalents", ("800,000", "730,000")),
    ]
    y = 140
    for label, values in flow_rows:
        flows.insert_text((40, y), label, fontsize=9)
        if values:
            for x, value in zip(_X, values):
                flows.insert_text((x, y), value, fontsize=9)
        y += 18

    document.save(path)
    document.close()


@unittest.skipUnless(HAVE_PYMUPDF, "the reader needs the optional pymupdf extra")
class AlbiladCashFlowOpeningLineTests(unittest.TestCase):
    CAPTIONS = (
        "Net income for the period before zakat",
        "Net income before zakat for the period",
        "Net income for the year before zakat",
        "Net income before zakat for the year",
    )

    def _read(self, directory: Path, caption: str):
        from finengine.reading import StatementReader

        pdf = directory / "albilad-q1-2024.pdf"
        _albilad_q1_pdf(pdf, caption)
        return StatementReader(pdf, enable_ocr=False).read(
            market="SA", symbol="1140", currency="SAR",
            source_url="https://issuer.example/q1-2024.pdf", filed_at="2024-04-28",
            period_end="2024-03-31", fiscal_year=2024, filing_type="interim-report",
            profile="bank")

    def test_pre_zakat_opening_line_is_not_published_as_net_income(self):
        for caption in self.CAPTIONS:
            with self.subTest(caption=caption):
                with tempfile.TemporaryDirectory() as name:
                    manifest = self._read(Path(name), caption)
                values = {fact["metric"]: fact["value"] for fact in manifest["facts"]}
                self.assertEqual(values.get("net_income"), "643050")
                self.assertEqual(values.get("income_before_income_taxes_and_zakat"), "716890")
                self.assertNotIn(
                    "716890",
                    [fact["value"] for fact in manifest["facts"]
                     if fact["metric"] == "net_income"],
                    "the pre-zakat figure must never be published as net income")
