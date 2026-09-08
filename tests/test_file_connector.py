import json, tempfile, unittest
from pathlib import Path
from finengine.connectors import LocalFileConnector
from finengine.models import Company, Market

class FileConnectorTests(unittest.TestCase):
    def test_local_file_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"filing.json"; p.write_text(json.dumps({"filed_at":"2026-01-01","facts":{}}))
            c=Company("us:TST",Market.US,"TST","Test","USD",cik="1")
            doc=LocalFileConnector(p,"https://www.sec.gov/example").fetch(c)
            self.assertEqual(doc.source_url,"https://www.sec.gov/example")
            self.assertTrue(doc.source_key.startswith("file:"))
            self.assertEqual(doc.filed_at,"2026-01-01")

    def test_local_manifest_can_retain_archived_document_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"manifest.json"
            p.write_text(json.dumps({"filed_at":"2026-01-01","facts":{}}))
            c=Company("sa:2082",Market.SA,"2082","ACWA","SAR")
            key="document:sa:2082:abc123"
            doc=LocalFileConnector(p,"https://issuer.example/report.pdf",key).fetch(c)
            self.assertEqual(doc.source_key,key)

if __name__=="__main__": unittest.main()
