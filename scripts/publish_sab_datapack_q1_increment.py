"""Publish only the Q1 vintage's independently reconciled extra stock date."""
import json
from decimal import Decimal
from pathlib import Path
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector
from finengine.verification import ManifestVerifier

root = Path('/app/state/reports/sab-period-correction-review/datapack-review')
key = 'document:sa:1060:300a90f7b1ead3c808e7533087326f82bb137678422d8e8e438720f627f8aee7'
manifest = json.loads((root / 'sab-q1-2026-stocks.json').read_text())
newer = json.loads((root / 'sab-q2-2026-stocks.json').read_text())
newer_values = {(f['metric'], f['period_end']): Decimal(f['value']) for f in newer['facts']}
included, excluded = [], []
for fact in manifest['facts']:
    identity = (fact['metric'], fact['period_end'])
    if identity not in newer_values:
        included.append(fact)
    else:
        assert newer_values[identity] == Decimal(fact['value'])
        excluded.append({**fact, 'reason': 'Same stock value in newer Q2 vintage; keep archived without republishing.'})
assert len(included) == 19 and {f['period_end'] for f in included} == {'2022-03-31'}
values = {f['metric']: Decimal(f['value']) * Decimal(f['scale']) for f in included}
assert abs(values['total_assets'] - values['total_liabilities'] - values['total_equity']) <= Decimal('1500')
assert values['total_assets'] == values['total_liabilities_equity']
manifest['facts'], manifest['excluded_facts'] = included, excluded
manifest['publication_scope'] = 'Incremental 2022-Q1 balance sheet only; other dates retained from newer vintage; income/segments not mapped.'
path = root / 'sab-q1-2026-increment.json'
path.write_text(json.dumps(manifest, indent=2))
verify = ManifestVerifier(root).verify(prefix=path.stem)
assert verify['ok'] and not verify['unmapped_labels']
db = Database('/app/state/financial.sqlite3', initialize=False)
before = [dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1")]
current = {(r['metric_key'],r['period_end'],r['period_kind']): r for r in before
           if r['scope']=='consolidated' and r['dimensions_json']=='{}'}
for fact in included:
    row = current.get((fact['metric'],fact['period_end'],fact['period_kind']))
    assert not row or Decimal(row['value_decimal']) == values[fact['metric']], 'Conflicting current value requires review'
backup = root / 'before-q1-increment-publication.json'
assert not backup.exists(), 'Inspect previous attempt before repeating'
source = dict(db.stored_source(key))
backup.write_text(json.dumps({'source':source,'company_current':before},indent=2))
company = CompanyRegistry.combined(db.conn,'/app/config/companies.json').get('sa:1060')
with db.conn:
    db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?",(key,))
result = Pipeline(db,root/'q1-increment-artifacts').run(company,LocalFileConnector(path,source['source_url'],source_key=key))
assert result['status']=='published',result
after = {(r['metric_key'],r['period_end'],r['period_kind']):r for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND scope='consolidated' AND dimensions_json='{}'")}
for fact in included:
    assert Decimal(after[fact['metric'],fact['period_end'],fact['period_kind']]['value_decimal'])==values[fact['metric']]
db.exception('sa:1060',key,'extraction','datapack_partial_coverage',
             'Published only incremental 2022-Q1 stocks. Income/segment mappings remain incomplete; 304 stocks retained through newer vintage.')
report={'publication':result,'verified_raw_values':len(included),'duplicate_vintage_values_not_republished':len(excluded),
        'current_before':len(before),'current_after':db.conn.execute("SELECT count(*) FROM data_points WHERE company_id='sa:1060' AND is_current=1").fetchone()[0],
        'company_complete':False,'source_complete':False}
(root/'q1-increment-publication-result.json').write_text(json.dumps(report,indent=2,default=str))
print(json.dumps(report,default=str),flush=True)
