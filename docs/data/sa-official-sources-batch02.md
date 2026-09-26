# Saudi official sources - batch 02 (80 companies)

Source discovery only. No documents were downloaded, and nothing here touches `data/raw/**`, `data/imports/**`, `src/finengine/**`, the relay, batch 01 records, company facts or any database.

Registry file: `config/source-registry/sa-batch-zero-source-02.json`, validated by `tests/test_sa_source_registry_batch02.py`. The generated `config/sa-market-registry.json` was regenerated with `python scripts/build_sa_market_registry.py`.

Checked 2026-09-26. Sources used: each company's own website and Saudi Exchange (saudiexchange.sa). No secondary source (Argaam, Mubasher, Yahoo, Investing, MarketScreener, Zawya) is recorded as a source. No company is claimed complete and nothing was deployed.

## How it was checked

1. In a real browser, the Saudi Exchange listed-companies page was opened and each company's profile was fetched (HTTP 200) to read its short name and its listed website. 74 of the 80 symbols are on that page; the other six are listed below.
2. Four research passes (20 symbols each) used plain HTTP fetch and search, seeded with those Saudi Exchange websites. They recorded only pages they opened and left the rest empty.
3. A real-browser pass re-checked the sites that failed plain fetch (JavaScript-only, TLS, 403/406) and several thin results. For the pages it opened, it fetched the recorded issuer pages from the same site and confirmed HTTP 200.
4. Not every URL was opened by me: for the rest, the record rests on the research passes' own reports. A second spot-check before the Relay depends on them is worth doing.

## Numbers

| Measure | Count |
|---|---|
| Companies in batch | 80 |
| access_status = reachable | 54 (see table) |
| access_status = js_required | 10 (1201, 1211, 1303, 2020, 2223, 2240, 2270, 2290, 2350, 4001) |
| access_status = ssl_issue | 4 (1213, 1832, 2090, 2283) |
| access_status = blocked | 3 (2280, 2310, 4005) |
| access_status = not_found | 9 (1090, 1310, 1330, 2002, 2030, 2210, 2260, 2340, 3001) |
| With at least one issuer annual, quarterly, statements or results page | 55 |
| With no issuer report page | 25 |
| Annual-report URLs | 43 |
| Quarterly-results URLs | 35 |
| Financial-statements URLs | 46 |
| Direct PDF/XLSX links seen (flag = yes) | 33 |
| Oldest visible report year | 2003 (2050) |

A URL count is not a document count: several companies list annual, quarterly and statement files on one page, so the same URL can appear in more than one field. `data_supplements_url` is empty wherever it would only repeat another field.

## Symbols not on the current Saudi Exchange listing

These six do not appear on the listed-companies page (checked in a real browser 2026-09-26), so they have no profile URL and no report URLs. The explanations below come from the research passes, mostly search results, and were not confirmed from an official page.

| Symbol | Seed short name | What research indicates |
|---|---|---|
| 1090 | Samba Financial Group | Seed short name SAMBA. Search results indicate Samba Financial Group merged into Saudi National Bank (1180) in 2021; no Saudi Exchange or issuer confirmation was opened, and no successor pages are used. |
| 1310 | Unknown (symbol 1310 not identified) | Seed short name MMG. The company could not be identified from official sources. |
| 1330 | Unknown (symbol 1330 not identified) | Seed short name ALKHODARI. The company could not be identified from official sources. |
| 2002 | National Petrochemical Company (Petroche | Seed short name PETROCHEM (National Petrochemical Company). Research indicates it was acquired by SIIG (2250) around 2022; not confirmed from an official page opened here. |
| 2260 | Sahara Petrochemical Company | Seed short name Sahara (Sahara Petrochemical). Research indicates it merged into Sipchem (2310) in 2019 and was delisted; confirmed only through a search-result announcement listing, not an opened official page. |
| 3001 | Hail Cement Company | Seed short name HCC (Hail Cement Company). Research indicates it was acquired by Qassim Cement (approved 10 June 2024, effective 11 June 2024) and delisted; no official issuer pages found. |

## Companies with no issuer report page (Saudi Exchange is the fallback)

For these listed companies the issuer site was unreachable, has no investor or financial section, or its pages could not be opened. Their filings should come from Saudi Exchange announcements; the profile URL is recorded.

| Symbol | Company | access_status | Why |
|---|---|---|---|
| 1210 | BCI (name not verified from offici | reachable | Real-browser check: site opens; its Investors menu contains only a link to the company's Saudi Exchange page, so no issuer financial reports exist on the site. Fallback:  |
| 1213 | Naseej International Trading Co. ( | ssl_issue | Real browser also refuses the certificate (expired). |
| 1303 | Electrical Industries Company (EIC | js_required | IR page is a blank shell with one iframe, even after 8 seconds in a real browser. |
| 1323 | United Carton Industries Company ( | reachable | Real-browser check: site opens but no investor or financial link was found in the rendered page. |
| 1324 | Saleh Alrashed (Salah Alrashed Gro | reachable | IR site mentions Financial Information and Reports sections but subpage URLs/years were not exposed; needs browser check to find document lists. |
| 1820 | Baan Holding Group | reachable | Investors page opens but is a static placeholder with no financial documents. |
| 1832 | Sadr Logistics Company | ssl_issue | Real browser also refuses the certificate. |
| 1834 | Saudi Manpower Solutions Company ( | reachable | Seed had no name/site; smasco.com found via search. Homepage shows an Investors menu and Shareholders Portal but sub-page URLs were not obtainable; /en/investors and /en/ |
| 1835 | Tamkeen Human Resources Company | reachable | IR page shows only a newsletter signup and links to Governance and IPO pages; no financial statements or PDFs seen. Governance page (tamkeenhr.sa/en/governance) had none  |
| 2030 | Saudi Arabian Refineries Company ( | not_found | The Saudi Exchange-listed domain returns a Cloudflare 'DNS points to prohibited IP' error in a real browser: a server-side misconfiguration, so no usable page at check ti |
| 2090 | National Gypsum Company | ssl_issue | gypsco.sa does not resolve and gypsco.com.sa fails TLS; neither opens in a real browser. |
| 2110 | Saudi Cable Company | reachable | Homepage (redirect stub to en/index.html) opens, but search-indexed pages /investor-relations, /investor-relations/financial-reports and /annual-reports returned 404 to p |
| 2130 | Saudi Industrial Development Compa | reachable | Reports/announcements page (2025-2026) lists financial-results announcements and governance PDFs; no annual/quarterly statement library established. Individual results an |
| 2150 | The National Company for Glass Ind | reachable | Site opens in a real browser (redirect from zoujaj-glass.com) but has no investor or financial links. |
| 2210 | Nama Chemicals Company | not_found | The Saudi Exchange-listed domain nama.com.sa fails in plain fetch and in a real browser. |
| 2270 | Saudia Dairy and Foodstuff Company | js_required | IR landing opens. The annual-report and financial-statement pages are on http://sadafcoir.sadafco.com (http only, not recorded). |
| 2340 | Artex Industrial Investment Compan | not_found | Saudi Exchange lists carpets.com, which fails in plain fetch and in a real browser. artexcarpets.com opens but ownership was not confirmed, so it is not recorded as the o |
| 2360 | Saudi Vitrified Clay Pipe Company | reachable | Homepage fetch returned empty content; a news article page (annual results FY2024) opened. Media Center has News and Downloads sections; Downloads not opened so no dedica |
| 4005 | National Medical Care Company (CAR | blocked | Plain fetch returns 403; a real browser opens the site, which shows no investor section. Fallback: Saudi Exchange. |

## All 80 companies

| Symbol | Company | access_status | Website | IR | Annual | Quarterly | Statements | Direct files | Years visible |
|---|---|---|---|---|---|---|---|---|---|
| 1090 | Samba Financial Group | not_found | - | - | - | - | - | ? | - |
| 1111 | Saudi Tadawul Group Holding Company | reachable | tadawulgroup.sa | - | yes | yes | yes | yes | 2021-2026 |
| 1201 | Takween Advanced Industries | js_required | takweenai.com | yes | - | - | yes | no | - |
| 1202 | Middle East Paper Company (MEPCO) | reachable | mep.co | yes | yes | yes | yes | yes | 2017-2026 |
| 1210 | BCI (name not verified from official | reachable | bci.sa | - | - | - | - | no | - |
| 1211 | Saudi Arabian Mining Company (Maaden | js_required | maaden.com | yes | - | - | yes | no | - |
| 1212 | Astra Industrial Group | reachable | aig.sa | yes | yes | yes | yes | yes | 2020-2026 |
| 1213 | Naseej International Trading Co. (Al | ssl_issue | al-sorayai.com | - | - | - | - | ? | - |
| 1214 | Shaker Group | reachable | shaker.com.sa | yes | yes | yes | yes | yes | 2022-2026 |
| 1301 | United Wire Factories Company (Aslak | reachable | unitedwires.com.sa | yes | yes | yes | yes | ? | 2016-2024 |
| 1302 | Bawan Company | reachable | bawan.com.sa | yes | yes | yes | yes | yes | 2017-2025 |
| 1303 | Electrical Industries Company (EIC) | js_required | eic.com.sa | yes | - | - | - | no | - |
| 1304 | Al Yamamah Steel Industries Company | reachable | yamsteel.com | yes | yes | yes | yes | no | 2018-2025 |
| 1310 | Unknown (symbol 1310 not identified) | not_found | - | - | - | - | - | ? | - |
| 1320 | Saudi Steel Pipe Company (SSP) | reachable | sspipe.com | - | yes | yes | yes | ? | 2015-2025 |
| 1321 | East Pipes Integrated Company for In | reachable | eastpipes.com | yes | yes | yes | yes | ? | 2021-2026 |
| 1322 | Al Masane Al Kobra Mining Company (A | reachable | amak.com.sa | yes | yes | yes | yes | ? | 2021-2026 |
| 1323 | United Carton Industries Company (UC | reachable | ucic.com.sa | - | - | - | - | no | - |
| 1324 | Saleh Alrashed (Salah Alrashed Group | reachable | salrashed.com.sa | yes | - | - | - | ? | - |
| 1330 | Unknown (symbol 1330 not identified) | not_found | - | - | - | - | - | ? | - |
| 1810 | Seera Group Holding | reachable | seera.sa | yes | yes | yes | yes | yes | 2011-2026 |
| 1820 | Baan Holding Group | reachable | baanholding.com | yes | - | - | - | no | - |
| 1830 | Leejam Sports Company | reachable | leejam.com.sa | - | yes | yes | yes | yes | 2018-2026 |
| 1831 | Maharah Human Resources Company | reachable | maharah.com | yes | yes | - | - | yes | 2019-2024 |
| 1832 | Sadr Logistics Company | ssl_issue | - | - | - | - | - | ? | - |
| 1833 | Al Mawarid Manpower Company | reachable | mawarid.com.sa | yes | - | yes | yes | no | 2021-2025 |
| 1834 | Saudi Manpower Solutions Company (SM | reachable | smasco.com | - | - | - | - | no | - |
| 1835 | Tamkeen Human Resources Company | reachable | tamkeenhr.com | yes | - | - | - | no | - |
| 2001 | Chemanol (Methanol Chemicals Company | reachable | chemanol.com | yes | yes | yes | yes | yes | 2015-2019 |
| 2002 | National Petrochemical Company (Petr | not_found | - | - | - | - | - | ? | - |
| 2020 | SABIC Agri-Nutrients Company | js_required | sabic-agrinutrients.com | - | yes | - | yes | no | - |
| 2030 | Saudi Arabian Refineries Company (SA | not_found | almasafi.com.sa | - | - | - | - | ? | - |
| 2040 | Saudi Ceramic Company | reachable | saudiceramics.com | yes | yes | - | - | yes | 2013-2025 |
| 2050 | Savola Group | reachable | savola.com | yes | yes | yes | yes | yes | 2003-2026 |
| 2070 | Saudi Pharmaceutical Industries & Me | reachable | ir.spimaco.com.sa | yes | yes | yes | yes | yes | 2019-2026 |
| 2083 | Marafiq (Power and Water Utility Com | reachable | marafiq.com.sa | - | - | yes | yes | yes | 2022-2026 |
| 2084 | Miahona Company | reachable | miahona.com | - | yes | yes | yes | yes | 2021-2026 |
| 2090 | National Gypsum Company | ssl_issue | - | - | - | - | - | ? | - |
| 2110 | Saudi Cable Company | reachable | saudicable.com | - | - | - | - | ? | - |
| 2130 | Saudi Industrial Development Company | reachable | sidc.com.sa | - | - | - | - | no | - |
| 2150 | The National Company for Glass Indus | reachable | zoujajglass.com | - | - | - | - | no | - |
| 2160 | Saudi Arabian Amiantit Company | reachable | amiantit.com | - | yes | - | - | yes | 2021-2023 |
| 2170 | Alujain Corporation | reachable | alujain.sa | yes | yes | yes | yes | yes | 2020-2026 |
| 2180 | Filing and Packing Materials Manufac | reachable | fipco.com.sa | yes | yes | yes | yes | yes | 2016-2026 |
| 2190 | SISCO Holding | reachable | sisco.com.sa | yes | yes | - | - | yes | 2017-2025 |
| 2200 | Arabian Pipes Company (APC) | reachable | arabian-pipes.com | - | yes | yes | yes | yes | 2012-2026 |
| 2210 | Nama Chemicals Company | not_found | - | - | - | - | - | ? | - |
| 2220 | National Metal Manufacturing and Cas | reachable | maadaniyah.com | yes | yes | yes | yes | yes | 2020-2026 |
| 2223 | Saudi Aramco Base Oil Company (Luber | js_required | luberef.com | yes | yes | yes | yes | no | - |
| 2240 | Senaat | js_required | senaat.com | yes | yes | - | yes | no | - |
| 2250 | Saudi Industrial Investment Group (S | reachable | siig.com.sa | yes | - | yes | yes | yes | 2018-2025 |
| 2260 | Sahara Petrochemical Company | not_found | - | - | - | - | - | ? | - |
| 2270 | Saudia Dairy and Foodstuff Company ( | js_required | sadafco.com | yes | - | - | - | ? | - |
| 2280 | Almarai Company | blocked | almarai.com | - | - | - | yes | yes | - |
| 2281 | Tanmiah Food Company | reachable | tanmiah.com | yes | - | yes | yes | yes | 2018-2026 |
| 2283 | The First Milling Company | ssl_issue | firstmills.com | yes | - | - | - | ? | - |
| 2287 | Entaj Foods | reachable | entaj.com | yes | yes | yes | yes | yes | 2024-2026 |
| 2290 | Yanbu National Petrochemical Company | js_required | yansab.com.sa | yes | - | yes | - | yes | - |
| 2300 | Saudi Paper Manufacturing Company (S | reachable | saudipaper.com | yes | yes | yes | yes | ? | 2015-2023 |
| 2310 | Sahara International Petrochemical C | blocked | sipchem.com | - | yes | - | - | yes | 2019-2025 |
| 2320 | Al-Babtain Power & Telecommunication | reachable | al-babtain.com.sa | yes | yes | - | yes | yes | 2023-2025 |
| 2330 | Advanced Petrochemical Company | reachable | - | yes | yes | yes | yes | yes | 2020-2025 |
| 2340 | Artex Industrial Investment Company | not_found | - | - | - | - | - | ? | - |
| 2350 | Saudi Kayan Petrochemical Company | js_required | saudikayan.com | yes | yes | - | yes | no | - |
| 2360 | Saudi Vitrified Clay Pipe Company | reachable | svcp-sa.com | - | - | - | - | ? | None-2024 |
| 2370 | Middle East Specialized Cables Compa | reachable | mesccables.com | yes | yes | - | yes | yes | 2014-2023 |
| 2380 | Rabigh Refining and Petrochemical Co | reachable | petrorabigh.com | - | - | yes | yes | no | 2023-2026 |
| 2381 | Arabian Drilling Company | reachable | arabdrill.com | - | yes | yes | yes | yes | 2019-2026 |
| 2382 | ADES Holding Company | reachable | adesgroup.com | - | yes | yes | yes | ? | 2023-2026 |
| 3001 | Hail Cement Company | not_found | - | - | - | - | - | ? | - |
| 3007 | Zahrat Al Waha for Trading Company ( | reachable | zaoasis.com | yes | yes | yes | yes | ? | 2019-2026 |
| 3008 | Al Kathiri Holding Company | reachable | alkathiriholding.com | - | yes | - | - | ? | 2023-2024 |
| 3080 | Eastern Province Cement Company | reachable | epcco.com.sa | - | yes | - | yes | ? | 2012-2020 |
| 3090 | Tabuk Cement Company | reachable | tcc-sa.com | - | yes | yes | yes | yes | 2019-2025 |
| 3091 | Al Jouf Cement Company | reachable | joufcem.com.sa | - | - | yes | yes | ? | 2023-2025 |
| 3092 | Riyadh Cement Company | reachable | riyadhcement.com.sa | - | yes | - | yes | yes | 2018-2025 |
| 4001 | Abdullah Al Othaim Markets Company | js_required | othaimmarkets.com | yes | - | - | yes | no | - |
| 4004 | Dallah Healthcare Company | reachable | dallahhealth.com | - | yes | - | - | ? | 2021-2026 |
| 4005 | National Medical Care Company (CARE) | blocked | care.med.sa | - | - | - | - | no | - |
| 4006 | Saudi Marketing Company (Farm Supers | reachable | farm.com.sa | yes | yes | - | yes | yes | 2014-2024 |

## Recurring problems the Relay should support

1. **Saudi Exchange blocks plain HTTP.** As in batch 01, every saudiexchange.sa page returned 403 to plain fetch and a real browser works. Profile links carry a portal state token, so discover them from the listed-companies page instead of building them.
2. **Script-rendered document lists.** 10 sites open but fill their report lists through scripts or frames (for example 1201, 1211, 1303, 2020, 2223, 2240, 2290, 2350, 4001). A rendering fetch is needed.
3. **Sites that open only in a real browser.** Almarai (2280), Sipchem (2310), Care (4005) return 403 or 406 to plain fetch but open in a browser; First Milling (2283) fails plain TLS but opens.
4. **Certificate failures that a browser also refuses.** 1213 (expired certificate) and 1832 (wrong certificate) cannot be opened even in a real browser; 2090's domains do not resolve or fail TLS.
5. **Broken or unreachable official sites.** 2030's domain returns a Cloudflare 'DNS points to prohibited IP' error, 2210's domain fails everywhere, and 2340's Saudi Exchange-listed domain fails. Retry later; do not substitute another site.
6. **Wrong domains in seed data.** Some Saudi Exchange website fields are malformed (`http://https://...`, `http//...`). Always open and normalise them; a seed value is a lead, not a source.
7. **Companies whose own site has no financial section.** 1210 (its Investors menu only links to Saudi Exchange), 1820, 2150, 4005 and others. Use Saudi Exchange announcements.
8. **Delisted, merged or renamed companies.** Six symbols are absent from the current listing (see above). Renames seen: 2310 (now Sahara International Petrochemical), 2340 (Artex), 2380 (Rabigh Refining and Petrochemical). Match on the Saudi Exchange symbol, not the name.
9. **Stale visible history.** 2001 shows reports only to 2019, 3080 to 2020, 2370 to 2023, 2300 to 2023. A missing year on the site is not proof the filing does not exist.
10. **Pages served over http only.** 2270's annual-report and financial-statement pages sit on an http-only host and are not recorded; the builder ingests https URLs only.
11. **One page for everything.** Several companies list annual, quarterly and statement files on one page; crawl the page instead of treating it as a single document.

## Remaining uncertainty

- Years and direct-link flags for several companies come from summarised fetches or page text, not from enumerating each file; treat them as leads.
- 1210, 1213, 1323 and 1324 company names were inferred from Saudi Exchange short names; 1310 and 1330 could not be identified beyond the seed short names.
- Merger and acquisition explanations for 1090, 2002, 2260 and 3001 rest on search results, not on an official page I opened.
- 2340 (Artex): the Saudi Exchange-listed domain fails, and artexcarpets.com opened but its ownership was not confirmed, so it is not recorded.
- Per-company Saudi Exchange announcements URLs are not recorded (`disclosures_url` is filled only where a company's own page was opened).
- No document was downloaded or read.
