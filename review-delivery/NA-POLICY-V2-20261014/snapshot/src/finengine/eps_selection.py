"""EPS candidate ordering, preserving all variants and never certifying accuracy."""
from copy import deepcopy
from datetime import datetime,timezone,date
from decimal import Decimal,InvalidOperation
import json
import re
from .normalization import per_share_contract_issues

EPS_METRICS=frozenset({'eps_diluted','basic_eps','eps_basic'})
ASSURANCE={'annual-report':3,'financial-statements':3,'interim-report':3,
           'annual-report-company-esg-market':3,
           'annual financial statements':3,'interim financial statements':3,
           'annual':3,'quarterly':3,'10-K':3,'10-Q':3,'20-F':3,'40-F':3,
           'regulatory-disclosure':2,'data-supplement':1}

def _instant(value):
    if not value:return None
    try:
        parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError,TypeError):return None

def _identity(item):
    return tuple(item.get(k) for k in ('company_id','metric','period_start','period_end','period_kind','fiscal_year','fiscal_quarter','scope','currency'))+(json.dumps(item.get('dimensions',{}),sort_keys=True,separators=(',',':')),)

def select_eps_versions(candidates, *, as_of=None):
    """Current source preference or strict local historical selection.

    Historical selection requires explicit confirmed official-known metadata;
    filing dates and filenames never substitute for it. All input editions remain.
    """
    cutoff=_instant(as_of) if as_of is not None else None
    if as_of is not None and cutoff is None:raise ValueError('as_of requires a timezone-aware instant')
    result=deepcopy(candidates)
    groups={}
    for item in result:
        if item.get('metric') not in EPS_METRICS:continue
        source=(item.get('provenance') or {}).get('source') or {}
        metadata=source.get('metadata') or {}
        reasons=per_share_contract_issues(item['metric'],item.get('unit'),item.get('currency'))
        currency=item.get('currency')
        if not currency or item.get('unit') not in {'currency/share',f'{currency}/share',f'{currency}/shares'}:
            reasons.append('eps_unit_currency_mismatch')
        kind=item.get('period_kind');quarter=item.get('fiscal_quarter')
        if kind not in {'fy','quarter','ytd'} or (kind=='fy' and quarter not in (None,0)) or (kind in {'quarter','ytd'} and quarter not in (1,2,3,4)):
            reasons.append('eps_period_contract_invalid')
        try:
            start=date.fromisoformat(item.get('period_start') or '')
            end=date.fromisoformat(item.get('period_end') or '')
            if start>end or not isinstance(item.get('fiscal_year'),int) or item['fiscal_year']<=0:
                reasons.append('eps_period_contract_invalid')
        except (ValueError,TypeError):reasons.append('eps_period_contract_invalid')
        status=item.get('quality_status')
        if status and status not in {'ok','published'}:reasons.append('existing_quality_flag')
        if item.get('quality_reasons'):reasons.append('existing_quality_reasons')
        try:
            if item.get('value') is None or not Decimal(str(item['value'])).is_finite():reasons.append('missing_or_nonfinite_value')
        except InvalidOperation:reasons.append('invalid_numeric_value')
        if not source.get('source_key') or not source.get('source_url') or not re.fullmatch(r'[0-9a-fA-F]{64}',source.get('content_hash') or ''):
            reasons.append('source_identity_or_sha256_missing')
        if item.get('source_key')!=source.get('source_key') or (item.get('source_url') is not None and item['source_url']!=source.get('source_url')):
            reasons.append('point_source_identity_mismatch')
        if item.get('is_calculated'):
            derivation=(item.get('provenance') or {}).get('derivation') or {}
            lineage=derivation.get('lineage') or {}
            if not derivation.get('calculation') or lineage.get('current_inputs_reproduced') is not True or not lineage.get('consumed_inputs'):
                reasons.append('calculated_eps_requires_reproduced_input_lineage')
        report_end=metadata.get('report_period_end') or metadata.get('document_period_end') or ''
        if report_end:
            try:
                if date.fromisoformat(report_end)<date.fromisoformat(item.get('period_end') or ''):
                    reasons.append('document_vintage_precedes_fact_period')
            except (ValueError,TypeError):reasons.append('document_vintage_invalid')
        official_known=_instant(metadata.get('official_known_at'))
        confirmed=metadata.get('official_known_at_verified') is True
        if cutoff is not None:
            if not confirmed or official_known is None:reasons.append('confirmed_official_known_at_missing')
            elif official_known>cutoff:reasons.append('disclosure_not_known_as_of')
        selection={'policy':'eps-source-unit-period-vintage/1','state':'blocked' if reasons else 'eligible',
                   'reasons':sorted(set(reasons)),'candidate_id':item.get('candidate_id'),
                   'official_known_at':metadata.get('official_known_at') if confirmed else None,
                   'document_report_period_end':report_end or None,
                   'independent_numeric_verification':'not_asserted_by_source_preference'}
        item['selection']=selection
        if reasons:continue
        rank=(ASSURANCE.get(source.get('filing_type'),0),not bool(item.get('is_calculated')),report_end,
              official_known.isoformat() if confirmed and official_known else '')
        if not rank[0]:
            selection.update(state='blocked',reasons=['source_assurance_unclassified'])
            continue
        groups.setdefault(_identity(item),[]).append((rank,item))
    for group in groups.values():
        rank=max(r for r,_ in group)
        top=[item for r,item in group if r==rank]
        values={Decimal(str(item['value'])) for item in top}
        if len(values)>1:
            for _,item in group:
                item['selection'].update(state='blocked',reasons=['conflicting_equally_ranked_eps_sources'])
            continue
        winner=min(top,key=lambda item:(str(item.get('source_key') or ''),str(item.get('candidate_id') or '')))
        for _,item in group:
            item['selection']['state']='selected' if item is winner else 'superseded_candidate'
    for item in result:
        if (item.get('selection') or {}).get('state')=='blocked':
            item['value']=None
            item['quality_status']='quarantined'
            item['quality_reasons']=sorted(set(item.get('quality_reasons',[])+item['selection']['reasons']))
    # Preserve metric/period order, but place selected variants first in each
    # semantic group. No suppressed source or quarantined trace is discarded.
    by_identity={}
    for item in result:
        if item.get('metric') in EPS_METRICS:by_identity.setdefault(_identity(item),[]).append(item)
    for items in by_identity.values():items.sort(key=lambda item:0 if item['selection']['state']=='selected' else 1)
    indexes={key:0 for key in by_identity}
    for i,item in enumerate(result):
        if item.get('metric') in EPS_METRICS:
            key=_identity(item);result[i]=by_identity[key][indexes[key]];indexes[key]+=1
    return result
