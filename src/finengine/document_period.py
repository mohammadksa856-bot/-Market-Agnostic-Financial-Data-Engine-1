"""Explicit reporting dates on document covers outrank discovery titles."""
import re
from datetime import date
from pathlib import Path

MONTHS = 'January February March April May June July August September October November December'.split()
ANNUAL = re.compile(r'for\s+the\s+year\s+ended\s+(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(20\d{2})', re.I)


def annual_period_from_text(text):
    dates = set()
    for day, month, year in ANNUAL.findall(text):
        try:
            dates.add(date(int(year), [m.lower() for m in MONTHS].index(month.lower()) + 1, int(day)))
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
