from __future__ import annotations

from decimal import Decimal
from .models import Fact, MappedFact


class NormalizationEngine:
    """Deterministic unit, scale, sign and period normalization."""
    def normalize(self, mapped: list[MappedFact], minimum_confidence: Decimal=Decimal("0.95")) -> tuple[list[Fact],list[dict],list[int]]:
        facts=[]; errors=[]; accepted=[]
        for index,item in enumerate(mapped):
            raw=item.extracted
            if item.metric is None or item.confidence < minimum_confidence:
                errors.append({"code":"mapping_review_required","label":raw.raw_label,"metric":item.metric,"confidence":str(item.confidence)})
                continue
            value=raw.raw_value * raw.scale
            # Capex is stored as a positive investment amount; formulas apply its cash-flow sign explicitly.
            if item.metric == "capex": value=abs(value)
            facts.append(Fact(
                raw.company_id,item.metric,value,raw.raw_currency,raw.raw_unit,
                raw.period_start,raw.period_end,raw.period_kind,raw.fiscal_year,
                raw.fiscal_quarter,raw.source_key,raw.source_url,raw.filed_at,
                raw.accession,raw.form,scope=raw.scope,dimensions=raw.dimensions,
            ))
            accepted.append(index)
        return facts,errors,accepted
