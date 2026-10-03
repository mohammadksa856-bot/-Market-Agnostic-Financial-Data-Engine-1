import json
M=1  # raw SAR
def bs(ta,tl,te,cash,nca=None,ca=None):
    d={"total_assets":ta,"total_liabilities":tl,"total_equity":te,"cash":cash}
    if nca:d["non_current_assets"]=nca;d["current_assets"]=ca
    return d
def inc(rev,gp,op,pbt,ni,eps):
    return {"revenue":rev,"gross_profit":gp,"operating_income":op,"pbt":pbt,"net_income":ni,"eps":eps}
def cf(cfo,cfi,cff,net,b,e,fx,capex):
    return {"cfo":cfo,"cfi":cfi,"cff":cff,"net_change":net,"cash_begin":b,"cash_end":e,"fx":fx,"capex":capex}
docs=[
{"sha256_prefix":"4850d417","label":"FY2025 consolidated FS English (KPMG; file labelled 2026|FY)","period_end":"2025-12-31","period_type":"FY","reading":"visual: image-only pages (all 53 textless); pdf p7 BS, p8 IS, p10 CF rendered and read (printed 1,2,4)","pages":{"bs":7,"is":8,"cf":10},
 "bs":{"cur":bs(6690882229,3947343864,2743538365,554443212,3391854833,3299027396),"prior_represented":bs(6173349244,3587246396,2586102848,956809579,3079780920,3093568324)},
 "is":{"cur":inc(10213238401,3805571399,926542494,845906381,830737560,6.39),"prior_represented":inc(9446420046,3512346996,873194409,834543624,820723624,6.31)},
 "cf":{"cur":cf(1133730127,-354326625,-1181955924,-402552422,956809579,554443212,186055,-387085742),"prior":cf(1491354483,-328014853,-1116960735,46378895,909662249,956809579,768435,-339530890)}},
{"sha256_prefix":"c063037c","label":"FY2024 consolidated FS English, original (file labelled 2025|FY)","period_end":"2024-12-31","period_type":"FY","reading":"visual: pdf p7 BS, p8 IS, p10 CF rendered and read (pages 7-10 textless; printed 1,2,4)","pages":{"bs":7,"is":8,"cf":10},
 "bs":{"cur":bs(6173349244,3587246396,2586102848,956809579,3062389988,3110959256),"prior":bs(5371327292,2908571313,2462755979,909662249,2623142091,2748185201)},
 "is":{"cur":inc(9446420046,3532866388,873194409,834543624,820723624,6.31),"prior":inc(8713675990,3522243657,960955041,944246155,892618140,6.87)},
 "cf":{"cur":cf(1491354483,-328014853,-1116960735,46378895,909662249,956809579,768435,-339530890),"prior_represented":cf(1316026804,-331555112,-1150673581,-166201889,1076311959,909662249,-447821,-353861780)}},
{"sha256_prefix":"71be975f","label":"FY2023 consolidated FS English, original (file labelled 2024|FY)","period_end":"2023-12-31","period_type":"FY","reading":"visual: pdf p7 BS, p8 IS, p10 CF rendered and read (printed 6,7,9)","pages":{"bs":7,"is":8,"cf":10},
 "bs":{"cur":bs(5371327292,2908571313,2462755979,909662249,2612583654,2758743638),"prior":bs(4944903090,2701518913,2243384177,1076311959,2381262144,2563640946)},
 "is":{"cur":inc(8713675990,3522243657,960955041,944246155,892618140,6.87),"prior_represented":inc(8616187816,3545391208,1002577401,937925392,887811814,6.83)},
 "cf":{"cur":cf(1368728218,-384256526,-1150673581,-166201889,1076311959,909662249,-447821,-353861780),"prior":cf(1667871281,-275129822,-717263779,675477680,401044447,1076311959,-210168,-250266759)}},
{"sha256_prefix":"9043db49","label":"FY2022 consolidated FS English, original (file labelled 2023|FY)","period_end":"2022-12-31","period_type":"FY","reading":"visual: pdf p8 BS, p9 IS, p11 CF rendered and read (printed 6,7,9)","pages":{"bs":8,"is":9,"cf":11},
 "bs":{"cur":bs(4944903090,2701518913,2243384177,1076311959,2381262144,2563640946),"prior":bs(4286924572,2683329073,1603595499,401044447,2487548823,1799375749)},
 "is":{"cur":inc(8616187816,3520892316,1002577401,937925392,887811814,6.83),"prior":inc(8066215379,3304681115,919568907,857266731,812528628,6.25)},
 "cf":{"cur":cf(1667871281,-275129822,-717263779,675477680,401044447,1076311959,-210168,-250266759),"prior":cf(1333970467,-299364583,-1642067579,-607461695,1008529663,401044447,-23521,-282574314)}},
{"sha256_prefix":"eeba86e1","label":"H1 2026 interim English (3M and 6M ended 2026-06-30)","period_end":"2026-06-30","period_type":"H1","reading":"visual: pdf p5 BS, p6 IS, p8-9 CF rendered and read (pages 5-9 textless; printed 1,2,4,5)","pages":{"bs":5,"is":6,"cf":[8,9]},
 "bs":{"cur":bs(6813816514,4302119911,2511696603,143679146)},
 "is":{"cur":inc(5468698658,1995364150,505605298,461748042,450908966,3.47),"prior":inc(5162518383,1909776616,530631220,491060050,493567061,3.80)},
 "is_q":{"cur":inc(2674256396,1007631773,245860455,222525763,215226163,1.66),"prior":inc(2527565322,965952700,260641932,238365869,238403369,1.83)},
 "cf":{"cur":cf(908113244,-703546902,-615416183,-410849841,554443212,143679146,85775,-149108107),"prior":cf(507597197,-456931761,-600901721,-550236285,956809579,406873558,300264,-177322521)}},
{"sha256_prefix":"c2d2b8f7","label":"Q1 2026 interim English (3M ended 2026-03-31)","period_end":"2026-03-31","period_type":"Q1","reading":"visual: pdf p5 BS, p6 IS, p8 CF rendered and read (CF heading mistakenly says nine-month period ended 31 March 2025; columns are 3M 2026 and 3M 2025)","pages":{"bs":5,"is":6,"cf":8},
 "bs":{"cur":bs(7414444780,4798763917,2615680863,1116099123)},
 "is":{"cur":inc(2794442262,987732377,259744843,239222279,235682803,1.81),"prior":inc(2634953061,943823916,269989288,252694181,255163692,1.96)},
 "cf":{"cur":cf(857752177,-176303865,-119585172,561863140,554443212,1116099123,-207229,-76096106),"prior":cf(631750485,-91822771,-509070930,30856784,956809579,987833115,166752,-95796778)}},
{"sha256_prefix":"ff6b8311","label":"9M 2025 interim English (3M and 9M ended 2025-09-30), inventory says no statements","period_end":"2025-09-30","period_type":"9M","reading":"visual: pdf p5 BS, p6 IS, p8 CF rendered and read (printed 1,2,4)","pages":{"bs":5,"is":6,"cf":8},
 "bs":{"cur":bs(6761763473,4245734880,2516028593,636682121)},
 "is":{"cur":inc(7623975278,2850345930,718202512,657517834,654815917,5.04),"prior":inc(7083412982,2636981753,680884851,662250668,662873435,5.10)},
 "is_q":{"cur":inc(2461456895,940569314,187571292,166457784,161248856,1.24),"prior":inc(2353251802,845362326,175825622,159305076,182188389,1.40)},
 "cf":{"cur":cf(1006332563,-267600512,-1059026261,-320294210,956809579,636682121,166752,-295462915),"prior":cf(1093933526,-230822120,-1025946995,-162835589,909662249,747650257,823597,-234428877)}}]
t={"symbol":"4164","name":"Nahdi Medical Company","currency":"SAR","unit":"whole Saudi riyals (statements printed in SR with no rounding)","docs":docs,
"notes":"cur = filing's own current column; prior = comparative as printed; prior_represented = same period differently presented than in its own original filing. CF cash_end equals BS cash (no restricted cash). Cash flows are cumulative YTD. No NCI shown (net income = attributable)."}
json.dump(t,open("transcripts/4164.json","w"),indent=1)
