"""Publish only reconciled non-conflicting SAB stocks, with explicit omissions."""
import json
from decimal import Decimal
from pathlib import Path
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector
from finengine.verification import ManifestVerifier

root = Path('/app/state/reports/sab-period-correction-review/datapack-review')
digest = '76acffa163e24985e1c3b9ea9a2d986656291d3698da73b3608df030956c5d0c'
key = 'document:sa:1060:' + digest
review = json.loads((root / 'review-checkpoint.json').read_text())
manifest = json.loads((root / 'sab-q2-2026-stocks.json').read_text())
assert review['verify']['failures'] == 0
bad = {r['period_end'] for r in review['source_arithmetic'] if not r['within_source_thousand_precision']}
conflicts = {(r['metric'], r['period_end']) for r in review['current_conflicts']}
included, excluded = [], []
for fact in manifest['facts']:
    if fact['period_end'] in bad:
        excluded.append({**fact, 'reason': 'Source totals exceed source-precision reconciliation; retain in review.'})
    elif (fact['metric'], fact['period_end']) in conflicts:
        excluded.append({**fact, 'reason': 'Differs from current filing; source-authority/restatement review required.'})
    else:
        included.append(fact)
assert len(included) == 244 and len(excluded) == 79
manifest['facts'], manifest['excluded_facts'] = included, excluded
manifest['publication_scope'] = 'Partial balance-sheet stocks only; income, segments and 79 excluded stock values remain under review.'
path = root / 'sab-q2-2026-verified-subset.json'
path.write_text(json.dumps(manifest, indent=2))
verification = ManifestVerifier(root).verify(prefix=path.stem)
assert verification['ok'] and not verification['unmapped_labels']
db = Database('/app/state/financial.sqlite3', initialize=False)
backup = root / 'before-subset-publication.json'
assert not backup.exists(), 'Inspect previous attempt before repeating'
before = [dict(r) for r in db.conn.execute("SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1 AND is_calculated=0")]
current = {(r['metric_key'], r['period_end'], r['period_kind']): r for r in before
           if r['scope'] == 'consolidated' and r['dimensions_json'] == '{}'}
for fact in included:
    previous = current.get((fact['metric'], fact['period_end'], fact['period_kind']))
    assert not previous or Decimal(previous['value_decimal']) == Decimal(fact['value']) * Decimal(fact['scale']), 'Data changed since review'
source = dict(db.stored_source(key))
backup.write_text(json.dumps({'source': source, 'raw_current_points': before}, indent=2))
company = CompanyRegistry.combined(db.conn, '/app/config/companies.json').get('sa:1060')
with db.conn:
    db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?", (key,))
result = Pipeline(db, root / 'subset-publication-artifacts').run(
    company, LocalFileConnector(path, source['source_url'], source_key=key))
assert result['status'] == 'published', result
for fact in included:
    rows = db.conn.execute("SELECT value_decimal FROM data_points WHERE company_id='sa:1060' AND metric_key=? AND period_end=? AND period_kind=? AND scope='consolidated' AND dimensions_json='{}' AND is_current=1", (fact['metric'], fact['period_end'], fact['period_kind'])).fetchall()
    assert rows and all(Decimal(r[0]) == Decimal(fact['value']) * Decimal(fact['scale']) for r in rows), fact
# A successful partial publication must not hide the still-unread domains.
db.exception('sa:1060', key, 'extraction', 'datapack_partial_coverage',
             'Published verified non-conflicting stocks only. 79 stock values require reconciliation; income and segment rows are not yet mapped.')
report = {'publication': result, 'included_raw_facts': len(included),
          'excluded_raw_facts': len(excluded), 'verified_current_values': len(included),
          'source_complete': False, 'company_complete': False}
(root / 'subset-publication-result.json').write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(report, default=str), flush=True)
