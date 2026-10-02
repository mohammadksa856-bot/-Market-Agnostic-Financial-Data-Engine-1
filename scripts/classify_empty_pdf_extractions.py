"""Inspect unique no-fact PDFs without changing sources or production data."""
import collections
import json
import sqlite3
from pathlib import Path
import pymupdf

db = sqlite3.connect('file:/app/state/financial.sqlite3?mode=ro', uri=True)
sources = {}
for key, payload in db.execute("SELECT source_key,payload_json FROM exceptions WHERE status='open' AND code='pdf_extraction_failed' AND company_id LIKE 'sa:%'"):
    data = json.loads(payload)
    if any(check.get('check') == 'manifest contains source facts' for check in data.get('verify_detail', [])):
        sources[key] = data.get('local_path')
counts = collections.Counter()
out = Path('/app/state/reports/sa-empty-pdf-classification.jsonl')
with out.open('w') as handle:
    for key, path in sources.items():
        try:
            with pymupdf.open(path) as doc:
                text = '\n'.join(page.get_text() for page in doc)
                letters = sum(char.isalpha() for char in text)
                arabic = sum('\u0600' <= char <= '\u06ff' for char in text)
                if letters < max(100, len(doc) * 20):
                    cause = 'needs_ocr_or_font_recovery'
                elif arabic > letters / 2:
                    cause = 'arabic_text_reader_review'
                elif 'pillar iii' in text[:6000].lower() or 'pillar 3' in text[:6000].lower():
                    cause = 'regulatory_disclosure_reader_review'
                else:
                    cause = 'statement_layout_or_document_classification_review'
                row = {'source_key': key, 'path': path, 'pages': len(doc), 'letters': letters, 'arabic_chars': arabic, 'root_cause_hint': cause}
        except Exception as error:
            row = {'source_key': key, 'path': path, 'root_cause_hint': 'file_open_failed', 'error': str(error)}
        counts[row['root_cause_hint']] += 1
        handle.write(json.dumps(row) + '\n')
        if sum(counts.values()) % 100 == 0:
            handle.flush()
            print(json.dumps({'inspected': sum(counts.values()), 'total': len(sources), 'counts': dict(counts)}), flush=True)
summary = {'inspected': sum(counts.values()), 'total': len(sources), 'counts': dict(counts), 'note': 'Diagnostic routing hints only; no sources approved or excluded.'}
Path('/app/state/reports/sa-empty-pdf-classification-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary), flush=True)
