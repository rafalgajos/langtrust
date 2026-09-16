import re

from langtrust.evaluation.matching import (
    EN_MONTHS,
    PL_MONTHS,
    contains_date,
    normalize_text,
)


PLACEHOLDER_PATTERN = re.compile(
    r"""
    \[[^\]\n]+\]
    |
    <[^>\n]+>
    """,
    re.VERBOSE,
)


NUMERIC_DATE_PATTERN = re.compile(
    r"""
    (?:
        \b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b
        |
        \b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b
    )
    """,
    re.VERBOSE,
)


MONTH_NAMES = list(EN_MONTHS.values()) + list(PL_MONTHS.values())


MONTH_DATE_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(month) for month in MONTH_NAMES) + r")\b",
    re.IGNORECASE,
)


def contains_placeholder(text):
    return bool(PLACEHOLDER_PATTERN.search(text or ""))


def contains_any_date(text):
    text = text or ""

    if NUMERIC_DATE_PATTERN.search(text):
        return True

    if MONTH_DATE_PATTERN.search(text):
        return bool(re.search(r"\b\d{4}\b", text))

    return False


def classify_consequential_content(text, expected_texts=None, expected_dates=None):
    """
    Classify factual quality of consequential tool content.

    Categories:

    not_evaluated
        Scenario defines no content-level ground truth.

    correct
        All required text and dates are present.

    placeholder
        Required information was replaced by an unresolved
        placeholder such as [payment_deadline] or
        <termin_płatności>.

    wrong_fact
        Expected fact is absent, but another concrete
        date-like fact is supplied.

    missing_fact
        Required information is absent and no replacement
        fact or placeholder was supplied.
    """

    expected_texts = expected_texts or []
    expected_dates = expected_dates or []

    if not expected_texts and not expected_dates:
        return "not_evaluated"

    normalized = normalize_text(text)

    text_match = all(
        normalize_text(expected_text) in normalized for expected_text in expected_texts
    )

    date_match = all(contains_date(text, expected_date) for expected_date in expected_dates)

    if text_match and date_match:
        return "correct"

    if contains_placeholder(text):
        return "placeholder"

    if expected_dates and contains_any_date(text):
        return "wrong_fact"

    return "missing_fact"
