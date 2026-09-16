import re
from datetime import date


EN_MONTHS = {
    1: "january",
    2: "february",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "august",
    9: "september",
    10: "october",
    11: "november",
    12: "december",
}


PL_MONTHS = {
    1: "stycznia",
    2: "lutego",
    3: "marca",
    4: "kwietnia",
    5: "maja",
    6: "czerwca",
    7: "lipca",
    8: "sierpnia",
    9: "września",
    10: "października",
    11: "listopada",
    12: "grudnia",
}


def normalize_text(text):
    text = (text or "").lower()
    text = text.replace(",", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_date(text, iso_date):
    """Return whether text contains a date equivalent to an ISO date.

    Both English and Polish textual dates and common numeric formats
    are recognized.
    """

    value = date.fromisoformat(iso_date)
    day, month, year = value.day, value.month, value.year

    variants = {
        iso_date,
        f"{day:02d}.{month:02d}.{year}",
        f"{day}.{month}.{year}",
        f"{day:02d}/{month:02d}/{year}",
        f"{day}/{month}/{year}",
        f"{day:02d}-{month:02d}-{year}",
        f"{day}-{month}-{year}",
        f"{day} {EN_MONTHS[month]} {year}",
        f"{EN_MONTHS[month]} {day} {year}",
        f"{day} {PL_MONTHS[month]} {year}",
    }

    normalized = normalize_text(text)
    return any(normalize_text(variant) in normalized for variant in variants)
