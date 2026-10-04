import json
def bs(ta,tl,te,cash): return {"total_assets":ta,"total_liabilities":tl,"total_equity":te,"cash":cash}
def inc(rev,gp,op,pbt,ni,par,nci,eps): return {"revenue":rev,"gross_profit":gp,"operating_income":op,"pbt":pbt,"net_income":ni,"ni_parent":par,"ni_nci":nci,"eps":eps}
def cf(cfo,cfi,cff,net,b,e): return {"cfo":cfo,"cfi":cfi,"cff":cff,"net_change":net,"cash_begin":b,"cash_end":e}
docs=[
{"sha256_prefix":"712f37a5","label":"FY2025 consolidated FS (file labelled 2026|FY)","period_end":"2025-12-31","period_type":"FY","reading":"visual: image-only pdf p9 BS, p10 IS, p13 CF rendered and read (printed 7,8,11); text layer of p13 is garbled OCR (e.g. 671,621.123) so values are from the image","pages":{"bs":9,"is":10,"cf":13},
 "bs":{"cur":bs(23204946364,14776266748,8428679616,2281635206),"prior":bs(20557929072,12945280975,7612648097,2890702697)},
 "is":{"cur":inc(13706897641,4207006604,2618981226,2519271079,2491659541,2401470273,90189268,6.86),"prior":inc(11200434264,3744258398,2356261259,2412858445,2369961072,2315290800,54670272,6.62)},
 "cf":{"cur":cf(3401903139,-2970423068,-1040547562,-609067491,2890702697,2281635206),"prior":cf(2970397894,-3775361539,1075285860,270322215,2620380482,2890702697)}},
{"sha256_prefix":"26dbee9b","label":"FY2024 consolidated FS (file labelled 2025|FY)","period_end":"2024-12-31","period_type":"FY","reading":"visual: image-only pdf p8 BS, p9 IS, p10 OCI, p12 CF rendered and read (printed 6,7,8,10)","pages":{"bs":8,"is":9,"cf":12},
 "bs":{"cur":bs(20557929072,12945280975,7612648097,2890702697),"prior":bs(15798041567,9031799748,6766241819,2620380482)},
 "is":{"cur":inc(11200434264,3744258398,2356261259,2412858445,2369961072,2315290800,54670272,6.62),"prior":inc(9508438768,3270048068,2095648916,2169986911,2101470578,2046013922,55456656,5.85)},
 "cf":{"cur":cf(2970397894,-3775361539,1075285860,270322215,2620380482,2890702697),"prior_represented":cf(3244152629,-3486628149,115866997,-126608523,2746989005,2620380482)}},
{"sha256_prefix":"bd1e1fbe","label":"FY2023 consolidated FS, scanned (file labelled 2024|FY)","period_end":"2023-12-31","period_type":"FY","reading":"visual: scanned pdf p8 BS, p9 IS, p12 CF rendered and read (printed 6,7,10)","pages":{"bs":8,"is":9,"cf":12},
 "bs":{"cur":bs(15798041567,9031799748,6766241819,2620380482),"prior":bs(12584117726,6478452959,6105664767,2746989005)},
 "is":{"cur":inc(9508438768,3270048068,2095648916,2169986911,2101470578,2046013922,55456656,5.85),"prior":inc(8310738514,2748135218,1700487330,1796657103,1688949178,1650750047,38199131,4.72)},
 "cf":{"cur":cf(3244152629,-3486628149,115866997,-126608523,2746989005,2620380482),"prior":cf(2843681235,-1939400334,-801121560,103159341,2643829664,2746989005)}},
{"sha256_prefix":"bef89920","label":"FY2022 consolidated FS (file labelled 2023|FY)","period_end":"2022-12-31","period_type":"FY","reading":"visual: image-only pdf p8 BS, p9 IS, p11 equity, p12 CF rendered and read (printed 5,6,8,9)","pages":{"bs":8,"is":9,"cf":12},
 "bs":{"cur":bs(12584117726,6478452959,6105664767,2746989005),"prior":bs(10827367258,5300291255,5527076003,2643829664)},
 "is":{"cur":inc(8310738514,2748135218,1700487330,1796657103,1688949178,1650750047,38199131,4.72),"prior":inc(7250472190,2330229460,1466151267,1501343683,1387277359,1376615197,10662162,3.93)},
 "cf":{"cur":cf(2843681235,-1939400334,-801121560,103159341,2643829664,2746989005),"prior":cf(2182793127,-1247523660,-630703570,304565897,2339263767,2643829664)}},
{"sha256_prefix":"687abe5c","label":"H1 2026 interim (PwC review; 3M and 6M ended 2026-06-30)","period_end":"2026-06-30","period_type":"H1","reading":"visual: image-only pdf p4 BS, p5 IS, p6 OCI, p8 CF rendered and read (printed 2,3,4,6)","pages":{"bs":4,"is":5,"cf":8},
 "bs":{"cur":bs(24688229274,15846610306,8841618968,2322207373),"prior":bs(23204946364,14776266748,8428679616,2281635206)},
 "is":{"cur":inc(7442208598,2177981941,1358155228,1265500013,1218714266,1165953973,52760293,3.33),"prior":inc(6542108726,2094294172,1270794443,1205244214,1182134535,1148029082,34105453,3.28)},
 "is_q":{"cur":inc(4006446109,1222011969,770410167,725952136,705320186,662661232,42658954,1.89),"prior":inc(3384328957,1065983776,644866288,615534127,602351693,591020007,11331686,1.69)},
 "cf":{"cur":cf(1832489867,-1102994800,-688922900,40572167,2281635206,2322207373),"prior":cf(1196356782,-1683937897,-218371668,-705952783,2890702697,2184749914)}}]
t={"symbol":"4013","name":"Dr. Sulaiman Al Habib Medical Services Group (HMG)","currency":"SAR","unit":"whole Saudi riyals","docs":docs,
"notes":"Cash flows cumulative YTD; H1 2026 is_q is the 3-month column. FY2023 cash-flow comparative in the FY2024 filing grosses up long-term loans (proceeds 1,700,512,995 net -> 1,930,000,000 proceeds and 229,487,005 repayments; CFF unchanged 115,866,997). FY2022 comparative working-capital lines in the FY2023 filing differ slightly from the original FY2022 filing (inventories -83,504,291 -> -92,566,741 per the FY2023 filing) with CFO unchanged 2,843,681,235."}
json.dump(t,open("transcripts/4013.json","w"),indent=1)
