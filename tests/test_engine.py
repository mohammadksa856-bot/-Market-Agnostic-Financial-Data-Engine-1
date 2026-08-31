import json, tempfile, unittest
from decimal import Decimal
from pathlib import Path
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

if __name__=="__main__": unittest.main()
