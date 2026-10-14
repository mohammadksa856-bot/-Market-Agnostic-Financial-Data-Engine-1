"""Characterization, NOT approval of current N/A scoring or proposed policy."""
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from finengine.database import Database
from finengine.factory_contract import measure_factory_contract
from finengine.models import Company, Market


class IndependentNAReview(unittest.TestCase):
    def measure(self, industry):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "review.sqlite3")
            try:
                db.register_company(Company("sa:1120", Market.SA, "1120", "Synthetic review fixture", "SAR", industry=industry))
                return measure_factory_contract(db, "sa:1120")
            finally:
                db.close()

    def test_reproduces_bank_free_credit_without_financial_data(self):
        result = self.measure("Banks")
        row = next(r for r in result["categories"] if r["category_key"] == "operational_kpis")
        self.assertEqual(row["status"], "not_applicable")
        self.assertEqual(Decimal(row["score"]), 1)
        self.assertEqual(Decimal(row["weighted_score"]), 7)
        self.assertEqual(result["readiness_state"], "not_ready")

    def test_telecom_exemption_has_same_algorithmic_issue(self):
        result = self.measure("Telecommunications")
        row = next(r for r in result["categories"] if r["category_key"] == "sector_specific_fields")
        self.assertEqual(row["status"], "not_applicable")
        self.assertEqual(Decimal(row["weighted_score"]), Decimal(row["weight"]))

    def test_non_excluded_industries_have_no_category_na_credit(self):
        for industry in ("Insurance", "Energy", "Retail"):
            result = self.measure(industry)
            self.assertFalse(any(r["status"] == "not_applicable" for r in result["categories"]))

    def test_proposed_valid_exclusion_denominator_is_not_adopted(self):
        # Pure illustrative mathematics; not a new engine score or financial fact.
        earned, excluded_weight = Decimal("15.3"), Decimal(7)
        self.assertEqual(earned + excluded_weight, Decimal("22.3"))
        self.assertEqual(100 - excluded_weight, Decimal(93))
        normalized = 100 * earned / (100 - excluded_weight)
        self.assertLess(normalized, earned + excluded_weight)
        self.assertEqual(100 * Decimal(93) / Decimal(93), Decimal(100))
        self.assertLess(Decimal(93), Decimal(95))  # removal without normalization unfairly caps readiness


if __name__ == "__main__":
    unittest.main()
