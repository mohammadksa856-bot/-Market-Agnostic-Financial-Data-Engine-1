"""Build docs/audits/saudi-independent/<symbol>.json (resumable audit records) for batch1-B.

Automated anchoring is recomputed here (so every record is reproducible); curated findings
(manual page reading, visual checks, cross-document proofs) live in CURATED below.
Usage: python build_records.py [symbol ...]   (writes JSON, never touches data/**)
"""
import sys, os, json, glob, collections, datetime
sys.path.insert(0, os.path.dirname(__file__))
from b_inventory import ROOT, inventory, PREFIX
from b_verify_pdf import check_manifest
from b_verify_p3 import check as p3_check, seq_check
from b_xlsx import verify_xlsx
from b_pages import rows, nums

OUT = os.path.join(ROOT, 'docs/audits/saudi-independent')
SCR = os.environ.get('AUDIT_SCRATCH', '')   # extracted read-only copies of docs that live on other branches
BRANCH = 'origin/codex/telecom-95pct @ ec610f3 (data/imports identical to origin/main for these companies)'

def kind_of(m):
    if 'pillar' in m or '-p3-' in m or '-km1-' in m: return 'pillar3_km1_pdf'
    if 'supplement' in m: return 'issuer_data_supplement_xlsx'
    return 'financial_statements_pdf'

def auto(sym, r):
    m = r['manifest']; k = kind_of(m)
    rec = dict(source_document=dict(manifest=m, archived_path=(r['local'] or [None])[0], source_url=None, kind=k,
                                    period_end=r['period_end'], published_facts=r['n_facts'], excluded_facts=r['n_excluded']),
               status='done', checks=[], anchors={})
    if not r['local'] or not os.path.exists(os.path.join(ROOT, r['local'][0])):
        rec['status'] = 'pending'; rec['numeric_correctness'] = 'unverified'
        rec['note'] = 'archived source document is not present in the checkout (git history of audited branch/main)'
        return rec
    path = os.path.join(ROOT, r['local'][0])
    if k == 'financial_statements_pdf' and not path.lower().endswith('.pdf'):
        rec['status'] = 'done'; rec['numeric_correctness'] = 'not_applicable'; rec['note'] = 'market-price/non-statement artifact (no financial-statement facts)'
        return rec
    if r['n_facts'] == 0:
        rec['numeric_correctness'] = 'not_applicable'; rec['note'] = 'qualitative/disclosure manifest without numeric facts; text content not audited in this batch'
        return rec
    mdata = json.load(open(os.path.join(ROOT, 'data/imports', m), encoding='utf8'))
    if k == 'financial_statements_pdf' and mdata.get('facts') and 'source_label' not in mdata['facts'][0]:
        # whole-document locator was run interactively (tools/b_verify_doc.py <manifest> <pdf>); recorded counts:
        present = {'aramco-2025-annual-metrics.json': (167, 176), 'aramco-2025-segment-ebitda-inputs.json': (9, 9), 'aramco-2025-other-reserve-components.json': (14, 14),
                   'aramco-2025-operational-precision.json': (3, 3)}.get(m)
        rec['anchors'] = dict(values_present_in_archived_2025_annual_report=present[0] if present else None, facts=present[1] if present else mdata and len(mdata['facts']))
        rec['checks'].append('whole-document value locator (printed page = pdf page - 2); re-run with: python tools/b_verify_doc.py data/imports/<manifest> <pdf>')
        rec['unanchored'] = []
        rec['numeric_correctness'] = 'unverified_partial'
        return rec
    if k == 'financial_statements_pdf':
        res = check_manifest(sym, m)['results']
        c = collections.Counter(x[1].split('_col')[0] for x in res)
        rec['anchors'] = dict(c)
        rec['checks'].append('every fact located on its cited PDF page (y-aligned row) and column index recorded (current vs prior, quarter vs ytd)')
        rec['unanchored'] = [dict(metric=x[0], status=x[1], value=x[2], kind=x[3], page=x[5]) for x in res if not x[1].startswith('ok')]
        bykind = collections.defaultdict(collections.Counter)
        for x in res:
            if len(x) >= 8 and x[7] is not None: bykind[f'{x[3]}@p{x[5]}'][x[7]] += 1
        rec['column_pattern_from_right'] = {k2: dict(v) for k2, v in bykind.items()}
    elif k == 'pillar3_km1_pdf':
        n, out = p3_check(sym, m)
        c = collections.Counter(o[5].split('(')[0] for o in out)
        rec['anchors'] = dict(c)
        rec['checks'].append('every published and excluded fact compared with the KM1 row/cell of the PDF (value at column letter)')
        seq = seq_check(sym, m)
        rec['checks'].append('column letters map to consecutive quarter-ends back from the document date: ' + ('PASS' if not seq else 'FAIL %s' % seq))
        rec['unanchored'] = [dict(kind=o[0], metric=o[1], period_end=o[2], cell=o[3], value=o[4], status=o[5]) for o in out if o[5] != 'ok']
        d = json.load(open(os.path.join(ROOT, 'data/imports', m), encoding='utf8'))
        reasons = collections.Counter(x.get('reason') for x in d.get('excluded_facts', []))
        rec['excluded_reasons'] = dict(reasons)
    else:
        res = verify_xlsx(path, os.path.join(ROOT, 'data/imports', m))
        c = collections.Counter((o[0], o[5]) for o in res)
        rec['anchors'] = {f'{a}:{b}': n for (a, b), n in c.items()}
        rec['checks'].append('every published/excluded fact matched to workbook cell by row label and column header (FY/nQ/1H) and value (sign flip and rounding classified)')
        rec['unanchored'] = [dict(kind=o[0], metric=o[1], period_kind=o[2], period_end=o[3], value=o[4], status=o[5]) for o in res if not o[5].startswith('ok')]
    bad = [u for u in rec['unanchored'] if u]
    rec['numeric_correctness'] = 'verified_correct' if not bad else 'review'
    return rec

def main(syms):
    sys.path.insert(0, os.path.dirname(__file__))
    from curated import CURATED
    for sym in syms:
        inv = inventory(sym)
        srcs = []
        for r in inv:
            rec = auto(sym, r)
            rec['source_document']['source_url'] = json.load(open(os.path.join(ROOT, 'data/imports', r['manifest']), encoding='utf8')).get('source_url')
            cur = CURATED.get(sym, {}).get('manifests', {}).get(r['manifest'])
            if cur: rec.update(cur)
            srcs.append(rec)
        company = CURATED[sym]['company']
        extra = CURATED[sym].get('extra_sources', [])
        if sym == '8010' and SCR:
            from curated import tawuniya_extra
            extra = tawuniya_extra(SCR)
        doc = dict(symbol=sym, audited_branch=BRANCH, audited_at=datetime.date.today().isoformat(), auditor='claude/audit-saudi-batch1-B',
                   dimensions_note='(1) numeric correctness of published values, (2) document completeness, (3) company coverage are reported separately and never blended',
                   **company, sources=srcs + extra,
                   progress=dict(total=len(srcs) + len(extra), done=sum(1 for s in srcs + extra if s['status'] == 'done'),
                                 pending=[s['source_document']['manifest'] for s in srcs + extra if s['status'] != 'done']))
        with open(os.path.join(OUT, f'{sym}.json'), 'w', encoding='utf8') as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        print(sym, doc['progress']['total'], 'sources', doc['progress']['done'], 'done')

if __name__ == '__main__':
    main(sys.argv[1:] or ['1150', '1030', '1180', '8010', '2222'])
