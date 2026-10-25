import unittest
from decimal import Decimal

from finengine.calculations import Calculator
from finengine.models import Fact, PeriodKind


def instant(metric, value):
    return Fact("sa:TST", metric, Decimal(value), "SAR", "SAR", None, "2026-06-30", PeriodKind.INSTANT, 2026, 2,
                "source:test", "https://example.test", "2026-07-29")


class TangibleBookTests(unittest.TestCase):
    def derived(self, facts):
        return {f.metric: f.value for f in Calculator().calculate(facts)}

    def test_missing_intangibles_are_unknown_not_zero(self):
        out = self.derived([instant("total_equity", "100"), instant("shares_outstanding", "10")])
        self.assertNotIn("tangible_book_value", out)
        self.assertNotIn("tangible_book_value_per_share", out)
        self.assertEqual(out["book_value_per_share"], Decimal("10"))

    def test_reported_intangibles_are_subtracted(self):
        out = self.derived([instant("total_equity", "100"), instant("intangible_assets", "30"),
                            instant("shares_outstanding", "10")])
        self.assertEqual(out["tangible_book_value"], Decimal("70"))
        self.assertEqual(out["tangible_book_value_per_share"], Decimal("7"))


if __name__ == "__main__":
    unittest.main()
