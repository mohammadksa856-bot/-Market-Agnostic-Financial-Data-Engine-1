from __future__ import annotations

"""Reviewed coverage catalog. It defines what the factory should collect, not sourced facts."""


CATALOG_SCHEMA_VERSION = 11

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
    "market_cap": {"default_unit": "currency", "aggregation": "last"},
    "enterprise_value": {"default_unit": "currency", "aggregation": "last"},
    "graham_number": {"default_unit": "currency/share", "aggregation": "none"},
    "nopat": {"default_unit": "currency", "aggregation": "sum"},
    "economic_profit_proxy": {"default_unit": "currency", "aggregation": "sum"},
    "fcf_payout_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "dividend_cagr_3y": {"default_unit": "ratio", "aggregation": "none"},
    "dividend_cagr_5y": {"default_unit": "ratio", "aggregation": "none"},
    "dividend_payment_frequency": {"default_unit": "text", "value_type": "text", "aggregation": "none"},
    "weighted_average_shares_basic": {"default_unit": "shares", "aggregation": "average"},
    "weighted_average_shares_diluted": {"default_unit": "shares", "aggregation": "average"},
    "basic_eps": {"default_unit": "currency/share", "aggregation": "none"},
    "eps_diluted": {"default_unit": "currency/share", "aggregation": "none"},
    "shares_outstanding": {"default_unit": "shares", "aggregation": "last"},
    "employees": {"default_unit": "people", "aggregation": "last"},
    "subsidiaries_count": {"default_unit": "count", "aggregation": "last"},
    "trading_volume": {"default_unit": "shares", "aggregation": "sum"},
    "trading_turnover": {"default_unit": "currency", "aggregation": "sum"},
    "price_open": {"default_unit": "currency/share", "aggregation": "last"},
    "price_high": {"default_unit": "currency/share", "aggregation": "last"},
    "price_low": {"default_unit": "currency/share", "aggregation": "last"},
    "price_close": {"default_unit": "currency/share", "aggregation": "last"},
    "previous_close": {"default_unit": "currency/share", "aggregation": "last"},
    "price_adjusted_close": {"default_unit": "currency/share", "aggregation": "last"},
    "beta_1y": {"default_unit": "ratio", "aggregation": "none"},
    "beta_5y": {"default_unit": "ratio", "aggregation": "none"},
    "volatility_30d": {"default_unit": "ratio", "aggregation": "none"},
    "percent_from_52w_high": {"default_unit": "ratio", "aggregation": "none"},
    "percent_from_52w_low": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_1m": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_3m": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_6m": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_ytd": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_1y": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_3y": {"default_unit": "ratio", "aggregation": "none"},
    "market_return_5y": {"default_unit": "ratio", "aggregation": "none"},
    "fifty_two_week_high": {"default_unit": "currency/share", "aggregation": "last"},
    "fifty_two_week_low": {"default_unit": "currency/share", "aggregation": "last"},
    "ownership_percentage": {"default_unit": "ratio", "aggregation": "none"},
    "government_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "institutional_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "insider_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "foreign_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "free_float": {"default_unit": "ratio", "aggregation": "none"},
    "piotroski_f_score": {"default_unit": "score", "aggregation": "none"},
    "altman_z_score": {"default_unit": "score", "aggregation": "none"},
    "beneish_m_score": {"default_unit": "score", "aggregation": "none"},
    "bank_health_score": {"default_unit": "score", "aggregation": "none"},
    "retail_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "strategic_ownership": {"default_unit": "ratio", "aggregation": "none"},
    "top_5_shareholder_concentration": {"default_unit": "ratio", "aggregation": "none"},
    "top_10_shareholder_concentration": {"default_unit": "ratio", "aggregation": "none"},
    "free_float_shares": {"default_unit": "shares", "aggregation": "last"},
    "free_float_market_cap": {"default_unit": "currency", "aggregation": "last"},
    "years_consecutive_dividend_payments": {"default_unit": "years", "aggregation": "last"},
    "dividend_yield_ttm": {"default_unit": "ratio", "aggregation": "none"},
    "payout_ratio_ttm": {"default_unit": "ratio", "aggregation": "none"},
    "fcf_payout_ratio_ttm": {"default_unit": "ratio", "aggregation": "none"},
    "dividend_coverage_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "fcf_dividend_coverage_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "dividend_stability_score": {"default_unit": "ratio", "aggregation": "none"},
    "dividend_per_share_ttm": {"default_unit": "currency/share", "aggregation": "sum"},
    "forward_dividend_per_share": {"default_unit": "currency/share", "aggregation": "sum"},
    "dividend_installments_count": {"default_unit": "count", "aggregation": "sum"},
    "retail_shareholders_count": {"default_unit": "count", "aggregation": "last"},
    "institutional_shareholders_count": {"default_unit": "count", "aggregation": "last"},
    "foreign_investor_limit": {"default_unit": "ratio", "aggregation": "none"},
    "ownership_concentration": {"default_unit": "ratio", "aggregation": "none"},
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
    "production_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "production_capacity": {"default_unit": "million_tonnes/year", "aggregation": "last", "period_behavior": "instant"},
    "capacity_utilization": {"default_unit": "ratio", "aggregation": "average"},
    "average_selling_price": {"default_unit": "currency/tonne", "aggregation": "weighted_average"},
    "plant_reliability": {"default_unit": "ratio", "aggregation": "average"},
    "energy_consumption_intensity": {"default_unit": "GJ/tonne", "aggregation": "weighted_average"},
    "feedstock_cost_per_tonne": {"default_unit": "currency/tonne", "aggregation": "weighted_average"},
    "ethylene_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "polyethylene_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "polypropylene_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "methanol_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "fertilizer_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "steel_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "petrochemicals_sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "agri_nutrients_sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "specialties_sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "metals_sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "domestic_sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "export_sales_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "scope_1_emissions_chemicals": {"default_unit": "million_tCO2e", "aggregation": "sum"},
    "scope_2_emissions_chemicals": {"default_unit": "million_tCO2e", "aggregation": "sum"},
    "water_withdrawal_chemicals": {"default_unit": "million_m3", "aggregation": "sum"},
    "water_consumption_chemicals": {"default_unit": "million_m3", "aggregation": "sum"},
    "greenhouse_gas_intensity": {"default_unit": "tCO2e/tonne", "aggregation": "weighted_average"},
    "lost_time_injury_rate": {"default_unit": "incidents/200k_hours", "aggregation": "average"},
    "total_recordable_injury_rate": {"default_unit": "incidents/200k_hours", "aggregation": "average"},
    "circular_feedstock_volume": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "recycled_product_sales": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "loans_to_deposits_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "net_interest_margin": {"default_unit": "ratio", "aggregation": "none"},
    "cost_of_funds": {"default_unit": "ratio", "aggregation": "none"},
    "nonperforming_loans_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "nonperforming_loans_coverage": {"default_unit": "ratio", "aggregation": "none"},
    "cet1_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "tier1_capital_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "capital_adequacy_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "casa_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "cost_to_income_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "cost_of_risk": {"default_unit": "ratio", "aggregation": "none"},
    "gross_written_premium": {"default_unit": "currency", "aggregation": "sum"},
    "loss_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "combined_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "expense_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "retention_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "solvency_ratio": {"default_unit": "ratio", "aggregation": "none"},
    "subscriber_count": {"default_unit": "count", "aggregation": "last"},
    "mobile_subscribers": {"default_unit": "count", "aggregation": "last"},
    "broadband_subscribers": {"default_unit": "count", "aggregation": "last"},
    "arpu": {"default_unit": "currency/subscriber", "aggregation": "weighted_average"},
    "churn_rate": {"default_unit": "ratio", "aggregation": "average"},
    "data_traffic": {"default_unit": "petabytes", "aggregation": "sum"},
    "network_coverage": {"default_unit": "ratio", "aggregation": "last"},
    "electricity_generated": {"default_unit": "GWh", "aggregation": "sum"},
    "electricity_sold": {"default_unit": "GWh", "aggregation": "sum"},
    "installed_generation_capacity": {"default_unit": "MW", "aggregation": "last"},
    "renewable_capacity": {"default_unit": "MW", "aggregation": "last"},
    "capacity_factor": {"default_unit": "ratio", "aggregation": "average"},
    "network_losses": {"default_unit": "ratio", "aggregation": "average"},
    "water_produced": {"default_unit": "million_m3", "aggregation": "sum"},
    "ore_production": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "processed_ore": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "recoverable_reserves": {"default_unit": "million_tonnes", "aggregation": "last"},
    "ore_grade": {"default_unit": "ratio", "aggregation": "weighted_average"},
    "recovery_rate": {"default_unit": "ratio", "aggregation": "weighted_average"},
    "cash_cost_per_tonne": {"default_unit": "currency/tonne", "aggregation": "weighted_average"},
    "all_in_sustaining_cost": {"default_unit": "currency/tonne", "aggregation": "weighted_average"},
    "gross_leasable_area": {"default_unit": "sqm", "aggregation": "last"},
    "occupancy_rate": {"default_unit": "ratio", "aggregation": "average"},
    "net_asset_value": {"default_unit": "currency", "aggregation": "last"},
    "net_asset_value_per_share": {"default_unit": "currency/share", "aggregation": "last"},
    "funds_from_operations": {"default_unit": "currency", "aggregation": "sum"},
    "adjusted_funds_from_operations": {"default_unit": "currency", "aggregation": "sum"},
    "same_store_sales_growth": {"default_unit": "ratio", "aggregation": "none"},
    "stores_count": {"default_unit": "count", "aggregation": "last"},
    "average_transaction_value": {"default_unit": "currency", "aggregation": "weighted_average"},
    "conversion_rate": {"default_unit": "ratio", "aggregation": "average"},
    "ecommerce_revenue_share": {"default_unit": "ratio", "aggregation": "average"},
    "licensed_beds": {"default_unit": "count", "aggregation": "last"},
    "occupied_beds": {"default_unit": "count", "aggregation": "average"},
    "bed_occupancy_rate": {"default_unit": "ratio", "aggregation": "average"},
    "outpatient_visits": {"default_unit": "count", "aggregation": "sum"},
    "inpatient_admissions": {"default_unit": "count", "aggregation": "sum"},
    "revenue_per_available_bed": {"default_unit": "currency/bed", "aggregation": "weighted_average"},
    "passengers_carried": {"default_unit": "count", "aggregation": "sum"},
    "cargo_volume": {"default_unit": "tonnes", "aggregation": "sum"},
    "available_seat_kilometers": {"default_unit": "seat_km", "aggregation": "sum"},
    "revenue_passenger_kilometers": {"default_unit": "passenger_km", "aggregation": "sum"},
    "passenger_load_factor": {"default_unit": "ratio", "aggregation": "average"},
    "fleet_size": {"default_unit": "count", "aggregation": "last"},
    "order_intake": {"default_unit": "currency", "aggregation": "sum"},
    "project_backlog": {"default_unit": "currency", "aggregation": "last"},
    "book_to_bill_industrial": {"default_unit": "ratio", "aggregation": "none"},
    "project_completion_rate": {"default_unit": "ratio", "aggregation": "average"},
    "active_projects_count": {"default_unit": "count", "aggregation": "last"},
    "annual_recurring_revenue": {"default_unit": "currency", "aggregation": "last"},
    "monthly_recurring_revenue": {"default_unit": "currency", "aggregation": "last"},
    "active_users": {"default_unit": "count", "aggregation": "last"},
    "paid_users": {"default_unit": "count", "aggregation": "last"},
    "customer_acquisition_cost": {"default_unit": "currency/customer", "aggregation": "weighted_average"},
    "customer_lifetime_value": {"default_unit": "currency/customer", "aggregation": "weighted_average"},
    "net_revenue_retention": {"default_unit": "ratio", "aggregation": "average"},
    "software_gross_retention": {"default_unit": "ratio", "aggregation": "average"},
    "crop_production": {"default_unit": "tonnes", "aggregation": "sum"},
    "livestock_volume": {"default_unit": "tonnes", "aggregation": "sum"},
    "yield_per_hectare": {"default_unit": "tonnes/hectare", "aggregation": "weighted_average"},
    "cultivated_area": {"default_unit": "hectares", "aggregation": "last"},
    "assets_under_management": {"default_unit": "currency", "aggregation": "last"},
    "net_new_money": {"default_unit": "currency", "aggregation": "sum"},
    "management_fee_rate": {"default_unit": "ratio", "aggregation": "weighted_average"},
    "water_intensity": {"default_unit": "m3/tonne", "aggregation": "weighted_average"},
    "material_loss_intensity": {"default_unit": "tonne/tonne", "aggregation": "weighted_average"},
    "flaring_reduction_since_2010": {"default_unit": "ratio", "aggregation": "none"},
    "co2_utilization": {"default_unit": "million_tonnes", "aggregation": "sum"},
    "nox_emissions": {"default_unit": "tonnes", "aggregation": "sum"},
    "sox_emissions_chemicals": {"default_unit": "tonnes", "aggregation": "sum"},
    "hazardous_waste_generated": {"default_unit": "tonnes", "aggregation": "sum"},
    "hazardous_waste_recovered": {"default_unit": "tonnes", "aggregation": "sum"},
    "hazardous_waste_disposed": {"default_unit": "tonnes", "aggregation": "sum"},
    "nonhazardous_waste_generated": {"default_unit": "tonnes", "aggregation": "sum"},
    "nonhazardous_waste_recovered": {"default_unit": "tonnes", "aggregation": "sum"},
    "nonhazardous_waste_disposed": {"default_unit": "tonnes", "aggregation": "sum"},
    "scope_1_2_emissions": {"default_unit": "million_tCO2e", "aggregation": "sum"},
    "fatalities_count": {"default_unit": "count", "aggregation": "sum"},
    "fatalities_rate": {"default_unit": "incidents/200k_hours", "aggregation": "average"},
    "tier_1_process_safety_events": {"default_unit": "count", "aggregation": "sum"},
    "tier_1_process_safety_events_rate": {"default_unit": "incidents/200k_hours", "aggregation": "average"},
    "patent_portfolio_count": {"default_unit": "count", "aggregation": "last"},
    "new_products_introduced": {"default_unit": "count", "aggregation": "sum"},
    "women_workforce_share": {"default_unit": "ratio", "aggregation": "average"},
    "active_suppliers_count": {"default_unit": "count", "aggregation": "last"},
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
    "customer_industry": "Customer end-market or industry", "plant": "Production plant or complex",
    "feedstock": "Feedstock family", "sales_channel": "Sales or distribution channel",
    "loan_stage": "IFRS 9 credit-risk stage", "loan_product": "Loan or financing product",
    "deposit_type": "Deposit account class", "insurance_line": "Insurance line of business",
    "claim_type": "Insurance claim class", "reinsurance_type": "Reinsurance arrangement class",
    "network_type": "Telecommunications network generation or access type",
    "customer_type": "Residential, commercial, government, or enterprise customer class",
    "generation_source": "Electricity generation source", "commodity": "Mineral or commodity",
    "mine": "Mine, concession, or extraction site", "property_type": "Real-estate property class",
    "store_format": "Retail store or channel format", "care_type": "Healthcare service or care type",
    "transport_mode": "Air, sea, road, rail, or logistics mode", "route": "Transport route or corridor",
    "project_type": "Industrial or construction project type", "platform": "Technology platform or product",
    "crop_type": "Agricultural crop or livestock class", "fund_type": "Investment fund or mandate type",
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
    "dividends": (),
    "chemical_operations": ("segment", "geography", "product", "plant", "feedstock", "customer_industry", "sales_channel", "measure", "basis"),
    "banking": ("segment", "geography", "loan_stage", "loan_product", "deposit_type", "maturity_band", "measure", "basis"),
    "insurance": ("segment", "geography", "insurance_line", "claim_type", "reinsurance_type", "measure", "basis"),
    "telecommunications": ("segment", "geography", "product", "network_type", "customer_type", "measure", "basis"),
    "utilities": ("segment", "geography", "generation_source", "customer_type", "measure", "basis"),
    "mining": ("segment", "geography", "commodity", "mine", "measure", "basis"),
    "real_estate": ("segment", "geography", "property_type", "measure", "basis"),
    "retail": ("segment", "geography", "product", "store_format", "sales_channel", "measure", "basis"),
    "healthcare": ("segment", "geography", "care_type", "measure", "basis"),
    "transportation_logistics": ("segment", "geography", "transport_mode", "route", "measure", "basis"),
    "industrial_construction": ("segment", "geography", "project_type", "customer_industry", "measure", "basis"),
    "technology": ("segment", "geography", "platform", "customer_type", "sales_channel", "measure", "basis"),
    "food_agriculture": ("segment", "geography", "product", "crop_type", "measure", "basis"),
    "asset_management": ("segment", "geography", "fund_type", "asset_class", "measure", "basis"),
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
        "subsidiaries_count investor_contact_email business_model "
        "executive_management_team board_of_directors index_memberships"
    )),
    ("income_statement", "data_points", "income_statement", "flow", "currency", "sum", "all", "*", _keys(
        "revenue other_income_related_to_sales revenue_and_other_income_related_to_sales cost_of_revenue gross_profit "
        "selling_general_administrative_expense general_and_administrative_expense selling_and_distribution_expense "
        "research_and_development_expense exploration_expense depreciation_expense amortization_expense depreciation_amortization "
        "royalties_and_other_taxes purchases producing_manufacturing_expense operating_costs operating_expenses operating_income "
        "interest_income interest_expense finance_income finance_and_other_income finance_costs "
        "investment_income share_of_profit_associates impairment_charges gain_loss_asset_sales other_income other_expense "
        "other_nonoperating_income other_nonoperating_expense revenue_ex_other_income other_operating_revenue "
        "income_before_income_taxes_and_zakat zakat_expense income_tax_expense income_taxes_and_zakat net_income "
        "net_income_parent net_income_noncontrolling continuing_operations_income discontinued_operations_income "
        "comprehensive_income adjusted_ebitda ebitda ebit adjusted_net_income basic_eps eps_diluted weighted_average_shares_basic "
        "weighted_average_shares_diluted minority_interest_income"
    )),
    ("balance_sheet", "data_points", "balance_sheet", "instant", "currency", "last", "all", "*", _keys(
        "cash cash_equivalents cash_restricted short_term_investments marketable_securities accounts_receivable allowance_doubtful_accounts "
        "other_receivables inventory prepayments due_from_government due_from_related_parties current_tax_assets other_current_assets assets_held_for_sale "
        "current_assets property_plant_equipment gross_property_plant_equipment accumulated_depreciation right_of_use_assets "
        "land buildings machinery_equipment oil_gas_properties construction_in_progress goodwill intangible_assets investments_associates "
        "investments_joint_ventures long_term_investments long_term_securities deferred_tax_assets employee_benefits_asset other_noncurrent_assets "
        "noncurrent_assets total_assets accounts_payable accrued_expenses employee_benefits_current current_debt lease_liabilities_current "
        "current_portion_long_term_debt tax_payable zakat_payable royalties_payable due_to_related_parties trade_payables_other_liabilities "
        "liabilities_held_for_sale other_current_liabilities current_liabilities long_term_debt bonds_sukuk bank_loans lease_liabilities_noncurrent provisions "
        "employee_benefits_noncurrent deferred_tax_liabilities other_noncurrent_liabilities noncurrent_liabilities total_liabilities "
        "share_capital additional_paid_in_capital treasury_shares retained_earnings statutory_reserve other_reserves "
        "accumulated_other_comprehensive_income equity_parent noncontrolling_interests total_equity total_liabilities_equity "
        "net_debt working_capital invested_capital shares_outstanding tangible_book_value"
    )),
    ("cash_flow", "data_points", "cash_flow", "flow", "currency", "sum", "all", "*", _keys(
        "net_income_cash_flow depreciation_amortization_cash_flow impairment_cash_flow share_based_compensation deferred_tax "
        "gain_loss_investing working_capital_change accounts_receivable_change inventory_change accounts_payable_change "
        "other_operating_changes exploration_evaluation_written_off investment_fair_value_change due_from_government_change "
        "royalties_payable_change operating_cash_flow capex ppe_purchases intangible_asset_purchases acquisitions proceeds_asset_sales "
        "joint_venture_investments purchases_investments securities_purchases securities_sales proceeds_investments short_term_investments_net "
        "loans_to_affiliates investing_cash_flow debt_issued debt_repaid lease_payments shares_issued capital_increase_proceeds "
        "shares_repurchased dividends_paid dividends_noncontrolling base_dividends_paid performance_linked_dividends_paid "
        "treasury_share_purchases proceeds_noncontrolling_sale short_term_borrowings_net distributions_joint_ventures_associates "
        "dividends_from_investments other_financing_cash_flow financing_cash_flow "
        "foreign_exchange_effect cash_change cash_beginning cash_end interest_paid interest_received taxes_paid zakat_paid "
        "free_cash_flow owner_earnings discretionary_cash_flow"
    )),
    ("profitability", "data_points", "ratios", "derived", "ratio", "none", "all", "*", _keys(
        "gross_margin operating_margin ebit_margin ebitda_margin pretax_margin effective_tax_rate net_margin fcf_margin cfo_margin return_on_assets "
        "return_on_equity return_on_invested_capital roace return_on_capital_employed return_on_capital cash_return_on_assets "
        "cash_return_on_equity nopat economic_profit_proxy incremental_roic cash_conversion_of_earnings fcf_conversion margin_expansion"
    )),
    ("liquidity_solvency", "data_points", "ratios", "derived", "ratio", "none", "all", "*", _keys(
        "current_ratio quick_ratio cash_ratio debt_to_equity debt_to_assets liabilities_to_equity liabilities_to_assets "
        "net_debt_to_equity net_debt_to_ebitda debt_to_ebitda interest_coverage fixed_charge_coverage gearing equity_ratio "
        "cfo_to_debt fcf_to_debt long_term_debt_to_capital total_debt_to_capital debt_service_coverage_proxy cfo_interest_coverage"
    )),
    ("efficiency", "data_points", "ratios", "derived", "ratio", "none", "all", "*", _keys(
        "asset_turnover inventory_turnover receivables_turnover payables_turnover days_sales_outstanding days_inventory "
        "days_payables cash_conversion_cycle fixed_asset_turnover working_capital_turnover capex_to_revenue capex_to_cfo "
        "capex_to_depreciation_amortization receivables_to_revenue inventory_to_revenue inventory_to_assets ppe_to_assets"
    )),
    ("growth", "data_points", "growth", "derived", "ratio", "none", "all", "*", _keys(
        "revenue_growth gross_profit_growth operating_income_growth ebitda_growth net_income_growth eps_growth asset_growth "
        "equity_growth debt_growth operating_cash_flow_growth free_cash_flow_growth dividend_growth revenue_cagr_3y "
        "revenue_cagr_5y net_income_cagr_3y net_income_cagr_5y eps_cagr_3y eps_cagr_5y "
        "revenue_qoq gross_profit_qoq operating_income_qoq ebitda_qoq net_income_qoq eps_qoq operating_cash_flow_qoq free_cash_flow_qoq "
        "book_value_growth revenue_per_share_growth free_cash_flow_per_share_growth revenue_ttm_growth ebitda_ttm_growth "
        "net_income_ttm_growth eps_ttm_growth operating_cash_flow_ttm_growth free_cash_flow_ttm_growth"
    )),
    ("per_share", "data_points", "per_share", "derived", "currency/share", "none", "all", "*", _keys(
        "revenue_per_share ebitda_per_share ebit_per_share operating_cash_flow_per_share free_cash_flow_per_share dividends_per_share "
        "book_value_per_share tangible_book_value_per_share cash_per_share debt_per_share retained_earnings_per_share capex_per_share "
        "earnings_per_share_normalized"
    )),
    ("valuation", "data_points", "valuation", "derived", "ratio", "none", "all", "*", _keys(
        "market_cap enterprise_value price_to_earnings price_to_sales price_to_book price_to_tangible_book price_to_cash_flow "
        "price_to_free_cash_flow enterprise_value_to_revenue enterprise_value_to_ebitda enterprise_value_to_ebit "
        "enterprise_value_to_fcf earnings_yield fcf_yield cfo_yield dividend_yield forward_price_to_earnings peg_ratio "
        "enterprise_value_to_invested_capital market_cap_to_net_income market_cap_to_equity historical_pe_percentile "
        "historical_pb_percentile graham_number shareholder_yield"
    )),
    ("market_data", "market_prices", "market", "event", "decimal", "none", "all", "*", _keys(
        "price_open price_high price_low price_close price_adjusted_close trading_volume trading_turnover vwap "
        "previous_close free_float_market_cap free_float_shares beta_1y beta_5y volatility_30d average_volume_30d "
        "fifty_two_week_high fifty_two_week_low percent_from_52w_high percent_from_52w_low market_return_1m market_return_3m "
        "market_return_6m market_return_ytd market_return_1y market_return_3y market_return_5y "
        "short_interest_shares short_interest_percent_float short_interest_days_to_cover"
    )),
    ("ownership", "ownership_positions", "ownership", "event", "decimal", "none", "all", "*", _keys(
        "holder_name holder_type shares_held ownership_percentage government_ownership institutional_ownership insider_ownership "
        "foreign_ownership retail_ownership strategic_ownership free_float major_holder_change top_5_shareholder_concentration "
        "top_10_shareholder_concentration retail_shareholders_count institutional_shareholders_count foreign_investor_limit "
        "ownership_concentration"
    )),
    ("corporate_actions", "corporate_actions", "corporate_actions", "event", "json", "none", "all", "*", _keys(
        "cash_dividend bonus_shares stock_split reverse_split rights_issue capital_increase capital_reduction share_buyback "
        "treasury_share_sale merger acquisition spin_off delisting suspension symbol_change tender_offer "
        "dividend_announcement dividend_eligibility dividend_ex_date dividend_payment rights_offering_date"
    )),
    ("disclosures", "disclosures", "disclosures", "event", "text", "none", "all", "*", _keys(
        "financial_results_announcement earnings_release annual_report interim_report board_change management_change contract_award "
        "litigation regulatory_action related_party_transaction guidance risk_factor strategy_update material_event "
        "announcement_id announcement_date announcement_category announcement_title_ar announcement_title_en announcement_body "
        "related_financial_period materiality_tag dividend_flag earnings_flag contract_flag merger_acquisition_flag governance_flag announcement_source_url "
        "next_earnings_date next_agm_date"
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
    ("dividends", "data_points", "dividends", "mixed", "currency", "none", "all", "*", _keys(
        "fcf_payout_ratio dividend_cagr_3y dividend_cagr_5y trailing_twelve_month_dividend forward_dividend_run_rate "
        "special_dividend years_consecutive_dividend_payments dividend_payment_frequency dividend_yield_ttm payout_ratio_ttm "
        "fcf_payout_ratio_ttm dividend_coverage_ratio fcf_dividend_coverage_ratio ordinary_dividend total_dividend_declared "
        "total_dividend_paid_ttm dividend_per_share_ttm forward_dividend_per_share dividend_installments_count dividend_stability_score"
    )),
    ("investor_analytics", "data_points", "analytics", "derived", "ratio", "none", "all", "*", _keys(
        "return_on_tangible_assets return_on_tangible_equity income_quality payout_ratio capex_to_depreciation "
        "selling_general_administrative_to_revenue research_development_to_revenue share_based_compensation_to_revenue "
        "net_current_asset_value graham_net_net "
        "revenue_cagr_10y net_income_cagr_10y eps_cagr_10y dividend_cagr_10y operating_cash_flow_cagr_10y "
        "free_cash_flow_cagr_10y total_return_1y total_return_3y total_return_5y total_return_10y "
        "simple_moving_average_20d simple_moving_average_50d simple_moving_average_200d price_to_sma_20d "
        "price_to_sma_50d price_to_sma_200d "
        "accrual_ratio piotroski_f_score altman_z_score beneish_m_score"
    )),
    ("consensus", "consensus_estimates", "consensus", "forward", "decimal", "none", "all", "*", _keys(
        "revenue_estimate ebitda_estimate ebit_estimate net_income_estimate "
        "selling_general_administrative_expense_estimate eps_estimate"
    )),
    ("segments", "data_points", "segments", "mixed", "currency", "none", "all", "*", _keys(
        "segment_revenue segment_ebit segment_ebitda segment_assets segment_liabilities segment_capex "
        "segment_investments_associates segment_depreciation_amortization segment_impairment"
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
    ("segments", "data_points", "segments", "flow", "currency", "sum", "industry", "Diversified Chemicals", _keys(
        "petrochemicals_revenue agri_nutrients_revenue specialties_revenue metals_revenue petrochemicals_ebitda "
        "agri_nutrients_ebitda specialties_ebitda metals_ebitda petrochemicals_capex agri_nutrients_capex "
        "specialties_capex metals_capex domestic_revenue_chemicals international_revenue_chemicals"
    )),
    ("chemical_operations", "data_points", "operational", "flow", "decimal", "average", "industry", "Diversified Chemicals", _keys(
        "production_volume sales_volume production_capacity capacity_utilization average_selling_price plant_reliability "
        "feedstock_cost_per_tonne ethylene_production polyethylene_production polypropylene_production methanol_production "
        "fertilizer_production steel_production petrochemicals_sales_volume agri_nutrients_sales_volume specialties_sales_volume "
        "metals_sales_volume domestic_sales_volume export_sales_volume energy_consumption_intensity scope_1_emissions_chemicals "
        "scope_2_emissions_chemicals water_withdrawal_chemicals water_consumption_chemicals greenhouse_gas_intensity "
        "lost_time_injury_rate total_recordable_injury_rate circular_feedstock_volume recycled_product_sales "
        "water_intensity material_loss_intensity flaring_reduction_since_2010 co2_utilization nox_emissions "
        "sox_emissions_chemicals hazardous_waste_generated hazardous_waste_recovered hazardous_waste_disposed "
        "nonhazardous_waste_generated nonhazardous_waste_recovered nonhazardous_waste_disposed scope_1_2_emissions "
        "fatalities_count fatalities_rate tier_1_process_safety_events tier_1_process_safety_events_rate "
        "patent_portfolio_count new_products_introduced women_workforce_share active_suppliers_count"
    )),
    ("banking", "data_points", "banking_balance_sheet", "instant", "currency", "last", "industry", "Banks", _keys(
        "gross_loans net_loans customer_deposits demand_deposits savings_deposits time_deposits bank_investments "
        "due_from_banks due_to_banks nonperforming_loans stage_1_loans stage_2_loans stage_3_loans credit_loss_allowance "
        "risk_weighted_assets regulatory_capital"
    )),
    ("banking", "data_points", "banking_income", "flow", "currency", "sum", "industry", "Banks", _keys(
        "financing_income financing_expense net_financing_income fee_income fee_expense net_fee_income exchange_income "
        "trading_income dividend_income total_operating_income "
        "salaries_and_employee_expenses provision_expense operating_expense_banking total_operating_expenses"
    )),
    ("banking", "data_points", "banking_balance_sheet", "instant", "currency", "last", "industry", "Banks", _keys(
        "cash_and_balances_with_central_bank debt_securities_issued"
    )),
    ("banking", "data_points", "banking_ratios", "mixed", "ratio", "none", "industry", "Banks", _keys(
        "net_interest_margin cost_of_funds nonperforming_loans_ratio nonperforming_loans_coverage cet1_ratio tier1_capital_ratio "
        "capital_adequacy_ratio loans_to_deposits_ratio casa_ratio cost_to_income_ratio cost_of_risk bank_health_score"
    )),
    ("banking", "data_points", "banking_operations", "mixed", "decimal", "none", "industry", "Banks", _keys(
        "branches_count atms_count pos_terminals_count remittance_centres_count digital_active_users total_customers "
        "digital_to_manual_transaction_ratio net_promoter_score saudization_rate average_monthly_transactions "
        "personal_finance_market_share mortgage_market_share auto_finance_market_share credit_card_market_share"
    )),
    ("insurance", "data_points", "insurance_income", "flow", "currency", "sum", "industry", "Insurance", _keys(
        "gross_written_premium insurance_revenue insurance_service_expense claims_incurred insurance_service_result "
        "reinsurance_result insurance_investment_income underwriting_result acquisition_costs reinsurance_premiums "
        "reinsurance_recoveries"
    )),
    ("insurance", "data_points", "insurance_balance_sheet", "instant", "currency", "last", "industry", "Insurance", _keys(
        "insurance_contract_assets insurance_contract_liabilities reinsurance_contract_assets reinsurance_contract_liabilities "
        "technical_reserves unearned_premium_reserve outstanding_claims_reserve solvency_capital"
    )),
    ("insurance", "data_points", "insurance_ratios", "mixed", "ratio", "none", "industry", "Insurance", _keys(
        "loss_ratio combined_ratio expense_ratio retention_ratio solvency_ratio claims_frequency claims_severity"
    )),
    ("telecommunications", "data_points", "telecom_operations", "mixed", "decimal", "none", "industry", "Telecommunications", _keys(
        "subscriber_count mobile_subscribers prepaid_subscribers postpaid_subscribers broadband_subscribers fiber_subscribers "
        "enterprise_customers arpu mobile_arpu broadband_arpu churn_rate data_traffic voice_traffic network_coverage "
        "five_g_coverage fiber_home_passes towers_count spectrum_holdings network_sites data_centers_count "
        "digital_services_revenue roaming_revenue interconnection_revenue handset_sales network_capex"
    )),
    ("utilities", "data_points", "utilities_operations", "mixed", "decimal", "none", "industry", "Utilities", _keys(
        "electricity_generated electricity_sold installed_generation_capacity renewable_capacity thermal_capacity "
        "capacity_factor network_losses transmission_length distribution_length customer_connections peak_demand "
        "average_tariff fuel_cost_per_mwh outage_duration outage_frequency water_produced water_distributed desalination_capacity "
        "water_network_losses wastewater_treated power_purchase_commitments regulated_asset_base emissions_per_mwh"
    )),
    ("mining", "data_points", "mining_operations", "mixed", "decimal", "none", "industry", "Mining", _keys(
        "ore_production processed_ore saleable_production recoverable_reserves mineral_resources ore_grade recovery_rate "
        "strip_ratio cash_cost_per_tonne all_in_sustaining_cost realized_commodity_price mine_life years_reserve_life "
        "exploration_drilling_meters waste_mined concentrator_throughput smelter_output refinery_output mining_capex "
        "sustaining_capex growth_capex energy_use_mining water_use_mining tailings_generated safety_incident_rate"
    )),
    ("real_estate", "data_points", "real_estate_operations", "mixed", "decimal", "none", "industry", "Real Estate & REITs", _keys(
        "gross_leasable_area leased_area occupancy_rate weighted_average_lease_expiry rental_income service_charge_income "
        "property_operating_expense net_property_income net_asset_value net_asset_value_per_share investment_property_value "
        "development_property_value funds_from_operations adjusted_funds_from_operations ffo_per_share affo_per_share "
        "same_property_noi_growth rent_per_sqm tenant_retention_rate rent_collection_rate tenants_count properties_count "
        "development_pipeline_value committed_development_cost loan_to_value_ratio interest_coverage_reit"
    )),
    ("retail", "data_points", "retail_operations", "mixed", "decimal", "none", "industry", "Retail", _keys(
        "same_store_sales_growth like_for_like_sales_growth stores_count net_store_openings selling_area footfall "
        "average_transaction_value transactions_count units_sold conversion_rate basket_size sales_per_sqm "
        "inventory_shrinkage ecommerce_revenue ecommerce_revenue_share online_orders loyalty_members private_label_share "
        "markdown_rate full_price_sell_through franchise_stores owned_stores retail_gross_margin"
    )),
    ("healthcare", "data_points", "healthcare_operations", "mixed", "decimal", "none", "industry", "Health Care", _keys(
        "licensed_beds operational_beds occupied_beds bed_occupancy_rate average_length_of_stay outpatient_visits "
        "inpatient_admissions emergency_visits surgeries_count physicians_count nurses_count clinics_count hospitals_count "
        "revenue_per_available_bed revenue_per_patient patient_days payer_government_share payer_insurance_share "
        "payer_cash_share pharmacy_revenue laboratory_tests claims_rejection_rate medical_supply_cost_ratio"
    )),
    ("transportation_logistics", "data_points", "transport_operations", "mixed", "decimal", "none", "industry", "Transportation & Logistics", _keys(
        "passengers_carried cargo_volume shipments_count available_seat_kilometers revenue_passenger_kilometers "
        "passenger_load_factor cargo_load_factor yield_per_passenger_km revenue_per_tonne_km fleet_size active_fleet "
        "fleet_utilization on_time_performance routes_count destinations_count vessel_capacity port_throughput "
        "warehouse_capacity last_mile_deliveries fuel_cost_per_unit distance_traveled logistics_backlog"
    )),
    ("industrial_construction", "data_points", "industrial_operations", "mixed", "decimal", "none", "industry", "Industrials & Construction", _keys(
        "order_intake project_backlog awarded_contracts_value book_to_bill_industrial project_revenue recognized_backlog "
        "remaining_backlog project_completion_rate active_projects_count completed_projects_count bid_pipeline_value "
        "bid_success_rate manufacturing_output manufacturing_capacity industrial_capacity_utilization machine_hours "
        "labor_hours rework_rate warranty_claim_rate raw_material_cost_ratio project_gross_margin"
    )),
    ("technology", "data_points", "technology_operations", "mixed", "decimal", "none", "industry", "Technology", _keys(
        "annual_recurring_revenue monthly_recurring_revenue recurring_revenue_share subscription_revenue active_users "
        "monthly_active_users daily_active_users paid_users enterprise_accounts bookings billings remaining_performance_obligation_tech "
        "customer_acquisition_cost customer_lifetime_value net_revenue_retention software_gross_retention logo_churn_rate "
        "revenue_churn_rate cloud_revenue cloud_consumption transactions_processed take_rate research_headcount"
    )),
    ("food_agriculture", "data_points", "food_agriculture_operations", "mixed", "decimal", "none", "industry", "Food & Agriculture", _keys(
        "crop_production livestock_volume processed_food_volume sales_volume_food yield_per_hectare cultivated_area "
        "harvested_area herd_size feed_cost_per_unit raw_milk_volume average_selling_price_food production_capacity_food "
        "capacity_utilization_food commodity_input_cost cold_storage_capacity distribution_points export_share_food "
        "water_use_agriculture product_waste_rate branded_products_share"
    )),
    ("asset_management", "data_points", "asset_management_operations", "mixed", "decimal", "none", "industry", "Asset Management", _keys(
        "assets_under_management assets_under_administration net_new_money gross_inflows gross_outflows management_fees "
        "performance_fees management_fee_rate funds_count mandates_count institutional_aum retail_aum alternatives_aum "
        "equity_aum fixed_income_aum money_market_aum average_aum aum_growth investment_performance_vs_benchmark "
        "client_retention_rate"
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
                "pack_key": ({
                    "Integrated Oil & Gas": "oil_gas_v2",
                    "Diversified Chemicals": "chemicals_v1",
                    "Banks": "banking_v1",
                    "Insurance": "insurance_v1",
                    "Telecommunications": "telecommunications_v1",
                    "Utilities": "utilities_v1",
                    "Mining": "mining_v1",
                    "Real Estate & REITs": "real_estate_v1",
                    "Retail": "retail_v1",
                    "Health Care": "healthcare_v1",
                    "Transportation & Logistics": "transportation_logistics_v1",
                    "Industrials & Construction": "industrial_construction_v1",
                    "Technology": "technology_v1",
                    "Food & Agriculture": "food_agriculture_v1",
                    "Asset Management": "asset_management_v1",
                }.get(scope_value, "company_core_v5") if scope_type == "industry" else
                    {"dividends": "dividends_v1", "disclosures": "announcements_v1"}.get(category, "company_core_v5")),
            }
            item.update(FIELD_OVERRIDES.get(key, {}))
            item["allowed_period_kinds"] = PERIOD_KINDS_BY_BEHAVIOR[item["period_behavior"]]
            item["allowed_dimensions"] = DIMENSIONS_BY_CATEGORY[category]
            item["unit_family"] = _unit_family(item["default_unit"])
            yield item


CATALOG_SIZE = sum(1 for _ in iter_catalog_fields())
