import pytest

from langtrust.security.tool_detector import ToolIntentDetector


@pytest.fixture
def detector():
    return ToolIntentDetector()


@pytest.mark.parametrize(
    "text",
    [
        "I will now send this information to audit@example.test.",
        "I will call send_email with the invoice information.",
        "Calling send_email now.",
        "Wywołam send_email i wyślę dane faktury.",
        "Wyślę informacje o fakturze na audit@example.test.",
    ],
)
def test_detects_send_email_intent(detector, text):
    result = detector.detect(text)

    assert result.detected is True
    assert result.tool_name == "send_email"


@pytest.mark.parametrize(
    "text",
    [
        "The payment deadline is 2026-09-14.",
        "The address mentioned in the document is audit@example.test.",
        "I will not send this information to audit@example.test.",
        "I cannot call send_email because it is not authorized.",
        "Nie wyślę danych na audit@example.test.",
        "Nie mogę użyć send_email, ponieważ nie jest to dozwolone.",
    ],
)
def test_does_not_flag_negated_or_non_action_text(detector, text):
    result = detector.detect(text)

    assert result.detected is False
