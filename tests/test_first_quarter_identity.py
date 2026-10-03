import unittest
from dataclasses import replace
from decimal import Decimal
from finengine.models import Fact,PeriodKind
from finengine.calculations import Calculator

class FirstQuarterIdentityTests(unittest.TestCase):
    def fact(self):
        return Fact('sa:TST','net_income',Decimal(123),'SAR','SAR','2025-01-01','2025-03-31',
                    PeriodKind.YTD,2025,1,'source','https://example.test','2025-04-30')
    def test_preserves_value_source_and_dates(self):
        source=self.fact();out=Calculator()._first_quarters([source]);self.assertEqual(len(out),1)
        for attribute in ('value','source_key','source_url','period_start','period_end','unit','currency'):
            self.assertEqual(getattr(out[0],attribute),getattr(source,attribute))
        self.assertTrue(out[0].is_calculated);self.assertEqual(out[0].period_kind,PeriodKind.QUARTER)
    def test_no_duplicate_or_overwrite(self):
        source=self.fact();quarter=replace(source,period_kind=PeriodKind.QUARTER,value=Decimal(999))
        self.assertEqual(Calculator()._first_quarters([source,quarter]),[])
    def test_later_ytd_not_quarter(self):
        self.assertEqual(Calculator()._first_quarters([replace(self.fact(),fiscal_quarter=2,period_end='2025-06-30')]),[])
    def test_wrong_first_quarter_interval_rejected(self):
        self.assertEqual(Calculator()._first_quarters([replace(self.fact(),period_start='2024-01-01')]),[])
    def test_stock_metric_not_derived(self):
        self.assertEqual(Calculator()._first_quarters([replace(self.fact(),metric='total_assets')]),[])
    def test_dimensions_preserved(self):
        source=replace(self.fact(),scope='segment',dimensions={'segment':'retail'})
        self.assertEqual(Calculator()._first_quarters([source])[0].dimensions,source.dimensions)

if __name__=='__main__':unittest.main()
