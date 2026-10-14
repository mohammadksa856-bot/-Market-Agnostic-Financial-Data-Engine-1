"""B05 R2 local, reproducible field/period measurement and method comparison.

The existing contract is never rewritten. Applicable-weight normalization is a
candidate method and cannot certify readiness before separate approval.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import re
from pathlib import Path

from .issuer_calendar import build_period_targets
from .disclosure_continuity import evaluate_continuity

POLICY_REVISION = 'field-period-coverage/2'
DEFAULT_POLICY = Path('config/factory/category_period_policies_r2.json')
DEFAULT_CONTRACT = Path('config/factory/18-category-contract.json')
ORIGINAL_CONTRACT_SHA256 = '454f14f05f5ea8dc3bc70bad828af93c9611f7c34141769d02cbfce00cd2b4cb'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def instant(value):
    if not value:
        return None
    try:
        if len(str(value)) == 10:
            value = str(value) + 'T23:59:59.999999+00:00'
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def known(record, cutoff):
    available = instant(record.get('known_at'))
    filed = instant(record.get('filed_at') or record.get('known_at'))
    return available is not None and filed is not None and max(available, filed) <= cutoff


def select_versions(facts, cutoff):
    selected = {}
    for fact in facts:
        if not known(fact, cutoff):
            continue
        # Production identity omits period_start: corrected starts replace old editions.
        key = tuple(fact.get(k) for k in ('company_id','metric_key','period_end','period_kind',
                    'fiscal_year','fiscal_quarter','scope','currency','unit')) + (canonical(fact.get('dimensions', {})),)
        rank = (int(fact.get('version', 1)), fact['known_at'], str(fact.get('id', '')))
        if key not in selected or rank > selected[key][0]:
            selected[key] = rank, fact
    return [selected[key][1] for key in sorted(selected, key=repr)]


def _exception(evidence, category, cutoff, company_id):
    for item in evidence:
        if item.get('category_key') != category:
            continue
        if (item.get('company_id') != company_id or item.get('reason_code') != 'not_applicable' or item.get('reviewed') is not True
                or not item.get('rule_reference') or not item.get('source_url')
                or not re.fullmatch(r'[0-9a-fA-F]{64}', str(item.get('source_sha256', '')))
                or not known(item, cutoff)):
            continue
        expires = instant(item.get('expires_at'))
        if item.get('expires_at') and (expires is None or expires < cutoff):
            continue
        return deepcopy(item)
    return None


def _fields(snapshot, definition, rule):
    company = snapshot['company']
    groups = rule['field_groups']
    # Sector activation is an explicit versioned input, not inferred from missing facts.
    if rule['category_key'] in ('operational_kpis','sector_specific_fields'):
        groups = snapshot.get('sector_activations', {}).get(rule['category_key'], groups)
    result = []
    for field in snapshot['catalog']:
        scope, value = field.get('scope_type', 'all'), field.get('scope_value', '*')
        applicable = scope == 'all' or value == company.get({'company':'company_id',
                    'market':'market','sector':'sector','industry':'industry'}.get(scope, ''))
        if applicable and field.get('enabled', True) and field.get('reviewed', True) and field['category'] in groups:
            result.append(field)
    return sorted(result, key=lambda f:f['field_key'])


def _targets(fields, rule, periods, cutoff):
    targets = {}
    mode = rule['target_mode']
    if mode == 'financial_history':
        windows = [*periods['annual'], *periods['analytical_quarters']]
        # Nomu actual semiannual periods are measured separately; original12Q gate remains.
        windows += [p for p in periods['interim'] if p['period_kind'] == 'H1']
    elif mode in ('annual_history','derived_history'):
        windows = periods['annual']
    elif mode == 'kpi_quarters':
        windows = periods['analytical_quarters'][:4]
    elif mode == 'latest_statement':
        windows = periods['annual'][:1]
    else:
        windows = [None]
    for field in fields:
        for period in windows:
            storage = field['storage_domain']
            if period is None or storage != 'data_points':
                target = {'field_key':field['field_key'],'category_key':rule['category_key'],
                          'storage_domain':storage,'selector':mode}
            else:
                allowed = field.get('allowed_period_kinds')
                if not allowed:
                    target = {'field_key':field['field_key'],'category_key':rule['category_key'],
                              'storage_domain':storage,'selector':'period_contract_missing'}
                else:
                    kind = 'fy' if period['period_kind'] == 'FY' else 'quarter' if period['period_kind'] == 'Q' else 'ytd'
                    if 'instant' in allowed and kind not in allowed:
                        kind = 'instant'
                    # An unsupported required cell remains in the denominator.
                    target = {'field_key':field['field_key'],'category_key':rule['category_key'],
                        'storage_domain':storage,'selector':'exact_period',
                        'period_start':None if kind == 'instant' else period['period_start'],
                        'period_end':period['period_end'],'period_kind':kind,
                        'fiscal_year':period['fiscal_year'],
                        'fiscal_quarter':0 if kind == 'instant' else period.get('quarter') or 0,
                        'scope':field.get('target_scope','consolidated'),
                        'dimensions':field.get('target_dimensions',{})}
            key = canonical(target)
            targets[key] = target
    return [targets[key] for key in sorted(targets)]


def _match(target, facts, records, cutoff, rule):
    if target['storage_domain'] == 'data_points':
        candidates = [f for f in facts if f['metric_key'] == target['field_key']]
        if target['selector'] == 'exact_period':
            keys = ('period_end','period_kind','fiscal_year','scope','dimensions')
            if target['period_kind'] != 'instant':
                keys += ('fiscal_quarter',)
            candidates = [f for f in candidates if all(f.get(k,0 if k=='fiscal_quarter' else {}) == target[k] for k in keys)
                          and (f.get('period_start') or None) == target['period_start']]
        elif target['selector'] == 'period_contract_missing':
            return None, 'period_contract_missing'
        else:
            candidates = [f for f in candidates if instant(f['period_end']) and instant(f['period_end']) <= cutoff]
    else:
        candidates = [r for r in records if r.get('field_key') == target['field_key']
                      and r.get('storage_domain') == target['storage_domain'] and known(r,cutoff)
                      and (not r.get('effective_at') or (instant(r['effective_at']) and instant(r['effective_at']) <= cutoff))]
    if not candidates:
        return None, 'missing_required_cell'
    candidate = max(candidates, key=lambda f:(f.get('period_end',f.get('effective_at','')),int(f.get('version',1)),str(f.get('id',''))))
    if candidate.get('contract_valid') is not True:
        return candidate, 'value_contract_not_verified'
    if candidate.get('is_calculated') and candidate.get('lineage_complete') is not True:
        return candidate, 'derived_inputs_unverified'
    # Audited historical cells are not invalidated by age.
    if target['selector'] not in ('exact_period', 'period_contract_missing'):
        max_age = rule.get('freshness_days')
        observed = instant(candidate.get('effective_at') or candidate.get('period_end'))
        if max_age is not None and (observed is None or cutoff - observed > timedelta(days=max_age)):
            return candidate, 'current_data_stale'
    return candidate, 'present'


def evaluate_coverage(snapshot, profile, *, as_of, policy=None, contract=None):
    cutoff = instant(as_of)
    if cutoff is None:
        raise ValueError('Explicit timezone-aware as_of required')
    policy = deepcopy(policy or json.loads(DEFAULT_POLICY.read_text(encoding='utf-8')))
    contract = deepcopy(contract or json.loads(DEFAULT_CONTRACT.read_text(encoding='utf-8')))
    required = {c['category_key'] for c in contract['categories']}
    rules = {r['category_key']:r for r in policy['categories']}
    if len(rules) != 18 or set(rules) != required or len(policy['categories']) != 18:
        raise ValueError('Exact18 category policies required')
    if policy['revision'] != POLICY_REVISION or Decimal(str(contract['overall_completeness_threshold'])) != Decimal('0.95'):
        raise ValueError('Governed revision and original95% threshold required')
    if digest(contract) != ORIGINAL_CONTRACT_SHA256:
        raise ValueError('Original contract immutable: changed gates/weights/thresholds require a new approved version')
    for definition in contract['categories']:
        rule=rules[definition['category_key']]
        if (Decimal(str(rule['original_weight'])) != Decimal(str(definition['weight']))
                or Decimal(str(rule['original_threshold'])) != Decimal(str(definition['completeness_threshold']))
                or rule['original_gate_declarations'] != definition.get('hard_gates', [])):
            raise ValueError('Policy cannot override the pinned original contract')
    if profile.get('company_id') != snapshot['company']['company_id']:
        raise ValueError('Issuer calendar and snapshot company mismatch')
    periods = build_period_targets(profile, as_of)
    facts = select_versions(snapshot.get('facts',[]), cutoff)
    facts = [f for f in facts if f.get('company_id') == profile['company_id']]
    records = [r for r in snapshot.get('records', []) if r.get('company_id') == profile['company_id']]
    blockers = list(periods['blockers'])
    # The proposed normalization is intentionally non-authoritative pending approval.
    blockers.append('r2_material_measurement_method_pending_approval')
    cells, categories = [], []
    weighted, weight_total, old_na_weighted, legacy_weighted = Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    known_weight = Decimal(0)
    unknown_denominator = False
    exclusions = snapshot.get('applicability_evidence',[])
    for definition in contract['categories']:
        key = definition['category_key']; rule = rules[key]
        if rule.get('review_state') != 'reviewed' or not rule.get('target_mode') or not rule.get('field_groups'):
            blockers.append('category_policy_incomplete:'+key)
        weight = Decimal(str(definition['weight']))
        threshold = Decimal(str(definition['completeness_threshold']))
        exclusion = _exception(exclusions, key, cutoff, profile['company_id']) if rule.get('allow_not_applicable') is True else None
        fields = _fields(snapshot,definition,rule)
        expected = _targets(fields,rule,periods,cutoff)
        category_cells = []
        for target in expected:
            candidate, reason = _match(target,facts,records,cutoff,rule)
            cell = {**target,'status':reason,'fact_id':candidate.get('id') if candidate else None,
                    'version':candidate.get('version') if candidate else None,
                    'source_complete':bool(candidate and candidate.get('source_complete')),
                    'independent_state':candidate.get('independent_state','not_verified') if candidate else 'not_verified'}
            category_cells.append(cell)
        present = sum(c['status']=='present' for c in category_cells)
        numerator = present
        gates = []
        if key == 'sources_lineage_freshness':
            # Missing required values must not disappear from the provenance denominator.
            basis = {}
            for cell in cells:
                identity = {k:cell.get(k) for k in ('storage_domain','field_key','selector','period_start','period_end','period_kind','fiscal_year','fiscal_quarter','scope','dimensions')}
                basis[canonical(identity)] = cell
            category_cells = [dict(c, provenance_status='complete' if c['status']=='present' and c['source_complete'] else 'missing_value_or_source_closure') for c in basis.values()]
            numerator = sum(c['provenance_status']=='complete' for c in category_cells)
            present = numerator
            gates.append({'gate':'all_original_and_derived_source_closure','status':'passed' if basis and numerator==len(basis) else 'failed'})
        elif key in ('announcements','corporate_actions','dividends'):
            window = snapshot.get('event_window')
            if window:
                continuity = evaluate_continuity(snapshot.get('monitor_captures',[]),window['start'],window['end'],as_of)
                gates.append({'gate':'disclosure_monitor_continuity','status':'passed' if continuity['coverage_complete'] else 'not_evaluated', 'evidence':continuity})
                gates.append({'gate':'event_or_verified_absence','status':'passed' if continuity['event_state']!='unknown' else 'not_evaluated'})
            else:
                gates.append({'gate':'disclosure_monitor_continuity','status':'not_evaluated'})
        if key == 'financial_statements':
            audited_years = set()
            for period in periods['annual']:
                annual_cells = [c for c in category_cells if c.get('period_end')==period['period_end'] and c.get('period_kind') in ('fy','instant')]
                evidence = [f for f in facts if f.get('audit_state')=='audited' and f.get('contract_valid') is True and f.get('source_complete') is True
                            and f.get('period_kind')=='fy' and f.get('period_start')==period['period_start'] and f['period_end']==period['period_end']]
                # A single audited revenue value is not a complete audited set of statements.
                statement_groups = {f.get('statement_group',f['category']) for f in fields if f.get('statement_group',f['category']) in ('balance_sheet','income_statement','cash_flow')}
                audited_ids = {str(f['id']) for f in facts if f.get('audit_state')=='audited' and f.get('source_complete') is True and f.get('contract_valid') is True}
                if statement_groups=={'balance_sheet','income_statement','cash_flow'} and annual_cells and all(c['status']=='present' and c['source_complete'] and str(c['fact_id']) in audited_ids for c in annual_cells) and evidence:
                    audited_years.add(period['fiscal_year'])
            quarter_keys = {(f['fiscal_year'],f.get('fiscal_quarter')) for f in facts if f.get('period_kind')=='quarter'
                            and f.get('contract_valid') is True and (not f.get('is_calculated') or f.get('lineage_complete') is True)
                            and any(p['period_start']==f.get('period_start') and p['period_end']==f['period_end'] and p['fiscal_year']==f['fiscal_year'] and p.get('quarter')==f.get('fiscal_quarter') for p in periods['analytical_quarters'])}
            gates.extend([{'gate':'original_five_audited_years','status':'passed' if len(audited_years)>=5 else 'failed','actual':len(audited_years),'required':5},
                          {'gate':'original_twelve_quarters','status':'passed' if len(quarter_keys)>=12 else 'failed','actual':len(quarter_keys),'required':12}])
        # Preserve all original gate declarations; unspecified proof never passes.
        supplied = snapshot.get('gate_evidence',{}).get(key,{})
        for index, declaration in enumerate(definition.get('hard_gates',[])):
            evidence = supplied.get(str(index))
            gates.append({'gate':'original_contract_gate:'+str(index),'declaration':declaration,
                'status':'passed' if evidence and evidence.get('reviewed') is True and evidence.get('passed') is True
                          and known(evidence,cutoff) and evidence.get('contract_sha256')==digest(contract) else 'not_evaluated'})
        denominator = len(category_cells)
        score = Decimal(numerator)/Decimal(denominator) if denominator else None
        if exclusion:
            score = None
            status = 'not_applicable_evidenced'
            old_na_weighted += weight
        else:
            status = 'not_evaluated' if score is None else 'complete' if score>=threshold else 'partial' if score else 'missing'
            weight_total += weight
            if score is None:
                unknown_denominator = True
            else:
                known_weight += weight
            weighted += (score or Decimal(0))*weight
            old_na_weighted += (score or Decimal(0))*weight
            if score is None or score < threshold:
                blockers.append('category_threshold_or_denominator:'+key)
            if any(g['status']!='passed' for g in gates):
                blockers.append('category_quality_gate:'+key)
        field_presence = sum(any(f['metric_key']==field['field_key'] for f in facts) or
                             any(r.get('field_key')==field['field_key'] and known(r,cutoff) for r in records) for field in fields)
        legacy_score = Decimal(field_presence)/Decimal(len(fields)) if fields else Decimal(1)
        legacy_weighted += legacy_score*weight
        categories.append({'category_key':key,'original_weight':str(weight),'original_threshold':str(threshold),
            'expected_cells':denominator,'present_cells':present,'coverage_score':str(score) if score is not None else None,
            'independently_verified_cells':sum(c.get('independent_state')=='verified' for c in category_cells),
            'excluded_by':exclusion,'status':status,'quality_gates':gates,'cells':category_cells,
            'historical_distinct_presence_score':str(legacy_score),
            'historical_age_invalidates_value':False})
        cells += category_cells if key!='sources_lineage_freshness' else []
    candidate = weighted/weight_total*Decimal(100) if weight_total and not unknown_denominator and not periods['blockers'] else None
    result = {'company_id':profile['company_id'],'as_of':cutoff.isoformat(),'policy_revision':POLICY_REVISION,
        'contract_version':contract['contract_version'],'contract_sha256':digest(contract),'policy_sha256':digest(policy),
        'input_snapshot_sha256':digest(snapshot),'profile_sha256':digest(profile),'periods':periods,
        'categories':categories,'applicable_weight':str(weight_total),
        'candidate_applicable_weighted_coverage':str(candidate) if candidate is not None else None,
        'diagnostic_known_denominator_weighted_coverage':str(weighted/known_weight*Decimal(100)) if known_weight else None,
        'diagnostic_known_weight':str(known_weight),
        'diagnostic_is_not_overall_coverage':True,
        'old_na_bonus_method_on_same_cells':str(old_na_weighted) if not unknown_denominator else None,
        'old_na_bonus_known_cells_diagnostic_only':str(old_na_weighted),
        'old_distinct_field_presence_method':str(legacy_weighted),
        'coverage_and_independent_accuracy_separate':True,'independent_accuracy_certified':False,
        'contract_gate_changes_applied':False,'production_policy_approved':False,
        'readiness_state':'not_ready','blocking_reasons':sorted(set(blockers)),
        'denominator_sha256':digest([{k:c.get(k) for k in ('category_key','field_key','period_start','period_end','period_kind','fiscal_year','fiscal_quarter','scope','dimensions')} for c in cells])}
    result['assessment_sha256'] = digest(result)
    return result


def save_assessment(result, directory):
    """Content-addressed append-only local artifact; never replace a past result."""
    payload={k:v for k,v in result.items() if k!='assessment_sha256'}
    if digest(payload)!=result.get('assessment_sha256'):
        raise ValueError('Assessment hash does not bind its contents')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/(result['assessment_sha256']+'.json')
    raw = canonical(result).encode()
    if path.exists():
        if path.read_bytes()!=raw:
            raise ValueError('Immutable assessment collision')
        return path
    with path.open('xb') as stream:
        stream.write(raw)
    return path
