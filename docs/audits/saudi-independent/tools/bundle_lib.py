"""Helpers for the unified Saudi defect bundle (offline, read-only on data/**)."""
import hashlib, json, os, re, subprocess, io
import pymupdf

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
NR = 'not recorded by batch'
UN = 'unavailable'

_idx = json.load(open(os.path.join(REPO, 'data/raw/archive-index.json'), encoding='utf8'))['artifacts']
BYURL = {a['source_url']: a for a in _idx}
BYHASH = {a['content_hash']: a for a in _idx}
_mcache, _scache, _tcache, _dcache = {}, {}, {}, {}


def load_manifest(name, ref=None):
    name = name if name.endswith('.json') else name + '.json'
    key = (name, ref)
    if key in _mcache:
        return _mcache[key]
    try:
        if ref is None:
            m = json.load(open(os.path.join(REPO, 'data/imports', name), encoding='utf8'))
        else:
            m = json.loads(git_show(ref, 'data/imports/' + name))
    except Exception:
        m = None
    _mcache[key] = m
    return m


def git_show(ref, path, binary=False):
    r = subprocess.run(['git', '-C', REPO, 'show', f'{ref}:{path}'], capture_output=True)
    if r.returncode:
        raise FileNotFoundError(f'{ref}:{path}')
    return r.stdout if binary else r.stdout.decode('utf8')


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def refs_holding(path):
    r = subprocess.run(['git', '-C', REPO, 'rev-list', '--all', '-n', '1', '--', path], capture_output=True, text=True).stdout.strip()
    if not r:
        return None
    b = subprocess.run(['git', '-C', REPO, 'branch', '-r', '--contains', r], capture_output=True, text=True).stdout.split('\n')
    return r, [x.strip() for x in b if x.strip()][:3]


def LP(a):
    return a['local_path'].replace(chr(92), '/')


def source_info(artifact=None, url=None, content_hash=None, ref=None, path=None):
    """Return a source-file dict. SHA-256 is recomputed from bytes whenever bytes are reachable offline."""
    a = artifact or BYURL.get(url) or BYHASH.get(content_hash)
    out = {'sha256': None, 'sha256_basis': None, 'archive_path': None, 'available_offline': False, 'where': None, 'url': None}
    if a:
        out['url'] = a['source_url']
        out['archive_path'] = LP(a)
        out['index_content_hash'] = a['content_hash']
        lp = os.path.join(REPO, LP(a))
        if os.path.exists(lp):
            s = sha_file(lp)
            out.update(sha256=s, sha256_basis='recomputed from archived file in this worktree' + ('; equals archive-index content_hash' if s == a['content_hash'] else '; DIFFERS from archive-index content_hash'),
                       available_offline=True, where='worktree: ' + LP(a))
            return out
        rr = refs_holding(LP(a))
        if rr:
            try:
                data = git_show(rr[0], LP(a), binary=True)
                s = hashlib.sha256(data).hexdigest()
                out.update(sha256=s, sha256_basis=f'recomputed via git show from commit {rr[0][:10]} (branches: {", ".join(rr[1])}); ' + ('equals archive-index content_hash' if s == a['content_hash'] else 'DIFFERS from archive-index'),
                           available_offline=True, where=f'git object {rr[0][:10]}:{LP(a)}')
                return out
            except Exception:
                pass
        out.update(sha256=a['content_hash'], sha256_basis='archive-index.json content_hash only; file bytes NOT available offline in this worktree or any local ref (not re-hashed)',
                   available_offline=False, where=UN + f'; listed in data/raw/archive-index.json, local_path {LP(a)} absent in all refs; must be re-archived from source url')
        return out
    if ref and path:
        try:
            data = git_show(ref, path, binary=True)
            s = hashlib.sha256(data).hexdigest()
            out.update(sha256=s, sha256_basis=f'recomputed via git show {ref}:{path}', available_offline=True, where=f'{ref}:{path}', archive_path=path)
            return out
        except Exception:
            pass
    out.update(sha256=UN, sha256_basis='no archive-index entry and no reachable file', where=UN)
    return out


def source_for_manifest(name, ref=None):
    m = load_manifest(name, ref)
    if not m:
        return None, None
    return m, source_info(url=m.get('source_url'))


# ---- PDF access -----------------------------------------------------------
def open_pdf(src):
    """src: source_info dict. Returns pymupdf doc or None."""
    if not src or not src.get('available_offline'):
        return None
    key = src['sha256']
    if key in _dcache:
        return _dcache[key]
    w = src['where']
    doc = None
    if w.startswith('worktree: '):
        doc = pymupdf.open(os.path.join(REPO, w[len('worktree: '):]))
    elif w.startswith('git object '):
        c, p = w[len('git object '):].split(':', 1)
        doc = pymupdf.open(stream=git_show(c.strip(), p, binary=True), filetype='pdf')
    else:
        ref, p = w.split(':', 1)
        if p.lower().endswith('.pdf'):
            doc = pymupdf.open(stream=git_show(ref, p, binary=True), filetype='pdf')
    _dcache[key] = doc
    return doc


def page_text(src, p):
    doc = open_pdf(src)
    if doc is None or p is None or p < 1 or p > len(doc):
        return None
    k = (src['sha256'], p)
    if k not in _tcache:
        _tcache[k] = doc[p - 1].get_text()
    return _tcache[k]


def printed_page(src, p):
    t = page_text(src, p)
    if t is None:
        return None
    ls = [l.strip() for l in t.splitlines() if l.strip()]
    cand = ls[:3] + ls[-3:]
    for l in cand:
        m = re.fullmatch(r'(?:Page\s+)?(\d{1,3})(?:\s+of\s+\d+)?', l, re.I)
        if m:
            return m.group(1)
    return None


def norm_num(s):
    return re.sub(r'[,\s]', '', str(s))


def on_page(src, p, needle):
    """True/False if the page has a text layer; None if the page is not readable. Matches on number boundaries (no digit/comma-digit around)."""
    t = page_text(src, p)
    if t is None:
        return None
    pat = r'(?<![\d])(?<!\d,)' + re.escape(str(needle)) + r'(?!\d)(?!,\d)'
    return bool(re.search(pat, t))


def fmt(v):
    """123456 -> '123,456' for matching printed numbers."""
    try:
        x = abs(int(float(v)))
        return f'{x:,}'
    except Exception:
        return str(v)


def render_png(src, p, out, zoom=1.1, clip=None):
    doc = open_pdf(src)
    if doc is None:
        return False
    pix = doc[p - 1].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pix.save(out)
    return True


def url_stamp(url):
    m = re.search(r'(20\d\d-\d\d-\d\d)_\d\d-\d\d-\d\d', url or '')
    return m.group(1) if m else None


PRIORITY_LABELS = {
    1: 'ANB (1080) defects D1-D4',
    2: 'stc (7010) scale errors (and other unit/scale-type errors)',
    3: 'Quarter-vs-YTD / wrong period-column defects',
    4: 'Zakat basis (D6) and other restated / continuing-operations basis defects',
    5: 'Other numeric value, mapping, sign and definition defects',
    6: 'Provenance and metadata defects (page citations, filed_at, scanned/digital tags)',
    7: 'Completeness, coverage and source-availability defects',
}
SRC_BRANCH = {
    'batch1-A': 'origin/claude/audit-saudi-batch1-A', 'batch1-B': 'origin/claude/audit-saudi-batch1-B',
    'batch1-C': 'origin/claude/audit-saudi-batch1-C', 'batch1-D': 'origin/claude/audit-saudi-batch1-D',
    'batch2-E': 'origin/claude/audit-saudi-batch2-E', 'batch2-F': 'origin/claude/audit-saudi-batch2-F',
}
BUNDLE = 'docs/audits/saudi-independent/bundle'
EVID = 'docs/audits/saudi-independent/bundle-evidence'
COMPANY = {'1080': 'Arab National Bank (ANB)', '1010': 'Riyad Bank', '1020': 'Bank AlJazira', '1120': 'Al Rajhi Bank', '1140': 'Bank Albilad',
           '1030': 'Saudi Investment Bank (SAIB)', '1150': 'Alinma Bank', '1180': 'Saudi National Bank (SNB)', '2222': 'Saudi Aramco', '8010': 'Tawuniya',
           '7010': 'stc (Saudi Telecom)', '7020': 'Mobily', '7030': 'Zain KSA', '7040': 'GO Telecom', '7203': 'Elm',
           '2010': 'SABIC', '2082': 'ACWA Power', '3010': 'Arabian Cement', '3030': 'Saudi Cement', '3050': 'Southern Province Cement',
           '3002': 'Najran Cement', '3003': 'City Cement', '3005': 'Umm Al-Qura Cement', '3020': 'Yamama Cement', '3040': 'Qassim Cement',
           '3060': 'Yanbu Cement', '7202': 'solutions by stc'}


def bpath(batch, name):
    return f'{BUNDLE}/{batch}/{name}'


def branch_path(batch, name):
    return f'{SRC_BRANCH[batch]}:docs/audits/saudi-independent/{name}'


def rec(**k):
    """Normalised record; every required field is present (explicit placeholder if the batch lacked it)."""
    base = dict(
        bundle_id=None, status='suspected', batch_claimed_status=NR, priority_group=5, priority_rank=0,
        symbol=None, company=None, defect_id=None, defect_class=NR, severity=NR, category=NR,
        manifest=NR, source_file=None,
        location=dict(pdf_page=NR, printed_page=NR, caption=NR, column=NR, unit_scale=NR, period=NR),
        published_value=NR, correct_value=NR,
        comparison=dict(restated=NR, continuing_operations=NR, comparison_source=NR, note=''),
        evidence_link=dict(batch_record=None, batch_branch_path=None, page_evidence=[], transcription=None),
        pinning_test=dict(test='none', scope_note=''),
        verification=dict(level='batch_only', by='batch auditor', result='not re-checked by bundle', notes=''),
        batch_fix=NR,
    )
    for key, v in k.items():
        if isinstance(v, dict) and isinstance(base.get(key), dict):
            base[key] = {**base[key], **v}
        else:
            base[key] = v
    if base['symbol'] and not base['company']:
        base['company'] = COMPANY.get(base['symbol'], NR)
    return base
