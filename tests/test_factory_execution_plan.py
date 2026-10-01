import copy
import json
import tempfile
import unittest
from pathlib import Path

from finengine.factory_execution import dependency_status, load_execution_plan


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "factory" / "18-category-contract.json"
PLAN = ROOT / "config" / "factory" / "execution-plan.json"


class FactoryExecutionPlanTests(unittest.TestCase):
    def test_plan_covers_every_contract_category_exactly_once(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        plan, metadata = load_execution_plan(CONTRACT, PLAN)
        self.assertEqual(len(plan["waves"]), 6)
        self.assertEqual(
            set(metadata), {item["category_key"] for item in contract["categories"]}
        )
        self.assertEqual(len(metadata), 18)

    def test_financial_derivations_wait_for_financial_statements(self):
        _, metadata = load_execution_plan(CONTRACT, PLAN)
        for key in (
            "profitability", "liquidity_solvency", "efficiency", "growth",
            "per_share", "calculated_smart_metrics",
        ):
            self.assertEqual(metadata[key]["depends_on"], ["financial_statements"])
            self.assertGreater(metadata[key]["wave_ordinal"], 1)

    def test_valuation_waits_for_financial_market_and_per_share_inputs(self):
        _, metadata = load_execution_plan(CONTRACT, PLAN)
        self.assertEqual(
            set(metadata["valuation"]["depends_on"]),
            {"financial_statements", "per_share", "market_data"},
        )

    def test_dependency_status_distinguishes_waiting_blocked_and_terminal(self):
        dependencies = ["financial_statements", "market_data"]
        self.assertEqual(
            dependency_status({"financial_statements": "running"}, dependencies),
            ("waiting", dependencies),
        )
        self.assertEqual(
            dependency_status({
                "financial_statements": "validated", "market_data": "published"
            }, dependencies),
            ("ready", []),
        )
        self.assertEqual(
            dependency_status({
                "financial_statements": "blocked", "market_data": "published"
            }, dependencies),
            ("blocked", ["financial_statements"]),
        )

    def test_plan_rejects_missing_duplicate_and_forward_dependencies(self):
        original = json.loads(PLAN.read_text(encoding="utf-8"))
        fixtures = []

        missing = copy.deepcopy(original)
        missing["waves"][0]["categories"].clear()
        fixtures.append((missing, "does not match contract"))

        duplicate = copy.deepcopy(original)
        duplicate["waves"][1]["categories"].append(
            {"category_key": "financial_statements", "depends_on": []}
        )
        fixtures.append((duplicate, "appears more than once"))

        forward = copy.deepcopy(original)
        forward["waves"][0]["categories"][0]["depends_on"] = ["valuation"]
        fixtures.append((forward, "must be in an earlier wave"))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            for payload, message in fixtures:
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    load_execution_plan(CONTRACT, path)


if __name__ == "__main__":
    unittest.main()
