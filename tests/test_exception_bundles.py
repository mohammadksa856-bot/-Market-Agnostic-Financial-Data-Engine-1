import json
import sys
import tempfile
import unittest
from pathlib import Path

from finengine.database import Database
from finengine.exception_bundles import build_bundles, redact_secrets, MAX_SAMPLES, MAX_CONTEXT_CHARS
from finengine.models import Company, Market, SourceDocument
from finengine.query import FinancialQueryService


def _company(company_id, symbol, name="X"):
    return Company(company_id, Market.SA, symbol, name, "SAR")


def _source(db, company_id, source_key, url="https://tadawul.com.sa/filing.pdf",
            filing_type="financial-results", content_type="application/pdf"):
    doc = SourceDocument(company_id, Market.SA, url, source_key, filing_type, "2025-03-01",
                          b"fake-pdf-bytes", content_type, {})
    db.save_source(doc, content_hash=f"hash-{source_key}", local_path=f"/archive/{source_key}.pdf")


class ExceptionBundlesTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.t.name) / "scratch.sqlite3")
        self.db = Database(self.dbpath)

    def tearDown(self):
        self.db.close()
        self.t.cleanup()

    def _rows_and_context(self):
        q = FinancialQueryService(self.dbpath)
        rows = q.exceptions(None, None, "open", 1000)
        source_lookup = {}
        for skey, in q.conn.execute("SELECT DISTINCT source_key FROM exceptions").fetchall():
            r = q.conn.execute(
                "SELECT source_key,source_url,filing_type,content_type,local_path,content_hash "
                "FROM source_documents WHERE source_key=?", (skey,),
            ).fetchone()
            if r:
                source_lookup[skey] = dict(r)
        catalog_requirement = {r["field_key"]: r["requirement"] for r in q.conn.execute(
            "SELECT field_key,requirement FROM data_catalog_fields WHERE enabled=1").fetchall()}
        known_metric_keys = {r["metric_key"] for r in q.conn.execute(
            "SELECT metric_key FROM metric_definitions WHERE enabled=1").fetchall()}
        q.close()
        return rows, source_lookup, catalog_requirement, known_metric_keys

    def _build(self):
        rows, source_lookup, catalog_requirement, known_metric_keys = self._rows_and_context()
        return build_bundles(rows, source_lookup, catalog_requirement, known_metric_keys)

    # 1. Deterministic grouping -------------------------------------------------
    def test_grouping_is_deterministic_across_repeated_runs(self):
        for i in range(5):
            company_id = f"sa:{1000+i}"
            self.db.register_company(_company(company_id, str(1000 + i)))
            source_key = f"tadawul:{1000+i}:fy2024"
            _source(self.db, company_id, source_key)
            self.db.exception(company_id, source_key, "mapping", "unmapped_metric",
                               "unmapped_metric",
                               {"label": "Sales revenue", "confidence": "0"})

        first = self._build()
        second = self._build()
        self.assertEqual(
            json.dumps(first, sort_keys=True, default=str),
            json.dumps(second, sort_keys=True, default=str),
        )
        self.assertEqual(len(first), 1)
        bundle = first[0]
        self.assertEqual(bundle["classification"], "generic_mapping_fix")
        self.assertEqual(bundle["exception_count"], 5)
        self.assertEqual(bundle["affected_companies_count"], 5)
        # order is stable: identical group keys, third run still matches
        third = self._build()
        self.assertEqual(json.dumps(first, sort_keys=True, default=str),
                          json.dumps(third, sort_keys=True, default=str))

    # 2. Secret redaction ---------------------------------------------------
    def test_secret_shaped_values_are_redacted_not_leaked(self):
        company_id = "sa:2001"
        self.db.register_company(_company(company_id, "2001"))
        source_key = "tadawul:2001:fy2024"
        _source(self.db, company_id, source_key)
        secret = "postgres://admin:Sup3rSecret!@db.internal.example.com:5432/finengine"
        self.db.exception(company_id, source_key, "extraction", "invalid_value",
                           f"could not parse value near connection string {secret}",
                           {"row": {"raw": secret}, "value": secret})
        bundles = self._build()
        self.assertEqual(len(bundles), 1)
        dumped = json.dumps(bundles)
        self.assertNotIn("Sup3rSecret!", dumped)
        self.assertNotIn(secret, dumped)
        self.assertIn("[REDACTED:secret-like-value]", dumped)
        self.assertTrue(bundles[0]["redactions_applied"])
        # unit-level function too
        clean, was_redacted = redact_secrets("AKIA1234567890ABCDEF is my key")
        self.assertTrue(was_redacted)
        self.assertNotIn("AKIA1234567890ABCDEF", clean)

    # 3. No full documents / bounded context ---------------------------------
    def test_samples_are_capped_and_context_is_bounded(self):
        company_id = "sa:3001"
        self.db.register_company(_company(company_id, "3001"))
        long_text = "REDACTED-FREE FILLER TEXT. " * 200  # a lot longer than MAX_CONTEXT_CHARS
        for i in range(10):
            source_key = f"tadawul:3001:doc{i}"
            _source(self.db, company_id, source_key)
            self.db.exception(company_id, source_key, "extraction", "invalid_value",
                               long_text, {"row": long_text, "value": long_text})
        bundles = self._build()
        self.assertEqual(len(bundles), 1)
        bundle = bundles[0]
        self.assertEqual(bundle["exception_count"], 10)  # provenance still counts all 10
        self.assertLessEqual(len(bundle["representative_samples"]), MAX_SAMPLES)
        self.assertEqual(len(bundle["representative_samples"]), MAX_SAMPLES)
        for sample in bundle["representative_samples"]:
            if sample["table_context"]:
                self.assertLessEqual(len(sample["table_context"]), MAX_CONTEXT_CHARS)
            self.assertNotIn(long_text, json.dumps(sample))  # never the full raw text
        dumped_size = len(json.dumps(bundle))
        self.assertLess(dumped_size, len(long_text) * 3)  # bundle stays small vs. 10x full docs

    # 4. Provenance preserved -------------------------------------------------
    def test_provenance_traces_back_to_real_exception_ids(self):
        company_id = "sa:4001"
        self.db.register_company(_company(company_id, "4001"))
        source_key = "tadawul:4001:fy2024"
        _source(self.db, company_id, source_key)
        for i in range(4):
            self.db.exception(company_id, source_key, "mapping", "unmapped_metric",
                               "unmapped_metric", {"label": "Net finance cost", "row": i})
        real_ids = sorted(r[0] for r in self.db.conn.execute(
            "SELECT id FROM exceptions ORDER BY id").fetchall())
        bundles = self._build()
        self.assertEqual(len(bundles), 1)
        bundle = bundles[0]
        self.assertEqual(bundle["exception_ids"], real_ids)
        self.assertEqual(bundle["exception_count"], len(real_ids))
        # every sample id must be a real exception id
        sample_ids = {s["exception_id"] for s in bundle["representative_samples"]}
        self.assertTrue(sample_ids.issubset(set(real_ids)))
        self.assertTrue(sample_ids)

    # 5. Conflicting restatements never merged with a generic mapping fix ----
    def test_conflicts_are_isolated_from_mapping_bundle_and_from_each_other(self):
        company_a = "sa:5001"
        company_b = "sa:5002"
        self.db.register_company(_company(company_a, "5001"))
        self.db.register_company(_company(company_b, "5002"))
        source_a = "tadawul:5001:fy2024"
        source_b = "tadawul:5002:fy2024"
        _source(self.db, company_a, source_a)
        _source(self.db, company_b, source_b)
        # A mapping-fix exception with the same metric name as the conflicts below.
        self.db.exception(company_a, source_a, "mapping", "unmapped_metric",
                           "unmapped_metric", {"label": "revenue", "metric": "revenue"})
        # Two genuine restated-value conflicts for the SAME metric, different companies/periods.
        self.db.exception(company_a, source_a, "validation", "lower_trust_current_conflict",
                           "revenue 2024-12-31 conflict",
                           {"metric": "revenue", "period_end": "2024-12-31",
                            "incoming_value": "100", "current_value": "120"})
        self.db.exception(company_b, source_b, "validation", "lower_trust_current_conflict",
                           "revenue 2023-12-31 conflict",
                           {"metric": "revenue", "period_end": "2023-12-31",
                            "incoming_value": "50", "current_value": "55"})
        bundles = self._build()
        classifications = {b["classification"] for b in bundles}
        self.assertIn("generic_mapping_fix", classifications)
        self.assertIn("data_conflict_or_restatement", classifications)
        conflict_bundles = [b for b in bundles if b["classification"] == "data_conflict_or_restatement"]
        # the two conflicts (different company + period) must NOT be merged into one bundle
        self.assertEqual(len(conflict_bundles), 2)
        for cb in conflict_bundles:
            self.assertEqual(cb["exception_count"], 1)
            self.assertNotEqual(cb["classification"], "generic_mapping_fix")
        mapping_bundle = [b for b in bundles if b["classification"] == "generic_mapping_fix"][0]
        conflict_ids = {i for cb in conflict_bundles for i in cb["exception_ids"]}
        self.assertFalse(conflict_ids & set(mapping_bundle["exception_ids"]))

    # 6. not_applicable / source_unavailable never implied resolved -----------
    def test_not_applicable_and_unavailable_bundles_are_not_marked_resolved(self):
        company_id = "sa:6001"
        self.db.register_company(_company(company_id, "6001"))
        source_key = "argaam:6001:consensus"
        _source(self.db, company_id, source_key, url="https://argaam.com/consensus")
        self.db.exception(company_id, source_key, "understanding", "not_applicable",
                           "field is not applicable for this company type",
                           {"metric": "insurance_gwp"})
        self.db.exception(company_id, source_key, "fetch", "source_access_blocked",
                           "source unreachable: connection timeout",
                           {"connector": "tadawul_fetch"})
        bundles = self._build()
        by_class = {b["classification"]: b for b in bundles}
        self.assertIn("not_applicable", by_class)
        self.assertIn("source_unavailable", by_class)
        for classification in ("not_applicable", "source_unavailable"):
            bundle = by_class[classification]
            self.assertEqual(bundle["status"], "open")
            self.assertFalse(bundle["resolved"])
            self.assertFalse(bundle["deterministic_fix_possible"])


class ExceptionBundlesCliTests(unittest.TestCase):
    """Smoke-tests the `finengine exception-bundles` CLI wiring end-to-end
    against a scratch DB outside the repo (never the default project DB)."""

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.t.name) / "scratch.sqlite3")
        self.db = Database(self.dbpath)
        company_id = "sa:7001"
        self.db.register_company(_company(company_id, "7001"))
        source_key = "tadawul:7001:fy2024"
        _source(self.db, company_id, source_key)
        self.db.exception(company_id, source_key, "mapping", "unmapped_metric",
                           "unmapped_metric", {"label": "Sales revenue"})
        self.db.close()

    def tearDown(self):
        self.t.cleanup()

    def test_cli_emits_valid_jsonl_bundles(self):
        from finengine.cli import main
        old_argv = sys.argv
        sys.argv = ["finengine", "--db", self.dbpath, "exception-bundles"]
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main()
        finally:
            sys.argv = old_argv
        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        bundle = json.loads(lines[0])
        self.assertEqual(bundle["classification"], "generic_mapping_fix")
        self.assertIn("priority_score", bundle)

    def test_cli_reads_more_than_one_thousand_open_exceptions(self):
        db = Database(self.dbpath)
        for index in range(1005):
            db.exception("sa:7001", "tadawul:7001:fy2024", "mapping", "unmapped_metric",
                         "unmapped_metric", {"label": "Sales revenue", "row": index})
        db.close()
        from finengine.cli import main
        import contextlib
        import io
        old_argv = sys.argv
        sys.argv = ["finengine", "--db", self.dbpath, "exception-bundles"]
        try:
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                main()
        finally:
            sys.argv = old_argv
        bundle = json.loads(buffer.getvalue().strip())
        self.assertEqual(bundle["exception_count"], 1006)


if __name__ == "__main__":
    unittest.main()
