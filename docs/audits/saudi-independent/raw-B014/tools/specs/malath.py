import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tx, decl
from tx import std
S = '8020'
E = []
H = {'symbol': S, 'name': 'MALATH COOPERATIVE INSURANCE COMPANY (Malath Insurance), Tadawul 8020', 'currency': 'SAR', 'unit': 'SAR thousand (SAR 000, printed)',
     'conventions': 'cumulative year-to-date as printed (is) and quarter column (is_q); costs negative; insurance_service_result = result after net reinsurance (revenue + service expenses + net reinsurance result); total_insurance_service_result equals it (no pool-surplus line); other_income = other income below other operating expenses; pbt = net income before zakat (zakat only, no income tax line); net_income attributable to shareholders after zakat; eps SAR per share as printed (50,000 thousand shares from 2023); bs prior = prior fiscal year-end as printed in that filing; cash = cash and cash equivalents (term deposits excluded). Labels are PAGE-DERIVED.'}
MAL = {'insurance_revenue': r'^insurance (service )?revenue', 'net_reinsurance_result': r'^net \(?expenses\)? ?/? ?\(?revenues?\)? from reinsurance|^net .{0,30}from reinsurance contracts held',
       'insurance_service_result': r'^insurance service result$', 'total_insurance_service_result': r'^insurance service result$', 'net_investment_income': r'^net investment income',
       'net_insurance_finance_result': r'^net insurance finance', 'net_insurance_investment_result': r'^net insurance and investment result', 'other_operating_expenses': r'^other operating expenses',
       'other_income': r'^other income$', 'zakat_tax': r'^zakat( expense)?( for the (period|year))?$', 'net_income': r'^net income for the (period|year) attributable to shareholders$'}
def c2(p):
    return {'page': p, 'cols': {'cur': -2, 'prior': -1}}
def _eps(sha, pg_, ci):
    m, d, ok = tx.getdoc(S, sha)
    for lab, nums in tx.rows_of(d, pg_):
        if 'per share' in lab.lower():
            dec = [x for x in nums if '.' in x]
            if len(dec) > ci: return tx.val(dec[ci])
    return None


def _fix(e, sha, pg_, four, merged):
    """eps: decimal numbers on the per-share row (share counts trail on the same text row). merged = (oi, zk): oi -> other income and profit before zakat share one text row (first n = other income, last n = pbt); zk -> zakat charge and net income share one text row."""
    n = 4 if four else 2
    if four:
        pos = {('is_q', 'cur'): 0, ('is_q', 'prior'): 1, ('is', 'cur'): 2, ('is', 'prior'): 3}
    else:
        pos = {('is', 'cur'): 0, ('is', 'prior'): 1}
    for (stmt, col), k in pos.items():
        if stmt not in e: continue
        v = _eps(sha, pg_, k)
        if v is not None: e[stmt][col]['eps'] = v
        oi, zk = merged or (False, False)
        if oi:
            for key, off in (('pbt', 0), ('other_income', -n)):
                v = tx.grab_opt(S, sha, pg_, r'^other income$', -(n - k) + off)
                if v is not None: e[stmt][col][key] = v
        if zk:
            v = tx.grab_opt(S, sha, pg_, r'^zakat (charge|expense)', -(n - k))
            if v is not None: e[stmt][col]['net_income'] = v
            v = tx.grab_opt(S, sha, pg_, r'^zakat (charge|expense)', -(2 * n - k))
            if v is not None: e[stmt][col]['zakat_tax'] = v
    return e


def cum(sha, label, pe, pt, ppe, bsp, pgs, reading, merged=(False, False), bscols=None):
    d = {'bs': bscols or c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': MAL, 'drop': ['eps']}, 'is_q': {'page': pgs[1], 'cols': {'cur': -4, 'prior': -3}, 'add': MAL, 'drop': ['eps']}, 'cf': c2(pgs[2])}
    return _fix(std(S, sha, label, pe, pt, ppe, bsp, reading, d), sha, pgs[1], True, merged)


def q1(sha, label, pe, ppe, bsp, pgs, reading, merged=(False, False), bscols=None):
    d = {'bs': bscols or c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': MAL, 'drop': ['eps']}, 'cf': c2(pgs[2])}
    return _fix(std(S, sha, label, pe, 'Q1', ppe, bsp, reading, d), sha, pgs[1], False, merged)


def mi(rev, exp, reins, isr, nii, fin, nir, opex, oi, pbt, zakat, ni, eps):
    return {'insurance_revenue': rev, 'insurance_service_expenses': exp, 'net_reinsurance_result': reins, 'insurance_service_result': isr, 'total_insurance_service_result': isr,
            'net_investment_income': nii, 'net_insurance_finance_result': fin, 'net_insurance_investment_result': nir, 'other_operating_expenses': opex, 'other_income': oi,
            'pbt': pbt, 'zakat_tax': zakat, 'net_income': ni, 'eps': eps}


def bsv(ta, tl, te, cash, icl):
    return {'total_assets': ta, 'total_liabilities': tl, 'total_equity': te, 'cash': cash, 'insurance_contract_liabilities': icl}


def cfv(cfo, cfi, cff, net, b, e):
    return {'cfo': cfo, 'cfi': cfi, 'cff': cff, 'net_change': net, 'cash_begin': b, 'cash_end': e}


def man(sha, label, pe, pt, ppe, bsp, reading, pages, bs, is_, cf, is_q=None, bs2=None, bs2pe=None):
    e = {'sha256_prefix': sha, 'label': label, 'period_end': pe, 'period_type': pt, 'prior_period_end': ppe, 'bs_prior_period_end': bsp, 'reading': reading, 'pages': pages, 'bs': bs, 'is': is_, 'cf': cf}
    if is_q: e['is_q'] = is_q
    if bs2:
        e['bs']['prior2'] = bs2; e['bs_prior2_period_end'] = bs2pe
    return e


E.append(q1('5eda2013', 'Q1 2026', '2026-03-31', '2025-03-31', '2025-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8'))
E.append(cum('3dd9ee2c', 'H1 2026', '2026-06-30', 'H1', '2025-06-30', '2025-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q2 2026, Q2 2025, 6M 2026, 6M 2025; pbt and other income printed on one merged text row) CF p8', merged=(True, False)))
E.append(q1('1f695835', 'Q1 2025', '2025-03-31', '2024-03-31', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8; pbt shares a text row with other income, net income with zakat', merged=(True, True)))
E.append(man('357e97db', 'H1 2025', '2025-06-30', 'H1', '2024-06-30', '2024-12-31',
 'VISUAL: text layer is OCR with spaced letters and detached values; BS p4 (printed 2), IS p5 (printed 3; columns Q2 2025, Q2 2024, 6M 2025, 6M 2024), CF p8 (printed 6) rendered at 1.8x and read by eye',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(1393508, 942165, 451343, 193714, 847689), 'prior': bsv(1199637, 766862, 432775, 172975, 653353)},
 {'cur': mi(706079, -707779, -5050, -6750, 15947, -6940, 2257, -13470, 32770, 21557, -5000, 16557, 0.33), 'prior': mi(431723, -418101, -13931, -309, 19016, -5419, 13288, -17610, 20667, 16345, -4752, 11593, 0.23)},
 {'cur': cfv(188872, -167903, -231, 20739, 172975, 193714), 'prior': cfv(42060, -49906, -625, -8471, 110571, 102100)},
 is_q={'cur': mi(365951, -342934, -19184, 3833, 3920, -3363, 4390, -7138, 13425, 10677, -4000, 6677, 0.13), 'prior': mi(225959, -224477, -1042, 440, 5339, -2824, 2955, -6410, 5982, 2527, -2376, 151, 0.00)}))
_nine = cum('173342ab', '9M 2025', '2025-09-30', '9M', '2024-09-30', '2024-12-31', (4, 5, 8), 'text layer BS p4 and CF p8; IS p5 (cols Q3 2025, Q3 2024, 9M 2025, 9M 2024) text rows are merged so the income statement was rendered at 1.8x and read by eye')
_nine['is'] = {'cur': mi(1072159, -1128915, 19384, -37372, 52578, -9965, 5241, -17201, 35309, 23349, -6161, 17188, 0.34), 'prior': mi(701464, -677345, -26424, -2305, 29152, -7968, 18879, -25183, 30576, 24273, -7128, 17145, 0.34)}
_nine['is_q'] = {'cur': mi(366080, -421136, 24434, -30622, 36631, -3025, 2984, -3731, 2539, 1792, -1161, 631, 0.01), 'prior': mi(269741, -259244, -12493, -1996, 10136, -2549, 5591, -7573, 9909, 7927, -2376, 5551, 0.11)}
E.append(_nine)
def fy(sha, label, pe, ppe, bsp, pgs, reading):
    d = {'bs': c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': MAL, 'drop': ['eps']}, 'cf': c2(pgs[2])}
    e = std(S, sha, label, pe, 'FY', ppe, bsp, reading, d)
    for col, k in (('cur', 0), ('prior', 1)):
        v = _eps(sha, pgs[1], k)
        if v is not None: e['is'][col]['eps'] = v
    return e


E.append(fy('3f67f59f', 'FY2025', '2025-12-31', '2024-12-31', '2024-12-31', (9, 10, 13), 'text layer BS p9 IS p10 CF p13 (printed 4-7 area); inventory label 2026|FY is publication year'))
E.append(man('3b65474b', 'FY2024', '2024-12-31', 'FY', '2023-12-31', '2023-12-31',
 'VISUAL: statements are image-only (pp7-12 zero text); BS p8 (printed 6), IS p9 (printed 7), CF p12 (printed 10) rendered at 1.8x and read by eye; inventory label 2025|FY is publication year; inventory statement_pages (81, 101-106) point to notes and miss the real primary pages',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': bsv(1199637, 766862, 432775, 172975, 653353), 'prior': bsv(924140, 534050, 390090, 110571, 433522)},
 {'cur': mi(1010723, -976030, -38892, -4199, 36697, -10197, 22301, -31080, 45172, 36393, -9504, 26889, 0.54), 'prior': mi(934712, -844801, -72461, 17450, 40470, -12342, 45578, -18341, 19951, 47188, -9000, 38188, 0.76)},
 {'cur': cfv(250597, -187215, -978, 62404, 110571, 172975), 'prior': cfv(-108911, -116866, -182, -225959, 336530, 110571)}))
E.append(man('e48700a1', 'FY2023', '2023-12-31', 'FY', '2022-12-31', '2022-12-31',
 'VISUAL: statements are image-only (pp3-8 zero text; BS p8 printed 6 with columns 2023, 2022 restated, 1 Jan 2022 restated; IS p9 printed 7; CF p12 printed 10) rendered at 1.9x and read by eye; inventory label 2024|FY is publication year; first IFRS 17 annual, 2022 restated (Note 4)',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': bsv(924140, 534050, 390090, 110571, 433522), 'prior': bsv(1020120, 666105, 354015, 336530, 570294)},
 {'cur': mi(934712, -844801, -72461, 17450, 40470, -12342, 45578, -18341, 19951, 47188, -9000, 38188, 0.76), 'prior': mi(973092, -981587, -30464, -38959, 31520, -6226, -13665, -23899, 6474, -31090, -10288, -41378, -0.83)},
 {'cur': cfv(-110312, -115466, -182, -225959, 336530, 110571), 'prior': cfv(-128618, -9907, -746, -139271, 475801, 336530)},
 bs2=bsv(1060554, 666836, 393718, 475801, 579086), bs2pe='2022-01-01'))
E.append(man('d79acfbb', 'FY2022', '2022-12-31', 'FY', '2021-12-31', '2021-12-31',
 'VISUAL: BS p8 (printed 2), IS p9 (printed 3), CF p12 (printed 6) rendered at 2x and read by eye (text layer partly OCR-garbled); inventory label 2023|FY is publication year; IFRS 4 as originally published; revenue = total revenues (net premiums earned plus commissions and other underwriting income); net_underwriting_result = net underwriting income; zakat_tax = zakat expense; no financing line printed in the cash flow (nil)',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': {'total_assets': 1372115, 'total_liabilities': 1035665, 'total_equity': 336450, 'cash': 342270}, 'prior': {'total_assets': 1354718, 'total_liabilities': 983142, 'total_equity': 371576, 'cash': 479381}},
 {'cur': {'revenue': 905137, 'gross_written_premiums': 944376, 'net_underwriting_result': 61270, 'pbt': -18027, 'zakat_tax': -10288, 'net_income': -28315, 'eps': -0.57}, 'prior': {'revenue': 788050, 'gross_written_premiums': 942107, 'net_underwriting_result': 13969, 'pbt': -72850, 'zakat_tax': -12810, 'net_income': -85660, 'eps': -1.71}},
 {'cur': cfv(-126649, -10462, 0, -137111, 479381, 342270), 'prior': cfv(-60137, -20552, 0, -80689, 560070, 479381)}))
_D = {e['label']: e for e in E}
_D['H1 2025'].setdefault('declared_footing', []).append({'col': 'cur', 'check': 'cf-sum', 'printed': 20739, 'computed': 20738})
_D['9M 2025'].setdefault('declared_footing', []).append({'col': 'prior', 'check': 'is-pbt-chain', 'printed': 24273, 'computed': 24272})
_D['FY2025'].setdefault('declared_footing', []).append({'col': 'cur', 'check': 'cf-sum', 'printed': 21229, 'computed': 21230})
_D['FY2023'].setdefault('declared_footing', []).append({'col': 'cur', 'check': 'cf-sum', 'printed': -225959, 'computed': -225960})
_D['Q1 2026'].setdefault('declared_footing', []).append({'col': 'cur', 'check': 'cf-sum', 'printed': -36348, 'computed': -36349})
import decl
_R = []
def _pairs(stmt, pe, order, reason, keys=None, pt='FY'):
    return [(stmt, pe, pt, (order[i], order[j]), reason, keys) for i in range(len(order)) for j in range(i + 1, len(order))]
for _st in ('bs', 'is', 'cf'):
    _R += _pairs(_st, '2022-12-31', ['FY2022', 'FY2023'], 'IFRS 17 transition restatement of 2022 (FY2023 note 4): FY2022 as originally published under IFRS 4 (total assets 1,372,115, equity 336,450, net loss 28,315, cash 342,270 including murabaha deposits classified as cash) versus restated (total assets 1,020,120, equity 354,015, net loss 41,378, cash 336,530)')
_R += _pairs('cf', '2023-12-31', ['FY2023', 'FY2024'], 'FY2023 cash flow comparative re-presented in FY2024: operating -110,312 -> -108,911, investing -115,466 -> -116,866 (1,401 right-of-use additions reclassified); net change -225,959 identical', None)
RESTATEMENTS = decl.declare(E, _R + [('cf', '2025-06-30', 'H1', ('H1 2025', 'H1 2026'), 'H1 2025 cash flow comparative in the H1 2026 filing: operating 188,872 -> 188,871, investing -167,903 -> -167,901 (additions to investments -83,242 -> -83,240); net change 20,739 vs components 20,738: printed rounding', None)])
QS = tx.quarter_sums([2025, 2026], {e['label'] for e in E}, tol={(2025, 'pbt', 'Q1+Q2=H1'): (1, 'printed rounding 10,881 + 10,677 = 21,558 vs 21,557'), (2025, 'net_income', 'Q1+Q2=H1'): (1, 'printed rounding 9,881 + 6,677 = 16,558 vs 16,557')})
if __name__ == '__main__':
    import decl as _d
    _d.show(E)
    tx.save(S, H, E, {'restatements': RESTATEMENTS, 'quarter_sums': QS})
