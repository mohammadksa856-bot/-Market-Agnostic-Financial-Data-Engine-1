"""Stage and verify SAB corrections before touching production or readers."""
import json
from pathlib import Path
from finengine.database import Database
from finengine.registry import CompanyRegistry
from finengine.document_period import annual_cover_period
from finengine import cli

HASHES = [
    '4c07523730a16faab0d77eb9ea7b8cdafdc44fe93b0dbf47bce04b849c77d4f6',
    '037d1400f403063c337058b9d42295a046a166a0877a45209934bf4fe928b562',
    '96230175ef2957c0dd0e18de3fbd5eb0d80559edd7525d0bb6fa09fc10216d99',
]
original = cli._source_period


def corrected(row, company):
    return annual_cover_period(row['local_path']) or original(row, company)


cli._source_period = corrected
db = Database('/app/state/financial.sqlite3', initialize=False)
db.conn.execute('PRAGMA query_only=ON')
company = CompanyRegistry.combined(db.conn, '/app/config/companies.json').get('sa:1060')
out = Path('/app/state/reports/sab-period-correction-review')
out.mkdir(exist_ok=True)
for digest in HASHES:
    source = db.stored_source('document:sa:1060:' + digest)
    path = Path(source['local_path'])
    period = corrected(source, company)
    manifest, report, reader = cli._read_pdf_manifest(path, company, source, False)
    (out / (digest + '.manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    result = {'source_key': source['source_key'], 'period': period,
              'reader': reader, 'verification': report,
              'facts': len(manifest.get('facts', [])), 'production_modified': False}
    (out / (digest + '.review.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False), flush=True)
db.close()
