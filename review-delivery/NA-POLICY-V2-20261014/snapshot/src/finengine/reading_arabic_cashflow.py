"""Conservative Arabic primary cash-flow staging; not publication approval."""
import re
from .reading_arabic_balance import normalize,columns,number,row_number

ALIASES={
 'صافي النقدية المستخدمة في الأنشطة التشغيلية':'operating_cash_flow',
 'صافي النقدية من الأنشطة التشغيلية':'operating_cash_flow',
 'صافي النقد من الأنشطة التشغيلية':'operating_cash_flow',
 'صافي النقدية الناتجة من الأنشطة التشغيلية':'operating_cash_flow',
 'صافي النقدية المستخدمة في الأنشطة الاستثمارية':'investing_cash_flow',
 'صافي النقدية من الأنشطة الاستثمارية':'investing_cash_flow',
 'صافي النقدية من / المستخدمة في الأنشطة التمويلية':'financing_cash_flow',
 'صافي النقدية من الأنشطة التمويلية':'financing_cash_flow',
 'صافي النقدية المستخدمة في الأنشطة التمويلية':'financing_cash_flow',
 'صافي النقص في النقدية وشبه النقدية':'cash_change',
 'صافي الزيادة في النقدية وشبه النقدية':'cash_change',
 'صافي التغير في النقدية وشبه النقدية':'cash_change',
 'النقدية وشبه النقدية في بداية الفترة':'cash_beginning',
 'النقدية وشبه النقدية في نهاية الفترة':'cash_end',
 'شراء ممتلكات ومعدات':'capex',
 'شراء ممتلكات ومعدات وموجودات غير ملموسة صافي':'capex',
 'استهلاك وإطفاء':'depreciation_amortization_cash_flow',
 'سندات دين مصدرة':'debt_issued',
 'توزيعات أرباح مدفوعة':'dividends_paid',
}
LABELS={normalize(k):v for k,v in ALIASES.items()}
# The archived Arabic PDF emits the lam-alef ligature in this known reordered
# spelling. Keep explicit whole-caption alternatives, not fuzzy word matching.
LABELS.update({normalize(k.replace('الأنشطة','األنشطة')):v for k,v in ALIASES.items()})
LABELS.update({k.replace(normalize('الاستثمارية'),normalize('االستثمارية')):v
              for k,v in list(LABELS.items())})
LABELS[normalize('صافي النقدية من المستخدمة في األنشطة التمويلية')]='financing_cash_flow'
LABELS[normalize('استهالك وإطفاء')]='depreciation_amortization_cash_flow'

def resolve(label,statement='cash_flow'):
    # The same issuer uses "issued debt securities" as a balance stock and
    # as proceeds in a cash-flow statement. Exact caption alone is not enough.
    return LABELS.get(normalize(label)) if statement=='cash_flow' else None

def sar_thousand_unit(text):
    clean=normalize(text)
    return 'السعود' in clean and any(u in clean for u in
        ('بالافالريالات','باالفالرياالت','بالافالرياالت','باالفالريالات'))

def read_page(words,text,width,height,page):
    clean=normalize(text)
    if any(h in normalize(text[:250]) for h in ('ايضاحاتحول','ايضاحاتالقوائم')):
        return [],'notes_not_primary_cashflow'
    if 'قائمةالتدفقاتالنقدية' not in normalize(text[:800]):
        return [],'not_primary_cashflow_candidate'
    if not sar_thousand_unit(text[:1200]):
        return [],'explicit_sar_thousand_unit_missing'
    dates=columns(words,height)
    if not dates:return [],'unreliable_or_missing_native_dates'
    right=max(x for x,end in dates)+55
    rows=[]
    for w in sorted(words,key=lambda w:w[1]):
        if rows and abs(w[1]-rows[-1][0][1])<3:rows[-1].append(w)
        else:rows.append([w])
    facts=[]
    for row in rows:
        label_words=[w for w in row if w[0]>right and re.search(r'[\u0600-\u06ff\ufb50-\ufeff]',w[4])]
        label=' '.join(w[4] for w in sorted(label_words,key=lambda w:w[0],reverse=True))
        metric=resolve(label)
        if not metric:continue
        for x,end in dates:
            values=[w for w in row if abs((w[0]+w[2])/2-x)<35 and number(w[4]) is not None]
            if len(values)!=1:continue
            value=row_number(row,values[0])
            if value is None:continue
            kind='fy' if end[5:]== '12-31' else 'ytd'
            facts.append({'metric':metric,'source_label':label,'value':str(value),'scale':'1000',
                'currency':'SAR','unit':'SAR','period_start':end[:4]+'-01-01','period_end':end,
                'period_kind':kind,'fiscal_year':int(end[:4]),'fiscal_quarter':(int(end[5:7])+2)//3,
                'page':page,'extraction_method':'native_arabic_cashflow_geometry_candidate'})
    return facts,'candidate_only_independent_review_required'
