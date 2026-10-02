"""Publish the verified SAB cash-flow addback without replacing its expense."""
import json
from pathlib import Path
from decimal import Decimal
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.pipeline import Pipeline
from finengine.connectors.file import LocalFileConnector

root = Path('/app/state/reports/sab-period-correction-review')
digest = '4c07523730a16faab0d77eb9ea7b8cdafdc44fe93b0dbf47bce04b849c77d4f6'
key = 'document:sa:1060:' + digest
manifest = root / (digest + '.manifest.json')
review = json.loads((root / (digest + '.review.json')).read_text())
assert review['verification']['ok']
facts = json.loads(manifest.read_text())['facts']
assert any(f['metric'] == 'depreciation_amortization_cash_flow' and
           Decimal(f['value']) * Decimal(f.get('scale', '1')) == Decimal('711910000')
           and f['period_end'] == '2025-12-31' for f in facts)
db = Database('/app/state/financial.sqlite3', initialize=False)
backup = root / 'before-cashflow-identity-publication.json'
assert not backup.exists(), 'Inspect previous attempt before repeating'
before = [dict(r) for r in db.conn.execute(
    "SELECT * FROM data_points WHERE company_id='sa:1060' AND is_current=1")]
backup.write_text(json.dumps(before, ensure_ascii=False, indent=2))
source = db.stored_source(key)
company = CompanyRegistry.combined(db.conn, '/app/config/companies.json').get('sa:1060')
with db.conn:
    db.conn.execute("UPDATE source_documents SET status='fetched' WHERE source_key=?", (key,))
result = Pipeline(db, root / 'cashflow-identity-artifacts').run(
    company, LocalFileConnector(manifest, source['source_url'], source_key=key))
assert result['status'] == 'published', result
verified = {}
for metric, expected in [('depreciation_amortization', '-711910000'),
                         ('depreciation_amortization_cash_flow', '711910000')]:
    rows = db.conn.execute("SELECT value_decimal FROM data_points WHERE company_id='sa:1060' AND metric_key=? AND period_end='2025-12-31' AND period_kind='fy' AND is_current=1", (metric,)).fetchall()
    assert rows and all(Decimal(r[0]) == Decimal(expected) for r in rows), (metric, rows)
    verified[metric] = expected
report = {'publication': result, 'verified_values': verified,
          'current_before': len(before), 'current_after': db.conn.execute(
              "SELECT count(*) FROM data_points WHERE company_id='sa:1060' AND is_current=1").fetchone()[0],
          'company_completeness_approved': False}
(root / 'cashflow-identity-publication-result.json').write_text(json.dumps(report, indent=2, default=str))
print(json.dumps(report, default=str), flush=True)
