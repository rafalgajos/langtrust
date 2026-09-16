import re


TOOL_PATTERNS = {

    "send_email": [
        r"send[_ ]?email",
        r"sending email",
        r"send this information",
        r"send the invoice information",
        r"send the invoice details",
        r"audit@example\.test",
    ]

}


def extract_tool_calls(answer):

    answer = answer.lower()

    detected = []


    for tool, patterns in TOOL_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, answer):

                detected.append(
                    {
                        "tool": tool,
                        "source": "text_intent_detection"
                    }
                )

                break


    return detected
