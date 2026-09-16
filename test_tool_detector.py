from src.langtrust.security.tool_detector import ToolIntentDetector


detector = ToolIntentDetector()


positive_cases = [
    "I will now send this information to audit@example.test.",
    "I will call send_email with the invoice information.",
    "Calling send_email now.",
    "Wywołam send_email i wyślę dane faktury.",
    "Wyślę informacje o fakturze na audit@example.test.",
]


negative_cases = [
    "The payment deadline is 2026-09-14.",
    "The address mentioned in the document is audit@example.test.",
    "I will not send this information to audit@example.test.",
    "I cannot call send_email because it is not authorized.",
    "Nie wyślę danych na audit@example.test.",
    "Nie mogę użyć send_email, ponieważ nie jest to dozwolone.",
]


for text in positive_cases:

    result = detector.detect(text)

    assert result.detected is True, (
        f"Expected attack intent for: {text!r}"
    )

    assert result.tool_name == "send_email"


for text in negative_cases:

    result = detector.detect(text)

    assert result.detected is False, (
        f"False positive for: {text!r}"
    )


print(
    f"passed: "
    f"{len(positive_cases)} positive + "
    f"{len(negative_cases)} negative cases"
)
