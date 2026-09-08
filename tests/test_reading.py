import json
import tempfile
import unittest
from pathlib import Path

try:
    import pymupdf
    HAVE_PYMUPDF = True
except ImportError:  # pragma: no cover
    HAVE_PYMUPDF = False

from finengine.verification import ManifestVerifier


class OcrGeometryTests(unittest.TestCase):
    def test_ocr_line_is_split_into_coordinate_words(self):
        from finengine.reading import StatementReader

        words = StatementReader._split_ocr_line(
            [[150, 30], [300, 30], [300, 60], [150, 60]],
            "30 Jun 2026", 1.5, 4,
        )
        self.assertEqual([word[4] for word in words], ["30", "Jun", "2026"])
        self.assertLess(words[0][0], words[-1][0])

    def test_ocr_currency_glyph_does_not_hide_thousands_scale(self):
        from finengine.reading import StatementReader

        self.assertEqual(StatementReader._scale(
            "All amounts in # thousands unless otherwise stated"
        ), 1000)


def _statement_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    def row(y, label, current, prior):
        page.insert_text((60, y), label, fontsize=9)
        page.insert_text((360, y), current, fontsize=9)
        page.insert_text((460, y), prior, fontsize=9)

    page.insert_text((60, 60), "Consolidated Statement of Financial Position", fontsize=13)
    page.insert_text((360, 90), "2025", fontsize=9)
    page.insert_text((460, 90), "2024", fontsize=9)
    page.insert_text((360, 102), "SAR '000", fontsize=8)
    rows = [
        ("Property, Plant and Equipment", "800,000", "760,000"),
        ("Total Non-Current Assets", "900,000", "850,000"),
        ("Inventories", "120,000", "110,000"),
        ("Cash and Cash Equivalents", "80,000", "70,000"),
        ("Total Current Assets", "300,000", "280,000"),
        ("TOTAL ASSETS", "1,200,000", "1,130,000"),
        ("Share Capital", "500,000", "500,000"),
        ("Retained Earnings", "250,000", "180,000"),
        ("TOTAL EQUITY", "750,000", "680,000"),
        ("Total Non-Current Liabilities", "300,000", "310,000"),
        ("Total Current Liabilities", "150,000", "140,000"),
        ("TOTAL LIABILITIES", "450,000", "450,000"),
        ("TOTAL EQUITY AND LIABILITIES", "1,200,000", "1,130,000"),
    ]
    for i, (label, current, prior) in enumerate(rows):
        row(140 + i * 20, label, current, prior)
    doc.save(path)
    doc.close()


def _two_panel_balance_sheet_pdf(path: Path) -> None:
    """A landscape balance sheet with assets on the left and equity and
    liabilities on the right - the layout finengine's own bundled Aramco/
    SABIC filings use, and the shape a single linear column list corrupts:
    a row can carry an unrelated left-panel and right-panel line together."""
    doc = pymupdf.open()
    page = doc.new_page(width=850, height=567)
    nav = "Stories of pride Strategic approach Financial and business performance At a glance"
    page.insert_text((40, 30), nav, fontsize=9)
    page.insert_text((40, 84), "CONSOLIDATED STATEMENT OF FINANCIAL POSITION", fontsize=11)
    page.insert_text((40, 109), "All amounts in thousands of Saudi Riyals unless otherwise stated", fontsize=8)
    page.insert_text((330, 132), "2025", fontsize=9)
    page.insert_text((395, 132), "2024", fontsize=9)
    page.insert_text((720, 132), "2025", fontsize=9)
    page.insert_text((785, 132), "2024", fontsize=9)
    page.insert_text((434, 132), "Equity and liabilities", fontsize=9)
    page.insert_text((40, 146), "Assets", fontsize=9)

    def left(y, label, current, prior):
        page.insert_text((44, y), label, fontsize=9)
        page.insert_text((311, y), current, fontsize=9)
        page.insert_text((373, y), prior, fontsize=9)

    def right(y, label, current, prior):
        page.insert_text((434, y), label, fontsize=9)
        page.insert_text((698, y), current, fontsize=9)
        page.insert_text((761, y), prior, fontsize=9)

    left(171, "Property, plant and equipment", "800,000", "760,000")
    left(196, "Inventories", "120,000", "110,000")
    left(220, "Cash and cash equivalents", "80,000", "70,000")
    left(247, "Total assets", "1,200,000", "1,130,000")
    right(171, "Share capital", "500,000", "500,000")
    right(196, "Retained earnings", "250,000", "180,000")
    right(220, "Total equity", "750,000", "680,000")
    right(247, "Total liabilities", "450,000", "450,000")
    doc.save(path)
    doc.close()


def _bank_pdf(path: Path) -> None:
    """A Saudi bank's two primary statements: special-commission (interest)
    income, fee income, no current/non-current split on the balance sheet."""
    doc = pymupdf.open()

    def statement(title, rows):
        page = doc.new_page(width=595, height=842)
        page.insert_text((60, 60), title, fontsize=13)
        page.insert_text((360, 92), "2025", fontsize=9)
        page.insert_text((460, 92), "2024", fontsize=9)
        page.insert_text((360, 104), "SAR '000", fontsize=8)
        for i, (label, cur, prior) in enumerate(rows):
            y = 140 + i * 20
            page.insert_text((60, y), label, fontsize=9)
            page.insert_text((360, y), cur, fontsize=9)
            page.insert_text((460, y), prior, fontsize=9)

    statement("Consolidated Statement of Income", [
        ("Special commission income", "30,000,000", "27,000,000"),
        ("Special commission expense", "(12,000,000)", "(10,000,000)"),
        ("Net special commission income", "18,000,000", "17,000,000"),
        ("Fee and commission income", "5,000,000", "4,600,000"),
        ("Fee and commission expense", "(1,200,000)", "(1,100,000)"),
        ("Exchange income", "900,000", "850,000"),
        ("Total operating income", "22,700,000", "21,350,000"),
        ("Impairment charge for expected credit losses", "(2,100,000)", "(2,400,000)"),
        ("Salaries and employee-related expenses", "(4,300,000)", "(4,100,000)"),
        ("Total operating expenses", "(9,500,000)", "(9,600,000)"),
        ("Income before zakat and income tax", "13,200,000", "11,750,000"),
        ("Zakat and income tax", "(1,500,000)", "(1,300,000)"),
        ("Net income for the year", "11,700,000", "10,450,000"),
    ])
    statement("Consolidated Statement of Financial Position", [
        ("Cash and balances with SAMA", "40,000,000", "38,000,000"),
        ("Due from banks and other financial institutions", "15,000,000", "12,000,000"),
        ("Investments, net", "90,000,000", "82,000,000"),
        ("Loans and advances, net", "300,000,000", "280,000,000"),
        ("Total assets", "445,000,000", "412,000,000"),
        ("Due to banks and other financial institutions", "20,000,000", "18,000,000"),
        ("Customers' deposits", "330,000,000", "305,000,000"),
        ("Total liabilities", "380,000,000", "352,000,000"),
        ("Share capital", "40,000,000", "40,000,000"),
        ("Statutory reserve", "15,000,000", "13,000,000"),
        ("Retained earnings", "10,000,000", "7,000,000"),
        ("Total shareholders' equity", "65,000,000", "60,000,000"),
        ("Total liabilities and equity", "445,000,000", "412,000,000"),
    ])
    doc.save(path)
    doc.close()


def _interim_pdf(path: Path) -> None:
    """Interim statement with discrete-quarter and YTD columns on one page."""
    doc = pymupdf.open()
    page = doc.new_page(width=850, height=567)
    page.insert_text((45, 60), "Condensed Consolidated Interim Statement of Income", fontsize=12)
    page.insert_text((300, 90), "For the three-month period ended 30 June", fontsize=8)
    page.insert_text((540, 90), "For the six-month period ended 30 June", fontsize=8)
    for x, year in ((360, "2026"), (460, "2025"), (600, "2026"), (700, "2025")):
        page.insert_text((x, 110), year, fontsize=9)
    rows = [
        ("Revenue", "100", "90", "190", "170"),
        ("Cost of sales", "(60)", "(55)", "(115)", "(105)"),
        ("Gross profit", "40", "35", "75", "65"),
        ("General and administrative expenses", "(10)", "(9)", "(19)", "(17)"),
        ("Income from operations", "30", "26", "56", "48"),
        ("Net income", "20", "18", "37", "32"),
    ]
    for index, row in enumerate(rows):
        y = 145 + index * 24
        page.insert_text((45, y), row[0], fontsize=9)
        for x, value in zip((360, 460, 600, 700), row[1:]):
            page.insert_text((x, y), value, fontsize=9)

    cash = doc.new_page(width=595, height=842)
    cash.insert_text((45, 60), "Condensed Consolidated Interim Statement of Cash Flows", fontsize=12)
    cash.insert_text((320, 88), "For the six-month period ended 30 June", fontsize=8)
    cash.insert_text((360, 108), "2026", fontsize=9)
    cash.insert_text((460, 108), "2025", fontsize=9)
    cash_rows = [
        ("Net cash from operating activities", "50", "45"),
        ("Purchase of property, plant and equipment", "(20)", "(18)"),
        ("Net cash used in investing activities", "(22)", "(19)"),
        ("Proceeds from debt", "10", "8"),
        ("Debt repayments", "(5)", "(4)"),
        ("Net cash from financing activities", "5", "4"),
    ]
    for index, (label, current, prior) in enumerate(cash_rows):
        y = 145 + index * 24
        cash.insert_text((45, y), label, fontsize=9)
        cash.insert_text((360, y), current, fontsize=9)
        cash.insert_text((460, y), prior, fontsize=9)
    doc.save(path)
    doc.close()


def _investor_release_pdf(path: Path) -> None:
    """A release table with a numbered heading, trailing change %, and the
    label/value baselines slightly offset (the layout used by STC)."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((45, 60), "1 Statement of Cash Flows", fontsize=12)
    page.insert_text((345, 90), "H1", fontsize=9)
    page.insert_text((365, 90), "2026", fontsize=9)
    page.insert_text((433, 90), "H1", fontsize=9)
    page.insert_text((453, 90), "2025", fontsize=9)
    rows = [
        ("Net Cash from Operating Activities", "8,342", "4,623", "80.4%"),
        ("Net Cash from Investing Activities", "(4,587)", "9,815", "(146.7%)"),
        ("Net Cash from Financing Activities", "1,813", "(16,638)", "110.9%"),
    ]
    for index, (label, current, prior, change) in enumerate(rows):
        y = 145 + index * 40
        page.insert_text((45, y + 5), label, fontsize=9)
        page.insert_text((350, y), current, fontsize=9)
        page.insert_text((440, y), prior, fontsize=9)
        page.insert_text((510, y), change, fontsize=9)
    doc.save(path)
    doc.close()


@unittest.skipUnless(HAVE_PYMUPDF, "reader needs the optional pymupdf extra")
class BankStatementTests(unittest.TestCase):
    def _read(self, directory: Path):
        from finengine.reading import StatementReader

        pdf = directory / "bank-2025.pdf"
        _bank_pdf(pdf)
        return StatementReader(pdf).read(
            market="SA", symbol="1120", currency="SAR",
            source_url="https://bank.example/fs-2025.pdf", filed_at="2026-02-20",
            period_end="2025-12-31", fiscal_year=2025, profile="bank")

    def test_reads_bank_specific_lines(self):
        with tempfile.TemporaryDirectory() as name:
            manifest = self._read(Path(name))
            metrics = {f["metric"]: f["value"] for f in manifest["facts"]}
            self.assertEqual(manifest["profile"], "bank")
            self.assertEqual(metrics["net_financing_income"], "18000000")
            self.assertEqual(metrics["fee_income"], "5000000")
            self.assertEqual(metrics["total_operating_income"], "22700000")
            self.assertEqual(metrics["provision_expense"], "-2100000")
            self.assertEqual(metrics["customer_deposits"], "330000000")
            self.assertEqual(metrics["net_loans"], "300000000")
            self.assertEqual(metrics["total_assets"], "445000000")
            self.assertEqual(metrics["net_income"], "11700000")

    def test_bank_manifest_passes_verify(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            manifest = self._read(directory)
            imports = directory / "imports"
            imports.mkdir()
            (imports / "alrajhi-2025-fy.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertTrue(report["ok"], report["detail"])
            passed = {c["check"] for c in report["detail"] if c["status"] == "pass"}
            self.assertIn("balance_sheet: assets = liabilities + equity", passed)
            self.assertIn("banking: net financing income = income - expense", passed)

    def test_corporate_profile_ignores_bank_lines(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "bank-2025.pdf"
            _bank_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="1120", currency="SAR",
                source_url="https://bank.example/x.pdf", filed_at="2026-02-20",
                period_end="2025-12-31", fiscal_year=2025)  # default corporate
            metrics = {f["metric"] for f in manifest["facts"]}
            self.assertNotIn("net_financing_income", metrics)
            self.assertNotIn("customer_deposits", metrics)


@unittest.skipUnless(HAVE_PYMUPDF, "reader needs the optional pymupdf extra")
class TwoPanelStatementTests(unittest.TestCase):
    def test_left_and_right_panels_do_not_cross_contaminate(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            pdf = directory / "acme-2025.pdf"
            _two_panel_balance_sheet_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/acme-2025.pdf", filed_at="2026-03-01")

            metrics = {f["metric"]: f["value"] for f in manifest["facts"]}
            self.assertEqual(manifest["period_end"], "2025-12-31")  # inferred, not passed
            self.assertEqual(metrics["total_assets"], "1200000")
            self.assertEqual(metrics["total_equity"], "750000")
            self.assertEqual(metrics["total_liabilities"], "450000")
            self.assertEqual(metrics["cash"], "80000")

            imports = directory / "imports"
            imports.mkdir()
            (imports / "acme-2025-fy.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertTrue(report["ok"], report["detail"])

    def test_navbar_text_in_the_same_zone_does_not_veto_the_page(self):
        # "At a glance" is a real section name in the persistent side-nav on
        # every page of this style of report; it must not be mistaken for a
        # "this is a summary page" signal just because it shares the top of
        # the page with the real statement heading.
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _two_panel_balance_sheet_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/x.pdf", filed_at="2026-03-01",
                period_end="2025-12-31", fiscal_year=2025)
            self.assertIn("total_assets", {f["metric"] for f in manifest["facts"]})


@unittest.skipUnless(HAVE_PYMUPDF, "reader needs the optional pymupdf extra")
class StatementReaderTests(unittest.TestCase):
    def test_reads_numbered_investor_release_table(self):
        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "release.pdf"
            _investor_release_pdf(pdf)
            from finengine.reading import StatementReader
            manifest = StatementReader(pdf).read(
                "SA", "7010", "SAR", "https://issuer.example/release.pdf",
                "2026-07-29", "2026-06-30", 2026, "interim-report",
            )
            values = {fact["metric"]: fact["value"] for fact in manifest["facts"]}
            self.assertEqual(values["operating_cash_flow"], "8342")
            self.assertEqual(values["investing_cash_flow"], "-4587")
            self.assertEqual(values["financing_cash_flow"], "1813")
            self.assertTrue(all(
                fact["period_kind"] == "ytd" for fact in manifest["facts"]
            ))

    def test_interim_reader_separates_quarter_and_ytd_columns(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "interim.pdf"
            _interim_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="2010", currency="SAR",
                source_url="https://issuer.example/q2.pdf", filed_at="2026-07-29",
                period_end="2026-06-30", fiscal_year=2026,
                filing_type="interim-report",
            )
            facts = {(fact["metric"], fact["period_kind"]): fact
                     for fact in manifest["facts"]}
            self.assertEqual(facts[("revenue", "quarter")]["value"], "100")
            self.assertEqual(facts[("revenue", "ytd")]["value"], "190")
            self.assertEqual(facts[("operating_cash_flow", "ytd")]["value"], "50")
            self.assertEqual(facts[("revenue", "quarter")]["period_start"], "2026-04-01")
            self.assertEqual(facts[("revenue", "ytd")]["period_start"], "2026-01-01")
            self.assertEqual(facts[("revenue", "quarter")]["fiscal_quarter"], 2)

    def test_interim_job_reader_derives_period_from_archived_source_title(self):
        from finengine.cli import _read_pdf_manifest
        from finengine.models import Company, Market

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "interim.pdf"
            _interim_pdf(pdf)
            company = Company("sa:2010", Market.SA, "2010", "SABIC", "SAR")
            row = {
                "source_url": "https://issuer.example/quarterly-2026-q2.pdf",
                "filed_at": "2026-07-29", "filing_type": "interim-report",
                "metadata_json": json.dumps({"title": "Quarterly report 2026 Q2"}),
            }
            manifest, report, reader = _read_pdf_manifest(pdf, company, row, False)
            self.assertTrue(report["ok"], report)
            self.assertEqual(reader, "deterministic")
            self.assertEqual(manifest["period_end"], "2026-06-30")
            self.assertEqual(
                {fact["period_kind"] for fact in manifest["facts"]},
                {"quarter", "ytd"},
            )

    def test_reads_a_balance_sheet_and_verify_accepts_it(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            pdf = directory / "acme-2025.pdf"
            _statement_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/acme-2025.pdf",
                filed_at="2026-03-01", period_end="2025-12-31", fiscal_year=2025)

            metrics = {f["metric"]: f for f in manifest["facts"]}
            self.assertEqual(metrics["total_assets"]["value"], "1200000")
            self.assertEqual(metrics["total_assets"]["scale"], "1000")   # SAR '000
            self.assertIn("total_equity", metrics)
            self.assertIn("total_liabilities", metrics)
            self.assertEqual(metrics["cash"]["value"], "80000")

            imports = directory / "imports"
            imports.mkdir()
            (imports / "acme-2025-fy.json").write_text(
                json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertTrue(report["ok"], report["detail"])
            self.assertTrue(any(
                c["check"].startswith("balance_sheet: assets = liabilities + equity")
                and c["status"] == "pass" for c in report["detail"]))

    def test_picks_the_current_year_column_not_the_prior_year(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "acme.pdf"
            _statement_pdf(pdf)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="9999", currency="SAR",
                source_url="https://example.test/x.pdf", filed_at="2026-03-01",
                period_end="2025-12-31", fiscal_year=2025)
            metrics = {f["metric"]: f["value"] for f in manifest["facts"]}
            self.assertEqual(metrics["total_equity"], "750000")   # 2025, not 680,000


if __name__ == "__main__":
    unittest.main()
