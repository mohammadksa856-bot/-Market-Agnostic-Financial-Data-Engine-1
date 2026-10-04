import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tx, decl
from tx import std
S = '8012'
E = []
H = {'symbol': S, 'name': 'ALJAZIRA TAKAFUL TAAWUNI COMPANY (Jazira Takaful), Tadawul 8012', 'currency': 'SAR', 'unit': 'SAR thousand (SAR 000, printed)',
     'conventions': 'cumulative year-to-date as printed (is) and quarter column (is_q); costs negative; insurance_service_result = result from directly written business (revenue + service expenses + net reinsurance result); total_insurance_service_result adds share of surplus from insurance pools (single line when the pool line is absent); pbt = income before zakat and income tax; zakat_tax = zakat charge, income_tax printed separately; net_income attributable to shareholders; eps SAR per share as printed; cash = cash and cash equivalents; bs prior = prior fiscal year-end as printed in that filing. The balance sheet includes investments held to cover unit-linked liabilities (about SAR 1.6bn) and goodwill 232,255. Labels are PAGE-DERIVED.'}
JAZ = {'insurance_revenue': r'insurance revenue', 'insurance_service_expenses': r'^insurance service expenses', 'net_reinsurance_result': r'^net expenses from reinsurance|^net .{0,30}from reinsurance contracts held',
       'insurance_service_result': r'directly written business', 'pool_surplus': r'^share of surplus', 'total_insurance_service_result': r'^(total|net) insurance service result',
       'net_investment_income': r'^net investment return', 'net_insurance_finance_result': r'^net insurance finance', 'net_insurance_investment_result': r'^net insurance and investment result',
       'other_operating_expenses': r'^other operating expenses', 'other_income': r'^other income$',
       'pbt': r'before zakat and income tax$|^income tax$|^income$|^(\(loss\) / )?income for the period attributable to the shareholders before',
       'zakat_tax': r'^zakat( charge)?$', 'income_tax': r'^income tax( charge)?$', 'net_income': r'^net .{0,30}for the (period|year) attributable to the shareholders$|ttributable to the shareholders$|^net (income|loss|\(loss\) / income) after'}


def c2(p):
    return {'page': p, 'cols': {'cur': -2, 'prior': -1}}


def eps(sha, pg_, k):
    m, d, ok = tx.getdoc(S, sha)
    for lab, nums in tx.rows_of(d, pg_):
        if 'per share' in lab.lower() and 'weighted' not in lab.lower():
            dec = [x for x in nums if '.' in x]
            if len(dec) >= 2:
                return tx.val(dec[k]) if k < len(dec) else None
    return None


def build(sha, label, pe, pt, ppe, bsp, pgs, reading, drop_iq=False, extra=None, bscols=None):
    ia = dict(JAZ); ia.update(extra or {})
    spec = {'bs': dict(bscols or c2(pgs[0]), add={'total_equity': r'^total equity$'}), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': ia, 'drop': ['pbt', 'eps']}, 'cf': c2(pgs[2])}
    spec['is']['add'] = ia
    if pt in ('H1', '9M'):
        spec['is_q'] = {'page': pgs[1], 'cols': {'cur': -4, 'prior': -3}, 'add': ia, 'drop': ['pbt', 'eps']}
    e = std(S, sha, label, pe, pt, ppe, bsp, reading, spec)
    for st in ('is', 'is_q'):
        for col in ('cur', 'prior'):
            c = e.get(st, {}).get(col)
            if c is not None and 'insurance_service_result' not in c and 'total_insurance_service_result' in c:
                c['insurance_service_result'] = c['total_insurance_service_result']; c.setdefault('pool_surplus', 0)
            if c is not None and 'eps' not in c:
                pass
    return e


LOST = {'income_tax': (r'^income tax$', 1)}
E.append(build('a2ef6774', 'H1 2026', '2026-06-30', 'H1', '2025-06-30', '2025-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q2 2026, Q2 2025, 6M 2026, 6M 2025; pbt label lost, income tax split by occurrence) CF p8', extra=LOST))
E.append(build('763ae825', 'Q1 2026', '2026-03-31', 'Q1', '2025-03-31', '2025-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8'))
def mi(rev, exp, reins, isr, pool, tot, nii, fin, nir, oi, opex, pbt, zakat, tax, ni, eps):
    return {'insurance_revenue': rev, 'insurance_service_expenses': exp, 'net_reinsurance_result': reins, 'insurance_service_result': isr, 'pool_surplus': pool, 'total_insurance_service_result': tot,
            'net_investment_income': nii, 'net_insurance_finance_result': fin, 'net_insurance_investment_result': nir, 'other_income': oi, 'other_operating_expenses': opex, 'pbt': pbt, 'zakat_tax': zakat, 'income_tax': tax, 'net_income': ni, 'eps': eps}


E.append({'sha256_prefix': 'e655fe25', 'label': 'Q1 2025', 'period_end': '2025-03-31', 'period_type': 'Q1', 'prior_period_end': '2024-03-31', 'bs_prior_period_end': '2024-12-31',
 'reading': 'VISUAL: pages 4-8 are image-only (inventory statement_pages 15, 21 point to segment notes and cash flow is flagged missing); BS p4 (printed 2), IS p5 (printed 3), CF p8 (printed 6) rendered at 1.8x and read by eye',
 'pages': {'bs': 4, 'is': 5, 'cf': 8},
 'bs': {'cur': {'total_assets': 3084480, 'total_liabilities': 2090183, 'total_equity': 994297, 'cash': 122818, 'insurance_contract_liabilities': 2008840}, 'prior': {'total_assets': 3088474, 'total_liabilities': 2112798, 'total_equity': 975676, 'cash': 169782, 'insurance_contract_liabilities': 2029738}},
 'is': {'cur': mi(83758, -52151, -15070, 16537, 0, 16537, 10996, -3742, 23791, 40, -6564, 17267, -1076, -79, 16112, 0.24), 'prior': mi(91965, -74353, -1939, 15673, 0, 15673, 106453, -97863, 24263, 481, -10956, 13788, -849, -159, 12780, 0.19)},
 'cf': {'cur': {'cfo': 15450, 'cfi': -61829, 'cff': -585, 'net_change': -46964, 'cash_begin': 169782, 'cash_end': 122818}, 'prior': {'cfo': 56582, 'cfi': 10812, 'cff': -584, 'net_change': 66810, 'cash_begin': 117616, 'cash_end': 184426}}})
def fy(sha, label, pe, ppe, pgs, reading, bscols=None, extra=None):
    e = build(sha, label, pe, 'FY', ppe, ppe, pgs, reading, bscols=bscols, extra=extra)
    for col, k in (('cur', 0), ('prior', 1)):
        v = eps(sha, pgs[1], k)
        if v is not None: e['is'][col]['eps'] = v
    return e


E.append(fy('71d4dcb1', 'FY2025', '2025-12-31', '2024-12-31', (7, 8, 12), 'text layer BS p7 IS p8 CF p12; inventory label 2026|FY is publication year'))
E.append(fy('dbdca144', 'FY2024', '2024-12-31', '2023-12-31', (7, 8, 12), 'text layer BS p7 IS p8 CF p12; inventory label 2025|FY is publication year'))
E.append(fy('3f4c9afd', 'FY2023', '2023-12-31', '2022-12-31', (9, 10, 14), 'text layer BS p9 (3 columns: 2023, 2022 restated, 1 Jan 2022 restated) IS p10 CF p14; inventory label 2024|FY is publication year; first IFRS 17 annual', bscols={'page': 9, 'cols': {'cur': -3, 'prior': -2}}))
E.append({'sha256_prefix': '868c2e31', 'label': 'FY2022', 'period_end': '2022-12-31', 'period_type': 'FY', 'prior_period_end': '2021-12-31', 'bs_prior_period_end': '2021-12-31',
 'reading': 'text layer BS p9 (printed 7), IS p10-11 (printed 8-9), CF p15 (printed 13); inventory label 2023|FY is publication year; IFRS 4 as originally published; revenue = total revenues (net premium earned + commissions + other underwriting income); net_underwriting_result = net underwriting income; pbt = income attributable to shareholders before zakat and income tax (after income attributed to insurance operations); zakat_tax = zakat + income tax',
 'pages': {'bs': 9, 'is': 11, 'cf': 15},
 'bs': {'cur': {'total_assets': 2652046, 'total_liabilities': 1810569, 'total_equity': 841477, 'cash': 263185}, 'prior': {'total_assets': 2788718, 'total_liabilities': 1974746, 'total_equity': 813972, 'cash': 83023}},
 'is': {'cur': {'revenue': 171057, 'gross_written_premiums': 415621, 'net_underwriting_result': 66017, 'pbt': 30284, 'zakat_tax': -1930, 'net_income': 28354, 'eps': 0.516}, 'prior': {'revenue': 173848, 'gross_written_premiums': 299031, 'net_underwriting_result': 68271, 'pbt': 21961, 'zakat_tax': -541, 'net_income': 21420, 'eps': 0.407}},
 'cf': {'cur': {'cfo': 148088, 'cfi': 33131, 'cff': -1057, 'net_change': 180162, 'cash_begin': 83023, 'cash_end': 263185}, 'prior': {'cfo': -103713, 'cfi': 83253, 'cff': -2549, 'net_change': -23009, 'cash_begin': 106032, 'cash_end': 83023}}})
E.append(build('42bd770f', 'H1 2025', '2025-06-30', 'H1', '2024-06-30', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q2 2025, Q2 2024, 6M 2025, 6M 2024) CF p8'))
E.append(build('d057a23f', '9M 2025', '2025-09-30', '9M', '2024-09-30', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q3 2025, Q3 2024, 9M 2025, 9M 2024) CF p8'))
E.append(build('62fafbbf', 'Q1 2024', '2024-03-31', 'Q1', '2023-03-31', '2023-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8; EPS column labelled Restated'))
E.append(build('b05cbba4', 'H1 2024', '2024-06-30', 'H1', '2023-06-30', '2023-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q2 2024, Q2 2023, 6M 2024, 6M 2023) CF p8'))
E.append(build('440eccd9', '9M 2024', '2024-09-30', '9M', '2023-09-30', '2023-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q3 2024, Q3 2023, 9M 2024, 9M 2023) CF p8'))
import decl
_R = []
for _st in ('bs', 'is', 'cf'):
    _R.append((_st, '2022-12-31', 'FY', ('FY2022', 'FY2023'), 'IFRS 17 transition restatement of 2022 (FY2023 annual, column marked Restated): FY2022 as originally published under IFRS 4 (total assets 2,652,046; total equity 841,477; income before zakat 30,284; net income 28,354; EPS 0.516; cash 263,185) versus restated (2,533,534; 892,718; 40,450; 38,520; 0.58; 254,752); the restated cash flow shows opening cash 83,021 and net change 171,731', None))
_R.append(('cf', '2024-12-31', 'FY', ('FY2024', 'FY2025'), 'FY2024 comparative cash flow re-presented in the FY2025 annual: operating 72,596 -> 72,024 and financing -21,885 -> -21,313 (572 reclassified); net change 52,166 and closing cash 169,782 unchanged', None))
RESTATEMENTS = decl.declare(E, _R)
QS = tx.quarter_sums([2024, 2025, 2026], {e['label'] for e in E}, tol={(2025, 'pbt', 'Q1+Q2=H1'): (1, 'printed rounding 17,267 + 5,369 = 22,636 vs 22,637'), (2025, 'pbt', 'H1+Q3=9M'): (1, 'printed rounding H1 22,637 + Q3 vs 9M differs by 1'), (2025, 'net_income', 'Q1+Q2=H1'): (1, 'printed rounding 16,112 + 4,080 = 20,192 vs 20,193')})
if __name__ == '__main__':
    import decl as _d
    _d.show(E)
    tx.save(S, H, E, {'restatements': RESTATEMENTS, 'quarter_sums': QS})
