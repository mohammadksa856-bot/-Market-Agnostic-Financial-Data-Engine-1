import unittest
from datetime import date, timedelta
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind

ENDS = ("03-31", "06-30", "09-30", "12-31")


def quarter(value, year, q, metric="revenue"):
    start = date(year, 1, 1) if q == 1 else date.fromisoformat(f"{year}-{ENDS[q - 2]}") + timedelta(days=1)
    return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", start.isoformat(), f"{year}-{ENDS[q - 1]}",
                PeriodKind.QUARTER, year, q, "source:test", "https://example.test", f"{year}-{ENDS[q - 1]}")


def eight_quarters(values, metric="revenue"):
    periods = [(2024, 4), (2025, 1), (2025, 2), (2025, 3), (2025, 4), (2026, 1), (2026, 2), (2026, 3)]
    return [quarter(v, y, q, metric) for v, (y, q) in zip(values, periods) if v is not None]


class TtmGrowthTests(unittest.TestCase):
    def derived(self, facts):
        return {f.metric: f.value for f in Calculator().calculate(facts)}

    def test_trailing_year_against_the_same_window_a_year_earlier(self):
        out = self.derived(eight_quarters(["25", "25", "25", "25", "30", "30", "30", "30"]))
        self.assertEqual(out["revenue_ttm"], Decimal("120"))
        self.assertEqual(out["revenue_ttm_growth"], Decimal("0.2"))

    def test_a_gap_in_the_earlier_window_withholds_the_growth(self):
        out = self.derived(eight_quarters(["25", None, "25", "25", "30", "30", "30", "30"]))
        self.assertIn("revenue_ttm", out)
        self.assertNotIn("revenue_ttm_growth", out)

    def test_ebitda_has_a_trailing_growth(self):
        out = self.derived(eight_quarters(["5", "5", "5", "5", "4", "4", "4", "4"], "ebitda"))
        self.assertEqual(out["ebitda_ttm_growth"], Decimal("-0.2"))


if __name__ == "__main__":
    unittest.main()


class TtmBasisTests(unittest.TestCase):
    def ytd(self, value, year, end, kind=PeriodKind.YTD):
        quarter_number = ENDS.index(end) + 1
        return Fact("sa:TST", "revenue", Decimal(value), "SAR", "SAR", f"{year}-01-01", f"{year}-{end}", kind,
                    year, quarter_number if kind == PeriodKind.YTD else None, "source:test", "https://example.test",
                    f"{year}-{end}")

    def ttm(self, facts):
        return {(f.metric, f.period_end): f.value for f in Calculator().calculate(facts)}

    def test_window_mixing_bases_within_a_year_is_withheld(self):
        # Q2-Q3 2024 as first published (they add to the 9M figure); Q4 2024 re-presented with the full year
        facts = [quarter("30", 2024, 1), quarter("30", 2024, 2), quarter("30", 2024, 3), quarter("20", 2024, 4),
                 quarter("20", 2025, 1), self.ytd("60", 2024, "06-30"), self.ytd("90", 2024, "09-30"),
                 self.ytd("80", 2024, "12-31", PeriodKind.FY)]
        self.assertNotIn(("revenue_ttm", "2025-03-31"), self.ttm(facts))

    def test_single_quarter_of_a_year_does_not_mix_the_window(self):
        facts = [quarter("20", 2024, 4), quarter("20", 2025, 1), quarter("20", 2025, 2), quarter("20", 2025, 3),
                 self.ytd("90", 2024, "09-30"), self.ytd("80", 2024, "12-31", PeriodKind.FY)]
        self.assertEqual(self.ttm(facts)[("revenue_ttm", "2025-09-30")], Decimal("80"))

    def test_every_quarter_of_the_batch_gets_its_window(self):
        out = self.ttm(eight_quarters(["25", "25", "25", "25", "30", "30", "30", "30"]))
        self.assertEqual(out[("revenue_ttm", "2025-09-30")], Decimal("100"))
        self.assertEqual(out[("revenue_ttm", "2026-09-30")], Decimal("120"))
