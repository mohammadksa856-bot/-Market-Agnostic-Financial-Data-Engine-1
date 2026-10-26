"""Independent classification of Aramco's missing contract keys (keys and points only, no values)."""
import json, sys
from decimal import Decimal
sys.path.insert(0, "tools"); from missing import missing

CLOSED = {  # proven this session on the isolated branch
    "ebitda_growth": ("UNPROVEN", "derivable", "AR2025 p174/p178 D&A 2024 + note 34 EBIT 2024; engine formula ebit+|D&A|"),
    "dividend_installments_count": ("UNPROVEN", "exists", "AR2025 note 37 p235: four quarterly declarations"),
    "adjusted_ebit": ("DEF", "resolved_by_existing_decision", "config/supplements/2222.json maps issuer 'Adjusted EBIT'; AR2025 p47/p48"),
}
UNPROVEN = {
    "dividend_payment_frequency": ("exists_no_ingestion_path", "AR2025 note 37: quarterly; text values have no manifest path"),
    "eps_cagr_5y": ("needs_period", "EPS 2020 on the post-2023-bonus basis is not in the engine"),
    "dividend_cagr_5y": ("needs_period", "DPS 2020 missing; DPS 2021-2022 are on the pre-2023-bonus basis"),
    "years_consecutive_dividend_payments": ("needs_period", "dividend history before 2021 not ingested; start-year policy"),
    "ebitda_qoq": ("needs_period", "no quarterly EBIT or D&A for Q1/Q2 2026"),
    "operating_income_qoq": ("needs_period", "quarterly operating income not ingested (data book not loaded)"),
    "eps_qoq": ("needs_period", "quarterly EPS not ingested"),
    "revenue_ttm_growth": ("needs_period", "discrete Q3/Q4 2025 and prior-year quarters missing"),
    "net_income_ttm_growth": ("needs_period", "same"),
    "eps_ttm_growth": ("needs_period", "same"),
    "ebitda_ttm_growth": ("needs_period", "same"),
    "free_cash_flow_ttm_growth": ("needs_period", "same"),
    "operating_cash_flow_ttm_growth": ("needs_period", "same"),
    "historical_pe_percentile": ("needs_period", "one archived price day only"),
    "historical_pb_percentile": ("needs_period", "one archived price day only"),
    "segment_assets": ("possibly_not_applicable", "note 34 reports no segment assets"),
    "segment_liabilities": ("possibly_not_applicable", "note 34 reports no segment liabilities"),
    "segment_investments_associates": ("possibly_not_applicable", "not disclosed by segment"),
    "customer_concentration": ("insufficient_evidence", "narrative only, no amount; correctly uncounted"),
    "contingencies": ("insufficient_evidence", "narrative only, no amount; correctly uncounted"),
}
DEF = {  # decision_id -> keys
    "D01_gross_profit_nature_of_expense": ["gross_profit", "cost_of_revenue", "gross_margin", "gross_profit_growth",
        "gross_profit_qoq", "days_inventory", "inventory_turnover", "days_payables", "payables_turnover",
        "cash_conversion_cycle", "beneish_m_score"],
    "D02_combined_sga": ["general_and_administrative_expense", "selling_and_distribution_expense"],
    "D03_adjusted_ebitda": ["adjusted_ebitda"],
    "D04_continuing_discontinued": ["continuing_operations_income", "discontinued_operations_income"],
    "D05_interest_vs_finance_costs": ["interest_expense"],
    "D06_cash_flow_subtotals": ["net_income_cash_flow", "operating_profit_before_working_capital_changes"],
    "D07_owner_and_discretionary_cash": ["owner_earnings", "discretionary_cash_flow"],
    "D08_pending_returns_and_wacc": ["fixed_charge_coverage", "return_on_capital", "economic_profit_proxy"],
    "D09_book_value_basis": ["book_value_growth"],
    "D10_segment_operating_income": ["upstream_operating_income", "downstream_operating_income"],
    "D11_upstream_downstream_kpis": ["refinery_utilization", "spare_capacity", "production_entitlement", "lifting_volume"],
    "D12_dividend_classes": ["ordinary_dividend", "special_dividend", "total_dividend_declared", "dividend_stability_score"],
    "D13_dividend_ttm_and_forward": ["dividend_per_share_ttm", "trailing_twelve_month_dividend", "total_dividend_paid_ttm",
        "dividend_yield_ttm", "payout_ratio_ttm", "fcf_payout_ratio_ttm", "forward_dividend_per_share", "forward_dividend_run_rate"],
    "D14_identity_and_sharia": ["cik", "sharia_status"],
    "D15_product_revenue_split": ["chemicals_revenue", "refined_products_revenue", "lng_revenue"],
    "D16_commercial_pipeline_applicability": ["average_selling_price_by_product", "book_to_bill_ratio", "committed_offtake_volume",
        "contract_renewal_profile", "contracted_sales_value", "contracted_sales_volume", "minimum_volume_commitments",
        "sales_contract_count", "sales_order_backlog", "sales_volume_by_geography", "sales_volume_by_product", "take_or_pay_commitments"],
    "D17_corporate_actions_never_occurred": ["capital_reduction", "delisting", "merger", "reverse_split", "rights_issue",
        "rights_offering_date", "spin_off", "stock_split", "suspension", "symbol_change", "tender_offer", "treasury_share_sale"],
}

_, base = missing("ready-base.json")
_, final = missing("runs/r5-adj/ready.json")
pts_base = {}
for c, g, k, p in base: pts_base[k] = pts_base.get(k, Decimal(0)) + p
pts_final = {}
for c, g, k, p in final: pts_final[k] = pts_final.get(k, Decimal(0)) + p
def_keys = {k for ks in DEF.values() for k in ks}
assert not def_keys & set(UNPROVEN) and not set(CLOSED) & set(UNPROVEN) & def_keys
for k in [*def_keys, *UNPROVEN]:
    assert k in pts_final, f"{k} not missing in final"
for k in CLOSED:
    assert k in pts_base and k not in pts_final, k
out = {"basis": {"engine": "54ef922 (defs/independent-validation, local)", "contract_keys": "717 field slots", "final_score": "65.3916"},
       "closed": [{"key": k, "set": s, "class": cl, "points": f"{pts_base[k]:.4f}", "evidence": ev} for k, (s, cl, ev) in CLOSED.items()],
       "unproven_open": [{"key": k, "class": cl, "points": f"{pts_final[k]:.4f}", "reason": r} for k, (cl, r) in UNPROVEN.items()],
       "definitions_open": [{"decision": d, "keys": ks, "points": f"{sum(pts_final[k] for k in ks):.4f}"} for d, ks in DEF.items()]}
other = sorted(set(pts_final) - def_keys - set(UNPROVEN))
out["outside_both_sets"] = {"count": len(other), "points": f"{sum(pts_final[k] for k in other):.4f}",
    "note": "source/extraction keys (Codex scope) and market/consensus/ownership/announcement feeds; not researched here", "keys": other}
summary = {"def_set": len(def_keys) + 1, "def_closed": 1, "unproven_set": len(UNPROVEN) + 2, "unproven_closed": 2,
           "def_open_points": f"{sum(pts_final[k] for k in def_keys):.4f}", "unproven_open_points": f"{sum(pts_final[k] for k in UNPROVEN):.4f}"}
out["summary"] = summary
json.dump(out, open("deliver/KEY-CLASSIFICATION.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary)); print({d["decision"]: d["points"] for d in out["definitions_open"]})
from collections import Counter; print(Counter(v[0] for v in UNPROVEN.values()), {cl: f"{sum(pts_final[k] for k,(c2,_) in UNPROVEN.items() if c2==cl):.4f}" for cl in set(v[0] for v in UNPROVEN.values())})
print("outside:", len(other), out["outside_both_sets"]["points"])
