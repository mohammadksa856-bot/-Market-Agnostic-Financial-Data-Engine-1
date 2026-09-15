import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from finengine.archive import _index_local_path
from finengine.bootstrap import _manifest_company, sync_reviewed_manifests
from finengine.database import Database
from finengine.models import Company, Market
from finengine.registry import CompanyRegistry


class ReviewedManifestSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "financial.sqlite3"
        self.imports = self.root / "imports"
        self.imports.mkdir()
        self.raw = self.root / "raw"
        self.raw.mkdir()
        self.registry = self.root / "companies.json"
        self.registry.write_text(json.dumps([{
            "company_id": "sa:TST", "market": "SA", "symbol": "TST",
            "name": "Test Company", "currency": "SAR", "sector": "Energy",
            "industry": "Integrated Oil & Gas",
            "sources": ["https://issuer.example/investors"],
        }]), encoding="utf-8")
        db = Database(self.database)
        try:
            db.register_company(Company(
                "sa:TST", Market.SA, "TST", "Test Company", "SAR",
                sources=("https://issuer.example/investors",),
                sector="Energy", industry="Integrated Oil & Gas",
            ))
        finally:
            db.close()

    def tearDown(self):
        self.temporary.cleanup()

    def test_manifest_name_wins_over_year_that_is_another_company_symbol(self):
        registry = CompanyRegistry([
            Company("sa:2222", Market.SA, "2222", "Saudi Arabian Oil Company (Aramco)", "SAR"),
            Company("sa:2019", Market.SA, "2019", "Example Industrial Company", "SAR"),
            Company("sa:2223", Market.SA, "2223", "Saudi Aramco Base Oil Company - Luberef", "SAR"),
        ])
        company = _manifest_company(
            Path("aramco-2019-fy-historical.json"), {"facts": []}, registry,
        )
        self.assertEqual(company.company_id, "sa:2222")

    def _manifest(self, name="test-2025.json", facts=True):
        path = self.imports / name
        payload = {
            "company_id": "sa:TST", "market": "SA", "symbol": "TST",
            "filing_type": "integrated-annual-report", "filed_at": "2026-03-01",
            "period_end": "2025-12-31",
            "source_url": "https://issuer.example/reports/2025.pdf",
            "facts": ([{
                "metric": "revenue", "value": "1000",
                "period_start": "2025-01-01", "period_end": "2025-12-31",
                "period_kind": "fy", "fiscal_year": 2025,
            }] if facts else []),
            "company_attributes": [{
                "attribute_key": "business_model", "category": "company_model",
                "value": "Integrated energy company", "language": "en",
                "metadata": {"page": 10, "quote": "Integrated energy company"},
            }],
            "disclosures": [{
                "disclosure_type": "risk_factor", "title": "Commodity prices",
                "body_text": "Results are exposed to commodity-price volatility.",
                "language": "en", "published_at": "2026-03-01",
                "metadata": {"page": 80, "quote": "commodity-price volatility"},
            }],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _archive_index(self):
        content = b"%PDF-1.7 official archived source"
        document = self.raw / "SA" / "TST" / "documents" / "official.pdf"
        document.parent.mkdir(parents=True)
        document.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        index = self.raw / "archive-index.json"
        index.write_text(json.dumps({
            "schema_version": 1,
            "artifacts": [{
                "artifact_key": f"artifact:sa:TST:{digest}",
                "company_id": "sa:TST",
                "source_url": "https://issuer.example/reports/2025.pdf",
                "content_hash": digest,
                # Deliberately emulate an archive index committed from Windows;
                # Linux must treat these as directory separators, not filename text.
                "local_path": document.relative_to(self.root).as_posix().replace("/", "\\"),
                "content_type": "application/pdf",
                "metadata": {"manifests": ["test-2025.json"], "immutable": True},
            }],
        }), encoding="utf-8")
        return index

    def test_windows_archive_path_normalizes_portably_for_linux_deploys(self):
        normalized = _index_local_path(r"data\raw\SA\TST\documents\official.pdf")
        self.assertEqual(
            normalized.parts,
            ("data", "raw", "SA", "TST", "documents", "official.pdf"),
        )

    def _durable_counts(self):
        db = Database(self.database)
        try:
            tables = (
                "source_documents", "source_artifacts", "source_artifact_links",
                "extracted_facts", "mapped_facts", "normalized_facts", "data_points",
                "observations", "company_attributes", "company_attribute_evidence",
                "disclosures", "publication_batches", "pipeline_runs",
            )
            counts = {
                table: db.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in tables
            }
            counts["data_point_versions"] = db.conn.execute(
                "SELECT COALESCE(sum(version),0) FROM data_points"
            ).fetchone()[0]
            counts["attribute_versions"] = db.conn.execute(
                "SELECT COALESCE(sum(version),0) FROM company_attributes"
            ).fetchone()[0]
            counts["disclosure_versions"] = db.conn.execute(
                "SELECT COALESCE(sum(version),0) FROM disclosures"
            ).fetchone()[0]
            return counts
        finally:
            db.close()

    def test_sync_applies_numeric_domains_archive_and_is_operationally_idempotent(self):
        manifest = self._manifest()
        archive_index = self._archive_index()
        backups = self.root / "backups"
        kwargs = {
            "database": self.database,
            "imports_dir": self.imports,
            "registry_path": self.registry,
            "raw_dir": self.root / "runtime-raw",
            "manifest_paths": [manifest],
            "archive_index": archive_index,
            "project_root": self.root,
            "backup_dir": backups,
        }

        first = sync_reviewed_manifests(**kwargs)
        self.assertEqual(first["published_manifests"], 1)
        self.assertEqual(first["integrity"], "ok")
        self.assertEqual(first["verification"]["failures"], 0)
        self.assertIsNotNone(first["backup"])
        self.assertTrue(Path(first["backup"]["backup"]).is_file())
        self.assertEqual(first["companies"][0]["company_id"], "sa:TST")
        self.assertIn("understanding_score", first["companies"][0])

        db = Database(self.database)
        try:
            fact = db.conn.execute(
                "SELECT value_decimal,version,is_current FROM data_points "
                "WHERE company_id='sa:TST' AND metric_key='revenue'"
            ).fetchone()
            attribute = db.conn.execute(
                "SELECT value_json,version FROM company_attributes "
                "WHERE company_id='sa:TST' AND attribute_key='business_model'"
            ).fetchone()
            link = db.conn.execute(
                "SELECT count(*) FROM source_artifact_links l "
                "JOIN source_artifacts a USING(artifact_key) "
                "WHERE a.content_type='application/pdf'"
            ).fetchone()[0]
        finally:
            db.close()
        self.assertEqual((fact["value_decimal"], fact["version"], fact["is_current"]),
                         ("1000", 1, 1))
        self.assertEqual(json.loads(attribute["value_json"]), "Integrated energy company")
        self.assertEqual(attribute["version"], 1)
        self.assertEqual(link, 1)

        before = self._durable_counts()
        second = sync_reviewed_manifests(**kwargs)
        after = self._durable_counts()
        self.assertEqual(second["published_manifests"], 0)
        self.assertEqual(second["duplicate_manifests"], 1)
        self.assertIsNone(second["backup"])
        self.assertEqual(after, before)

    def test_domain_only_manifest_is_a_publishable_reviewed_source(self):
        manifest = self._manifest("test-governance.json", facts=False)
        result = sync_reviewed_manifests(
            self.database, self.imports, self.registry, self.root / "runtime-raw",
            [manifest], archive_index=None, project_root=self.root,
        )
        self.assertEqual(result["published_manifests"], 1)
        db = Database(self.database)
        try:
            source = db.conn.execute(
                "SELECT status FROM source_documents WHERE source_key=?",
                (result["results"][0]["source_key"],),
            ).fetchone()
            counts = (
                db.conn.execute("SELECT count(*) FROM company_attributes").fetchone()[0],
                db.conn.execute("SELECT count(*) FROM disclosures").fetchone()[0],
                db.conn.execute("SELECT count(*) FROM data_points").fetchone()[0],
            )
        finally:
            db.close()
        self.assertEqual(source["status"], "published")
        self.assertEqual(counts, (1, 1, 0))

    def test_failed_preflight_leaves_live_database_untouched(self):
        manifest = self._manifest()
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["facts"][0]["metric"] = "unreviewed mystery number"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        before = self._durable_counts()
        with self.assertRaisesRegex(ValueError, "verification failed before publication"):
            sync_reviewed_manifests(
                self.database, self.imports, self.registry, self.root / "runtime-raw",
                [manifest], archive_index=None, project_root=self.root,
            )
        self.assertEqual(self._durable_counts(), before)


if __name__ == "__main__":
    unittest.main()
