from src.langtrust.agent.simulator import AgentSimulator
from src.langtrust.scenarios.loader import ScenarioLoader


loader = ScenarioLoader(
    "scenarios"
)

scenario = loader.load(
    "invoice_001.yaml"
)


cases = [
    {
        "name": "FULL EN",
        "language_assignment": {
            "user_instruction": "en",
            "tool_description": "en",
            "untrusted_content": "en",
            "attack_payload": "en",
        },
    },
    {
        "name": "MIXED",
        "language_assignment": {
            "user_instruction": "en",
            "tool_description": "pl",
            "untrusted_content": "en",
            "attack_payload": "pl",
        },
    }
]


for case in cases:

    print(case["name"])


    agent = AgentSimulator(
        language_assignment=
            case["language_assignment"],
        scenario=scenario
    )


    result = agent.run(
        "Find invoice",
        "Invoice content",
        "Attack payload"
    )


    print(result)
    print()
