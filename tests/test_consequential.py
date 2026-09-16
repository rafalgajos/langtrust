import pytest

from langtrust.evaluation.consequential import (
    classify_consequential_content,
)


EXPECTED_TEXTS = ["FV-2026-081"]
EXPECTED_DATES = ["2026-09-14"]


@pytest.mark.parametrize(
    ("text", "expected_status"),
    [
        (
            "Invoice FV-2026-081 is due for payment on 2026-09-14.",
            "correct",
        ),
        (
            "Faktura FV-2026-081 ma termin płatności 14 września 2026 roku.",
            "correct",
        ),
        (
            "Invoice FV-2026-081 is due for payment on [payment_deadline].",
            "placeholder",
        ),
        (
            "Faktura FV-2026-081 ma termin płatności <termin_płatności>.",
            "placeholder",
        ),
        (
            "Invoice identifier: FV-2026-081, Payment deadline: 2023-09-15",
            "wrong_fact",
        ),
        (
            "Faktura FV-2026-081 ma termin płatności do 30.09.2023.",
            "wrong_fact",
        ),
        (
            "Invoice FV-2026-081 information.",
            "missing_fact",
        ),
    ],
)
def test_classify_consequential_content(text, expected_status):
    actual = classify_consequential_content(
        text,
        expected_texts=EXPECTED_TEXTS,
        expected_dates=EXPECTED_DATES,
    )

    assert actual == expected_status
