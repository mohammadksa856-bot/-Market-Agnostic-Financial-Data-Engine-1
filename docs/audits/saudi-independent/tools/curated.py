"""Curated (manually proven) findings for batch1-B. Evidence = archived source page + line item."""
import os, json, re
from b_inventory import ROOT, inventory
from b_pages import rows, nums
from b_verify_pdf import norm

def _alinma_threemonth_as_ytd(mf, pdf_rel):
    """For each fact published as ytd from the three-month column, give the true cumulative figure from the same row."""
    d = json.load(open(os.path.join(ROOT, 'data/imports', mf), encoding='utf8'))
    pdf = os.path.join(ROOT, pdf_rel); cache = {}; out = []
    for f in d['facts']:
        if f['period_kind'] != 'ytd' or f.get('page') != 4: continue
        R = cache.setdefault(4, rows(pdf, 4))
        lab = norm(f['source_label'])
        for y, t in R:
            if lab[:25] in norm(t):
                ns = nums(t)
                if len(ns) >= 4 and abs(abs(ns[-4]) - abs(float(f['value']))) < 1e-6:
                    out.append(dict(metric=f['metric'], page=4, line_item=f['source_label'], published_ytd=f['value'],
                                    printed_row=re.sub(r'\s+', ' ', t)[:140], correct_cumulative_value=str(int(abs(ns[-2])) * (1 if float(f['value']) > 0 else -1)),
                                    evidence='published equals the first (three-month) column; the cumulative column is the third number'))
                break
    return out

def alinma_manifests():
    inv = {r['manifest']: r for r in inventory('1150')}
    cur = {}
    for mf in ('alinma-2018-q2.json', 'alinma-2018-q3.json'):
        facts = _alinma_threemonth_as_ytd(mf, inv[mf]['local'][0])
        cur[mf] = dict(
            numeric_correctness='defective',
            defects=[dict(id='ALN-1', defect_class='quarter_vs_cumulative_confusion', page=4, severity='high',
                          summary='Income-statement facts carry the THREE-MONTH column but are labelled period_kind=ytd (period_start 2018-01-01). Page 4 has both a three-month and a six/nine-month pair of columns; the reader cut off the heading band at y<155 and the subtitle line pushed the headings lower, so no heading was seen and the first pair was published as ytd.',
                          affected_fact_count=len(facts), facts=facts,
                          fix='general reader fix (src/finengine/reading.py _header_limit) + regression test tests/test_audit_alinma_interim_columns.py; re-read and republish; the published three-month values are valid as period_kind=quarter')])
    cur['alinma-2018-q2.json']['defects'].append(dict(
        id='ALN-3', defect_class='wrapped_caption_mapped_to_gross_line', page=4, severity='medium',
        summary='Caption "Income from investments and financing, / net" wraps over two rows (y=259.7 / 271.2). The first row carries no figures, the second only the fragment "net", so the reader published the GROSS line 1,185,931 (three-month) and never the net line 942,390 (6M 1,838,667).',
        evidence='page 4 rows: "Income from investments and financing 1,185,931 1,021,141 2,299,017 2,028,650" (gross) then "Income from investments and financing, / net 942,390 834,219 1,838,667 1,648,645"',
        fix='caption stitching in _statement_facts (same commit)'))
    cur['alinma-2019-q2.json'] = dict(
        defects=[dict(id='ALN-3', defect_class='wrapped_caption_mapped_to_gross_line', page=4, severity='medium',
                      summary='Same wrapped caption: published financing_income 1,378,495 (quarter) / 2,685,608 (ytd) are the GROSS line; net line 1,079,559 / 2,072,658 never published.',
                      evidence='page 4 rows "Income from investments and financing 1,378,495 1,185,931 2,685,608 2,299,017" then ", / net 1,079,559 942,390 2,072,658 1,838,667"')])
    return cur


def _aln2(mf):
    d = json.load(open(os.path.join(ROOT, 'data/imports', mf), encoding='utf8'))
    facts = [dict(period_kind=f['period_kind'], published_metric=f['metric'], source_label=f['source_label'], value=f['value'], page=f.get('page'))
             for f in d['facts'] if f['metric'] == 'financing_income' and f['source_label'].strip().lower().endswith(('net', 'financing,'))]
    return facts

_ALN2_TEXT = ('The NET line "Income from investments and financing, net" is published under metric financing_income (gross special-commission income elsewhere: '
              'SNB/SAIB/Alinma supplement use financing_income = gross and net_financing_income = net). Alinma FY2019 page 9: gross 5,608,762; return on time investments (1,214,303); '
              'net 4,394,459 - published financing_income = 4,394,459. Series for one metric mixes net (FS manifests) and gross (XLSX supplement 2021-2025, e.g. FY2019 5,537,518), and the vintage '
              'reconciler then mislabels the genuine line-item difference as "restated_in_higher_ranked_publication".')

def _build():
    c = alinma_manifests()
    for mf in ('alinma-2018-fy.json', 'alinma-2018-q3.json', 'alinma-2019-fy.json', 'alinma-2020-fy.json', 'alinma-2020-q1.json', 'alinma-2020-q2.json', 'alinma-2020-q3.json'):
        facts = _aln2(mf)
        if not facts: continue
        e = c.setdefault(mf, {})
        e.setdefault('defects', []).append(dict(id='ALN-2', defect_class='metric_mapping_net_published_as_gross', severity='medium', summary=_ALN2_TEXT,
                                                 facts=facts, fix='BANK_LINE_MAP: "income from investments and financing, net" -> net_financing_income and "return on time investments" -> financing_expense (this branch); republish'))
        e['numeric_correctness'] = e.get('numeric_correctness', 'defective')
    for mf, e in c.items():
        e.setdefault('numeric_correctness', 'defective')
    # completeness (document vs extracted) - from page reading
    comp = {
        'alinma-2019-fy.json': dict(statements_in_document=['financial position p8', 'income p9', 'cash flow p13', 'equity changes'],
                                   missing_fields=['cash and balances with SAMA 8,039,748 (p8)', 'property and equipment 2,413,893', 'other assets 962,473', 'other liabilities 4,041,838', 'fair value reserve 77,372',
                                                   'proposed bonus shares 5,000,000', 'treasury shares (103,475)', 'fee income/expense lines (1,127,259 / (306,676))', 'impairment charges (700,480 / 5,837)', 'share of loss of associate (10,825)', 'zakat (281,646)', 'cash-flow lines other than the four totals']),
        'alinma-2018-fy.json': dict(missing_fields=['cash flow statement entirely (no operating/investing/financing totals)', 'balance-sheet lines other than 13 captured']),
    }
    for mf, v in comp.items(): c.setdefault(mf, {})['completeness'] = v
    # Pillar 3 Sep-2021 conflict
    c['alinma-pillar-3-tables-final-september-2021-pillar3.json'] = dict(
        numeric_correctness='defective_suspect',
        defects=[dict(id='ALN-4', defect_class='restated_or_corrected_later_by_issuer_not_adopted', page=1, severity='high',
                      summary='Published 2021-09-30 cet1_capital 30,887,221 (row 1 col a) and cet1_ratio/tier1_capital_ratio 0.2126 are exactly as printed in the Sep-2021 disclosure, where CET1 = Tier 1 (rows 1 and 2 identical). Three later Alinma disclosures (Dec-2021 p15 col b, Mar-2022, Jun-2022) print CET1 25,887,221 and ratio 0.1735 for the same quarter (Tier 1 stays 30,887,221, ratio 0.207). The issuer evidently corrected AT1 inclusion; the later numbers themselves do not reconcile (25,887,221/145,249,745=17.82% not 17.35%), so the engine excluded them and kept the earlier figure.',
                      evidence='Sep-2021 PDF p1 row 1: 30,887,221; Dec-2021 PDF p15 row 1 column b: 25,887,221',
                      correct_value='unresolved: CET1 for 2021-09-30 is either 30,887,221 (original) or 25,887,221 (issuer restatement); no source states a reconciling pair',
                      fix='flag the period as conflicting_issuer_vintages; do not publish CET1 ratio for 2021-09-30 as a clean value until the issuer clarifies')])
    return c

MAN = {}
CURATED = {}
def init():
    CURATED['1150'] = dict(
        company=dict(name='Alinma Bank', numeric_correctness_summary='defective in 9 interim/annual PDF manifests (see defects); Pillar 3 (21 docs, 1,259 facts incl. excluded) and XLSX supplement (493 facts) match their sources cell-for-cell',
                     document_completeness_summary='statement-level fields extracted are a minority of printed lines (13 of ~26 balance sheet lines; cash flow only totals; interim cash flow missing)',
                     coverage=dict(have=['FY2018','FY2019','FY2020 audited PDF; Q2-2018, Q3-2018, Q2-2019, Q1/Q2/Q3-2020 interim PDF; FY2021-FY2025 + Q1-2023..Q4-2025 only via issuer XLSX supplement; Pillar 3 KM1 2018Q4..2026Q2 (quarterly, 21 docs)'],
                                   absent=['audited FS FY2021-FY2025 (no PDF archived)', 'interim PDFs Q1-2018, Q1/Q3-2019, all 2021-2026', 'quarterly series 2021Q1-2022Q4 (supplement carries FY only for those years)', 'no cash-flow statement outside FY2019/FY2020 and 6M-2018/2019 fragments'])),
        manifests=_build())
    CURATED['1030'] = dict(company=dict(name='Saudi Investment Bank (SAIB)'), manifests={})
    CURATED['1180'] = dict(company=dict(name='Saudi National Bank (SNB)'), manifests={})
    CURATED['8010'] = dict(company=dict(name='The Company for Cooperative Insurance (Tawuniya)'), manifests={})
    CURATED['2222'] = dict(company=dict(name='Saudi Arabian Oil Company (Aramco)'), manifests={})
init()

import curated2
curated2.apply(CURATED)

def tawuniya_extra(scratch):
    """Candidate manifests that exist only on origin/claude/insurance-tawuniya-bupa-enrichment (read-only extracts in scratch)."""
    import subprocess, collections
    from b_verify_pdf import check_manifest
    br = 'origin/claude/insurance-tawuniya-bupa-enrichment'
    idx = json.loads(subprocess.check_output(['git', 'show', br + ':data/raw/archive-index.json'], cwd=ROOT))['artifacts']
    m2 = {m: x for x in idx if x['company_id'] == 'sa:8010' for m in x['metadata']['manifests']}
    out = []
    for m, x in sorted(m2.items()):
        if m == 'tawuniya-2025-fy.json': continue
        mp = os.path.join(scratch, 'tawm', m); pdf = os.path.join(scratch, 'taw', x['content_hash'] + '.pdf')
        res = check_manifest('8010', m, manifest_path=mp, pdf_path=pdf)['results']
        c = collections.Counter(r[1].split('_col')[0] for r in res)
        d = json.load(open(mp, encoding='utf8'))
        rec = dict(source_document=dict(manifest=m, archived_path='(on %s) %s' % (br, x['local_path']), source_url=x['source_url'], kind='financial_statements_pdf',
                                        period_end=d['period_end'], published_facts=len(d['facts']), excluded_facts=0, branch_status='UNMERGED candidate (not published on main)'),
                   status='done', anchors=dict(c), checks=['each fact located on its cited pdf page row; column index recorded'],
                   numeric_correctness='verified_correct')
        bad = [r for r in res if not r[1].startswith('ok')]
        if m == 'tawuniya-2023-fy.json':
            rec['numeric_correctness'] = 'defective'
            rec['defects'] = [dict(id='TAW-1', defect_class='two_panel_layout_wrong_pairing_sign_and_magnitude', page=179, severity='high',
                                   line_item='Net change in cash and cash equivalents during the period', published_value='-106248', correct_value='422514',
                                   evidence=('pdf p179 (printed 179): the caption "Net change in cash and cash equivalents during / the period" is in the right-hand panel, '
                                             'printed value 422,514 (2023) / 471,057 (2022). The reader paired it with the left-panel row "Reinsurance contract assets (780,487) (106,248)". '
                                             'Proof: 1,591,389 - 1,044,024 - 124,851 = 422,514 and 1,659,193 + 422,514 = 2,081,707 (cash at end).'),
                                   fix='two-panel pages: pair captions only with numbers of the same panel (reading._statement_facts panel split by x boundary fails when the caption wraps across rows); do not merge this manifest until fixed')]
        elif bad:
            rec['numeric_correctness'] = 'review'
        rec['unanchored'] = [dict(metric=r[0], status=r[1], value=r[2], kind=r[3], page=r[5]) for r in bad]
        out.append(rec)
    return out
