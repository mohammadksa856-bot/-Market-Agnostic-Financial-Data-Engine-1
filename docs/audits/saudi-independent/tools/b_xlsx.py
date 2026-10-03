"""Dump an XLSX sheet region as aligned rows with coordinates (read-only)."""
import sys, openpyxl
def dump(path, sheet, r0=1, r1=40, c0=1, c1=40, w=11):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet]
    for r in range(r0, r1 + 1):
        cells = []
        for c in range(c0, c1 + 1):
            v = ws.cell(r, c).value
            if v is None: continue
            cells.append('%s=%s' % (ws.cell(r, c).coordinate, (('%.6g' % v) if isinstance(v, float) else str(v))[:34]))
        if cells: print(' | '.join(cells))
if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[1] != 'verify':
    a = sys.argv
    dump(a[1], a[2], *[int(x) for x in a[3:7]])


import re, json, os, collections, datetime
sys.path.insert(0, os.path.dirname(__file__))

def _norm(s): return re.sub(r'[^a-z0-9]', '', str(s).lower())

def _hdr_key(v):
    s = str(v).strip() if v is not None else ''
    m = re.match(r'^([1-4])Q\s*(\d{4})$', s) or re.match(r'^Q([1-4])\s*(\d{4})$', s)
    if m: return ('Q', int(m.group(1)), int(m.group(2)))
    m = re.match(r'^FY\s*(\d{4})$', s)
    if m: return ('FY', 0, int(m.group(1)))
    m = re.match(r'^(1H|9M)\s*(\d{4})$', s)
    if m: return (m.group(1), 0, int(m.group(2)))
    return None

def build_index(path):
    """{sheet: {'headers': {key: [col...]}, 'rows': [(row, label, {col: value})]}}"""
    wb = openpyxl.load_workbook(path, data_only=True)
    idx = {}
    for ws in wb:
        hdr = collections.defaultdict(list)
        hrow = None
        for r in range(1, 10):
            ks = [(c, _hdr_key(ws.cell(r, c).value)) for c in range(1, ws.max_column + 1)]
            ks = [(c, k) for c, k in ks if k]
            if len(ks) >= 3:
                hrow = r
                for c, k in ks: hdr[k].append(c)
                break
        rows = []
        if hrow:
            for r in range(hrow + 1, ws.max_row + 1):
                lab = ws.cell(r, 1).value if isinstance(ws.cell(r, 1).value, str) and ws.cell(r, 1).value.strip() else ws.cell(r, 2).value
                if not isinstance(lab, str): continue
                rows.append((r, lab, {c: ws.cell(r, c).value for cs in hdr.values() for c in cs}))
        idx[ws.title] = dict(headers=hdr, rows=rows, hrow=hrow)
    return idx

def keys_for(kind, period_end):
    y, m = int(period_end[:4]), int(period_end[5:7])
    q = (m - 1) // 3 + 1
    if kind == 'fy': return [('FY', 0, y)]
    if kind == 'quarter': return [('Q', q, y)]
    if kind == 'instant': return [('Q', q, y)] + ([('FY', 0, y)] if m == 12 else [])
    if kind == 'ytd': return [('1H', 0, y)] if m == 6 else [('9M', 0, y)] if m == 9 else [('Q', q, y)] if m == 3 else [('FY', 0, y)]
    return []

def verify_xlsx(path, manifest_path):
    idx = build_index(path)
    d = json.load(open(manifest_path, encoding='utf8'))
    out = []
    for kind_f, lst in (('pub', d.get('facts', [])), ('exc', d.get('excluded_facts', []))):
        for x in lst:
            val = float(x['value']); lab = _norm(x['source_label'])
            ks = keys_for(x['period_kind'], x['period_end'])
            found = []  # (sheet,row,label,col,cellvalue)
            labelhit = False
            for sh, info in idx.items():
                for r, rl, cells in info['rows']:
                    nl = _norm(rl)
                    if nl == lab or (len(lab) > 8 and (nl.startswith(lab) or lab.startswith(nl) and len(nl) > 8)):
                        labelhit = True
                        for k in ks:
                            for c in info['headers'].get(k, []):
                                v = cells.get(c)
                                if isinstance(v, (int, float)):
                                    found.append((sh, r, rl.strip(), openpyxl.utils.get_column_letter(c), v))
            ok = [f for f in found if abs(f[4] - val) <= max(6e-4, abs(val) * 1e-9)]
            sign = [f for f in found if abs(abs(f[4]) - abs(val)) <= max(6e-4, abs(val) * 1e-9)]
            rnd = [f for f in found if abs(abs(f[4]) - abs(val)) <= (0.5 if abs(val) >= 100 else 0.0051)]
            if ok: st = 'ok'
            elif sign: st = 'ok_signflip'; ok = sign
            elif rnd: st = 'ok_rounded'; ok = rnd
            elif found: st = 'MISMATCH'
            elif labelhit: st = 'no_column'
            else: st = 'label_not_found'
            out.append((kind_f, x['metric'], x['period_kind'], x['period_end'], x['value'], st, ok[:1] or found[:3], x.get('reason')))
    return out

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'verify':
    from b_inventory import inventory, ROOT
    sym = sys.argv[2]
    for r in inventory(sym):
        if 'supplement' not in r['manifest']: continue
        res = verify_xlsx(os.path.join(ROOT, r['local'][0]), os.path.join(ROOT, 'data/imports', r['manifest']))
        c = collections.Counter((o[0], o[5]) for o in res)
        print(r['manifest'], dict(c))
        for o in res:
            if not o[5].startswith('ok') and o[0] == 'pub': print('    ', o)
