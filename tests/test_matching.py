import pytest

from langtrust.evaluation.matching import contains_date


EXPECTED_DATE = "2026-09-14"


@pytest.mark.parametrize(
    "text",
    [
        "Payment deadline: 2026-09-14.",
        "Payment deadline: 14 September 2026.",
        "Payment deadline: September 14, 2026.",
        "Termin płatności: 14 września 2026 roku.",
        "Termin płatności: 14.09.2026.",
    ],
)
def test_contains_date_accepts_equivalent_en_pl_formats(text):
    assert contains_date(text, EXPECTED_DATE)


@pytest.mark.parametrize(
    "text",
    [
        "Payment deadline: 2023-09-15.",
        "Termin płatności: 2023-10-15.",
        "Payment deadline: [payment_deadline].",
        "Termin płatności: <termin_płatności>.",
    ],
)
def test_contains_date_rejects_wrong_or_placeholder_dates(text):
    assert not contains_date(text, EXPECTED_DATE)
