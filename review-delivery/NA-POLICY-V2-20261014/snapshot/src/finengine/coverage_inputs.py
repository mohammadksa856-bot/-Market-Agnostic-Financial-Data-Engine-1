"""Capture an as-of local read-only input snapshot; no score refresh or publish."""
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from .database import Database
from .asof_evidence import points_known_as_of, provenance_for_point
from .period_coverage import instant, known


def _timestamp(value):
    if not value:
        return None
    value=str(value).replace(' ','T')
    if len(value)==10:
        return value+'T23:59:59.999999+00:00'
    return value if '+' in value[10:] or value.endswith('Z') else value+'+00:00'

def _validate_registered_contract(conn, row):
    """Reuse registered period/scope/dimension rules without constructing Database."""
    issues=[]
    contract=conn.execute('SELECT * FROM metric_contracts WHERE metric_key=? AND enabled=1',(row['metric_key'],)).fetchone()
    field=conn.execute('SELECT * FROM data_catalog_fields WHERE field_key=? AND enabled=1',(row['metric_key'],)).fetchone()
    if contract is None or field is None or field['review_state']!='reviewed':
        return False,['registered_reviewed_contract_missing']
    try:
        dimensions=json.loads(row['dimensions_json'])
        if not isinstance(dimensions,dict) or any(not isinstance(v,str) for v in dimensions.values()):
            raise ValueError('dimensions must be string-valued object')
        validator=Database.__new__(Database)
        validator.conn=conn
        validator._validate_fact_contract(row['metric_key'],row['period_kind'],row['scope'],dimensions)
    except (ValueError,TypeError):issues.append('period_scope_or_dimensions_invalid')
    if row['value_type'] != field['value_type']:
        issues.append('registered_value_type_mismatch')
    if row['value_type']=='decimal':
        try:
            if not Decimal(row['value_decimal']).is_finite():issues.append('nonfinite_value')
        except (InvalidOperation,TypeError):issues.append('invalid_decimal_value')
    unit=row['unit']; family=contract['unit_family']; currency=row['currency']
    valid_unit=False
    if family=='monetary': valid_unit=bool(currency and (unit=='currency' or unit==currency))
    elif family=='per_share': valid_unit=bool(currency and unit in ('currency/share',currency+'/share'))
    elif family=='ratio': valid_unit=unit=='ratio'
    elif family=='count': valid_unit=unit==field['default_unit']
    elif family in ('text','json','date','boolean'): valid_unit=unit==family
    elif family=='physical_or_scalar': valid_unit=bool(field['default_unit'] and unit==field['default_unit'])
    if not valid_unit:issues.append('registered_unit_family_mismatch')
    try:
        end=date.fromisoformat(row['period_end'])
        start=date.fromisoformat(row['period_start']) if row['period_start'] else None
        if start and start>end:issues.append('period_start_after_end')
        if row['period_kind'] in ('fy','quarter','ytd','ttm') and start is None:issues.append('duration_start_missing')
        if row['period_kind'] in ('quarter','ytd') and row['fiscal_quarter'] not in (1,2,3,4):issues.append('quarter_invalid')
    except (TypeError,ValueError):issues.append('period_date_invalid')
    return not issues,issues


def capture_coverage_inputs(conn, company_id, as_of):
    before_changes=conn.total_changes
    cutoff=instant(as_of)
    if cutoff is None: raise ValueError('Explicit as_of required')
    company=conn.execute('SELECT * FROM companies WHERE company_id=?',(company_id,)).fetchone()
    if company is None: raise KeyError(company_id)
    catalog=[]
    for row in conn.execute('SELECT * FROM data_catalog_fields ORDER BY field_key'):
        item=dict(row)
        definition=conn.execute('SELECT allowed_period_kinds_json FROM metric_contracts WHERE metric_key=? AND enabled=1',(item['field_key'],)).fetchone()
        item.update(reviewed=item['review_state']=='reviewed',enabled=bool(item['enabled']),
                    allowed_period_kinds=json.loads(definition[0]) if definition else [])
        catalog.append(item)
    facts=[]
    for row in points_known_as_of(conn,company_id,cutoff.isoformat()):
        item=dict(row)
        item.pop('is_current',None)
        proof=provenance_for_point(conn,row['id'],cutoff.isoformat())
        try:
            dimensions=json.loads(row['dimensions_json'])
        except (TypeError,ValueError):dimensions=None
        item.update(known_at=_timestamp(row['published_at']),dimensions=dimensions,
                    contract_valid=False,lineage_complete=proof['lineage_complete'],
                    source_complete=proof['source_complete'],independent_state=proof['independent_state'],
                    provenance=proof,audit_state='unknown')
        item['contract_valid'],item['contract_issues']=_validate_registered_contract(conn,row)
        # Audit status needs bound independent source evidence, never filename inference.
        audit=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='period_audit_evidence'").fetchone()
        if audit:
            proofrow=conn.execute('SELECT * FROM period_audit_evidence WHERE point_id=? AND point_version=?',(row['id'],row['version'])).fetchall()
            source=conn.execute('SELECT content_hash FROM source_documents WHERE source_key=?',(row['source_key'],)).fetchone()
            if any(p['audit_state']=='audited' and instant(_timestamp(p['known_at'])) and instant(_timestamp(p['known_at']))<=cutoff
                   and p['snapshot_sha256']==proof.get('snapshot_sha256') and proof['source_complete']
                   and 'source_hash' in p.keys() and source and p['source_hash']==source['content_hash']
                   and 'authority' in p.keys() and p['authority'].strip() for p in proofrow):item['audit_state']='audited'
        facts.append(item)
    records=[]
    # Only versioned stored records; current registry columns do not prove past facts.
    domains=(('company_attributes','company_profile','effective_at'),
             ('ownership_positions','ownership_positions','as_of_date'),
             ('corporate_actions','corporate_actions','announcement_date'),
             ('disclosures','disclosures','published_at'),
             ('consensus_estimates','consensus_estimates','estimate_as_of'))
    tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table,domain,effective in domains:
        if table not in tables:continue
        for row in conn.execute(f'SELECT * FROM {table} WHERE company_id=? ORDER BY id',(company_id,)):
            raw=dict(row)
            source=conn.execute('SELECT * FROM source_documents WHERE source_key=?',(raw.get('source_key'),)).fetchone() if raw.get('source_key') else None
            available=raw.get('published_at') or raw.get('created_at')
            common={'id':raw['id'],'company_id':company_id,'version':raw.get('version',1),'storage_domain':domain,
                    'known_at':_timestamp(available),'effective_at':_timestamp(raw.get(effective)),
                    'filed_at':source['filed_at'] if source else _timestamp(available),
                    'source_complete':False,'independent_state':'not_verified','contract_valid':False,
                    'contract_issues':['typed_record_contract_and_bound_evidence_not_validated']}
            fields={}
            if table=='company_attributes':fields={raw['attribute_key']:json.loads(raw['value_json'])}
            elif table=='ownership_positions':
                fields={key:raw[column] for key,column in {'holder_name':'holder_name','holder_type':'holder_type',
                    'shares_held':'shares','ownership_percentage':'ownership_pct'}.items() if raw.get(column) is not None}
            elif table=='corporate_actions':fields={raw['action_type']:raw['title']}
            elif table=='disclosures':fields={raw['disclosure_type']:raw.get('title')}
            else:fields={raw['metric_key']:raw['value_decimal']}
            for field,value in fields.items():
                candidate={**common,'field_key':field,'value':value}
                if known(candidate,cutoff):records.append(candidate)
    return {'company':dict(company),'catalog':catalog,'facts':facts,'records':records,
            'applicability_evidence':[],'monitor_captures':[],
            'capture_mode':'read_only_as_of_history','SQL_changes':conn.total_changes-before_changes,
            'historical_retirement_assurance':'requires_versioned_retirement_evidence_not_current_flag'}
