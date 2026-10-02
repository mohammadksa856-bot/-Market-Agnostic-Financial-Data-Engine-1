import unittest

from finengine.reading import BANK_LINE_MAP, _resolve_line


class CashFlowDepreciationIdentityTests(unittest.TestCase):
    def test_cash_flow_add_back_has_its_own_metric(self):
        self.assertEqual(_resolve_line('Depreciation and amortization', 'cash_flow', BANK_LINE_MAP),
                         'depreciation_amortization_cash_flow')

    def test_income_expense_identity_is_preserved(self):
        self.assertEqual(_resolve_line('Depreciation and amortization', 'income_statement', BANK_LINE_MAP),
                         'depreciation_amortization')

    def test_balance_sheet_does_not_take_flow_label(self):
        self.assertIsNone(_resolve_line('Depreciation and amortization', 'balance_sheet', BANK_LINE_MAP))
