import json, tempfile, unittest
from decimal import Decimal
from pathlib import Path
from finengine.connectors.file import LocalFileConnector
from finengine.database import Database
from finengine.models import Company, Market, SourceDocument
from finengine.pipeline import Pipeline
from finengine.query import FinancialQueryService

class FakeConnector:
    def __init__(self,payload,key="fixture:1"): self.content=json.dumps(payload).encode(); self.key=key
    def fetch(self,c): return SourceDocument(c.company_id,c.market,"fixture://report",self.key,"financial-results","2025-03-01",self.content)

def sa_payload(revenue=1000):
    return {"period_end":"2024-12-31","filed_at":"2025-03-01","facts":[
      {"metric":"revenue","value":revenue,"period_start":"2024-01-01","period_end":"2024-12-31","period_kind":"fy","fiscal_year":2024},
      {"metric":"net income","value":100,"period_start":"2024-01-01","period_end":"2024-12-31","period_kind":"fy","fiscal_year":2024},
      {"metric":"total assets","value":2000,"period_end":"2024-12-31","period_kind":"instant","fiscal_year":2024},
      {"metric":"total liabilities","value":800,"period_end":"2024-12-31","period_kind":"instant","fiscal_year":2024},
      {"metric":"total equity","value":1200,"period_end":"2024-12-31","period_kind":"instant","fiscal_year":2024},
      {"metric":"net cash from operating activities","value":250,"period_start":"2024-01-01","period_end":"2024-12-31","period_kind":"fy","fiscal_year":2024},
      {"metric":"capital expenditure","value":-80,"period_start":"2024-01-01","period_end":"2024-12-31","period_kind":"fy","fiscal_year":2024}]}

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.dbpath=str(Path(self.t.name)/"db.sqlite3"); self.db=Database(self.dbpath); self.c=Company("sa:2222",Market.SA,"2222","Aramco","SAR")
    def tearDown(self): self.db.close(); self.t.cleanup()
    def test_pipeline_calculation_and_query(self):
        r=Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,FakeConnector(sa_payload())); self.assertEqual(r["status"],"published"); self.assertGreaterEqual(r["published"],9)
        q=FinancialQueryService(self.dbpath); h=q.metric_history("SA","2222","free_cash_flow"); q.close(); self.assertEqual(h[0]["value"],"170")
    def test_calculated_ratios_are_dimensionless(self):
        Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,FakeConnector(sa_payload()))
        rows=self.db.conn.execute("SELECT metric,currency,unit FROM observations WHERE metric IN ('net_margin','liabilities_to_equity') ORDER BY metric").fetchall()
        self.assertEqual([(row["metric"],row["currency"],row["unit"]) for row in rows],[
            ("liabilities_to_equity","","ratio"),("net_margin","","ratio")])
    def test_non_monetary_fact_with_explicit_unit_is_valid(self):
        payload={"period_end":"2024-12-31","filed_at":"2025-03-01","facts":[
            {"label":"supply reliability","value":99.9,"currency":"","unit":"percent","period_start":"2024-01-01","period_end":"2024-12-31","period_kind":"fy","fiscal_year":2024}]}
        result=Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,FakeConnector(payload,"fixture:operational"))
        self.assertEqual(result["status"],"published")
        row=self.db.conn.execute("SELECT metric,currency,unit,value FROM observations").fetchone()
        self.assertEqual((row["metric"],row["currency"],row["unit"],row["value"]),("supply_reliability","","percent","99.9"))
    def test_aramco_annual_metric_manifests_publish_and_restate(self):
        imports=Path(__file__).resolve().parents[1]/"data"/"imports"
        pipeline=Pipeline(self.db,Path(self.t.name)/"raw")
        for year in range(2021,2026):
            result=pipeline.run(self.c,LocalFileConnector(imports/f"aramco-{year}-annual-metrics.json"))
            self.assertEqual(result["status"],"published",year)
        current_roace=self.db.conn.execute("SELECT value,version FROM observations WHERE metric='roace' AND fiscal_year=2024 AND is_current=1").fetchone()
        current_eps=self.db.conn.execute("SELECT value,version FROM observations WHERE metric='eps_diluted' AND fiscal_year=2022 AND is_current=1").fetchone()
        self.assertEqual((current_roace["value"],current_roace["version"]),("21.1",2))
        self.assertEqual((current_eps["value"],current_eps["version"]),("2.47",2))
        count=self.db.conn.execute("SELECT count(*) FROM observations WHERE is_current=1").fetchone()[0]
        self.assertGreaterEqual(count,120)
    def test_idempotent_source(self):
        p=Pipeline(self.db,Path(self.t.name)/"raw"); p.run(self.c,FakeConnector(sa_payload())); r=p.run(self.c,FakeConnector(sa_payload())); self.assertEqual(r["status"],"duplicate")
    def test_restatement_versions(self):
        p=Pipeline(self.db,Path(self.t.name)/"raw"); p.run(self.c,FakeConnector(sa_payload(),"fixture:1")); r=p.run(self.c,FakeConnector(sa_payload(1100),"fixture:2")); self.assertGreater(r["restated"],0)
        rows=self.db.conn.execute("SELECT value,version,is_current FROM observations WHERE metric='revenue' ORDER BY version").fetchall(); self.assertEqual([(x["value"],x["version"],x["is_current"]) for x in rows],[("1000",1,0),("1100",2,1)])
    def test_validation_blocks_unbalanced(self):
        payload=sa_payload(); payload["facts"][4]["value"]=1000
        r=Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,FakeConnector(payload)); self.assertEqual(r["status"],"exception"); self.assertEqual(self.db.conn.execute("SELECT count(*) FROM exceptions").fetchone()[0],1)
    def test_staging_audit_trail_precedes_production(self):
        r=Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,FakeConnector(sa_payload()))
        self.assertEqual(r["staging"]["extracted"],7)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM extracted_facts").fetchone()[0],7)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM mapped_facts WHERE status='accepted'").fetchone()[0],7)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM normalized_facts WHERE status='published'").fetchone()[0],7)
        self.assertEqual(self.db.conn.execute("SELECT status FROM source_documents").fetchone()[0],"published")
    def test_unknown_mapping_never_reaches_production(self):
        payload=sa_payload(); payload["facts"].append({"label":"Brand new ambiguous metric","value":42,"period_end":"2024-12-31","period_kind":"fy","fiscal_year":2024})
        r=Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,FakeConnector(payload))
        self.assertEqual((r["status"],r["stage"]),("exception","mapping"))
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM observations").fetchone()[0],0)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM mapped_facts WHERE status='review'").fetchone()[0],1)
    def test_crashed_source_restarts_and_pipeline_run_is_audited(self):
        connector=FakeConnector(sa_payload(),"fixture:crash"); doc=connector.fetch(self.c)
        self.db.register_company(self.c); self.db.save_source(doc,"crash",None); self.db.set_source_status(doc.source_key,"extracting")
        result=Pipeline(self.db,Path(self.t.name)/"raw").run(self.c,connector)
        self.assertEqual(result["status"],"published")
        run=self.db.conn.execute("SELECT status,stage,source_key FROM pipeline_runs WHERE run_id=?",(result["run_id"],)).fetchone()
        self.assertEqual((run["status"],run["stage"],run["source_key"]),("published","complete","fixture:crash"))

if __name__=="__main__": unittest.main()
