import json, unittest
from finengine.extraction import JsonExtractor
from finengine.models import Company, Market, SourceDocument, PeriodKind

class SecTests(unittest.TestCase):
    def test_sec_mapping_period_and_latest_accession(self):
        payload={"facts":{"us-gaap":{"Revenues":{"units":{"USD":[
          {"start":"2024-01-01","end":"2024-03-31","val":100,"fy":2024,"fp":"Q1","form":"10-Q","filed":"2024-04-20","accn":"old"},
          {"start":"2024-01-01","end":"2024-03-31","val":101,"fy":2024,"fp":"Q1","form":"10-Q","filed":"2024-04-21","accn":"new"}]}}}}}
        c=Company("us:TST",Market.US,"TST","Test","USD",cik="1"); d=SourceDocument(c.company_id,c.market,"fixture://sec","sec:1","companyfacts","2024-04-21",json.dumps(payload).encode())
        facts,errors=JsonExtractor().extract(c,d); self.assertFalse(errors); self.assertEqual(len(facts),1); self.assertEqual(facts[0].metric,"revenue"); self.assertEqual(facts[0].period_kind,PeriodKind.QUARTER); self.assertEqual(str(facts[0].value),"101")

if __name__=="__main__": unittest.main()
