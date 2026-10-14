"""Companion preview envelope: no replacement of API1.0/page5 or readiness policy."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json

from .api_contract import API_CONTRACT_VERSION, PAGE_PAYLOAD_VERSION

REVISION='company-preview-evidence/1'
BANK_COMPARISON_HOLD=frozenset({'free_cash_flow','fcf_yield','free_cash_flow_yield','capex_to_revenue','free_cash_flow_margin','return_on_invested_capital'})


def sector_metric_policy(industry,metric):
    hold=industry=='Banks' and metric in BANK_COMPARISON_HOLD
    return {'policy':'sector-comparison-preview/1','comparison_allowed':not hold,
            'reason':'bank_generic_cashflow_or_enterprise_ratio_not_automatically_comparable' if hold else None,
            'stored_fact_preserved':True,'readiness_exclusion':False,'score_changed':False}


def numeric_rows(payload, industry='', inherited_metric=None, path='$'):
    rows=[]
    if isinstance(payload,list):
        for index,item in enumerate(payload):rows+=numeric_rows(item,industry,inherited_metric,f'{path}[{index}]')
    elif isinstance(payload,dict):
        if 'value' in payload and 'unit' in payload and 'period_end' in payload:
            metric=payload.get('metric') or inherited_metric
            if metric:
                value=payload.get('value')
                try:finite=value is not None and Decimal(str(value)).is_finite()
                except (InvalidOperation,ValueError):finite=False
                provenance=payload.get('provenance') or {}
                derived=provenance.get('derivation') or {}
                calculated=bool(payload.get('is_calculated')) or bool(derived)
                lineage=derived.get('lineage') or {}
                flagged=bool(payload.get('quality_reasons')) or payload.get('quality_status') not in (None,'ok','published')
                missing_inputs=calculated and (lineage.get('current_inputs_reproduced') is not True or not lineage.get('consumed_inputs'))
                reasons=list(payload.get('quality_reasons') or ([] if finite else ['numeric_value_not_available']))
                if missing_inputs:reasons.append('calculated_input_lineage_not_reproduced')
                rows.append({'metric':metric,'value':value if finite and not flagged else None,
                             'unit':payload.get('unit'),'currency':payload.get('currency'),
                             'period_start':payload.get('period_start'),'period_end':payload.get('period_end'),
                             'period_kind':payload.get('period_kind'),'statement_type':payload.get('statement'),
                             'scope':payload.get('scope'),'dimensions':payload.get('dimensions',{}),'version':payload.get('version'),
                             'status':'withheld' if flagged or missing_inputs else 'available' if finite else 'unavailable',
                             'reasons':reasons,
                             'source':deepcopy(provenance.get('source')),
                             'verification':{'independent_numeric':'NOT_VERIFIED','production_acceptance':False,
                                 'production_method':'calculated' if calculated else 'reported',
                                 'input_lineage_status':lineage.get('status','not_recorded') if calculated else 'not_applicable_to_original',
                                 'inputs_reproduced':lineage.get('current_inputs_reproduced',False) if calculated else False},
                             'calculation':derived.get('calculation'),'consumed_inputs':deepcopy(lineage.get('consumed_inputs',[])),
                             'sector_policy':sector_metric_policy(industry,metric),'origin_path':path})
                if missing_inputs:rows[-1]['value']=None
        for key,item in payload.items():
            if key=='provenance':continue # inputs are attached, not counted again as current output facts.
            if key=='metrics' and isinstance(item,dict):
                for metric,values in item.items():rows+=numeric_rows(values,industry,metric,path+'.metrics.'+metric)
            else:rows+=numeric_rows(item,industry,inherited_metric,path+'.'+key)
    return rows


def unique_rows(rows):
    seen=set();result=[]
    for row in rows:
        identity=json.dumps({k:v for k,v in row.items() if k!='origin_path'},sort_keys=True,default=str)
        if identity not in seen:seen.add(identity);result.append(row)
    return result


def make_envelope(page,topics,operational,history=None,*,dataset_id,dataset_state):
    if page.get('contract_version')!=PAGE_PAYLOAD_VERSION or len(topics)!=18:
        raise ValueError('Pinned page5 and exact18 investor topics required')
    rows=unique_rows(numeric_rows(page,page['company'].get('industry',''))+numeric_rows(history or {},page['company'].get('industry','')))
    topics=deepcopy(topics)
    for topic in topics:
        relevant=[r for r in rows if r['metric'] in topic.get('delivered',[])]
        if topic.get('topic_key')=='competitors':
            relevant=[r for r in rows if '.peer_comparison.' in r['origin_path']]
        topic['raw_API_availability_state']=topic['state']
        topic['availability_is_not_independent_accuracy']=True
        if relevant and not any(r['status']=='available' and (topic.get('topic_key')!='competitors' or r['sector_policy']['comparison_allowed']) for r in relevant):
            topic['state']='unavailable';topic['reasons']=list(dict.fromkeys(topic.get('reasons',[])+['numeric_evidence_withheld_in_preview']))
        elif any(r['status']=='withheld' for r in relevant) and topic['state']=='available':
            topic['state']='partial';topic['reasons']=list(dict.fromkeys(topic.get('reasons',[])+['some_numeric_evidence_withheld_in_preview']))
    return {'companion_contract':REVISION,'base_API_contract':API_CONTRACT_VERSION,'page_contract':PAGE_PAYLOAD_VERSION,
            'base_response_unchanged':True,'company_id':page['company']['company_id'],
            'dataset':{'id':dataset_id,'state':dataset_state,'independent_numeric_accuracy':'NOT_VERIFIED',
                       'use':'development_preview_only_not_production_or_readiness_acceptance'},
            'investor_topics_18':topics,'operational_categories_18':deepcopy(operational),
            'model_separation':'Investor topic availability is not factory readiness, independent accuracy or95%coverage',
            'numeric_evidence':rows,'sector_history':deepcopy(history),
            'missing_data_policy':'null/status/reason; never substitute zero, demo values or100%readiness',
            'B05_production_policy':'PENDING_USER_APPROVAL','feature_activation':False}


def reproducible_payload_hash(payload):
    data=deepcopy(payload)
    if isinstance(data,dict):data.pop('generated_at',None)
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
