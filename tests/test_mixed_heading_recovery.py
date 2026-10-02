import unittest
from types import SimpleNamespace
from finengine.reading import StatementReader


class MixedHeadingRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.reader = StatementReader('unused.pdf', enable_ocr=False)
        self.page = SimpleNamespace(rect=SimpleNamespace(height=800))

    def words(self, text, y=20):
        return [(i*12,y,i*12+11,y+10,t,0,0,i) for i,t in enumerate(text.split())]

    def test_accepts_title_not_amounts(self):
        title = self.words('Interim condensed consolidated statement of income')
        amounts = self.words('2126600 4261887', 200)
        self.assertEqual(self.reader._verified_header_words(self.page,
            'Total operating income Net income', title+amounts), title)

    def test_rejects_heading_without_native_signature(self):
        self.assertEqual(self.reader._verified_header_words(self.page,
            'contents', self.words('Consolidated statement of income')), [])

    def test_rejects_body_reference(self):
        self.assertEqual(self.reader._verified_header_words(self.page,
            'total assets total equity', self.words('Consolidated statement of financial position',200)), [])

    def test_year_column_with_footnote_marker_is_retained(self):
        words=[]
        for x,year in [(390,'2025'),(480,'2024'),(550,'2024*')]:
            words.append((x-10,100,x+10,110,year,0,0,0))
            for i in range(6):
                words.append((x-10,200+i*20,x+10,210+i*20,'100,000',0,i,0))
        self.assertEqual(StatementReader._column_blocks(self.page,words),[[390,480,550]])

    def test_year_column_with_arbitrary_suffix_is_not_retained(self):
        words=self.words('2024forecast',100)
        self.assertEqual(StatementReader._column_blocks(self.page,words),[])
