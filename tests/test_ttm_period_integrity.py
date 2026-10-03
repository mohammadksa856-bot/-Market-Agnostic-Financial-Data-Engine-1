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

if __name__=='__main__':unittest.main()
