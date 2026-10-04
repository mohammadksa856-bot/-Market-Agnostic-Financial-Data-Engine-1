"""AICC / Arabia Insurance Cooperative Company (8160): values typed from rendered pages (image-only primary statements in every transcribed file).
Identities are enforced by check_transcripts.py."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tx, decl
S = '8160'
H = {'symbol': S, 'name': 'ARABIA INSURANCE COOPERATIVE COMPANY (AICC), Tadawul 8160', 'currency': 'SAR', 'unit': 'SAR (whole riyals, as printed; NOT thousands)',
     'conventions': 'whole SAR as printed; cumulative year-to-date as printed (is) and quarter column (is_q); costs negative; insurance_service_result = revenue + service expenses + net reinsurance result; net_insurance_investment_result = insurance service result + net investment income + net insurance finance result; pbt = (gross) income before zakat and income tax; zakat_tax = provision for zakat and income tax; net_income = income after zakat and income tax BEFORE attribution to insurance operations; ni_nci = amount attributed to insurance operations (deducted), ni_parent = income attributable to shareholders (filings from 2023 print the attribution line in FY2023, FY2024 and 9M/H1/Q1 2024-2025; FY2025 and 2026 filings print no attribution line and net_income equals the shareholders result); eps SAR per share as printed; bs prior = prior fiscal year-end as printed in that filing; cash = cash and cash equivalents (term deposits excluded). Labels are PAGE-DERIVED. 9M 2025 prints insurance service expenses as POSITIVE amounts (53,749,930 for 9M and 336,870,742 for Q3) exactly as printed, offset by large negative net reinsurance results; the chain still foots as printed.'}


def bs(ta, tl, te, cash, icl=None):
    d = {'total_assets': ta, 'total_liabilities': tl, 'total_equity': te, 'cash': cash}
    if icl is not None:
        d['insurance_contract_liabilities'] = icl
    return d


def isv(rev, exp, reins, isr, nii, fin, nir, oi, opex, pbt, zakat, ni, eps, nci=None, parent=None):
    d = {'insurance_revenue': rev, 'insurance_service_expenses': exp, 'net_reinsurance_result': reins, 'insurance_service_result': isr, 'total_insurance_service_result': isr,
         'net_investment_income': nii, 'net_insurance_finance_result': fin, 'net_insurance_investment_result': nir, 'other_income': oi, 'other_operating_expenses': opex,
         'pbt': pbt, 'zakat_tax': zakat, 'net_income': ni, 'eps': eps}
    if nci is not None:
        d['ni_nci'] = nci
        d['ni_parent'] = parent
    return d


def cf(cfo, cfi, cff, net, b, e):
    return {'cfo': cfo, 'cfi': cfi, 'cff': cff, 'net_change': net, 'cash_begin': b, 'cash_end': e}


def doc(sha, label, pe, pt, ppe, bsp, reading, pages, bs_, is_, cf_, is_q=None, bs2=None, bs2pe=None):
    e = {'sha256_prefix': sha, 'label': label, 'period_end': pe, 'period_type': pt, 'prior_period_end': ppe, 'bs_prior_period_end': bsp, 'reading': reading, 'pages': pages, 'bs': bs_, 'is': is_, 'cf': cf_}
    if is_q:
        e['is_q'] = is_q
    if bs2:
        e['bs']['prior2'] = bs2
        e['bs_prior2_period_end'] = bs2pe
    return e


E = []
VIS = 'VISUAL: primary statements are image-only pages (zero text); rendered at 1.7x to 1.9x and read by eye; '

# ---------------- FY2022 (IFRS 4 original) ----------------
E.append(doc('5ccb37ec', 'FY2022', '2022-12-31', 'FY', '2021-12-31', '2021-12-31',
 VIS + 'BS p8 (printed 6), IS p9 (printed 7), CF p12 (printed 10); inventory label 2023|FY is publication year; IFRS 4 original; revenue = net revenues (net premiums earned + reinsurance commission + other income); total_liabilities = total liabilities and insurance operations accumulated surplus (liabilities 1,320,168,783 plus insurance operations accumulated surplus lines 2,494,147 and -512,515 = 1,322,150,415, before shareholders equity); pbt = total surplus for the year before zakat; ni_nci = income attributed to insurance operations',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': bs(1544343140, 1322150415, 222192725, 79119498), 'prior': bs(652158209, 436518873, 215639336, 85343072)},
 {'cur': {'revenue': 456787480, 'gross_written_premiums': 733193225, 'net_underwriting_result': 108158162, 'pbt': 13833194, 'zakat_tax': -4500000, 'net_income': 9333194, 'ni_nci': 1055602, 'ni_parent': 8277592, 'eps': 0.31},
  'prior': {'revenue': 300183401, 'gross_written_premiums': 422322603, 'net_underwriting_result': 57145444, 'pbt': 530474, 'zakat_tax': -6047859, 'net_income': -5517385, 'ni_nci': 0, 'ni_parent': -5517385, 'eps': -0.21}},
 {'cur': cf(131343608, -135985780, -1581402, -6223574, 85343072, 79119498), 'prior': cf(-29708910, -31948609, -2326864, -63984382, 149327454, 85343072)}))
E[-1]['declared_footing'] = [{'col': 'prior', 'check': 'cf-sum', 'printed': -63984382, 'computed': -63984383}]


# ---------------- Q1 2023 (zero-text scan, whole file) ----------------
E.append(doc('093df361', 'Q1 2023', '2023-03-31', 'Q1', '2022-03-31', '2022-12-31',
 'VISUAL: whole 39-page file is a zero-text scan (inventory scanned_unread) holding a complete interim set: BS p4 (printed 2; columns 31 Mar 2023, 31 Dec 2022 restated, 1 Jan 2022 restated), IS p5 (printed 3), OCI p6, equity p7 (landscape), CF p8 (printed 6); rendered at 1.8x and read by eye; total_liabilities = liabilities plus insurance operations accumulated surplus; first IFRS 17 interim; no other income line printed',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bs(1610607698, 1110131852, 500475846, 125877111, 1016726219), 'prior': bs(1351994986, 1108858163, 243136823, 79119375, 1055679287)},
 {'cur': isv(197279217, -148636507, -32419152, 16223558, 6405530, -1501412, 21127677, 0, -9565032, 11562644, -3500000, 8062644, 0.15, 740563, 7322081),
  'prior': isv(100218191, -84236544, -21670107, -5688460, 1230098, -395017, -4853379, 0, -4430843, -9284222, -1000000, -10284222, -0.39, 0, -10284222)},
 {'cur': cf(16125492, -219100712, 249732955, 46757736, 79119375, 125877111), 'prior': cf(-8069122, -5144645, -406416, -13620182, 85343023, 71722841)},
 bs2=bs(520240158, 284480914, 235759244, 85343023, 250826332), bs2pe='2022-01-01'))
E[-1]['declared_footing'] = [{'col': 'cur', 'check': 'is-net-ins-inv', 'printed': 21127677, 'computed': 21127676}, {'col': 'cur', 'check': 'is-pbt-chain', 'printed': 11562644, 'computed': 11562645},
                             {'col': 'cur', 'check': 'cf-sum', 'printed': 46757736, 'computed': 46757735}, {'col': 'prior', 'check': 'cf-sum', 'printed': -13620182, 'computed': -13620183}]

# ---------------- FY2023 (first IFRS 17 annual) ----------------
E.append(doc('05b6aab3', 'FY2023', '2023-12-31', 'FY', '2022-12-31', '2022-12-31',
 VIS + 'BS p9 (printed 7; three columns: 2023, 2022 restated, 1 Jan 2022 restated), IS p10 (printed 8), CF p13 (printed 11); inventory label 2024|FY is publication year; cover reads ARABIA INSURANCE COOPERATVE COMPANY (typo as printed); first IFRS 17 annual, 2022 restated (note 4)',
 {'bs': 9, 'is': 10, 'cf': 13},
 {'cur': bs(1799925371, 1240009716, 559915655, 57719509, 1118895267), 'prior': bs(1383530679, 1140727009, 242803670, 79119375, 1065924808)},
 {'cur': isv(838947058, -621372330, -141054122, 76520606, 30529135, -6580804, 100468937, 17531040, -41708309, 76291668, -10000000, 66291668, 1.14, 5829494, 60462174),
  'prior': isv(560650740, -1116858220, 579381656, 23174176, 6678881, -2661277, 27191780, 6857662, -22293663, 11755779, -4500000, 7255779, 0.21, 1055602, 6200177)},
 {'cur': cf(79881442, -348888682, 247607374, -21399866, 79119375, 57719509), 'prior': cf(132334993, -136977240, -1581400, -6223647, 85343023, 79119376)},
 bs2=bs(520313465, 285090103, 235223362, 85343023, 250826332), bs2pe='2022-01-01'))

# ---------------- FY2024 ----------------
E.append(doc('afa49c17', 'FY2024', '2024-12-31', 'FY', '2023-12-31', '2023-12-31',
 VIS + 'BS p8 (printed 6), IS p9 (printed 7), CF p12 (printed 10); inventory label 2025|FY is publication year; inventory statement_pages put BS, IS and CF all on p13 which is a notes page',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': bs(1726033997, 1121096037, 604937960, 67784373, 993085264), 'prior': bs(1799925371, 1240009716, 559915655, 57719509, 1118895267)},
 {'cur': isv(694691468, -488149657, -169877736, 36664075, 38074548, -6081222, 68657401, 3075455, -30605112, 41127744, -9400000, 31727744, 0.57, 1580139, 30147605),
  'prior': isv(838947058, -621372330, -141054122, 76520606, 30529135, -6580804, 100468937, 17531040, -41708309, 76291668, -10000000, 66291668, 1.14, 5829494, 60462174)},
 {'cur': cf(-18597175, 31968036, -3305997, 10064864, 57719509, 67784373), 'prior': cf(79881442, -348888682, 247607374, -21399866, 79119375, 57719509)}))

# ---------------- FY2025 ----------------
E.append(doc('607fd3a1', 'FY2025', '2025-12-31', 'FY', '2024-12-31', '2024-12-31',
 VIS + 'BS p8 (printed 6), IS p9 (printed 7), CF p12 (printed 10); inventory label 2026|FY is publication year; the 2024 comparative columns are re-presented (see restatements)',
 {'bs': 8, 'is': 9, 'cf': 12},
 {'cur': bs(1254533749, 683551269, 570982480, 84918484, 573711282), 'prior': bs(1726033997, 1121096037, 604937960, 67784373, 1001933463)},
 {'cur': isv(851122253, -199136372, -667517349, -15531468, 922285, -4202168, -18811351, 1872603, -17242553, -34181301, -11000000, -45181301, -0.85),
  'prior': isv(694691468, -489729796, -169877736, 35083936, 38074548, -6081222, 67077262, 3075455, -30605112, 39547605, -9400000, 30147605, 0.57)},
 {'cur': cf(122130997, -101321100, -3675786, 17134111, 67784373, 84918484), 'prior': cf(-22249333, 35620194, -3305997, 10064864, 57719509, 67784373)}))

# ---------------- 2025 interims ----------------
E.append(doc('c5c2ce5b', 'Q1 2025', '2025-03-31', 'Q1', '2024-03-31', '2024-12-31',
 VIS + 'BS p4 (printed 2), IS p5 (printed 3), CF p8 (printed 6)',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bs(1760520837, 1148490650, 612030187, 97976165, 999053788), 'prior': bs(1726033997, 1121096037, 604937960, 67784373, 993085264)},
 {'cur': isv(171472735, -127927714, -45494479, -1949458, 9222428, -1091161, 6181809, 1786071, -1520303, 6447577, -2000000, 4447577, 0.08, 0, 4447577),
  'prior': isv(198271385, -137242967, -55045894, 5982524, 9351511, -1823696, 13510339, 3337580, -6576456, 10271463, -2000000, 8271463, 0.15, 435625, 7835838)},
 {'cur': cf(51050162, -19805220, -1053150, 30191792, 67784373, 97976165), 'prior': cf(2999768, 41994873, -75149, 44919492, 57719509, 102639001)}))

E.append(doc('52d244a2', 'H1 2025', '2025-06-30', 'H1', '2024-06-30', '2024-12-31',
 VIS + 'BS p4 (printed 2), IS p5 (printed 3; columns Q2 2025, Q2 2024, 6M 2025, 6M 2024), CF p8 (printed 6)',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bs(1878745912, 1261564009, 617181903, 326432394, 1068069232), 'prior': bs(1726033997, 1121096037, 604937960, 67784373, 993085264)},
 {'cur': isv(369236573, -283120812, -86102487, 13274, 19380363, -2115501, 17278136, 1787779, -5991445, 13074470, -3500000, 9574470, 0.18, 0, 9574470),
  'prior': isv(367829286, -258615244, -89213120, 20000922, 18899059, -3438769, 35461212, 3140573, -11009191, 27592594, -5000000, 22592594, 0.40, 1533247, 21059347)},
 {'cur': cf(167887355, 92526963, -1766297, 258648021, 67784373, 326432394), 'prior': cf(-8718240, 111061387, -1446459, 100896688, 57719509, 158616197)},
 is_q={'cur': isv(197763838, -155193098, -40608008, 1962732, 10157935, -1024340, 11096327, 1708, -4471142, 6626893, -1500000, 5126893, 0.10, 0, 5126893),
       'prior': isv(169557901, -121372276, -34167227, 14018398, 9547547, -1615073, 21950872, -197006, -4432735, 17321131, -3000000, 14321131, 0.25, 1097622, 13223509)}))

E.append(doc('373def63', '9M 2025', '2025-09-30', '9M', '2024-09-30', '2024-12-31',
 VIS + 'BS p4 (printed 2), IS p5 (printed 3; columns Q3 2025, Q3 2024, 9M 2025, 9M 2024), CF p8 (printed 6); insurance service expenses printed as POSITIVE (53,749,930 for 9M, 336,870,742 for Q3) with net reinsurance -634,768,356 / -548,665,869; transcribed as printed',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bs(1229878757, 612256930, 617621827, 144177311, 516189982), 'prior': bs(1726033997, 1121096037, 604937960, 67784373, 993085264)},
 {'cur': isv(589360583, 53749930, -634768356, 8342157, 20017271, -3022904, 25336524, 2070987, -12347963, 15059548, -4500000, 10559548, 0.19, 631163, 9928385),
  'prior': isv(532533963, -366629132, -125055596, 40849235, 28092841, -4913692, 64028384, 3075724, -23411696, 43692412, -6500000, 37192412, 0.65, 2572361, 34620051)},
 {'cur': cf(104972040, -25834803, -2744299, 76392938, 67784373, 144177311), 'prior': cf(-37303461, 120350168, -2500918, 80545789, 57719509, 138265298)},
 is_q={'cur': isv(220124010, 336870742, -548665869, 8328883, 636908, -907403, 8058388, 283208, -6356518, 1985078, -1000000, 985078, 0.01, 631163, 353915),
       'prior': isv(164704677, -108013888, -35842476, 20848313, 9193782, -1474923, 28567172, -64849, -12402505, 16099818, -1500000, 14599818, 0.26, 1039114, 13560704)}))

# ---------------- 2026 interims ----------------
E.append(doc('0caa9bbb', 'Q1 2026', '2026-03-31', 'Q1', '2025-03-31', '2025-12-31',
 VIS + 'BS p4 (printed 2), IS p5 (printed 3), CF p8 (printed 6); no attribution line printed',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bs(1235620719, 679155889, 556464830, 71796964, 527007465), 'prior': bs(1254533749, 683551269, 570982480, 84918484, 573711282)},
 {'cur': isv(246809694, -244141090, -18041600, -15372996, 8749912, -1054968, -7678052, -125394, -6501012, -14304458, -500000, -14804458, -0.28),
  'prior': isv(171472735, -127927714, -45494479, -1949458, 9222428, -1091161, 6181809, 1786071, -1520303, 6447577, -2000000, 4447577, 0.08)},
 {'cur': cf(-63776296, 51818376, -1163600, -13121520, 84918484, 71796964), 'prior': cf(51050872, -19805930, -1053150, 30191792, 67784373, 97976165)}))

E.append(doc('bac3bec3', 'H1 2026', '2026-06-30', 'H1', '2025-06-30', '2025-12-31',
 VIS.replace('image-only pages (zero text)', 'pages 4-8 have a text layer only partly (BS p4 and CF p8 text empty, IS p5 text); all three') + 'BS p4 (printed 2), IS p5 (printed 3; columns Q2 2026, Q2 2025, 6M 2026, 6M 2025), CF p8 (printed 6); segment note p36 prints total assets 1,131,330,217 and liabilities 586,665,582 (differs from the primary BS by 10,048,971; equity identical), not reconciled',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bs(1121281246, 576616611, 544664635, 115860589, 451772788), 'prior': bs(1254533749, 683551269, 570982480, 84918484, 573711282)},
 {'cur': isv(486019879, -449761576, -57937876, -21679573, 11323823, -2238310, -12594060, 0, -11897199, -24491259, -2250000, -26741259, -0.50),
  'prior': isv(369236573, -283120812, -86102487, 13274, 19380363, -2115501, 17278136, 1787779, -5991445, 13074470, -3500000, 9574470, 0.18)},
 {'cur': cf(-100313373, 132385286, -1129808, 30942105, 84918484, 115860589), 'prior': cf(167887561, 92526757, -1766297, 258648021, 67784373, 326432394)},
 is_q={'cur': isv(239210185, -205620486, -39896276, -6306577, 2573911, -1183342, -4916008, 125394, -5396187, -10186801, -1750000, -11936801, -0.23),
       'prior': isv(197763838, -155193098, -40608008, 1962732, 10157935, -1024340, 11096327, 1708, -4471142, 6626893, -1500000, 5126893, 0.10)}))

_R = []


def _pairs(stmt, pe, order, reason, keys=None, pt='FY'):
    return [(stmt, pe, pt, (order[i], order[j]), reason, keys) for i in range(len(order)) for j in range(i + 1, len(order))]


_R += _pairs('bs', '2022-12-31', ['Q1 2023', 'FY2023'], '31 Dec 2022 restated balance sheet differs between the Q1 2023 interim (total assets 1,351,994,986; total equity 243,136,823; insurance contract liabilities 1,055,679,287) and the FY2023 annual (1,383,530,679; 242,803,670; 1,065,924,808): the IFRS 17 transition figures were revised between filings, no reconciliation read')
_R += _pairs('bs', '2022-01-01', ['Q1 2023', 'FY2023'], '1 Jan 2022 IFRS 17 opening balance sheet differs between the Q1 2023 interim (total assets 520,240,158; equity 235,759,244) and the FY2023 annual (520,313,465; 235,223,362)')
for _st in ('bs', 'is', 'cf'):
    _R += _pairs(_st, '2022-12-31', ['FY2022', 'FY2023'] if _st != 'bs' else ['FY2022', 'FY2023'], 'IFRS 17 transition restatement of 2022 (FY2023 annual, comparative marked Restated, note 4): FY2022 as published under IFRS 4 (total assets 1,544,343,140; equity 222,192,725; net income attributable 8,277,592; EPS 0.31; operating cash flow 131,343,608; cash 79,119,498) versus restated (1,383,530,679; 242,803,670; 6,200,177; 0.21; 132,334,993; 79,119,375)')
_R += _pairs('bs', '2022-12-31', ['FY2022', 'Q1 2023'], 'IFRS 17 transition restatement of 31 Dec 2022: FY2022 as published under IFRS 4 (total assets 1,544,343,140; equity 222,192,725) versus restated in the Q1 2023 interim (1,351,994,986; 243,136,823)')
_R += _pairs('bs', '2024-12-31', ['FY2024', 'Q1 2025', 'H1 2025', '9M 2025', 'FY2025'], 'FY2024 balance sheet re-presented in the FY2025 annual: insurance contract liabilities 993,085,264 -> 1,001,933,463 with accrued expenses and other liabilities reduced by the same 8,848,199 (reclassification, total liabilities 1,121,096,037 unchanged); the 2025 interims carry the original presentation', None)
_R += _pairs('is', '2024-12-31', ['FY2024', 'FY2025'], 'FY2024 income statement re-presented in the FY2025 annual: insurance service expenses -488,149,657 -> -489,729,796 (-1,580,139) so insurance service result 36,664,075 -> 35,083,936; the attribution to insurance operations (1,580,139) is now inside insurance expenses so profit before zakat 41,127,744 -> 39,547,605 and the net income line equals the shareholders result 30,147,605 (previously 31,727,744 before attribution); shareholders net income unchanged', None)
_R += _pairs('cf', '2024-12-31', ['FY2024', 'FY2025'], 'FY2024 cash flow re-presented in the FY2025 annual: operating -18,597,175 -> -22,249,333 and investing 31,968,036 -> 35,620,194 (3,652,158 reclassified); net change 10,064,864 identical', None)
_R += _pairs('cf', '2025-03-31', ['Q1 2025', 'Q1 2026'], 'Q1 2025 cash flow comparative in the Q1 2026 filing: operating 51,050,162 -> 51,050,872 and investing -19,805,220 -> -19,805,930 (710 reclassified); net change identical', None, 'Q1')
_R += _pairs('cf', '2025-06-30', ['H1 2025', 'H1 2026'], 'H1 2025 cash flow comparative in the H1 2026 filing: operating 167,887,355 -> 167,887,561 and investing 92,526,963 -> 92,526,757 (206 reclassified); net change identical', None, 'H1')
RESTATEMENTS = decl.declare(E, _R, quiet=True)
QS = tx.quarter_sums([2025, 2026], {e['label'] for e in E}, tol={})
if __name__ == '__main__':
    import decl as _d
    _d.show(E)
    tx.save(S, H, E, {'restatements': RESTATEMENTS, 'quarter_sums': QS})
