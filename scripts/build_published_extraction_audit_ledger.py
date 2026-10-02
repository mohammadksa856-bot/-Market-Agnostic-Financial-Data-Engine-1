"""Read-only inventory for independent audits; publishing is NOT audit approval."""
import argparse
import collections
import datetime
import json
import sqlite3
from pathlib import Path


def build(db_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(Path(db_path).resolve().as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA query_only=ON')
    conn.execute('BEGIN')  # One consistent snapshot, without changing production.
    points = {r['source_key']: dict(r) for r in conn.execute('''
        SELECT source_key, count(*) AS versions,
        sum(is_current) AS current_points,
        count(DISTINCT metric_key) AS metrics
        FROM data_points WHERE company_id LIKE 'sa:%' AND is_calculated=0
        GROUP BY source_key''')}
    extracted = {r['source_key']: dict(r) for r in conn.execute('''
        SELECT source_key, count(*) AS extracted_rows,
        sum(CASE WHEN page IS NULL AND coalesce(table_ref,'')=''
            AND location_json IN ('{}','') THEN 1 ELSE 0 END) AS unlocated_rows
        FROM extracted_facts WHERE company_id LIKE 'sa:%' GROUP BY source_key''')}
    companies = set()
    counts = collections.Counter()
    path = output_dir / 'sa-published-extraction-audit-ledger.jsonl'
    with path.open('w', encoding='utf-8') as handle:
        for source in conn.execute("SELECT * FROM source_documents WHERE company_id LIKE 'sa:%' AND status='published' ORDER BY company_id,source_key"):
            key = source['source_key']
            companies.add(source['company_id'])
            meta = json.loads(source['metadata_json'])
            facts = extracted.get(key, {})
            issues = []
            if not source['source_url']:
                issues.append('missing_source_url')
            if facts.get('unlocated_rows', 0):
                issues.append('extracted_rows_without_page_table_or_location')
            row = {
                'source_key': key, 'company_id': source['company_id'],
                'source_url': source['source_url'], 'local_path': source['local_path'],
                'content_hash': source['content_hash'], 'reader': meta.get('reader'),
                'filing_type': source['filing_type'],
                'published_counts': points.get(key, {}), 'extraction_counts': facts,
                'preliminary_provenance_flags': issues,
                'correctness_audit': 'not_audited',
                'document_completeness_audit': 'not_audited',
                'company_period_coverage_audit': 'not_audited',
                'required_checks': ['independent_source_value_match',
                    'currency_unit_scale_sign', 'period_scope_restatement',
                    'statement_page_and_unmapped_line_inventory',
                    'rebuild_and_published_version_comparison',
                    'financial_reconciliation', 'historical_period_coverage'],
            }
            counts['sources'] += 1
            counts['sources_with_preliminary_flags'] += bool(issues)
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    conn.close()
    summary = {'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'companies': len(companies), **dict(counts),
               'correctness_approved': 0, 'completeness_approved': 0,
               'note': 'Inventory only. All published sources remain pending independent correctness and completeness audits. Counts are not completeness percentages.'}
    (output_dir / 'sa-published-extraction-audit-summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='/app/state/financial.sqlite3')
    parser.add_argument('--output-dir', default='/app/state/reports')
    args = parser.parse_args()
    print(json.dumps(build(args.db, args.output_dir), ensure_ascii=False), flush=True)
