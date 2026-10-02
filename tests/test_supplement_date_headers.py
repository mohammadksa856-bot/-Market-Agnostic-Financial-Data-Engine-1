import unittest
from datetime import datetime
from finengine.reading_xlsx import SupplementReader


class Sheet:
    title = 'Reviewed'
    def iter_rows(self, **kwargs):
        return iter([[None, datetime(2025, 12, 31), datetime(2026, 3, 31), datetime(2026, 3, 31)]])


class DateHeaderTests(unittest.TestCase):
    def reader(self, header=None):
        reader = object.__new__(SupplementReader)
        reader.mapping = {'date_headers': {'Reviewed': header}} if header else {}
        return reader

    def test_dates_are_not_guessed_without_explicit_contract(self):
        self.assertEqual(self.reader()._period_columns(Sheet(), {'quarter'}), {})

    def test_only_reviewed_columns_and_kind_are_used(self):
        reader = self.reader({'row': 4, 'first_column': 2, 'last_column': 3, 'period_kind': 'quarter'})
        self.assertEqual(reader._period_columns(Sheet(), {'quarter'}),
                         {1: ('quarter', 2025, '2025-12-31'), 2: ('quarter', 2026, '2026-03-31')})
        self.assertEqual(reader._period_columns(Sheet(), {'fy'}), {})

    def test_invalid_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            self.reader({'period_kind': 'guess'})._period_columns(Sheet(), {'quarter'})
