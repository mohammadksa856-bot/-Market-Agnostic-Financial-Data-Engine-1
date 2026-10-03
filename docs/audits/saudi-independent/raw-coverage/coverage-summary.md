# Saudi raw coverage inventory (Step 1)

Document inventory only. **Value correctness: not assessed.** No company's statements are verified by this step.

- Companies inventoried: 390 (registry 419; 29 excluded: 1010, 1020, 1030, 1050, 1060, 1080, 1120, 1140, 1150, 1180, 2010, 2082, 2222, 3002, 3003, 3005, 3010, 3020, 3030, 3040, 3050, 3060, 7010, 7020, 7030, 7040, 7202, 7203, 8010)
- Files inventoried: 8,720 (23.7 GB)

## Company coverage (expected periods with complete statements)

- high: 8
- good: 29
- partial: 62
- sparse: 234
- none: 57
- no_expected_periods: 0

Expected period slots: 11,302; with complete statements 1,879 (16.6%).

Slot status: absent=6048, statements_complete=1702, partial_statements=1448, unreadable_scan_only=1243, non_statement_only=684, statements_via_annual_report=177

## Extractability (document completeness dimension)

- C_scan_or_nonstatement_heavy: 268
- B_mostly_text: 88
- A_text_clean: 33
- none: 1

## File classes

- financial_statements: 3132
- scanned_unreadable: 1863
- other_no_statements_found: 1470
- partial_statements: 992
- annual_report_with_statements: 457
- annual_report_no_statements_found: 379
- results_announcement: 249
- pillar3: 63
- factsheet: 54
- presentation: 37
- data_supplement: 20
- board_report: 3
- excluded_after_download: 1

## Readability

- text: 5709
- scanned_zero_text: 1873
- mixed: 769
- mostly_scanned: 235
- None: 134

## Anomaly classes (flag kind: files / companies)

- weak_period_classification: 2606 / 379
- not_financial_statements: 2138 / 275
- entity_name_not_in_front_pages_check: 1920 / 196
- zero_text_scan_needs_visual_reading: 1863 / 288
- missing_primary_statement: 1150 / 253
- period_mismatch_candidate: 1088 / 321
- partial_statements_only: 992 / 254
- partly_scanned_pages: 769 / 197
- same_hash_under_other_symbol: 461 / 14
- primary_statement_pages_may_be_image_only: 433 / 150
- unclassified_period: 417 / 88
- multiple_same_language_same_period: 412 / 92
- mostly_scanned_needs_visual: 235 / 117
- not_in_final_state_manifest: 205 / 12
- same_hash_multiple_period_labels: 200 / 72
- duplicate_text_candidate_of: 166 / 39
- duration_phrase_mismatch: 160 / 70
- missing_on_disk: 69 / 6
- found_only_under_other_symbol: 65 / 3
- missing_on_disk_under_this_symbol: 65 / 3

Period-label mismatch candidates (detected period end in text vs collector label): label_is_one_year_after_detected_period=857, other=152, same_year_different_period_end=59, label_is_one_year_before_detected_period=20
Most are collector `text_year_only` fiscal-year labels taken from the publication year (label one year after the period actually shown).

Cross-company identical sha256: 213; identical front-text digest: 148.

## Batch plan

81 batches of 5 (35 visual-reading batches). Companies without statement files: 6030.

- B001 T1: 1810, 1111, 6010, 8210, 8250
- B002 T1: 8230, 1211, 1302, 2223, 2290
- B003 T1: 2050, 2080, 2020, 2280, 2330
- B004 T1: 4310, 4190, 4263, 4030, 4031
- B005 T1: 4250, 4164, 4321, 4009, 4013
- B006 T1: 4004, 4001, 4002, 7200, 5110
- B007 T1 VISUAL: 1830, 8200, 2083, 2060, 2310
- B008 T1 VISUAL: 2380, 2350, 4240, 4323, 4020
- B009 T1 VISUAL: 4300, 4200, 4280, 4003, 4007
- B010 T1 VISUAL: 7201
- B011 T2: 3080, 3091, 3092, 1090, 6019
- B012 T2: 6014, 6015, 6070, 6090, 6002
- B013 T2: 6017, 6018, 6016, 6004, 6012
- B014 T2: 8311, 8040, 8020, 8012, 8160
- B015 T2: 8240, 8130, 8190, 8270, 8050
- B016 T2: 8313, 8120, 8180, 8100, 8170
- B017 T2: 8300, 8070, 8260, 8280, 8060
- B018 T2: 8150, 1323, 1324, 1321, 1322
- B019 T2: 1202, 1320, 1304, 1303, 2320
- B020 T2: 2250, 2382, 2084, 2288, 2285
- B021 T2: 2286, 2300, 2130, 2283, 2284
- B022 T2: 2282, 2081, 2190, 2220, 2040
- B023 T2: 2240, 2110, 2120, 2287, 2340
- B024 T2: 4017, 4012, 4010, 4019, 4011
- B025 T2: 4018, 4016, 4015, 4008, 7211
- B026 T2 VISUAL: 3007, 3008, 3004, 3090, 3001
- B027 T2 VISUAL: 1183, 1182, 6022, 6013, 6050
- B028 T2 VISUAL: 6020, 6060, 6001, 6040, 6080
- B029 T2 VISUAL: 8310, 8011, 8080, 8030, 8290
- B030 T2 VISUAL: 8090, 8110, 8140, 8220, 8312
- B031 T2 VISUAL: 1310, 1212, 1214, 1301, 1210
- B032 T2 VISUAL: 1201, 1213, 1330, 2370, 2070
- B033 T2 VISUAL: 2270, 2200, 2381, 2150, 2281
- B034 T2 VISUAL: 2360, 2030, 2180, 2002, 2001
- B035 T2 VISUAL: 2260, 2230, 2140, 2170, 2100
- B036 T2 VISUAL: 2210, 2160, 2090, 4005, 4006
- B037 T2 VISUAL: 4014, 7205, 7050, 7204
- B038 T3: 1831, 1834, 1820, 1832, 4145
- B039 T3: 4264, 4194, 4327, 4165, 4146
- B040 T3: 4082, 4325, 4322, 4084, 4083
- B041 T3: 4160, 4110, 4220, 4070, 4072
- B042 T3: 4193, 4291, 4326, 4192, 4147
- B043 T3: 4161, 4050, 4150, 4320, 4260
- B044 T3: 4100, 4270, 4081, 4265, 4700
- B045 T3: 4702, 4703
- B046 T3 VISUAL: 1833, 1835, 4021, 4071, 4262
- B047 T3 VISUAL: 4292, 4090, 4324, 4163, 4148
- B048 T3 VISUAL: 4142, 4290, 4130, 4261, 4144
- B049 T3 VISUAL: 4143, 4180, 4328, 4061, 4210
- B050 T3 VISUAL: 4230, 4040, 4140, 4191, 4141
- B051 T3 VISUAL: 4080, 4051, 4162, 4170
- B052 T4: 4338, 4340, 4346, 4339, 4347
- B053 T4: 9300, 4335, 4336, 4331, 4333
- B054 T4: 4350, 4330, 4344, 4348, 4334
- B055 T4: 4342, 4345, 4337, 4332
- B056 T4 VISUAL: 4349
- B057 T5: 9641, 9649, 9651, 9591, 9597
- B058 T5: 9619, 9617, 9620, 9527, 9567
- B059 T5: 9642, 9622, 9581, 9602, 9576
- B060 T5: 9607, 9639, 9621, 9637, 9548
- B061 T5: 9625, 9626, 9627, 9574, 9583
- B062 T5: 9543, 9647, 9605, 9557, 9565
- B063 T5: 9640, 9648, 9579, 9599, 9632
- B064 T5: 9635, 9596, 9610, 9570, 9585
- B065 T5: 9541, 9612, 9630, 9559, 9600
- B066 T5: 9584, 9589, 9608, 9616, 9523
- B067 T5: 9631, 9587, 9578, 9580, 9611
- B068 T5: 9568, 9513, 9530, 9533, 9572
- B069 T5: 9593, 9598, 9628
- B070 T5 VISUAL: 9540, 9564, 9614, 9522, 9645
- B071 T5 VISUAL: 9655, 9588, 9538, 9586, 9539
- B072 T5 VISUAL: 9561, 9550, 9555, 9562, 9545
- B073 T5 VISUAL: 9551, 9595, 9601, 9644, 9516
- B074 T5 VISUAL: 9524, 9566, 9553, 9558, 9618
- B075 T5 VISUAL: 9624, 9537, 9542, 9532, 9604
- B076 T5 VISUAL: 9515, 9547, 9514, 9609, 9571
- B077 T5 VISUAL: 9606, 9536, 9549, 9552, 9575
- B078 T5 VISUAL: 9546, 9521, 9560, 9510, 9517
- B079 T5 VISUAL: 9544, 9563, 9569, 9577, 9592
- B080 T5 VISUAL: 9594, 9603, 9613, 9615, 9623
- B081 T5 VISUAL: 9633, 9634, 9636, 9650, 9653

## Caveats

- Listing dates are not available locally; the expected window starts at the earliest period seen in Saudi Exchange announcements or collected files (proxy). Earlier history is neither expected nor counted missing.
- Statement detection, period-end detection and entity checks are text-layer heuristics (English and Arabic headings); image-only pages are invisible to them and are queued for visual reading.
- Nothing here verifies any figure. 'statements_complete' means a file shows all three primary-statement headings with numbers, not that values are correct.
- Absence of published/collected data is not absence of an extractable document: absent periods may still be obtainable from issuer sites, annual reports or Saudi Exchange.
