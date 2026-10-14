"""Explicit first-cover reporting dates outrank generated discovery titles."""
import re
from pathlib import Path
from datetime import date

MONTHS = 'January February March April May June July August September October November December'.split()
DATE = re.compile(r'\bfor\s+the\s+(?:(?:three|six|nine|twelve|3|6|9|12)\s+months?\s+(?:period\s+)?|year\s+)ended\s+(?:(' + '|'.join(MONTHS) + r')\s+(\d{1,2}),?\s+(20\d{2})|(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(20\d{2}))\b', re.I)


def explicit_cover_decision(text):
    dates = set()
    heading = False
    for match in DATE.finditer(text):
        heading = True
        month, day, year = match.group(1, 2, 3) if match.group(1) else match.group(5, 4, 6)
        try:
            dates.add(date(int(year), [m.lower() for m in MONTHS].index(month.lower()) + 1, int(day)))
        except ValueError:
            return True, None
    if not heading:
        return False, None
    if len(dates) != 1:
        return True, None
    end = dates.pop()
    return True, (end.isoformat(), end.year)


def cover_period_decision(path):
    if not path or Path(path).suffix.lower() != '.pdf' or not Path(path).is_file():
        return False, None
    import pymupdf
    with pymupdf.open(path) as document:
        for index in range(min(3, len(document))):
            text = document[index].get_text()
            if text.strip():
                return explicit_cover_decision(text)
    return False, None
