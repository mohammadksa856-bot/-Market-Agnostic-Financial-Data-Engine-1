"""Persist issuer evidence distinguishing restatement from presentation mismatch."""
import hashlib
import json
from pathlib import Path
import pymupdf
from finengine.database import Database

root=Path('/app/state/reports/sab-period-correction-review')
output=root/'restatement-presentation-evidence-v1.json'
assert not output.exists(),'Preserve existing independent audit'
digest='71bebafc0e248e3ea46ee0de02a434a7fa5aa6838b3e32d6abea423717304b7c'
db=Database('/app/state/financial.sqlite3',initialize=False)
source=dict(db.stored_source('document:sa:1060:'+digest))
assert hashlib.sha256(Path(source['local_path']).read_bytes()).hexdigest()==source['content_hash']
doc=pymupdf.open(source['local_path'])
note=doc[32].get_text()
assert 'corrected the valuation' in note and 'IAS 8' in note and '1,160,570' in note
equity=doc[6].get_text()
assert '31 March 2025' in equity and 'Restated' in equity
assert all(value in equity for value in ['13,710,716','17,559,617','2,054,795'])
report={'company_id':'sa:1060','source_key':source['source_key'],'source_url':source['source_url'],
        'content_hash':digest,'note_page':33,'equity_page':7,'note_text':note,'equity_text':equity,
        'issuer_error_correction_SAR_thousand':{'FVOCI':918484,'FVSI':242086,'total':1160570},
        'presentation_cases':[
            {'period_end':'2025-03-31','reported_retained_earnings_restated':13710716,
             'proposed_dividends_separate':2054795,'supplement_retained_earnings':15765511},
            {'period_end':'2026-03-31','reported_retained_earnings':17559617,
             'proposed_dividends_separate':2054795,'supplement_retained_earnings':19614412}],
        'financial_data_modified':False,'company_complete':False,
        'next_gate':'Version-preserving remapping of the two aggregated retained-earnings values, then dependent metric recalculation. Do not replace restated assets/equity with earlier original values.'}
assert 918484+242086==1160570
for row in report['presentation_cases']:
    retained=row.get('reported_retained_earnings',row.get('reported_retained_earnings_restated'))
    assert retained+row['proposed_dividends_separate']==row['supplement_retained_earnings']
output.write_text(json.dumps(report,indent=2))
db.exception('sa:1060','document:sa:1060:76acffa163e24985e1c3b9ea9a2d986656291d3698da73b3608df030956c5d0c',
             'mapping','retained_earnings_includes_proposed_dividends',
             '2025-Q1 and 2026-Q1 supplement retained earnings include a separately disclosed proposed dividend; see source equity page 7 and audit evidence.',
             payload={'evidence_path':str(output),'cases':report['presentation_cases']})
print(json.dumps({'evidence_saved':str(output),'presentation_cases':2,'restatement_explained':True,'financial_data_modified':False}),flush=True)
