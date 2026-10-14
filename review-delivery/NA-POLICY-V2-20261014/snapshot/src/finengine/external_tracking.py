"""Read-only sender admission: derived references, never a raw ledger copy.

Source claims do not authorize merges, product acceptance or production changes.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from .project_tracking import BOARD,load,canonical,fingerprint,_immutable

def _git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True,encoding='utf-8').strip()
def _sha(raw):return hashlib.sha256(raw).hexdigest()

def import_claude_evidence(root,sender,actor='Codex'):
    if actor!='Codex':raise PermissionError('Coordinator review required')
    root=Path(root);sender=Path(sender)
    head=_git(sender,'rev-parse','HEAD');branch=_git(sender,'branch','--show-current')
    paths={'ledger':sender/'docs/claude_product/tracking/CHANGELOG.jsonl',
           'status':sender/'docs/claude_product/tracking/TRACK_STATUS.json'}
    raw={k:p.read_bytes() for k,p in paths.items()}
    reports={p.name:p.read_bytes() for p in (sender/'docs/claude_product/tracking/reports').glob('BR-*') if p.is_file()}
    events=[json.loads(line) for line in raw['ledger'].splitlines() if line.strip()]
    status=json.loads(raw['status']);mapping={t['id']:t.get('central_id','P01') for t in status['tasks']}
    runs={r['run_id']:r for r in status.get('test_runs',[])}
    namespace=_sha(str(sender.resolve()).encode())[:16]
    store=root/'docs/tracking/external_events'
    seen={r['external_id']:r for p in store.glob('*.json') for r in [load(p)]}
    pending=[]
    for index,event in enumerate(events,1):
        if event.get('seq')!=index or not isinstance(event.get('actor'),str) or not event['actor'].strip():raise ValueError('Invalid sender sequence/actor')
        sourcehash=fingerprint(event);identity=namespace+':'+str(index)
        if identity in seen:
            if seen[identity]['source_event_sha256']!=sourcehash:raise ValueError('Sender history changed; review required')
            continue
        pending.append(dict(external_id=identity,source_event_sha256=sourcehash,
            source_event_sequence=index,source_actor_claim=event['actor'],source_repository=str(sender),source_path=str(paths['ledger']),
            source_branch=event.get('branch'),source_commit=event.get('commit'),source_at=event.get('at'),
            central_task_id=mapping.get(event['task'],event['task'] if event['task'] in ('R01','B03','P01') else 'P01'),
            sender_task_id=event['task'],claim_type=event['type'],test_run_refs=event.get('test_runs',[]),
            referenced_runs=[dict(runs[r],verification='sender_reported_not_rerun') for r in event.get('test_runs',[]) if r in runs],
            unresolved_run_refs=[r for r in event.get('test_runs',[]) if r not in runs],
            reviewed_source_head=head,source_ledger_sha256=_sha(raw['ledger']),
            review_state='ADMITTED_AS_EVIDENCE_ONLY',code_accepted=False,tests_verified_here=False,
            integrated=False,product_accepted=False,production_published=False))
    # Validate prefix, all old identities and stable byte snapshots before any write.
    if any(int(r['source_event_sequence'])>len(events) for r in seen.values() if r['external_id'].startswith(namespace+':')):
        raise ValueError('Sender history was truncated')
    if any(paths[k].read_bytes()!=v for k,v in raw.items()) or _git(sender,'rev-parse','HEAD')!=head:
        raise ValueError('Sender changed while reading; retry on a stable snapshot')
    for name,value in reports.items():
        if (sender/'docs/claude_product/tracking/reports'/name).read_bytes()!=value:raise ValueError('Report changed while reading')
    for item in pending:
        _immutable(store/(item['external_id'].replace(':','-')+'.json'),item)
    report_refs=[]
    for name,value in reports.items():
        receipt=dict(source_report_id=name,source_sha256=_sha(value),source_path=str(sender/'docs/claude_product/tracking/reports'/name),
                     reviewed_source_head=head,source_branch=branch,raw_report_copied=False,
                     central_disposition='Reference retained; sender tests kept separate; no automatic acceptance')
        destination=root/'docs/tracking/external_reports'/(_sha(value)+'.json')
        if not destination.exists():_immutable(destination,receipt)
        report_refs.append(destination.relative_to(root).as_posix())
    board=load(root/BOARD);byid={t['id']:t for t in board['tasks']}
    # Recover a projection if a previous admission stopped after writing receipts.
    for path in store.glob('*.json'):
        item=load(path);task=byid.get(item['central_task_id'])
        if task is None:continue
        refs=task.setdefault('external_evidence',[])
        reference=path.relative_to(root).as_posix()
        if reference not in refs:refs.append(reference);refs.sort()
    board['execution_tracking']['latest_Claude_admission']={
        'head':head,'branch':branch,'source_repository':str(sender),'observed_at':datetime.now(timezone.utc).isoformat(),
        'source_ledger_sha256':_sha(raw['ledger']),'source_status_sha256':_sha(raw['status']),
        'new_events':len(pending),'events_seen':len(events),'reports':report_refs,
        'source_dirty_files':_git(sender,'status','--short').splitlines(),
        'no_original_writes':True,'no_status_promotion':True}
    (root/BOARD).write_text(json.dumps(board,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return board['execution_tracking']['latest_Claude_admission']
