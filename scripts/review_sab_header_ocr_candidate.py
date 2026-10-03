"""Isolated mixed-header OCR experiment: source numbers and live DB stay untouched."""
import importlib.util
import json
import sys
import os
from pathlib import Path
import pymupdf

spec = importlib.util.spec_from_file_location('finengine.reading', '/tmp/reading-heading-candidate.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
BaseReader = module.StatementReader


class HeaderReader(BaseReader):
    def _page_content(self, page, page_index, ocr_budget):
        words, text = super()._page_content(page, page_index, ocr_budget)
        if (not words or self._heading_statement(page, words, text)
                or page_index > 10 or not any(
                    all(any(term in text.lower() for term in group) for group in signature)
                    for signature in self._SIGNATURE.values())):
            return words, text
        from rapidocr import RapidOCR
        if self._ocr_engine is None:
            self._ocr_engine = RapidOCR()
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2,2),
                             clip=pymupdf.Rect(0,0,page.rect.width,page.rect.height*.18))
        output = self._ocr_engine(pix.tobytes('png'))
        recovered = []
        for index, (box, line, score) in enumerate(zip(output.boxes, output.txts, output.scores)):
            if score >= .85:
                recovered.extend(self._split_ocr_line(box,str(line),2,index))
        headings = self._verified_header_words(page,text,recovered)
        if not headings:
            return words,text
        # Only an explicit unit declaration joins the recovered heading text.
        units = [str(line) for line in output.txts if self._declared_scale(str(line)) is not None]
        evidence = {'page': page_index+1,'heading': ' '.join(w[4] for w in headings),
                    'unit_declarations':units,'native_numbers_replaced':False}
        print(json.dumps(evidence),flush=True)
        return words+headings,text+'\n'+evidence['heading']+'\n'+'\n'.join(units)


module.StatementReader = HeaderReader
from finengine import cli
from finengine.database import Database
from finengine.registry import CompanyRegistry

db=Database('/app/state/financial.sqlite3',initialize=False)
db.conn.execute('PRAGMA query_only=ON')
company=CompanyRegistry.combined(db.conn,'/app/config/companies.json').get('sa:1060')
prior=Path('/app/state/reports/sab-period-correction-review/interim-batch-v1')
root=prior.with_name(os.environ.get('SAB_BATCH_ROOT', 'interim-header-candidate-v3'))
root.mkdir(exist_ok=True)
if os.environ.get('SAB_BATCH_KEYS'):
    keys=json.loads(Path(os.environ['SAB_BATCH_KEYS']).read_text())
else:
    keys=[json.loads(p.read_text())['source_key'] for p in sorted(prior.glob('*.review.json'))]
for key in keys:
    digest=key.rsplit(':',1)[1]
    target=root/(digest+'.review.json')
    if target.exists():continue
    source=db.stored_source(key)
    try:
        manifest,report,reader=cli._read_pdf_manifest(Path(source['local_path']),company,source,False)
    except Exception as error:
        target.write_text(json.dumps({'source_key':key,'error':str(error),'production_modified':False}))
        continue
    (root/(digest+'.manifest.json')).write_text(json.dumps(manifest,indent=2,default=str))
    result={'source_key':key,'facts':len(manifest.get('facts',[])),
            'verification':report,'production_modified':False,'candidate_only':True}
    target.write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,default=str),flush=True)
