import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tx
from tx import std
S = '8311'
def c2(p): return {'page': p, 'cols': {'cur': -2, 'prior': -1}}
E = []
H = {'symbol': S, 'name': 'SAUDI ENAYA COOPERATIVE INSURANCE COMPANY (ENAYA)', 'currency': 'SAR', 'unit': 'SAR thousand (SAR 000, printed)',
     'conventions': 'cumulative year-to-date as printed (is) and quarter column (is_q); costs negative; net_income = net income/(loss) attributable to shareholders after zakat and income tax; zakat_tax = zakat charge, income_tax = income tax charge printed separately; eps SAR per share as printed; bs prior = prior fiscal year-end; is/cf prior = same period prior year; cash = cash and cash equivalents. Labels are PAGE-DERIVED (period printed on the cover/statements), not collector labels.'}
# FY2025 (inventory label 2026|FY)
E.append(std(S, 'f40bef6117031f1f', 'FY2025', '2025-12-31', 'FY', '2024-12-31', '2024-12-31', 'text layer, statements pp7-11 PDF (printed 5-9); inventory label 2026|FY is publication year', {'bs': c2(7), 'is': c2(8), 'cf': c2(11)}))
# FY2024 (inventory 2025|FY)
E.append(std(S, '68acd7ba', 'FY2024', '2024-12-31', 'FY', '2023-12-31', '2023-12-31', 'text layer BS p8 IS p9 CF p12; inventory label 2025|FY is publication year', {'bs': c2(8), 'is': c2(9), 'cf': c2(12)}))
# FY2023 (inventory 2024|FY): BS has 3 columns (2023, 2022 restated, 1 Jan 2022 restated)
E.append(std(S, '9edb28b3', 'FY2023', '2023-12-31', 'FY', '2022-12-31', '2022-12-31', 'text layer BS p10 (3 columns: 2023, 2022 restated, 1 Jan 2022) IS p11 CF p14; inventory label 2024|FY is publication year; IFRS 17 first year, comparatives restated', {'bs': {'page': 10, 'cols': {'cur': -3, 'prior': -2}}, 'is': c2(11), 'cf': c2(14)}))
def q1(sha, lab, pe, ppe, bsp, pgs, rd):
    return std(S, sha, lab, pe, 'Q1', ppe, bsp, rd, {'bs': c2(pgs[0]), 'is': c2(pgs[1]), 'cf': c2(pgs[2])})
def cum(sha, lab, pe, pt, ppe, bsp, pgs, rd, addis=None):
    isadd = addis or {}
    return std(S, sha, lab, pe, pt, ppe, bsp, rd, {'bs': c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': isadd}, 'is_q': {'page': pgs[1], 'cols': {'cur': -4, 'prior': -3}, 'add': isadd}, 'cf': c2(pgs[2])})
E.append(q1('eadf03ce', 'Q1 2025', '2025-03-31', '2024-03-31', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8'))
E.append(cum('50078130', 'H1 2025', '2025-06-30', 'H1', '2024-06-30', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols: Q2 2025, Q2 2024, 6M 2025, 6M 2024) CF p8', {'pbt': (r'^shareholders$', 0)}))
E.append(cum('a4e7c620', '9M 2025', '2025-09-30', '9M', '2024-09-30', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols: Q3 2025, Q3 2024, 9M 2025, 9M 2024) CF p8'))
E.append(q1('7d829b44', 'Q1 2026', '2026-03-31', '2025-03-31', '2025-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8'))
E.append(cum('bf1ebd72', 'H1 2026', '2026-06-30', 'H1', '2025-06-30', '2025-12-31', (5, 6, 9), 'text layer BS p5 IS p6 (cols: Q2 2026, Q2 2025, 6M 2026, 6M 2025) CF p9', {'pbt': (r'^shareholders$', 0), 'net_income': (r'^shareholders$', 1)}))

def b3(p): return {'page': p, 'cols': {'cur': -3, 'prior': -2}}
def q1b(sha, lab, pe, ppe, bsp, pgs, rd, bscols=None):
    return std(S, sha, lab, pe, 'Q1', ppe, bsp, rd, {'bs': bscols or c2(pgs[0]), 'is': c2(pgs[1]), 'cf': c2(pgs[2])})
def cumb(sha, lab, pe, pt, ppe, bsp, pgs, rd, bscols=None, addis=None, patch=None):
    isadd = addis or {}
    return std(S, sha, lab, pe, pt, ppe, bsp, rd, {'bs': bscols or c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': isadd}, 'is_q': {'page': pgs[1], 'cols': {'cur': -4, 'prior': -3}, 'add': isadd}, 'cf': c2(pgs[2])}, patch=patch)
E.append(q1b('eeeca99f', 'Q1 2024', '2024-03-31', '2023-03-31', '2023-12-31', (4, 5, 8), 'text layer BS p4 IS p5 CF p8'))
E.append(cumb('198b2c6a', 'H1 2024', '2024-06-30', 'H1', '2023-06-30', '2023-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (Q2 2024, Q2 2023, 6M 2024, 6M 2023) CF p8', addis={'net_income': (r'^shareholders$', 0)}))
E.append(cumb('a2ee67ed', '9M 2024', '2024-09-30', '9M', '2023-09-30', '2023-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (Q3 2024, Q3 2023, 9M 2024, 9M 2023) CF p8; insurance service result row is merged with later rows in the text layer, values patched from the printed row (-14,563 / 10,723 / -17,342 / 14,763)', addis={'net_income': (r'^shareholders$', 0)}, patch={('is', 'cur'): {'insurance_service_result': -17342}, ('is', 'prior'): {'insurance_service_result': 14763}, ('is_q', 'cur'): {'insurance_service_result': -14563}, ('is_q', 'prior'): {'insurance_service_result': 10723}}))
E.append(q1b('d0f2a113', 'Q1 2023', '2023-03-31', '2022-03-31', '2022-12-31', (4, 5, 8), 'text layer BS p4 (3 columns: 31 Mar 2023, 31 Dec 2022 restated, 1 Jan 2022 restated) IS p5 CF p8', b3(4)))
E.append(cumb('247b0195', 'H1 2023', '2023-06-30', 'H1', '2022-06-30', '2022-12-31', (4, 5, 8), 'text layer BS p4 (3 columns) IS p5 (Q2 2023, Q2 2022, 6M 2023, 6M 2022) CF p8', b3(4)))
E.append(cumb('d6833a6b', '9M 2023', '2023-09-30', '9M', '2022-09-30', '2022-12-31', (4, 5, 8), 'text layer BS p4 (3 columns) IS p5 (Q3 2023, Q3 2022, 9M 2023, 9M 2022) CF p8', b3(4)))

def ifrs4(sha, lab, pe, pt, ppe, bsp, pgs_bs_is1_is2_cf, rd, iscols=(-2, -1), bscols=(-2, -1), cfcols=(-2, -1)):
    """pre-IFRS 17 (IFRS 4) annual: revenue = TOTAL REVENUES (net premiums earned) from the underwriting page, remaining income lines from the next page"""
    pb, p1, p2, pc = pgs_bs_is1_is2_cf
    e = std(S, sha, lab, pe, pt, ppe, bsp, rd, {'bs': {'page': pb, 'cols': {'cur': bscols[0], 'prior': bscols[1]}, 'add': {'total_equity': r'^total equity$'}}, 'is': {'page': p2, 'cols': {'cur': iscols[0], 'prior': iscols[1]}, 'drop': ['insurance_revenue', 'insurance_service_expenses', 'insurance_service_result', 'net_investment_income', 'zakat_tax', 'income_tax']}, 'cf': {'page': pc, 'cols': {'cur': cfcols[0], 'prior': cfcols[1]}}})
    for col, ci in (('cur', iscols[0]), ('prior', iscols[1])):
        e['is'][col]['revenue'] = tx.grab_opt(S, sha, p1, r'^total revenues', ci)
        e['is'][col]['gross_written_premiums'] = tx.grab_opt(S, sha, p1, r'gross premiums written', ci)
        e['is'][col]['net_underwriting_result'] = tx.grab_opt(S, sha, p1, r'net underwriting', ci)
        e['is'][col]['zakat_tax'] = tx.grab_opt(S, sha, p2, r'adjustment for prior years', ci) + tx.grab_opt(S, sha, p2, r'^zakat (and income tax )?provision for the (current )?year', ci)
    for col, ci in (('cur', iscols[0]), ('prior', iscols[1])):
        e['is'][col]['net_income'] = tx.grab_opt(S, sha, p2, r'^net (loss|income) for the year$', ci, -1)
        e['is'][col]['eps'] = tx.grab_opt(S, sha, p2, r'per share for the year', ci)
    return e
E.append(ifrs4('f185283b', 'FY2022', '2022-12-31', 'FY', '2021-12-31', '2021-12-31', (8, 9, 10, 14), 'text layer BS p8 IS p9-10 CF p14 (printed 6-8, 12); inventory label 2023|FY is publication year; IFRS 4 presentation, revenue = total revenues (net premiums earned); zakat_tax = provision adjustment for prior years + zakat and income tax provision for the year'))
E.append(ifrs4('7b9da951', 'FY2021', '2021-12-31', 'FY', '2020-12-31', '2020-12-31', (8, 9, 10, 14), 'text layer BS p8 IS p9-10 CF p14 (printed 6-8, 12); inventory label 2021|FY is the true fiscal year (published 2022); IFRS 4; zakat_tax = provision adjustment for prior years + zakat and income tax provision for the year'))
E.append({'sha256_prefix': 'c035017f', 'label': 'FY2020', 'period_end': '2020-12-31', 'period_type': 'FY', 'prior_period_end': '2019-12-31', 'bs_prior_period_end': '2019-12-31',
 'reading': 'VISUAL: primary statements pp6-14 of this PDF are image-only (zero text layer); BS p8 (printed 6), IS p9-10 (printed 7-8), CF p14 (printed 12) rendered at 1.5x and read by eye; inventory flags the file partial/annual_report but it holds full audited statements; inventory label 2020|FY is the true fiscal year; IFRS 4; zakat_tax = release for prior years +5,298 and current-year provision -1,800 (net +3,498; 2019: -4,800); 2019 EPS restated as printed',
 'pages': {'bs': 8, 'is': 10, 'cf': 14},
 'bs': {'cur': {'total_assets': 315981, 'total_liabilities': 194246, 'total_equity': 121735, 'cash': 115226}, 'prior': {'total_assets': 345159, 'total_liabilities': 195795, 'total_equity': 149364, 'cash': 77375}},
 'is': {'cur': {'revenue': 174290, 'gross_written_premiums': 165874, 'net_underwriting_result': 16861, 'pbt': -31911, 'zakat_tax': 3498, 'net_income': -28413, 'eps': -1.89}, 'prior': {'revenue': 98446, 'gross_written_premiums': 154028, 'net_underwriting_result': -44976, 'pbt': -101352, 'zakat_tax': -4800, 'net_income': -106152, 'eps': -7.37}},
 'cf': {'cur': {'cfo': -22772, 'cfi': 62238, 'cff': -1615, 'net_change': 37851, 'cash_begin': 77375, 'cash_end': 115226}, 'prior': {'cfo': -110081, 'cfi': -69265, 'cff': 200000, 'net_change': 20654, 'cash_begin': 56721, 'cash_end': 77375}}})
E.append({'sha256_prefix': '5ac01a62', 'label': '9M 2021', 'period_end': '2021-09-30', 'period_type': '9M', 'prior_period_end': '2020-09-30', 'bs_prior_period_end': '2020-12-31',
 'reading': 'VISUAL: whole file is zero-text scan (inventory scanned_unread, 34 pages) but holds the full interim set: BS p4 (printed 2), IS p5-6 (printed 3-4; columns Q3 2021, Q3 2020, 9M 2021, 9M 2020), CF p9 (printed 7); rendered 1.5x and read by eye; IFRS 4; zakat_tax = zakat expense',
 'pages': {'bs': 4, 'is': 6, 'cf': 9},
 'bs': {'cur': {'total_assets': 343767, 'total_liabilities': 266808, 'total_equity': 76959, 'cash': 138412}, 'prior': {'total_assets': 315981, 'total_liabilities': 194246, 'total_equity': 121735, 'cash': 115226}},
 'is': {'cur': {'revenue': 124973, 'gross_written_premiums': 164832, 'net_underwriting_result': -14394, 'pbt': -42526, 'zakat_tax': -2250, 'net_income': -44776, 'eps': -2.99}, 'prior': {'revenue': 131523, 'gross_written_premiums': 133331, 'net_underwriting_result': 10150, 'pbt': -22123, 'zakat_tax': -1800, 'net_income': -23923, 'eps': -1.59}},
 'is_q': {'cur': {'revenue': 47005, 'gross_written_premiums': 72959, 'net_underwriting_result': -4079, 'pbt': -12828, 'zakat_tax': -750, 'net_income': -13578, 'eps': -0.91}, 'prior': {'revenue': 41823, 'gross_written_premiums': 46291, 'net_underwriting_result': 1439, 'pbt': -10100, 'zakat_tax': -600, 'net_income': -10700, 'eps': -0.71}},
 'cf': {'cur': {'cfo': -4095, 'cfi': 27281, 'cff': 0, 'net_change': 23186, 'cash_begin': 115226, 'cash_end': 138412}, 'prior': {'cfo': -25415, 'cfi': 3812, 'cff': -1615, 'net_change': -23218, 'cash_begin': 77375, 'cash_end': 54157}}})
for e in E:
    if e['label'].startswith('Q1'):
        for col in ('cur', 'prior'): e['cf'][col].setdefault('cff', 0)
        e['reading'] += '; no financing-activities line printed in Q1 cash flow (nil), cff=0 and net change = cfo + cfi on the page'
import decl
def qs(key, yr, labs, tol=0, note=None):
    q1, h1, m9 = labs
    o = {'key': key, 'parts': [[q1, 'is', 'cur', key], [h1, 'is_q', 'cur', key]], 'total': [h1, 'is', 'cur', key]}
    return o
QS = tx.quarter_sums([2023, 2024, 2025, 2026], {e['label'] for e in E}, tol={(2025, 'net_income', 'H1+Q3=9M'): (1, 'H1 682 + Q3 727 = 1,409 vs printed 9M 1,408 (rounding as printed)'), (2025, 'pbt', 'H1+Q3=9M'): (1, 'H1 2,466 + Q3 977 = 3,443 vs printed 9M 3,442 (rounding as printed)')})
_ORDER = ['FY2023', 'Q1 2024', 'H1 2024', '9M 2024', 'FY2024']
_BSR = []
for _i in range(len(_ORDER)):
    for _j in range(_i + 1, len(_ORDER)):
        _BSR.append(('bs', '2023-12-31', 'FY', (_ORDER[_i], _ORDER[_j]), 'the 31 Dec 2023 comparative balance sheet total assets/total liabilities (and insurance contract liabilities) differ between filings while total equity 190,757 is identical in all: FY2023 audited 339,800/149,043; Q1 2024 repeats 339,800; H1 2024 prints 343,127/152,370 labelled (Audited) (page rendered and read, foots internally); 9M 2024 prints 335,309/144,552; FY2024 annual 325,127/134,370 after reclassification (note 28 comparative figures reclassified). No restatement explanation is printed for the interim figures', None))
_IFRS17 = []
for _st in ('bs', 'is', 'cf'):
    for _r in ('FY2023', 'Q1 2023', 'H1 2023', '9M 2023'):
        _IFRS17.append((_st, '2022-12-31', 'FY', ('FY2022', _r), 'IFRS 17 transition restatement of 2022: FY2022 as originally published under IFRS 4 (total assets 430,987, total equity 171,577, net loss 9,581) versus the 2022 comparatives re-presented under IFRS 17 in the first IFRS 17 filings (total assets 360,743, total equity 170,062, net loss 6,355); 1 Jan 2022 equity 59,688 restated to 54,947', None))
RESTATEMENTS = decl.declare(E, _BSR + _IFRS17 + [
 ('is', '2023-09-30', '9M', ('9M 2023', '9M 2024'), '9M 2023 comparative: zakat -1,253 and income tax -73 printed separately in the 9M 2023 filing, combined as -1,326 on one line (Zakat and income tax charge) in the 9M 2024 filing; net income 19,440 identical', ['zakat_tax']),
 ('is', '2025-03-31', 'Q1', ('Q1 2025', 'Q1 2026'), 'EPS printed at 2 decimals in the Q1 2025 filing (0.02) and at 4 decimals in Q1 2026 comparatives (0.0223): presentation precision only', ['eps']),
])
if __name__ == '__main__':
    tx.save(S, H, E, {'restatements': RESTATEMENTS, 'quarter_sums': QS})
