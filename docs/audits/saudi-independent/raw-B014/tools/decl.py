"""decl.py: list cross-filing differences for a doc list and build explicit restatement declarations.
declare(docs, rules) where rules = [(stmt, period_end, period_type, {docA, docB}, reason, keys-or-None)] ; every difference must be covered by a rule (else SystemExit),
so a difference can only be declared after a human has looked at it and written the reason."""
import check_transcripts as ct
def differences(docs):
    out = []
    for (stmt, pe, pt), cols in ct.column_index(docs).items():
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                (la, ca, a), (lb, cb, b) = cols[i], cols[j]
                for k in ct.CROSS_KEYS[stmt]:
                    if k in a and k in b and a[k] != b[k]:
                        out.append((stmt, pe, pt, k, la, a[k], lb, b[k]))
    return out
def show(docs):
    for d in differences(docs): print(d)
def declare(docs, rules, quiet=False):
    decl = []; unc = []
    for stmt, pe, pt, k, la, va, lb, vb in differences(docs):
        hit = None
        for r in rules:
            if (r[0], r[1], r[2]) == (stmt, pe, pt) and {la, lb} == set(r[3]) and (r[5] is None or k in r[5]):
                hit = r; break
        if not hit: unc.append((stmt, pe, pt, k, la, va, lb, vb)); continue
        o, rp = hit[3]
        vals = {la: va, lb: vb}
        decl.append({'stmt': stmt, 'period_end': pe, 'period_type': pt, 'key': k, 'original_doc': o, 'represented_doc': rp, 'original': vals[o], 'represented': vals[rp], 'reason': hit[4]})
    if unc:
        for u in unc: print('UNCOVERED', u)
        if not quiet: raise SystemExit('uncovered differences')
    return decl
