"""Record visually reviewed predecessor covers without moving or deleting facts."""
import datetime
import hashlib
import json
import sqlite3
from pathlib import Path

periods = {
    '4e820fa156586e10daf62c78384e04a30618a50b17d4c8e013bc3faa5e8525b3': '2012-12-31',
    'c4e8d970e0ba5a39b59075b93e843198f8875a4d242a879d6aa133801119c670': '2011-09-30',
    '5b31acdea006a3c1c244b45b2199d0ce15f6e073f300e11ad5605f25d523f2aa': '2011-12-31',
    '7d087610ea81106b633223ea34ba03b50f210a6dd4e91d9160fc3034889f6700': '2011-06-30',
    'e324982a67288d99798950f96326c34e118520614310a2f143ce5f337b62d513': '2011-03-31',
    '8a788ea3fc0756df5073015541c2e0b5730e6b4def52e8f021b3b305220d5d56': '2011-09-30',
}
db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
db.row_factory = sqlite3.Row
db.execute('BEGIN')
results = []
for digest, end in periods.items():
    key = 'document:sa:1060:' + digest
    source = db.execute('SELECT * FROM source_documents WHERE source_key=?', (key,)).fetchone()
    assert source and hashlib.sha256(Path(source['local_path']).read_bytes()).hexdigest() == digest
    points = db.execute('SELECT count(*) FROM data_points WHERE source_key=? AND is_current=1', (key,)).fetchone()[0]
    results.append({'source_key': key, 'source_url': source['source_url'],
                    'document_entity': 'Saudi Hollandi Bank', 'cover_period_end': end,
                    'cover_page': 1, 'inspection': 'independent_visual_cover_review',
                    'rendered_evidence': '/app/state/reports/sab-period-correction-review/interim-covers/' + digest + '.png',
                    'archive_hash_matched': True, 'current_points': points,
                    'decision': 'requires_predecessor_entity_scope_review_before_publication',
                    'action': 'Keep archive; model predecessor identity separately, validate primary statements before any numeric publication.',
                    'correctness_approved': False, 'completeness_approved': False})
db.close()
report = {'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'company_id': 'sa:1060', 'production_modified': False, 'sources': results}
out = Path('/app/state/reports/company-audits/sa-1060/predecessor-cover-review-20261002.json')
assert not out.exists(), 'Do not overwrite completed review'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report), flush=True)
