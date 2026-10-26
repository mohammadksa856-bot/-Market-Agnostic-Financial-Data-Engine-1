import re,sys
t=open(sys.argv[1]).read().split('=== page ')
pat=re.compile(sys.argv[2],re.I)
for p in t[1:]:
    num,_,body=p.partition('\n')
    if pat.search(body) and not re.search(r'\.{8,}',body):
        print('## page',num); print('|'.join(x.strip() for x in body.split('\n') if x.strip())[:int(sys.argv[3]) if len(sys.argv)>3 else 6000]); print()
