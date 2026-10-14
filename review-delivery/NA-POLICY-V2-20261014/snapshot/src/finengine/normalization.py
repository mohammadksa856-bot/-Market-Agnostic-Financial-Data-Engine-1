from __future__ import annotations

from decimal import Decimal
from .models import Fact, MappedFact
from .catalog import iter_catalog_fields

_PER_SHARE_METRICS = frozenset(item['field_key'] for item in iter_catalog_fields()
                              if item.get('default_unit') == 'currency/share')
_SHARE_COUNT_METRICS = frozenset({'shares_outstanding','weighted_average_shares_basic',
                                  'weighted_average_shares_diluted'})

def per_share_contract_issues(metric, unit, currency, scale=None):
    """Public eligibility guard for originals and consumed calculation inputs.

    None scale assesses a persisted normalized unit, without guessing a factor.
    Non-unit per-share source scales require review, including cents declarations.
    """
    reasons=[]
    if metric in _PER_SHARE_METRICS:
        allowed={'currency/share',f'{currency}/share',f'{currency}/shares'}
        if not currency or unit not in allowed:
            reasons.append('per_share_unit_currency_mismatch')
        if scale is not None:
            try:
                parsed=Decimal(str(scale))
                if not parsed.is_finite() or parsed!=1:
                    reasons.append('per_share_scale_requires_review')
            except (ValueError,ArithmeticError): reasons.append('per_share_scale_requires_review')
    elif metric in _SHARE_COUNT_METRICS:
        if unit not in {'share','shares'}:
            reasons.append('share_count_requires_explicit_share_unit')
        if scale is not None:
            try:
                parsed=Decimal(str(scale))
                if not parsed.is_finite() or parsed<=0:
                    reasons.append('share_count_scale_invalid')
            except (ValueError,ArithmeticError): reasons.append('share_count_scale_invalid')
    return reasons


class NormalizationEngine:
    """Deterministic unit, scale, sign and period normalization."""
    def normalize(self, mapped: list[MappedFact], minimum_confidence: Decimal=Decimal("0.95")) -> tuple[list[Fact],list[dict],list[int]]:
        facts=[]; errors=[]; accepted=[]
        for index,item in enumerate(mapped):
            raw=item.extracted
            if item.metric is None or item.confidence < minimum_confidence:
                errors.append({"code":"mapping_review_required","label":raw.raw_label,"metric":item.metric,"confidence":str(item.confidence)})
                continue
            # A statement's monetary heading does not establish a per-share or
            # share-count unit. Preserve ambiguous extraction in staging rather
            # than silently undoing its multiplier or inventing source units.
            reasons=per_share_contract_issues(item.metric,raw.raw_unit,raw.raw_currency,raw.scale)
            if item.metric in _PER_SHARE_METRICS|_SHARE_COUNT_METRICS and not raw.raw_value.is_finite():
                reasons.append('per_share_or_count_value_nonfinite')
            if reasons:
                errors.append({'code':'scale_unit_review_required','reason':reasons[0],'reasons':reasons,
                               'label':raw.raw_label,'metric':item.metric,
                               'raw_value':str(raw.raw_value),'scale':str(raw.scale),
                               'raw_unit':raw.raw_unit,'source_key':raw.source_key,
                               'page':raw.page,'table_ref':raw.table_ref})
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
