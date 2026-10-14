"""Conservative Arabic native-text balance-sheet staging, not publication approval."""
import re
import unicodedata
from datetime import date
from decimal import Decimal

def normalize(text):
    text=unicodedata.normalize('NFKC',text)
    text=re.sub(r'[\u064b-\u065f\u0670\u0640\u200e\u200f]', '',text)
    text=text.translate(str.maketrans('أإآى','اااي'))
    return re.sub(r'[\s،,؛:()\-]+','',text)

ALIASES={
    'اجمالي الموجودات':'total_assets','اجمالي المطلوبات':'total_liabilities',
    'اجمالي حقوق الملكية':'total_equity','اجمالي المطلوبات وحقوق الملكية':'total_liabilities_equity',
    'اجمالي حقوق الملكية العائدة لمساهمي البنك':'equity_parent',
    'راس المال':'share_capital','علاوة اصدار':'additional_paid_in_capital',
    'عالوة اصدار':'additional_paid_in_capital',
    'احتياطي نظامي':'statutory_reserve','احتياطيات اخري':'other_reserves',
    'ارباح مبقاة':'retained_earnings','حقوق الملكية غير المسيطرة':'noncontrolling_interests',
    'ودائع العملاء':'customer_deposits','ودائع العمالء':'customer_deposits',
    'قروض وسلف صافي':'net_loans','استثمارات صافي':'bank_investments',
    'ممتلكات ومعدات صافي':'property_plant_equipment',
    'نقدية وارصدة لدي مؤسسة النقد العربي السعودي':'cash_and_balances_with_central_bank',
    'ارصدة لدي البنوك والمؤسسات المالية الاخري صافي':'due_from_banks',
    'ارصدة للبنوك والمؤسسات المالية الاخري':'due_to_banks','سندات دين مصدرة':'debt_securities_issued',
    'ارصدة لدي البنوك والمؤسسات المالية االاخري صافي':'due_from_banks',
    'ارصدة للبنوك والمؤسسات المالية االاخري':'due_to_banks',
}
LABELS={normalize(k):v for k,v in ALIASES.items()}
MONTHS={normalize(k):v for k,v in {'مارس':3,'يونيو':6,'سبتمبر':9,'ديسمبر':12}.items()}

def number(token):
    token=unicodedata.normalize('NFKC',token).strip()
    token=''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in token)
    negative=token.startswith('(') and token.endswith(')')
    if negative:token=token[1:-1]
    if not re.fullmatch(r'\d+|\d{1,3}(?:[.,٬]\d{3})+',token):return None
    value=Decimal(re.sub(r'[.,٬]','',token))
    return -value if negative else value

def row_number(row, word):
    """Preserve detached RTL parentheses; reject incomplete sign evidence."""
    value=number(word[4])
    if value is None:return None
    left=[w for w in row if w[4] in ('(',')') and abs(w[1]-word[1])<3
          and abs(w[2]-word[0])<=6]
    right=[w for w in row if w[4] in ('(',')') and abs(w[1]-word[1])<3
           and abs(w[0]-word[2])<=6]
    if not left and not right:return value
    if len(left)!=1 or len(right)!=1 or {left[0][4],right[0][4]}!={'(',')'}:return None
    return -abs(value)

def columns(words,height):
    out=[]
    header=[w for w in words if w[1]<=height*.25]
    shared=[]
    for month in header:
        if normalize(month[4]) not in MONTHS:continue
        days=[w for w in header if abs(w[1]-month[1])<3
              and abs((w[0]+w[2]-month[0]-month[2])/2)<50 and number(w[4]) in (30,31)]
        if len(days)==1:shared.append((MONTHS[normalize(month[4])],int(number(days[0][4]))))
    for word in words:
        year=number(word[4])
        if year is None or not 1990<=year<=2035 or word[1]>height*.25:continue
        x=(word[0]+word[2])/2
        months=[w for w in words if normalize(w[4]) in MONTHS and abs((w[0]+w[2])/2-x)<40 and 0<word[1]-w[1]<25]
        if not months and len(shared)==1:
            try:period=date(int(year),*shared[0]).isoformat()
            except ValueError:continue
            out.append((x,period));continue
        if len(months)!=1:continue
        month=months[0]
        days=[w for w in words if abs(w[1]-month[1])<3 and abs((w[0]+w[2])/2-x)<40 and number(w[4]) in (30,31)]
        if len(days)!=1:continue
        try:period=date(int(year),MONTHS[normalize(month[4])],int(number(days[0][4]))).isoformat()
        except ValueError:continue
        out.append((x,period))
    # Ambiguous duplicate columns are rejected, not guessed.
    if len({p for x,p in out})!=len(out):return []
    return sorted(out)

def read_page(words,text,width,height,page):
    clean=normalize(text)
    if 'قايمةالمركزالمالي' not in normalize(text[:600]) and 'قائمةالمركزالمالي' not in normalize(text[:600]):
        return [],'not_primary_balance_candidate'
    if 'اجماليالموجودات' not in clean:return [],'not_primary_balance_candidate'
    if not any(u in clean for u in ('بالافالريالات','باالفالرياالت','بالافالرياالت','باالفالريالات')) or 'السعود' not in clean:
        return [],'explicit_sar_thousand_unit_missing'
    dates=columns(words,height)
    if not dates:return [],'unreliable_or_missing_native_dates'
    right=max(x for x,p in dates)+55
    rows=[]
    for w in sorted(words,key=lambda w:w[1]):
        if rows and abs(w[1]-rows[-1][0][1])<3:rows[-1].append(w)
        else:rows.append([w])
    facts=[]
    for row in rows:
        label_words=[w for w in row if w[0]>right and re.search(r'[\u0600-\u06ff\ufb50-\ufeff]',w[4])]
        label=' '.join(w[4] for w in sorted(label_words,key=lambda w:w[0],reverse=True))
        metric=LABELS.get(normalize(label))
        if not metric:continue
        for x,end in dates:
            values=[w for w in row if abs((w[0]+w[2])/2-x)<35 and number(w[4]) is not None]
            if len(values)!=1:continue
            value=row_number(row,values[0])
            if value is None:continue
            facts.append({'metric':metric,'source_label':label,'value':str(value),'scale':'1000',
                          'currency':'SAR','unit':'SAR','period_end':end,'period_kind':'instant',
                          'fiscal_year':int(end[:4]),'fiscal_quarter':(int(end[5:7])+2)//3,
                          'page':page,'extraction_method':'native_arabic_geometry_candidate'})
    return facts,'candidate_only_independent_review_required'
