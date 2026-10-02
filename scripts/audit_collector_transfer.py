"""Compare archived bytes with the collector's recorded SHA-256 inventory."""
import hashlib
import json
import sqlite3
from pathlib import Path

db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
inventory = Path('/tmp/final-sa-collector-inventory.jsonl')
result = {'checked': 0, 'matched': 0, 'missing': [], 'mismatched': []}
for line in inventory.read_text().splitlines():
    row = json.loads(line)
    result['checked'] += 1
    paths = db.execute(
        'SELECT local_path FROM source_documents WHERE company_id=? AND content_hash=?',
        (row['company_id'], row['content_hash']),
    ).fetchall()
    existing = [Path(p[0]) for p in paths if p[0] and Path(p[0]).is_file()]
    if not existing:
        result['missing'].append({'company_id': row['company_id'], 'hash': row['content_hash']})
        continue
    path = existing[0]
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != row['content_hash'] or path.stat().st_size != row['byte_size']:
        result['mismatched'].append({'company_id': row['company_id'], 'path': str(path)})
    else:
        result['matched'] += 1
    if result['checked'] % 500 == 0:
        print(json.dumps({k: result[k] for k in ('checked', 'matched')}), flush=True)
out = Path('/app/state/reports/sa-transfer-byte-audit.json')
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
