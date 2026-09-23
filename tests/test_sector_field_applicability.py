from __future__ import annotations

"""Generic proof that industry-inapplicable fields are excluded by cited
rule, not silently dropped, and that the exclusion is scoped to the industry
- never to one named company - so any bank benefits and any non-bank is
unaffected.

Real Saudi-market companies (see config/companies.json) carry a broad
``sector`` such as "Financials" and a specific ``industry`` such as "Banks" -
the same distinction the catalog itself uses for scope_type='industry' rows
(catalog.py GROUPS). The exclusion table is keyed by industry to match that
existing convention, so it fires for any bank regardless of its broader
sector label.
"""

import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.domains import (
    INDUSTRY_FIELD_EXCLUSION_REASON_CODE,
    INDUSTRY_FIELD_EXCLUSIONS,
    CompanyDomainStore,
)
from finengine.models import Company, Market, SourceDocument


class SectorFieldApplicabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "sector.sqlite3")
        self.db = Database(self.path)
        self.store = CompanyDomainStore(self.db)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def _register(self, company_id, symbol, sector, industry):
        company = Company(company_id, Market.SA, symbol, f"Synthetic {symbol}", "SAR",
                          isin=f"SA{symbol.zfill(10)}", exchange="Saudi Exchange",
                          country="SA", sector=sector, industry=industry,
                          timezone="Asia/Riyadh")
        self.db.register_company(company)
        return company

    def test_bank_industry_excludes_current_assets_and_current_liabilities_with_rule_reference(self):
        # Mirrors real registry data: broad sector "Financials", specific
        # industry "Banks" (see config/companies.json for Al Rajhi Bank).
        self._register("sa:BANK1", "BANK1", "Financials", "Banks")
        self.store.refresh_catalog_completeness("sa:BANK1")
        rows = {
            row["category"]: row for row in self.db.conn.execute(
                "SELECT * FROM company_completeness WHERE company_id=?", ("sa:BANK1",))
        }
        balance_sheet = rows["balance_sheet"]
        import json
        missing = set(json.loads(balance_sheet["missing_fields_json"]))
        self.assertNotIn("current_assets", missing)
        self.assertNotIn("current_liabilities", missing)
        required_missing = set(json.loads(balance_sheet["required_missing_json"]))
        self.assertNotIn("current_assets", required_missing)
        self.assertNotIn("current_liabilities", required_missing)

        # The exclusion must be documented, not silent.
        availability = {
            row["field_key"]: row for row in self.db.conn.execute(
                "SELECT * FROM company_field_availability WHERE company_id=?", ("sa:BANK1",))
        }
        for field_key in ("current_assets", "current_liabilities"):
            self.assertIn(field_key, availability)
            self.assertEqual(availability[field_key]["status"], "not_applicable")
            self.assertEqual(availability[field_key]["reason_code"], INDUSTRY_FIELD_EXCLUSION_REASON_CODE)
            self.assertTrue(availability[field_key]["rule_reference"])

    def test_financials_sector_alone_does_not_trigger_the_exclusion(self):
        """The gate reads ``industry``, not the broader ``sector`` label: an
        insurer or asset manager sharing the "Financials" sector but a
        different industry must still require these fields."""
        self._register("sa:INS1", "INS1", "Financials", "Insurance")
        self.store.refresh_catalog_completeness("sa:INS1")
        import json
        balance_sheet = self.db.conn.execute(
            "SELECT * FROM company_completeness WHERE company_id=? AND category='balance_sheet'",
            ("sa:INS1",),
        ).fetchone()
        required_missing = set(json.loads(balance_sheet["required_missing_json"]))
        self.assertIn("current_assets", required_missing)
        self.assertIn("current_liabilities", required_missing)

    def test_non_bank_sector_still_requires_current_assets_and_current_liabilities(self):
        """The exclusion is industry-scoped, not global: an unrelated
        corporate company's required-fields gate must be completely
        unaffected."""
        self._register("sa:CORP1", "CORP1", "Energy", "Oil & Gas")
        self.store.refresh_catalog_completeness("sa:CORP1")
        import json
        balance_sheet = self.db.conn.execute(
            "SELECT * FROM company_completeness WHERE company_id=? AND category='balance_sheet'",
            ("sa:CORP1",),
        ).fetchone()
        required_missing = set(json.loads(balance_sheet["required_missing_json"]))
        self.assertIn("current_assets", required_missing)
        self.assertIn("current_liabilities", required_missing)
        self.assertEqual(
            self.db.conn.execute(
                "SELECT count(*) FROM company_field_availability WHERE company_id=?", ("sa:CORP1",)
            ).fetchone()[0],
            0,
        )

    def test_exclusion_table_is_keyed_by_industry_not_by_company_id(self):
        """Structural guard against a company-specific hack creeping in here:
        every exclusion must be declared against an industry name, and the
        two bank-excluded fields must each carry a citable rule_reference."""
        for industry, fields in INDUSTRY_FIELD_EXCLUSIONS.items():
            self.assertIsInstance(industry, str)
            self.assertNotRegex(industry, r"^\d+$")  # not a company_id-shaped key
            for field_key, rule in fields.items():
                self.assertTrue(rule.get("rule_reference"))
                self.assertTrue(rule.get("reason"))

    def test_two_different_banks_get_the_same_exclusion_independently(self):
        """Proves the rule is industry logic, not a hard-coded single-company
        carve-out, by applying it to two distinct synthetic bank companies."""
        self._register("sa:BANKA", "BANKA", "Financials", "Banks")
        self._register("sa:BANKB", "BANKB", "Financials", "Banks")
        self.store.refresh_catalog_completeness("sa:BANKA")
        self.store.refresh_catalog_completeness("sa:BANKB")
        for company_id in ("sa:BANKA", "sa:BANKB"):
            count = self.db.conn.execute(
                "SELECT count(*) FROM company_field_availability WHERE company_id=? "
                "AND status='not_applicable' AND field_key IN ('current_assets','current_liabilities')",
                (company_id,),
            ).fetchone()[0]
            self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
