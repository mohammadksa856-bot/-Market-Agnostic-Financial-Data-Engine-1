"""Headline-line extractor: kv.py SYM SHA PAGES(csv) [extra regex labels..]. Prints label + next numbers."""
import sys,re,pymupdf
from pg import path
LAB=r"total assets|total liabilities(?! and)|total equity(?! and)|total (?:shareholders|stockholders)[^;]{0,30}equity|total liabilities and[^;]{0,30}|revenues?|total revenues?|net revenues?|gross (?:profit|written premiums)|operating profit|profit for the (?:year|period)|(?:net )?(?:profit|income|loss)[^;]{0,40}(?:attributable|before|for the)[^;]{0,40}|net (?:income|profit|surplus)[^;]{0,40}|net cash[^;]{0,60}|cash and (?:cash equivalents|bank[^;]{0,20}) (?:at|as at|end)[^;]{0,30}|cash and cash equivalents|(?:basic|diluted)[^;]{0,50}per share|earnings per share[^;]{0,30}|total comprehensive[^;]{0,40}|insurance (?:revenue|service result)[^;]{0,30}|net (?:insurance|premiums)[^;]{0,30}"
NUM=r"\(?-?[\d,]{1,}(?:\.\d+)?\)?"
def main():
    sym,pre,pages=sys.argv[1:4]; extra=sys.argv[4:]
    d=pymupdf.open(path(sym,pre)); lab=LAB+("|"+"|".join(extra) if extra else "")
    for a in pages.split(','):
        i=int(a); t=d[i-1].get_text(); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\s*\n\s*',' ; ',t)
        print(f'## p{i}: '+t[:110])
        for m in re.finditer(r"(?i)(?<=; )(("+lab+r")[^;]*?);((?: ?;? ?[A-Za-z0-9 ]{0,3}; ?)?(?:\s*"+NUM+r"\s*(?:;|$| )){1,4})",t):
            print('  ',m.group(1).strip()[:70],'|',m.group(3).replace(' ;','').strip()[:90])
main()
