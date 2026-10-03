"""Build docs/audits/saudi-independent/defect-bundle.json and .md from the six batch records.
Offline, read-only on data/**, never edits the per-batch records (copies live in bundle/<batch>/).
Run from repo root:  PYTHONPATH=docs/audits/saudi-independent/tools python docs/audits/saudi-independent/tools/bundle_build.py
"""
import json, os, re, sys, subprocess
from bundle_lib import *
from bundle_curated import curated
from bundle_adapters import adapt_all, finalize

OUT = os.path.join(REPO, 'docs/audits/saudi-independent')

def main():
    recs = []
    recs += curated()
    recs += adapt_all(existing=recs)
    recs = finalize(recs)
    proven = [r for r in recs if r['status'] == 'proven']
    suspected = [r for r in recs if r['status'] == 'suspected']
    doc = {
        'schema_version': 1,
        'title': 'Unified Saudi audit defect bundle (batches 1-A, 1-B, 1-C, 1-D, 2-E, 2-F)',
        'base': 'origin/codex/telecom-95pct @ ec610f3',
        'status_rule': ('proven = the bundle auditor re-checked the defect itself against the archived source file '
                        '(rendered page read and/or text layer, and the published value read from the manifest in data/imports); '
                        'suspected = proven only in a batch record, or source file not available offline, or check not possible.'),
        'priority_order': PRIORITY_LABELS,
        'counts': {'proven': len(proven), 'suspected': len(suspected), 'total': len(recs)},
        'proven': proven,
        'suspected': suspected,
    }
    json.dump(doc, open(os.path.join(OUT, 'defect-bundle.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    from bundle_md import write_md
    write_md(doc, os.path.join(OUT, 'defect-bundle.md'))
    print(doc['counts'])

from bundle_lib import PRIORITY_LABELS
if __name__ == '__main__':
    main()
