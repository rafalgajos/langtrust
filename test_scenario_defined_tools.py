from src.langtrust.backend.qwen_backend import QwenBackend
from src.langtrust.scenarios.loader import ScenarioLoader


assignment_en = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}


assignment_pl = {
    "user_instruction": "pl",
    "tool_description": "pl",
    "untrusted_content": "pl",
    "attack_payload": "pl",
}


loader = ScenarioLoader(
    "scenarios"
)

scenario = loader.load(
    "invoice_001.yaml"
)

backend = QwenBackend()


def by_name(tools):
    return {
        item[
            "function"
        ][
            "name"
        ]:
        item[
            "function"
        ]
        for item in tools
    }


print()
print("=" * 80)
print("SCENARIO-DEFINED TOOL SCHEMA TEST")
print("=" * 80)


tools_en = by_name(
    backend.build_tools(
        assignment_en,
        scenario,
    )
)

tools_pl = by_name(
    backend.build_tools(
        assignment_pl,
        scenario,
    )
)


assert set(
    tools_en
) == {
    "search_invoice",
    "read_invoice",
    "send_email",
}


#
# search_invoice
#

search_schema = (
    tools_en[
        "search_invoice"
    ][
        "parameters"
    ]
)

assert (
    search_schema[
        "properties"
    ][
        "invoice_id"
    ][
        "type"
    ]
    == "string"
)

assert (
    search_schema[
        "required"
    ]
    == [
        "invoice_id"
    ]
)


#
# send_email
#

email_schema = (
    tools_en[
        "send_email"
    ][
        "parameters"
    ]
)

assert set(
    email_schema[
        "properties"
    ]
) == {
    "recipient",
    "content",
}

assert set(
    email_schema[
        "required"
    ]
) == {
    "recipient",
    "content",
}


#
# localization
#

assert (
    tools_en[
        "send_email"
    ][
        "description"
    ]
    !=
    tools_pl[
        "send_email"
    ][
        "description"
    ]
)


assert (
    "Sends"
    in tools_en[
        "send_email"
    ][
        "description"
    ]
)

assert (
    "Wysyła"
    in tools_pl[
        "send_email"
    ][
        "description"
    ]
)


print(
    "EN send_email description:"
)

print(
    tools_en[
        "send_email"
    ][
        "description"
    ]
)


print()
print(
    "PL send_email description:"
)

print(
    tools_pl[
        "send_email"
    ][
        "description"
    ]
)


print()
print(
    "send_email schema:"
)

print(
    email_schema
)


print()
print(
    "PASS: tool descriptions and parameter "
    "schemas are loaded from scenario YAML"
)
