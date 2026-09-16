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

    def test_left_curly_apostrophe_declares_thousands_scale(self):
        from finengine.reading import StatementReader

        self.assertEqual(StatementReader._scale(
            "Amounts in SAR ‘000 (Unaudited)"
        ), 1000)

    def test_document_scale_can_come_from_later_text_backed_page(self):
        from finengine.reading import StatementReader

        self.assertEqual(StatementReader._document_scale([
            "INTERIM CONSOLIDATED STATEMENT OF INCOME",
            "Notes to the statements\nAmounts in SAR ‘000",
        ]), 1000)

    def test_narrative_amount_does_not_declare_document_scale(self):
        from finengine.reading import StatementReader

        self.assertEqual(StatementReader._document_scale([
            "The facility amounted to SAR 45.3 million during the period."
        ]), 1)

    def test_comprehensive_attribution_is_not_net_income_attribution(self):
        from finengine.reading import StatementReader

        heading = "INTERIM CONSOLIDATED STATEMENT OF COMPREHENSIVE INCOME"
        self.assertTrue(StatementReader._is_comprehensive_attribution(
            heading, "Attributable to equity holders of the Bank", "net_income_parent"
        ))
        self.assertFalse(StatementReader._is_comprehensive_attribution(
            "INTERIM CONSOLIDATED STATEMENT OF INCOME",
            "Attributable to equity holders of the Bank", "net_income_parent"
        ))
        self.assertFalse(StatementReader._is_comprehensive_attribution(
            heading, "Net income attributable to equity holders", "net_income_parent"
        ))

    def test_changes_in_equity_is_not_a_primary_statement_continuation(self):
        from finengine.reading import _NON_PRIMARY_STATEMENT

        self.assertIsNotNone(_NON_PRIMARY_STATEMENT.search(
            "INTERIM CONSOLIDATED STATEMENT OF CHANGES IN EQUITY"
        ))
        self.assertIsNone(_NON_PRIMARY_STATEMENT.search(
            "INTERIM CONSOLIDATED STATEMENT OF INCOME"
        ))

    def test_reported_amount_does_not_override_declared_millions_scale(self):
        from finengine.reading import StatementReader

        self.assertEqual(StatementReader._scale(
            "All amounts in millions of Saudi Riyals. Cash was 210,000."
        ), 1_000_000)

    def test_dual_currency_headers_keep_quarter_and_ytd_semantics(self):
        from finengine.reading import StatementReader

        def word(text, center, y):
            return (center - 5, y, center + 5, y + 8, text, 0, 0, 0)

        columns = [255.6, 298.2, 340.7, 383.3, 431.4, 474.0, 516.4, 559.0]
        words = []
        for text, center in [
            ("2nd", 235.0), ("quarter", 251.7),
            ("2nd", 277.9), ("quarter", 294.3),
            ("Six", 320.1), ("months", 336.7),
            ("Six", 362.9), ("months", 379.4),
            ("2nd", 410.8), ("quarter", 427.4),
            ("Six", 495.9), ("months", 512.5),
        ]:
            words.append(word(text, center, 84))
        for year, center in zip(["2026", "2025"] * 4, columns):
            words.append(word(year, center, 94))
        groups = StatementReader._period_column_groups(
            words, "income_statement", columns, "ytd"
        )
        self.assertEqual([kind for _, kind in groups], ["quarter", "ytd"])


def _statement_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    def row(y, label, current, prior):
        page.insert_text((60, y), label, fontsize=9)
        page.insert_text((360, y), current, fontsize=9)
        page.insert_text((460, y), prior, fontsize=9)

    page.insert_text((60, 60), "Consolidated Statement of Financial Position", fontsize=13)
    # A report-header year unrelated to the statement's period columns.
    page.insert_text((200, 35), "2025", fontsize=9)
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


def _bank_pdf(path: Path, *, unsigned_expenses: bool = False) -> None:
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
        ("Special commission expense",
         "12,000,000" if unsigned_expenses else "(12,000,000)",
         "10,000,000" if unsigned_expenses else "(10,000,000)"),
        ("Net special commission income", "18,000,000", "17,000,000"),
        ("Fee and commission income", "5,000,000", "4,600,000"),
        ("Fee and commission expense",
         "1,200,000" if unsigned_expenses else "(1,200,000)",
         "1,100,000" if unsigned_expenses else "(1,100,000)"),
        ("Exchange income", "900,000", "850,000"),
        ("Total operating income", "22,700,000", "21,350,000"),
        ("Impairment charge for expected credit losses",
         "2,100,000" if unsigned_expenses else "(2,100,000)",
         "2,400,000" if unsigned_expenses else "(2,400,000)"),
        ("Salaries and employee-related expenses", "(4,300,000)", "(4,100,000)"),
        ("Total operating expenses",
         "9,500,000" if unsigned_expenses else "(9,500,000)",
         "9,600,000" if unsigned_expenses else "(9,600,000)"),
        ("Income before zakat and income tax", "13,200,000", "11,750,000"),
        ("Zakat and income tax", "(1,500,000)", "(1,300,000)"),
        ("Net income for the year", "11,700,000", "10,450,000"),
        # Note-table spillover: the embedded value belongs to another column,
        # so this must not overwrite the clean primary-statement tax row.
        ("Zakat and income tax 447,520", "513,232", "400,000"),
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
    page.insert_text((330, 90), "2nd quarter", fontsize=8)
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
def _singular_cash_flow_pdf(path: Path) -> None:
    """ANB titles the page "Consolidated statement of cash flow" (singular)."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    def row(y, label, current, prior):
        page.insert_text((60, y), label, fontsize=9)
        page.insert_text((360, y), current, fontsize=9)
        page.insert_text((460, y), prior, fontsize=9)

    page.insert_text((60, 60), "Consolidated statement of cash flow", fontsize=13)
    page.insert_text((360, 90), "2024", fontsize=9)
    page.insert_text((460, 90), "2023", fontsize=9)
    page.insert_text((360, 102), "SAR '000", fontsize=8)
    rows = [
        ("Net cash from operating activities", "9,100,000", "8,400,000"),
        ("Net cash used in investing activities", "(3,200,000)", "(2,900,000)"),
        ("Net cash used in financing activities", "(1,400,000)", "(1,100,000)"),
    ]
    for index, (label, current, prior) in enumerate(rows):
        row(140 + index * 20, label, current, prior)
    doc.save(path)
    doc.close()


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
            self.assertEqual(metrics["income_taxes_and_zakat"], "-1500000")

    def test_reordered_net_commission_label_is_not_gross_income(self):
        from finengine.reading import BANK_LINE_MAP, _resolve_line

        self.assertEqual(
            _resolve_line("Special commission income, net", "income_statement", BANK_LINE_MAP),
            "net_financing_income",
        )

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

    def test_unsigned_bank_expenses_are_normalized_to_natural_sign(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "bank-2025.pdf"
            _bank_pdf(pdf, unsigned_expenses=True)
            manifest = StatementReader(pdf).read(
                market="SA", symbol="1080", currency="SAR",
                source_url="https://bank.example/fs-2025.pdf", filed_at="2026-02-20",
                period_end="2025-12-31", fiscal_year=2025, profile="bank")
            metrics = {f["metric"]: f["value"] for f in manifest["facts"]}
            self.assertEqual(metrics["financing_expense"], "-12000000")
            self.assertEqual(metrics["fee_expense"], "-1200000")
            self.assertEqual(metrics["provision_expense"], "-2100000")
            self.assertEqual(metrics["total_operating_expenses"], "-9500000")

            imports = Path(name) / "imports"
            imports.mkdir()
            (imports / "anb-2025-fy.json").write_text(
                json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
            self.assertTrue(report["ok"], report["detail"])

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

    def test_two_different_statements_on_one_spread_are_isolated(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "insurance-spread.pdf"
            doc = pymupdf.open()
            page = doc.new_page(width=1190, height=842)
            page.insert_text((45, 70), "Consolidated Statement of Financial Position", fontsize=11)
            page.insert_text((640, 70), "Consolidated Statement of Income", fontsize=11)
            for x, year in ((455, "2025"), (525, "2024"),
                            (1050, "2025"), (1120, "2024")):
                page.insert_text((x, 105), year, fontsize=9)
            left_rows = [("Cash and cash equivalents", "100", "90"),
                         ("Total assets", "1000", "900"),
                         ("Total liabilities", "600", "550"),
                         ("Total equity", "400", "350")]
            right_rows = [("Insurance revenue", "800", "700"),
                          ("Insurance service expenses", "(600)", "(530)"),
                          ("Net profit for the year after Zakat", "100", "90")]
            for index, (label, current, prior) in enumerate(left_rows):
                y = 145 + index * 30
                page.insert_text((45, y), label, fontsize=9)
                page.insert_text((445, y), current, fontsize=9)
                page.insert_text((515, y), prior, fontsize=9)
            for index, (label, current, prior) in enumerate(right_rows):
                y = 145 + index * 30
                page.insert_text((640, y), label, fontsize=9)
                page.insert_text((1040, y), current, fontsize=9)
                page.insert_text((1110, y), prior, fontsize=9)
            doc.save(pdf)
            doc.close()
            manifest = StatementReader(pdf).read(
                "SA", "8010", "SAR", "https://issuer.example/report.pdf",
                "2026-03-01", "2025-12-31", 2025, profile="insurance",
            )
            metrics = {fact["metric"]: fact["value"] for fact in manifest["facts"]}
            self.assertEqual(metrics["total_assets"], "1000")
            self.assertEqual(metrics["insurance_revenue"], "800")
            self.assertEqual(metrics["net_income"], "100")


@unittest.skipUnless(HAVE_PYMUPDF, "reader needs the optional pymupdf extra")
class StatementReaderTests(unittest.TestCase):
    def test_ocr_bank_caption_years_do_not_become_value_columns(self):
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "bank-columns.pdf"
            doc = pymupdf.open()
            page = doc.new_page(width=595, height=842)
            page.insert_text((275, 90), "2023", fontsize=9)
            page.insert_text((337, 90), "2022", fontsize=9)
            page.insert_text((416, 108), "2023", fontsize=9)
            page.insert_text((494, 108), "2022", fontsize=9)
            for index in range(6):
                y = 145 + index * 30
                page.insert_text((54, y), f"Financial line {index}", fontsize=9)
                page.insert_text((342, y), str(20 + index), fontsize=9)
                page.insert_text((398, y), f"{6200 + index},000", fontsize=9)
                page.insert_text((476, y), f"{3900 + index},000", fontsize=9)
            words = page.get_text("words")
            columns = StatementReader._column_blocks(page, words)
            doc.close()

            self.assertEqual(len(columns), 1)
            self.assertEqual(len(columns[0]), 2)
            self.assertGreater(columns[0][0], 400)

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

    def test_cash_flow_statement_titled_in_the_singular_is_read(self):
        # The heading list required "statement of cash flows"; ANB's annual
        # statements title the page "statement of cash flow", so the page was
        # skipped and every figure on it was lost.
        from finengine.reading import StatementReader

        with tempfile.TemporaryDirectory() as name:
            pdf = Path(name) / "cash-flow.pdf"
            _singular_cash_flow_pdf(pdf)
            manifest = StatementReader(pdf, enable_ocr=False).read(
                market="SA", symbol="1080", currency="SAR",
                source_url="https://bank.example/fs-2024.pdf", filed_at="2025-02-13",
                period_end="2024-12-31", fiscal_year=2024,
                filing_type="financial-statements", profile="bank")
        values = {fact["metric"]: fact["value"] for fact in manifest["facts"]
                  if fact["period_end"] == "2024-12-31"}
        self.assertEqual(values["operating_cash_flow"], "9100000")
        self.assertEqual(values["investing_cash_flow"], "-3200000")
        self.assertEqual(values["financing_cash_flow"], "-1400000")

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


_INTERIM_X = (360, 420, 500, 560)


def _bank_interim_pdf(path: Path) -> None:
    """A Saudi bank's condensed interim statements in the layout SNB files.

    Expenses are printed unsigned, a reversal of credit impairment appears in
    parentheses, and rule lines sit a few points above each subtotal - close
    enough to share a text row with the subtotal's figures but not its caption.
    """
    doc = pymupdf.open()

    def put_values(page, y, values):
        for x, value in zip(_INTERIM_X, values):
            page.insert_text((x, y), value, fontsize=9)

    income = doc.new_page(width=640, height=842)
    income.insert_text((40, 50), "Condensed Interim Consolidated Statement of Income", fontsize=12)
    income.insert_text((345, 80), "For the three-month period ended", fontsize=7)
    income.insert_text((485, 80), "For the six-month period ended", fontsize=7)
    for x, year in zip(_INTERIM_X, ("2026", "2025", "2026", "2025")):
        income.insert_text((x + 12, 100), year, fontsize=9)
    rows = [
        ("Special commission income", ("15,403,976", "15,158,013", "30,164,208", "29,478,376")),
        ("Special commission expense",
         ("(7,509,937)", "(8,073,927)", "(14,773,847)", "(15,143,237)")),
        ("RULE", ()),
        ("Net special commission income", ("7,894,039", "7,084,086", "15,390,361", "14,335,139")),
        ("Fee income from banking services", ("1,840,082", "1,855,664", "3,804,787", "3,676,706")),
        ("Fee expense from banking services", ("(597,475)", "(612,209)", "(1,251,992)", "(1,196,097)")),
        ("RULE", ()),
        ("Fee income from banking services, net",
         ("1,242,607", "1,243,455", "2,552,795", "2,480,609")),
        ("Other operating expenses, net", ("(454,872)", "(371,720)", "(997,432)", "(690,646)")),
        ("RULE", ()),
        ("Total operating income", ("10,582,649", "9,510,390", "20,233,004", "19,121,905")),
        ("Salaries and employee-related expenses",
         ("1,270,116", "1,227,368", "2,590,836", "2,476,571")),
        ("Total operating expenses before expected credit losses",
         ("2,790,036", "2,764,875", "5,591,366", "5,491,470")),
        ("Impairment charge/(reversal) for expected credit losses, net",
         ("257,760", "(169,849)", "(320,109)", "(138,555)")),
        ("RULE", ()),
        ("Total operating expenses", ("3,047,796", "2,595,026", "5,271,257", "5,352,915")),
        ("Other non-operating income/(expense), net",
         ("(110,744)", "(50,555)", "(249,051)", "(185,018)")),
        ("RULE", ()),
        ("Income for the period before zakat and income tax",
         ("7,424,109", "6,864,809", "14,712,696", "13,583,972")),
        ("Zakat and income tax expense", ("(809,261)", "(737,743)", "(1,670,464)", "(1,472,539)")),
        ("RULE", ()),
        ("Net income for the period", ("6,614,848", "6,127,066", "13,042,232", "12,111,433")),
        ("EPS", ("1.07", "0.99", "2.11", "1.95")),
    ]
    y = 130
    for label, values in rows:
        if label == "RULE":
            # The rule's words start 5.5pt above the figures, which start 1.5pt
            # above their caption: within six points of each, as in the filing.
            for x in _INTERIM_X:
                income.insert_text((x, y - 1), "--------", fontsize=9)
            y += 6.5
            continue
        if label == "EPS":
            income.insert_text((40, y + 1.5), "Diluted earnings per share (expressed in SAR per share)",
                               fontsize=9)
            income.insert_text((318, y + 1.5), "16", fontsize=9)
        else:
            income.insert_text((40, y + 1.5), label, fontsize=9)
        put_values(income, y, values)
        y += 16

    position = doc.new_page(width=640, height=842)
    position.insert_text((40, 50), "Condensed Interim Consolidated Statement of Financial Position",
                         fontsize=12)
    for x, year in zip(_INTERIM_X[:2], ("2026", "2025")):
        position.insert_text((x + 12, 100), year, fontsize=9)
    balance_rows = [
        ("Cash and balances with central banks", None, ("62,968,568", "44,923,237")),
        ("Financing and advances, net", "6", ("739,562,568", "729,310,906")),
        ("Total assets", None, ("1,244,688,218", "1,210,031,553")),
        ("Customers' deposits", "10, 22", ("698,169,934", "636,094,377")),
        ("Total liabilities", None, ("1,029,827,867", "1,006,204,305")),
        ("Total equity", None, ("214,860,351", "203,827,248")),
        ("Total liabilities and equity", None, ("1,244,688,218", "1,210,031,553")),
    ]
    for index, (label, note, values) in enumerate(balance_rows):
        row_y = 130 + index * 18
        position.insert_text((40, row_y), label, fontsize=9)
        if note:
            position.insert_text((300, row_y), note, fontsize=9)
        put_values(position, row_y, values)
    doc.save(path)
    doc.close()


@unittest.skipUnless(HAVE_PYMUPDF, "reader needs the optional pymupdf extra")
class BankInterimStatementTests(unittest.TestCase):
    def _read(self, directory: Path):
        from finengine.reading import StatementReader

        pdf = directory / "bank-q2-2026.pdf"
        _bank_interim_pdf(pdf)
        return StatementReader(pdf, enable_ocr=False).read(
            market="SA", symbol="1180", currency="SAR",
            source_url="https://bank.example/fs-2q-2026.pdf", filed_at="2026-07-30",
            period_end="2026-06-30", fiscal_year=2026, filing_type="interim-report",
            profile="bank")

    def _by_kind(self, manifest):
        return {(f["metric"], f["period_kind"]): f for f in manifest["facts"]}

    def test_rule_lines_do_not_shift_subtotal_figures_between_rows(self):
        with tempfile.TemporaryDirectory() as name:
            facts = self._by_kind(self._read(Path(name)))
        self.assertEqual(facts[("net_financing_income", "quarter")]["value"], "7894039")
        self.assertEqual(facts[("net_financing_income", "ytd")]["value"], "15390361")
        self.assertEqual(facts[("total_operating_income", "quarter")]["value"], "10582649")
        self.assertEqual(facts[("income_before_income_taxes_and_zakat", "ytd")]["value"],
                         "14712696")
        self.assertEqual(facts[("net_income", "quarter")]["value"], "6614848")

    def test_gross_and_net_fee_lines_keep_distinct_metrics(self):
        with tempfile.TemporaryDirectory() as name:
            facts = self._by_kind(self._read(Path(name)))
        self.assertEqual(facts[("fee_income", "quarter")]["value"], "1840082")
        self.assertEqual(facts[("fee_expense", "quarter")]["value"], "-597475")
        self.assertEqual(facts[("net_fee_income", "quarter")]["value"], "1242607")
        self.assertEqual(facts[("other_income", "quarter")]["value"], "-454872")

    def test_unsigned_statement_keeps_impairment_reversals_as_income(self):
        with tempfile.TemporaryDirectory() as name:
            facts = self._by_kind(self._read(Path(name)))
        self.assertEqual(facts[("salaries_and_employee_expenses", "quarter")]["value"], "-1270116")
        self.assertEqual(facts[("operating_expense_banking", "quarter")]["value"], "-2790036")
        self.assertEqual(facts[("total_operating_expenses", "quarter")]["value"], "-3047796")
        self.assertEqual(facts[("provision_expense", "quarter")]["value"], "-257760")  # charge
        self.assertEqual(facts[("provision_expense", "ytd")]["value"], "320109")       # reversal

    def test_non_operating_line_is_not_operating_income(self):
        with tempfile.TemporaryDirectory() as name:
            facts = self._by_kind(self._read(Path(name)))
        self.assertNotIn(("operating_income", "quarter"), facts)
        self.assertNotIn(("operating_income", "ytd"), facts)

    def test_per_share_figures_survive_the_magnitude_filter_with_a_share_unit(self):
        with tempfile.TemporaryDirectory() as name:
            facts = self._by_kind(self._read(Path(name)))
        eps = facts[("eps_diluted", "quarter")]
        self.assertEqual((eps["value"], eps["unit"], eps["scale"]), ("1.07", "SAR/share", "1"))
        self.assertEqual(facts[("eps_diluted", "ytd")]["value"], "2.11")

    def test_financing_line_and_multi_note_deposit_row_are_read(self):
        with tempfile.TemporaryDirectory() as name:
            facts = self._by_kind(self._read(Path(name)))
        self.assertEqual(facts[("net_loans", "instant")]["value"], "739562568")
        self.assertEqual(facts[("customer_deposits", "instant")]["value"], "698169934")

    def test_interim_bank_manifest_passes_verify(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            manifest = self._read(directory)
            imports = directory / "imports"
            imports.mkdir()
            (imports / "snb-2026-q2.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = ManifestVerifier(imports).verify()
        self.assertTrue(report["ok"], report["detail"])
        passed = {(c["check"], c["period"]) for c in report["detail"] if c["status"] == "pass"}
        self.assertIn(("banking: net financing income = income - expense", "2026-06-30 quarter"),
                      passed)
        self.assertIn(("income_statement: pre-tax income - tax = net income", "2026-06-30 ytd"),
                      passed)

    def test_typographic_apostrophe_and_word_start_matching(self):
        from finengine.reading import BANK_LINE_MAP, LINE_MAP, _resolve_line

        bank = {**LINE_MAP, **BANK_LINE_MAP}
        self.assertEqual(_resolve_line("Customers’ deposits", "balance_sheet", bank),
                         "customer_deposits")
        self.assertIsNone(_resolve_line("Other non-operating income/(expense), net",
                                        "income_statement", LINE_MAP))
        self.assertEqual(_resolve_line("Total non-current assets", "balance_sheet", LINE_MAP),
                         "noncurrent_assets")

    def test_box_drawing_rules_are_not_caption_text(self):
        from finengine.reading import _is_rule_token

        self.assertTrue(_is_rule_token("────────"))
        self.assertTrue(_is_rule_token("════════"))
        self.assertTrue(_is_rule_token("--------"))
        self.assertFalse(_is_rule_token("-"))
        self.assertFalse(_is_rule_token("(454,872)"))


if __name__ == "__main__":
    unittest.main()
