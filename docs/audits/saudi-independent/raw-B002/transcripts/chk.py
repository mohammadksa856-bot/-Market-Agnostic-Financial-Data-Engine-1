import sys, importlib
bad = 0
for sym in sys.argv[1:]:
    m = importlib.import_module('t' + sym)
    for d in m.T:
        for s in d['statements']:
            for n, p, t in s['checks']:
                if abs(sum(p) - t) > 0.5: print('FAIL', sym, d['sha'], s['name'], n, sum(p), t); bad += 1
print('failures', bad)
