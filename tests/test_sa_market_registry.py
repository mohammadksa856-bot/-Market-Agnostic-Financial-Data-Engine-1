import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_sa_market_registry.py"
SPEC = importlib.util.spec_from_file_location("build_sa_market_registry", SCRIPT)
registry_builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(registry_builder)


class SaudiMarketRegistryTests(unittest.TestCase):
    def test_tracked_registry_is_current_complete_and_deterministic(self):
        built = registry_builder.build_registry()
        tracked = json.loads(registry_builder.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(tracked, built)
        self.assertEqual(len(built), 439)
        self.assertEqual(len({item["symbol"] for item in built}), 439)
        self.assertEqual(built, sorted(built, key=lambda item: int(item["symbol"])))
        registry_builder.validate_registry(built)

    def test_known_company_sources_override_seed_without_dropping_universe(self):
        by_symbol = {item["symbol"]: item for item in registry_builder.build_registry()}
        self.assertEqual(by_symbol["2222"]["company_id"], "sa:2222")
        self.assertTrue(by_symbol["2222"]["sources"])
        self.assertIn("sector", by_symbol["2222"])
        self.assertEqual(by_symbol["8220"]["sources"], [])

    def test_duplicate_seed_symbol_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed = root / "seed.json"
            overrides = root / "companies.json"
            seed.write_text(json.dumps({"data": [
                {"symbol": "1111", "name": "A", "active": "true"},
                {"symbol": "1111", "name": "B", "active": "true"},
            ]}), encoding="utf-8")
            overrides.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(registry_builder.RegistryError, "duplicate"):
                registry_builder.build_registry(seed, overrides)

    def test_check_mode_rejects_stale_output_and_normal_mode_repairs_it(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "registry.json"
            output.write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(registry_builder.RegistryError, "stale"):
                registry_builder.ensure_registry(output, check=True)
            self.assertTrue(registry_builder.ensure_registry(output))
            self.assertFalse(registry_builder.ensure_registry(output))


if __name__ == "__main__":
    unittest.main()
