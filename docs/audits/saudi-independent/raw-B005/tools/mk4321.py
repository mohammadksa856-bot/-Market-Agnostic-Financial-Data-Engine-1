import json
def bs(ta,tl,te,cash): return {"total_assets":ta,"total_liabilities":tl,"total_equity":te,"cash":cash}
def inc(rev,gp,op,pbt,ni,par,nci,eps): return {"revenue":rev,"gross_profit":gp,"operating_income":op,"pbt":pbt,"net_income":ni,"ni_parent":par,"ni_nci":nci,"eps":eps}
def cf(cfo,cfi,cff,net,b,e): return {"cfo":cfo,"cfi":cfi,"cff":cff,"net_change":net,"cash_begin":b,"cash_end":e}
docs=[
{"sha256_prefix":"18a0b461","label":"FY2025 consolidated FS (EY; file labelled 2026|FY)","period_end":"2025-12-31","period_type":"FY","reading":"visual: pdf p10 BS, p11 IS, p12 OCI, p13 equity, p14-15 CF rendered and read (pages 9-13,15 have no text layer; printed 7,8,9,10,11,12)","pages":{"bs":10,"is":11,"cf":[14,15]},
 "bs":{"cur":bs(36892157366,21326767102,15565390264,4293589740),"prior":bs(31452545879,16624509056,14828036823,670342011)},
 "is":{"cur":inc(2288296428,1934616283,2015142759,1323159842,1276159843,1266893372,9266471,2.67),"prior_represented":inc(2344038571,1985602963,1962969589,1268163900,1224163900,1216906944,7256956,2.56)},
 "cf":{"cur":cf(1783562209,-1157982696,2997668216,3623247729,670342011,4293589740),"prior":cf(1006385476,-1938921386,1517882087,585346177,84995834,670342011)}},
{"sha256_prefix":"0fa3978a","label":"FY2024 consolidated FS English, scanned (file labelled 2025|FY)","period_end":"2024-12-31","period_type":"FY","reading":"visual: scanned pdf p9 BS, p10 IS, p13-14 CF rendered and read (printed 6,7,10,11)","pages":{"bs":9,"is":10,"cf":[13,14]},
 "bs":{"cur":bs(31452545879,16624509056,14828036823,670342011),"prior":bs(27751227420,13439259317,14311968103,84995834)},
 "is":{"cur":inc(2344038571,1985602963,1965365971,1268163900,1224163900,1216906944,7256956,2.56),"prior":inc(2253673262,1870184686,1909468066,1541468407,1500995182,1514995569,-14000387,3.19)},
 "cf":{"cur":cf(1006385476,-1938921386,1517882087,585346177,84995834,670342011),"prior_represented":cf(1390236167,-688965821,-1226720308,-525449962,610445796,84995834)}},
{"sha256_prefix":"310cb87e","label":"FY2023 consolidated FS (KPMG; file labelled 2024|FY)","period_end":"2023-12-31","period_type":"FY","reading":"visual: pdf p9 BS, p10 IS, p13-14 CF rendered and read (printed 6,7,10,11)","pages":{"bs":9,"is":10,"cf":[13,14]},
 "bs":{"cur":bs(27751227420,13439259317,14311968103,84995834),"prior":bs(25876858984,11808258279,14068600705,610445796)},
 "is":{"cur":inc(2253673262,1870184686,1909468066,1541468407,1500995182,1514995569,-14000387,3.19),"prior_9m_transition":inc(1687534280,1401744254,1130366824,874095806,836993094,831907569,5085525,1.75)},
 "cf":{"cur":cf(1383597758,-681118473,-1227929247,-525449962,610445796,84995834),"prior_9m_transition_represented":cf(818678082,-283770154,-480589882,54318046,556127750,610445796)}},
{"sha256_prefix":"64c5dbde","label":"Nine-month transition period ended 2022-12-31 consolidated FS (KPMG; file labelled 2023|FY)","period_end":"2022-12-31","period_type":"9M transition (fiscal year changed from 31 March to 31 December)","reading":"visual: pdf p9 BS, p10 IS, p13-14 CF rendered and read (printed 6,7,10,11)","pages":{"bs":9,"is":10,"cf":[13,14]},
 "bs":{"cur":bs(25876858984,11808258279,14068600705,610445796),"prior_31Mar2022_restated":bs(26085926175,12500581523,13585344652,556127750)},
 "is":{"cur":inc(1687534280,1411536752,1130366824,874095806,836993094,831907569,5085525,1.75),"prior_FY_Mar2022_restated":inc(2037485632,1678040468,1134219231,789978848,750208925,775431515,-25222590,1.63)},
 "cf":{"cur":cf(871508353,-336600425,-480589882,54318046,556127750,610445796),"prior_FY_Mar2022_restated":cf(1476133882,-1078862884,-476813169,-79542171,635669921,556127750)}},
{"sha256_prefix":"78e4dbd4","label":"H1 2026 interim (EY review; 3M and 6M ended 2026-06-30)","period_end":"2026-06-30","period_type":"H1","reading":"visual: pdf p5 BS, p6 IS, p7 OCI, p8 equity, p9-10 CF rendered and read (printed 2,3,4,5,6,7)","pages":{"bs":5,"is":6,"cf":[9,10]},
 "bs":{"cur":bs(35134671838,18987747020,16146924818,614362718)},
 "is":{"cur":inc(1151923190,962881096,1051448448,608235653,592623857,588205550,4418307,1.24),"prior":inc(1173250146,1001126311,1030599644,719661999,697328666,689820269,7508397,1.45)},
 "is_q":{"cur":inc(569373497,473987078,615359568,392640513,389362050,385715184,3646866,0.81),"prior":inc(582616442,489380127,635108621,486987959,474654626,472903887,1750739,1.00)},
 "cf":{"cur":cf(379888386,-1324925616,-2734189792,-3679227022,4293589740,614362718),"prior":cf(740779560,-700595577,-472129225,-431945242,670342011,238396769)}}]
t={"symbol":"4321","name":"Cenomi Centers (Arabian Centres Company)","currency":"SAR","unit":"whole Saudi riyals","docs":docs,
"notes":"Fiscal year end changed from 31 March to 31 December (shareholders approved 2022-12-29); first Dec-year-end statements cover the 9-month period 2022-04-01 to 2022-12-31. Cash flows cumulative YTD. H1 2026 is_q is the three-month column. Operating profit in the 2024-onward statements is labelled 'profit before net finance costs, share of loss of EAI and zakat'. 9M-2022 'prior_9m_transition' in the FY2023 filing is re-presented (gross profit 1,411,536,752 -> 1,401,744,254; CFO 871,508,353 -> 818,678,082; CFI -336,600,425 -> -283,770,154)."}
json.dump(t,open("transcripts/4321.json","w"),indent=1)
