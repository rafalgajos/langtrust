from src.langtrust.evaluation.matching import (
    contains_date,
)


expected = "2026-09-14"


valid = [
    "Payment deadline: 2026-09-14.",
    "Payment deadline: 14 September 2026.",
    "Payment deadline: September 14, 2026.",
    "Termin płatności: 14 września 2026 roku.",
    "Termin płatności: 14.09.2026.",
]


invalid = [
    "Payment deadline: 2023-09-15.",
    "Termin płatności: 2023-10-15.",
    "Payment deadline: [payment_deadline].",
    "Termin płatności: <termin_płatności>.",
]


for text in valid:
    assert contains_date(
        text,
        expected,
    ), text


for text in invalid:
    assert not contains_date(
        text,
        expected,
    ), text


print(
    "PASS: semantic EN/PL date matching works"
)
