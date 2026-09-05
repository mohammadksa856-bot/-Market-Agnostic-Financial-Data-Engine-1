from __future__ import annotations

"""Reviewed coverage catalog. It defines what the factory should collect, not sourced facts."""


CATALOG_SCHEMA_VERSION = 6

# These are the minimum fields that make a company/period usable. Everything else
# remains recommended until a market, sector, or company pack makes it required.
CORE_REQUIRED_FIELDS = {
    "company_name", "symbol", "exchange", "market", "country", "currency", "fiscal_year_end",
    "sector", "industry", "business_description", "revenue", "operating_income", "net_income",
    "net_income_parent", "basic_eps", "cash", "current_assets", "total_assets",
    "current_liabilities", "total_liabilities", "total_equity", "total_liabilities_equity",
    "operating_cash_flow", "capex", "investing_cash_flow", "financing_cash_flow", "cash_end",
    "free_cash_flow",
}

# Group defaults are intentionally overridden where a metric's financial meaning
# differs. This keeps unit/period/aggregation semantics attached to the field, not
# inferred later from its name or the source presentation.
FIELD_OVERRIDES = {
    "weighted_average_shares_basic": {"default_unit": "shares", "aggregation": "average"},
    "weighted_average_shares_diluted": {"default_unit": "shares", "aggregation": "average"},
    "basic_eps": {"default_unit": "currency/share", "aggregation": "none"},
    "eps_diluted": {"default_unit": "currency/share", "aggregation": "none"},
    "shares_outstanding": {"default_unit": "shares", "aggregation": "last"},
    "employees": {"default_unit": "people", "aggregation": "last"},
    "subsidiaries_count": {"default_unit": "count", "aggregation": "last"},
    "trading_volume": {"default_unit": "shares", "aggregation": "sum"},
    "trading_turnover": {"default_unit": "currency", "aggregation": "sum"},
    "ownership_percentage": {"default_unit": "ratio", "aggregation": "none"},
    "government_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "institutional_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "insider_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "foreign_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "free_float": {"default_unit": "ratio", "aggregation": "none"},
    "total_hydrocarbon_production": {"default_unit": "mboe/day", "aggregation": "average"},
    "total_liquids_production": {"default_unit": "mbbl/day", "aggregation": "average"},
    "crude_oil_production": {"default_unit": "mbbl/day", "aggregation": "average"},
    "condensate_production": {"default_unit": "mbbl/day", "aggregation": "average"},
    "natural_gas_liquids_production": {"default_unit": "mbbl/day", "aggregation": "average"},
    "total_gas_production": {"default_unit": "mmscfd", "aggregation": "average"},
    "natural_gas_sales": {"default_unit": "mmscfd", "aggregation": "average"},
    "refinery_throughput": {"default_unit": "mbbl/day", "aggregation": "average"},
    "refinery_utilization": {"default_unit": "ratio", "aggregation": "average"},
    "net_refining_capacity": {"default_unit": "mbbl/day", "aggregation": "last", "period_behavior": "instant"},
    "gross_refining_capacity": {"default_unit": "mbbl/day", "aggregation": "last", "period_behavior": "instant"},
    "chemicals_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "chemicals_sales": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "net_chemicals_production_capacity": {"default_unit": "million_tonnes/year", "aggregation": "last", "period_behavior": "instant"},
    "total_hydrocarbon_reserves": {"default_unit": "million_boe", "aggregation": "last", "period_behavior": "instant"},
    "crude_oil_reserves": {"default_unit": "million_bbl", "aggregation": "last", "period_behavior": "instant"},
    "gas_reserves": {"default_unit": "bcf", "aggregation": "last", "period_behavior": "instant"},
    "reserve_replacement_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "reserve_life_index": {"default_unit": "years", "aggregation": "none"},
    "maximum_sustainable_capacity": {"default_unit": "mbbl/day", "aggregation": "last", "period_behavior": "instant"},
    "spare_capacity": {"default_unit": "mbbl/day", "aggregation": "last", "period_behavior": "instant"},
    "supply_reliability": {"default_unit": "ratio", "aggregation": "average"},
    "average_realized_crude_oil_price": {"default_unit": "USD/bbl", "aggregation": "weighted_average"},
    "average_realized_gas_price": {"default_unit": "USD/mmbtu", "aggregation": "weighted_average"},
    "lifting_cost_per_boe": {"default_unit": "USD/boe", "aggregation": "weighted_average"},
    "upstream_capex_per_boe": {"default_unit": "USD/boe", "aggregation": "weighted_average"},
    "upstream_carbon_intensity": {"default_unit": "kgCO2e/boe", "aggregation": "weighted_average"},
    "scope_1_emissions": {"default_unit": "million_tCO2e", "aggregation": "sum"},
    "scope_2_emissions": {"default_unit": "million_tCO2e", "aggregation": "sum"},
    "methane_intensity": {"default_unit": "ratio", "aggregation": "weighted_average"},
    "flaring_intensity": {"default_unit": "scf/boe", "aggregation": "weighted_average"},
    "water_withdrawal": {"default_unit": "million_m3", "aggregation": "sum"},
    "water_consumption": {"default_unit": "million_m3", "aggregation": "sum"},
}


DIMENSION_DEFINITIONS = {
    "segment": "Reportable business segment", "geography": "Country or geographic region",
    "product": "Product or service family", "asset_class": "Asset or liability class",
    "instrument": "Financial instrument", "maturity_band": "Contractual maturity bucket",
    "jurisdiction": "Tax or legal jurisdiction", "fair_value_level": "IFRS/GAAP fair-value hierarchy level",
    "counterparty": "Named counterparty", "counterparty_type": "Counterparty classification",
    "cash_generating_unit": "Cash-generating unit", "facility_type": "Financing facility type",
    "financing_type": "Financing type", "financing_class": "Financing classification",
    "plan_type": "Employee benefit plan type", "benefit_type": "Employee benefit type",
    "balance_type": "Opening, movement, or closing balance", "direction": "Inflow or outflow",
    "compensation_type": "Compensation component", "provision_class": "Provision class",
    "asset_type": "Asset type", "commitment_type": "Commitment class", "beneficiary": "Guarantee beneficiary",
    "guarantee_type": "Guarantee class", "reconciliation_component": "Reconciliation line",
    "measure": "Reported measure", "origin": "Domestic or international origin",
    "basis": "Measurement or presentation basis", "overlap_note": "Non-additivity disclosure",
    "measurement": "Measurement basis", "security_basis": "Secured or unsecured basis",
    "reported_label": "Source-native label", "component": "Statement or note component",
    "reported_as": "Source-native presentation", "ledger": "Accounting ledger classification",
    "cost_type": "Cost classification", "liability_class": "Liability classification",
}

PERIOD_KINDS_BY_BEHAVIOR = {
    "flow": ("quarter", "ytd", "fy", "ttm"),
    "instant": ("instant",),
    "derived": ("quarter", "ytd", "fy", "ttm", "instant", "as_of"),
    "as_of": ("as_of",),
    "event": ("event", "as_of"),
    "forward": ("quarter", "fy"),
    "mixed": ("quarter", "ytd", "fy", "ttm", "instant", "as_of"),
}

DIMENSIONS_BY_CATEGORY = {
    "income_statement": tuple(DIMENSION_DEFINITIONS),
    "balance_sheet": tuple(DIMENSION_DEFINITIONS),
    "cash_flow": tuple(DIMENSION_DEFINITIONS), "company_model": (),
    "market_data": (), "ownership": (), "corporate_actions": (), "disclosures": (),
    "per_share": ("segment", "geography", "product"),
    "profitability": ("segment", "geography", "product"),
    "liquidity_solvency": ("segment", "geography", "product"),
    "efficiency": ("segment", "geography", "product"),
    "growth": ("segment", "geography", "product"),
    "valuation": ("segment", "geography", "product"),
    "investor_analytics": ("segment", "geography", "product"),
    "segments": ("segment", "geography", "product", "origin"),
    "oil_gas_operations": ("segment", "geography", "product", "measure", "basis"),
    "commercial_pipeline": ("segment", "geography", "product", "counterparty", "maturity_band"),
    "consensus": (),
    # Notes legitimately use heterogeneous axes; the vocabulary is still governed.
    "financial_notes": tuple(DIMENSION_DEFINITIONS),
}


def _unit_family(unit: str) -> str:
    if unit == "currency":
        return "monetary"
    if unit == "currency/share":
        return "per_share"
    if unit == "ratio":
        return "ratio"
    if unit in {"text", "json", "date", "boolean"}:
        return unit
    if unit in {"shares", "people", "count"}:
        return "count"
    return "physical_or_scalar"


def _keys(value: str) -> list[str]:
    return value.split()


GROUPS = (
    ("company_model", "company_profile", "company_profile", "as_of", "text", "none", "all", "*", _keys(
        "company_name company_name_ar legal_name legal_name_ar symbol isin cik lei exchange market country currency "
        "listing_date fiscal_year_end sector industry sub_industry business_description headquarters_address website "
        "investor_relations_url incorporation_date founding_date legal_form employees auditor credit_rating sharia_status "
        "reporting_standard reporting_languages ceo_name chairman_name products_services geographic_presence "
        "subsidiaries_count investor_contact_email"
    )),
    ("income_statement", "data_points", "income_statement", "flow", "currency", "sum", "all", "*", _keys(
        "revenue other_income_related_to_sales revenue_and_other_income_related_to_sales cost_of_revenue gross_profit "
        "selling_general_administrative_expense general_and_administrative_expense selling_and_distribution_expense "
        "research_and_development_expense exploration_expense depreciation_amortization "
        "royalties_and_other_taxes purchases producing_manufacturing_expense operating_costs operating_expenses operating_income "
        "interest_income interest_expense finance_income finance_and_other_income finance_costs "
        "investment_income share_of_profit_associates impairment_charges gain_loss_asset_sales other_income other_expense "
        "income_before_income_taxes_and_zakat zakat_expense income_tax_expense income_taxes_and_zakat net_income "
        "net_income_parent net_income_noncontrolling continuing_operations_income discontinued_operations_income "
        "comprehensive_income adjusted_ebitda ebitda ebit adjusted_net_income basic_eps eps_diluted weighted_average_shares_basic "
        "weighted_average_shares_diluted minority_interest_income"
    )),
    ("balance_sheet", "data_points", "balance_sheet", "instant", "currency", "last", "all", "*", _keys(
        "cash cash_restricted short_term_investments accounts_receivable inventory due_from_government current_tax_assets other_current_assets assets_held_for_sale "
        "current_assets property_plant_equipment gross_property_plant_equipment accumulated_depreciation right_of_use_assets "
        "goodwill intangible_assets investments_associates long_term_investments deferred_tax_assets employee_benefits_asset other_noncurrent_assets "
        "noncurrent_assets total_assets accounts_payable accrued_expenses employee_benefits_current current_debt lease_liabilities_current "
        "tax_payable royalties_payable trade_payables_other_liabilities liabilities_held_for_sale other_current_liabilities current_liabilities long_term_debt lease_liabilities_noncurrent provisions "
        "employee_benefits_noncurrent deferred_tax_liabilities other_noncurrent_liabilities noncurrent_liabilities total_liabilities "
        "share_capital additional_paid_in_capital treasury_shares retained_earnings statutory_reserve other_reserves "
        "accumulated_other_comprehensive_income equity_parent noncontrolling_interests total_equity total_liabilities_equity "
        "net_debt working_capital invested_capital shares_outstanding tangible_book_value"
    )),
    ("cash_flow", "data_points", "cash_flow", "flow", "currency", "sum", "all", "*", _keys(
        "net_income_cash_flow depreciation_amortization_cash_flow impairment_cash_flow share_based_compensation deferred_tax "
        "gain_loss_investing working_capital_change accounts_receivable_change inventory_change accounts_payable_change "
        "other_operating_changes exploration_evaluation_written_off investment_fair_value_change due_from_government_change "
        "royalties_payable_change operating_cash_flow capex acquisitions proceeds_asset_sales purchases_investments "
        "proceeds_investments loans_to_affiliates investing_cash_flow debt_issued debt_repaid lease_payments shares_issued "
        "shares_repurchased dividends_paid dividends_noncontrolling base_dividends_paid performance_linked_dividends_paid "
        "proceeds_noncontrolling_sale short_term_borrowings_net distributions_joint_ventures_associates dividends_from_investments financing_cash_flow "
        "foreign_exchange_effect cash_change cash_beginning cash_end interest_paid interest_received taxes_paid zakat_paid "
        "free_cash_flow owner_earnings discretionary_cash_flow"
    )),
    ("profitability", "data_points", "ratios", "derived", "ratio", "none", "all", "*", _keys(
        "gross_margin operating_margin ebit_margin ebitda_margin pretax_margin effective_tax_rate net_margin fcf_margin cfo_margin return_on_assets "
        "return_on_equity return_on_invested_capital roace return_on_capital_employed cash_return_on_assets"
    )),
    ("liquidity_solvency", "data_points", "ratios", "derived", "ratio", "none", "all", "*", _keys(
        "current_ratio quick_ratio cash_ratio debt_to_equity debt_to_assets liabilities_to_equity liabilities_to_assets "
        "net_debt_to_equity net_debt_to_ebitda debt_to_ebitda interest_coverage fixed_charge_coverage gearing equity_ratio"
    )),
    ("efficiency", "data_points", "ratios", "derived", "ratio", "none", "all", "*", _keys(
        "asset_turnover inventory_turnover receivables_turnover payables_turnover days_sales_outstanding days_inventory "
        "days_payables cash_conversion_cycle capex_to_revenue capex_to_cfo receivables_to_revenue inventory_to_assets ppe_to_assets"
    )),
    ("growth", "data_points", "growth", "derived", "ratio", "none", "all", "*", _keys(
        "revenue_growth gross_profit_growth operating_income_growth ebitda_growth net_income_growth eps_growth asset_growth "
        "equity_growth debt_growth operating_cash_flow_growth free_cash_flow_growth dividend_growth revenue_cagr_3y "
        "revenue_cagr_5y net_income_cagr_3y net_income_cagr_5y eps_cagr_3y eps_cagr_5y"
    )),
    ("per_share", "data_points", "per_share", "derived", "currency/share", "none", "all", "*", _keys(
        "revenue_per_share operating_cash_flow_per_share free_cash_flow_per_share dividends_per_share book_value_per_share "
        "tangible_book_value_per_share earnings_per_share_normalized"
    )),
    ("valuation", "data_points", "valuation", "derived", "ratio", "none", "all", "*", _keys(
        "market_cap enterprise_value price_to_earnings price_to_sales price_to_book price_to_tangible_book price_to_cash_flow "
        "price_to_free_cash_flow enterprise_value_to_revenue enterprise_value_to_ebitda enterprise_value_to_ebit "
        "earnings_yield fcf_yield dividend_yield peg_ratio graham_number shareholder_yield"
    )),
    ("market_data", "market_prices", "market", "event", "decimal", "none", "all", "*", _keys(
        "price_open price_high price_low price_close price_adjusted_close trading_volume trading_turnover vwap "
        "beta_1y beta_5y volatility_30d average_volume_30d fifty_two_week_high fifty_two_week_low"
    )),
    ("ownership", "ownership_positions", "ownership", "event", "decimal", "none", "all", "*", _keys(
        "holder_name holder_type shares_held ownership_percentage government_ownership institutional_ownership insider_ownership "
        "foreign_ownership free_float major_holder_change"
    )),
    ("corporate_actions", "corporate_actions", "corporate_actions", "event", "json", "none", "all", "*", _keys(
        "cash_dividend bonus_shares stock_split reverse_split rights_issue capital_increase capital_reduction share_buyback "
        "merger acquisition spin_off delisting symbol_change tender_offer"
    )),
    ("disclosures", "disclosures", "disclosures", "event", "text", "none", "all", "*", _keys(
        "financial_results_announcement earnings_release annual_report interim_report board_change management_change contract_award "
        "litigation regulatory_action related_party_transaction guidance risk_factor strategy_update material_event"
    )),
    ("financial_notes", "data_points", "financial_notes", "mixed", "currency", "none", "all", "*", _keys(
        "revenue_by_product revenue_by_geography revenue_by_customer_type contract_assets contract_liabilities "
        "remaining_performance_obligations customer_concentration property_plant_equipment_by_class "
        "ppe_additions_by_class ppe_disposals_by_class depreciation_by_ppe_class accumulated_depreciation_by_class "
        "capital_commitments intangible_assets_by_class intangible_additions_by_class intangible_amortization_by_class "
        "goodwill_by_cash_generating_unit impairment_by_asset_class borrowings_by_instrument borrowings_by_currency "
        "borrowings_by_maturity weighted_average_borrowing_rate undrawn_credit_facilities secured_borrowings "
        "unsecured_borrowings finance_cost_by_type current_tax_expense deferred_tax_expense "
        "tax_reconciliation_by_component deferred_tax_assets_by_component deferred_tax_liabilities_by_component "
        "unrecognized_tax_losses defined_benefit_obligation fair_value_plan_assets employee_benefit_expense "
        "service_cost_employee_benefits net_interest_employee_benefits actuarial_gain_loss plan_assets_by_class "
        "benefit_obligation_by_geography financial_assets_by_class financial_liabilities_by_class "
        "fair_value_assets_by_level fair_value_liabilities_by_level expected_credit_losses related_party_revenue "
        "related_party_purchases related_party_receivables related_party_payables related_party_loans "
        "key_management_compensation lease_maturity_by_band lease_interest_expense short_term_lease_expense low_value_lease_expense "
        "variable_lease_expense provisions_by_class provision_additions provision_utilization contingencies "
        "purchase_commitments purchase_commitment_units lease_commitments_not_commenced "
        "cancellable_commitment_exposure other_commitments_by_type guarantees_issued"
    )),
    ("commercial_pipeline", "data_points", "commercial", "mixed", "currency", "none", "all", "*", _keys(
        "sales_order_backlog contracted_sales_value contracted_sales_volume committed_offtake_volume "
        "take_or_pay_commitments minimum_volume_commitments average_selling_price_by_product "
        "sales_volume_by_product sales_volume_by_geography sales_contract_count contract_renewal_profile "
        "book_to_bill_ratio advance_payment_long_term_sales_agreement"
    )),
    ("investor_analytics", "data_points", "analytics", "derived", "ratio", "none", "all", "*", _keys(
        "return_on_tangible_assets return_on_tangible_equity income_quality payout_ratio capex_to_depreciation "
        "selling_general_administrative_to_revenue research_development_to_revenue share_based_compensation_to_revenue "
        "net_current_asset_value graham_net_net cash_per_share capex_per_share debt_per_share ebitda_per_share "
        "revenue_cagr_10y net_income_cagr_10y eps_cagr_10y dividend_cagr_10y operating_cash_flow_cagr_10y "
        "free_cash_flow_cagr_10y total_return_1y total_return_3y total_return_5y total_return_10y "
        "simple_moving_average_20d simple_moving_average_50d simple_moving_average_200d price_to_sma_20d "
        "price_to_sma_50d price_to_sma_200d"
    )),
    ("consensus", "consensus_estimates", "consensus", "forward", "decimal", "none", "all", "*", _keys(
        "revenue_estimate ebitda_estimate ebit_estimate net_income_estimate "
        "selling_general_administrative_expense_estimate eps_estimate"
    )),
    ("segments", "data_points", "segments", "flow", "currency", "sum", "industry", "Integrated Oil & Gas", _keys(
        "upstream_revenue downstream_revenue corporate_revenue upstream_operating_income downstream_operating_income "
        "upstream_ebit upstream_adjusted_ebit downstream_ebit downstream_adjusted_ebit corporate_ebit corporate_adjusted_ebit "
        "upstream_ebitda downstream_ebitda upstream_capex downstream_capex corporate_capex domestic_revenue international_revenue "
        "crude_oil_revenue refined_products_revenue chemicals_revenue natural_gas_revenue lng_revenue"
    )),
    ("oil_gas_operations", "data_points", "operational", "flow", "decimal", "average", "industry", "Integrated Oil & Gas", _keys(
        "total_hydrocarbon_production total_liquids_production crude_oil_production condensate_production natural_gas_liquids_production "
        "total_gas_production natural_gas_sales production_entitlement lifting_volume refinery_throughput refinery_utilization "
        "net_refining_capacity gross_refining_capacity chemicals_production chemicals_sales net_chemicals_production_capacity "
        "total_hydrocarbon_reserves crude_oil_reserves gas_reserves reserve_replacement_ratio reserve_life_index "
        "maximum_sustainable_capacity spare_capacity supply_reliability average_realized_crude_oil_price average_realized_gas_price "
        "average_realized_refined_product_price lifting_cost_per_boe upstream_capex_per_boe finding_development_cost_per_boe upstream_carbon_intensity "
        "downstream_crude_utilization base_oils_sold finished_lubricants_sold liquid_chemicals_traded crude_refined_products_traded "
        "scope_1_emissions scope_2_emissions methane_intensity flaring_intensity water_withdrawal water_consumption energy_intensity "
        "hydrocarbon_discharge_to_water sox_emissions industrial_waste_disposed"
    )),
)


def iter_catalog_fields():
    seen = set()
    for category, storage_domain, statement, period_behavior, unit, aggregation, scope_type, scope_value, keys in GROUPS:
        for key in keys:
            if key in seen:
                raise ValueError(f"duplicate catalog field definition: {key}")
            seen.add(key)
            item = {
                "field_key": key,
                "display_name": key.replace("_", " ").title(),
                "category": category,
                "storage_domain": storage_domain,
                "statement": statement,
                "period_behavior": period_behavior,
                "value_type": "decimal" if storage_domain == "data_points" else unit,
                "default_unit": unit,
                "aggregation": aggregation,
                "scope_type": scope_type,
                "scope_value": scope_value,
                "requirement": "required" if key in CORE_REQUIRED_FIELDS else "recommended",
                "pack_key": "oil_gas_v2" if scope_type == "industry" else "company_core_v4",
            }
            item.update(FIELD_OVERRIDES.get(key, {}))
            item["allowed_period_kinds"] = PERIOD_KINDS_BY_BEHAVIOR[item["period_behavior"]]
            item["allowed_dimensions"] = DIMENSIONS_BY_CATEGORY[category]
            item["unit_family"] = _unit_family(item["default_unit"])
            yield item


CATALOG_SIZE = sum(1 for _ in iter_catalog_fields())
