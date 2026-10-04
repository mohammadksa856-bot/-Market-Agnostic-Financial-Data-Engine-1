import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tx, decl
from tx import std
S = '8040'
E = []
H = {'symbol': S, 'name': 'MUTAKAMELA INSURANCE COMPANY (formerly Allianz Saudi Fransi Cooperative Insurance Company), Tadawul 8040', 'currency': 'SAR', 'unit': 'SAR (whole riyals, as printed; NOT thousands)',
     'conventions': 'whole SAR as printed in every statement of this issuer; cumulative year-to-date as printed (is) and quarter column (is_q); costs negative; insurance_service_result = result from the Company directly written business (revenue + service expenses + net reinsurance result); total_insurance_service_result adds share of surplus from insurance pools; pbt = net income before zakat and income tax; zakat_tax = provision for zakat and (income) tax as one line; net_income attributable to shareholders after zakat and tax; eps SAR per share as printed; bs prior = prior fiscal year-end as printed in that filing (may be restated); cash = cash and cash equivalents. Labels are PAGE-DERIVED, not collector labels. Image-only pages read by eye.'}


def man(sha, label, pe, pt, ppe, bsp, reading, pages, bs, is_, cf, is_q=None, bs2=None, bs2pe=None):
    e = {'sha256_prefix': sha, 'label': label, 'period_end': pe, 'period_type': pt, 'prior_period_end': ppe, 'bs_prior_period_end': bsp, 'reading': reading, 'pages': pages, 'bs': bs, 'is': is_, 'cf': cf}
    if is_q:
        e['is_q'] = is_q
    if bs2:
        e['bs']['prior2'] = bs2
        e['bs_prior2_period_end'] = bs2pe
    return e


# ---- FY2022 original (IFRS 4), image pages read by eye
E.append(man('978d3b51', 'FY2022', '2022-12-31', 'FY', '2021-12-31', '2021-12-31',
 'VISUAL: statements are image-only pages in this PDF (pp7-11 zero text); BS p7 (printed 5), IS p8 (printed 6), CF p11 (printed 9) rendered at 2x and read by eye; inventory label 2023|FY is the publication year; IFRS 4 presentation; revenue = net revenues; pbt = net income attributable to shareholders before zakat and tax (after surplus attributed to insurance operations); zakat_tax = zakat charge + income tax charge',
 {'bs': 7, 'is': 8, 'cf': 11},
 {'cur': {'total_assets': 2537136500, 'total_liabilities': 1837259570, 'total_equity': 699876930, 'cash': 194904123}, 'prior': {'total_assets': 2583326092, 'total_liabilities': 1872033068, 'total_equity': 711293024, 'cash': 160979644}},
 {'cur': {'revenue': 485578869, 'gross_written_premiums': 848254771, 'net_underwriting_result': 102083601, 'pbt': 28035486, 'zakat_tax': -8116139, 'net_income': 19919347, 'eps': 0.33}, 'prior': {'revenue': 422669602, 'gross_written_premiums': 763115103, 'net_underwriting_result': 115652799, 'pbt': 16485325, 'zakat_tax': -10865896, 'net_income': 5619429, 'eps': 0.09}},
 {'cur': {'cfo': 112222803, 'cfi': -74643242, 'cff': -3655082, 'net_change': 33924479, 'cash_begin': 160979644, 'cash_end': 194904123}, 'prior': {'cfo': -162946, 'cfi': -161091847, 'cff': -2811788, 'net_change': -164066581, 'cash_begin': 325046225, 'cash_end': 160979644}}))

# ---- FY2023 (first IFRS 17 annual), BS 3 columns
E.append(man('1949fedd', 'FY2023', '2023-12-31', 'FY', '2022-12-31', '2022-12-31',
 'VISUAL: statements are image-only (pp10-14 zero text); BS p10 (printed 9; columns 2023, 2022 restated, 1 Jan 2022 restated), IS p11 (printed 10), CF p14 (printed 13, landscape page) rendered and read by eye; inventory label 2024|FY is the publication year (cover period not text-detectable); first IFRS 17 annual, 2022 comparatives restated',
 {'bs': 10, 'is': 11, 'cf': 14},
 {'cur': {'total_assets': 2155386277, 'total_liabilities': 1354701964, 'total_equity': 800684313, 'cash': 126187903, 'insurance_contract_liabilities': 1111134900}, 'prior': {'total_assets': 2050052354, 'total_liabilities': 1304372651, 'total_equity': 745679703, 'cash': 194590855, 'insurance_contract_liabilities': 1053789268}},
 {'cur': {'insurance_revenue': 862625067, 'insurance_service_expenses': -704853280, 'net_reinsurance_result': -139862075, 'insurance_service_result': 17909712, 'pool_surplus': 12294000, 'total_insurance_service_result': 30203712, 'net_investment_income': 96896522, 'net_insurance_finance_result': -54112222, 'net_insurance_investment_result': 72988012, 'other_operating_expenses': -23767776, 'pbt': 49220236, 'zakat_tax': -12233344, 'net_income': 36986892, 'eps': 0.62},
  'prior': {'insurance_revenue': 735650282, 'insurance_service_expenses': -482595734, 'net_reinsurance_result': -248455299, 'insurance_service_result': 4599249, 'pool_surplus': 15330000, 'total_insurance_service_result': 19929249, 'net_investment_income': 27771255, 'net_insurance_finance_result': -6515068, 'net_insurance_investment_result': 41185436, 'other_operating_expenses': -24493495, 'pbt': 16691941, 'zakat_tax': -8116139, 'net_income': 8575802, 'eps': 0.14}},
 {'cur': {'cfo': 142265736, 'cfi': -202970355, 'cff': -7698333, 'net_change': -68402952, 'cash_begin': 194590855, 'cash_end': 126187903}, 'prior': {'cfo': 104490846, 'cfi': -67057981, 'cff': -3655082, 'net_change': 33777783, 'cash_begin': 160813072, 'cash_end': 194590855}},
 bs2={'total_assets': 2245206738, 'total_liabilities': 1489375863, 'total_equity': 755830875, 'cash': 160813072, 'insurance_contract_liabilities': 1324704985}, bs2pe='2022-01-01'))

# ---- FY2024 as originally published
E.append(man('a53dc12b', 'FY2024', '2024-12-31', 'FY', '2023-12-31', '2023-12-31',
 'VISUAL: statements are image-only (pp7-12 zero text); BS p8 (printed 6), IS p9 (printed 7), CF p12 (printed 10) rendered at 2x and read by eye; inventory label 2025|FY is the publication year; cover reads MUTAKAMELA INSURANCE COMPANY (formerly ALLIANZ SAUDI FRANSI COOPERATIVE INSURANCE COMPANY)',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': {'total_assets': 2048366016, 'total_liabilities': 1235274655, 'total_equity': 813091361, 'cash': 78672393, 'insurance_contract_liabilities': 1028139843}, 'prior': {'total_assets': 2155386277, 'total_liabilities': 1354701964, 'total_equity': 800684313, 'cash': 126187903, 'insurance_contract_liabilities': 1111134900}},
 {'cur': {'insurance_revenue': 873885304, 'insurance_service_expenses': -753155692, 'net_reinsurance_result': -117619163, 'insurance_service_result': 3110449, 'pool_surplus': 5063916, 'total_insurance_service_result': 8174365, 'net_investment_income': 85354481, 'net_insurance_finance_result': -31475601, 'net_insurance_investment_result': 62053245, 'other_operating_expenses': -35577466, 'pbt': 26475779, 'zakat_tax': -11308704, 'net_income': 15167075, 'eps': 0.26},
  'prior': {'insurance_revenue': 862625067, 'insurance_service_expenses': -704853280, 'net_reinsurance_result': -139862075, 'insurance_service_result': 17909712, 'pool_surplus': 12294000, 'total_insurance_service_result': 30203712, 'net_investment_income': 96896522, 'net_insurance_finance_result': -54112222, 'net_insurance_investment_result': 72988012, 'other_operating_expenses': -23767776, 'pbt': 49220236, 'zakat_tax': -12233344, 'net_income': 36986892, 'eps': 0.62}},
 {'cur': {'cfo': -65604502, 'cfi': 26859485, 'cff': -8770493, 'net_change': -47515510, 'cash_begin': 126187903, 'cash_end': 78672393}, 'prior': {'cfo': 142265736, 'cfi': -202970355, 'cff': -7698333, 'net_change': -68402952, 'cash_begin': 194590855, 'cash_end': 126187903}}))

# ---- FY2025 (2024 and 2023 BS restated for prior-period error, note 33)
E.append(man('226217a9', 'FY2025', '2025-12-31', 'FY', '2024-12-31', '2024-12-31',
 'VISUAL: statements are image-only (pp4-9 and 12 zero text); BS p8 (printed 6; columns 2025, 2024 restated, 2023 restated), IS p9 (printed 7), CF p12 (printed 10) rendered at 2x and read by eye; inventory label 2026|FY is the publication year; note 33 (text pp121-123) corrects a material prior-year error in insurance contract assets/liabilities and statutory reserve at 31 Dec 2023 and 31 Dec 2024',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': {'total_assets': 1894005958, 'total_liabilities': 1170115439, 'total_equity': 723890519, 'cash': 63292063, 'insurance_contract_liabilities': 945066527}, 'prior': {'total_assets': 1987355223, 'total_liabilities': 1285062892, 'total_equity': 702292331, 'cash': 78672393, 'insurance_contract_liabilities': 1077928080}},
 {'cur': {'insurance_revenue': 879806971, 'insurance_service_expenses': -519865567, 'net_reinsurance_result': -352525979, 'insurance_service_result': 7415425, 'pool_surplus': 4187544, 'total_insurance_service_result': 11602969, 'net_investment_income': 45798125, 'net_insurance_finance_result': -11807915, 'net_insurance_investment_result': 45593179, 'other_operating_expenses': -28012749, 'pbt': 17580430, 'zakat_tax': -10174394, 'net_income': 7406036, 'eps': 0.13},
  'prior': {'insurance_revenue': 873885304, 'insurance_service_expenses': -753155692, 'net_reinsurance_result': -117619163, 'insurance_service_result': 3110449, 'pool_surplus': 5063916, 'total_insurance_service_result': 8174365, 'net_investment_income': 85354481, 'net_insurance_finance_result': -31475601, 'net_insurance_investment_result': 62053245, 'other_operating_expenses': -35577466, 'pbt': 26475779, 'zakat_tax': -11308704, 'net_income': 15167075, 'eps': 0.26}},
 {'cur': {'cfo': -54991225, 'cfi': 42527633, 'cff': -2916738, 'net_change': -15380330, 'cash_begin': 78672393, 'cash_end': 63292063}, 'prior': {'cfo': -65604502, 'cfi': 26859485, 'cff': -8770493, 'net_change': -47515510, 'cash_begin': 126187903, 'cash_end': 78672393}},
 bs2={'total_assets': 2062069139, 'total_liabilities': 1372183856, 'total_equity': 689885283, 'cash': 126187903, 'insurance_contract_liabilities': 1128616792}, bs2pe='2023-12-31'))


MUT = {'net_reinsurance_result': r'^net expenses from reinsurance', 'insurance_service_result': r'directly written business', 'pool_surplus': r'^share of surplus from insurance pools',
       'total_insurance_service_result': r'^(total )?insurance service result$', 'net_investment_income': r'^net investment (and other )?income', 'net_insurance_finance_result': r'^net insurance finance',
       'net_insurance_investment_result': r'^net insurance and investment result', 'other_operating_expenses': r'^other operating expenses'}


def c2(p):
    return {'page': p, 'cols': {'cur': -2, 'prior': -1}}


def mt_cum(sha, label, pe, pt, ppe, bsp, pgs, reading, bscols=None, extra=None):
    """text-layer interim with Q2/Q3 quarter columns (4 IS columns): Q cur, Q prior, YTD cur, YTD prior"""
    ia = dict(MUT); ia.update(extra or {})
    return std(S, sha, label, pe, pt, ppe, bsp, reading, {'bs': bscols or c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': ia}, 'is_q': {'page': pgs[1], 'cols': {'cur': -4, 'prior': -3}, 'add': ia}, 'cf': c2(pgs[2])})


def mt_q1(sha, label, pe, ppe, bsp, pgs, reading, bscols=None, extra=None):
    ia = dict(MUT); ia.update(extra or {})
    return std(S, sha, label, pe, 'Q1', ppe, bsp, reading, {'bs': bscols or c2(pgs[0]), 'is': {'page': pgs[1], 'cols': {'cur': -2, 'prior': -1}, 'add': ia}, 'cf': c2(pgs[2])})


E.append(mt_cum('acc8cacc', 'H1 2025', '2025-06-30', 'H1', '2024-06-30', '2024-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q2 2025, Q2 2024, 6M 2025, 6M 2024) CF p8; BS comparative column is 31 Dec 2024 as originally published (before the note 33 restatement)'))
E.append(mt_cum('58559b21', 'H1 2026', '2026-06-30', 'H1', '2025-06-30', '2025-12-31', (4, 5, 8), 'text layer BS p4 IS p5 (cols Q2 2026, Q2 2025, 6M 2026, 6M 2025) CF p8'))

from mut_vis import VIS
E.extend(VIS)
_D = {e['label']: e for e in E}
_D['H1 2025'].setdefault('declared_footing', []).append({'col': 'cur', 'check': 'is_q-net-ins-inv', 'printed': 17733408, 'computed': 17733407})
_D['H1 2023'].setdefault('declared_footing', []).append({'col': 'prior', 'check': 'cf-roll', 'printed': 149244713, 'computed': 149244714})

TOL = {(2025, 'pbt', 'Q1+Q2=H1'): (1, 'printed rounding 8,503,206 + 11,482,145 = 19,985,351 vs 19,985,350'), (2025, 'net_income', 'Q1+Q2=H1'): (1, 'printed rounding 5,804,345 + 8,719,888 = 14,524,233 vs 14,524,232'), (2026, 'net_income', 'Q1+Q2=H1'): (1, 'printed rounding -10,628,132 + -11,393,778 = -22,021,910 vs -22,021,909')}


def _pairs(stmt, pe, order, reason, keys=None, pt='FY'):
    return [(stmt, pe, pt, (order[i], order[j]), reason, keys) for i in range(len(order)) for j in range(i + 1, len(order))]


_R = []
_R += _pairs('bs', '2022-12-31', ['FY2022', 'Q1 2023', 'H1 2023', 'FY2023'], '31 Dec 2022 balance sheet: FY2022 as published under IFRS 4 (total assets 2,537,136,500, equity 699,876,930) versus the IFRS 17 transition restatement printed in the 2023 interims (2,119,368,916 / 748,744,118) and re-stated again in the FY2023 annual (2,050,052,354 / 745,679,703); restatement basis changes between 2023 filings, no reconciliation printed in the pages read')
_R += _pairs('is', '2022-12-31', ['FY2022', 'FY2023'], 'FY2022 net income 19,919,347 (IFRS 4, as published) versus 8,575,802 restated under IFRS 17 in the FY2023 annual')
_R += _pairs('cf', '2022-12-31', ['FY2022', 'FY2023'], 'FY2022 cash flow as published versus IFRS 17 restated comparative in the FY2023 annual (opening cash 160,979,644 vs 160,813,072; closing cash 194,904,123 vs 194,590,855)')
_R += _pairs('bs', '2023-12-31', ['FY2023', 'Q1 2024', 'H1 2024', '9M 2024', 'FY2024', 'Q1 2025', 'H1 2025', 'FY2025', '9M 2025'], '31 Dec 2023 balance sheet restated for a material prior-year error (FY2025 note 33, restatements A and B: insurance contract assets overstated and liabilities understated, opening retained earnings overstated by about SAR 110 million, statutory reserve transfer reversed): total equity 800,684,313 as audited -> 689,885,283 restated; first shown restated in the 9M 2025 filing')
_R += _pairs('bs', '2022-01-01', ['Q1 2023', 'H1 2023', 'FY2023'], '1 Jan 2022 IFRS 17 opening balance sheet: total assets 2,249,103,623 in the Q1/H1 2023 filings versus 2,245,206,738 in the FY2023 annual (insurance contract liabilities 1,275,940,332 vs 1,324,704,985); total equity 755,830,875 identical')
_R += _pairs('bs', '2024-12-31', ['FY2024', 'Q1 2025', 'H1 2025', 'FY2025', '9M 2025'], '31 Dec 2024 balance sheet restated for the prior-year error in FY2025 note 33 (insurance contract assets 142,596,003 -> 81,585,210; insurance contract liabilities 1,028,139,843 -> 1,077,928,080; total equity 813,091,361 -> 702,292,331); FY2024 audited, Q1 and H1 2025 repeat the original, 9M 2025 and FY2025 carry the restated figures')
_R += [('is', '2025-06-30', 'H1', ('H1 2025', 'H1 2026'), 'EPS printed to three decimals in the H1 2025 filing (0.243) and two decimals in the H1 2026 comparative (0.24): precision only', ['eps']),
       ('is', '2024-06-30', 'H1', ('H1 2024', 'H1 2025'), 'H1 2024 EPS 0.177 in the H1 2024 filing vs 0.176 in the H1 2025 comparative: printed rounding (net income 10,588,825 identical)', ['eps']),
       ('is', '2023-06-30', 'H1', ('H1 2023', 'H1 2024'), 'H1 2023 EPS 0.33 (two decimals) vs 0.334 (three) in H1 2024 comparative: precision only; other H1 2023 differences are declared separately', ['eps'])]
_R += _pairs('is', '2023-03-31', ['Q1 2023', 'Q1 2024'], 'Q1 2023 comparative restated in the Q1 2024 filing (labelled Restated): service expenses -177,269,912 -> -175,340,535, investment income 24,288,639 -> 17,070,639 with 7,218,000 surplus from insurance pools moved into the insurance service result; profit before zakat 13,507,505 and net income 9,602,927 unchanged', ['insurance_service_expenses', 'insurance_service_result', 'net_investment_income'], 'Q1')
_R += _pairs('is', '2023-06-30', ['H1 2023', 'H1 2024'], 'H1 2023 comparative restated in the H1 2024 filing (labelled Restated): service expenses -334,785,808 -> -317,743,853, insurance service result -831,762 -> 16,210,193 (adds pool surplus 7,218,000), investment income 62,835,422 -> 55,617,422; profit before zakat 26,673,287 and net income 20,012,215 unchanged', ['insurance_service_expenses', 'insurance_service_result', 'net_investment_income'], 'H1')
_R += _pairs('cf', '2023-06-30', ['H1 2023', 'H1 2024'], 'H1 2023 net cash from operating activities printed 67,759,541 in the H1 2023 filing (does not foot: components add to 67,756,541) and 67,756,541 in the H1 2024 comparative', ['cfo'], 'H1')
_R += _pairs('is', '2023-09-30', ['9M 2024'], 'placeholder', None, '9M')
RESTATEMENTS = decl.declare(E, _R)
QS = tx.quarter_sums([2023, 2024, 2025, 2026], {e['label'] for e in E}, tol=TOL)
if __name__ == '__main__':
    import decl as _d
    _d.show(E)
    tx.save(S, H, E, {'restatements': RESTATEMENTS, 'quarter_sums': QS})
