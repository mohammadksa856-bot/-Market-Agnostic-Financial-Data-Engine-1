# Saudi official sources - batch 01 (40 companies)

Source-discovery only. No documents were downloaded, and nothing here touches `config/companies.json`, `data/raw/**`, `data/imports/**`, the readers, the database or the relay.

Registry file: `config/source-registry/sa-batch-zero-source-01.json` (validated by `tests/test_sa_source_registry_batch01.py`).

Checked 2026-09-26. Sources used: each company's own website, and Saudi Exchange (saudiexchange.sa). No secondary source (Argaam, Mubasher, Yahoo, Zawya and similar) is recorded as a source.

## How it was checked

1. Four research passes used plain HTTP fetch and search. Saudi Exchange returned 403 to every plain fetch, so the Tadawul fields stayed empty at that stage.

2. A real-browser pass then opened the Saudi Exchange listed-companies page, extracted each company's profile link and confirmed all 40 profiles return HTTP 200. Each profile lists the company's own website, which corrected several wrong guesses (for example 3004 and 4008).

3. The same real browser re-checked the sites that failed plain fetch (403, TLS, JavaScript-only) and the four companies whose website was still empty.

4. The research agents were told to record a URL only if they had opened it, and to leave links seen only in a menu out. I opened the Saudi Exchange profiles and the sites listed in the browser pass myself; for the other URLs this rests on the agents' reports, and a second spot-check by Codex or a human is worth doing before the Relay depends on them.

## Numbers

| Measure | Count |
|---|---|
| Companies in batch | 40 |
| With an official website or IR page recorded | 40 |
| Reachable with at least one annual, quarterly or statements URL | 25 |
| access_status = reachable | 31 |
| access_status = js_required | 5 (2081, 2230, 4008, 4011, 4163) |
| access_status = ssl_issue | 2 (4080, 4200) |
| access_status = blocked | 1 (4220) |
| access_status = not_found | 1 (4061) |
| No visible historical archive year recorded | 11 |
| Annual-report URLs discovered | 23 |
| Quarterly-results URLs discovered | 18 |
| Financial-statements URLs discovered | 24 |
| Direct PDF/XLSX links seen | 25 |
| No annual, quarterly or statements URL at all | 10 (2282, 2286, 3004, 4011, 4051, 4061, 4081, 4163, 4220, 4322) |

A URL count is not a document count. Several companies expose one page that holds annual, quarterly and statement files, so the same URL can appear in more than one field. `data_supplements_url` is empty wherever it would only repeat another field, because nothing verified that supplements exist.

No company is marked complete, and nothing here says any company reaches a completeness or readiness threshold.

## All 40 companies

| Symbol | Company | access_status | Website | IR | Annual | Quarterly | Statements | Direct files | Years visible |
|---|---|---|---|---|---|---|---|---|---|
| 1182 | Amlak International Finance Company | reachable | amlakint.com | yes | yes | yes | yes | yes | 2014-2026 |
| 1183 | SHL Finance Company (formerly Saudi Home Loa | reachable | shlfinance.com | yes | yes | yes | yes | yes | 2015-2026 |
| 2060 | National Industrialization Company (Tasnee) | reachable | tasnee.com | yes | yes | yes | yes | yes | 2006-2026 |
| 2080 | National Gas and Industrialization Company ( | reachable | gasco.com.sa | yes | yes | - | - | yes | 2020-2026 |
| 2081 | Alkhorayef Water and Power Technologies Comp | js_required | awpt.com.sa | yes | yes | yes | yes | no | 2021-2026 |
| 2100 | Wafrah for Industry and Development Company | reachable | wafrah.sa | yes | - | yes | yes | yes | 2021-2023 |
| 2120 | Saudi Advanced Industries Company (SAIC) | reachable | saic.com.sa | yes | yes | - | - | yes | 2022-2026 |
| 2140 | Ayyan Investment Company (formerly Al Ahsa D | reachable | ayyan.com.sa | yes | yes | - | yes | yes | 2020-2025 |
| 2230 | Saudi Chemical Holding Company | js_required | saudichemical.com | yes | yes | - | - | yes | 2025-2026 |
| 2282 | Naqi Water Company | reachable | naqiwater.com | yes | - | - | - | ? | 2021-2026 |
| 2284 | Modern Mills Company | reachable | modernmills.com.sa | yes | yes | yes | yes | no | 2019-2026 |
| 2285 | Arabian Mills for Food Products Company | reachable | arabianmills.com | yes | yes | yes | yes | yes | 2021-2025 |
| 2286 | Fourth Milling Company (MC4) | reachable | ir.mc4.com.sa | yes | - | - | - | ? | 2021-2026 |
| 2288 | Nofoth Food Products Company | reachable | nofoth.com | - | - | - | yes | yes | 2022-2025 |
| 3004 | Northern Region Cement Company | reachable | nrc.com.sa | - | - | - | - | no | - |
| 4002 | Mouwasat Medical Services Company | reachable | mouwasat.com | - | yes | - | - | yes | 2021-2025 |
| 4003 | United Electronics Company (eXtra) | reachable | - | yes | yes | yes | yes | yes | 2025-2026 |
| 4007 | Al Hammadi Holding Company | reachable | alhammadi.com | yes | yes | yes | yes | yes | 2021-2026 |
| 4008 | Saudi Company for Hardware (SACO) | js_required | saco.sa | yes | - | yes | yes | no | - |
| 4009 | Saudi German Health (Middle East Healthcare  | reachable | saudigermanhealth.com | yes | yes | yes | yes | yes | 2019-2026 |
| 4011 | L'azurde Company for Jewelry | js_required | lazurde.com | yes | - | - | - | ? | - |
| 4014 | Scientific and Medical Equipment House Compa | reachable | smeh.com.sa | yes | yes | yes | yes | yes | 2019-2026 |
| 4051 | Baazeem Trading Company | reachable | baazeem.com | - | - | - | - | ? | - |
| 4061 | Anaam International Holding Group | not_found | anaamgroup.com | - | - | - | - | ? | - |
| 4071 | Arabian Contracting Services Company (AlArab | reachable | al-arabia.com | yes | yes | yes | yes | yes | 2020-2026 |
| 4080 | Sinad Holding Company | ssl_issue | sinadholding.com | - | - | - | yes | no | - |
| 4081 | Nayifat Finance Company | reachable | - | yes | - | - | - | no | - |
| 4130 | Saudi Darb Investment Company (formerly Al-B | reachable | albahacompany.com | - | - | yes | yes | yes | 2022-2026 |
| 4163 | Al-Dawaa Medical Services Company | js_required | - | yes | - | - | - | ? | - |
| 4165 | Al Majed for Oud Company | reachable | almajed4oud.com | yes | yes | yes | yes | yes | 2024-2026 |
| 4193 | Nice One Beauty Digital Marketing Company | reachable | niceonesa.com | yes | yes | yes | yes | yes | 2024-2026 |
| 4200 | Aldrees Petroleum and Transport Services Com | ssl_issue | aldrees.com | yes | - | - | yes | yes | None-2026 |
| 4220 | Emaar, The Economic City | blocked | kaec.net | - | - | - | - | no | - |
| 4230 | Red Sea International Company | reachable | redseaintl.com | yes | yes | yes | yes | yes | 2020-2025 |
| 4290 | Alkhaleej Training and Education Company | reachable | alkhaleej.com.sa | yes | - | - | - | ? | 2015-2026 |
| 4300 | Dar Al Arkan Real Estate Development Company | reachable | daralarkan.com | yes | yes | - | yes | yes | 2010-2025 |
| 4322 | Retal Urban Development Company | reachable | retal.com.sa | - | - | - | - | ? | - |
| 4323 | Sumou Real Estate Company | reachable | sumou.com.sa | yes | yes | - | yes | yes | 2018-2022 |
| 6012 | Raydan Food Company | reachable | raydan.com.sa | yes | yes | yes | yes | yes | 2020-2024 |
| 6040 | Tabuk Agricultural Development Company (TADC | reachable | tadco-agri.com | yes | yes | - | - | yes | 2011-2019 |

## Recurring problems the Relay should support

1. **Saudi Exchange blocks plain HTTP.** Every saudiexchange.sa page returned 403 to plain fetch; a real browser works. Profile links carry a portal state token (`!ut/p/z1/...`), so a hand-built `?companySymbol=` URL redirects to the home page. Discover profile links from the listed-companies page instead of constructing them, and refresh them when they stop resolving.
2. **Seed the crawl from the Tadawul profile, not from guesses.** The profile page lists the company's own website. Agents that guessed domains were wrong for 3004 (nrc.com.sa, not nrcc.com.sa) and 4008 (saco.sa, not saco-ksa.com).
3. **JavaScript-rendered document lists.** 2081, 4008, 4011 and 4163 (and 2282 in part) show their report lists only through scripts or embedded frames, so a plain fetch sees no files. The Relay needs a rendering fetch for these.
4. **Incomplete TLS certificate chains.** 4200 and 4080 fail plain fetch with 'unable to verify the first certificate' but open in a browser. The Relay needs a fetch that tolerates a missing intermediate certificate, or a documented per-host exception.
5. **Official pages that host documents on a third-party CDN.** 2081's official IR page links about 44 PDFs stored on an Argaam Plus bucket. Those are a secondary source and are not recorded; obtain the same filings from Saudi Exchange.
6. **Companies with no financial section on their own site.** 3004 has none (statements exist only on Saudi Exchange), 4081's IR portal is enquiry-only, 4220 has no IR page and 4322 and 4051 showed none. For these, Saudi Exchange announcements are the only source.
7. **A company website that is down.** 4061's official domain returns a WordPress fatal error. Retry later; do not substitute another source.
8. **Renames and code changes.** 2285 (formerly Second Milling), 2140 (formerly Al Ahsa Development), 1183 (formerly Saudi Home Loans), 4130 (renamed Saudi Darb, June 2025) and 4007 (now Al Hammadi Holding). 2282's own site and PDFs use code 3423 although Saudi Exchange lists it as 2282. Match on the Saudi Exchange symbol, not the name.
9. **Short or stale visible history.** 2100 shows only Q3 2021 to Q3 2023, 4323 only 2018-2022, 6040 only 2011-2019 (Arabic only) and 4130 only 2024 onwards. A missing year on the site is not proof the filing does not exist.
10. **Report years that cannot be read from the URL.** 4200 uses numeric file names, and 6012's '2024' annual-report entry links to a file named Annual-2023.pdf. Take the period from the document, not the link text.
11. **Time-limited download links.** 4002 serves annual reports through signed links that expire; record the page, not the link.
12. **One page for everything.** Several companies list annual, quarterly and statement files on one page. Crawl the page; do not treat it as a single document.

## Not done

- Per-company Saudi Exchange announcements URLs are not recorded (`disclosures_url` is empty except where a company's own announcements page was opened): announcements sit inside the profile page and no separate stable URL was verified.
- Several report pages were confirmed to open but their file lists were not enumerated, so the earliest and latest visible years are empty for those companies.
- Arabic-version availability was not checked for every company, so `languages_available` is incomplete.
- No document was downloaded or read.
