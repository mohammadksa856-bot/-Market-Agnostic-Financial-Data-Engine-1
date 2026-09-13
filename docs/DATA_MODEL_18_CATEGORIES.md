# The 18-category company data model

What a company record must contain for an investor to understand the
business without opening another source. This replaces the earlier
6-category sketch (historical financials, ratios, operational KPIs,
company info, news, valuation), which was written from memory and turned
out to be incomplete when checked against how professionals actually
analyse a company.

## How this was verified

The 6-category list was not expanded by brainstorming. It was checked,
item by item, against six independent references — three of them
professional standards rather than products:

| Reference | What it is | Why it counts |
| --- | --- | --- |
| [CFA Institute, *Equity Research Report Essentials*](https://www.cfainstitute.org/sites/default/files/-/media/documents/support/research-challenge/challenge/rc-equity-research-report-essentials.pdf) (Sept 2020) | The professional standard for what an equity research report must contain | Authoritative, vendor-neutral |
| [GIB Capital — Saudi Tadawul Group](https://www.gibcapital.com/media/ze0brn0b/tadawul_9june26_en.pdf) (9 June 2026) | A real sell-side report on a Saudi listed company | Shows what a bank actually publishes |
| [Derayah Financial — Rasan, initiation of coverage](https://argaamplus.s3.amazonaws.com/fafe4bf2-9130-4d38-9686-292cf92710f0.pdf) (11 Mar 2026) | A full 14-page initiation report | The most complete report type there is |
| [Argaam company page](https://www.argaam.com/en/tadawul/tasi/alrajhi/profile) | 18 tabs per company | What the leading Saudi portal considers essential |
| [Sahmk API](https://www.sahmk.sa/developers) | A Tadawul-licensed data vendor's model | What a licensed Saudi data product ships |
| [Simply Wall St Company Analysis Model](https://github.com/SimplyWallSt/Company-Analysis-Model/blob/master/MODEL.markdown) | 35 explicit, enumerable checks | A fully specified analysis model, published openly |

## The two structural flaws this exposed

Individual missing fields mattered less than two defects in the shape of
the old model.

**1. The model was entirely backward-looking.** Every real research
report is built around the forward view: GIB projects 2026e–2027e,
Derayah projects 2024a–2028e for revenue, operating profit, net profit,
margins, EPS and DPS, and GIB carries a dedicated *"Revision in
estimates"* table comparing the current forecast against the previous
one. The old 6 categories contained no forward number at all. An
investor does not buy the past.

**2. The model assumed one ratio set fits every company.** Simply Wall
St runs three distinct financial-health models — one for ordinary
companies, one for **financial institutions** (assets-to-equity leverage,
bad-loan coverage, deposits-to-liabilities, loans-to-assets,
loans-to-deposits, net charge-off ratio), and modified checks for
**loss-making companies** (does cash cover the current burn rate for more
than a year, and the growing burn rate). A single ratio list silently
breaks for banks, insurers and the many small Nomu companies that are
not yet profitable.

## The 18 categories

### Layer A — Foundation: what the company is

**1. Identity**
`legal_name`, `legal_name_ar`, `founding_date`, `incorporation_date`,
`cr_number`, `headquarters_address`, `legal_form`, `exchange`, `symbol`,
`isin`, `sector`, `industry`, `fiscal_year_end`, `reporting_standard`,
`sharia_status`, `website`, `investor_relations_url`, `listing_date`.

**2. Business model and unit economics**
`business_description`, `products_services`, `revenue_by_product` (each
line with its share of revenue), `unit_economics` (the metric the
business actually turns — take-rate, revenue per branch, per subscriber,
per square metre), `key_revenue_drivers`, `key_cost_drivers`,
`value_chain_position`, `geographic_presence`, `subsidiaries` (name and
ownership %). CFA is explicit that a business description must "convey a
clear understanding of the company's economics, including a discussion of
the key drivers of revenues and expenses" — a prose description alone
does not satisfy this.

**3. Management and governance**
`ceo_name`, `chairman_name`, `executive_management_team`,
`board_of_directors`, `board_independence_ratio`, `board_committees`,
`executive_compensation_policy`, `ceo_pay_vs_peer_median`,
`avg_management_tenure`, `avg_board_tenure`, `insider_transactions`
(net buying/selling), `related_party_transactions`, `auditor_name`,
`auditor_tenure_years`, `succession_planning`.

**4. Ownership and share register**
`ownership_positions` (holder, %, type), `major_shareholders_5pct`,
`free_float_percent`, `free_float_trend`, `foreign_ownership_percent`,
`foreign_ownership_limit`, `qfi_holding`, `pledged_shares`,
`government_ownership`, `index_memberships`, `index_weight`.
Foreign ownership and its limit appear in the stock-info box of both real
research reports and as a dedicated Argaam tab; they are not optional in
this market.

### Layer B — Performance: what happened

**5. Historical financial statements**
Income statement, balance sheet and cash flow, annual and quarterly, at
least five years, from the audited statements themselves. Plus
`capex` broken out, `free_cash_flow` (operating cash flow − capex), and
`segment_breakdown` (revenue, assets, profit per operating segment).

**6. Earnings quality and accounting signals**
`adjusted_net_income` (recurring earnings), `one_time_items` (type,
amount, reason), `earnings_quality_ratio` (operating cash flow ÷ net
income), `auditor_opinion_type`, `going_concern_flag`,
`material_weakness_flag`, `off_balance_sheet_financing`,
`accounting_policy_changes`, `restatements`. CFA calls qualified audit
opinions and material weaknesses "automatic red flags"; Argaam publishes
a *Recurring EPS* separate from reported EPS for the same reason. The
accuracy review of this project's own data repeatedly hit exactly these
cases — a land-sale gain, one-time IPO costs, going-concern warnings at
Saudi Cable and United Cooperative — and had nowhere structured to put
them.

**7. Financial ratios — three sets, selected by company type**

*Ordinary companies:* margins (gross, operating, net), ROE, ROA, ROIC,
ROCE, current ratio, quick ratio, debt-to-equity, interest coverage,
debt-to-EBITDA, asset turnover, receivable/payable/inventory days,
revenue and earnings growth, 3y and 5y CAGR.

*Financial institutions:* assets-to-equity leverage, bad-loan coverage,
deposits-to-liabilities, loans-to-assets, loans-to-deposits, net
charge-off ratio, NPL ratio (on **gross** loans), cost-to-income, capital
adequacy ratio, equity-to-RWA.

*Loss-making companies:* cash runway at the current burn rate, cash
runway at the historical burn growth rate, months to breakeven.

**8. Operational KPIs — defined per industry**
Banks: branches, ATMs, POS terminals, digital active users, total
customers, Saudization, NPS. Retail: store count, same-store sales
growth, sales per square metre. Telecom: subscribers, ARPU, churn.
Real estate: units delivered, occupancy, land bank. Insurance: combined
ratio, loss ratio, solvency margin. Industrial: capacity utilisation,
production volume.

**9. Dividends and corporate actions**
`dividend_history`, `dividend_policy` (stated payout %),
`dividend_yield`, `payout_ratio`, `payout_coverage_forward`,
`dividend_volatility_10y`, `dividend_growth_10y`, `buyback_program`,
`corporate_actions` (cash dividends, bonus shares, rights issues,
splits, capital changes — each with announcement, eligibility and
effective dates).

### Layer C — Context: compared to what

**10. Industry and sector**
`sector_dynamics`, `porter_five_forces`, `market_size_and_growth`,
`penetration_vs_peer_markets`, `regulatory_environment`,
`competitive_moat`, `barriers_to_entry`, `sector_aggregates` (SAMA
banking aggregates, insurance GWP, and similar). The Derayah initiation
spends four of fourteen pages here — sector education, insurance
penetration as a share of GDP benchmarked against other countries, and
the regulatory changes driving demand. Sector data is shared across every
company in the sector, so it is roughly twenty datasets, not four hundred.

**11. Competitors and market share**
`peer_group`, `peer_comparison_table` (the same ratios and multiples side
by side), `market_share`, `market_share_trend`, `relative_positioning`.

**12. Liquidity, trading and market risk**
`avg_daily_traded_value`, `avg_daily_volume`, `bid_ask_spread`, `beta`,
`volatility`, `free_float_turnover`, `relative_performance_vs_index`,
`negotiated_deals` (block trades), `52_week_range`.
CFA treats float and liquidity as basic information an analyst must state,
not as a footnote.

### Layer D — Forward view and valuation: what it is worth

**13. Forecasts and company guidance**
`company_guidance` (the issuer's own stated outlook), `revenue_forecast`,
`earnings_forecast`, `eps_forecast`, `dps_forecast`, `margin_forecast`,
`roe_forecast` — three to five years forward, each tagged with its source
and date. `estimate_revisions` (current versus previous forecast).

**14. Analyst coverage**
`analyst_ratings` (firm, rating, date), `target_prices`, `consensus_rating`,
`consensus_target`, `upside_to_target`, `analyst_count`, `estimate_history`.

**15. Valuation — two methods, never one**
*Relative:* `pe_ratio`, `pb_ratio`, `ev_ebitda`, `ps_ratio`, `peg_ratio`,
`dividend_yield`, each against its own history and against the sector and
market average.
*Intrinsic:* a DCF with its assumptions visible — `wacc`,
`terminal_growth_rate`, `forecast_fcf`, `terminal_value`,
`intrinsic_value_per_share`, `upside_to_intrinsic`, plus a sensitivity
table. CFA: "Because model outputs can vary, more than one valuation
model should be used." The Derayah report lays out the full ladder:
NOPAT, capex, free cash flow, terminal value, discount factor, DCF + TV,
plus cash, equity value, target price per share.

### Layer E — Risk and disclosure

**16. Risks and exposures**
`risk_factors` (as disclosed by the issuer), `debt_maturity_schedule`
(the maturity wall), `debt_currency_breakdown`,
`fixed_vs_floating_rate_debt`, `credit_rating`,
`customer_concentration` (share of revenue from the largest customers),
`supplier_concentration`, `fx_exposure` and hedging policy,
`commodity_exposure`, `litigation`, `contingent_liabilities`,
`zakat_tax_disputes`, `government_dependence` (share of revenue from
government contracts or subsidised inputs), `regulatory_licences`,
`ipo_lockup_expiry` for recently listed companies.

**17. ESG**
`environmental` (emissions, energy, water, waste), `social`
(Saudization, workforce, community, customer satisfaction),
`governance_esg` (board composition, audit committee, anti-corruption
policy), `sustainability_report_url`. CFA gives ESG its own section.

**18. News, disclosures and investor materials**
`official_announcement` (exchange or issuer channel — the same trust
level as a financial disclosure), `press_coverage` (named outlets only,
always attributed, never shown as a bare fact),
`investor_presentations`, `earnings_call_transcripts`, `annual_reports`,
`events_calendar` (results date, AGM, ex-dividend, eligibility,
conferences), `mergers_and_acquisitions`.

## Baseline: Al Rajhi Bank (1120), the best-instrumented company

Measured 2026-09-13 across every source this project holds.

| Status | Count | Categories |
| --- | --- | --- |
| Complete | 3 | 1 Identity · 5 Financial statements (487 facts, 5 years) · 8 Operational KPIs |
| Partial | 10 | 2, 3, 4, 7, 9, 11, 12, 15, 16, 18 |
| Empty | 5 | 6 Earnings quality · 10 Industry · 13 Forecasts · 14 Analyst coverage · 17 ESG |

The financial-institution ratio set computes correctly from data already
held: leverage 7.3x, loans-to-deposits 112.8%, deposits-to-liabilities
74.1%, bad-loan coverage 152%, NPL 0.76%, equity-to-RWA 21.2%, ROE 17.3%,
ROA 2.38%.

## Defects found by applying the model

1. **Sign convention.** `total_operating_expenses` is stored negative
   (−11,447,469 thousand SAR), so cost-to-income computes as −29.3%
   instead of 29.3%. Any ratio consuming this field is silently wrong.
2. **Undeclared methodology.** ROE computes to 17.3% here against
   Argaam's 23.49%. Neither is wrong: this project uses year-end equity,
   Argaam uses trailing-twelve-month average equity. Without publishing
   the basis, correct numbers look like errors.
3. **Wrong denominator.** NPL ratio is computed against *net* loans
   because `gross_loans` is not stored at all. The ratio belongs on gross
   loans.

## The second gap: data held but never delivered

Missing data is only half the problem. For Al Rajhi, operational KPIs
(511 branches, 4,327 ATMs, 20.6M customers) exist in a reviewed manifest,
while the consumer database's `operational_kpis` field is empty. The same
holds for `ownership`, `news` and `trading_stats`. Filling categories and
delivering them are separate pieces of work, and the second one is
currently the cheaper win.
