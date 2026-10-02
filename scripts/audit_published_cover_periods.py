"""Independent, resumable cover-date checks. Never alters production data."""
import datetime
import hashlib
import json
import re
import sqlite3
from pathlib import Path
import pymupdf

MONTHS = ('January February March April May June July August September October November December').split()
PATTERN = re.compile(r'for\s+the\s+year\s+ended\s+(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(20\d{2})', re.I)


def cover_period(text):
    dates = set()
    for day, month, year in PATTERN.findall(text):
        try:
            dates.add(datetime.date(int(year), [m.lower() for m in MONTHS].index(month.lower()) + 1, int(day)).isoformat())
        except ValueError:
            pass
    return next(iter(dates)) if len(dates) == 1 else None


def main(limit=100):
    db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    out = Path('/app/state/reports/sa-published-cover-period-audit.jsonl')
    seen = set()
    if out.exists():
        for line in out.read_text().splitlines():
            row = json.loads(line)
            seen.add((row['source_key'], row['content_hash']))
    inspected = mismatches = 0
    with out.open('a', encoding='utf-8') as handle:
        for source in db.execute("""SELECT * FROM source_documents
            WHERE company_id LIKE 'sa:%' AND status='published'
            AND content_type='application/pdf'
            ORDER BY CASE WHEN company_id='sa:1060' THEN 0 ELSE 1 END, company_id,source_key"""):
            if (source['source_key'], source['content_hash']) in seen:
                continue
            row = {'source_key': source['source_key'], 'company_id': source['company_id'],
                   'content_hash': source['content_hash'], 'audit': 'cover_period_v1',
                   'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'correctness_approved': False, 'completeness_approved': False}
            try:
                path = Path(source['local_path'])
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest != source['content_hash']:
                    row.update(status='archive_hash_mismatch')
                else:
                    with pymupdf.open(path) as doc:
                        cover = doc[0].get_text() if len(doc) else ''
                    period = cover_period(cover)
                    row['cover_excerpt'] = cover[:1500]
                    row['cover_period_end'] = period
                    metadata = json.loads(source['metadata_json'])
                    row['metadata_title'] = metadata.get('title')
                    row['status'] = 'unresolved_cover_period'
                    if period:
                        dates = [r[0] for r in db.execute("""SELECT DISTINCT period_end FROM data_points
                            WHERE source_key=? AND is_calculated=0 AND is_current=1""", (source['source_key'],))]
                        row['current_published_periods'] = dates
                        later = [d for d in dates if d > period]
                        row['later_than_source_period'] = later
                        row['status'] = 'confirmed_period_mismatch' if later else 'no_later_period_detected'
                        mismatches += bool(later)
                        # This check cannot prove all values or periods are correct.
            except Exception as error:
                row.update(status='inspection_error', error=str(error))
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
            handle.flush()
            inspected += 1
            if inspected >= limit:
                break
    db.close()
    print(json.dumps({'inspected_this_run': inspected, 'period_mismatches_this_run': mismatches,
                      'report': str(out), 'production_modified': False}), flush=True)


if __name__ == '__main__':
    main()
