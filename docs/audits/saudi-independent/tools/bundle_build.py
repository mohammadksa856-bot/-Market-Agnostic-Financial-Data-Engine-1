"""Build docs/audits/saudi-independent/defect-bundle.json and .md from the six batch records.
Offline, read-only on data/**; never edits the per-batch records (copies live in bundle/<batch>/).
Run from the repo root:
  PYTHONIOENCODING=utf8 PYTHONPATH=docs/audits/saudi-independent/tools:src python docs/audits/saudi-independent/tools/bundle_build.py
"""
import json, os
from bundle_lib import *
from bundle_curated import curated
from bundle_adapters_all import adapt_all
from bundle_final import finalize, write_md

OUT = os.path.join(REPO, 'docs/audits/saudi-independent')


def main():
    recs = curated() + adapt_all()
    recs = finalize(recs)
    proven = [r for r in recs if r['status'] == 'proven']
    suspected = [r for r in recs if r['status'] == 'suspected']
    doc = {
        'schema_version': 1,
        'title': 'Unified Saudi audit defect bundle (batches 1-A, 1-B, 1-C, 1-D, 2-E, 2-F)',
        'base': 'origin/codex/telecom-95pct @ ec610f3',
        'status_rule': ('proven = the bundle auditor re-checked the defect itself against the archived source file (page rendered and read and/or text layer) and the published value in the manifest '
                        'under data/imports; suspected = proven only in a batch record, or the source file is not available offline, or the check could not be completed.'),
        'priority_order': PRIORITY_LABELS,
        'counts': {'proven': len(proven), 'suspected': len(suspected), 'total': len(recs)},
        'proven': proven,
        'suspected': suspected,
    }
    json.dump(doc, open(os.path.join(OUT, 'defect-bundle.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    write_md(doc, os.path.join(OUT, 'defect-bundle.md'))
    print(doc['counts'])


if __name__ == '__main__':
    main()
