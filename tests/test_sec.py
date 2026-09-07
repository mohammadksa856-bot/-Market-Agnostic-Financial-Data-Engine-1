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

    def test_comparative_fact_uses_its_period_fiscal_year(self):
        payload={"facts":{"us-gaap":{"Revenues":{"units":{"USD":[
          {"start":"2024-01-01","end":"2024-03-31","val":100,"fy":2025,"fp":"Q1","form":"10-Q","filed":"2025-04-20","accn":"comparison"}]}}}}}
        c=Company("us:TST",Market.US,"TST","Test","USD",cik="1",fiscal_year_end="12-31")
        d=SourceDocument(c.company_id,c.market,"fixture://sec","sec:1","companyfacts","2025-04-20",json.dumps(payload).encode())
        facts,errors=JsonExtractor().extract(c,d)
        self.assertFalse(errors)
        self.assertEqual(facts[0].fiscal_year,2024)

    def test_non_calendar_fiscal_year_is_derived_from_period_end(self):
        self.assertEqual(JsonExtractor._fiscal_year(
            Company("us:TST",Market.US,"TST","Test","USD",fiscal_year_end="06-30"),
            "2024-09-29"),2025)

    def test_equity_including_nci_is_preferred_for_total_equity(self):
        rows=lambda value:[{"end":"2024-06-30","val":value,"fy":2024,"fp":"FY",
                            "form":"10-K","filed":"2024-09-01","accn":"same"}]
        payload={"facts":{"us-gaap":{
            "StockholdersEquity":{"units":{"USD":rows(100)}},
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest":{
                "units":{"USD":rows(110)}}}}}
        c=Company("us:TST",Market.US,"TST","Test","USD",cik="1",fiscal_year_end="06-30")
        d=SourceDocument(c.company_id,c.market,"fixture://sec","sec:1","companyfacts","2024-09-01",json.dumps(payload).encode())
        facts,errors=JsonExtractor().extract(c,d)
        self.assertFalse(errors)
        equity=[fact for fact in facts if fact.metric=="total_equity"]
        self.assertEqual((len(equity),str(equity[0].value)),(1,"110"))

if __name__=="__main__": unittest.main()
