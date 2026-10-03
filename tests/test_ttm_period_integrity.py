import unittest
from dataclasses import replace
from decimal import Decimal
from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind

class TtmPeriodIntegrityTests(unittest.TestCase):
    def facts(self):
        spans=[('2025-01-01','2025-03-31'),('2025-04-01','2025-06-30'),
               ('2025-07-01','2025-09-30'),('2025-10-01','2025-12-31')]
        return [Fact('sa:TST','net_income',Decimal(10),'SAR','SAR',start,end,
                     PeriodKind.QUARTER,2025,i+1,'fixture','https://example.test','2026-01-01')
                for i,(start,end) in enumerate(spans)]
    def output(self,facts):
        return Calculator()._ttm(facts,{facts[-1].period_end})
    def test_four_contiguous_quarters(self):
        out=self.output(self.facts());self.assertEqual(out[0].value,Decimal(40))
        self.assertEqual(out[0].period_start,'2025-01-01')
    def test_missing_quarter_not_ttm(self):
        facts=self.facts();facts[0]=replace(facts[0],period_start='2024-07-01',period_end='2024-09-30')
        self.assertEqual(self.output(facts),[])
    def test_overlapping_ytd_not_ttm(self):
        facts=self.facts();facts[1]=replace(facts[1],period_start='2025-01-01')
        self.assertEqual(self.output(facts),[])
    def test_missing_start_not_ttm(self):
        facts=self.facts();facts[1]=replace(facts[1],period_start=None)
        self.assertEqual(self.output(facts),[])
    def test_one_day_gap_not_ttm(self):
        facts=self.facts();facts[1]=replace(facts[1],period_start='2025-04-02')
        self.assertEqual(self.output(facts),[])
    def test_leap_year_supported(self):
        facts=[replace(f,period_start=f.period_start.replace('2025','2024'),
                       period_end=f.period_end.replace('2025','2024'),fiscal_year=2024) for f in self.facts()]
        self.assertEqual(self.output(facts)[0].value,Decimal(40))
    def test_53_week_fiscal_year_supported(self):
        spans=[('2024-12-29','2025-03-29'),('2025-03-30','2025-06-28'),
               ('2025-06-29','2025-09-27'),('2025-09-28','2026-01-03')]
        facts=[replace(f,period_start=start,period_end=end) for f,(start,end) in zip(self.facts(),spans)]
        self.assertEqual(self.output(facts)[0].value,Decimal(40))

if __name__=='__main__':unittest.main()
