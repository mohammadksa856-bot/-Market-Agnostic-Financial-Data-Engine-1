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
