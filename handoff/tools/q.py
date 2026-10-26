import sqlite3,sys
c=sqlite3.connect(sys.argv[1])
for r in c.execute(sys.argv[2]): print('|'.join(str(x) for x in r))
