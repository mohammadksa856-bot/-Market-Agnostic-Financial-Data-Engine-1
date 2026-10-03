"""Contact sheet of pages for visual triage. usage: sheet.py SYM SHA_PREFIX OUTNAME page,page,... [dpi]"""
import sys, os, io, pymupdf
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from pg import path, OUT
sym, pre, name, pages = sys.argv[1:5]; dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 60
d = pymupdf.open(path(sym, pre)); ims = []
for n in pages.split(','):
    ims.append(Image.open(io.BytesIO(d[int(n)-1].get_pixmap(dpi=dpi).tobytes('png'))))
w = sum(i.width for i in ims); h = max(i.height for i in ims)
s = Image.new('RGB', (w, h), 'white'); x = 0
for i in ims: s.paste(i, (x, 0)); x += i.width
f = os.path.join(OUT, name + '.png'); s.save(f); print(f)
