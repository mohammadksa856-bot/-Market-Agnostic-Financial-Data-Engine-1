"""Company-by-company source inventory. No production writes or approvals."""
import argparse
import collections
import datetime
import hashlib
import json
import re
import sqlite3
from pathlib import Path
import pymupdf
try:
    from finengine.document_period import annual_period_from_text
except ImportError:
    # The persistent read-only audit container carries this tested helper
    # beside the script, independently of the production image version.
    from document_period import annual_period_from_text


def run(company_id):
    db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.execute('BEGIN')
    sources = list(db.execute('SELECT * FROM source_documents WHERE company_id=? ORDER BY source_key', (company_id,)))
    facts = collections.defaultdict(list)
    for row in db.execute('SELECT * FROM data_points WHERE company_id=? AND is_current=1 AND is_calculated=0', (company_id,)):
        facts[row['source_key']].append(dict(row))
    exceptions = collections.defaultdict(list)
    for row in db.execute("SELECT source_key,code,message FROM exceptions WHERE company_id=? AND status='open'", (company_id,)):
        exceptions[row['source_key']].append(dict(row))
    out = Path('/app/state/reports/company-audits') / company_id.replace(':', '-')
    out.mkdir(parents=True, exist_ok=True)
    counts = collections.Counter()
    evidence_dir = out / 'source-evidence-v1'
    evidence_dir.mkdir(exist_ok=True)
    headings = {
        'balance_sheet': r'(?:consolidated\s+)?statement\s+of\s+financial\s+position',
        'income_statement': r'(?:consolidated\s+)?statement\s+of\s+(?:income|profit\s+or\s+loss)',
        'cash_flow': r'(?:consolidated\s+)?statement\s+of\s+cash\s+flows?',
    }
    ledger = []
    for source in sources:
        key = source['source_key']
        evidence_path = evidence_dir / (hashlib.sha256(key.encode()).hexdigest() + '.json')
        evidence = {'source_key': key, 'content_hash': source['content_hash'],
                    'source_url': source['source_url'], 'local_path': source['local_path'],
                    'archive_check': 'not_checked', 'correctness_approved': False,
                    'completeness_approved': False}
        reusable = False
        if evidence_path.exists():
            cached = json.loads(evidence_path.read_text())
            if cached.get('content_hash') == source['content_hash']:
                evidence = cached
                reusable = True
        if not reusable:
            try:
                path = Path(source['local_path'] or '')
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                evidence['archive_check'] = 'matched' if digest == source['content_hash'] else 'hash_mismatch'
                if source['content_type'] == 'application/pdf':
                    with pymupdf.open(path) as doc:
                        cover = '\n'.join(doc[i].get_text() for i in range(min(3, len(doc))))
                        period = annual_period_from_text(cover)
                        evidence['cover_period'] = period
                        evidence['cover_excerpt'] = cover[:2000]
                        evidence['pages'] = len(doc)
                        evidence['statement_heading_candidates'] = {name: [] for name in headings}
                        evidence['textless_pages'] = []
                        for i, page in enumerate(doc):
                            text = page.get_text()
                            if sum(c.isalpha() for c in text) < 20:
                                evidence['textless_pages'].append(i + 1)
                            for name, pattern in headings.items():
                                if re.search(pattern, text[:2500], re.I):
                                    evidence['statement_heading_candidates'][name].append(i + 1)
                        evidence['note'] = 'Heading candidates can include contents or notes; textless pages need OCR. No approval inferred.'
            except Exception as error:
                evidence.update(archive_check='inspection_error', error=str(error))
            evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        current = facts.get(key, [])
        period = evidence.get('cover_period')
        later = sorted({f['period_end'] for f in current if period and f['period_end'] > period[0]})
        row = {**evidence, 'source_status': source['status'], 'current_points': len(current),
               'current_periods': sorted({(f['period_end'], f['period_kind']) for f in current}),
               'current_metrics': sorted({f['metric_key'] for f in current}),
               'published_later_than_annual_cover': later,
               'open_exceptions': exceptions.get(key, []),
               'value_unit_scope_match': 'pending_independent_review',
               'all_statement_lines_accounted_for': 'pending_review'}
        ledger.append(row)
        counts[source['status']] += 1
        counts['period_mismatch_sources'] += bool(later)
        counts['archive_' + evidence['archive_check']] += 1
        print(json.dumps({'company': company_id, 'checked': len(ledger), 'total': len(sources), 'source': key}), flush=True)
    (out / 'source-ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2))
    summary = {'company_id': company_id, 'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'sources': len(sources), 'counts': dict(counts),
               'company_state': 'review_in_progress', 'correctness_approved': False,
               'completeness_approved': False, 'production_modified': False}
    (out / 'checkpoint.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    db.close()
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('company_id')
    run(parser.parse_args().company_id)
