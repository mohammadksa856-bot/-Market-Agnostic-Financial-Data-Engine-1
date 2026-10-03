"""Cross-document consistency of Pillar-3 values for one symbol (published + excluded)."""
import sys, os, json, glob, collections
sys.path.insert(0, os.path.dirname(__file__))
from b_inventory import ROOT, PREFIX

def run(sym, glob_pat=None):
    vals = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(ROOT, 'data/imports', (glob_pat or PREFIX[sym] + '*pillar3*.json')))):
        d = json.load(open(f, encoding='utf8'))
        for kind in ('facts', 'excluded_facts'):
            for x in d.get(kind, []):
                vals[(x['period_end'], x['metric'])].append((float(x['value']), os.path.basename(f), kind[:3], x.get('cell'), x.get('reason')))
    bad = 0
    for k in sorted(vals):
        distinct = {v[0] for v in vals[k]}
        if len(distinct) > 1:
            bad += 1
            print(k)
            for v in vals[k]: print('    ', v)
    print('conflicting keys:', bad, 'of', len(vals))

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
