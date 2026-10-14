"""Central project tracking: immutable events, linked tasks and batch receipts.

Historical test runs remain separate records. No product/data/production writes.
Only Codex mutates the central board; consumer reports require explicit review.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

BOARD='docs/PROJECT_EXECUTION_BOARD_ROOT_20261011_v1.json'
STATES={'TODO','IN_PROGRESS','BLOCKED','REVIEW','TESTED','MERGED','ACCEPTED'}
REPORT_FIELDS={'completed','in_progress','blocked','files_and_commits','test_runs','merged_and_unmerged',
               'area_progress','agent_dependencies','user_decisions','next_three','executive_summary_ar'}

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def fingerprint(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def _immutable(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=canonical(payload)
    if path.exists():
        if path.read_text(encoding='utf-8')!=raw:raise ValueError('Immutable artifact already exists')
        return
    with path.open('x',encoding='utf-8') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())

def verify_events(root):
    result=[];previous=None
    for path in sorted((Path(root)/'docs/tracking/events').glob('*.json')):
        item=load(path);claimed=item.pop('event_sha256')
        if fingerprint(item)!=claimed or item['previous_event_sha256']!=previous or item['sequence']!=len(result)+1:
            raise ValueError('Broken immutable event chain')
        item['event_sha256']=claimed;result.append(item);previous=claimed
    return result

def validate_batch(report):
    if not REPORT_FIELDS<=set(report):raise ValueError('All ten report sections and Arabic executive summary required')
    if len(report['next_three'])!=3:raise ValueError('Exactly three prioritized next tasks required')
    required_areas={'factory','data','website','bot','API'}
    if not required_areas<=set(report['area_progress']):raise ValueError('All five product areas required')
    for run in report['test_runs']:
        if not {'run_id','branch','commit','artifact','scope','passed','failed','errors','expected_failures','skipped','observed_at'}<=set(run):
            raise ValueError('Each test run needs its own branch, commit, artifact, scope and counts')
        if any(type(run[k])!=int or run[k]<0 for k in ('passed','failed','errors','expected_failures','skipped')):
            raise ValueError('Invalid per-run test counts')
    return deepcopy(report)

def record_batch(root,report):
    report=validate_batch(report)
    for key in ('batch_id','observed_at','branch','baseline_commit'):
        if not report.get(key):raise ValueError('Batch identity and baseline required')
    if not report['batch_id'].replace('-','').replace('_','').isalnum():raise ValueError('Unsafe batch identifier')
    path=Path(root)/'docs/tracking/batches'/(report['batch_id']+'.json')
    _immutable(path,report)
    return path

def append_event(root,event,actor='Codex'):
    if actor!='Codex':raise PermissionError('Only Codex coordinates central board updates')
    root=Path(root);board=load(root/BOARD)
    for key in ('event_id','occurred_at','task_id','change','branch','commits','changed_files','test_runs','review_decision','batch_report'):
        if key not in event:raise ValueError('Missing event field:'+key)
    task=next((t for t in board['tasks'] if t['id']==event['task_id']),None)
    if task is None:raise ValueError('Unknown central task')
    if event.get('state') not in STATES:raise ValueError('Unknown task state')
    report_path=root/event['batch_report']
    if not report_path.resolve().is_relative_to((root/'docs/tracking/batches').resolve()):raise ValueError('Batch must be an immutable local receipt')
    report=validate_batch(load(report_path))
    if event['state'] in {'TESTED','MERGED','ACCEPTED'} and not event['test_runs']:
        raise ValueError('Completion requires test evidence')
    if event['state'] in {'MERGED','ACCEPTED'} and event['review_decision']!='approved_local_merge':
        raise ValueError('Merge requires explicit coordinator review')
    if event['state']=='ACCEPTED' and not event.get('user_acceptance_evidence'):
        raise ValueError('Product acceptance requires separate human evidence')
    if event.get('production_published') and not event.get('production_authorization_evidence'):
        raise ValueError('Production requires explicit authorization')
    declared={r['run_id']:r for r in report['test_runs']}
    for run in event['test_runs']:
        if run['run_id'] not in declared or run!=declared[run['run_id']]:raise ValueError('Run cannot be combined or relabelled')
        if event['state'] in {'TESTED','MERGED','ACCEPTED'} and any(run[k] for k in ('failed','errors','expected_failures','skipped')):
            raise ValueError('Unresolved failures/skips cannot close completion')
    folder=root/'docs/tracking/events';folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'.writer.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        history=verify_events(root)
        if any(e['event_id']==event['event_id'] for e in history):raise ValueError('Duplicate event identifier')
        item=deepcopy(event);item.update(sequence=len(history)+1,actor=actor,
            previous_event_sha256=history[-1]['event_sha256'] if history else None)
        item['event_sha256']=fingerprint(item)
        _immutable(folder/f"{item['sequence']:06d}-{item['event_sha256']}.json",item)
        task.update(state=event['state'],branch=event['branch'],commits=event['commits'],changed_files=event['changed_files'],
            test_runs=event['test_runs'],evidence=event.get('evidence',task.get('evidence',[])),
            blockers=event.get('blockers',[]),required_decisions=event.get('required_decisions',[]),
            change_stage=event.get('change_stage','LOCAL'),production_published=bool(event.get('production_published')),
            latest_event_sha256=item['event_sha256'],latest_batch_report=event['batch_report'])
        # The board is a current projection; only the event history is immutable.
        temporary=root/(BOARD+'.pending')
        temporary.write_text(json.dumps(board,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.replace(temporary,root/BOARD)
        return item
    finally:
        os.close(fd);lock.unlink()

def validate_claude_report(report):
    required={'report_id','task_ids','branch','base_commit','commits','changed_files','test_runs',
              'shared_file_patches','blockers','decisions_required','review_requested','production_changes'}
    if not required<=set(report):raise ValueError('Incomplete Claude delivery report')
    if report['production_changes']!=0 or report['review_requested'] is not True:raise ValueError('No unreviewed production or automatic acceptance')
    return deepcopy(report)
