"""Finalisation (ids, source files for aggregate records, ordering) and Markdown writer."""
import json, os, re
from bundle_lib import *

MANRE = re.compile(r'[A-Za-z0-9][A-Za-z0-9\-_.]*\.json')


def _manifests_of(r):
    names = []
    if isinstance(r.get('manifest'), str):
        names += [m for m in MANRE.findall(r['manifest']) if not m.startswith('1') or '-' in m]
    pv = r.get('published_value')
    if isinstance(pv, list):
        for e in pv:
            if isinstance(e, dict) and e.get('manifest'):
                names.append(e['manifest'] if e['manifest'].endswith('.json') else e['manifest'] + '.json')
    out = []
    for n in names:
        if n not in out:
            out.append(n)
    return out


NONVALUE = {'metadata_filed_at': 'metadata field, not a reported amount', 'coverage': 'coverage gap, no reported amount involved', 'completeness': 'completeness gap, nothing published to compare',
            'completeness_stale_reader': 'completeness gap', 'completeness_and_notes': 'completeness gap', 'source_not_archived': 'source file missing', 'provenance_page': 'page-citation defect, value not in question',
            'provenance_tag': 'provenance text, no amount', 'duplicates': 'duplicate manifests'}


def finalize(recs):
    for r in recs:
        na = NONVALUE.get(r['category'])
        if na:
            for k in ('restated', 'continuing_operations', 'comparison_source'):
                if r['comparison'].get(k) == NR:
                    r['comparison'][k] = f'not applicable ({na})'
            for k in ('printed_page', 'caption', 'column', 'unit_scale', 'period'):
                if r['location'].get(k) == NR:
                    r['location'][k] = f'not applicable ({na})'
    for r in recs:
        if r['company'] in (None, NR):
            r['company'] = COMPANY.get(r['symbol'], 'multiple companies (see published_value)')
        if r['source_file'] is None:
            mans = _manifests_of(r)
            if mans:
                sf = []
                for n in mans:
                    m = load_manifest(n)
                    if not m:
                        sf.append(dict(manifest=n, sha256=UN, sha256_basis='manifest not in data/imports of the base branch'))
                        continue
                    s = source_info(url=m.get('source_url'))
                    sf.append(dict(manifest=n, sha256=s['sha256'], sha256_basis=s['sha256_basis'], archive_path=s['archive_path'], available_offline=s['available_offline']))
                r['source_file'] = dict(sha256='see source_files (aggregate record covering several manifests)', source_files=sf)
            else:
                r['source_file'] = dict(sha256='not applicable: the defect concerns a missing manifest/coverage, so there is no source file for the defective item',
                                        sha256_basis='n/a', available_offline=False, where='n/a')
    recs.sort(key=lambda r: (r['priority_group'], r['priority_rank'], r['symbol'] or '', r['manifest'] if isinstance(r['manifest'], str) else ''))
    seq = {}
    for r in recs:
        g = r['priority_group']
        seq[g] = seq.get(g, 0) + 1
        r['bundle_id'] = f'BDL-P{g}-{seq[g]:03d}'
    return recs


def _s(v, n=420):
    t = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    t = t.replace('|', '/').replace('\n', ' ')
    return t if len(t) <= n else t[:n] + ' ... (full value in defect-bundle.json)'


def _sha(r):
    sf = r['source_file']
    if 'source_files' in sf:
        return f'{len(sf["source_files"])} source files (see JSON): ' + ', '.join(f'`{(x["sha256"] or "")[:12]}`' for x in sf['source_files'][:4]) + (' ...' if len(sf['source_files']) > 4 else '')
    h = sf.get('sha256') or ''
    return f'`{h}`' if len(h) == 64 else h


def write_md(doc, path):
    L = []
    c = doc['counts']
    L.append('# Unified Saudi audit defect bundle')
    L.append('')
    L.append(f'Base: `{doc["base"]}`. Sources: six independent audit batches (1-A, 1-B, 1-C, 1-D, 2-E, 2-F), copied unchanged under `docs/audits/saudi-independent/bundle/<batch>/`.')
    L.append('')
    L.append(f'**Counts: {c["proven"]} proven, {c["suspected"]} suspected, {c["total"]} total.**')
    L.append('')
    L.append('## How "proven" and "suspected" are decided')
    L.append('')
    L.append(doc['status_rule'])
    L.append('')
    L.append('- Source file SHA-256 is recomputed from the archived file where the bytes are reachable offline (worktree or a local git ref); otherwise it is the `data/raw/archive-index.json` content hash and the record says so. Nothing is invented: `unavailable` means the file is not in this repository.')
    L.append('- `not recorded by batch` means the batch record does not give that field and the bundle did not add it.')
    L.append('- Pinning tests exist only on the six source branches (not on the base); each record states what the test actually asserts. `none` means no test pins the defect.')
    L.append('- Evidence PNGs of pages the bundle auditor rendered and read are in `docs/audits/saudi-independent/bundle-evidence/`.')
    L.append('- Rule for restated figures: a restated comparative is never offered as a replacement for the published original; every record that involves one names the comparison document, its SHA-256, page and scope in `comparison.comparison_source`.')
    L.append('')
    L.append('## Priority order')
    L.append('')
    for k, v in PRIORITY_LABELS.items():
        n1 = sum(1 for r in doc['proven'] if r['priority_group'] == k)
        n2 = sum(1 for r in doc['suspected'] if r['priority_group'] == k)
        L.append(f'{k}. {v}: {n1} proven, {n2} suspected')
    L.append('')
    for status in ('proven', 'suspected'):
        L.append(f'# Section: {status.upper()} defects ({len(doc[status])})')
        L.append('')
        for g, lab in PRIORITY_LABELS.items():
            rs = [r for r in doc[status] if r['priority_group'] == g]
            if not rs:
                continue
            L.append(f'## {status}: group {g} - {lab}')
            L.append('')
            for r in rs:
                loc = r['location']
                cmp_ = r['comparison']
                v = r['verification']
                L.append(f'### {r["bundle_id"]} - {r["symbol"]} {r["company"]} - {r["defect_id"]} ({r["severity"]})')
                L.append(f'- Defect class: {r["defect_class"]}; category: {r["category"]}; batch claimed: {r["batch_claimed_status"]}')
                L.append(f'- Manifest: {_s(r["manifest"], 200)}')
                L.append(f'- Source file SHA-256: {_sha(r)}' + (f' ({_s(r["source_file"].get("sha256_basis", ""), 160)})' if 'sha256_basis' in r['source_file'] else ''))
                L.append(f'- PDF page: {_s(loc["pdf_page"], 120)}; printed page: {_s(loc["printed_page"], 120)}')
                L.append(f'- Caption/label: {_s(loc["caption"], 300)}')
                L.append(f'- Column: {_s(loc["column"], 300)}')
                L.append(f'- Unit/scale: {_s(loc["unit_scale"], 200)}; period: {_s(loc["period"], 160)}')
                L.append(f'- Published value: {_s(r["published_value"])}')
                L.append(f'- Correct value: {_s(r["correct_value"])}')
                L.append(f'- Restated: {_s(cmp_["restated"], 120)}; continuing operations: {_s(cmp_["continuing_operations"], 160)}; comparison source: {_s(cmp_["comparison_source"], 360)}' + (f'; note: {_s(cmp_["note"], 300)}' if cmp_.get('note') else ''))
                e = r['evidence_link']
                L.append(f'- Evidence: batch record `{e["batch_record"]}`; branch path `{e["batch_branch_path"]}`' + (f'; transcription `{e["transcription"]}`' if e.get('transcription') else '') + (f'; rendered pages {", ".join("`" + x + "`" for x in e["page_evidence"])}' if e.get('page_evidence') else ''))
                t = r['pinning_test']
                L.append(f'- Pinning test: `{t["test"]}`' + (f' - {_s(t["scope_note"], 300)}' if t.get('scope_note') else ''))
                nchk = len(v.get('checks', []))
                L.append(f'- Verification: {v["level"]}; result: {v["result"]}; {nchk} check(s)' + (f'; notes: {_s(v.get("notes", ""), 300)}' if v.get('notes') else ''))
                L.append('')
    open(path, 'w', encoding='utf8').write('\n'.join(L))
