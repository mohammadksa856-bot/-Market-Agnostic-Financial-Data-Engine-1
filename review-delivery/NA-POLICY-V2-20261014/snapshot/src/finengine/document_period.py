"""Explicit reporting dates on document covers outrank discovery titles."""
import re
import unicodedata
from datetime import date
from pathlib import Path

MONTHS = 'January February March April May June July August September October November December'.split()
ANNUAL = re.compile(r'for\s+the\s+year\s+ended\s+(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(20\d{2})', re.I)
ANNUAL_MONTH_FIRST = re.compile(r'(?:for\s+the\s+)?year\s+ended\s+(' + '|'.join(MONTHS) + r')\s+(\d{1,2}),?\s+(20\d{2})', re.I)
ARABIC_ANNUAL = re.compile(r'(?:للسنة|للعام|عن\s+السنة|السنة)\s+(?:المالية\s+)?المنتهية\s+في\s+(\d{1,2})\s+(ديسمبر)\s+(20\d{2})')


def normalized_reporting_text(text):
    text = unicodedata.normalize('NFKC', text)
    text = ''.join(c for c in text if unicodedata.category(c) not in {'Cf', 'Mn'})
    return text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))


def annual_period_from_text(text):
    text = normalized_reporting_text(text)
    dates = set()
    for day, month, year in ANNUAL.findall(text):
        try:
            dates.add(date(int(year), [m.lower() for m in MONTHS].index(month.lower()) + 1, int(day)))
        except ValueError:
            continue
    for month, day, year in ANNUAL_MONTH_FIRST.findall(text):
        try:
            dates.add(date(int(year), [m.lower() for m in MONTHS].index(month.lower()) + 1, int(day)))
        except ValueError:
            continue
    for day, month, year in ARABIC_ANNUAL.findall(text):
        try:
            dates.add(date(int(year), 12, int(day)))
        except ValueError:
            continue
    if len(dates) != 1:
        return None
    end = dates.pop()
    return end.isoformat(), end.year


def annual_cover_period(path):
    if not path or Path(path).suffix.lower() != '.pdf' or not Path(path).is_file():
        return None
    import pymupdf
    with pymupdf.open(path) as document:
        # Some exchange PDFs prepend a blank page. Inspect only the cover
        # region, never years in statement notes or historical tables.
        text = '\n'.join(document[i].get_text() for i in range(min(3, len(document))))
        return annual_period_from_text(text)
