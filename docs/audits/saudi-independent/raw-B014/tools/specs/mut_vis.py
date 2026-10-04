"""Visually read (image-only page) Mutakamela / Allianz Saudi Fransi interim statement sets. Values typed from rendered pages; identities are enforced by check_transcripts.py."""


def bsv(ta, tl, te, cash, icl=None):
    d = {'total_assets': ta, 'total_liabilities': tl, 'total_equity': te, 'cash': cash}
    if icl is not None:
        d['insurance_contract_liabilities'] = icl
    return d


def isv(rev, exp, reins, direct, pool, total, nii, fin, nir, opex, pbt, zakat, ni, eps):
    return {'insurance_revenue': rev, 'insurance_service_expenses': exp, 'net_reinsurance_result': reins, 'insurance_service_result': direct, 'pool_surplus': pool,
            'total_insurance_service_result': total, 'net_investment_income': nii, 'net_insurance_finance_result': fin, 'net_insurance_investment_result': nir,
            'other_operating_expenses': opex, 'pbt': pbt, 'zakat_tax': zakat, 'net_income': ni, 'eps': eps}


def cfv(cfo, cfi, cff, net, b, e):
    return {'cfo': cfo, 'cfi': cfi, 'cff': cff, 'net_change': net, 'cash_begin': b, 'cash_end': e}


def doc(sha, label, pe, pt, ppe, bsp, reading, pages, bs, is_, cf, is_q=None, bs2=None, bs2pe=None):
    e = {'sha256_prefix': sha, 'label': label, 'period_end': pe, 'period_type': pt, 'prior_period_end': ppe, 'bs_prior_period_end': bsp, 'reading': reading, 'pages': pages, 'bs': bs, 'is': is_, 'cf': cf}
    if is_q:
        e['is_q'] = is_q
    if bs2:
        e['bs']['prior2'] = bs2
        e['bs_prior2_period_end'] = bs2pe
    return e


VIS = []

VIS.append(doc('090d92ef', 'Q1 2026', '2026-03-31', 'Q1', '2025-03-31', '2025-12-31',
 'VISUAL: statement pages 4-8 are image-only (zero text); BS p4 (printed 2), IS p5 (printed 3), CF p8 (printed 6) rendered at 1.8x and read by eye',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(1851421146, 1137063308, 714357838, 32058015, 919253169), 'prior': bsv(1894005958, 1170115439, 723890519, 63292063, 945066527)},
 {'cur': isv(194654905, -138182983, -68231402, -11759480, 0, -11759480, 14404230, -5365562, -2720812, -6247058, -8967870, -1660262, -10628132, -0.178),
  'prior': isv(206359243, -94843446, -105461660, 6054137, 335779, 6389916, 17926569, -10404848, 13911637, -5408431, 8503206, -2698861, 5804345, 0.097)},
 {'cur': cfv(-29989195, -294, -1244559, -31234048, 63292063, 32058015), 'prior': cfv(-4936658, -10733848, -1708088, -17378594, 78672393, 61293799)}))

VIS.append(doc('f2ab33c6', 'Q1 2025', '2025-03-31', 'Q1', '2024-03-31', '2024-12-31',
 'VISUAL: statement pages 4-8 are image-only (inventory class partial_statements is wrong: BS p4, IS p5, CF p8 are all present); rendered at 1.8x and read by eye; BS comparative is 31 Dec 2024 as originally published (before the note 33 restatement)',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(2042325735, 1223108759, 819216976, 61293799, 1034670682), 'prior': bsv(2048366016, 1235274655, 813091361, 78672393, 1028139843)},
 {'cur': isv(206359243, -94843446, -105461660, 6054137, 335779, 6389916, 17926569, -10404848, 13911637, -5408431, 8503206, -2698861, 5804345, 0.097),
  'prior': isv(231980300, -205153581, -28155524, -1328805, 3611916, 2283111, 31828572, -15747121, 18364562, -4358358, 14006204, -4018165, 9988039, 0.167)},
 {'cur': cfv(-4936658, -10733848, -1708088, -17378594, 78672393, 61293799), 'prior': cfv(14819986, -4426471, -1731445, 8662070, 126187903, 134849973)}))

VIS.append(doc('fb520870', '9M 2025', '2025-09-30', '9M', '2024-09-30', '2024-12-31',
 'VISUAL: statement pages 4-8 are image-only; BS p4 (printed 2; three columns: 30 Sep 2025, 31 Dec 2024 restated, 1 Jan 2024 restated), IS p5 (printed 3; columns Q3 2025, Q3 2024, 9M 2025, 9M 2024), CF p8 (printed 6; 9M 2024 labelled Restated) rendered at 1.8x and read by eye',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(1968776946, 1249313018, 719463928, 49600041, 963679479), 'prior': bsv(1987355223, 1285062892, 702292331, 78672393, 1077928080)},
 {'cur': isv(648575610, -354224339, -276300702, 18050569, 3937544, 21988113, 42748911, -14788889, 49948135, -26737229, 23210906, -8137784, 15073122, 0.252),
  'prior': isv(675466282, -591591024, -75572366, 8302892, 3611916, 11914808, 72422218, -31930672, 52406354, -27321404, 25084950, -9975511, 15109439, 0.254)},
 {'cur': cfv(-63568687, 35042486, -546151, -29072352, 78672393, 49600041), 'prior': cfv(-35356226, 41679217, -8366278, -2043287, 126187903, 124144616)},
 is_q={'cur': isv(221628997, -124630886, -92042044, 4956067, 2636443, 7592510, 15835911, -5125330, 18303091, -15077535, 3225556, -2676666, 548890, 0.009),
       'prior': isv(205158252, -167564227, -31165958, 6428067, 0, 6428067, 29314868, -15402182, 20340753, -11694702, 8646051, -4125437, 4520614, 0.076)},
 bs2=bsv(2062069139, 1372183856, 689885283, 126187903, 1128616792), bs2pe='2023-12-31'))

VIS.append(doc('7280d173', 'Q1 2024', '2024-03-31', 'Q1', '2023-03-31', '2023-12-31',
 'VISUAL: statement pages 3-8 are image-only; BS p4 (printed 2), IS p5 (printed 3), CF p8 (printed 6) rendered at 1.8x and read by eye; cover reads Allianz Saudi Fransi Cooperative Insurance Company; the 2023 comparative column is labelled Restated',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(2037791699, 1231678734, 806112965, 134849973, 1040727211), 'prior': bsv(2155386277, 1354701964, 800684313, 126187903, 1111134900)},
 {'cur': isv(231980300, -205153581, -28155524, -1328805, 3611916, 2283111, 31828572, -15747121, 18364562, -4358358, 14006204, -4018165, 9988039, 0.167),
  'prior': isv(184806116, -175340535, -3519086, 5946495, 7218000, 13164495, 17070639, -11161526, 19073608, -5566103, 13507505, -3904578, 9602927, 0.160)},
 {'cur': cfv(14819986, -4426471, -1731445, 8662070, 126187903, 134849973), 'prior': cfv(70185596, -67482505, -1485294, 1217797, 194590855, 195808652)}))

VIS.append(doc('5b94fef2', 'H1 2024', '2024-06-30', 'H1', '2023-06-30', '2023-12-31',
 'VISUAL: statement pages 3-8 are image-only; BS p4 (printed 2), IS p5 (printed 3; columns Q2 2024, Q2 2023 restated, 6M 2024, 6M 2023 restated), CF p8 (printed 6) rendered at 1.8x and read by eye',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(2044535692, 1243774874, 800760818, 132703510, 1038549757), 'prior': bsv(2155386277, 1354701964, 800684313, 126187903, 1111134900)},
 {'cur': isv(470308030, -424026797, -44406408, 1874825, 3611916, 5486741, 43107350, -16528490, 32065601, -15626702, 16438899, -5850074, 10588825, 0.177),
  'prior': isv(391938457, -317743853, -57984411, 16210193, 7218000, 23428193, 55617422, -33403324, 45642291, -18969004, 26673287, -6661072, 20012215, 0.334)},
 {'cur': cfv(5660098, 7340519, -6485010, 6515607, 126187903, 132703510), 'prior': cfv(67756541, -77823763, -3564800, -13632022, 194590855, 180958833)},
 is_q={'cur': isv(238327730, -218873216, -16250884, 3203630, 0, 3203630, 11278778, -781369, 13701039, -11268344, 2432695, -1831909, 600786, 0.010),
       'prior': isv(207132341, -142403318, -54465326, 10263697, 0, 10263697, 38546783, -22241798, 26568682, -13402900, 13165782, -2756494, 10409288, 0.173)}))

VIS.append(doc('c26a790d', '9M 2024', '2024-09-30', 'Q9M_PLACEHOLDER', '2023-09-30', '2023-12-31',
 'VISUAL: statement pages 3-8 are image-only (inventory class partial_statements is wrong: BS p4, IS p5, OCI p6, equity p7, CF p8 are all present); BS p4 (printed 2), IS p5 (printed 3; columns Q3 2024, Q3 2023 restated, 9M 2024, 9M 2023 restated), CF p8 (printed 6) rendered at 1.8x and read by eye',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(2015385887, 1207338964, 808046923, 124144616, 1052088833), 'prior': bsv(2155386277, 1354701964, 800684313, 126187903, 1111134900)},
 {'cur': isv(675466282, -591591024, -75572366, 8302892, 3611916, 11914808, 72422218, -31930672, 52406354, -27321404, 25084950, -9975511, 15109439, 0.254),
  'prior': isv(615338765, -480981780, -120778531, 13578454, 10922000, 24500454, 66029994, -30601806, 59928642, -26093962, 33834680, -10239019, 23595661, 0.393)},
 {'cur': cfv(-35356226, 41679217, -8366278, -2043287, 126187903, 124144616), 'prior': cfv(137788534, -101574038, -7752790, 28461706, 194590855, 223052561)},
 is_q={'cur': isv(205158252, -167564227, -31165958, 6428067, 0, 6428067, 29314868, -15402182, 20340753, -11694702, 8646051, -4125437, 4520614, 0.076),
       'prior': isv(223400308, -163237927, -62794120, -2631739, 3704000, 1072261, 10412572, 2801518, 14286351, -7124958, 7161393, -3577947, 3583446, 0.060)}))
VIS[-1]['period_type'] = '9M'


def isv23(rev, exp, reins, isr, nii, fin, other, pbta, surplus, pbt, zakat, ni, eps):
    return {'insurance_revenue': rev, 'insurance_service_expenses': exp, 'net_reinsurance_result': reins, 'insurance_service_result': isr, 'net_investment_income': nii,
            'net_insurance_finance_result': fin, 'other_income_expenses': other, 'pbt_before_attribution': pbta, 'surplus_to_insurance_operations': surplus, 'pbt': pbt, 'zakat_tax': zakat, 'net_income': ni, 'eps': eps}


VIS.append(doc('fa6a5b3c', 'Q1 2023', '2023-03-31', 'Q1', '2022-03-31', '2022-12-31',
 'VISUAL: text layer is scrambled OCR (values detached from labels), so BS p4 (printed 2; columns 31 Mar 2023, 31 Dec 2022 restated, 1 Jan 2022 restated), IS p5 (printed 3) and CF p8 (printed 6) were rendered at 1.8x and read by eye; first-year IFRS 17 presentation: no share-of-pool-surplus line, surplus attributed to insurance operations deducted before shareholders PBT; other_income_expenses = other expenses as printed',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(2336336678, 1564256545, 772080133, 195808652, 1173246795), 'prior': bsv(2119368916, 1370624798, 748744118, 194590855, 1079092216)},
 {'cur': isv23(184806116, -177269912, -3519086, 4017118, 24288639, -11161526, -2623513, 14520718, -1013213, 13507505, -3904578, 9602927, 0.160),
  'prior': isv23(182472072, -150333729, -36708201, -4569858, 19946851, -14743668, -2092046, -1458721, 0, -1458721, -2395476, -3854197, -0.064)},
 {'cur': cfv(70185596, -67482505, -1485294, 1217797, 194590855, 195808652), 'prior': cfv(-3509373, -32562500, -1485294, -37557167, 160813072, 123255905)},
 bs2=bsv(2249103623, 1493272748, 755830875, 160813072, 1275940332), bs2pe='2022-01-01'))

VIS.append(doc('6d2dd737', 'H1 2023', '2023-06-30', 'H1', '2022-06-30', '2022-12-31',
 'VISUAL: text layer is scrambled OCR; BS p4 (printed 2; columns 30 Jun 2023, 31 Dec 2022 restated, 1 Jan 2022 restated), IS p5 (printed 3; columns Q2 2023, Q2 2022 restated, 6M 2023, 6M 2022 restated), CF p8 (printed 6) rendered at 1.8x and read by eye; the printed 6M 2023 cash from operations 67,759,541 is a footing error (components add to 67,756,541, the figure the H1 2024 filing prints as comparative; page region zoomed 4x to confirm the print)',
 {'bs': 4, 'is': 5, 'cf': 8},
 {'cur': bsv(2268979658, 1493123325, 775856333, 180958833, 1076348235), 'prior': bsv(2119368916, 1370624798, 748744118, 194590855, 1079092216)},
 {'cur': isv23(391938457, -334785808, -57984411, -831762, 62835422, -33403324, 0, 28600336, -1927049, 26673287, -6661072, 20012215, 0.33),
  'prior': isv23(352143143, -220246673, -149598002, -17701532, 13766005, -850830, -1495309, -6281666, 0, -6281666, -5696321, -11977987, -0.19)},
 {'cur': cfv(67759541, -77823763, -3564800, -13632022, 194590855, 180958833), 'prior': cfv(-9308366, 209797, -2469789, -11568358, 160813072, 149244713)},
 is_q={'cur': isv23(207132341, -157515898, -54465324, -4848881, 38546784, -22241796, 2623513, 14079620, -913838, 13165782, -2756494, 10409288, 0.17),
       'prior': isv23(169671071, -69912943, -112889802, -13131674, -6180844, 13892836, 596738, -4822944, 0, -4822944, -3300845, -8123789, -0.13)},
 bs2=bsv(2249103623, 1493272748, 755830875, 160813072, 1275940332), bs2pe='2022-01-01'))
VIS[-1]['declared_footing'] = [{'col': 'cur', 'check': 'cf-sum', 'printed': -13632022, 'computed': -13629022}]
