"""Stage rejected text-layer interim reports without modifying production."""
import json
from pathlib import Path
from finengine import cli
from finengine.database import Database
from finengine.registry import CompanyRegistry

hashes = ['2ebc4b865d5762698af873864e54a63aa3253b4e77ceec09913c536e139d2a00',
          '31dd72c0bb12023c5657736175f6fcb5b0de00f6bc05f67a00b27b7dc129f9b6',
          '71bebafc0e248e3ea46ee0de02a434a7fa5aa6838b3e32d6abea423717304b7c',
          'f305d8f91e4d579c92391b31c4643e36714113d95b86b62ae0691a82717f92d6']
root = Path('/app/state/reports/sab-period-correction-review/interim-batch-v1')
root.mkdir(exist_ok=True)
db = Database('/app/state/financial.sqlite3', initialize=False)
db.conn.execute('PRAGMA query_only=ON')
company = CompanyRegistry.combined(db.conn, '/app/config/companies.json').get('sa:1060')
for digest in hashes:
    output = root / (digest + '.review.json')
    if output.exists():
        print(output.read_text(), flush=True)
        continue
    source = db.stored_source('document:sa:1060:' + digest)
    result = {'source_key': source['source_key'], 'production_modified': False}
    try:
        result['resolved_period'] = cli._source_period(source, company)
        manifest, report, reader = cli._read_pdf_manifest(Path(source['local_path']), company, source, False)
        result.update(reader=reader, verification=report, facts=len(manifest.get('facts', [])))
        (root/(digest+'.manifest.json')).write_text(json.dumps(manifest, indent=2, default=str))
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
    output.write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps(result, default=str), flush=True)
