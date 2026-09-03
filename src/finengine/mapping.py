CANONICAL_TAGS = {
"Revenues":"revenue","RevenueFromContractWithCustomerExcludingAssessedTax":"revenue","SalesRevenueNet":"revenue",
"NetIncomeLoss":"net_income","ProfitLoss":"net_income","NetIncomeLossAvailableToCommonStockholdersBasic":"net_income_parent","Assets":"total_assets","Liabilities":"total_liabilities",
"StockholdersEquity":"total_equity","CashAndCashEquivalentsAtCarryingValue":"cash","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents":"cash",
"NetCashProvidedByUsedInOperatingActivities":"operating_cash_flow","PaymentsToAcquirePropertyPlantAndEquipment":"capex",
"EarningsPerShareDiluted":"eps_diluted","CommonStocksIncludingAdditionalPaidInCapital":"share_capital",
"LongTermDebtAndFinanceLeaseObligationsCurrent":"current_debt","LongTermDebtAndFinanceLeaseObligations":"long_term_debt"
}
SAUDI_LABELS = {
"revenue":"revenue","sales":"revenue","net income":"net_income","net profit":"net_income","total assets":"total_assets",
"total liabilities":"total_liabilities","total equity":"total_equity","cash and cash equivalents":"cash",
"net cash from operating activities":"operating_cash_flow","capital expenditure":"capex","diluted earnings per share":"eps_diluted",
"net profit attributable to owners":"net_income_parent","net income attributable to owners":"net_income_parent","net income attributable to shareholders equity":"net_income_parent",
"other income related to sales":"other_income_related_to_sales","revenue and other income related to sales":"revenue_and_other_income_related_to_sales",
"operating costs":"operating_costs","operating income":"operating_income",
"income before income taxes and zakat":"income_before_income_taxes_and_zakat","income taxes and zakat":"income_taxes_and_zakat",
"adjusted net income":"adjusted_net_income","dividends paid":"dividends_paid","base dividends paid":"base_dividends_paid",
"performance-linked dividends paid":"performance_linked_dividends_paid","dividends paid per share":"dividends_per_share",
"earnings per share basic and diluted":"eps_diluted","average realized crude oil price":"average_realized_crude_oil_price",
"return on average capital employed":"roace","roace":"roace","gearing":"gearing",
"total hydrocarbon production":"total_hydrocarbon_production","total liquids production":"total_liquids_production",
"total gas production":"total_gas_production","total hydrocarbon reserves":"total_hydrocarbon_reserves",
"maximum sustainable capacity":"maximum_sustainable_capacity","net refining capacity":"net_refining_capacity",
"net chemicals production capacity":"net_chemicals_production_capacity","supply reliability":"supply_reliability",
"\u0627\u0644\u0627\u064a\u0631\u0627\u062f\u0627\u062a":"revenue","\u0635\u0627\u0641\u064a \u0627\u0644\u0631\u0628\u062d":"net_income","\u0627\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0648\u062c\u0648\u062f\u0627\u062a":"total_assets","\u0627\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0637\u0644\u0648\u0628\u0627\u062a":"total_liabilities","\u062d\u0642\u0648\u0642 \u0627\u0644\u0645\u0644\u0643\u064a\u0629":"total_equity"
}

def canonicalize(label: str, market: str) -> str | None:
    if market == "US": return CANONICAL_TAGS.get(label)
    key=" ".join(label.lower().replace("\u0625","\u0627").replace("\u0623","\u0627").split())
    return SAUDI_LABELS.get(key)

from decimal import Decimal
from .models import ExtractedFact, MappedFact

class MappingEngine:
    """Deterministic exact mapping. Fuzzy/AI suggestions must remain below the publication threshold."""
    def __init__(self, allowed_metrics: set[str] | None = None):
        self.allowed_metrics = allowed_metrics or set()

    def map(self, facts: list[ExtractedFact], market: str) -> tuple[list[MappedFact], list[dict]]:
        mapped=[]; errors=[]
        for fact in facts:
            metric=canonicalize(fact.raw_label,market)
            if metric is None and fact.raw_label in self.allowed_metrics:
                metric=fact.raw_label
            if metric:
                mapped.append(MappedFact(fact,metric,Decimal("1.0"),"exact_dictionary"))
            else:
                mapped.append(MappedFact(fact,None,Decimal("0"),"unmapped","No canonical metric"))
                errors.append({"code":"unmapped_metric","label":fact.raw_label,"confidence":"0"})
        return mapped,errors
