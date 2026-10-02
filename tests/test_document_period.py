import unittest
from decimal import Decimal
from finengine.document_period import annual_period_from_text


class CoverPeriodTests(unittest.TestCase):
    def test_upload_year_does_not_override_reporting_date(self):
        self.assertEqual(annual_period_from_text('Published 2026. For the year ended\n31 December 2025'), ('2025-12-31', 2025))

    def test_dates_not_attached_to_reporting_heading_are_not_evidence(self):
        self.assertIsNone(annual_period_from_text('Annual 2025. Approved 15 February 2026'))

    def test_ambiguous_reporting_dates_are_not_guessed(self):
        self.assertIsNone(annual_period_from_text('For the year ended 31 December 2025; for the year ended 31 December 2024'))

    def test_invalid_date_is_not_accepted(self):
        self.assertIsNone(annual_period_from_text('For the year ended 31 February 2025'))

    def test_spaced_ocr_thousands_declaration(self):
        from finengine.reading import StatementReader
        self.assertEqual(StatementReader._declared_scale("2022 2021 SAR' 000 SAR' 000"), Decimal(1000))

    def test_reported_number_is_not_a_thousands_declaration(self):
        from finengine.reading import StatementReader
        self.assertIsNone(StatementReader._declared_scale('Total assets 210,000'))
        self.assertIsNone(StatementReader._declared_scale("Customer' 000123"))
