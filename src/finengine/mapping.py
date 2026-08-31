CANONICAL_TAGS = {
"Revenues":"revenue","RevenueFromContractWithCustomerExcludingAssessedTax":"revenue","SalesRevenueNet":"revenue",
"NetIncomeLoss":"net_income","ProfitLoss":"net_income","Assets":"total_assets","Liabilities":"total_liabilities",
"StockholdersEquity":"total_equity","CashAndCashEquivalentsAtCarryingValue":"cash","CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents":"cash",
"NetCashProvidedByUsedInOperatingActivities":"operating_cash_flow","PaymentsToAcquirePropertyPlantAndEquipment":"capex",
"EarningsPerShareDiluted":"eps_diluted","CommonStocksIncludingAdditionalPaidInCapital":"share_capital",
"LongTermDebtAndFinanceLeaseObligationsCurrent":"current_debt","LongTermDebtAndFinanceLeaseObligations":"long_term_debt"
}
SAUDI_LABELS = {
"revenue":"revenue","sales":"revenue","net income":"net_income","net profit":"net_income","total assets":"total_assets",
"total liabilities":"total_liabilities","total equity":"total_equity","cash and cash equivalents":"cash",
"net cash from operating activities":"operating_cash_flow","capital expenditure":"capex","diluted earnings per share":"eps_diluted",
"\u0627\u0644\u0627\u064a\u0631\u0627\u062f\u0627\u062a":"revenue","\u0635\u0627\u0641\u064a \u0627\u0644\u0631\u0628\u062d":"net_income","\u0627\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0648\u062c\u0648\u062f\u0627\u062a":"total_assets","\u0627\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0637\u0644\u0648\u0628\u0627\u062a":"total_liabilities","\u062d\u0642\u0648\u0642 \u0627\u0644\u0645\u0644\u0643\u064a\u0629":"total_equity"
}

def canonicalize(label: str, market: str) -> str | None:
    if market == "US": return CANONICAL_TAGS.get(label)
    key=" ".join(label.lower().replace("\u0625","\u0627").replace("\u0623","\u0627").split())
    return SAUDI_LABELS.get(key)
